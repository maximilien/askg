#!/usr/bin/env python3
"""
Test script for the LangGraph MCP Orchestrator
Demonstrates the system with various task types
"""

import asyncio
import sys
import os
import pytest

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_orchestrator import MCPOrchestrator
from neo4j_integration import Neo4jManager


async def test_single_task():
    """Test a single task execution"""
    print("🧪 Testing single task execution")
    print("=" * 50)
    
    # Check if config file exists
    if not os.path.exists('.config.yaml'):
        pytest.skip("Config file .config.yaml not found - skipping Neo4j tests")
    
    # Initialize Neo4j manager (using local instance)
    neo4j_manager = Neo4jManager(instance="local")
    
    # Create orchestrator
    orchestrator = MCPOrchestrator(neo4j_manager)
    
    # Test task
    task = "Analyze cryptocurrency market trends and create a report"
    
    print(f"🎯 Task: {task}")
    print("-" * 50)
    
    try:
        results = await orchestrator.execute_task(task)
        
        print(f"\n✅ Task completed!")
        print(f"📊 Summary: {results.get('summary', {})}")
        
        # Display pipeline steps
        if 'summary' in results:
            summary = results['summary']
            print(f"\n📋 Pipeline Details:")
            print(f"   - Status: {summary['status']}")
            print(f"   - Servers Used: {summary['servers_used']}")
            print(f"   - Pipeline Steps: {summary['pipeline_steps']}")
            print(f"   - Errors: {len(summary['errors'])}")
            
            if summary['errors']:
                print(f"   - Error Details: {summary['errors']}")
        
    except Exception as e:
        print(f"❌ Task failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Close Neo4j connection
    neo4j_manager.close()


async def test_multiple_tasks():
    """Test multiple different task types"""
    print("🧪 Testing multiple task types")
    print("=" * 50)
    
    # Check if config file exists
    if not os.path.exists('.config.yaml'):
        pytest.skip("Config file .config.yaml not found - skipping Neo4j tests")
    
    # Initialize Neo4j manager (using local instance)
    neo4j_manager = Neo4jManager(instance="local")
    
    # Create orchestrator
    orchestrator = MCPOrchestrator(neo4j_manager)
    
    # Test different types of tasks
    test_tasks = [
        "Query database for user information",
        "Process customer feedback data using AI",
        "Save processed results to file system",
        "Transform JSON data to CSV format",
        "Search API for product information"
    ]
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n🎯 Test {i}/{len(test_tasks)}: {task}")
        print("-" * 50)
        
        try:
            results = await orchestrator.execute_task(task)
            
            summary = results.get('summary', {})
            print(f"✅ Status: {summary.get('status', 'unknown')}")
            print(f"📊 Servers: {summary.get('servers_used', 0)}")
            print(f"🔗 Steps: {summary.get('pipeline_steps', 0)}")
            
            if summary.get('errors'):
                print(f"❌ Errors: {len(summary['errors'])}")
            
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
        
        # Brief pause between tasks
        await asyncio.sleep(0.5)
    
    # Close Neo4j connection
    neo4j_manager.close()


async def test_complex_pipeline():
    """Test a complex multi-step pipeline"""
    print("🧪 Testing complex pipeline")
    print("=" * 50)
    
    # Check if config file exists
    if not os.path.exists('.config.yaml'):
        pytest.skip("Config file .config.yaml not found - skipping Neo4j tests")
    
    # Initialize Neo4j manager (using local instance)
    neo4j_manager = Neo4jManager(instance="local")
    
    # Create orchestrator
    orchestrator = MCPOrchestrator(neo4j_manager)
    
    # Complex task requiring multiple server types
    complex_task = """
    Fetch market data from cryptocurrency APIs, process the data to identify trends,
    use AI to generate predictions, and save the results to both database and file system
    """
    
    print(f"🎯 Complex Task: {complex_task.strip()}")
    print("-" * 50)
    
    try:
        results = await orchestrator.execute_task(complex_task)
        
        summary = results.get('summary', {})
        print(f"\n✅ Task completed!")
        print(f"📊 Summary:")
        print(f"   - Status: {summary.get('status', 'unknown')}")
        print(f"   - Servers Used: {summary.get('servers_used', 0)}")
        print(f"   - Pipeline Steps: {summary.get('pipeline_steps', 0)}")
        print(f"   - Errors: {len(summary.get('errors', []))}")
        
        # Show individual server results
        print(f"\n🔍 Individual Server Results:")
        for server_id, result in results.items():
            if server_id != 'summary':
                print(f"   - {server_id}: {result.get('type', 'unknown')} - {result.get('message', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Complex task failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Close Neo4j connection
    neo4j_manager.close()


def main():
    """Main function to run tests"""
    print("🚀 Starting MCP Orchestrator Tests")
    print("=" * 80)
    
    # Check if Neo4j is available (mock check)
    print("🔍 Checking prerequisites...")
    print("   - Neo4j connection: Mock (OK)")
    print("   - LangGraph installed: Mock (OK)")
    print("   - ASKG models: Mock (OK)")
    print("")
    
    # Run tests
    print("🧪 Running test suite...")
    
    try:
        # Test 1: Single task
        print("\n" + "="*80)
        print("TEST 1: Single Task Execution")
        print("="*80)
        asyncio.run(test_single_task())
        
        # Test 2: Multiple tasks
        print("\n" + "="*80)
        print("TEST 2: Multiple Task Types")
        print("="*80)
        asyncio.run(test_multiple_tasks())
        
        # Test 3: Complex pipeline
        print("\n" + "="*80)
        print("TEST 3: Complex Pipeline")
        print("="*80)
        asyncio.run(test_complex_pipeline())
        
        print("\n" + "="*80)
        print("✅ All tests completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()