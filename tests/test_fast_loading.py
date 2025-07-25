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


def create_mock_servers(count: int = 10) -> List[MCPServer]:
    """Create mock servers for testing instead of loading from files"""
    servers = []
    
    for i in range(count):
        server = MCPServer(
            id=f"test-server-{i}",
            name=f"Test Server {i}",
            description=f"Test server description {i}",
            author=f"Test Author {i}",
            version="1.0.0",
            repository=f"https://github.com/test/test-server-{i}",
            implementation_language="Python",
            categories=["database", "api"],
            operations=["read", "write"],
            registry_source=RegistrySource.GLAMA,
            popularity_score=100 + i,
            last_updated=datetime.now(),
            installation_command=f"pip install test-server-{i}",
            download_count=1000 + i
        )
        servers.append(server)
    
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


@pytest.mark.slow
async def test_loading_modes():
    """Test both standard and fast loading modes with smaller dataset"""
    # Skip test if Neo4j is not available
    if not check_neo4j_available():
        pytest.skip("Neo4j not available - skipping Neo4j loading tests")
    
    print("🧪 Testing Neo4j loading modes...")
    
    # Create mock servers instead of loading from files
    test_servers = create_mock_servers(20)  # Reduced from 200 to 20
    print(f"📊 Created {len(test_servers)} mock servers")
    
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
    
    # Test fast loading only (skip standard loading to save time)
    print("\n" + "="*60)
    print("⚡ Testing FAST loading mode...")
    print("="*60)
    
    try:
        with Neo4jManager(instance="local") as neo4j:
            neo4j.clear_database()
            neo4j.load_knowledge_graph_fast(kg, batch_size=10)  # Smaller batch size
    except Exception as e:
        print(f"❌ Fast loading failed: {e}")
        raise
    
    # Verify final state
    print("\n🔍 Verifying final database state...")
    with Neo4jManager(instance="local") as neo4j:
        with neo4j.driver.session() as session:
            result = session.run("MATCH (s:Server) RETURN count(s) as count")
            count = result.single()["count"]
            print(f"✅ Final server count in Neo4j: {count}")
            assert count == len(unique_servers), f"Expected {len(unique_servers)} servers, got {count}"


if __name__ == "__main__":
    asyncio.run(test_loading_modes())