#!/usr/bin/env python3
"""Smart Neo4j loader that uses master data when available and current.

This script:
1. Checks if master data exists and is newer than registry data
2. If current master data exists, loads it directly to Neo4j
3. If master data is outdated/missing, runs full deduplication and saves new master data
4. Supports both local and remote Neo4j instances with fast/standard loading
"""

import argparse
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List

from deduplication import ServerDeduplicator
from master_data import MasterDataManager
from models import KnowledgeGraph, MCPServer, OntologyCategory, ServerCategory
from neo4j_integration import Neo4jManager


def load_all_registry_servers() -> list[MCPServer]:
    """Load all servers from existing registry data"""
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
            import json
            with open(latest_file) as f:
                data = json.load(f)

            servers_from_registry = []
            for server_data in data.get("servers", []):
                try:
                    server = MCPServer(**server_data)
                    servers_from_registry.append(server)
                except Exception:
                    continue

            registry_counts[registry_name] = len(servers_from_registry)
            all_servers.extend(servers_from_registry)
            print(f"   ✅ Loaded {len(servers_from_registry):,} servers")

        except Exception as e:
            print(f"   ❌ Failed to load {registry_name}: {e}")

    print(f"\n📊 Total servers loaded: {len(all_servers):,}")
    for registry, count in sorted(registry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {registry}: {count:,}")

    return all_servers


def create_basic_categories() -> list[OntologyCategory]:
    """Create basic ontology categories"""
    categories = []

    category_definitions = [
        ("database", "Database Systems", "Servers that interact with databases and data storage"),
        ("file_system", "File System Operations", "Servers that work with files and directories"),
        ("api_integration", "API Integration", "Servers that integrate with external APIs"),
        ("development_tools", "Development Tools", "Servers that support software development"),
        ("data_processing", "Data Processing", "Servers that process and transform data"),
        ("cloud_services", "Cloud Services", "Servers that integrate with cloud platforms"),
        ("communication", "Communication", "Servers that handle messaging and notifications"),
        ("authentication", "Authentication", "Servers that handle authentication and security"),
        ("monitoring", "Monitoring", "Servers that monitor systems and applications"),
        ("search", "Search", "Servers that provide search capabilities"),
        ("ai_ml", "AI/ML", "Servers that provide AI and machine learning capabilities"),
        ("other", "Other", "Servers that don't fit into other categories"),
    ]

    for cat_id, name, description in category_definitions:
        category = OntologyCategory(
            id=cat_id,
            name=name,
            description=description,
        )
        categories.append(category)

    return categories


def assign_servers_to_categories(servers: list[MCPServer], categories: list[OntologyCategory]):
    """Assign servers to categories based on their category enums"""
    # Reset server lists
    for category in categories:
        category.servers = []

    # Map category enum values to category objects
    category_map = {cat.id: cat for cat in categories}

    for server in servers:
        for server_category in server.categories:
            category_id = server_category.value
            if category_id in category_map:
                category_map[category_id].servers.append(server.id)


async def run_full_deduplication_pipeline(master_manager: MasterDataManager) -> KnowledgeGraph:
    """Run the complete deduplication pipeline and save master data"""
    print("🔄 Running full deduplication pipeline...")

    # Load all registry data
    all_servers = load_all_registry_servers()

    if not all_servers:
        raise ValueError("No servers found in registry data!")

    # Run deduplication
    print(f"\n🔧 Starting deduplication of {len(all_servers):,} servers...")
    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(all_servers)

    print(f"✅ Deduplication complete: {len(unique_servers):,} unique servers")

    # Create categories and assign servers
    print("\n📂 Creating and assigning categories...")
    categories = create_basic_categories()
    assign_servers_to_categories(unique_servers, categories)

    # Print category statistics
    print("📊 Category assignments:")
    for category in categories:
        if category.servers:
            print(f"   • {category.name}: {len(category.servers)} servers")

    # Save master data
    print("\n💾 Saving master data...")
    master_file = master_manager.save_master_data(unique_servers, categories)

    # Clean up old master data files
    master_manager.cleanup_old_master_data(keep_count=3)

    # Create knowledge graph
    kg = KnowledgeGraph(
        created_at=datetime.now(),
        last_updated=datetime.now(),
        servers=unique_servers,
        relationships=[],  # Can be added later
        categories=categories,
        registry_snapshots=[],
    )

    return kg


async def load_to_neo4j(kg: KnowledgeGraph, neo4j_instance: str, fast_mode: bool, batch_size: int):
    """Load knowledge graph to Neo4j"""
    mode_str = "fast mode" if fast_mode else "standard mode"
    print(f"\n📤 Loading to Neo4j ({neo4j_instance}, {mode_str})...")

    try:
        with Neo4jManager(instance=neo4j_instance) as neo4j:
            # Clear existing data
            print("🗑️  Clearing existing Neo4j data...")
            neo4j.clear_database()

            # Load data
            if fast_mode:
                neo4j.load_knowledge_graph_fast(kg, batch_size=batch_size)
            else:
                neo4j.load_knowledge_graph(kg)

        print(f"✅ Successfully loaded {len(kg.servers):,} servers to Neo4j ({neo4j_instance})")

        # Verify loading
        print("\n🔍 Verifying data in Neo4j...")
        with Neo4jManager(instance=neo4j_instance) as neo4j:
            with neo4j.driver.session() as session:
                result = session.run("MATCH (s:Server) RETURN count(s) as count")
                count = result.single()["count"]
                print(f"   📊 Servers in Neo4j: {count:,}")

                result = session.run("MATCH (c:Category) RETURN count(c) as count")
                category_count = result.single()["count"]
                print(f"   📁 Categories in Neo4j: {category_count}")

    except Exception as e:
        print(f"❌ Error loading to Neo4j: {e}")
        raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Smart Neo4j loader with master data support")

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

    # Master data options
    parser.add_argument("--force-rebuild", action="store_true",
                       help="Force rebuild of master data even if current")
    parser.add_argument("--status-only", action="store_true",
                       help="Only show master data status, don't load")

    args = parser.parse_args()

    # Determine Neo4j instance
    neo4j_instance = "remote" if args.remote else "local"

    print("🚀 Smart Neo4j Loader with Master Data")
    print(f"🎯 Target Neo4j instance: {neo4j_instance}")
    if args.fast:
        print(f"⚡ Fast mode enabled (batch size: {args.batch_size})")
    print()

    # Initialize master data manager
    master_manager = MasterDataManager()

    # Show status
    master_manager.print_status()

    if args.status_only:
        print("\n📊 Status check complete.")
        return

    print()

    try:
        # Check if we can use existing master data
        is_current, info = master_manager.is_master_data_current()

        if is_current and not args.force_rebuild:
            print("✅ Using current master data (skipping deduplication)")
            kg = master_manager.create_knowledge_graph_from_master()

            if kg is None:
                print("❌ Failed to load master data, falling back to full pipeline")
                kg = await run_full_deduplication_pipeline(master_manager)
        else:
            if args.force_rebuild:
                print("🔄 Force rebuild requested")
            else:
                print("⚠️  Master data is outdated or missing")

            kg = await run_full_deduplication_pipeline(master_manager)

        # Load to Neo4j
        await load_to_neo4j(kg, neo4j_instance, args.fast, args.batch_size)

        # Show example queries
        print(f"\n🔍 Example Neo4j queries for your {len(kg.servers):,} servers:")
        print("   MATCH (s:Server) WHERE 'database' IN s.categories RETURN s.name LIMIT 10")
        print("   MATCH (s:Server) RETURN s.registry_source, count(s) ORDER BY count(s) DESC")
        print("   MATCH (s:Server) WHERE s.popularity_score IS NOT NULL RETURN s.name, s.popularity_score ORDER BY s.popularity_score DESC LIMIT 10")

        print("\n🎉 Loading complete! Access Neo4j at:")
        if neo4j_instance == "local":
            print("   Browser: http://localhost:7474")
            print("   Bolt: bolt://localhost:7687")
        else:
            print("   Remote instance as configured")

    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
