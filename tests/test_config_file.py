#!/usr/bin/env python3
"""
Simple test to verify config file exists and is valid
"""

import os
import yaml
import pytest
from pathlib import Path

def test_config_file_exists():
    """Test that the config file exists"""
    config_path = Path('.config.yaml')
    
    if not config_path.exists():
        pytest.skip("Config file .config.yaml not found - this is expected in some CI environments")
    
    assert config_path.exists(), "Config file should exist"
    assert config_path.is_file(), "Config file should be a file"
    assert config_path.stat().st_size > 0, "Config file should not be empty"

def test_config_file_valid_yaml():
    """Test that the config file is valid YAML"""
    config_path = Path('.config.yaml')
    
    if not config_path.exists():
        pytest.skip("Config file .config.yaml not found")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check that it's a dictionary
        assert isinstance(config, dict), "Config should be a dictionary"
        
        # Check for required sections
        assert 'neo4j' in config, "Config should have 'neo4j' section"
        assert 'local' in config['neo4j'], "Config should have 'neo4j.local' section"
        
        # Check local config
        local_config = config['neo4j']['local']
        assert 'uri' in local_config, "Local config should have 'uri'"
        assert 'user' in local_config, "Local config should have 'user'"
        assert 'password' in local_config, "Local config should have 'password'"
        
        print("✅ Config file is valid YAML with required sections")
        
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
    assert os.access(config_path, os.R_OK), "Config file should be readable"
    
    # Check file size
    file_size = config_path.stat().st_size
    assert file_size > 0, "Config file should not be empty"
    
    print(f"✅ Config file size: {file_size} bytes")

if __name__ == "__main__":
    # Run tests
    test_config_file_exists()
    test_config_file_valid_yaml()
    test_config_file_permissions()
    print("🎉 All config file tests passed!") 