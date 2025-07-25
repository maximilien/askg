#!/usr/bin/env python3
"""
Test the Neo4j configuration loading for both local and remote instances
"""

import os
import yaml
import pytest
from neo4j_integration import Neo4jManager

def test_config():
    """Test loading both local and remote configurations"""
    
    # Test config loading
    config_path = '.config.yaml'
    if not os.path.exists(config_path):
        pytest.skip(f"Config file {config_path} not found - skipping config test")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("📋 Testing Neo4j configuration loading...")
    
    # Test local config
    print("\n🏠 Local Neo4j Configuration:")
    local_config = config['neo4j']['local']
    print(f"  URI: {local_config['uri']}")
    print(f"  User: {local_config['user']}")
    print(f"  Password: {'*' * len(local_config['password'])}")
    
    # Test remote config (if available)
    print("\n🌐 Remote Neo4j Configuration:")
    if 'remote' in config['neo4j']:
        remote_config = config['neo4j']['remote']
        print(f"  URI: {remote_config['uri']}")
        print(f"  User: {remote_config['user']}")
        print(f"  Password: {'*' * len(remote_config['password'])}")
    else:
        print("  ⚠️  No remote configuration found")
    
    # Test Neo4jManager initialization (without connecting)
    print("\n🔧 Testing Neo4jManager initialization...")
    
    try:
        # This will initialize the manager but not test the connection
        local_manager = Neo4jManager(instance="local")
        print("  ✅ Local Neo4jManager initialized successfully")
        local_manager.close()
    except Exception as e:
        print(f"  ❌ Local Neo4jManager failed: {e}")
    
    # Only test remote if configuration exists
    if 'remote' in config['neo4j']:
        try:
            remote_manager = Neo4jManager(instance="remote") 
            print("  ✅ Remote Neo4jManager initialized successfully")
            remote_manager.close()
        except Exception as e:
            print(f"  ❌ Remote Neo4jManager failed: {e}")
    else:
        print("  ⏭️  Skipping remote Neo4jManager test (no config)")
    
    print("\n🎉 Configuration test completed!")
    print("\n💡 To use remote Neo4j:")
    print("   1. Update config.yaml with your remote Neo4j details")
    print("   2. Run any script with --remote flag")
    print("   3. Example: python run_full_deduplication.py --remote")

if __name__ == "__main__":
    test_config()