#!/usr/bin/env python3
"""
Run deduplication on existing data and load to Neo4j
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List

from models import MCPServer, KnowledgeGraph, RegistrySource, OntologyCategory, ServerCategory
from deduplication import ServerDeduplicator
from neo4j_integration import Neo4jManager


def load_all_existing_servers() -> List[MCPServer]:
    """Load all servers from existing registry data"""
    data_dir = Path("data/registries")
    all_servers = []
    
    for registry_dir in data_dir.iterdir():
        if not registry_dir.is_dir():
            continue
        
        registry_name = registry_dir.name
        json_files = list(registry_dir.glob("*.json"))
        
        if not json_files:
            continue
        
        # Get the latest file
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        
        print(f"Loading from {registry_name}: {latest_file.name}")
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        for server_data in data.get('servers', []):
            try:
                server = MCPServer(**server_data)
                all_servers.append(server)
            except Exception as e:
                print(f"Error loading server from {registry_name}: {e}")
    
    return all_servers


def create_basic_ontology_categories() -> List[OntologyCategory]:
    """Create basic ontology categories"""
    categories = []
    
    database_cat = OntologyCategory(
        id="database",
        name="Database Systems",
        description="Servers that interact with databases and data storage systems"
    )
    
    filesystem_cat = OntologyCategory(
        id="file_system", 
        name="File System Operations",
        description="Servers that work with files and directories"
    )
    
    api_cat = OntologyCategory(
        id="api_integration",
        name="API Integration", 
        description="Servers that integrate with external APIs"
    )
    
    dev_tools_cat = OntologyCategory(
        id="development_tools",
        name="Development Tools",
        description="Servers that support software development"
    )
    
    categories.extend([database_cat, filesystem_cat, api_cat, dev_tools_cat])
    return categories


async def main():
    """Main deduplication and loading process"""
    print("🔍 Loading existing server data...")
    
    # Load all existing servers
    all_servers = load_all_existing_servers()
    print(f"📊 Total servers loaded: {len(all_servers)}")
    
    if not all_servers:
        print("❌ No servers found!")
        return
    
    # Show registry breakdown
    registry_counts = {}
    for server in all_servers:
        registry = server.registry_source.value
        registry_counts[registry] = registry_counts.get(registry, 0) + 1
    
    print("\n📦 Servers by Registry (before deduplication):")
    for registry, count in sorted(registry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {registry}: {count}")
    
    # Run deduplication
    print("\n🔧 Starting deduplication process...")
    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(all_servers)
    
    duplicates_found = len(all_servers) - len(unique_servers)
    print(f"   • Duplicates removed: {duplicates_found}")
    print(f"   • Unique servers: {len(unique_servers)}")
    
    # Show post-deduplication registry breakdown
    unique_registry_counts = {}
    for server in unique_servers:
        registry = server.registry_source.value
        unique_registry_counts[registry] = unique_registry_counts.get(registry, 0) + 1
    
    print("\n📦 Servers by Registry (after deduplication):")
    for registry, count in sorted(unique_registry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {registry}: {count}")
    
    # Create categories and assign servers
    print("\n📂 Creating ontology categories...")
    categories = create_basic_ontology_categories()
    
    for category in categories:
        try:
            category_enum = ServerCategory(category.id)
            for server in unique_servers:
                if category_enum in server.categories:
                    category.servers.append(server.id)
        except ValueError:
            continue
    
    # Create knowledge graph
    kg = KnowledgeGraph(
        created_at=datetime.now(),
        last_updated=datetime.now(),
        servers=unique_servers,
        relationships=[],  # We'll skip relationship inference for now
        categories=categories,
        registry_snapshots=[]
    )
    
    # Load into Neo4j
    print("\n📤 Loading deduplicated data into Neo4j...")
    try:
        with Neo4jManager() as neo4j:
            # Clear existing data
            print("🗑️  Clearing existing Neo4j data...")
            neo4j.clear_database()
            
            # Load new data
            neo4j.load_knowledge_graph(kg)
            
        print(f"✅ Successfully loaded {len(unique_servers)} unique servers into Neo4j")
        
        # Print some example queries
        print("\n🔍 Example Neo4j queries you can run:")
        print("  - Find all servers: MATCH (s:Server) RETURN s LIMIT 10")
        print("  - Find database servers: MATCH (s:Server) WHERE 'database' IN s.categories RETURN s.name, s.description")
        print("  - Registry distribution: MATCH (s:Server) RETURN s.registry_source, count(s) ORDER BY count(s) DESC")
        print("  - Popular servers: MATCH (s:Server) WHERE s.popularity_score IS NOT NULL RETURN s.name, s.popularity_score ORDER BY s.popularity_score DESC LIMIT 10")
        
    except Exception as e:
        print(f"❌ Error loading to Neo4j: {e}")
        print("Make sure Neo4j is running with the correct credentials in config.yaml")
    
    print("\n🎉 Deduplication and loading completed!")


if __name__ == "__main__":
    asyncio.run(main())