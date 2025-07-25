#!/usr/bin/env python3
"""
Test global ID generation and deduplication with mock data
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from models import MCPServer, RegistrySource
from id_standardization import batch_convert_to_global_ids, GlobalIDGenerator
from deduplication import ServerDeduplicator


def create_mock_snapshots() -> Dict[str, List[MCPServer]]:
    """Create mock snapshots for testing instead of loading from files"""
    snapshots = {}
    
    # Create mock servers for different registries
    registries = {
        "glama": [
            MCPServer(
                id="glama_1",
                name="Test Server 1",
                description="Test server from Glama",
                author="Test Author",
                version="1.0.0",
                repository="https://github.com/test/server-1",
                implementation_language="Python",
                categories=["database"],
                operations=["read"],
                registry_source=RegistrySource.GLAMA,
                popularity_score=100,
                last_updated=datetime.now(),
                installation_command="pip install test-server-1",
                download_count=1000
            ),
            MCPServer(
                id="glama_2",
                name="Test Server 2", 
                description="Another test server from Glama",
                author="Test Author 2",
                version="1.0.0",
                repository="https://github.com/test/server-2",
                implementation_language="TypeScript",
                categories=["api_integration"],
                operations=["write"],
                registry_source=RegistrySource.GLAMA,
                popularity_score=50,
                last_updated=datetime.now(),
                installation_command="npm install test-server-2",
                download_count=500
            )
        ],
        "mcp.so": [
            MCPServer(
                id="mcpso_1",
                name="Test Server 1",  # Same name as Glama server
                description="Test server from MCP.so",
                author="Test Author",
                version="1.0.0",
                repository="https://github.com/test/server-1",  # Same repo as Glama
                implementation_language="Python",
                categories=["database"],
                operations=["read"],
                registry_source=RegistrySource.MCP_SO,
                popularity_score=75,
                last_updated=datetime.now(),
                installation_command="pip install test-server-1",
                download_count=750
            )
        ]
    }
    
    for registry_name, servers in registries.items():
        snapshots[registry_name] = servers
        print(f"Created {len(servers)} mock servers for {registry_name}")
    
    return snapshots


def test_global_id_generation():
    """Test global ID generation on mock data"""
    
    print("🔍 TESTING GLOBAL ID GENERATION")
    print("=" * 50)
    
    # Create mock data
    snapshots = create_mock_snapshots()
    
    # Combine all servers
    all_servers = []
    for servers in snapshots.values():
        all_servers.extend(servers)
    
    print(f"📊 Original data: {len(all_servers)} servers with registry-specific IDs")
    
    # Convert to global IDs
    global_servers = batch_convert_to_global_ids(all_servers)
    
    print(f"\n🔧 Testing deduplication with global IDs...")
    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(global_servers)
    
    print(f"   • Before deduplication: {len(global_servers)} servers")
    print(f"   • After deduplication: {len(unique_servers)} servers")
    print(f"   • Duplicates removed: {len(global_servers) - len(unique_servers)}")
    
    # Analyze duplicate detection with global IDs
    print(f"\n🔍 Global ID Duplicate Analysis:")
    
    # Find exact ID matches (should be rare now)
    id_counts = {}
    for server in global_servers:
        id_counts[server.id] = id_counts.get(server.id, 0) + 1
    
    exact_duplicates = {id_: count for id_, count in id_counts.items() if count > 1}
    
    if exact_duplicates:
        print(f"   ⚠️  Exact ID duplicates found:")
        for id_, count in exact_duplicates.items():
            print(f"     - {id_}: {count} instances")
    else:
        print(f"   ✅ No exact ID duplicates found")
    
    # Show examples of different ID types
    print(f"\n📝 Sample Global IDs by Type:")
    
    repo_based = [s for s in global_servers if '/' in s.id]
    name_based = [s for s in global_servers if '/' not in s.id and s.id != s.name]
    
    if repo_based:
        print(f"   • Repository-based IDs ({len(repo_based)}):")
        for server in repo_based[:3]:
            print(f"     - {server.id} (from {server.registry_source})")
    
    if name_based:
        print(f"   • Name-based IDs ({len(name_based)}):")
        for server in name_based[:3]:
            print(f"     - {server.id} (from {server.registry_source})")
    
    # Test that duplicates are properly merged
    expected_unique = 2  # We have 2 unique servers (same repo, different names)
    assert len(unique_servers) == expected_unique, f"Expected {expected_unique} unique servers, got {len(unique_servers)}"
    
    print(f"\n✅ Global ID generation and deduplication test passed!")


def test_id_stability():
    """Test that global IDs are stable across multiple runs"""
    print(f"\n🔄 TESTING ID STABILITY")
    print("=" * 50)
    
    snapshots = create_mock_snapshots()
    all_servers = []
    for servers in snapshots.values():
        all_servers.extend(servers)
    
    # Convert to global IDs multiple times
    global_servers_1 = batch_convert_to_global_ids(all_servers)
    global_servers_2 = batch_convert_to_global_ids(all_servers)
    
    # Check that IDs are stable
    for i, (server1, server2) in enumerate(zip(global_servers_1, global_servers_2)):
        assert server1.id == server2.id, f"ID not stable for server {i}: {server1.id} != {server2.id}"
    
    print(f"✅ Global IDs are stable across multiple runs")


if __name__ == "__main__":
    test_global_id_generation()
    test_id_stability()