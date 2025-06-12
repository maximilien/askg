#!/usr/bin/env python3
"""
MCP Agent-Server Knowledge Graph Builder

This script orchestrates the building of a comprehensive knowledge graph
of MCP (Model Context Protocol) servers from various registries.
"""

import asyncio
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List

from models import KnowledgeGraph, OntologyCategory, ServerCategory
from scrapers import ScrapingOrchestrator, RegistrySource
from neo4j_integration import Neo4jManager, RelationshipInferencer
from deduplication import ServerDeduplicator


def create_ontology_categories() -> List[OntologyCategory]:
    """Create predefined ontology categories for MCP servers"""
    categories = []
    
    # Root categories
    database_cat = OntologyCategory(
        id="database",
        name="Database Systems",
        description="Servers that interact with databases and data storage systems",
        data_domains=["sql", "nosql", "key-value", "document", "graph"],
        operational_patterns=["query", "crud", "transaction", "migration"],
        integration_patterns=["connection-pool", "orm", "raw-sql"]
    )
    
    filesystem_cat = OntologyCategory(
        id="filesystem",
        name="File System Operations",
        description="Servers that work with files, directories, and file system operations",
        data_domains=["text", "binary", "structured", "media"],
        operational_patterns=["read", "write", "search", "watch", "sync"],
        integration_patterns=["local-fs", "cloud-storage", "version-control"]
    )
    
    api_cat = OntologyCategory(
        id="api_integration",
        name="API Integration",
        description="Servers that integrate with external APIs and web services",
        data_domains=["rest", "graphql", "soap", "webhooks"],
        operational_patterns=["request", "response", "polling", "streaming"],
        integration_patterns=["oauth", "api-key", "jwt", "rate-limiting"]
    )
    
    dev_tools_cat = OntologyCategory(
        id="development_tools",
        name="Development Tools",
        description="Servers that support software development workflows",
        data_domains=["code", "documentation", "builds", "deployments"],
        operational_patterns=["analyze", "transform", "build", "test", "deploy"],
        integration_patterns=["git", "ci-cd", "package-managers", "ide"]
    )
    
    data_processing_cat = OntologyCategory(
        id="data_processing",
        name="Data Processing",
        description="Servers that process, transform, and analyze data",
        data_domains=["structured", "unstructured", "streams", "batches"],
        operational_patterns=["extract", "transform", "load", "analyze", "aggregate"],
        integration_patterns=["etl-pipelines", "streaming", "batch-processing"]
    )
    
    cloud_cat = OntologyCategory(
        id="cloud_services",
        name="Cloud Services",
        description="Servers that integrate with cloud platforms and services",
        data_domains=["infrastructure", "compute", "storage", "networking"],
        operational_patterns=["provision", "scale", "monitor", "backup"],
        integration_patterns=["aws", "azure", "gcp", "kubernetes"]
    )
    
    communication_cat = OntologyCategory(
        id="communication",
        name="Communication",
        description="Servers that handle messaging, notifications, and communication",
        data_domains=["messages", "notifications", "emails", "chats"],
        operational_patterns=["send", "receive", "broadcast", "queue"],
        integration_patterns=["slack", "discord", "email", "sms", "webhooks"]
    )
    
    categories.extend([
        database_cat, filesystem_cat, api_cat, dev_tools_cat,
        data_processing_cat, cloud_cat, communication_cat
    ])
    
    return categories


async def build_knowledge_graph(force_refresh: bool = False, registries: List[str] = None, neo4j_instance: str = "local") -> KnowledgeGraph:
    """Build the complete knowledge graph"""
    pipeline_start = time.time()
    print("🚀 Starting MCP Knowledge Graph construction...")
    
    # Initialize scraping orchestrator
    orchestrator = ScrapingOrchestrator()
    
    # Determine which registries to scrape
    if registries:
        registry_sources = [RegistrySource(reg) for reg in registries if reg in [r.value for r in RegistrySource]]
    else:
        registry_sources = list(RegistrySource)
    
    print(f"📋 Target registries: {[r.value for r in registry_sources]}")
    
    # Scrape all registries
    scraping_start = time.time()
    snapshots = []
    for registry in registry_sources:
        snapshot = await orchestrator.scrape_registry(registry, force_refresh)
        if snapshot:
            snapshots.append(snapshot)
    
    scraping_time = time.time() - scraping_start
    
    # Combine all servers
    all_servers = []
    for snapshot in snapshots:
        all_servers.extend(snapshot.servers)
    
    print(f"\n📊 Scraping Summary:")
    print(f"   • Total servers found: {len(all_servers)}")
    print(f"   • Scraping time: {scraping_time:.1f}s")
    print(f"   • Rate: {len(all_servers)/scraping_time:.1f} servers/sec")
    
    # Robust deduplication using multiple criteria
    print("\n🔧 Starting deduplication process...")
    dedup_start = time.time()
    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(all_servers)
    dedup_time = time.time() - dedup_start
    
    duplicates_found = len(all_servers) - len(unique_servers)
    print(f"   • Duplicates removed: {duplicates_found}")
    print(f"   • Unique servers: {len(unique_servers)}")
    print(f"   • Deduplication time: {dedup_time:.1f}s")
    
    # Create ontology categories
    print("\n📂 Creating ontology categories...")
    categories = create_ontology_categories()
    
    # Assign servers to categories
    categorization_start = time.time()
    for category in categories:
        category_enum = None
        try:
            category_enum = ServerCategory(category.id)
        except ValueError:
            continue
        
        for server in unique_servers:
            if category_enum in server.categories:
                category.servers.append(server.id)
    
    categorization_time = time.time() - categorization_start
    print(f"   • Categorization time: {categorization_time:.1f}s")
    
    # Infer relationships between servers
    print("\n🔗 Inferring relationships between servers...")
    relationships_start = time.time()
    with Neo4jManager(instance=neo4j_instance) as neo4j:
        inferencer = RelationshipInferencer(neo4j)
        relationships = inferencer.infer_all_relationships(unique_servers)
    
    relationships_time = time.time() - relationships_start
    print(f"   • Relationships generated: {len(relationships)}")
    print(f"   • Relationship inference time: {relationships_time:.1f}s")
    
    # Create knowledge graph
    kg = KnowledgeGraph(
        created_at=datetime.now(),
        last_updated=datetime.now(),
        servers=unique_servers,
        relationships=relationships,
        categories=categories,
        registry_snapshots=snapshots
    )
    
    total_time = time.time() - pipeline_start
    print(f"\n⏱️  Total pipeline time: {total_time:.1f}s")
    print(f"📈 Processing rate: {len(unique_servers)/total_time:.1f} servers/sec")
    
    return kg


