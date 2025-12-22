from neo4j import AsyncGraphDatabase
from app.config import settings

class GraphDatabase:
    def __init__(self):
        self._driver = None

    async def connect(self):
        """Initialize Neo4j driver connection"""
        if not self._driver:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Check connection
            try:
                await self._driver.verify_connectivity()
                print("✅ Neo4j connected successfully")
            except Exception as e:
                print(f"⚠️ Neo4j connection failed: {e}")
                self._driver = None

    async def close(self):
        """Close Neo4j driver connection"""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def create_user_node(self, user_id: str, name: str, email: str):
        """Create a User node in Neo4j"""
        if not self._driver:
            return
            
        query = """
        MERGE (u:User {id: $user_id})
        SET u.name = $name, u.email = $email
        RETURN u
        """
        async with self._driver.session() as session:
            await session.run(query, user_id=user_id, name=name, email=email)

    async def create_remix_node(self, node_id: str, title: str, layer: str, created_by: str):
        """Create a RemixNode and link to User"""
        if not self._driver:
            return

        query = """
        MERGE (n:RemixNode {id: $node_id})
        SET n.title = $title, n.layer = $layer, n.created_at = datetime()
        WITH n
        MATCH (u:User {id: $created_by})
        MERGE (u)-[:CREATED]->(n)
        """
        async with self._driver.session() as session:
            await session.run(query, node_id=node_id, title=title, layer=layer, created_by=created_by)

    async def link_remix_nodes(self, parent_node_id: str, child_node_id: str):
        """Create FORKED_FROM relationship"""
        if not self._driver:
            return
            
        query = """
        MATCH (p:RemixNode {id: $parent_id})
        MATCH (c:RemixNode {id: $child_id})
        MERGE (c)-[:FORKED_FROM]->(p)
        """
        async with self._driver.session() as session:
            await session.run(query, parent_id=parent_node_id, child_id=child_node_id)

    async def get_genealogy(self, node_id: str):
        """
        Fetch the genealogy tree for a given node.
        Returns parent path (ancestors) and children (descendants).
        """
        if not self._driver:
            return None

        # Cypher query to get ancestors and immediate children
        query = """
        MATCH (n:RemixNode {id: $node_id})
        
        // Find Ancestors (up to 3 levels)
        OPTIONAL MATCH path_up = (n)-[:FORKED_FROM*1..3]->(ancestor)
        
        // Find Children (immediate forks)
        OPTIONAL MATCH (child)-[:FORKED_FROM]->(n)
        
        RETURN 
            n as current,
            collect(DISTINCT ancestor) as ancestors,
            collect(DISTINCT child) as children
        """
        
        async with self._driver.session() as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            
            if not record:
                return None
                
            return {
                "current": dict(record["current"]),
                "ancestors": [dict(node) for node in record["ancestors"]],
                "children": [dict(node) for node in record["children"]]
            }

graph_db = GraphDatabase()
