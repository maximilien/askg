#!/usr/bin/env python3
"""
Master Data Management for deduplicated MCP servers.

This module handles saving and loading deduplicated server data, with smart
timestamp checking to avoid unnecessary reprocessing.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from models import MCPServer, KnowledgeGraph, OntologyCategory


class MasterDataManager:
    """Manages master data storage and retrieval with timestamp validation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.master_dir = self.data_dir / "master"
        self.registries_dir = self.data_dir / "registries"
        
        # Ensure master directory exists
        self.master_dir.mkdir(exist_ok=True)
    
    def get_latest_registry_timestamps(self) -> Dict[str, float]:
        """Get the latest modification timestamp for each registry"""
        timestamps = {}
        
        for registry_dir in self.registries_dir.iterdir():
            if not registry_dir.is_dir():
                continue
            
            registry_name = registry_dir.name
            json_files = list(registry_dir.glob("*.json"))
            
            if json_files:
                # Get the most recent file
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                timestamps[registry_name] = latest_file.stat().st_mtime
        
        return timestamps
    
    def get_master_data_timestamp(self) -> Optional[float]:
        """Get the timestamp of the latest master data file"""
        master_files = list(self.master_dir.glob("deduplicated_servers_*.json"))
        
        if not master_files:
            return None
        
        # Get the most recent master data file
        latest_master = max(master_files, key=lambda f: f.stat().st_mtime)
        return latest_master.stat().st_mtime
    
    def is_master_data_current(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if master data is newer than all registry data
        
        Returns:
            (is_current, info_dict) where info_dict contains timing details
        """
        registry_timestamps = self.get_latest_registry_timestamps()
        master_timestamp = self.get_master_data_timestamp()
        
        info = {
            'master_timestamp': master_timestamp,
            'registry_timestamps': registry_timestamps,
            'master_exists': master_timestamp is not None,
            'registries_found': len(registry_timestamps)
        }
        
        if master_timestamp is None:
            info['status'] = 'no_master_data'
            return False, info
        
        if not registry_timestamps:
            info['status'] = 'no_registry_data'
            return False, info
        
        # Check if master data is newer than all registry data
        latest_registry_time = max(registry_timestamps.values())
        is_current = master_timestamp > latest_registry_time
        
        info['latest_registry_time'] = latest_registry_time
        info['time_difference'] = master_timestamp - latest_registry_time
        info['status'] = 'current' if is_current else 'outdated'
        
        return is_current, info
    
    def save_master_data(self, servers: List[MCPServer], categories: List[OntologyCategory]) -> str:
        """
        Save deduplicated servers and categories as master data
        
        Returns:
            Path to the saved master data file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deduplicated_servers_{timestamp}.json"
        filepath = self.master_dir / filename
        
        # Prepare data for serialization
        data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_servers': len(servers),
                'total_categories': len(categories),
                'version': '1.0'
            },
            'servers': [server.dict() for server in servers],
            'categories': [category.dict() for category in categories]
        }
        
        print(f"💾 Saving master data to: {filepath}")
        print(f"   • Servers: {len(servers):,}")
        print(f"   • Categories: {len(categories)}")
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"✅ Master data saved successfully")
        return str(filepath)
    
    def load_master_data(self) -> Optional[Tuple[List[MCPServer], List[OntologyCategory]]]:
        """
        Load the latest master data
        
        Returns:
            (servers, categories) tuple or None if no master data exists
        """
        master_files = list(self.master_dir.glob("deduplicated_servers_*.json"))
        
        if not master_files:
            return None
        
        # Get the most recent master data file
        latest_master = max(master_files, key=lambda f: f.stat().st_mtime)
        
        print(f"📂 Loading master data from: {latest_master.name}")
        
        try:
            with open(latest_master, 'r') as f:
                data = json.load(f)
            
            # Load servers
            servers = []
            for server_data in data.get('servers', []):
                try:
                    server = MCPServer(**server_data)
                    servers.append(server)
                except Exception as e:
                    print(f"   ⚠️  Skipped invalid server: {e}")
            
            # Load categories
            categories = []
            for category_data in data.get('categories', []):
                try:
                    category = OntologyCategory(**category_data)
                    categories.append(category)
                except Exception as e:
                    print(f"   ⚠️  Skipped invalid category: {e}")
            
            metadata = data.get('metadata', {})
            created_at = metadata.get('created_at', 'unknown')
            
            print(f"✅ Master data loaded successfully:")
            print(f"   • Created: {created_at}")
            print(f"   • Servers: {len(servers):,}")
            print(f"   • Categories: {len(categories)}")
            
            return servers, categories
            
        except Exception as e:
            print(f"❌ Error loading master data: {e}")
            return None
    
    def create_knowledge_graph_from_master(self) -> Optional[KnowledgeGraph]:
        """Create a KnowledgeGraph from master data"""
        master_data = self.load_master_data()
        
        if master_data is None:
            return None
        
        servers, categories = master_data
        
        # Create knowledge graph (without relationships for now)
        kg = KnowledgeGraph(
            created_at=datetime.now(),
            last_updated=datetime.now(),
            servers=servers,
            relationships=[],  # Can be extended later
            categories=categories,
            registry_snapshots=[]
        )
        
        return kg
    
    def cleanup_old_master_data(self, keep_count: int = 5):
        """Keep only the most recent N master data files"""
        master_files = list(self.master_dir.glob("deduplicated_servers_*.json"))
        
        if len(master_files) <= keep_count:
            return
        
        # Sort by modification time (newest first)
        master_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Remove old files
        files_to_remove = master_files[keep_count:]
        
        print(f"🧹 Cleaning up old master data files:")
        for file_path in files_to_remove:
            print(f"   • Removing: {file_path.name}")
            file_path.unlink()
        
        print(f"✅ Cleanup complete, kept {keep_count} most recent files")
    
    def print_status(self):
        """Print detailed status of master data vs registry data"""
        is_current, info = self.is_master_data_current()
        
        print("📊 Master Data Status:")
        print(f"   • Master data exists: {info['master_exists']}")
        print(f"   • Registries found: {info['registries_found']}")
        
        if info['master_exists']:
            master_time = datetime.fromtimestamp(info['master_timestamp'])
            print(f"   • Master data created: {master_time}")
        
        if info['registries_found'] > 0 and 'latest_registry_time' in info:
            latest_registry_time = datetime.fromtimestamp(info['latest_registry_time'])
            print(f"   • Latest registry data: {latest_registry_time}")
            
            if info['master_exists']:
                time_diff = info['time_difference']
                if time_diff > 0:
                    print(f"   • Master is {time_diff/3600:.1f} hours newer ✅")
                else:
                    print(f"   • Master is {abs(time_diff)/3600:.1f} hours older ⚠️")
        
        print(f"   • Status: {info['status']}")
        
        if is_current:
            print("✅ Master data is current and can be used directly")
        else:
            print("⚠️  Master data needs to be rebuilt")


def main():
    """Test the master data manager"""
    manager = MasterDataManager()
    manager.print_status()


if __name__ == "__main__":
    main()