#!/usr/bin/env python3
"""Analyze the effectiveness of deduplication and ID standardization
"""

import asyncio
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urlparse

from deduplication import ServerDeduplicator
from models import MCPServer, RegistrySource


def load_latest_snapshots() -> dict[str, list[MCPServer]]:
    """Load the latest snapshot from each registry"""
    data_dir = Path("data/registries")
    snapshots = {}

    for registry_dir in data_dir.iterdir():
        if not registry_dir.is_dir():
            continue

        registry_name = registry_dir.name
        json_files = list(registry_dir.glob("*.json"))

        if not json_files:
            continue

        # Get the latest file
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

        with open(latest_file) as f:
            data = json.load(f)

        servers = []
        for server_data in data.get("servers", []):
            try:
                server = MCPServer(**server_data)
                servers.append(server)
            except Exception as e:
                print(f"Error loading server from {registry_name}: {e}")

        snapshots[registry_name] = servers
        print(f"Loaded {len(servers)} servers from {registry_name}")

    return snapshots


def analyze_id_standardization(snapshots: dict[str, list[MCPServer]]):
    """Analyze the quality of standardized IDs"""
    print("\n=== ID STANDARDIZATION ANALYSIS ===")

    all_ids = []
    id_patterns = defaultdict(int)
    registry_prefixes = Counter()

    for registry_name, servers in snapshots.items():
        print(f"\n{registry_name.upper()} Registry:")
        print(f"  Total servers: {len(servers)}")

        ids = [server.id for server in servers]
        all_ids.extend(ids)

        # Analyze ID patterns
        for server_id in ids:
            prefix = server_id.split("_")[0]
            registry_prefixes[prefix] += 1

            # Check ID pattern
            if server_id.startswith(f"{registry_name}_"):
                id_patterns[f"{registry_name}_correct"] += 1
            else:
                id_patterns[f"{registry_name}_incorrect"] += 1
                print(f"    Unexpected ID: {server_id}")

        # Sample some IDs
        print(f"  Sample IDs: {ids[:3]}")

    print(f"\nTotal unique IDs: {len(set(all_ids))}")
    print(f"Total IDs: {len(all_ids)}")
    if len(all_ids) != len(set(all_ids)):
        print(f"⚠️  ID collisions detected: {len(all_ids) - len(set(all_ids))}")

    print("\nRegistry prefix distribution:")
    for prefix, count in registry_prefixes.most_common():
        print(f"  {prefix}: {count}")


def analyze_repository_urls(snapshots: dict[str, list[MCPServer]]):
    """Analyze repository URL patterns and potential duplicates"""
    print("\n=== REPOSITORY URL ANALYSIS ===")

    repo_to_servers = defaultdict(list)
    domains = Counter()

    for registry_name, servers in snapshots.items():
        for server in servers:
            if server.repository:
                repo_url = str(server.repository).lower().rstrip("/").rstrip(".git")
                repo_to_servers[repo_url].append((registry_name, server))

                # Extract domain
                domain = urlparse(str(server.repository)).netloc
                domains[domain] += 1

    print(f"Unique repository URLs: {len(repo_to_servers)}")
    print(f"Repository domains: {dict(domains.most_common())}")

    # Find potential duplicates by repository
    duplicates = {repo: servers for repo, servers in repo_to_servers.items() if len(servers) > 1}

    if duplicates:
        print(f"\nPotential duplicates by repository URL ({len(duplicates)}):")
        for repo_url, servers in list(duplicates.items())[:5]:  # Show first 5
            print(f"  {repo_url}:")
            for registry, server in servers:
                print(f"    {registry}: {server.name} (id: {server.id})")
    else:
        print("\n✅ No duplicate repository URLs found")


