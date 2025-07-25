"""Global standardized ID generation for MCP servers.

Creates stable, unique, global identifiers based on server properties
rather than registry-specific prefixes.
"""

import hashlib
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from models import MCPServer, RegistrySource


class GlobalIDGenerator:
    """Generates standardized global IDs for MCP servers"""

    def __init__(self):
        self.used_ids = set()
        self.id_mappings = {}  # Maps old registry-specific IDs to global IDs

    def generate_global_id(self, server_data: dict[str, Any], registry_source: RegistrySource) -> str:
        """Generate a global standardized ID for an MCP server.
        
        Priority order for ID generation:
        1. Repository-based ID (github.com/owner/repo -> owner/repo)
        2. Name + Author combination
        3. Unique name if author is missing
        4. Content hash as fallback
        """
        # Strategy 1: Repository-based ID (most stable)
        if server_data.get("repository"):
            repo_id = self._extract_repository_id(server_data["repository"])
            if repo_id:
                global_id = self._normalize_id(repo_id)
                if global_id not in self.used_ids:
                    self.used_ids.add(global_id)
                    return global_id

        # Strategy 2: Name + Author combination
        name = server_data.get("name", "")
        author = server_data.get("author", "")

        if name and author:
            combined_id = f"{author}/{name}"
            global_id = self._normalize_id(combined_id)
            if global_id not in self.used_ids:
                self.used_ids.add(global_id)
                return global_id

        # Strategy 3: Unique name only
        if name:
            global_id = self._normalize_id(name)
            if global_id not in self.used_ids:
                self.used_ids.add(global_id)
                return global_id

        # Strategy 4: Content hash fallback
        content_hash = self._generate_content_hash(server_data)
        global_id = f"server-{content_hash[:12]}"

        # Ensure uniqueness even for hash collisions
        counter = 1
        original_id = global_id
        while global_id in self.used_ids:
            global_id = f"{original_id}-{counter}"
            counter += 1

        self.used_ids.add(global_id)
        return global_id

    def _extract_repository_id(self, repository_url: str) -> str | None:
        """Extract owner/repo from repository URL"""
        try:
            # Handle various URL formats
            url = str(repository_url).lower()

            # Remove protocol and www
            url = re.sub(r"^https?://", "", url)
            url = re.sub(r"^www\.", "", url)

            # Parse GitHub URLs: github.com/owner/repo
            if "github.com" in url:
                parts = url.split("/")
                if len(parts) >= 3:
                    owner = parts[1]
                    repo = parts[2]

                    # Remove .git suffix
                    repo = re.sub(r"\.git$", "", repo)

                    return f"{owner}/{repo}"

            # Handle other git hosting services similarly
            # gitlab.com, bitbucket.org, etc.
            for domain in ["gitlab.com", "bitbucket.org", "codeberg.org"]:
                if domain in url:
                    parts = url.split("/")
                    if len(parts) >= 3:
                        owner = parts[1]
                        repo = parts[2]
                        repo = re.sub(r"\.git$", "", repo)
                        return f"{owner}/{repo}"

            return None

        except Exception:
            return None

    def _normalize_id(self, raw_id: str) -> str:
        """Normalize an ID to be URL-safe and consistent"""
        if not raw_id:
            return ""

        # Convert to lowercase
        normalized = raw_id.lower()

        # Replace common separators with hyphens
        normalized = re.sub(r"[_\s]+", "-", normalized)

        # Remove or replace special characters
        normalized = re.sub(r"[^a-z0-9\-\/]", "", normalized)

        # Clean up multiple hyphens
        normalized = re.sub(r"-+", "-", normalized)

        # Remove leading/trailing hyphens
        normalized = normalized.strip("-")

        # Ensure reasonable length (max 100 chars)
        if len(normalized) > 100:
            # Take first 80 chars + hash of remainder
            remainder_hash = hashlib.md5(normalized[80:].encode()).hexdigest()[:8]
            normalized = normalized[:80] + "-" + remainder_hash

        return normalized

    def _generate_content_hash(self, server_data: dict[str, Any]) -> str:
        """Generate a content hash based on key server properties"""
        # Create a stable hash from key identifying properties
        hash_components = [
            str(server_data.get("name", "")).lower(),
            str(server_data.get("author", "")).lower(),
            str(server_data.get("description", ""))[:100].lower(),  # First 100 chars
            str(server_data.get("repository", "")).lower(),
        ]

        # Add tools if available
        tools = server_data.get("tools", [])
        if tools and isinstance(tools, list):
            tool_names = [str(tool.get("name", "")) for tool in tools if isinstance(tool, dict)]
            hash_components.append("|".join(sorted(tool_names)))

        content_string = "|".join(hash_components)
        return hashlib.sha256(content_string.encode()).hexdigest()


