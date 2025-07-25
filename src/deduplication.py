"""Robust deduplication system for MCP servers across multiple registries.
"""

import hashlib
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from tqdm import tqdm

from models import MCPServer, RegistrySource


class ServerDeduplicator:
    """Advanced deduplication system using multiple matching criteria"""

    def __init__(self):
        self.repository_index: dict[str, MCPServer] = {}
        self.name_author_index: dict[str, MCPServer] = {}
        self.fuzzy_name_index: dict[str, list[MCPServer]] = {}
        self.content_hash_index: dict[str, MCPServer] = {}

    def deduplicate_servers(self, servers: list[MCPServer]) -> list[MCPServer]:
        """Deduplicate servers using multiple strategies:
        1. Exact repository URL match
        2. Name + author combination 
        3. Fuzzy name matching
        4. Content hash similarity
        5. Domain-based clustering
        """
        print(f"🔍 Starting deduplication of {len(servers):,} servers...")
        print("📋 Using strategies: Repository URL, Name+Author, Content Hash, Fuzzy Matching")
        print()

        # Reset indexes
        self.repository_index.clear()
        self.name_author_index.clear()
        self.fuzzy_name_index.clear()
        self.content_hash_index.clear()

        unique_servers = []
        duplicates_found = 0

        # Enhanced progress bar for deduplication
        progress_bar = tqdm(
            servers,
            desc="🔎 Deduplicating",
            unit="server",
            colour="magenta",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )

        for server in progress_bar:
            # Update progress with current server name
            progress_bar.set_postfix_str(f"Checking: {server.name[:25]}...")

            if self._is_duplicate(server):
                duplicates_found += 1
                # Merge metadata from duplicate
                self._merge_server_metadata(server)
                progress_bar.set_postfix_str(f"Duplicate: {server.name[:25]}...")
            else:
                # Add as new unique server
                self._add_to_indexes(server)
                unique_servers.append(server)
                progress_bar.set_postfix_str(f"Unique: {server.name[:25]}...")

        progress_bar.close()

        print("✅ Deduplication phase 1 complete:")
        print(f"   • Unique servers: {len(unique_servers):,}")
        print(f"   • Duplicates found: {duplicates_found:,}")
        if len(servers) > 0:
            print(f"   • Deduplication rate: {(duplicates_found / len(servers) * 100):.1f}%")
        else:
            print("   • Deduplication rate: N/A (no servers to deduplicate)")
        print()

        # Post-process: merge similar servers with high confidence
        print("🔗 Starting similarity merging phase...")
        final_servers = self._merge_similar_servers(unique_servers)

        additional_merges = len(unique_servers) - len(final_servers)
        total_removed = duplicates_found + additional_merges

        print("✅ Deduplication complete:")
        print(f"   • Final unique servers: {len(final_servers):,}")
        print(f"   • Additional merges: {additional_merges:,}")
        print(f"   • Total removed: {total_removed:,}")
        if len(servers) > 0:
            print(f"   • Overall deduplication rate: {(total_removed / len(servers) * 100):.1f}%")
        else:
            print("   • Overall deduplication rate: N/A (no servers to deduplicate)")

        return final_servers

    def _is_duplicate(self, server: MCPServer) -> bool:
        """Check if server is a duplicate using multiple criteria"""
        # 1. Exact repository URL match (highest confidence)
        if server.repository:
            normalized_repo = self._normalize_repository_url(str(server.repository))
            if normalized_repo in self.repository_index:
                return True

        # 2. Name + author combination
        if server.name and server.author:
            name_author_key = f"{self._normalize_name(server.name)}|{self._normalize_name(server.author)}"
            if name_author_key in self.name_author_index:
                return True

        # 3. Content hash similarity (for servers with similar descriptions)
        content_hash = self._calculate_content_hash(server)
        if content_hash in self.content_hash_index:
            return True

        # 4. Fuzzy name matching (for variations in naming)
        if self._has_fuzzy_name_match(server):
            return True

        return False

    def _add_to_indexes(self, server: MCPServer):
        """Add server to all relevant indexes"""
        # Repository index
        if server.repository:
            normalized_repo = self._normalize_repository_url(str(server.repository))
            self.repository_index[normalized_repo] = server

        # Name + author index
        if server.name and server.author:
            name_author_key = f"{self._normalize_name(server.name)}|{self._normalize_name(server.author)}"
            self.name_author_index[name_author_key] = server

        # Content hash index
        content_hash = self._calculate_content_hash(server)
        self.content_hash_index[content_hash] = server

        # Fuzzy name index
        normalized_name = self._normalize_name(server.name)
        if normalized_name not in self.fuzzy_name_index:
            self.fuzzy_name_index[normalized_name] = []
        self.fuzzy_name_index[normalized_name].append(server)

    def _normalize_repository_url(self, url: str) -> str:
        """Normalize repository URL for comparison"""
        # Remove trailing slashes, .git suffix, and normalize case
        url = url.lower().rstrip("/")
        url = url.removesuffix(".git")

        # Parse URL to get clean domain + path
        parsed = urlparse(url)
        return f"{parsed.netloc}{parsed.path}"

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""

        # Convert to lowercase, remove special chars, normalize spaces
        normalized = re.sub(r"[^a-z0-9\s]", "", name.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Remove common prefixes/suffixes
        normalized = re.sub(r"^(mcp[-_\s]*)?", "", normalized)
        normalized = re.sub(r"[-_\s]*(server|mcp)$", "", normalized)

        return normalized

    def _calculate_content_hash(self, server: MCPServer) -> str:
        """Calculate content hash based on key identifying features"""
        content_parts = [
            self._normalize_name(server.name),
            self._normalize_name(server.author or ""),
            (server.description or "").lower()[:200],  # First 200 chars
            str(sorted(cat.value for cat in server.categories)),
            str(sorted(op.value for op in server.operations)),
        ]

        content_string = "|".join(content_parts)
        return hashlib.md5(content_string.encode()).hexdigest()

    def _has_fuzzy_name_match(self, server: MCPServer) -> bool:
        """Check for fuzzy name matches using string similarity"""
        normalized_name = self._normalize_name(server.name)

        for existing_name, existing_servers in self.fuzzy_name_index.items():
            # Skip exact matches (already handled)
            if existing_name == normalized_name:
                continue

            # Calculate similarity ratio
            similarity = SequenceMatcher(None, normalized_name, existing_name).ratio()

            # High similarity threshold for fuzzy matching
            if similarity > 0.85:
                # Additional checks to confirm it's the same server
                for existing_server in existing_servers:
                    if self._servers_are_similar(server, existing_server):
                        return True

        return False

    def _servers_are_similar(self, server1: MCPServer, server2: MCPServer) -> bool:
        """Check if two servers are likely the same using multiple signals"""
        similarity_score = 0

        # Author similarity
        if server1.author and server2.author:
            author_sim = SequenceMatcher(None,
                self._normalize_name(server1.author),
                self._normalize_name(server2.author),
            ).ratio()
            similarity_score += author_sim * 0.3

        # Description similarity
        if server1.description and server2.description:
            desc_sim = SequenceMatcher(None,
                server1.description.lower()[:100],
                server2.description.lower()[:100],
            ).ratio()
            similarity_score += desc_sim * 0.2

        # Category overlap
        common_categories = set(server1.categories) & set(server2.categories)
        if server1.categories and server2.categories:
            category_sim = len(common_categories) / max(len(server1.categories), len(server2.categories))
            similarity_score += category_sim * 0.2

        # Language similarity
        if (server1.implementation_language and server2.implementation_language and
            server1.implementation_language == server2.implementation_language):
            similarity_score += 0.1

        # Repository domain similarity (different repos but same author/org)
        if server1.repository and server2.repository:
            repo1_parts = str(server1.repository).split("/")
            repo2_parts = str(server2.repository).split("/")
            if len(repo1_parts) >= 4 and len(repo2_parts) >= 4:
                if repo1_parts[3] == repo2_parts[3]:  # Same GitHub organization
                    similarity_score += 0.2

        return similarity_score > 0.7

    def _merge_server_metadata(self, duplicate_server: MCPServer):
        """Merge metadata from duplicate server into existing server"""
        # Find the existing server to merge into
        existing_server = None

        # Try repository match first
        if duplicate_server.repository:
            normalized_repo = self._normalize_repository_url(str(duplicate_server.repository))
            existing_server = self.repository_index.get(normalized_repo)

        # Try name+author match
        if not existing_server and duplicate_server.name and duplicate_server.author:
            name_author_key = f"{self._normalize_name(duplicate_server.name)}|{self._normalize_name(duplicate_server.author)}"
            existing_server = self.name_author_index.get(name_author_key)

        if not existing_server:
            return

        # Merge metadata (prefer non-empty values)
        if not existing_server.description and duplicate_server.description:
            existing_server.description = duplicate_server.description

        if not existing_server.version and duplicate_server.version:
            existing_server.version = duplicate_server.version

        if not existing_server.license and duplicate_server.license:
            existing_server.license = duplicate_server.license

        if not existing_server.homepage and duplicate_server.homepage:
            existing_server.homepage = duplicate_server.homepage

        # Merge categories and operations (union)
        existing_server.categories = list(set(existing_server.categories + duplicate_server.categories))
        existing_server.operations = list(set(existing_server.operations + duplicate_server.operations))
        existing_server.data_types = list(set((existing_server.data_types or []) + (duplicate_server.data_types or [])))

        # Merge tools, resources, prompts
        if duplicate_server.tools:
            existing_tools = {tool.name for tool in (existing_server.tools or [])}
            for tool in duplicate_server.tools:
                if tool.name not in existing_tools:
                    if not existing_server.tools:
                        existing_server.tools = []
                    existing_server.tools.append(tool)

        # Update popularity metrics (take maximum)
        if duplicate_server.popularity_score and (not existing_server.popularity_score or
                                                 duplicate_server.popularity_score > existing_server.popularity_score):
            existing_server.popularity_score = duplicate_server.popularity_score

        if duplicate_server.download_count and (not existing_server.download_count or
                                               duplicate_server.download_count > existing_server.download_count):
            existing_server.download_count = duplicate_server.download_count

        # Update last_updated to most recent
        if (duplicate_server.last_updated and
            (not existing_server.last_updated or duplicate_server.last_updated > existing_server.last_updated)):
            existing_server.last_updated = duplicate_server.last_updated

    def _merge_similar_servers(self, servers: list[MCPServer]) -> list[MCPServer]:
        """Final pass: merge servers that are very similar but not exact duplicates"""
        final_servers = []
        processed_indices = set()
        merges_found = 0

        # Progress bar for similarity merging
        progress_bar = tqdm(
            enumerate(servers),
            total=len(servers),
            desc="🔗 Similarity merge",
            unit="server",
            colour="cyan",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )

        for i, server in progress_bar:
            if i in processed_indices:
                continue

            progress_bar.set_postfix_str(f"Analyzing: {server.name[:20]}...")

            # Look for highly similar servers
            similar_indices = []
            for j, other_server in enumerate(servers[i+1:], i+1):
                if j in processed_indices:
                    continue

                if self._servers_are_highly_similar(server, other_server):
                    similar_indices.append(j)

            if similar_indices:
                # Merge all similar servers into one
                merged_server = self._merge_multiple_servers([server] + [servers[j] for j in similar_indices])
                final_servers.append(merged_server)
                merges_found += len(similar_indices)

                # Mark all as processed
                processed_indices.add(i)
                processed_indices.update(similar_indices)

                progress_bar.set_postfix_str(f"Merged {len(similar_indices)+1} servers")
            else:
                final_servers.append(server)
                processed_indices.add(i)

        progress_bar.close()

        print(f"   • Similarity groups merged: {merges_found}")

        return final_servers

    def _servers_are_highly_similar(self, server1: MCPServer, server2: MCPServer) -> bool:
        """Check if servers are highly similar and should be merged"""
        # Don't merge servers from the same registry (already deduplicated)
        if server1.registry_source == server2.registry_source:
            return False

        # High similarity threshold for cross-registry merging
        return self._servers_are_similar(server1, server2) and self._calculate_similarity_score(server1, server2) > 0.9

    def _calculate_similarity_score(self, server1: MCPServer, server2: MCPServer) -> float:
        """Calculate detailed similarity score between two servers"""
        score = 0.0

        # Name similarity (high weight)
        if server1.name and server2.name:
            name_sim = SequenceMatcher(None,
                self._normalize_name(server1.name),
                self._normalize_name(server2.name),
            ).ratio()
            score += name_sim * 0.4

        # Author similarity
        if server1.author and server2.author:
            author_sim = SequenceMatcher(None,
                self._normalize_name(server1.author),
                self._normalize_name(server2.author),
            ).ratio()
            score += author_sim * 0.2

        # Repository domain similarity
        if server1.repository and server2.repository:
            repo1_domain = urlparse(str(server1.repository)).netloc
            repo2_domain = urlparse(str(server2.repository)).netloc
            if repo1_domain == repo2_domain:
                score += 0.2

        # Description similarity
        if server1.description and server2.description:
            desc_sim = SequenceMatcher(None,
                server1.description.lower(),
                server2.description.lower(),
            ).ratio()
            score += desc_sim * 0.1

        # Category overlap
        if server1.categories and server2.categories:
            common_cats = set(server1.categories) & set(server2.categories)
            total_cats = set(server1.categories) | set(server2.categories)
            if total_cats:
                score += (len(common_cats) / len(total_cats)) * 0.1

        return score

    def _merge_multiple_servers(self, servers: list[MCPServer]) -> MCPServer:
        """Merge multiple similar servers into one comprehensive server"""
        # Use the server with the most complete metadata as base
        base_server = max(servers, key=lambda s: self._calculate_completeness_score(s))

        # Merge all other servers into the base
        for server in servers:
            if server != base_server:
                self._merge_server_into_base(base_server, server)

        return base_server

    def _calculate_completeness_score(self, server: MCPServer) -> int:
        """Calculate how complete a server's metadata is"""
        score = 0

        if server.description: score += 2
        if server.author: score += 1
        if server.repository: score += 2
        if server.version: score += 1
        if server.license: score += 1
        if server.homepage: score += 1
        if server.tools: score += len(server.tools)
        if server.resources: score += len(server.resources)
        if server.categories: score += len(server.categories)
        if server.popularity_score: score += 1

        return score

    def _merge_server_into_base(self, base_server: MCPServer, other_server: MCPServer):
        """Merge another server's metadata into the base server"""
        # Use non-empty values from other_server to fill gaps in base_server
        if not base_server.description and other_server.description:
            base_server.description = other_server.description

        if not base_server.version and other_server.version:
            base_server.version = other_server.version

        if not base_server.license and other_server.license:
            base_server.license = other_server.license

        if not base_server.homepage and other_server.homepage:
            base_server.homepage = other_server.homepage

        if not base_server.implementation_language and other_server.implementation_language:
            base_server.implementation_language = other_server.implementation_language

        # Merge lists (union)
        base_server.categories = list(set(base_server.categories + other_server.categories))
        base_server.operations = list(set(base_server.operations + other_server.operations))

        if other_server.data_types:
            base_server.data_types = list(set((base_server.data_types or []) + other_server.data_types))

        # Take higher popularity metrics
        if other_server.popularity_score and (not base_server.popularity_score or
                                             other_server.popularity_score > base_server.popularity_score):
            base_server.popularity_score = other_server.popularity_score

        if other_server.download_count and (not base_server.download_count or
                                           other_server.download_count > base_server.download_count):
            base_server.download_count = other_server.download_count

        # Take more recent update date
        if (other_server.last_updated and
            (not base_server.last_updated or other_server.last_updated > base_server.last_updated)):
            base_server.last_updated = other_server.last_updated
