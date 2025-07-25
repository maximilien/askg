#!/usr/bin/env python3
"""Test script to debug crypto queries and text2cypher conversion"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from text2cypher import Text2CypherConverter


def test_crypto_queries():
    """Test crypto-related queries to debug text2cypher conversion"""
    
    print("🔍 Testing Crypto Queries")
    print("=" * 40)
    
    # Test queries
    test_queries = [
        "crypto",
        "popular servers for crypto",
        "Find crypto servers",
        "Show me blockchain tools",
        "What are the best cryptocurrency servers?"
    ]
    
    try:
        # Initialize converter
        converter = Text2CypherConverter()
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: '{query}'")
            print("-" * 30)
            
            try:
                # Convert to Cypher
                result = converter.convert_to_cypher(query, limit=5, min_confidence=0.3)
                
                print(f"✅ Cypher Query:")
                print(result["cypher"])
                print(f"\n📋 Parameters:")
                for key, value in result["parameters"].items():
                    print(f"  {key}: {value}")
                
                # Test the search terms extraction
                search_terms = converter._extract_search_terms(query)
                print(f"\n🔍 Extracted Search Terms:")
                print(f"  Categories: {search_terms['categories']}")
                print(f"  Operations: {search_terms['operations']}")
                print(f"  Keywords: {search_terms['keywords']}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Failed to initialize converter: {e}")
        print("\n💡 This is expected if you don't have an OpenAI API key set.")


if __name__ == "__main__":
    test_crypto_queries() 