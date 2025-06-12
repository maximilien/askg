from datetime import datetime
from typing import List, Dict, Any, Optional
import time
import yaml
from neo4j import GraphDatabase
from tqdm import tqdm
from models import (
    MCPServer, ServerRelationship, OntologyCategory, KnowledgeGraph,
    RelationshipType, ServerCategory, OperationType
)


class Neo4jManager:
    def __init__(self, config_path: str = "config.yaml", instance: str = "local"):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        neo4j_config = config['neo4j'][instance]
        self.instance = instance
        self.driver = GraphDatabase.driver(
            neo4j_config['uri'],
            auth=(neo4j_config['user'], neo4j_config['password'])
        )
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def create_constraints_and_indexes(self):
        """Create database constraints and indexes for optimal performance"""
        constraints_and_indexes = [
            # Constraints
            "CREATE CONSTRAINT server_id_unique IF NOT EXISTS FOR (s:Server) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR (r:Relationship) REQUIRE r.id IS UNIQUE",
            
            # Indexes
            "CREATE INDEX server_name_index IF NOT EXISTS FOR (s:Server) ON (s.name)",
            "CREATE INDEX server_category_index IF NOT EXISTS FOR (s:Server) ON (s.categories)",
            "CREATE INDEX server_author_index IF NOT EXISTS FOR (s:Server) ON (s.author)",
            "CREATE INDEX server_language_index IF NOT EXISTS FOR (s:Server) ON (s.implementation_language)",
            "CREATE INDEX relationship_type_index IF NOT EXISTS FOR (r:Relationship) ON (r.type)",
        ]
        
        with self.driver.session() as session:
            for query in constraints_and_indexes:
                try:
                    session.run(query)
                except Exception as e:
                    print(f"Warning: Could not create constraint/index: {e}")
    
    def clear_database(self):
        """Clear all nodes and relationships"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def create_server_node(self, server: MCPServer) -> None:
        """Create a server node in Neo4j"""
        cypher = """
        MERGE (s:Server {id: $id})
        SET s.name = $name,
            s.description = $description,
            s.version = $version,
            s.author = $author,
            s.license = $license,
            s.homepage = $homepage,
            s.repository = $repository,
            s.implementation_language = $implementation_language,
            s.installation_command = $installation_command,
            s.categories = $categories,
            s.operations = $operations,
            s.data_types = $data_types,
            s.registry_source = $registry_source,
            s.source_url = $source_url,
            s.last_updated = $last_updated,
            s.popularity_score = $popularity_score,
            s.download_count = $download_count,
            s.tools_count = $tools_count,
            s.resources_count = $resources_count,
            s.prompts_count = $prompts_count,
            s.created_at = datetime()
        """
        
        with self.driver.session() as session:
            session.run(cypher, {
                'id': server.id,
                'name': server.name,
                'description': server.description,
                'version': server.version,
                'author': server.author,
                'license': server.license,
                'homepage': str(server.homepage) if server.homepage else None,
                'repository': str(server.repository) if server.repository else None,
                'implementation_language': server.implementation_language,
                'installation_command': server.installation_command,
                'categories': [cat.value for cat in server.categories],
                'operations': [op.value for op in server.operations],
                'data_types': server.data_types,
                'registry_source': server.registry_source.value,
                'source_url': str(server.source_url) if server.source_url else None,
                'last_updated': server.last_updated.isoformat() if server.last_updated else None,
                'popularity_score': server.popularity_score or 0,
                'download_count': server.download_count or 0,
                'tools_count': len(server.tools) if server.tools else 0,
                'resources_count': len(server.resources) if server.resources else 0,
                'prompts_count': len(server.prompts) if server.prompts else 0,
            })
    
    def load_knowledge_graph_fast(self, kg: KnowledgeGraph, batch_size: int = 500) -> None:
        """Load knowledge graph using batch processing for better performance"""
        start_time = time.time()
        
        total_items = len(kg.servers) + len(kg.categories) + len(kg.relationships)
        print(f"⚡ Fast loading knowledge graph: {total_items:,} total items")
        print(f"📦 Batch size: {batch_size}")
        print(f"🎯 Target Neo4j instance: {self.instance}")
        print()
        
        # Step 1: Create constraints and indexes
        print("🔧 Creating constraints and indexes...")
        self.create_constraints_and_indexes()
        print("   ✅ Database schema ready")
        print()
        
        # Step 2: Batch load servers
        if kg.servers:
            print(f"⚡ Batch loading {len(kg.servers):,} servers...")
            
            batches = [kg.servers[i:i + batch_size] for i in range(0, len(kg.servers), batch_size)]
            
            progress_bar = tqdm(
                batches,
                desc="📥 Server Batches",
                unit="batch",
                colour='blue',
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} batches [{elapsed}<{remaining}, {rate_fmt}]'
            )
            
            for batch in progress_bar:
                progress_bar.set_postfix_str(f"Processing {len(batch)} servers")
                self.create_servers_batch(batch)
            
            progress_bar.close()
            print(f"   ✅ {len(kg.servers):,} servers loaded in {len(batches)} batches")
            print()
        
        # Categories and relationships use regular loading since they're typically smaller
        if kg.categories:
            print(f"📂 Loading {len(kg.categories)} categories...")
            for category in tqdm(kg.categories, desc="📁 Categories", colour='green'):
                self.create_category_nodes([category])
            print(f"   ✅ {len(kg.categories)} categories loaded")
            print()
        
        if kg.relationships:
            print(f"🔗 Loading {len(kg.relationships):,} relationships...")
            for relationship in tqdm(kg.relationships, desc="🔗 Relationships", colour='yellow'):
                self.create_relationship(relationship)
            print(f"   ✅ {len(kg.relationships):,} relationships loaded")
            print()
        
        # Final summary
        elapsed_time = time.time() - start_time
        rate = total_items / elapsed_time if elapsed_time > 0 else 0
        
        print("=" * 60)
        print(f"⚡ Fast loading completed!")
        print(f"⏱️  Total time: {elapsed_time:.1f}s")
        print(f"📈 Loading rate: {rate:.1f} items/second")
        print(f"🎯 Instance: {self.instance}")
        print("=" * 60)
    
    def create_servers_batch(self, servers: List[MCPServer]) -> None:
        """Create server nodes in a single batch operation"""
        if not servers:
            return
            
        cypher = """
        UNWIND $servers as server
        MERGE (s:Server {id: server.id})
        SET s.name = server.name,
            s.description = server.description,
            s.version = server.version,
            s.author = server.author,
            s.license = server.license,
            s.homepage = server.homepage,
            s.repository = server.repository,
            s.implementation_language = server.implementation_language,
            s.installation_command = server.installation_command,
            s.categories = server.categories,
            s.operations = server.operations,
            s.data_types = server.data_types,
            s.registry_source = server.registry_source,
            s.source_url = server.source_url,
            s.last_updated = server.last_updated,
            s.popularity_score = server.popularity_score,
            s.download_count = server.download_count,
            s.tools_count = server.tools_count,
            s.resources_count = server.resources_count,
            s.prompts_count = server.prompts_count,
            s.created_at = datetime()
        """
        
        server_data = []
        for server in servers:
            server_data.append({
                'id': server.id,
                'name': server.name,
                'description': server.description,
                'version': server.version,
                'author': server.author,
                'license': server.license,
                'homepage': str(server.homepage) if server.homepage else None,
                'repository': str(server.repository) if server.repository else None,
                'implementation_language': server.implementation_language,
                'installation_command': server.installation_command,
                'categories': [cat.value for cat in server.categories],
                'operations': [op.value for op in server.operations],
                'data_types': server.data_types,
                'registry_source': server.registry_source.value,
                'source_url': str(server.source_url) if server.source_url else None,
                'last_updated': server.last_updated.isoformat() if server.last_updated else None,
                'popularity_score': server.popularity_score or 0,
                'download_count': server.download_count or 0,
                'tools_count': len(server.tools) if server.tools else 0,
                'resources_count': len(server.resources) if server.resources else 0,
                'prompts_count': len(server.prompts) if server.prompts else 0,
            })
        
        with self.driver.session() as session:
            session.run(cypher, {'servers': server_data})
    
    def create_tool_nodes(self, server: MCPServer) -> None:
        """Create tool nodes and link them to servers"""
        if not server.tools:
            return
        
        for tool in server.tools:
            cypher = """
            MERGE (t:Tool {name: $name, server_id: $server_id})
            SET t.description = $description,
                t.parameters = $parameters
            WITH t
            MATCH (s:Server {id: $server_id})
            MERGE (s)-[:HAS_TOOL]->(t)
            """
            
            with self.driver.session() as session:
                session.run(cypher, {
                    'name': tool.name,
                    'server_id': server.id,
                    'description': tool.description,
                    'parameters': tool.parameters
                })
    
    def create_resource_nodes(self, server: MCPServer) -> None:
        """Create resource nodes and link them to servers"""
        if not server.resources:
            return
        
        for resource in server.resources:
            cypher = """
            MERGE (r:Resource {uri: $uri, server_id: $server_id})
            SET r.name = $name,
                r.description = $description,
                r.mime_type = $mime_type
            WITH r
            MATCH (s:Server {id: $server_id})
            MERGE (s)-[:HAS_RESOURCE]->(r)
            """
            
            with self.driver.session() as session:
                session.run(cypher, {
                    'uri': resource.uri,
                    'server_id': server.id,
                    'name': resource.name,
                    'description': resource.description,
                    'mime_type': resource.mime_type
                })
    
    def create_category_nodes(self, categories: List[OntologyCategory]) -> None:
        """Create category nodes and their hierarchical relationships"""
        for category in categories:
            cypher = """
            MERGE (c:Category {id: $id})
            SET c.name = $name,
                c.description = $description,
                c.data_domains = $data_domains,
                c.operational_patterns = $operational_patterns,
                c.integration_patterns = $integration_patterns
            """
            
            with self.driver.session() as session:
                session.run(cypher, {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'data_domains': category.data_domains,
                    'operational_patterns': category.operational_patterns,
                    'integration_patterns': category.integration_patterns
                })
                
                # Create parent-child relationships
                if category.parent_category_id:
                    parent_cypher = """
                    MATCH (parent:Category {id: $parent_id})
                    MATCH (child:Category {id: $child_id})
                    MERGE (parent)-[:HAS_SUBCATEGORY]->(child)
                    """
                    session.run(parent_cypher, {
                        'parent_id': category.parent_category_id,
                        'child_id': category.id
                    })
                
                # Link servers to categories
                for server_id in category.servers:
                    server_cypher = """
                    MATCH (s:Server {id: $server_id})
                    MATCH (c:Category {id: $category_id})
                    MERGE (s)-[:BELONGS_TO_CATEGORY]->(c)
                    """
                    session.run(server_cypher, {
                        'server_id': server_id,
                        'category_id': category.id
                    })
    
    def create_relationship(self, relationship: ServerRelationship) -> None:
        """Create a relationship between two servers"""
        cypher = """
        MATCH (source:Server {id: $source_id})
        MATCH (target:Server {id: $target_id})
        MERGE (source)-[r:RELATES_TO {type: $relationship_type}]->(target)
        SET r.id = $relationship_id,
            r.confidence_score = $confidence_score,
            r.description = $description,
            r.evidence = $evidence,
            r.created_at = $created_at
        """
        
        with self.driver.session() as session:
            session.run(cypher, {
                'source_id': relationship.source_server_id,
                'target_id': relationship.target_server_id,
                'relationship_type': relationship.relationship_type.value,
                'relationship_id': relationship.id,
                'confidence_score': relationship.confidence_score,
                'description': relationship.description,
                'evidence': relationship.evidence,
                'created_at': relationship.created_at.isoformat()
            })
    
    def load_knowledge_graph(self, kg: KnowledgeGraph) -> None:
        """Load entire knowledge graph into Neo4j with enhanced progress tracking"""
        start_time = time.time()
        
        total_items = len(kg.servers) + len(kg.categories) + len(kg.relationships)
        print(f"📊 Loading knowledge graph: {total_items:,} total items ({len(kg.servers):,} servers, {len(kg.categories)} categories, {len(kg.relationships):,} relationships)")
        print(f"🎯 Target Neo4j instance: {self.instance}")
        print()
        
        # Step 1: Create constraints and indexes
        print("🔧 Creating constraints and indexes...")
        self.create_constraints_and_indexes()
        print("   ✅ Database schema ready")
        print()
        
        # Step 2: Load servers with enhanced progress
        if kg.servers:
            print(f"🗂️  Loading {len(kg.servers):,} servers...")
            
            # Enhanced progress bar for servers
            progress_bar = tqdm(
                kg.servers, 
                desc="📥 Servers", 
                unit="server",
                unit_scale=True,
                colour='blue',
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )
            
            for server in progress_bar:
                # Update progress description with current server
                progress_bar.set_postfix_str(f"Loading: {server.name[:30]}...")
                
                self.create_server_node(server)
                self.create_tool_nodes(server)
                self.create_resource_nodes(server)
            
            progress_bar.close()
            print(f"   ✅ {len(kg.servers):,} servers loaded successfully")
            print()
        
        # Step 3: Load categories with enhanced progress
        if kg.categories:
            print(f"📂 Loading {len(kg.categories)} categories...")
            
            progress_bar = tqdm(
                kg.categories, 
                desc="📁 Categories", 
                unit="category",
                colour='green',
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )
            
            for category in progress_bar:
                progress_bar.set_postfix_str(f"Loading: {category.name}")
                self.create_category_nodes([category])
            
            progress_bar.close()
            print(f"   ✅ {len(kg.categories)} categories loaded successfully")
            print()
        
        # Step 4: Load relationships with enhanced progress
        if kg.relationships:
            print(f"🔗 Loading {len(kg.relationships):,} relationships...")
            
            progress_bar = tqdm(
                kg.relationships, 
                desc="🔗 Relationships", 
                unit="relationship",
                colour='yellow',
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )
            
            for relationship in progress_bar:
                progress_bar.set_postfix_str(f"Type: {relationship.relationship_type.value}")
                self.create_relationship(relationship)
            
            progress_bar.close()
            print(f"   ✅ {len(kg.relationships):,} relationships loaded successfully")
            print()
        
        # Final summary
        elapsed_time = time.time() - start_time
        rate = total_items / elapsed_time if elapsed_time > 0 else 0
        
        print("=" * 60)
        print(f"✅ Knowledge graph loaded successfully!")
        print(f"⏱️  Total time: {elapsed_time:.1f}s")
        print(f"📈 Loading rate: {rate:.1f} items/second")
        print(f"🎯 Instance: {self.instance}")
        print("=" * 60)
    
    def get_servers_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all servers in a specific category"""
        cypher = """
        MATCH (s:Server)-[:BELONGS_TO_CATEGORY]->(c:Category {name: $category})
        RETURN s
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, {'category': category})
            return [record['s'] for record in result]
    
    def get_similar_servers(self, server_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find servers similar to the given server"""
        cypher = """
        MATCH (s1:Server {id: $server_id})
        MATCH (s2:Server)
        WHERE s1 <> s2
        WITH s1, s2,
             SIZE([cat IN s1.categories WHERE cat IN s2.categories]) as common_categories,
             SIZE([op IN s1.operations WHERE op IN s2.operations]) as common_operations,
             CASE WHEN s1.author = s2.author THEN 1 ELSE 0 END as same_author,
             CASE WHEN s1.implementation_language = s2.implementation_language THEN 1 ELSE 0 END as same_language
        WITH s2, (common_categories * 2 + common_operations + same_author + same_language) as similarity_score
        WHERE similarity_score > 0
        RETURN s2, similarity_score
        ORDER BY similarity_score DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, {'server_id': server_id, 'limit': limit})
            return [(record['s2'], record['similarity_score']) for record in result]
    
    def get_server_relationships(self, server_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for a server"""
        cypher = """
        MATCH (s:Server {id: $server_id})
        MATCH (s)-[r:RELATES_TO]-(other:Server)
        RETURN r, other
        ORDER BY r.confidence_score DESC
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, {'server_id': server_id})
            return [{'relationship': record['r'], 'server': record['other']} for record in result]
    
    def get_category_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics about categories"""
        cypher = """
        MATCH (c:Category)
        OPTIONAL MATCH (s:Server)-[:BELONGS_TO_CATEGORY]->(c)
        RETURN c.name as category_name,
               c.description as description,
               COUNT(s) as server_count
        ORDER BY server_count DESC
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            return [dict(record) for record in result]
    
    def get_popular_servers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular servers by popularity score"""
        cypher = """
        MATCH (s:Server)
        WHERE s.popularity_score IS NOT NULL
        RETURN s
        ORDER BY s.popularity_score DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, {'limit': limit})
            return [record['s'] for record in result]
    
    def search_servers(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search servers by name or description"""
        cypher = """
        MATCH (s:Server)
        WHERE toLower(s.name) CONTAINS toLower($query)
           OR toLower(s.description) CONTAINS toLower($query)
        RETURN s, 
               CASE 
                   WHEN toLower(s.name) CONTAINS toLower($query) THEN 2
                   ELSE 1
               END as relevance_score
        ORDER BY relevance_score DESC, s.popularity_score DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, {'query': query, 'limit': limit})
            return [record['s'] for record in result]


class RelationshipInferencer:
    """Infers relationships between MCP servers based on their properties"""
    
    def __init__(self, neo4j_manager: Neo4jManager):
        self.neo4j = neo4j_manager
    
    def infer_all_relationships(self, servers: List[MCPServer]) -> List[ServerRelationship]:
        """Infer relationships between all servers"""
        relationships = []
        
        for i, server1 in enumerate(servers):
            for server2 in servers[i+1:]:
                rels = self.infer_relationships(server1, server2)
                relationships.extend(rels)
        
        return relationships
    
    def infer_relationships(self, server1: MCPServer, server2: MCPServer) -> List[ServerRelationship]:
        """Infer relationships between two servers"""
        relationships = []
        
        # Same author relationship
        if server1.author and server2.author and server1.author == server2.author:
            relationships.append(ServerRelationship(
                id=f"{server1.id}_same_author_{server2.id}",
                source_server_id=server1.id,
                target_server_id=server2.id,
                relationship_type=RelationshipType.SAME_AUTHOR,
                confidence_score=1.0,
                description=f"Both servers created by {server1.author}",
                evidence=[f"Author: {server1.author}"],
                created_at=datetime.now()
            ))
        
        # Category similarity
        common_categories = set(server1.categories) & set(server2.categories)
        if common_categories:
            confidence = len(common_categories) / max(len(server1.categories), len(server2.categories))
            relationships.append(ServerRelationship(
                id=f"{server1.id}_similar_{server2.id}",
                source_server_id=server1.id,
                target_server_id=server2.id,
                relationship_type=RelationshipType.SIMILAR_FUNCTIONALITY,
                confidence_score=confidence,
                description=f"Share {len(common_categories)} common categories",
                evidence=[f"Common categories: {', '.join(cat.value for cat in common_categories)}"],
                created_at=datetime.now()
            ))
        
        # Operation similarity
        common_operations = set(server1.operations) & set(server2.operations)
        if common_operations and len(common_operations) >= 2:
            confidence = len(common_operations) / max(len(server1.operations), len(server2.operations))
            relationships.append(ServerRelationship(
                id=f"{server1.id}_complementary_{server2.id}",
                source_server_id=server1.id,
                target_server_id=server2.id,
                relationship_type=RelationshipType.COMPLEMENTARY,
                confidence_score=confidence * 0.8,  # Lower confidence than categories
                description=f"Share {len(common_operations)} common operations",
                evidence=[f"Common operations: {', '.join(op.value for op in common_operations)}"],
                created_at=datetime.now()
            ))
        
        # Language similarity (potential alternatives)
        if (server1.implementation_language and server2.implementation_language and
            server1.implementation_language == server2.implementation_language and
            common_categories):
            relationships.append(ServerRelationship(
                id=f"{server1.id}_alternative_{server2.id}",
                source_server_id=server1.id,
                target_server_id=server2.id,
                relationship_type=RelationshipType.ALTERNATIVE_TO,
                confidence_score=0.6,
                description=f"Alternative implementations in {server1.implementation_language}",
                evidence=[f"Same language: {server1.implementation_language}", "Similar categories"],
                created_at=datetime.now()
            ))
        
        return relationships