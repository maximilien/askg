#!/usr/bin/env python3
"""
MCP Server for ASKG (Agent-Server Knowledge Graph)

This MCP server provides semantic search capabilities for MCP servers
stored in the Neo4j knowledge graph database.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

import yaml
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

# Import from the parent askg package
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from models import MCPServer, ServerCategory, OperationType, RegistrySource


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerSearchRequest(BaseModel):
    """Request model for server search"""
    prompt: str = Field(..., description="Search prompt describing the desired MCP servers")
    limit: int = Field(default=10, description="Maximum number of servers to return")
    min_confidence: float = Field(default=0.5, description="Minimum confidence score for results")


class ServerSearchResult(BaseModel):
    """Result model for server search"""
    servers: List[MCPServer] = Field(..., description="List of matching MCP servers")
    total_found: int = Field(..., description="Total number of servers found")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="Search metadata")


class ASKGMCPServer:
    """MCP Server for ASKG semantic search"""
    
    def __init__(self, config_path: str = ".config.yaml", instance: str = "local"):
        """Initialize the MCP server with Neo4j connection"""
        self.config_path = config_path
        self.instance = instance
        self.driver = None
        self._load_config()
        self._connect_to_neo4j()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_path} not found")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
    
    def _connect_to_neo4j(self):
        """Establish connection to Neo4j database"""
        try:
            neo4j_config = self.config['neo4j'][self.instance]
            self.driver = GraphDatabase.driver(
                neo4j_config['uri'],
                auth=(neo4j_config['user'], neo4j_config['password'])
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j instance: {self.instance}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def search_servers(self, request: ServerSearchRequest) -> ServerSearchResult:
        """
        Search for MCP servers based on a semantic prompt
        
        This function performs a multi-faceted search:
        1. Text-based search on server names and descriptions
        2. Category-based search using semantic matching
        3. Operation-based search for functional capabilities
        4. Combined scoring and ranking
        """
        try:
            # Parse the prompt to extract search terms and intent
            search_terms = self._extract_search_terms(request.prompt)
            
            # Perform semantic search
            servers = await self._semantic_search(search_terms, request.limit, request.min_confidence)
            
            # Convert Neo4j records to MCPServer objects
            mcp_servers = []
            for server_record in servers:
                mcp_server = self._convert_to_mcp_server(server_record)
                if mcp_server:
                    mcp_servers.append(mcp_server)
            
            # Create search metadata
            search_metadata = {
                "search_terms": search_terms,
                "prompt": request.prompt,
                "instance": self.instance,
                "search_strategy": "semantic_multi_faceted"
            }
            
            return ServerSearchResult(
                servers=mcp_servers,
                total_found=len(mcp_servers),
                search_metadata=search_metadata
            )
            
        except Exception as e:
            logger.error(f"Error during server search: {e}")
            raise
    
    def _extract_search_terms(self, prompt: str) -> Dict[str, Any]:
        """
        Extract search terms and intent from the prompt
        
        This is a simple keyword extraction. In a production system,
        you might use NLP techniques or LLM-based intent extraction.
        """
        prompt_lower = prompt.lower()
        
        # Extract potential categories
        categories = []
        category_keywords = {
            "database": ["database", "db", "sql", "nosql", "query", "store"],
            "file_system": ["file", "filesystem", "fs", "storage", "read", "write"],
            "api_integration": ["api", "rest", "graphql", "http", "webhook"],
            "development_tools": ["dev", "development", "tool", "utility"],
            "data_processing": ["process", "transform", "analyze", "etl"],
            "cloud_services": ["cloud", "aws", "azure", "gcp", "s3"],
            "communication": ["chat", "message", "email", "notification"],
            "authentication": ["auth", "login", "oauth", "jwt", "security"],
            "monitoring": ["monitor", "log", "metric", "alert"],
            "search": ["search", "index", "elasticsearch", "lucene"],
            "ai_ml": ["ai", "ml", "machine learning", "model", "prediction"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                categories.append(category)
        
        # Extract potential operations
        operations = []
        operation_keywords = {
            "read": ["read", "get", "fetch", "retrieve"],
            "write": ["write", "save", "store", "create", "update"],
            "execute": ["execute", "run", "call", "invoke"],
            "query": ["query", "search", "find", "filter"],
            "transform": ["transform", "convert", "process", "analyze"],
            "monitor": ["monitor", "watch", "observe", "track"]
        }
        
        for operation, keywords in operation_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                operations.append(operation)
        
        # Extract general search terms
        search_terms = prompt.split()
        
        return {
            "categories": categories,
            "operations": operations,
            "keywords": search_terms,
            "original_prompt": prompt
        }
    
    async def _semantic_search(self, search_terms: Dict[str, Any], limit: int, min_confidence: float) -> List[Dict]:
        """
        Perform semantic search using multiple strategies
        """
        # Build the Cypher query based on search terms
        cypher_query, params = self._build_search_query(search_terms, limit, min_confidence)
        
        with self.driver.session() as session:
            result = session.run(cypher_query, params)
            return [dict(record) for record in result]
    
    def _build_search_query(self, search_terms: Dict[str, Any], limit: int, min_confidence: float) -> tuple:
        """
        Build a Cypher query for semantic search
        """
        # Base query
        cypher = """
        MATCH (s:Server)
        WITH s,
             // Text relevance score
             CASE 
                 WHEN toLower(s.name) CONTAINS toLower($prompt) THEN 3.0
                 WHEN toLower(s.description) CONTAINS toLower($prompt) THEN 2.0
                 ELSE 0.0
             END as text_score,
             
             // Category relevance score
             CASE 
                 WHEN $categories IS NOT NULL AND ANY(cat IN $categories WHERE cat IN s.categories) 
                 THEN SIZE([cat IN $categories WHERE cat IN s.categories]) * 2.0
                 ELSE 0.0
             END as category_score,
             
             // Operation relevance score
             CASE 
                 WHEN $operations IS NOT NULL AND ANY(op IN $operations WHERE op IN s.operations)
                 THEN SIZE([op IN $operations WHERE op IN s.operations]) * 1.5
                 ELSE 0.0
             END as operation_score,
             
             // Popularity bonus
             COALESCE(s.popularity_score, 0) * 0.1 as popularity_bonus
             
        WITH s, (text_score + category_score + operation_score + popularity_bonus) as total_score
        
        WHERE total_score >= $min_confidence
        
        RETURN s, total_score
        ORDER BY total_score DESC
        LIMIT $limit
        """
        
        params = {
            'prompt': search_terms['original_prompt'],
            'categories': search_terms['categories'],
            'operations': search_terms['operations'],
            'min_confidence': min_confidence,
            'limit': limit
        }
        
        return cypher, params
    
    def _convert_to_mcp_server(self, server_record: Dict) -> Optional[MCPServer]:
        """
        Convert Neo4j record to MCPServer object
        """
        try:
            server_data = server_record['s']
            score = server_record.get('total_score', 0.0)
            
            # Convert string categories back to ServerCategory enums
            categories = []
            if server_data.get('categories'):
                for cat_str in server_data['categories']:
                    try:
                        categories.append(ServerCategory(cat_str))
                    except ValueError:
                        categories.append(ServerCategory.OTHER)
            
            # Convert string operations back to OperationType enums
            operations = []
            if server_data.get('operations'):
                for op_str in server_data['operations']:
                    try:
                        operations.append(OperationType(op_str))
                    except ValueError:
                        operations.append(OperationType.EXECUTE)
            
            # Convert registry source
            registry_source = RegistrySource.UNKNOWN
            if server_data.get('registry_source'):
                try:
                    registry_source = RegistrySource(server_data['registry_source'])
                except ValueError:
                    pass
            
            # Create MCPServer object
            return MCPServer(
                id=server_data.get('id', 'unknown'),
                name=server_data.get('name', 'Unknown Server'),
                description=server_data.get('description'),
                version=server_data.get('version'),
                author=server_data.get('author'),
                license=server_data.get('license'),
                homepage=server_data.get('homepage'),
                repository=server_data.get('repository'),
                implementation_language=server_data.get('implementation_language'),
                installation_command=server_data.get('installation_command'),
                categories=categories,
                operations=operations,
                data_types=server_data.get('data_types', []),
                registry_source=registry_source,
                source_url=server_data.get('source_url'),
                last_updated=server_data.get('last_updated'),
                popularity_score=server_data.get('popularity_score'),
                download_count=server_data.get('download_count'),
                raw_metadata={'search_score': score}
            )
            
        except Exception as e:
            logger.error(f"Error converting server record: {e}")
            return None


# MCP Server Protocol Implementation
class MCPServerProtocol:
    """MCP Server Protocol implementation"""
    
    def __init__(self, askg_server: ASKGMCPServer):
        self.askg_server = askg_server
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get('method')
        params = request.get('params', {})
        
        if method == 'search_servers':
            search_request = ServerSearchRequest(**params)
            result = await self.askg_server.search_servers(search_request)
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': result.dict()
            }
        else:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32601,
                    'message': f'Method {method} not found'
                }
            }


async def main():
    """Main entry point for the MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ASKG MCP Server')
    parser.add_argument('--config', default='.config.yaml', help='Configuration file path')
    parser.add_argument('--instance', default='local', help='Neo4j instance to use')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    
    args = parser.parse_args()
    
    # Initialize the ASKG MCP server
    with ASKGMCPServer(args.config, args.instance) as server:
        protocol = MCPServerProtocol(server)
        
        # Simple HTTP server for demonstration
        # In production, you'd use a proper MCP server implementation
        import aiohttp
        from aiohttp import web
        
        async def handle_request(request):
            try:
                data = await request.json()
                response = await protocol.handle_request(data)
                return web.json_response(response)
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                return web.json_response({
                    'jsonrpc': '2.0',
                    'id': data.get('id') if 'data' in locals() else None,
                    'error': {
                        'code': -32603,
                        'message': str(e)
                    }
                })
        
        app = web.Application()
        app.router.add_post('/', handle_request)
        
        logger.info(f"Starting ASKG MCP server on port {args.port}")
        web.run_app(app, port=args.port)


if __name__ == '__main__':
    asyncio.run(main()) 