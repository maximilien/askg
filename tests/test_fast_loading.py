#!/usr/bin/env python3
"""
Test fast loading mode with a subset of servers
"""

import json
import asyncio
import pytest
from pathlib import Path
from datetime import datetime
from typing import List

from models import MCPServer, KnowledgeGraph, RegistrySource, OntologyCategory, ServerCategory
from deduplication import ServerDeduplicator
from neo4j_integration import Neo4jManager


def load_test_servers(count: int = 100) -> List[MCPServer]:
    """Load a test set of servers"""
    data_dir = Path("data/registries")
    servers = []
    
    # Load from mcp.so (largest dataset)
    mcp_so_dir = data_dir / "mcp.so"
    if mcp_so_dir.exists():
        json_files = list(mcp_so_dir.glob("*.json"))
        if json_files:
            latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            for i, server_data in enumerate(data.get('servers', [])):
                if i >= count:
                    break
                try:
                    server = MCPServer(**server_data)
                    servers.append(server)
                except Exception:
                    continue
    
    return servers


def check_neo4j_available():
    """Check if Neo4j is available for testing"""
    try:
        with Neo4jManager(instance="local") as neo4j:
            # Try a simple query to test connection
            with neo4j.driver.session() as session:
                session.run("RETURN 1 as test")
        return True
    except Exception:
        return False


async def test_loading_modes():
    """Test both standard and fast loading modes"""
    # Skip test if Neo4j is not available
    if not check_neo4j_available():
        pytest.skip("Neo4j not available - skipping Neo4j loading tests")
    
    print("🧪 Testing Neo4j loading modes...")
    
    # Load test servers
    test_servers = load_test_servers(200)
    print(f"📊 Loaded {len(test_servers)} test servers")
    
    # Deduplicate
    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(test_servers)
    print(f"🔧 After deduplication: {len(unique_servers)} unique servers")
    
    # Create test knowledge graph
    kg = KnowledgeGraph(
        created_at=datetime.now(),
        last_updated=datetime.now(),
        servers=unique_servers,
        relationships=[],
        categories=[],
        registry_snapshots=[]
    )
    
    # Test standard loading
    print("\n" + "="*60)
    print("🐌 Testing STANDARD loading mode...")
    print("="*60)
    
    try:
        with Neo4jManager(instance="local") as neo4j:
            neo4j.clear_database()
            neo4j.load_knowledge_graph(kg)
    except Exception as e:
        print(f"❌ Standard loading failed: {e}")
    
    # Test fast loading
    print("\n" + "="*60)
    print("⚡ Testing FAST loading mode...")
    print("="*60)
    
    try:
        with Neo4jManager(instance="local") as neo4j:
            neo4j.clear_database()
            neo4j.load_knowledge_graph_fast(kg, batch_size=50)
    except Exception as e:
        print(f"❌ Fast loading failed: {e}")
    
    # Verify final state
    print("\n🔍 Verifying final database state...")
    with Neo4jManager(instance="local") as neo4j:
        with neo4j.driver.session() as session:
            result = session.run("MATCH (s:Server) RETURN count(s) as count")
            count = result.single()["count"]
            print(f"✅ Final server count in Neo4j: {count}")


if __name__ == "__main__":
    asyncio.run(test_loading_modes())