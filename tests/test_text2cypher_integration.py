#!/usr/bin/env python3
"""Integration test for text2cypher functionality with MCP server"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import ASKGMCPServer, ServerSearchRequest


async def test_text2cypher_integration():
    """Test the text2cypher integration with MCP server"""
    
    print("🧪 Testing Text2Cypher Integration")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Find database servers",
        "Show me file system tools",
        "Find popular AI servers",
        "What are the best monitoring tools?",
        "Find servers that can read and write files"
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
                    for j, server_result in enumerate(result.servers[:3], 1):
                        print(f"  {j}. {server_result.name} (Score: {server_result.raw_metadata.get('search_score', 'N/A')})")
                        print(f"     Categories: {[cat.value for cat in server_result.categories]}")
                        print(f"     Operations: {[op.value for op in server_result.operations]}")
                else:
                    print("  No servers found")
                    
            except Exception as e:
                print(f"❌ Error testing query '{query}': {e}")
        
        # Clean up
        server.close()
        print("\n✅ Integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Failed to initialize MCP server: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Neo4j running and accessible")
        print("   2. .config.yaml file with proper Neo4j configuration")
        print("   3. OpenAI API key set (optional, for enhanced search)")


if __name__ == "__main__":
    asyncio.run(test_text2cypher_integration()) 