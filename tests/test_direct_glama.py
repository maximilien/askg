#!/usr/bin/env python3
"""
Test Glama scraper with mocking to avoid network calls
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from models import MCPServer, RegistrySource
from datetime import datetime

def create_mock_glama_response():
    """Create mock Glama API response"""
    return {
        "servers": [
            {
                "id": "glama_test_1",
                "name": "Test Server 1",
                "description": "Test server for unit testing",
                "author": "Test Author",
                "version": "1.0.0",
                "repository": "https://github.com/test/test-server-1",
                "implementation_language": "Python",
                "categories": ["database"],
                "operations": ["read"],
                "registry_source": "glama",
                "popularity_score": 100,
                "last_updated": datetime.now().isoformat(),
                "installation_command": "pip install test-server-1",
                "download_count": 1000
            },
            {
                "id": "glama_test_2", 
                "name": "Test Server 2",
                "description": "Another test server",
                "author": "Test Author 2",
                "version": "1.0.0",
                "repository": "https://github.com/test/test-server-2",
                "implementation_language": "TypeScript",
                "categories": ["api"],
                "operations": ["write"],
                "registry_source": "glama",
                "popularity_score": 50,
                "last_updated": datetime.now().isoformat(),
                "installation_command": "npm install test-server-2",
                "download_count": 500
            }
        ]
    }

@pytest.mark.asyncio
@pytest.mark.slow
async def test_glama_scraper():
    """Test Glama scraper with mocked responses"""
    
    # Mock the HTTP client to avoid real network calls
    with patch('scrapers.aiohttp.ClientSession') as mock_session:
        # Create mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = create_mock_glama_response()
        mock_response.status = 200
        
        # Configure mock session
        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        # Import here to ensure mocking is in place
        from scrapers import GlamaScraper, ConfigManager, StorageManager
        
        config = ConfigManager()
        storage = StorageManager(config)
        
        async with GlamaScraper(config, storage) as scraper:
            print("Testing Glama scraper with mocked responses...")
            snapshot = await scraper.scrape()
            print(f"Snapshot result: {snapshot.servers_count} servers")
            
            assert snapshot.servers_count == 2, f"Expected 2 servers, got {snapshot.servers_count}"
            
            for i, server in enumerate(snapshot.servers[:2]):
                print(f"  {i+1}: {server.name} by {server.author}")
                assert server.name == f"Test Server {i+1}"
                assert server.author in ["Test Author", "Test Author 2"]

if __name__ == "__main__":
    asyncio.run(test_glama_scraper())