#!/usr/bin/env python3
"""Run full deduplication on all existing data and load to Neo4j
"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List

from deduplication import ServerDeduplicator
from models import (
    KnowledgeGraph,
    MCPServer,
    OntologyCategory,
    RegistrySource,
    ServerCategory,
)
from neo4j_integration import Neo4jManager


def load_all_servers_efficiently() -> list[MCPServer]:
    """Load all servers from existing registry data efficiently"""
    data_dir = Path("data/registries")
    all_servers = []

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

        print(f"📁 Loading {registry_name}: {latest_file.name}")

        try:
            with open(latest_file) as f:
                data = json.load(f)

            servers_from_registry = []
            for server_data in data.get("servers", []):
                try:
                    server = MCPServer(**server_data)
                    servers_from_registry.append(server)
                except Exception:
                    # Skip invalid servers but don't print every error
                    continue

            registry_counts[registry_name] = len(servers_from_registry)
            all_servers.extend(servers_from_registry)
            print(f"   ✅ Loaded {len(servers_from_registry)} servers")

        except Exception as e:
            print(f"   ❌ Failed to load {registry_name}: {e}")

    print("\n📊 Total servers loaded by registry:")
    for registry, count in sorted(registry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {registry}: {count:,}")

    return all_servers


async def main():
    """Main full deduplication and loading process"""
    parser = argparse.ArgumentParser(description="Run full deduplication and load to Neo4j")

    # Neo4j instance selection
    neo4j_group = parser.add_mutually_exclusive_group()
    neo4j_group.add_argument("--local", action="store_true", default=True,
                           help="Use local Neo4j instance (default)")
    neo4j_group.add_argument("--remote", action="store_true",
                           help="Use remote Neo4j instance")

    # Performance options
    parser.add_argument("--fast", action="store_true",
                       help="Use fast batch loading for better performance")
    parser.add_argument("--batch-size", type=int, default=500,
                       help="Batch size for fast loading (default: 500)")

    args = parser.parse_args()

    # Determine Neo4j instance
    neo4j_instance = "remote" if args.remote else "local"

    print("🚀 Starting full deduplication and Neo4j loading...")
    print(f"🎯 Target Neo4j instance: {neo4j_instance}")
    if args.fast:
        print(f"⚡ Fast mode enabled with batch size: {args.batch_size}")
    print("⏱️  This may take a few minutes for the complete dataset...\n")

    # Load all servers
    print("🔍 Loading all server data...")
    all_servers = load_all_servers_efficiently()
    print(f"\n📊 Total servers loaded: {len(all_servers):,}")

    if not all_servers:
        print("❌ No servers found!")
        return

    # Run deduplication
    print("\n🔧 Running deduplication on full dataset...")
    print("   This is the most time-intensive step...")

    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(all_servers)

    duplicates_found = len(all_servers) - len(unique_servers)
    dedup_rate = (duplicates_found / len(all_servers)) * 100 if all_servers else 0

    print("\n📈 Deduplication Results:")
    print(f"   • Total input servers: {len(all_servers):,}")
    print(f"   • Duplicates removed: {duplicates_found:,}")
    print(f"   • Unique servers: {len(unique_servers):,}")
    print(f"   • Deduplication rate: {dedup_rate:.1f}%")

    # Show post-deduplication registry breakdown
    unique_registry_counts = {}
    for server in unique_servers:
        registry = server.registry_source.value
        unique_registry_counts[registry] = unique_registry_counts.get(registry, 0) + 1

    print("\n📦 Unique servers by registry:")
    for registry, count in sorted(unique_registry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {registry}: {count:,}")

    # Create basic categories
    print("\n📂 Creating basic ontology categories...")
    categories = []

    # Create basic categories and assign servers
    for category_enum in ServerCategory:
        category = OntologyCategory(
            id=category_enum.value,
            name=category_enum.value.replace("_", " ").title(),
            description=f"Servers in the {category_enum.value} category",
        )

        # Find servers in this category
        for server in unique_servers:
            if category_enum in server.categories:
                category.servers.append(server.id)

        if category.servers:  # Only add categories that have servers
            categories.append(category)
            print(f"   📁 {category.name}: {len(category.servers)} servers")

    # Create knowledge graph
    print("\n🏗️  Creating knowledge graph...")
    kg = KnowledgeGraph(
        created_at=datetime.now(),
        last_updated=datetime.now(),
        servers=unique_servers,
        relationships=[],  # Skip relationships for now - can be added later
        categories=categories,
        registry_snapshots=[],
    )

    # Load into Neo4j
    print(f"\n📤 Loading complete dataset into Neo4j ({neo4j_instance})...")
    try:
        with Neo4jManager(instance=neo4j_instance) as neo4j:
            # Clear existing data
            print("🗑️  Clearing existing Neo4j data...")
            neo4j.clear_database()

            # Load new data
            if args.fast:
                print(f"📊 Fast loading deduplicated servers (batch size: {args.batch_size})...")
                neo4j.load_knowledge_graph_fast(kg, batch_size=args.batch_size)
            else:
                print("📊 Loading deduplicated servers...")
                neo4j.load_knowledge_graph(kg)

        print(f"\n✅ Successfully loaded {len(unique_servers):,} unique servers into Neo4j ({neo4j_instance})!")

        # Verify loading with test queries
        print(f"\n🔍 Verifying data in Neo4j ({neo4j_instance})...")
        with Neo4jManager(instance=neo4j_instance) as neo4j:
            with neo4j.driver.session() as session:
                # Count servers
                result = session.run("MATCH (s:Server) RETURN count(s) as count")
                server_count = result.single()["count"]
                print(f"   📊 Servers in Neo4j: {server_count:,}")

                # Count categories
                result = session.run("MATCH (c:Category) RETURN count(c) as count")
                category_count = result.single()["count"]
                print(f"   📁 Categories in Neo4j: {category_count}")

                # Sample popular servers
                result = session.run("""
                    MATCH (s:Server) 
                    WHERE s.popularity_score IS NOT NULL 
                    RETURN s.name, s.popularity_score 
                    ORDER BY s.popularity_score DESC 
                    LIMIT 5
                """)
                popular_servers = result.data()
                if popular_servers:
                    print("   🌟 Top popular servers:")
                    for server in popular_servers:
                        print(f"      {server['s.name']} (score: {server['s.popularity_score']})")

        # Print example queries
        print(f"\n🔍 Example Neo4j queries for your {len(unique_servers):,} servers:")
        print("   # Find all database servers")
        print("   MATCH (s:Server) WHERE 'database' IN s.categories RETURN s.name, s.description LIMIT 10")
        print("\n   # Registry distribution")
        print("   MATCH (s:Server) RETURN s.registry_source, count(s) ORDER BY count(s) DESC")
        print("\n   # Popular servers")
        print("   MATCH (s:Server) WHERE s.popularity_score IS NOT NULL RETURN s.name, s.popularity_score ORDER BY s.popularity_score DESC LIMIT 20")
        print("\n   # Find servers by author")
        print("   MATCH (s:Server) WHERE s.author CONTAINS 'anthropic' RETURN s.name, s.description")
        print("\n   # Category breakdown")
        print("   MATCH (c:Category)<-[:BELONGS_TO_CATEGORY]-(s:Server) RETURN c.name, count(s) ORDER BY count(s) DESC")

    except Exception as e:
        print(f"❌ Error loading to Neo4j: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 Full deduplication and Neo4j loading completed!")
    print(f"📊 Final result: {len(unique_servers):,} unique MCP servers loaded into Neo4j")


if __name__ == "__main__":
    asyncio.run(main())