async def load_to_neo4j(kg: KnowledgeGraph, neo4j_instance: str = "local", fast_mode: bool = False, batch_size: int = 500):
    """Load knowledge graph into Neo4j"""
    loading_start = time.time()
    mode_str = "fast mode" if fast_mode else "standard mode"
    print(f"\n📤 Loading knowledge graph into Neo4j ({neo4j_instance}, {mode_str})...")
    
    with Neo4jManager(instance=neo4j_instance) as neo4j:
        # Optionally clear existing data
        # neo4j.clear_database()
        
        if fast_mode:
            neo4j.load_knowledge_graph_fast(kg, batch_size=batch_size)
        else:
            neo4j.load_knowledge_graph(kg)
    
    loading_time = time.time() - loading_start
    print(f"✅ Neo4j loading completed in {loading_time:.1f}s")
    print(f"📊 Loaded {len(kg.servers)} servers and {len(kg.relationships)} relationships")


def print_statistics(kg: KnowledgeGraph):
    """Print statistics about the knowledge graph"""
    print("\n📈 Knowledge Graph Statistics:")
    print(f"  Total Servers: {len(kg.servers)}")
    print(f"  Total Relationships: {len(kg.relationships)}")
    print(f"  Total Categories: {len(kg.categories)}")
    print(f"  Registry Snapshots: {len(kg.registry_snapshots)}")
    
    # Category breakdown
    print("\n📊 Servers by Category:")
    category_counts = {}
    for server in kg.servers:
        for category in server.categories:
            category_counts[category.value] = category_counts.get(category.value, 0) + 1
    
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    # Registry breakdown
    print("\n📦 Servers by Registry:")
    registry_counts = {}
    for server in kg.servers:
        registry = server.registry_source.value
        registry_counts[registry] = registry_counts.get(registry, 0) + 1
    
    for registry, count in sorted(registry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {registry}: {count}")
    
    # Language breakdown
    print("\n💻 Servers by Language:")
    language_counts = {}
    for server in kg.servers:
        if server.implementation_language:
            lang = server.implementation_language
            language_counts[lang] = language_counts.get(lang, 0) + 1
    
    for lang, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {lang}: {count}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build MCP Server Knowledge Graph")
    parser.add_argument("--force-refresh", action="store_true", 
                       help="Force refresh of all registry data")
    parser.add_argument("--registries", nargs="+", 
                       choices=[r.value for r in RegistrySource],
                       help="Specific registries to scrape")
    parser.add_argument("--skip-neo4j", action="store_true",
                       help="Skip loading data into Neo4j")
    parser.add_argument("--clear-neo4j", action="store_true",
                       help="Clear Neo4j database before loading")
    parser.add_argument("--stats-only", action="store_true",
                       help="Only show statistics, don't scrape or load")
    
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
    
    try:
        if args.stats_only:
            # Load existing data and show stats
            print("📊 Loading existing data for statistics...")
            # This would need to be implemented to load from storage
            print("Stats-only mode not yet implemented")
            return
        
        # Build knowledge graph
        kg = await build_knowledge_graph(
            force_refresh=args.force_refresh,
            registries=args.registries,
            neo4j_instance=neo4j_instance
        )
        
        # Print statistics
        print_statistics(kg)
        
        # Load into Neo4j
        if not args.skip_neo4j:
            if args.clear_neo4j:
                print(f"🗑️  Clearing Neo4j database ({neo4j_instance})...")
                with Neo4jManager(instance=neo4j_instance) as neo4j:
                    neo4j.clear_database()
            
            await load_to_neo4j(kg, neo4j_instance, fast_mode=args.fast, batch_size=args.batch_size)
            
            # Show some example queries
            print("\n🔍 Example Neo4j queries you can run:")
            print("  - Find popular servers: MATCH (s:Server) RETURN s ORDER BY s.popularity_score DESC LIMIT 10")
            print("  - Find database servers: MATCH (s:Server) WHERE 'database' IN s.categories RETURN s")
            print("  - Find server relationships: MATCH (s1:Server)-[r:RELATES_TO]->(s2:Server) RETURN s1.name, r.type, s2.name")
            print("  - Category statistics: MATCH (c:Category)<-[:BELONGS_TO_CATEGORY]-(s:Server) RETURN c.name, COUNT(s)")
        
        print("\n🎉 Knowledge graph construction completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())