def convert_server_to_global_id(server: MCPServer, id_generator: GlobalIDGenerator) -> MCPServer:
    """Convert a server with registry-specific ID to use global ID"""
    # Generate global ID
    server_data = {
        "name": server.name,
        "author": server.author,
        "description": server.description,
        "repository": str(server.repository) if server.repository else None,
        "tools": [{"name": tool.name} for tool in (server.tools or [])],
    }

    global_id = id_generator.generate_global_id(server_data, server.registry_source)

    # Create new server instance with global ID
    server_dict = server.dict()
    server_dict["id"] = global_id

    # Store the original registry-specific ID in metadata
    if not server_dict.get("raw_metadata"):
        server_dict["raw_metadata"] = {}
    server_dict["raw_metadata"][f"{server.registry_source.value}_id"] = server.id

    return MCPServer(**server_dict)


def batch_convert_to_global_ids(servers: list[MCPServer]) -> list[MCPServer]:
    """Convert a batch of servers to use global IDs"""
    id_generator = GlobalIDGenerator()
    converted_servers = []

    print(f"Converting {len(servers)} servers to global IDs...")

    for server in servers:
        try:
            converted_server = convert_server_to_global_id(server, id_generator)
            converted_servers.append(converted_server)
        except Exception as e:
            print(f"Error converting server {server.id}: {e}")
            # Keep original server if conversion fails
            converted_servers.append(server)

    print(f"Conversion complete. Generated {len(id_generator.used_ids)} unique global IDs.")

    # Report on ID patterns
    id_patterns = analyze_id_patterns(converted_servers)
    print_id_analysis(id_patterns)

    return converted_servers


def analyze_id_patterns(servers: list[MCPServer]) -> dict[str, Any]:
    """Analyze the patterns in generated global IDs"""
    patterns = {
        "repository_based": 0,
        "author_name": 0,
        "name_only": 0,
        "hash_based": 0,
        "total": len(servers),
    }

    examples = {
        "repository_based": [],
        "author_name": [],
        "name_only": [],
        "hash_based": [],
    }

    for server in servers:
        server_id = server.id

        if "/" in server_id and not server_id.startswith("server-"):
            if server.repository and "github.com" in str(server.repository):
                patterns["repository_based"] += 1
                if len(examples["repository_based"]) < 3:
                    examples["repository_based"].append(server_id)
            else:
                patterns["author_name"] += 1
                if len(examples["author_name"]) < 3:
                    examples["author_name"].append(server_id)
        elif server_id.startswith("server-"):
            patterns["hash_based"] += 1
            if len(examples["hash_based"]) < 3:
                examples["hash_based"].append(server_id)
        else:
            patterns["name_only"] += 1
            if len(examples["name_only"]) < 3:
                examples["name_only"].append(server_id)

    patterns["examples"] = examples
    return patterns


def print_id_analysis(patterns: dict[str, Any]):
    """Print analysis of ID generation patterns"""
    total = patterns["total"]
    print("\n📊 Global ID Generation Analysis:")
    print(f"   Repository-based: {patterns['repository_based']}/{total} ({patterns['repository_based']/total*100:.1f}%)")
    print(f"   Author/Name combo: {patterns['author_name']}/{total} ({patterns['author_name']/total*100:.1f}%)")
    print(f"   Name-only: {patterns['name_only']}/{total} ({patterns['name_only']/total*100:.1f}%)")
    print(f"   Hash-based: {patterns['hash_based']}/{total} ({patterns['hash_based']/total*100:.1f}%)")

    print("\n📝 Example IDs:")
    for pattern_type, examples in patterns["examples"].items():
        if examples:
            print(f"   {pattern_type}: {', '.join(examples)}")


if __name__ == "__main__":
    # Test the ID generation
    test_servers = [
        {
            "name": "playwright-mcp",
            "author": "microsoft",
            "repository": "https://github.com/microsoft/playwright-mcp",
            "description": "Playwright MCP server",
        },
        {
            "name": "Cairo Coder",
            "author": "kasarlabs",
            "repository": "https://github.com/kasarlabs/cairo-coder-mcp",
            "description": "Cairo coding assistant",
        },
        {
            "name": "time-server",
            "author": None,
            "repository": None,
            "description": "Simple time server",
        },
    ]

    id_gen = GlobalIDGenerator()

    print("Testing Global ID Generation:")
    for server_data in test_servers:
        global_id = id_gen.generate_global_id(server_data, RegistrySource.GITHUB)
        print(f"  {server_data['name']} -> {global_id}")
