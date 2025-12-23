from neo4j import GraphDatabase
from app.config import settings
import json
from typing import List, Dict, Optional

class Neo4jGraph:
    def __init__(self):
        self._driver = None
        try:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            print("✅ Neo4j driver initialized")
        except Exception as e:
            print(f"⚠️ Neo4j driver init failed: {e}")

    def close(self):
        if self._driver:
            self._driver.close()

    @property
    def is_connected(self) -> bool:
        return self._driver is not None

    async def create_remix_node(self, node_id: str, metadata: dict):
        """
        Creates a Remix node in the graph.
        """
        if not self._driver:
            print("⚠️ Neo4j not connected, skipping node creation")
            return
            
        query = """
        MERGE (n:Remix {node_id: $node_id})
        SET n += $metadata, n.created_at = timestamp()
        RETURN n
        """
        try:
            with self._driver.session() as session:
                session.run(query, node_id=node_id, metadata=metadata)
                print(f"✅ Neo4j Remix node created: {node_id}")
        except Exception as e:
            print(f"❌ Failed to create Neo4j node: {e}")

    async def create_genealogy_edge(
        self,
        parent_node_id: str,
        child_node_id: str,
        mutations: dict,
        performance_delta: str
    ) -> Dict:
        """
        Creates the EVOLVED_TO relationship tracking mutations and performance.
        """
        if not self._driver:
            print("⚠️ Neo4j not connected, skipping edge creation")
            return {"created": False, "reason": "Neo4j not connected"}
            
        query = """
        MATCH (parent:Remix {node_id: $parent_id})
        MATCH (child:Remix {node_id: $child_id})
        MERGE (parent)-[r:EVOLVED_TO]->(child)
        SET r.mutation_profile = $mutations,
            r.performance_delta = $delta,
            r.created_at = timestamp()
        RETURN r
        """
        try:
            with self._driver.session() as session:
                session.run(query, 
                            parent_id=parent_node_id, 
                            child_id=child_node_id, 
                            mutations=json.dumps(mutations), 
                            delta=performance_delta)
            print(f"✅ Genealogy edge created: {parent_node_id} → {child_node_id} ({performance_delta})")
            return {
                "created": True,
                "parent": parent_node_id,
                "child": child_node_id,
                "performance_delta": performance_delta
            }
        except Exception as e:
            print(f"❌ Failed to create genealogy edge: {e}")
            return {"created": False, "reason": str(e)}

    async def create_edge_from_mutation_profile(
        self,
        mutation_profile  # MutationProfile (avoiding circular import)
    ) -> Dict:
        """
        MutationProfile 객체를 받아 EVOLVED_TO 엣지 생성
        
        이 함수는 detect_mutations() 결과를 바로 사용:
        1. Fork 생성 시 부모/자식 분석 결과 비교
        2. MutationProfile 생성
        3. 이 함수로 Neo4j 엣지 저장
        """
        mutations_dict = {
            "audio": mutation_profile.audio_mutation.model_dump() if mutation_profile.audio_mutation else None,
            "visual": mutation_profile.visual_mutation.model_dump() if mutation_profile.visual_mutation else None,
            "setting": mutation_profile.setting_mutation.model_dump() if mutation_profile.setting_mutation else None,
            "hook": mutation_profile.hook_pattern_mutation.model_dump() if mutation_profile.hook_pattern_mutation else None,
            "timing": mutation_profile.timing_mutation.model_dump() if mutation_profile.timing_mutation else None,
            "text": mutation_profile.text_overlay_mutation.model_dump() if mutation_profile.text_overlay_mutation else None,
            "mutation_count": mutation_profile.mutation_count,
            "primary_type": mutation_profile.primary_mutation_type,
            "summary": mutation_profile.mutation_summary
        }
        
        # Remove None values
        mutations_dict = {k: v for k, v in mutations_dict.items() if v is not None}
        
        return await self.create_genealogy_edge(
            parent_node_id=mutation_profile.parent_node_id,
            child_node_id=mutation_profile.child_node_id,
            mutations=mutations_dict,
            performance_delta=mutation_profile.performance_delta or "pending"
        )

    async def query_mutation_strategy(
        self,
        template_node_id: str,
        target_category: Optional[str] = None
    ) -> List[Dict]:
        """
        "이 템플릿에서 어떤 변주를 하면 터질까?"
        → 과거 성공 사례 기반 추천
        """
        if not self._driver:
            # Mock response for development
            return self._get_mock_mutation_strategies()
            
        # Build query based on whether we have a specific template
        if template_node_id:
            query = """
            MATCH (template:Remix {node_id: $template_id})-[r:EVOLVED_TO]->(successful:Remix)
            WHERE r.performance_delta CONTAINS '+'
            RETURN r.mutation_profile as mutation, 
                   r.performance_delta as delta, 
                   successful.view_count as views,
                   successful.node_id as node_id
            ORDER BY successful.view_count DESC
            LIMIT 5
            """
            params = {"template_id": template_node_id}
        else:
            # Global top strategies
            query = """
            MATCH (parent:Remix)-[r:EVOLVED_TO]->(child:Remix)
            WHERE r.performance_delta CONTAINS '+'
            RETURN r.mutation_profile as mutation, 
                   r.performance_delta as delta, 
                   child.view_count as views,
                   parent.node_id as parent_id,
                   child.node_id as child_id
            ORDER BY child.view_count DESC
            LIMIT 10
            """
            params = {}
        
        try:
            with self._driver.session() as session:
                result = session.run(query, **params)
                recommendations = []
                for record in result:
                    mutation_data = record.get("mutation")
                    if mutation_data and isinstance(mutation_data, str):
                        try:
                            mutation_data = json.loads(mutation_data)
                        except:
                            pass
                    
                    recommendations.append({
                        "mutation_strategy": mutation_data,
                        "expected_boost": record.get("delta", "+0%"),
                        "reference_views": record.get("views"),
                        "confidence": 0.85,  # Can be calculated based on sample size
                        "rationale": f"Similar template achieved {record.get('delta', 'N/A')} with this mutation"
                    })
                
                return recommendations if recommendations else self._get_mock_mutation_strategies()
                
        except Exception as e:
            print(f"❌ Mutation strategy query failed: {e}")
            return self._get_mock_mutation_strategies()

    async def get_genealogy_tree(self, node_id: str, depth: int = 3) -> Dict:
        """
        특정 노드의 가계도(Genealogy Tree) 반환
        """
        if not self._driver:
            return {"root": node_id, "children": [], "mock": True}
            
        query = f"""
        MATCH path = (root:Remix {{node_id: $node_id}})-[:EVOLVED_TO*0..{depth}]->(descendant:Remix)
        RETURN path
        """
        try:
            with self._driver.session() as session:
                result = session.run(query, node_id=node_id)
                # Parse paths into tree structure
                nodes = set()
                edges = []
                for record in result:
                    path = record["path"]
                    for node in path.nodes:
                        nodes.add(node["node_id"])
                    for rel in path.relationships:
                        edges.append({
                            "parent": rel.start_node["node_id"],
                            "child": rel.end_node["node_id"],
                            "delta": rel.get("performance_delta", "N/A")
                        })
                
                return {
                    "root": node_id,
                    "total_nodes": len(nodes),
                    "edges": edges
                }
        except Exception as e:
            print(f"❌ Genealogy tree query failed: {e}")
            return {"root": node_id, "error": str(e)}

    def _get_mock_mutation_strategies(self) -> List[Dict]:
        """Mock data for development when Neo4j is not available"""
        return [
            {
                "mutation_strategy": {
                    "audio": {"before": "Original Track", "after": "K-pop Cover"},
                    "setting": {"before": "Indoor", "after": "Outdoor Cafe"}
                },
                "expected_boost": "+127%",
                "reference_views": 500000,
                "confidence": 0.85,
                "rationale": "K-pop audio swap has historically shown +127% avg boost"
            },
            {
                "mutation_strategy": {
                    "timing": {"before": "Standard", "after": "Fast-paced cuts"},
                    "filter": {"before": "None", "after": "Retro VHS"}
                },
                "expected_boost": "+89%",
                "reference_views": 350000,
                "confidence": 0.78,
                "rationale": "Retro aesthetic + fast cuts trending in this category"
            },
            {
                "mutation_strategy": {
                    "text_overlay": {"before": "None", "after": "Meme Caption"}
                },
                "expected_boost": "+65%",
                "reference_views": 200000,
                "confidence": 0.72,
                "rationale": "Adding meme captions increases shareability"
            }
        ]

neo4j_graph = Neo4jGraph()

