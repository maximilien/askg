#!/usr/bin/env python3
"""
Test Glama scraper directly to debug the issue
"""

import asyncio
from scrapers import GlamaScraper, ConfigManager, StorageManager

async def test_glama_scraper():
    config = ConfigManager()
    storage = StorageManager(config)
    
    async with GlamaScraper(config, storage) as scraper:
        print("Testing Glama scraper directly...")
        snapshot = await scraper.scrape()
        print(f"Snapshot result: {snapshot.servers_count} servers")
        
        for i, server in enumerate(snapshot.servers[:5]):
            print(f"  {i+1}: {server.name} by {server.author}")

if __name__ == "__main__":
    asyncio.run(test_glama_scraper())