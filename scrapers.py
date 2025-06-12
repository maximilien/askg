import asyncio
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import base64

import aiohttp
import yaml
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm

from models import (
    MCPServer, RegistrySource, RegistrySnapshot, 
    ServerCategory, OperationType, MCPTool, MCPResource, MCPPrompt
)


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for i, k in enumerate(keys):
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class StorageManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.base_path = Path(config.get('storage.base_path', './data'))
        self.registries_path = Path(config.get('storage.registries_path', './data/registries'))
        self.snapshots_path = Path(config.get('storage.snapshots_path', './data/snapshots'))
        
        # Create directories
        self.base_path.mkdir(exist_ok=True)
        self.registries_path.mkdir(exist_ok=True)
        self.snapshots_path.mkdir(exist_ok=True)
    
    def get_registry_path(self, registry: RegistrySource) -> Path:
        path = self.registries_path / registry.value
        path.mkdir(exist_ok=True)
        return path
    
    def get_snapshot_filename(self, registry: RegistrySource, date: datetime) -> str:
        return f"{registry.value}_{date.strftime('%Y%m%d_%H%M%S')}.json"
    
    def save_snapshot(self, snapshot: RegistrySnapshot) -> Path:
        filename = self.get_snapshot_filename(snapshot.registry_source, snapshot.snapshot_date)
        filepath = self.get_registry_path(snapshot.registry_source) / filename
        
        with open(filepath, 'w') as f:
            json.dump(snapshot.dict(), f, indent=2, default=str)
        
        return filepath
    
    def load_latest_snapshot(self, registry: RegistrySource) -> Optional[RegistrySnapshot]:
        registry_path = self.get_registry_path(registry)
        snapshots = list(registry_path.glob(f"{registry.value}_*.json"))
        
        if not snapshots:
            return None
        
        latest = max(snapshots, key=lambda p: p.stat().st_mtime)
        
        with open(latest, 'r') as f:
            data = json.load(f)
        
        return RegistrySnapshot(**data)
    
    def calculate_checksum(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()


class BaseScraper:
    def __init__(self, config: ConfigManager, storage: StorageManager):
        self.config = config
        self.storage = storage
        self.session = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.config.get('scraping.timeout', 30))
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': self.config.get('scraping.user_agent', 'MCP-Scraper/1.0')}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape(self) -> RegistrySnapshot:
        raise NotImplementedError
    
    def categorize_server(self, server_data: Dict[str, Any]) -> List[ServerCategory]:
        categories = []
        description = (server_data.get('description', '') + ' ' + 
                      server_data.get('name', '')).lower()
        
        category_keywords = {
            ServerCategory.DATABASE: ['database', 'sql', 'postgres', 'mysql', 'mongodb', 'redis'],
            ServerCategory.FILE_SYSTEM: ['file', 'filesystem', 'directory', 'folder', 'storage'],
            ServerCategory.API_INTEGRATION: ['api', 'rest', 'graphql', 'webhook', 'http'],
            ServerCategory.DEVELOPMENT_TOOLS: ['git', 'github', 'code', 'development', 'build'],
            ServerCategory.DATA_PROCESSING: ['data', 'etl', 'transform', 'process', 'analytics'],
            ServerCategory.CLOUD_SERVICES: ['aws', 'azure', 'gcp', 'cloud', 'kubernetes'],
            ServerCategory.COMMUNICATION: ['slack', 'discord', 'email', 'notification', 'message'],
            ServerCategory.AUTHENTICATION: ['auth', 'oauth', 'login', 'security', 'jwt'],
            ServerCategory.MONITORING: ['monitor', 'metrics', 'logging', 'observability'],
            ServerCategory.SEARCH: ['search', 'index', 'elasticsearch', 'solr'],
            ServerCategory.AI_ML: ['ai', 'ml', 'machine learning', 'neural', 'model']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in description for keyword in keywords):
                categories.append(category)
        
        return categories or [ServerCategory.OTHER]
    
    def determine_operations(self, server_data: Dict[str, Any]) -> List[OperationType]:
        operations = []
        tools = server_data.get('tools', [])
        
        if tools:
            for tool in tools:
                tool_name = tool.get('name', '').lower()
                if any(op in tool_name for op in ['get', 'read', 'fetch', 'list']):
                    operations.append(OperationType.READ)
                elif any(op in tool_name for op in ['create', 'write', 'update', 'delete']):
                    operations.append(OperationType.WRITE)
                elif any(op in tool_name for op in ['query', 'search', 'find']):
                    operations.append(OperationType.QUERY)
                elif any(op in tool_name for op in ['execute', 'run', 'call']):
                    operations.append(OperationType.EXECUTE)
        
        return list(set(operations)) or [OperationType.READ]


