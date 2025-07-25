"""Tests for text2cypher functionality"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text2cypher import Text2CypherConverter, create_text2cypher_converter


class TestText2CypherConverter:
    """Test the Text2CypherConverter class"""
    
    def test_init_without_api_key(self):
        """Test initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                Text2CypherConverter()
    
    def test_init_with_api_key(self):
        """Test initialization with API key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OpenAI') as mock_openai:
                converter = Text2CypherConverter()
                assert converter.api_key == "test_key"
                mock_openai.assert_called_once_with(api_key="test_key")
    
    def test_convert_to_cypher_success(self):
        """Test successful conversion to Cypher"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OpenAI') as mock_openai:
                # Mock the OpenAI client response
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = "MATCH (s:Server) WHERE 'database' IN s.categories RETURN s"
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                converter = Text2CypherConverter()
                result = converter.convert_to_cypher("Find database servers")
                
                assert result["cypher"] == "MATCH (s:Server) WHERE 'database' IN s.categories RETURN s"
                assert result["original_query"] == "Find database servers"
                assert result["model"] == "gpt-4o-mini"
                assert "parameters" in result
    
    def test_convert_to_cypher_fallback(self):
        """Test fallback to keyword-based query when LLM fails"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OpenAI') as mock_openai:
                # Mock the OpenAI client to raise an exception
                mock_client = MagicMock()
                mock_client.chat.completions.create.side_effect = Exception("API Error")
                mock_openai.return_value = mock_client
                
                converter = Text2CypherConverter()
                result = converter.convert_to_cypher("Find database servers")
                
                assert result["model"] == "fallback_keyword"
                assert "MATCH (s:Server)" in result["cypher"]
                assert "database" in result["parameters"]["categories"]
    
    def test_extract_search_terms(self):
        """Test search term extraction"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OpenAI'):
                converter = Text2CypherConverter()
                terms = converter._extract_search_terms("Find database servers that can read files")
                
                assert "database" in terms["categories"]
                assert "file_system" in terms["categories"]
                assert "read" in terms["operations"]
                assert "Find" in terms["keywords"]
    
    def test_fallback_query(self):
        """Test fallback query generation"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OpenAI'):
                converter = Text2CypherConverter()
                result = converter._fallback_query("Find database servers", 10, 0.5)
                
                assert "MATCH (s:Server)" in result["cypher"]
                assert result["parameters"]["limit"] == 10
                assert result["parameters"]["min_confidence"] == 0.5
                assert result["model"] == "fallback_keyword"
    
    def test_clean_cypher_query(self):
        """Test cleaning of Cypher queries with markdown formatting"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OpenAI'):
                converter = Text2CypherConverter()
                
                # Test with cypher code block
                cypher_with_cypher = "```cypher\nMATCH (s:Server) RETURN s\n```"
                cleaned = converter._clean_cypher_query(cypher_with_cypher)
                assert cleaned == "MATCH (s:Server) RETURN s"
                
                # Test with regular code block
                cypher_with_code = "```\nMATCH (s:Server) RETURN s\n```"
                cleaned = converter._clean_cypher_query(cypher_with_code)
                assert cleaned == "MATCH (s:Server) RETURN s"
                
                # Test with no code block
                cypher_clean = "MATCH (s:Server) RETURN s"
                cleaned = converter._clean_cypher_query(cypher_clean)
                assert cleaned == "MATCH (s:Server) RETURN s"
                
                # Test with extra whitespace
                cypher_whitespace = "```cypher\n  MATCH (s:Server)  \n  RETURN s  \n```"
                cleaned = converter._clean_cypher_query(cypher_whitespace)
                assert cleaned == "MATCH (s:Server)  \n  RETURN s"


class TestCreateText2CypherConverter:
    """Test the create_text2cypher_converter function"""
    
    def test_create_with_api_key(self):
        """Test creating converter with API key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OpenAI'):
                converter = create_text2cypher_converter()
                assert converter is not None
                assert isinstance(converter, Text2CypherConverter)
    
    def test_create_without_api_key(self):
        """Test creating converter without API key"""
        with patch.dict(os.environ, {}, clear=True):
            converter = create_text2cypher_converter()
            assert converter is None
    
    def test_create_with_openai_import_error(self):
        """Test creating converter when OpenAI is not available"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('text2cypher.OPENAI_AVAILABLE', False):
                converter = create_text2cypher_converter()
                assert converter is None


if __name__ == "__main__":
    pytest.main([__file__]) 