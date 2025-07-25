#!/usr/bin/env python3
"""
Test CI configuration file creation and loading
"""

import os
import yaml
import pytest
from pathlib import Path

def test_config_file_exists():
    """Test that the config file exists and is valid YAML"""
    config_path = Path('.config.yaml')
    
    if not config_path.exists():
        pytest.skip("Config file .config.yaml not found - this is expected in some CI environments")
    
    print(f"✅ Config file exists at {config_path.absolute()}")
    
    # Test that it's valid YAML
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        assert 'neo4j' in config, "Config must have 'neo4j' section"
        assert 'local' in config['neo4j'], "Config must have 'neo4j.local' section"
        
        local_config = config['neo4j']['local']
        assert 'uri' in local_config, "Local config must have 'uri'"
        assert 'user' in local_config, "Local config must have 'user'"
        assert 'password' in local_config, "Local config must have 'password'"
        
        print("✅ Config file is valid YAML with required sections")
        print(f"   Local URI: {local_config['uri']}")
        print(f"   Local User: {local_config['user']}")
        
        # Check optional sections
        if 'remote' in config['neo4j']:
            print("✅ Remote config section found")
        else:
            print("ℹ️  No remote config section (optional)")
        
        if 'github' in config:
            print("✅ GitHub config section found")
        else:
            print("ℹ️  No GitHub config section (optional)")
        
        if 'storage' in config:
            print("✅ Storage config section found")
        else:
            print("ℹ️  No storage config section (optional)")
        
        return True
        
    except yaml.YAMLError as e:
        pytest.fail(f"Config file is not valid YAML: {e}")
    except Exception as e:
        pytest.fail(f"Error reading config file: {e}")

def test_config_file_permissions():
    """Test that the config file has appropriate permissions"""
    config_path = Path('.config.yaml')
    
    if not config_path.exists():
        pytest.skip("Config file .config.yaml not found")
    
    # Check if file is readable
    if os.access(config_path, os.R_OK):
        print("✅ Config file is readable")
    else:
        pytest.fail("Config file is not readable")
    
    # Check file size
    file_size = config_path.stat().st_size
    print(f"✅ Config file size: {file_size} bytes")
    
    if file_size == 0:
        pytest.fail("Config file is empty")

def test_environment_variables():
    """Test that relevant environment variables are set"""
    print("Testing environment variables...")
    
    # Check for common CI environment variables
    ci_vars = [
        'CI',
        'GITHUB_ACTIONS',
        'GITHUB_WORKFLOW',
        'GITHUB_RUN_ID'
    ]
    
    for var in ci_vars:
        if os.getenv(var):
            print(f"✅ {var} is set: {os.getenv(var)}")
        else:
            print(f"ℹ️  {var} is not set (optional)")
    
    # Check Python environment
    print(f"✅ Python version: {os.getenv('PYTHON_VERSION', 'unknown')}")
    print(f"✅ Working directory: {os.getcwd()}")

if __name__ == "__main__":
    # Run tests
    test_config_file_exists()
    test_config_file_permissions()
    test_environment_variables()
    print("🎉 All CI config tests passed!") 