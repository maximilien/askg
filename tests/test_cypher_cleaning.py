#!/usr/bin/env python3
"""Test script to verify Cypher query cleaning fix"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from text2cypher import Text2CypherConverter


def test_cypher_cleaning():
    """Test the Cypher query cleaning functionality"""
    
    print("🧪 Testing Cypher Query Cleaning")
    print("=" * 40)
    
    # Test cases that were causing issues
    test_cases = [
        {
            "name": "Markdown with cypher language",
            "input": "```cypher\nMATCH (s:Server)\nWHERE (s.name CONTAINS $query OR s.description CONTAINS $query)\nAND s.popularity_score >= $min_confidence\nRETURN s\nORDER BY s.popularity_score DESC\nLIMIT $limit\n```",
            "expected_start": "MATCH (s:Server)"
        },
        {
            "name": "Regular markdown code block",
            "input": "```\nMATCH (s:Server) WHERE 'database' IN s.categories RETURN s\n```",
            "expected_start": "MATCH (s:Server)"
        },
        {
            "name": "Clean query (no markdown)",
            "input": "MATCH (s:Server) WHERE 'ai' IN s.categories RETURN s",
            "expected_start": "MATCH (s:Server)"
        },
        {
            "name": "Query with extra whitespace",
            "input": "```cypher\n  MATCH (s:Server)  \n  WHERE 'file' IN s.categories  \n  RETURN s  \n```",
            "expected_start": "MATCH (s:Server)"
        }
    ]
    
    try:
        # Initialize converter (will fail without API key, but we can test the cleaning function)
        converter = Text2CypherConverter()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['name']}")
            print("-" * 30)
            
            try:
                # Clean the query
                cleaned = converter._clean_cypher_query(test_case['input'])
                
                print(f"Input: {repr(test_case['input'][:50])}...")
                print(f"Cleaned: {repr(cleaned)}")
                
                # Verify the cleaned query starts correctly
                if cleaned.startswith(test_case['expected_start']):
                    print("✅ PASS: Query cleaned successfully")
                else:
                    print(f"❌ FAIL: Expected to start with '{test_case['expected_start']}'")
                    print(f"   Actual: '{cleaned[:len(test_case['expected_start'])+10]}'")
                
                # Verify no markdown artifacts remain
                if "```" in cleaned:
                    print("❌ FAIL: Markdown code blocks still present")
                else:
                    print("✅ PASS: No markdown artifacts")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Failed to initialize converter: {e}")
        print("\n💡 This is expected if you don't have an OpenAI API key set.")
        print("   The cleaning functionality should still work for testing purposes.")


if __name__ == "__main__":
    test_cypher_cleaning() 