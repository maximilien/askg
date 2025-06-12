#!/usr/bin/env python3
"""
Debug script to test individual scrapers and see what's happening
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_mcp_so():
    """Test mcp.so scraping"""
    print("Testing mcp.so scraping...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://mcp.so") as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                print(f"Page title: {soup.title.get_text() if soup.title else 'No title'}")
                print(f"Page length: {len(html)} characters")
                
                # Look for server links
                server_links = soup.find_all('a', href=True)
                mcp_links = [link for link in server_links if '/server/' in link.get('href', '')]
                
                print(f"Found {len(mcp_links)} potential server links")
                for i, link in enumerate(mcp_links[:5]):  # Show first 5
                    print(f"  {i+1}: {link.get('href')} - {link.get_text(strip=True)}")
                
                # Look for any element that might contain servers
                divs = soup.find_all('div')
                print(f"Found {len(divs)} div elements")
                
                # Look for specific patterns
                patterns = ['server', 'mcp', 'card', 'listing', 'item']
                for pattern in patterns:
                    elements = soup.find_all(attrs={'class': lambda x: x and pattern in str(x).lower()})
                    if elements:
                        print(f"Found {len(elements)} elements with '{pattern}' in class")

async def test_glama():
    """Test Glama API"""
    print("\nTesting Glama API...")
    
    async with aiohttp.ClientSession() as session:
        # Test main API endpoint
        try:
            async with session.get("https://glama.ai/api/mcp/v1/servers") as response:
                print(f"API Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"API Response type: {type(data)}")
                    if isinstance(data, list):
                        print(f"Found {len(data)} servers in API")
                    elif isinstance(data, dict):
                        print(f"API response keys: {data.keys()}")
        except Exception as e:
            print(f"API Error: {e}")
        
        # Test main website
        try:
            async with session.get("https://glama.ai/mcp") as response:
                print(f"Website Status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    print(f"Website title: {soup.title.get_text() if soup.title else 'No title'}")
                    print(f"Website length: {len(html)} characters")
                    
                    # Look for server listings
                    server_links = soup.find_all('a', href=lambda x: x and 'servers' in x)
                    print(f"Found {len(server_links)} server-related links")
        except Exception as e:
            print(f"Website Error: {e}")

async def test_github_search():
    """Test GitHub search with specific queries"""
    print("\nTesting GitHub search...")
    
    # You'll need to set your GitHub token in config.yaml
    import yaml
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        github_token = config.get('github', {}).get('token')
        if not github_token:
            print("No GitHub token found in config.yaml")
            return
        
        headers = {'Authorization': f'token {github_token}'}
        
        async with aiohttp.ClientSession() as session:
            # Test a simple search
            query = "mcp server in:readme"
            url = f"https://api.github.com/search/repositories?q={query}&per_page=5"
            
            async with session.get(url, headers=headers) as response:
                print(f"GitHub API Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    total_count = data.get('total_count', 0)
                    items = data.get('items', [])
                    
                    print(f"Total repositories found: {total_count}")
                    print(f"Returned in this request: {len(items)}")
                    
                    for i, repo in enumerate(items):
                        print(f"  {i+1}: {repo['full_name']} - {repo['description'][:50] if repo.get('description') else 'No description'}")
                
                elif response.status == 403:
                    print("Rate limited or authentication error")
                else:
                    print(f"Error: {response.status}")
    
    except Exception as e:
        print(f"GitHub test error: {e}")

async def main():
    """Run all debug tests"""
    await test_mcp_so()
    await test_glama()
    await test_github_search()

if __name__ == "__main__":
    asyncio.run(main())