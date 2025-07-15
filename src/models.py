from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, HttpUrl, validator


class ServerCategory(str, Enum):
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    API_INTEGRATION = "api_integration"
    DEVELOPMENT_TOOLS = "development_tools"
    DATA_PROCESSING = "data_processing"
    CLOUD_SERVICES = "cloud_services"
    COMMUNICATION = "communication"
    AUTHENTICATION = "authentication"
    MONITORING = "monitoring"
    SEARCH = "search"
    AI_ML = "ai_ml"
    OTHER = "other"


class OperationType(str, Enum):
    READ = "read"
    WRITE = "write"
    QUERY = "query"
    EXECUTE = "execute"
    TRANSFORM = "transform"
    ANALYZE = "analyze"
    SYNC = "sync"
    STREAM = "stream"


class RegistrySource(str, Enum):
    GITHUB = "github"
    MCP_SO = "mcp.so"
    GLAMA = "glama"
    MCP_MARKET = "mcpmarket.com"


class MCPTool(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class MCPResource(BaseModel):
    uri: str
    name: Optional[str] = None
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPPrompt(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPServer(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[HttpUrl] = None
    repository: Optional[HttpUrl] = None
    
    # Technical details
    implementation_language: Optional[str] = None
    runtime_requirements: Optional[List[str]] = None
    installation_command: Optional[str] = None
    
    # Capabilities
    tools: Optional[List[MCPTool]] = None
    resources: Optional[List[MCPResource]] = None
    prompts: Optional[List[MCPPrompt]] = None
    
    # Categorization
    categories: List[ServerCategory] = []
    operations: List[OperationType] = []
    data_types: List[str] = []
    
    # Metadata
    registry_source: RegistrySource
    source_url: Optional[HttpUrl] = None
    last_updated: Optional[datetime] = None
    popularity_score: Optional[int] = None
    download_count: Optional[int] = None
    
    # Raw data for reference
    raw_metadata: Optional[Dict[str, Any]] = None


class RelationshipType(str, Enum):
    SIMILAR_FUNCTIONALITY = "similar_functionality"
    COMPLEMENTARY = "complementary"
    DEPENDS_ON = "depends_on"
    ALTERNATIVE_TO = "alternative_to"
    EXTENDS = "extends"
    INTEGRATES_WITH = "integrates_with"
    SAME_AUTHOR = "same_author"
    SAME_CATEGORY = "same_category"
    DATA_FLOW = "data_flow"


class ServerRelationship(BaseModel):
    id: str
    source_server_id: str
    target_server_id: str
    relationship_type: RelationshipType
    confidence_score: float  # 0.0 to 1.0
    description: Optional[str] = None
    evidence: Optional[List[str]] = None  # Why this relationship exists
    created_at: datetime
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v


class OntologyCategory(BaseModel):
    id: str
    name: str
    description: str
    parent_category_id: Optional[str] = None
    subcategories: List[str] = []
    servers: List[str] = []  # Server IDs
    
    # Ontological properties
    data_domains: List[str] = []  # What kind of data
    operational_patterns: List[str] = []  # How they operate
    integration_patterns: List[str] = []  # How they connect


class RegistrySnapshot(BaseModel):
    registry_source: RegistrySource
    snapshot_date: datetime
    url: Optional[HttpUrl] = None
    servers_count: int
    servers: List[MCPServer]
    metadata: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None


class KnowledgeGraph(BaseModel):
    created_at: datetime
    last_updated: datetime
    servers: List[MCPServer]
    relationships: List[ServerRelationship]
    categories: List[OntologyCategory]
    registry_snapshots: List[RegistrySnapshot]
    
    def get_server_by_id(self, server_id: str) -> Optional[MCPServer]:
        return next((s for s in self.servers if s.id == server_id), None)
    
    def get_servers_by_category(self, category: ServerCategory) -> List[MCPServer]:
        return [s for s in self.servers if category in s.categories]
    
    def get_relationships_for_server(self, server_id: str) -> List[ServerRelationship]:
        return [r for r in self.relationships 
                if r.source_server_id == server_id or r.target_server_id == server_id]