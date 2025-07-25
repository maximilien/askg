from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

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
    description: str | None = None
    parameters: dict[str, Any] | None = None


class MCPResource(BaseModel):
    uri: str
    name: str | None = None
    description: str | None = None
    mime_type: str | None = None


class MCPPrompt(BaseModel):
    name: str
    description: str | None = None
    arguments: list[dict[str, Any]] | None = None


class MCPServer(BaseModel):
    id: str
    name: str
    description: str | None = None
    version: str | None = None
    author: str | None = None
    license: str | None = None
    homepage: HttpUrl | None = None
    repository: HttpUrl | None = None

    # Technical details
    implementation_language: str | None = None
    runtime_requirements: list[str] | None = None
    installation_command: str | None = None

    # Capabilities
    tools: list[MCPTool] | None = None
    resources: list[MCPResource] | None = None
    prompts: list[MCPPrompt] | None = None

    # Categorization
    categories: list[ServerCategory] = []
    operations: list[OperationType] = []
    data_types: list[str] = []

    # Metadata
    registry_source: RegistrySource
    source_url: HttpUrl | None = None
    last_updated: datetime | None = None
    popularity_score: int | None = None
    download_count: int | None = None

    # Raw data for reference
    raw_metadata: dict[str, Any] | None = None


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
    description: str | None = None
    evidence: list[str] | None = None  # Why this relationship exists
    created_at: datetime

    @validator("confidence_score")
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class OntologyCategory(BaseModel):
    id: str
    name: str
    description: str
    parent_category_id: str | None = None
    subcategories: list[str] = []
    servers: list[str] = []  # Server IDs

    # Ontological properties
    data_domains: list[str] = []  # What kind of data
    operational_patterns: list[str] = []  # How they operate
    integration_patterns: list[str] = []  # How they connect


class RegistrySnapshot(BaseModel):
    registry_source: RegistrySource
    snapshot_date: datetime
    url: HttpUrl | None = None
    servers_count: int
    servers: list[MCPServer]
    metadata: dict[str, Any] | None = None
    checksum: str | None = None


class KnowledgeGraph(BaseModel):
    created_at: datetime
    last_updated: datetime
    servers: list[MCPServer]
    relationships: list[ServerRelationship]
    categories: list[OntologyCategory]
    registry_snapshots: list[RegistrySnapshot]

    def get_server_by_id(self, server_id: str) -> MCPServer | None:
        return next((s for s in self.servers if s.id == server_id), None)

    def get_servers_by_category(self, category: ServerCategory) -> list[MCPServer]:
        return [s for s in self.servers if category in s.categories]

    def get_relationships_for_server(self, server_id: str) -> list[ServerRelationship]:
        return [r for r in self.relationships
                if r.source_server_id == server_id or r.target_server_id == server_id]
