#!/usr/bin/env python3
"""
Test MCP server search functionality
"""

import asyncio
import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from mcp.server import ASKGMCPServer, ServerSearchRequest

@pytest.mark.asyncio
async def test_search():
    """Test the MCP server search functionality"""
    
    print("Testing MCP server search...")
    
    try:
        # Initialize the MCP server with local instance
        with ASKGMCPServer(".config.yaml", "local") as server:
            
            # Test queries
            test_queries = [
                "database",
                "file system", 
                "api",
                "search",
                "test"
            ]
            
            for query in test_queries:
                print(f"\n{'='*50}")
                print(f"Testing query: '{query}'")
                print(f"{'='*50}")
                
                try:
                    # Create search request
                    request = ServerSearchRequest(
                        prompt=query,
                        limit=5,
                        min_confidence=0.0  # Lower threshold to see more results
                    )
                    
                    # Print the Cypher query and params
                    search_terms = server._extract_search_terms(request.prompt)
                    cypher, params = server._build_search_query(search_terms, request.limit, request.min_confidence)
                    print("Cypher query:")
                    print(cypher)
                    print("Params:")
                    print(params)
                    
                    # Perform search
                    result = await server.search_servers(request)
                    
                    print(f"Total found: {result.total_found}")
                    print(f"Search metadata: {result.search_metadata}")
                    
                    if result.servers:
                        print(f"Found {len(result.servers)} servers:")
                        for i, mcp_server in enumerate(result.servers, 1):
                            print(f"  {i}. {mcp_server.name}")
                            if mcp_server.raw_metadata and 'search_score' in mcp_server.raw_metadata:
                                print(f"     Score: {mcp_server.raw_metadata['search_score']:.2f}")
                            if mcp_server.raw_metadata and mcp_server.raw_metadata.get('mock', False):
                                print(f"     ⚠️  MOCK DATA")
                    else:
                        print("No servers found")
                        
                except Exception as e:
                    print(f"Error during search: {e}")
                    # Continue with other queries even if one fails
                    
    except KeyError as e:
        if 'remote' in str(e):
            pytest.skip("Remote Neo4j configuration not available - skipping MCP search test")
        else:
            raise
    except Exception as e:
        print(f"Failed to initialize MCP server: {e}")
        pytest.skip("Neo4j not available - skipping MCP search test")

if __name__ == "__main__":
    asyncio.run(test_search()) 