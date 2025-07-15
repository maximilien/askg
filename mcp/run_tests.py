#!/usr/bin/env python3
"""
Test Runner for ASKG MCP Server

This script runs tests to verify the MCP server functionality.
"""

import sys
import subprocess
from pathlib import Path

def run_pytest():
    """Run pytest on the test files"""
    print("Running MCP Server tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_mcp_server.py", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ Tests failed with return code: {result.returncode}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test basic imports
        from mcp_server import ASKGMCPServer, ServerSearchRequest, ServerSearchResult
        print("✅ Basic imports successful")
        
        # Test client example imports
        from client_example import search_example, interactive_search, test_connection
        print("✅ Client example imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("Testing configuration loading...")
    
    try:
        import yaml
        config_path = Path(__file__).parent.parent / ".config.yaml"
        
        if not config_path.exists():
            print("⚠️  Configuration file not found, creating test config...")
            test_config = {
                'neo4j': {
                    'local': {
                        'uri': 'bolt://localhost:7687',
                        'user': 'neo4j',
                        'password': 'password'
                    }
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            print("✅ Test configuration created")
        else:
            print("✅ Configuration file exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("=" * 60)
    print("ASKG MCP Server Test Runner")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config_loading),
        ("Pytest Tests", run_pytest),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The MCP server is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 