#!/usr/bin/env python3
"""Test the fallback query to debug why it returns the same results"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import ASKGMCPServer, ServerSearchRequest


async def test_fallback_queries():
    """Test different queries to see if they return different results"""
    
    print("🔍 Testing Fallback Query Results")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "crypto",
        "popular servers for crypto", 
        "Find crypto servers",
        "database servers",
        "file system tools"
    ]
    
    try:
        # Initialize the MCP server
        print("📡 Initializing MCP server...")
        server = ASKGMCPServer(".config.yaml", "local")
        
        print(f"🔧 Text2Cypher available: {server.text2cypher is not None}")
        
        # Test each query
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: '{query}'")
            print("-" * 30)
            
            try:
                # Create search request
                request = ServerSearchRequest(
                    prompt=query,
                    limit=5,
                    min_confidence=0.3
                )
                
                # Perform search
                result = await server.search_servers(request)
                
                # Display results
                print(f"✅ Found {result.total_found} servers")
                print(f"🔧 Search strategy: {result.search_metadata.get('search_strategy', 'unknown')}")
                print(f"🔄 Query conversion: {result.search_metadata.get('query_conversion', 'unknown')}")
                
                if result.servers:
                    print("  Top 3 results:")
                    for j, server_result in enumerate(result.servers[:3], 1):
                        print(f"    {j}. {server_result.name}")
                        print(f"       Score: {server_result.raw_metadata.get('search_score', 'N/A')}")
                        print(f"       Categories: {[cat.value for cat in server_result.categories]}")
                else:
                    print("  No servers found")
                    
            except Exception as e:
                print(f"❌ Error testing query '{query}': {e}")
        
        # Clean up
        server.close()
        print("\n✅ Fallback query test completed!")
        
    except Exception as e:
        print(f"❌ Failed to initialize MCP server: {e}")


if __name__ == "__main__":
    asyncio.run(test_fallback_queries()) 