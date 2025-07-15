#!/usr/bin/env python3
"""
Run deduplication on a sample of existing data for testing
"""

import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import List

from models import MCPServer, KnowledgeGraph, RegistrySource, OntologyCategory, ServerCategory
from deduplication import ServerDeduplicator
from neo4j_integration import Neo4jManager


def load_sample_servers(sample_size: int = 500) -> List[MCPServer]:
    """Load a sample of servers from existing registry data"""
    data_dir = Path("data/registries")
    all_servers = []
    
    # Track how many we've loaded from each registry
    registry_counts = {}
    
    for registry_dir in data_dir.iterdir():
        if not registry_dir.is_dir():
            continue
        
        registry_name = registry_dir.name
        json_files = list(registry_dir.glob("*.json"))
        
        if not json_files:
            continue
        
        # Get the latest file
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        
        print(f"Loading sample from {registry_name}: {latest_file.name}")
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        servers_from_registry = []
        for i, server_data in enumerate(data.get('servers', [])):
            # Take a sample from each registry
            if i >= sample_size // 4:  # Divide sample across registries
                break
                
            try:
                server = MCPServer(**server_data)
                servers_from_registry.append(server)
            except Exception as e:
                print(f"Error loading server from {registry_name}: {e}")
        
        registry_counts[registry_name] = len(servers_from_registry)
        all_servers.extend(servers_from_registry)
    
    print(f"\nSample loaded by registry:")
    for registry, count in registry_counts.items():
        print(f"  {registry}: {count}")
    
    return all_servers


def analyze_duplicates_preview(servers: List[MCPServer]):
    """Quickly analyze potential duplicates without full deduplication"""
    print("\n🔍 Quick duplicate analysis:")
    
    # Check repository URL duplicates
    repo_urls = {}
    for server in servers:
        if server.repository:
            url = str(server.repository).lower().rstrip('/').rstrip('.git')
            if url in repo_urls:
                repo_urls[url].append(server)
            else:
                repo_urls[url] = [server]
    
    repo_duplicates = {url: servers for url, servers in repo_urls.items() if len(servers) > 1}
    print(f"  Repository URL duplicates: {len(repo_duplicates)}")
    
    # Show a few examples
    if repo_duplicates:
        print("  Example repository duplicates:")
        for url, dups in list(repo_duplicates.items())[:3]:
            print(f"    {url}:")
            for server in dups:
                print(f"      {server.registry_source.value}: {server.name}")
    
    # Check name similarity
    names = {}
    for server in servers:
        if server.name:
            normalized = server.name.lower().replace('-', '').replace('_', '').replace(' ', '')
            if normalized in names:
                names[normalized].append(server)
            else:
                names[normalized] = [server]
    
    name_duplicates = {name: servers for name, servers in names.items() if len(servers) > 1}
    print(f"  Name duplicates: {len(name_duplicates)}")


async def main():
    """Main sample deduplication process"""
    parser = argparse.ArgumentParser(description="Run sample deduplication and test Neo4j")
    
    # Neo4j instance selection
    neo4j_group = parser.add_mutually_exclusive_group()
    neo4j_group.add_argument("--local", action="store_true", default=True,
                           help="Use local Neo4j instance (default)")
    neo4j_group.add_argument("--remote", action="store_true",
                           help="Use remote Neo4j instance")
    
    args = parser.parse_args()
    
    # Determine Neo4j instance
    neo4j_instance = "remote" if args.remote else "local"
    
    print("🔍 Loading sample server data...")
    print(f"🎯 Target Neo4j instance: {neo4j_instance}")
    
    # Load sample of servers
    sample_servers = load_sample_servers(500)
    print(f"📊 Sample servers loaded: {len(sample_servers)}")
    
    if not sample_servers:
        print("❌ No servers found!")
        return
    
    # Quick duplicate analysis
    analyze_duplicates_preview(sample_servers)
    
    # Run deduplication on sample
    print("\n🔧 Running deduplication on sample...")
    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(sample_servers)
    
    duplicates_found = len(sample_servers) - len(unique_servers)
    dedup_rate = (duplicates_found / len(sample_servers)) * 100 if sample_servers else 0
    
    print(f"   • Sample size: {len(sample_servers)}")
    print(f"   • Duplicates removed: {duplicates_found}")
    print(f"   • Unique servers: {len(unique_servers)}")
    print(f"   • Deduplication rate: {dedup_rate:.1f}%")
    
    # Show post-deduplication registry breakdown
    unique_registry_counts = {}
    for server in unique_servers:
        registry = server.registry_source.value
        unique_registry_counts[registry] = unique_registry_counts.get(registry, 0) + 1
    
    print("\n📦 Sample servers by registry (after deduplication):")
    for registry, count in sorted(unique_registry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {registry}: {count}")
    
    # Test Neo4j connection (without loading full data)
    print(f"\n🔌 Testing Neo4j connection ({neo4j_instance})...")
    try:
        with Neo4jManager(instance=neo4j_instance) as neo4j:
            # Just test the connection
            result = neo4j.driver.session().run("RETURN 1 as test")
            test_value = result.single()["test"]
            if test_value == 1:
                print("✅ Neo4j connection successful")
                
                # Load sample data
                print("📤 Loading sample data to Neo4j...")
                
                # Create simple knowledge graph with sample
                kg = KnowledgeGraph(
                    created_at=datetime.now(),
                    last_updated=datetime.now(),
                    servers=unique_servers[:50],  # Just first 50 for testing
                    relationships=[],
                    categories=[],
                    registry_snapshots=[]
                )
                
                # Clear and load sample
                neo4j.clear_database()
                neo4j.load_knowledge_graph(kg)
                
                print(f"✅ Loaded {len(kg.servers)} sample servers to Neo4j")
                
                # Test a query
                with neo4j.driver.session() as session:
                    result = session.run("MATCH (s:Server) RETURN count(s) as count")
                    count = result.single()["count"]
                    print(f"🔍 Neo4j query test: {count} servers found")
            
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("Make sure Neo4j is running with credentials: neo4j/mcpservers")
    
    print(f"\n📈 Estimated full dataset results:")
    total_estimate = len(sample_servers) * 8  # Rough estimate based on sample
    unique_estimate = total_estimate * (len(unique_servers) / len(sample_servers))
    print(f"  Estimated total servers: ~{total_estimate}")
    print(f"  Estimated unique after dedup: ~{int(unique_estimate)}")
    print(f"  Estimated duplicates: ~{int(total_estimate - unique_estimate)}")
    
    print("\n🎉 Sample deduplication completed!")


if __name__ == "__main__":
    asyncio.run(main())