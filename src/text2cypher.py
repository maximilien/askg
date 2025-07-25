"""Text to Cypher Query Converter

This module provides functionality to convert natural language queries into
Cypher queries for the Neo4j knowledge graph using OpenAI's GPT-4o-mini model.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Install with: pip install openai")

logger = logging.getLogger(__name__)


class Text2CypherConverter:
    """Convert natural language queries to Cypher queries using OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the converter with OpenAI API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Neo4j schema information for the MCP knowledge graph
        self.schema_info = """
        # Neo4j Knowledge Graph Schema for MCP Servers
        
        ## Node Labels
        - Server: Represents MCP servers with properties like name, description, author, etc.
        
        ## Server Properties
        - id: String (unique identifier)
        - name: String (server name)
        - description: String (server description)
        - version: String (version number)
        - author: String (author/creator)
        - license: String (license type)
        - homepage: String (homepage URL)
        - repository: String (repository URL)
        - implementation_language: String (programming language)
        - installation_command: String (installation command)
        - categories: List[String] (server categories like "database", "file_system", etc.)
        - operations: List[String] (operations like "read", "write", "execute", etc.)
        - data_types: List[String] (data types the server works with)
        - registry_source: String (source registry like "github", "glama", etc.)
        - source_url: String (source URL)
        - last_updated: DateTime (last update timestamp)
        - popularity_score: Float (popularity metric)
        - download_count: Integer (download count)
        
        ## Categories (ServerCategory enum values)
        - DATABASE: Database-related servers
        - FILE_SYSTEM: File system operations
        - API_INTEGRATION: API and web service integration
        - DEVELOPMENT_TOOLS: Development and programming tools
        - DATA_PROCESSING: Data processing and analysis
        - CLOUD_SERVICES: Cloud platform services
        - COMMUNICATION: Communication and messaging
        - AUTHENTICATION: Authentication and security
        - MONITORING: Monitoring and logging
        - SEARCH: Search and indexing
        - AI_ML: AI and machine learning
        - OTHER: Other categories
        
        ## Operations (OperationType enum values)
        - READ: Read operations
        - WRITE: Write operations
        - EXECUTE: Execute operations
        - QUERY: Query operations
        - TRANSFORM: Transform operations
        - MONITOR: Monitor operations
        
        ## Example Queries
        - "Find database servers": MATCH (s:Server) WHERE 'database' IN s.categories RETURN s
        - "Find servers that can read files": MATCH (s:Server) WHERE 'read' IN s.operations AND 'file_system' IN s.categories RETURN s
        - "Find popular AI servers": MATCH (s:Server) WHERE 'ai_ml' IN s.categories AND s.popularity_score > 1000 RETURN s ORDER BY s.popularity_score DESC
        """
    
    def convert_to_cypher(self, query: str, limit: int = 20, min_confidence: float = 0.5) -> Dict[str, Any]:
        """Convert natural language query to Cypher query"""
        try:
            prompt = self._build_prompt(query, limit, min_confidence)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.schema_info},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=1000
            )
            
            cypher_query = response.choices[0].message.content.strip()
            
            # Clean up the Cypher query - remove markdown code blocks if present
            cypher_query = self._clean_cypher_query(cypher_query)
            
            # Extract parameters if the response includes them
            params = self._extract_parameters(cypher_query, query, limit, min_confidence)
            
            logger.info(f"Converted query '{query}' to Cypher: {cypher_query}")
            
            return {
                "cypher": cypher_query,
                "parameters": params,
                "original_query": query,
                "model": "gpt-4o-mini"
            }
            
        except Exception as e:
            logger.error(f"Error converting query to Cypher: {e}")
            # Fallback to simple keyword-based query
            return self._fallback_query(query, limit, min_confidence)
    
    def _clean_cypher_query(self, cypher_query: str) -> str:
        """Clean up the Cypher query by removing markdown code blocks and extra formatting"""
        # Remove markdown code blocks
        if cypher_query.startswith("```cypher"):
            cypher_query = cypher_query[9:]  # Remove "```cypher"
        elif cypher_query.startswith("```"):
            cypher_query = cypher_query[3:]  # Remove "```"
        
        if cypher_query.endswith("```"):
            cypher_query = cypher_query[:-3]  # Remove trailing "```"
        
        # Clean up any extra whitespace
        cypher_query = cypher_query.strip()
        
        # Remove any leading/trailing newlines
        cypher_query = cypher_query.strip('\n')
        
        return cypher_query
    
    def _build_prompt(self, query: str, limit: int, min_confidence: float) -> str:
        """Build the prompt for the LLM"""
        return f"""
        Convert the following natural language query into a Cypher query for Neo4j.
        
        Query: "{query}"
        Limit: {limit} results
        Minimum confidence: {min_confidence}
        
        Requirements:
        1. Use the schema information provided above
        2. Return ONLY the raw Cypher query - NO markdown formatting, NO code blocks, NO explanations
        3. Include proper scoring and filtering based on relevance
        4. Use these EXACT parameter names: $query, $limit, $min_confidence
        5. Order results by relevance score (highest first)
        6. For text matching, use the extracted keywords from the query, not the full query text
        7. Consider categories and operations for better matching
        8. ALWAYS include tools data by using: OPTIONAL MATCH (s)-[:HAS_TOOL]->(t:Tool) WITH s, COLLECT(t) as tools
        9. ALWAYS return tools in the result: RETURN s, tools, total_score
        
        IMPORTANT: 
        - Return the Cypher query as plain text without any markdown formatting or code blocks
        - Use parameter names: $query (for search text), $limit (for result limit), $min_confidence (for minimum score)
        - For text matching, focus on the key search terms, not the full sentence
        - ALWAYS include text matching on name and description fields using CONTAINS
        - Example: For "Find popular crypto servers", use: WHERE (s.name CONTAINS $query OR s.description CONTAINS $query)
        - Categories and operations are additional filters, not replacements for text matching
        - ALWAYS include tools retrieval: OPTIONAL MATCH (s)-[:HAS_TOOL]->(t:Tool) WITH s, COLLECT(t) as tools
        - ALWAYS return tools: RETURN s, tools, total_score
        
        The query should search for MCP servers that match the user's intent and include their tools.
        """
    
    def _extract_parameters(self, cypher_query: str, original_query: str, limit: int, min_confidence: float) -> Dict[str, Any]:
        """Extract parameters from the Cypher query"""
        # Extract search terms for better matching
        search_terms = self._extract_search_terms(original_query)
        
        # Create a search query from the most relevant keywords
        search_keywords = []
        for keyword in search_terms["keywords"]:
            # Filter out common words and focus on meaningful terms
            if keyword.lower() not in ["find", "show", "me", "the", "best", "popular", "servers", "tools", "for", "that", "can", "and", "or", "with", "are", "what", "how", "when", "where", "why"]:
                search_keywords.append(keyword)
        
        # Use the most relevant keywords for text matching
        search_text = " ".join(search_keywords) if search_keywords else original_query
        
        params = {
            "query": search_text,  # Use extracted keywords instead of full query
            "limit": limit,
            "min_confidence": min_confidence
        }
        
        params.update(search_terms)
        
        return params
    
    def _extract_search_terms(self, query: str) -> Dict[str, Any]:
        """Extract search terms from the query for parameter building"""
        query_lower = query.lower()
        
        # Extract categories
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
            "ai_ml": ["ai", "ml", "machine learning", "model", "prediction"],
            "blockchain": ["crypto", "cryptocurrency", "blockchain", "bitcoin", "ethereum", "web3"],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                categories.append(category)
        
        # Extract operations
        operations = []
        operation_keywords = {
            "read": ["read", "get", "fetch", "retrieve"],
            "write": ["write", "save", "store", "create", "update"],
            "execute": ["execute", "run", "call", "invoke"],
            "query": ["query", "search", "find", "filter"],
            "transform": ["transform", "convert", "process", "analyze"],
            "monitor": ["monitor", "watch", "observe", "track"],
        }
        
        for operation, keywords in operation_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                operations.append(operation)
        
        return {
            "categories": categories,
            "operations": operations,
            "keywords": query.split()
        }
    
    def _fallback_query(self, query: str, limit: int, min_confidence: float) -> Dict[str, Any]:
        """Fallback to simple keyword-based query if LLM conversion fails"""
        search_terms = self._extract_search_terms(query)
        
        # Create a search query from the most relevant keywords
        search_keywords = []
        for keyword in search_terms["keywords"]:
            # Filter out common words and focus on meaningful terms
            if keyword.lower() not in ["find", "show", "me", "the", "best", "popular", "servers", "tools", "for", "that", "can", "and", "or", "with", "are", "what", "how", "when", "where", "why"]:
                search_keywords.append(keyword)
        
        # Use the most relevant keywords for text matching
        search_text = " ".join(search_keywords) if search_keywords else query
        
        # Create a more flexible query that prioritizes text matching
        cypher = """
        MATCH (s:Server)
        OPTIONAL MATCH (s)-[:HAS_TOOL]->(t:Tool)
        WITH s, COLLECT(t) as tools,
             // Text relevance score - primary matching on name and description
             CASE 
                 WHEN toLower(s.name) CONTAINS toLower($query) THEN 10.0
                 WHEN toLower(s.description) CONTAINS toLower($query) THEN 8.0
                 ELSE 0.0
             END as text_score,
             
             // Popularity bonus (very small weight, only for tie-breaking)
             COALESCE(s.popularity_score, 0) * 0.001 as popularity_bonus
             
        WITH s, tools, (text_score + popularity_bonus) as total_score
        
        WHERE text_score > 0 AND total_score >= $min_confidence
        
        RETURN s, tools, total_score
        ORDER BY total_score DESC
        LIMIT $limit
        """
        
        params = {
            "query": search_text,  # Use extracted keywords instead of full query
            "categories": search_terms["categories"],
            "operations": search_terms["operations"],
            "min_confidence": min_confidence,
            "limit": limit,
        }
        
        return {
            "cypher": cypher,
            "parameters": params,
            "original_query": query,
            "model": "fallback_keyword"
        }


def create_text2cypher_converter() -> Optional[Text2CypherConverter]:
    """Create a Text2CypherConverter instance if OpenAI is available"""
    try:
        return Text2CypherConverter()
    except (ValueError, ImportError) as e:
        logger.warning(f"Text2CypherConverter not available: {e}")
        return None 