def analyze_name_similarity(snapshots: dict[str, list[MCPServer]]):
    """Analyze name similarity across registries"""
    print("\n=== NAME SIMILARITY ANALYSIS ===")

    all_servers = []
    for servers in snapshots.values():
        all_servers.extend(servers)

    name_to_servers = defaultdict(list)

    for server in all_servers:
        if server.name:
            # Normalize name for comparison
            normalized_name = server.name.lower().replace("-", "").replace("_", "").replace(" ", "")
            name_to_servers[normalized_name].append(server)

    # Find potential name duplicates
    name_duplicates = {name: servers for name, servers in name_to_servers.items() if len(servers) > 1}

    print(f"Unique normalized names: {len(name_to_servers)}")
    print(f"Potential name duplicates: {len(name_duplicates)}")

    if name_duplicates:
        print("\nSample name duplicates:")
        for name, servers in list(name_duplicates.items())[:3]:
            print(f"  '{name}':")
            for server in servers:
                print(f"    {server.registry_source.value}: {server.name} (id: {server.id})")


def test_deduplication_effectiveness(snapshots: dict[str, list[MCPServer]]):
    """Test how well the deduplication system works"""
    print("\n=== DEDUPLICATION EFFECTIVENESS TEST ===")

    # Combine all servers
    all_servers = []
    for registry_name, servers in snapshots.items():
        all_servers.extend(servers)

    print(f"Total servers before deduplication: {len(all_servers)}")

    # Run deduplication
    deduplicator = ServerDeduplicator()
    unique_servers = deduplicator.deduplicate_servers(all_servers)

    print(f"Unique servers after deduplication: {len(unique_servers)}")
    print(f"Duplicates removed: {len(all_servers) - len(unique_servers)}")
    print(f"Deduplication rate: {((len(all_servers) - len(unique_servers)) / len(all_servers) * 100):.1f}%")

    # Analyze what was merged
    registry_distribution = Counter()
    for server in unique_servers:
        registry_distribution[server.registry_source.value] += 1

    print("\nRegistry distribution after deduplication:")
    for registry, count in registry_distribution.most_common():
        print(f"  {registry}: {count}")


def analyze_metadata_completeness(snapshots: dict[str, list[MCPServer]]):
    """Analyze completeness of server metadata"""
    print("\n=== METADATA COMPLETENESS ANALYSIS ===")

    fields = ["name", "description", "author", "repository", "version", "license", "homepage"]

    for registry_name, servers in snapshots.items():
        if not servers:  # Skip empty registries
            continue

        print(f"\n{registry_name.upper()} Registry:")

        completeness = {}
        for field in fields:
            count = sum(1 for server in servers if getattr(server, field, None))
            completeness[field] = (count, len(servers), count/len(servers)*100)

        for field, (count, total, percentage) in completeness.items():
            print(f"  {field}: {count}/{total} ({percentage:.1f}%)")

        # Calculate overall completeness score
        total_score = sum(count for count, _, _ in completeness.values())
        max_score = len(servers) * len(fields)
        overall = total_score / max_score * 100
        print(f"  Overall completeness: {overall:.1f}%")


def analyze_categories_and_coverage(snapshots: dict[str, list[MCPServer]]):
    """Analyze category distribution and domain coverage"""
    print("\n=== CATEGORY AND DOMAIN COVERAGE ANALYSIS ===")

    all_categories = Counter()
    all_servers = []

    for servers in snapshots.values():
        all_servers.extend(servers)

    for server in all_servers:
        for category in server.categories:
            all_categories[category.value] += 1

    print("Category distribution across all servers:")
    for category, count in all_categories.most_common():
        print(f"  {category}: {count}")

    # Analyze languages
    languages = Counter()
    for server in all_servers:
        if server.implementation_language:
            languages[server.implementation_language] += 1

    print("\nImplementation languages:")
    for lang, count in languages.most_common(10):
        print(f"  {lang}: {count}")


async def main():
    """Main analysis function"""
    print("🔍 Loading latest snapshots...")
    snapshots = load_latest_snapshots()

    if not snapshots:
        print("❌ No snapshots found!")
        return

    # Run all analyses
    analyze_id_standardization(snapshots)
    analyze_repository_urls(snapshots)
    analyze_name_similarity(snapshots)
    test_deduplication_effectiveness(snapshots)
    analyze_metadata_completeness(snapshots)
    analyze_categories_and_coverage(snapshots)

    print("\n🎉 Analysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
