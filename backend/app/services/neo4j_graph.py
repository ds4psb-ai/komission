from neo4j import GraphDatabase
from app.config import settings
import json

class Neo4jGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    async def create_remix_node(self, node_id: str, metadata: dict):
        """
        Creates a Remix node in the graph.
        """
        query = """
        MERGE (n:Remix {node_id: $node_id})
        SET n += $metadata, n.created_at = timestamp()
        RETURN n
        """
        try:
            with self.driver.session() as session:
                session.run(query, node_id=node_id, metadata=metadata)
        except Exception as e:
            print(f"Failed to create Neo4j node: {e}")

    async def create_genealogy_edge(
        self,
        parent_node_id: str,
        child_node_id: str,
        mutations: dict,
        performance_delta: str
    ):
        """
        Creates the EVOLVED_TO relationship tracking mutations and performance.
        """
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
            # Serialize dicts to string if needed or rely on Neo4j driver serialization
            # Here keeping it simple
            with self.driver.session() as session:
                session.run(query, 
                            parent_id=parent_node_id, 
                            child_id=child_node_id, 
                            mutations=json.dumps(mutations), 
                            delta=performance_delta)
        except Exception as e:
            print(f"Failed to create genealogy edge: {e}")

    async def get_strategy_recommendation(self, category: str):
        """
        Finds high-performing mutation strategies for a category.
        """
        query = """
        MATCH (p:Remix)-[r:EVOLVED_TO]->(c:Remix)
        WHERE c.commerce_category = $category AND r.performance_delta CONTAINS '+'
        RETURN r.mutation_profile, r.performance_delta, c.view_count
        ORDER BY c.view_count DESC
        LIMIT 5
        """
        # Implementation placeholder
        pass

neo4j_graph = Neo4jGraph()