class GitHubScraper(BaseScraper):
    async def scrape(self) -> RegistrySnapshot:
        start_time = time.time()
        github_token = self.config.get('github.token')
        if not github_token:
            raise ValueError("GitHub token is required")
        
        headers = {'Authorization': f'token {github_token}'}
        servers = []
        
        # Enhanced search queries for comprehensive MCP server discovery
        search_queries = [
            # Basic MCP searches
            "mcp server in:readme",
            "model context protocol in:readme",
            "mcp-server in:name,description",
            "\"mcp server\" in:readme",
            
            # Topic searches
            "topic:mcp",
            "topic:model-context-protocol", 
            "topic:mcp-server",
            "topic:claude",
            
            # File-based searches
            "filename:glama.json",
            "filename:mcp.json",
            "path:mcp filename:package.json",
            
            # Dependency searches
            "@modelcontextprotocol in:file",
            "mcp-server in:file",
            
            # Claude-related searches
            "claude desktop mcp in:readme",
            "claude mcp server in:readme",
            
            # Awesome lists
            "awesome-mcp-servers in:name,description",
            "mcp awesome in:name,description",
            
            # Organization searches
            "org:modelcontextprotocol",
            "user:modelcontextprotocol",
        ]
        
        seen_repos = set()
        
        # Progress bar for search queries
        with tqdm(total=len(search_queries), desc="🔍 GitHub Search Queries", unit="query") as pbar:
            for query in search_queries:
                pbar.set_postfix_str(f"Searching: {query[:40]}...")
                
                # Search repositories with pagination
                for page in range(1, 6):  # First 5 pages (500 results max)
                    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&page={page}&per_page=100"
                    
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            repos = data.get('items', [])
                            
                            if not repos:  # No more results
                                break
                                
                            for repo in repos:
                                repo_url = repo['html_url']
                                if repo_url not in seen_repos:
                                    seen_repos.add(repo_url)
                                    server = await self._process_github_repo(repo, headers)
                                    if server:
                                        servers.append(server)
                        
                        elif response.status == 403:  # Rate limit
                            pbar.set_postfix_str("Rate limited, waiting...")
                            await asyncio.sleep(60)
                            break
                        else:
                            pbar.set_postfix_str(f"Error {response.status}")
                            break
                    
                    # Respect rate limits
                    await asyncio.sleep(1)
                
                pbar.set_postfix_str(f"Found {len(servers)} servers so far")
                pbar.update(1)
        
        # Search for awesome MCP lists and parse them
        print("🔍 Searching awesome MCP lists...")
        awesome_servers = await self._scrape_awesome_lists(headers)
        servers.extend(awesome_servers)
        
        # Search for code containing MCP patterns
        print("🔍 Searching MCP code patterns...")
        code_servers = await self._search_mcp_code(headers)
        servers.extend(code_servers)
        
        # Remove duplicates by repository URL
        print("🔧 Deduplicating repositories...")
        unique_servers = []
        final_seen = set()
        for server in tqdm(servers, desc="Processing servers", unit="server"):
            if server.repository and str(server.repository) not in final_seen:
                unique_servers.append(server)
                final_seen.add(str(server.repository))
        
        elapsed_time = time.time() - start_time
        print(f"✅ GitHub scraping completed in {elapsed_time:.1f}s")
        
        return RegistrySnapshot(
            registry_source=RegistrySource.GITHUB,
            snapshot_date=datetime.now(),
            servers_count=len(unique_servers),
            servers=unique_servers
        )
    
    async def _process_github_repo(self, repo: Dict[str, Any], headers: Dict[str, str]) -> Optional[MCPServer]:
        try:
            # Check if it's actually an MCP server
            if not await self._is_mcp_server(repo, headers):
                return None
            
            server_id = f"github_{repo['owner']['login']}_{repo['name']}"
            
            # Try to get package.json or pyproject.toml for more details
            package_info = await self._get_package_info(repo, headers)
            
            categories = self.categorize_server(repo)
            operations = self.determine_operations(package_info)
            
            return MCPServer(
                id=server_id,
                name=repo['name'],
                description=repo.get('description'),
                author=repo['owner']['login'],
                homepage=repo.get('homepage') if repo.get('homepage') else None,
                repository=repo['html_url'],
                implementation_language=repo.get('language'),
                categories=categories,
                operations=operations,
                registry_source=RegistrySource.GITHUB,
                source_url=repo['html_url'],
                last_updated=datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00')),
                popularity_score=repo.get('stargazers_count', 0),
                raw_metadata=repo
            )
        except Exception as e:
            print(f"Error processing GitHub repo {repo.get('name', 'unknown')}: {e}")
            return None
    
    async def _is_mcp_server(self, repo: Dict[str, Any], headers: Dict[str, str]) -> bool:
        # Check README for MCP indicators
        readme_url = f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/readme"
        
        try:
            async with self.session.get(readme_url, headers=headers) as response:
                if response.status == 200:
                    readme_data = await response.json()
                    readme_content = readme_data.get('content', '')
                    
                    # Decode base64 content
                    readme_text = base64.b64decode(readme_content).decode('utf-8').lower()
                    
                    mcp_indicators = [
                        'mcp server', 'model context protocol', 'mcp-server',
                        'claude desktop', 'mcp.json', 'model-context-protocol'
                    ]
                    
                    return any(indicator in readme_text for indicator in mcp_indicators)
        except Exception:
            pass
        
        # Fallback to description and topics
        description = repo.get('description', '').lower()
        topics = repo.get('topics', [])
        
        return (any(topic in ['mcp', 'model-context-protocol'] for topic in topics) or
                'mcp' in description or 'model context protocol' in description)
    
    async def _get_package_info(self, repo: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        package_files = ['package.json', 'pyproject.toml', 'Cargo.toml']
        
        for filename in package_files:
            url = f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/contents/{filename}"
            
            try:
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        file_data = await response.json()
                        
                        content = base64.b64decode(file_data['content']).decode('utf-8')
                        
                        if filename == 'package.json':
                            return json.loads(content)
                        # TODO: Parse TOML files for Rust/Python projects
                        
            except Exception:
                continue
        
        return {}
    
    async def _scrape_awesome_lists(self, headers: Dict[str, str]) -> List[MCPServer]:
        """Scrape awesome MCP server lists to find more servers"""
        servers = []
        awesome_repos = [
            "TensorBlock/awesome-mcp-servers",
            "punkpeye/awesome-mcp-servers", 
            "wong2/awesome-mcp-servers",
            "modelcontextprotocol/servers",
            "anthropics/mcp-servers"
        ]
        
        for repo_name in awesome_repos:
            try:
                # Get README content
                url = f"https://api.github.com/repos/{repo_name}/readme"
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        readme_data = await response.json()
                        
                        readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
                        
                        # Extract GitHub URLs from markdown
                        import re
                        github_urls = re.findall(r'https://github\.com/([^/]+/[^/\s\)]+)', readme_content)
                        
                        for repo_path in github_urls:
                            # Get repo details
                            repo_url = f"https://api.github.com/repos/{repo_path}"
                            async with self.session.get(repo_url, headers=headers) as repo_response:
                                if repo_response.status == 200:
                                    repo_data = await repo_response.json()
                                    server = await self._process_github_repo(repo_data, headers)
                                    if server:
                                        servers.append(server)
                            
                            await asyncio.sleep(0.5)  # Rate limiting
                            
            except Exception as e:
                print(f"Error scraping awesome list {repo_name}: {e}")
                continue
        
        return servers
    
    async def _search_mcp_code(self, headers: Dict[str, str]) -> List[MCPServer]:
        """Search for code patterns that indicate MCP servers"""
        servers = []
        
        # Search for specific code patterns
        code_queries = [
            '"@modelcontextprotocol/sdk" language:typescript',
            '"@modelcontextprotocol/sdk" language:javascript', 
            '"model-context-protocol" language:python',
            '"mcp.Server" language:python',
            '"from mcp" language:python',
            '"import mcp" language:python',
        ]
        
        for query in code_queries:
            try:
                url = f"https://api.github.com/search/code?q={query}&per_page=100"
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('items', [])[:50]:  # Limit to avoid rate limits
                            repo = item.get('repository', {})
                            if repo:
                                server = await self._process_github_repo(repo, headers)
                                if server:
                                    servers.append(server)
                    
                    await asyncio.sleep(2)  # Code search has stricter rate limits
                    
            except Exception as e:
                print(f"Error in code search for {query}: {e}")
                continue
        
        return servers


class MCPSoScraper(BaseScraper):
    async def scrape(self) -> RegistrySnapshot:
        start_time = time.time()
        base_url = self.config.get('registries.mcp_so.base_url', 'https://mcp.so')
        servers = []
        
        # Get all server URLs from the main page and category pages
        print("🔍 Discovering server URLs on mcp.so...")
        server_urls = await self._discover_all_server_urls(base_url)
        print(f"📋 Found {len(server_urls)} server URLs on mcp.so")
        
        # Scrape each server detail page with enhanced progress tracking
        successful_count = 0
        failed_count = 0
        
        async def process_server_with_progress(server_url, pbar):
            nonlocal successful_count, failed_count
            try:
                server = await self._scrape_server_detail(server_url)
                if server:
                    successful_count += 1
                    pbar.set_postfix_str(f"✅ {successful_count} success, ❌ {failed_count} failed")
                else:
                    failed_count += 1
                    pbar.set_postfix_str(f"✅ {successful_count} success, ❌ {failed_count} failed")
                pbar.update(1)
                await asyncio.sleep(0.5)  # Rate limiting
                return server
            except Exception as e:
                failed_count += 1
                pbar.set_postfix_str(f"✅ {successful_count} success, ❌ {failed_count} failed")
                pbar.update(1)
                return None
        
        # Process with detailed progress bar
        print(f"🌐 Starting detailed scraping of {len(server_urls)} servers...")
        with tqdm(total=len(server_urls), desc="🌐 Scraping mcp.so servers", unit="server") as pbar:
            # Process in smaller batches to avoid overwhelming the server
            batch_size = 50
            results = []
            
            for i in range(0, len(server_urls), batch_size):
                batch_urls = server_urls[i:i + batch_size]
                pbar.set_description(f"🌐 Batch {i//batch_size + 1}/{(len(server_urls)-1)//batch_size + 1}")
                
                # Create tasks for this batch
                batch_tasks = [process_server_with_progress(url, pbar) for url in batch_urls]
                
                # Process batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                results.extend([r for r in batch_results if not isinstance(r, Exception)])
                
                # Small delay between batches
                await asyncio.sleep(1)
        
        # Filter out None results
        servers = [server for server in results if server is not None]
        
        elapsed_time = time.time() - start_time
        print(f"✅ mcp.so scraping completed in {elapsed_time:.1f}s")
        
        return RegistrySnapshot(
            registry_source=RegistrySource.MCP_SO,
            snapshot_date=datetime.now(),
            url=base_url,
            servers_count=len(servers),
            servers=servers
        )
    
    async def _discover_all_server_urls(self, base_url: str) -> List[str]:
        """Discover ALL server URLs from mcp.so using sitemaps (3,642+ servers)"""
        server_urls = set()
        
        print("🗂️  Extracting servers from MCP.so sitemaps...")
        
        # Use the discovered sitemap files to get all servers
        sitemap_urls = [
            f"{base_url}/sitemap_projects_1.xml",  # 958 servers
            f"{base_url}/sitemap_projects_2.xml",  # 980 servers
            f"{base_url}/sitemap_projects_3.xml",  # 938 servers
            f"{base_url}/sitemap_projects_4.xml",  # 766 servers
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                print(f"  📄 Processing {sitemap_url}...")
                async with self.session.get(sitemap_url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        
                        # Extract URLs from XML sitemap
                        import re
                        urls = re.findall(r'<loc>(https://mcp\.so/server/[^<]+)</loc>', xml_content)
                        
                        for url in urls:
                            server_urls.add(url)
                        
                        print(f"    ✅ Found {len(urls)} servers in this sitemap")
                    else:
                        print(f"    ⚠️  Failed to access {sitemap_url}: {response.status}")
                        
            except Exception as e:
                print(f"    ❌ Error processing {sitemap_url}: {e}")
                continue
        
        print(f"🎯 Total servers discovered from sitemaps: {len(server_urls)}")
        
        # Also try the homepage for any additional servers not in sitemaps
        homepage_urls = await self._get_homepage_servers(base_url)
        server_urls.update(homepage_urls)
        
        return list(server_urls)
    
    async def _get_homepage_servers(self, base_url: str) -> List[str]:
        """Get servers from homepage tabs as fallback"""
        server_urls = set()
        
        # Pages to check for server listings  
        pages_to_check = [
            base_url,
            f"{base_url}/?tab=featured",
            f"{base_url}/?tab=latest", 
            f"{base_url}/?tab=today",
            f"{base_url}/?tab=hosted",
            f"{base_url}/?tab=official",
            f"{base_url}/?tab=innovations"
        ]
        
        for page_url in pages_to_check:
            try:
                async with self.session.get(page_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find all server links (pattern: /server/{name}/{author})
                        server_links = soup.find_all('a', href=re.compile(r'/server/'))
                        
                        for link in server_links:
                            href = link.get('href')
                            if href and '/server/' in href:
                                if href.startswith('/'):
                                    full_url = f"https://mcp.so{href}"
                                elif href.startswith('http'):
                                    full_url = href
                                else:
                                    continue
                                server_urls.add(full_url)
                        
                        # Also look for any other patterns
                        all_links = soup.find_all('a', href=True)
                        for link in all_links:
                            href = link.get('href')
                            if href and '/server/' in href and href.count('/') >= 4:
                                if href.startswith('/'):
                                    full_url = f"https://mcp.so{href}"
                                elif href.startswith('http'):
                                    full_url = href
                                else:
                                    continue
                                server_urls.add(full_url)
                
            except Exception as e:
                print(f"  Error discovering servers from {page_url}: {e}")
                continue
            
            await asyncio.sleep(1)  # Rate limiting
        
        return list(server_urls)
    
    async def _scrape_server_detail(self, server_url: str) -> Optional[MCPServer]:
        """Scrape detailed information from a server page"""
        try:
            async with self.session.get(server_url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract server metadata
                name = None
                author = None
                description = None
                repository = None
                tags = []
                
                # Extract name from title or h1
                title_elem = soup.find('h1') or soup.find('title')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if ' by ' in title_text:
                        name, author = title_text.split(' by ', 1)
                    else:
                        name = title_text
                
                # Extract description from meta or first paragraph
                desc_meta = soup.find('meta', {'name': 'description'})
                if desc_meta:
                    description = desc_meta.get('content')
                else:
                    desc_elem = soup.find('p')
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                
                # Extract repository URL
                repo_links = soup.find_all('a', href=re.compile(r'github\.com'))
                if repo_links:
                    repository = repo_links[0].get('href')
                
                # Extract tags
                tag_elements = soup.find_all(['span', 'div'], class_=re.compile(r'tag|label|badge'))
                for tag_elem in tag_elements:
                    tag_text = tag_elem.get_text(strip=True)
                    if tag_text.startswith('#'):
                        tags.append(tag_text[1:])
                    elif len(tag_text) < 20:  # Likely a tag
                        tags.append(tag_text)
                
                # Extract from URL if name/author not found
                if not name or not author:
                    url_parts = server_url.split('/')
                    if len(url_parts) >= 6:
                        if not name:
                            name = url_parts[-2]
                        if not author:
                            author = url_parts[-1]
                
                if not name:
                    return None
                
                server_id = f"mcp_so_{name.lower().replace(' ', '_').replace('-', '_')}"
                categories = self.categorize_server({'name': name, 'description': description or '', 'tags': tags})
                
                return MCPServer(
                    id=server_id,
                    name=name,
                    description=description,
                    author=author,
                    repository=repository,
                    categories=categories,
                    operations=self.determine_operations({'tags': tags}),
                    data_types=tags,
                    registry_source=RegistrySource.MCP_SO,
                    source_url=server_url
                )
                
        except Exception as e:
            print(f"Error scraping server detail {server_url}: {e}")
            return None
    
    def _parse_mcp_so_server(self, element) -> Optional[MCPServer]:
        try:
            name_elem = element.find(['h1', 'h2', 'h3', 'h4'])
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            description = None
            
            desc_elem = element.find('p')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract links
            links = element.find_all('a', href=True)
            repository = None
            homepage = None
            
            for link in links:
                href = link['href']
                if 'github.com' in href:
                    repository = href
                elif href.startswith('http'):
                    homepage = href
            
            server_id = f"mcp_so_{name.lower().replace(' ', '_')}"
            categories = self.categorize_server({'name': name, 'description': description or ''})
            
            return MCPServer(
                id=server_id,
                name=name,
                description=description,
                repository=repository,
                homepage=homepage,
                categories=categories,
                operations=[OperationType.READ],  # Default
                registry_source=RegistrySource.MCP_SO,
                source_url=f"https://mcp.so#{server_id}"
            )
        except Exception as e:
            print(f"Error parsing MCP.so server: {e}")
            return None


class GlamaScraper(BaseScraper):
    async def scrape(self) -> RegistrySnapshot:
        servers = []
        
        # Use Glama API to get all servers
        api_servers = await self._scrape_glama_api()
        servers.extend(api_servers)
        print(f"  Found {len(api_servers)} servers from Glama API")
        
        # Search GitHub for glama.json files
        github_token = self.config.get('github.token')
        if github_token:
            glama_servers = await self._search_glama_json_files()
            servers.extend(glama_servers)
            print(f"  Found {len(glama_servers)} additional servers from glama.json files")
        
        # Scrape Glama website for any missed servers
        base_url = self.config.get('registries.glama.base_url', 'https://glama.ai/mcp')
        web_servers = await self._scrape_glama_website(base_url)
        servers.extend(web_servers)
        print(f"  Found {len(web_servers)} additional servers from Glama website")
        
        return RegistrySnapshot(
            registry_source=RegistrySource.GLAMA,
            snapshot_date=datetime.now(),
            url=base_url,
            servers_count=len(servers),
            servers=servers
        )
    
    async def _scrape_glama_api(self) -> List[MCPServer]:
        """Scrape servers using Glama's API with pagination"""
        servers = []
        
        try:
            # Start with the first page
            api_url = "https://glama.ai/api/mcp/v1/servers"
            cursor = None
            page_count = 0
            
            # First request to get total info
            print("🔍 Discovering Glama servers...")
            async with self.session.get(api_url) as response:
                if response.status != 200:
                    print(f"  API request failed with status {response.status}")
                    return []
                
                data = await response.json()
                if not isinstance(data, dict) or 'servers' not in data:
                    print(f"  Unexpected API response structure: {type(data)}")
                    return []
                
                # Process first page
                page_servers = data['servers']
                for server_data in page_servers:
                    server = self._process_glama_api_server(server_data)
                    if server:
                        servers.append(server)
                
                page_count = 1
                cursor = data.get('pageInfo', {}).get('endCursor')
                has_next = data.get('pageInfo', {}).get('hasNextPage', False)
            
            # Continue with remaining pages if any
            if has_next:
                # We don't know exact total, so use indeterminate progress
                with tqdm(desc="📡 Fetching Glama API pages", unit="page") as pbar:
                    pbar.update(1)  # First page already done
                    
                    while cursor and has_next and page_count < 1000:
                        url = f"{api_url}?after={cursor}"
                        
                        async with self.session.get(url) as response:
                            if response.status != 200:
                                break
                            
                            data = await response.json()
                            if not isinstance(data, dict) or 'servers' not in data:
                                break
                            
                            page_servers = data['servers']
                            
                            # Process servers from this page
                            for server_data in page_servers:
                                server = self._process_glama_api_server(server_data)
                                if server:
                                    servers.append(server)
                            
                            page_count += 1
                            pbar.set_postfix_str(f"{len(servers)} servers found")
                            pbar.update(1)
                            
                            # Check if there are more pages
                            page_info = data.get('pageInfo', {})
                            has_next = page_info.get('hasNextPage', False)
                            cursor = page_info.get('endCursor')
                            
                            # Rate limiting
                            await asyncio.sleep(0.5)
            
            print(f"✅ Glama API: {len(servers)} servers found across {page_count} pages")
                
        except Exception as e:
            print(f"❌ Error accessing Glama API: {e}")
        
        return servers
    
    def _process_glama_api_server(self, server_data: Dict[str, Any]) -> Optional[MCPServer]:
        """Process server data from Glama API"""
        try:
            name = server_data.get('name')
            if not name:
                return None
            
            # Extract namespace/author
            namespace = server_data.get('namespace', '')
            author = namespace if namespace else None
            
            # Create unique server ID
            server_id = f"glama_{server_data.get('id', name.lower().replace(' ', '_').replace('-', '_'))}"
            
            # Get repository URL
            repository = None
            repo_info = server_data.get('repository', {})
            if isinstance(repo_info, dict):
                repository = repo_info.get('url')
            elif isinstance(repo_info, str):
                repository = repo_info
            
            # Get license info
            license_info = server_data.get('spdxLicense', {})
            license_name = None
            if isinstance(license_info, dict):
                license_name = license_info.get('name')
            
            # Get tools and attributes
            tools = server_data.get('tools', [])
            attributes = server_data.get('attributes', [])
            
            # Build MCPTool objects
            mcp_tools = []
            for tool in tools:
                if isinstance(tool, dict):
                    mcp_tools.append(MCPTool(
                        name=tool.get('name', ''),
                        description=tool.get('description'),
                        parameters=tool.get('parameters')
                    ))
            
            categories = self.categorize_server(server_data)
            operations = self.determine_operations({'tools': tools, 'attributes': attributes})
            
            return MCPServer(
                id=server_id,
                name=name,
                description=server_data.get('description'),
                author=author,
                license=license_name,
                repository=repository,
                tools=mcp_tools if mcp_tools else None,
                categories=categories,
                operations=operations,
                data_types=attributes,
                registry_source=RegistrySource.GLAMA,
                source_url=server_data.get('url', f"https://glama.ai/mcp/servers/{server_data.get('slug', server_data.get('id', ''))}"),
                raw_metadata=server_data
            )
            
        except Exception as e:
            print(f"  Error processing Glama API server {server_data.get('name', 'unknown')}: {e}")
            return None
    
    async def _scrape_glama_paginated(self) -> List[MCPServer]:
        """Scrape Glama servers with pagination"""
        servers = []
        base_url = "https://glama.ai/mcp/servers"
        
        # Try different sorting and pagination
        sort_options = ['relevance', 'date', 'downloads', 'stars']
        
        for sort_by in sort_options:
            page = 1
            while page <= 20:  # Limit to 20 pages per sort option
                try:
                    url = f"{base_url}?sort={sort_by}&page={page}"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Look for server cards/listings
                            server_elements = soup.find_all(['div', 'article'], class_=re.compile(r'server|card|listing'))
                            
                            if not server_elements:
                                break  # No more servers on this page
                            
                            for element in server_elements:
                                server = self._parse_glama_server_element(element)
                                if server:
                                    servers.append(server)
                        
                        else:
                            break  # Error, move to next sort option
                
                except Exception as e:
                    print(f"Error scraping Glama page {page} with sort {sort_by}: {e}")
                    break
                
                page += 1
                await asyncio.sleep(1)  # Rate limiting
        
        return servers
    
    def _parse_glama_server_element(self, element) -> Optional[MCPServer]:
        """Parse a server element from Glama website"""
        try:
            # Extract server name
            name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            if not name:
                return None
            
            # Extract description
            desc_elem = element.find('p') or element.find('div', class_=re.compile(r'description'))
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract GitHub link
            repo_link = element.find('a', href=re.compile(r'github\.com'))
            repository = repo_link.get('href') if repo_link else None
            
            # Extract author from GitHub URL or name
            author = None
            if repository and 'github.com' in repository:
                parts = repository.split('/')
                if len(parts) >= 5:
                    author = parts[3]
            
            # Extract stats
            star_elem = element.find(text=re.compile(r'star|★'))
            download_elem = element.find(text=re.compile(r'download|⬇'))
            
            server_id = f"glama_web_{name.lower().replace(' ', '_').replace('-', '_')}"
            categories = self.categorize_server({'name': name, 'description': description or ''})
            
            return MCPServer(
                id=server_id,
                name=name,
                description=description,
                author=author,
                repository=repository,
                categories=categories,
                operations=[OperationType.READ],  # Default
                registry_source=RegistrySource.GLAMA,
                source_url=f"https://glama.ai/mcp/servers/{name}"
            )
            
        except Exception as e:
            print(f"Error parsing Glama server element: {e}")
            return None
    
    async def _search_glama_json_files(self) -> List[MCPServer]:
        headers = {'Authorization': f'token {self.config.get("github.token")}'}
        servers = []
        
        # Search for glama.json files
        search_url = "https://api.github.com/search/code?q=filename:glama.json"
        
        async with self.session.get(search_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                for item in data.get('items', [])[:50]:  # Limit to avoid rate limits
                    server = await self._process_glama_json(item, headers)
                    if server:
                        servers.append(server)
        
        return servers
    
    async def _process_glama_json(self, item: Dict[str, Any], headers: Dict[str, str]) -> Optional[MCPServer]:
        try:
            # Get the actual file content
            download_url = item.get('download_url')
            if not download_url:
                return None
            
            async with self.session.get(download_url, headers=headers) as response:
                if response.status == 200:
                    glama_data = await response.json()
                    
                    server_id = f"glama_{item['repository']['name']}"
                    
                    return MCPServer(
                        id=server_id,
                        name=glama_data.get('name', item['repository']['name']),
                        description=glama_data.get('description'),
                        version=glama_data.get('version'),
                        author=glama_data.get('author'),
                        repository=item['repository']['html_url'],
                        categories=self.categorize_server(glama_data),
                        operations=self.determine_operations(glama_data),
                        registry_source=RegistrySource.GLAMA,
                        source_url=item['html_url'],
                        raw_metadata=glama_data
                    )
        except Exception as e:
            print(f"Error processing glama.json: {e}")
            return None
    
    async def _scrape_glama_website(self, base_url: str) -> List[MCPServer]:
        # Placeholder for scraping Glama website
        # Implementation depends on the actual website structure
        return []


class MCPMarketScraper(BaseScraper):
    async def scrape(self) -> RegistrySnapshot:
        start_time = time.time()
        base_url = self.config.get('registries.mcp_market.base_url', 'https://mcpmarket.com')
        servers = []
        
        print("🔍 Attempting to scrape mcpmarket.com...")
        print("⚠️  Note: mcpmarket.com currently uses Vercel security protection")
        print("   This may prevent automated scraping until protection is bypassed")
        
        try:
            # Try multiple approaches to access the site
            servers = await self._scrape_with_retry(base_url)
            
            if not servers:
                print("   No valid servers found - likely blocked by security measures")
                print("   mcpmarket.com will need manual configuration or API access")
            
        except Exception as e:
            print(f"⚠️  mcpmarket.com scraping failed: {e}")
            print("   This is expected due to Vercel security checkpoint")
        
        elapsed_time = time.time() - start_time
        print(f"✅ mcpmarket.com scraping completed in {elapsed_time:.1f}s")
        
        return RegistrySnapshot(
            registry_source=RegistrySource.MCP_MARKET,
            snapshot_date=datetime.now(),
            url=base_url,
            servers_count=len(servers),
            servers=servers
        )
    
    async def _scrape_with_retry(self, base_url: str) -> List[MCPServer]:
        """Try multiple approaches to scrape the site"""
        servers = []
        
        # Approach 1: Try direct access with different headers
        headers = [
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            {'User-Agent': 'MCP-Knowledge-Graph-Scraper/1.0'},
        ]
        
        for header in headers:
            try:
                async with self.session.get(base_url, headers=header) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Check if we hit a security checkpoint
                        if ('vercel security checkpoint' in html.lower() or 
                            'we\'re verifying your browser' in html.lower() or
                            'data-astro-cid-nbv56vs3' in html or
                            len(html) < 1000):  # Suspiciously small page
                            print(f"  Hit security checkpoint or invalid page with header: {header['User-Agent'][:30]}...")
                            continue
                        
                        # If we get valid HTML, try to parse it
                        servers = await self._parse_mcpmarket_html(html, base_url)
                        if servers:
                            print(f"  ✅ Successfully scraped with header: {header['User-Agent'][:30]}...")
                            return servers
                        else:
                            print(f"  No servers found in HTML with header: {header['User-Agent'][:30]}...")
                        
                await asyncio.sleep(2)  # Rate limiting between attempts
                
            except Exception as e:
                print(f"  Failed with header {header['User-Agent'][:30]}: {e}")
                continue
        
        # Approach 2: Try to find API endpoints
        api_endpoints = [
            f"{base_url}/api/servers",
            f"{base_url}/api/mcp/servers", 
            f"{base_url}/api/v1/servers",
            f"{base_url}/.netlify/functions/servers",
            f"{base_url}/servers.json",
        ]
        
        for endpoint in api_endpoints:
            try:
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        servers = await self._parse_mcpmarket_api(data)
                        if servers:
                            print(f"  ✅ Found API endpoint: {endpoint}")
                            return servers
            except Exception:
                continue
        
        # Approach 3: Check for sitemap or robots.txt
        try:
            sitemap_servers = await self._scrape_from_sitemap(base_url)
            if sitemap_servers:
                return sitemap_servers
        except Exception:
            pass
        
        return servers
    
    async def _parse_mcpmarket_html(self, html: str, base_url: str) -> List[MCPServer]:
        """Parse HTML to extract MCP server information"""
        servers = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for common patterns that might indicate server listings
            patterns = [
                # Server cards/tiles
                {'tag': 'div', 'class': re.compile(r'(server|card|tile|item)')},
                {'tag': 'article', 'class': re.compile(r'(server|mcp)')},
                
                # Links to individual servers
                {'tag': 'a', 'href': re.compile(r'/(server|mcp)/')},
                
                # Lists of servers
                {'tag': 'li', 'class': re.compile(r'server')},
            ]
            
            for pattern in patterns:
                elements = soup.find_all(pattern['tag'], pattern.get('class') or pattern.get('href'))
                
                for element in elements:
                    server = await self._parse_mcpmarket_element(element, base_url)
                    if server:
                        servers.append(server)
            
            # Remove duplicates by name
            seen_names = set()
            unique_servers = []
            for server in servers:
                if server.name not in seen_names:
                    unique_servers.append(server)
                    seen_names.add(server.name)
            
            return unique_servers
            
        except Exception as e:
            print(f"  Error parsing HTML: {e}")
            return []
    
    async def _parse_mcpmarket_element(self, element, base_url: str) -> Optional[MCPServer]:
        """Parse a single HTML element to extract server info"""
        try:
            # Extract name
            name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element.find('a')
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            if not name or len(name) < 2:
                return None
            
            # Extract description
            desc_elem = element.find('p') or element.find('div', class_=re.compile(r'desc'))
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract repository link
            repo_link = element.find('a', href=re.compile(r'github\.com'))
            repository = repo_link.get('href') if repo_link else None
            
            # Extract author from repository or other sources
            author = None
            if repository and 'github.com' in repository:
                parts = repository.split('/')
                if len(parts) >= 5:
                    author = parts[3]
            
            # Look for author in other places
            if not author:
                author_elem = element.find(['span', 'div'], class_=re.compile(r'author|by'))
                if author_elem:
                    author = author_elem.get_text(strip=True).replace('by ', '').replace('By ', '')
            
            # Create temporary server ID (will be converted to global ID later)
            server_id = f"mcpmarket_{name.lower().replace(' ', '-').replace('_', '-')}"
            
            # Categorize
            categories = self.categorize_server({'name': name, 'description': description or ''})
            
            return MCPServer(
                id=server_id,
                name=name,
                description=description,
                author=author,
                repository=repository,
                categories=categories,
                operations=self.determine_operations({'name': name, 'description': description}),
                registry_source=RegistrySource.MCP_MARKET,
                source_url=f"{base_url}/server/{name.lower().replace(' ', '-')}"
            )
            
        except Exception as e:
            print(f"    Error parsing element: {e}")
            return None
    
    async def _parse_mcpmarket_api(self, data: Dict[str, Any]) -> List[MCPServer]:
        """Parse API response to extract server information"""
        servers = []
        
        try:
            # Handle different API response formats
            server_list = None
            
            if isinstance(data, dict):
                # Try common API response patterns
                for key in ['servers', 'data', 'items', 'results']:
                    if key in data and isinstance(data[key], list):
                        server_list = data[key]
                        break
            elif isinstance(data, list):
                server_list = data
            
            if not server_list:
                return servers
            
            for server_data in server_list:
                if not isinstance(server_data, dict):
                    continue
                
                name = server_data.get('name') or server_data.get('title')
                if not name:
                    continue
                
                # Create temporary server ID (will be converted to global ID later)
                server_id = f"mcpmarket_{name.lower().replace(' ', '-').replace('_', '-')}"
                
                server = MCPServer(
                    id=server_id,
                    name=name,
                    description=server_data.get('description'),
                    author=server_data.get('author') or server_data.get('owner'),
                    repository=server_data.get('repository') or server_data.get('repo_url'),
                    categories=self.categorize_server(server_data),
                    operations=self.determine_operations(server_data),
                    registry_source=RegistrySource.MCP_MARKET,
                    source_url=server_data.get('url'),
                    raw_metadata=server_data
                )
                
                servers.append(server)
            
        except Exception as e:
            print(f"  Error parsing API data: {e}")
        
        return servers
    
    async def _scrape_from_sitemap(self, base_url: str) -> List[MCPServer]:
        """Try to find servers via sitemap"""
        servers = []
        
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap/servers.xml",
            f"{base_url}/robots.txt"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                async with self.session.get(sitemap_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        if sitemap_url.endswith('.xml'):
                            # Parse XML sitemap
                            server_urls = re.findall(r'<loc>(.*?/server/.*?)</loc>', content)
                            for url in server_urls:
                                # Could scrape individual server pages
                                pass
                        elif sitemap_url.endswith('robots.txt'):
                            # Look for sitemap references
                            sitemap_refs = re.findall(r'Sitemap: (.*)', content)
                            for ref in sitemap_refs:
                                # Could recursively check sitemaps
                                pass
                                
            except Exception:
                continue
        
        return servers


class ScrapingOrchestrator:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = ConfigManager(config_path)
        self.storage = StorageManager(self.config)
        
        self.scrapers = {
            RegistrySource.GITHUB: GitHubScraper,
            RegistrySource.MCP_SO: MCPSoScraper,
            RegistrySource.GLAMA: GlamaScraper,
            RegistrySource.MCP_MARKET: MCPMarketScraper
        }
    
    async def scrape_all(self, force_refresh: bool = False) -> List[RegistrySnapshot]:
        overall_start = time.time()
        snapshots = []
        
        print(f"🚀 Starting scraping of {len(self.scrapers)} registries...")
        
        with tqdm(total=len(self.scrapers), desc="📦 Registry Progress", unit="registry") as pbar:
            for registry, scraper_class in self.scrapers.items():
                registry_start = time.time()
                pbar.set_postfix_str(f"Processing {registry.value}")
                
                try:
                    # Check if we need to scrape
                    if not force_refresh:
                        latest = self.storage.load_latest_snapshot(registry)
                        if latest and (datetime.now() - latest.snapshot_date).days < 1:
                            elapsed = datetime.now() - latest.snapshot_date
                            pbar.set_postfix_str(f"Using cache ({elapsed.seconds//3600}h old)")
                            snapshots.append(latest)
                            pbar.update(1)
                            continue
                    
                    async with scraper_class(self.config, self.storage) as scraper:
                        snapshot = await scraper.scrape()
                        self.storage.save_snapshot(snapshot)
                        snapshots.append(snapshot)
                    
                    registry_time = time.time() - registry_start
                    pbar.set_postfix_str(f"✅ {snapshot.servers_count} servers ({registry_time:.1f}s)")
                    
                except Exception as e:
                    pbar.set_postfix_str(f"❌ Error: {str(e)[:30]}...")
                    print(f"\n❌ Error scraping {registry.value}: {e}")
                
                pbar.update(1)
        
        overall_time = time.time() - overall_start
        total_servers = sum(s.servers_count for s in snapshots)
        print(f"\n🎉 Scraping completed in {overall_time:.1f}s")
        print(f"📊 Total servers discovered: {total_servers}")
        
        return snapshots
    
    async def scrape_registry(self, registry: RegistrySource, force_refresh: bool = False) -> Optional[RegistrySnapshot]:
        if registry not in self.scrapers:
            raise ValueError(f"Unknown registry: {registry}")
        
        if not force_refresh:
            latest = self.storage.load_latest_snapshot(registry)
            if latest and (datetime.now() - latest.snapshot_date).days < 1:
                return latest
        
        scraper_class = self.scrapers[registry]
        
        async with scraper_class(self.config, self.storage) as scraper:
            snapshot = await scraper.scrape()
            self.storage.save_snapshot(snapshot)
            return snapshot