#!/usr/bin/env python3
"""
Test script to verify Neo4j configuration detection
"""

import yaml
import os

def check_remote_config():
    """Test the configuration detection logic"""
    if os.path.exists(".config.yaml"):
        try:
            with open('.config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            if 'neo4j' in config and 'remote' in config['neo4j']:
                print("✅ Remote Neo4j configuration found")
                print(f"   URI: {config['neo4j']['remote']['uri']}")
                print(f"   User: {config['neo4j']['remote']['user']}")
                return 'remote'
            else:
                print("✅ Local Neo4j configuration found")
                if 'local' in config.get('neo4j', {}):
                    print(f"   URI: {config['neo4j']['local']['uri']}")
                return 'local'
        except Exception as e:
            print(f"❌ Error reading .config.yaml: {e}")
            return 'local'
    else:
        print("📄 No .config.yaml found, will use local Neo4j")
        return 'local'

if __name__ == "__main__":
    print("Testing Neo4j configuration detection...")
    instance = check_remote_config()
    print(f"\n🎯 Selected instance: {instance}")
    
    # Test the actual Neo4jManager if possible
    try:
        import sys
        sys.path.append('src')
        from neo4j_integration import Neo4jManager
        
        print(f"\n🔗 Testing connection to {instance} instance...")
        with Neo4jManager(instance=instance) as neo4j:
            with neo4j.driver.session() as session:
                result = session.run('RETURN 1 as test')
                print("✅ Neo4j connection successful!")
                print(f"   Instance: {instance}")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("   This is expected if Neo4j is not running") 