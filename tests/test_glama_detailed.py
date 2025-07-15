#!/usr/bin/env python3
"""
Detailed test of Glama API to understand the data structure
"""

import asyncio
import aiohttp
import json

async def test_glama_detailed():
    """Test Glama API in detail"""
    print("Testing Glama API in detail...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://glama.ai/api/mcp/v1/servers") as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                
                print(f"Response type: {type(data)}")
                print(f"Response keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
                
                if isinstance(data, dict):
                    if 'servers' in data:
                        servers = data['servers']
                        print(f"Number of servers: {len(servers)}")
                        
                        if servers:
                            print("\nFirst server structure:")
                            first_server = servers[0]
                            print(json.dumps(first_server, indent=2))
                            
                            print("\nFirst 5 server names:")
                            for i, server in enumerate(servers[:5]):
                                name = server.get('name', 'No name')
                                desc = server.get('description', 'No description')[:50]
                                print(f"  {i+1}: {name} - {desc}")
                    
                    if 'pageInfo' in data:
                        page_info = data['pageInfo']
                        print(f"\nPage info: {page_info}")

if __name__ == "__main__":
    asyncio.run(test_glama_detailed())