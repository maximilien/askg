# askg
## Agent-Server Knowledge Graph

This is the repository for the ASKG, a project of OAKS, the Open-source Agentic AI Knowledge Stack.

OAKS is a collaboratory, comprised of a set of OSS AI partners and their projects that can be integrated with one another, forming a stack for writing AI applications.

OAKS is maintained as a Notion workspace at 

oaks.town

The ASKG project aims to maintain a knowledge graph of MCP servers and A2A agents that could be used both by himans and AI developer tools to write composable workflows.

We aim to automate the ingestion of MCP server definitions and make the knowledge graph publicly available.  Neo4j provides an instance of AuraDB, a cloud Neo4j database, to host, visualize, and analyze the graph.

*askg* comprehensive knowledge graph system for Model Context Protocol (MCP) servers, built with Python, Pydantic, and Neo4j.


## Features

- **Multi-Registry Scraping**: Automatically discovers MCP servers from:
  - GitHub repositories
  - mcp.so
  - Glama.ai (including glama.json files)
  - Mastra.ai MCP registry
- **Intelligent Categorization**: Automatically categorizes servers by functionality, data types, and operations
- **Relationship Inference**: Discovers relationships between servers based on similarity, complementarity, and dependencies
- **Versioned Storage**: Maintains historical snapshots with change detection
- **Neo4j Integration**: Loads data into Neo4j graph database for advanced querying
- **Resumable Operations**: Efficiently handles incremental updates without re-downloading unchanged data

## Architecture

### Core Components

- **`models.py`**: Pydantic models for servers, relationships, and ontology
- **`scrapers.py`**: Multi-registry scraping system with resumable operations
- **`neo4j_integration.py`**: Neo4j database integration and relationship inference
- **`main.py`**: Main orchestration script
- **`config.yaml`**: Configuration for databases, APIs, and scraping parameters

### Data Model

The system models MCP servers with rich metadata including:
- Basic information (name, description, author, version)
- Technical details (language, installation, capabilities)
- Categorization (functionality, operations, data types)
- Registry metadata (source, popularity, last updated)
- Tools, resources, and prompts exposed by the server

## Setup

### Prerequisites

1. **Neo4j Database**: Install and run Neo4j locally
   ```bash
   # Using Docker
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/mcpservers neo4j:latest
   ```

2. **GitHub Token**: Create a GitHub personal access token for API access
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create a token with `repo` and `public_repo` permissions

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd askg
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the system:
   - Edit `config.yaml` to set your GitHub token
   - Adjust Neo4j connection details if needed
   - Modify scraping parameters as desired

## Usage

### Basic Usage

Build the complete knowledge graph:
```bash
python main.py
```

### Advanced Options

```bash
# Force refresh all registry data
python main.py --force-refresh

# Scrape specific registries only
python main.py --registries github glama

# Skip Neo4j loading (useful for development)
python main.py --skip-neo4j

# Clear Neo4j database before loading
python main.py --clear-neo4j

# Show statistics only
python main.py --stats-only
```

### Configuration

The `config.yaml` file allows you to customize:

- **Neo4j connection**: URI, username, password
- **GitHub API**: Personal access token
- **Storage paths**: Local directories for data storage
- **Scraping parameters**: Timeouts, retry logic, user agents
- **Registry settings**: URLs and search parameters

## Data Storage

The system maintains organized local storage:

```
data/
├── registries/
│   ├── github/
│   │   ├── github_20240101_120000.json
│   │   └── github_20240102_120000.json
│   ├── glama/
│   ├── mcp_so/
│   └── mastra/
└── snapshots/
    └── combined_snapshots.json
```

Each registry snapshot is timestamped and includes:
- Server metadata
- Scraping timestamp
- Data checksums for change detection
- Source URLs and metadata

## Neo4j Queries

Once loaded, you can query the knowledge graph using Cypher:

### Find Popular Servers
```cypher
MATCH (s:Server) 
WHERE s.popularity_score IS NOT NULL
RETURN s.name, s.description, s.popularity_score
ORDER BY s.popularity_score DESC 
LIMIT 10
```

### Find Servers by Category
```cypher
MATCH (s:Server)
WHERE 'database' IN s.categories
RETURN s.name, s.description, s.repository
```

### Discover Server Relationships
```cypher
MATCH (s1:Server)-[r:RELATES_TO]->(s2:Server)
WHERE r.confidence_score > 0.7
RETURN s1.name, r.type, s2.name, r.confidence_score
ORDER BY r.confidence_score DESC
```

### Find Similar Servers
```cypher
MATCH (s:Server {name: 'your-server-name'})
MATCH (s)-[r:RELATES_TO {type: 'similar_functionality'}]->(similar:Server)
RETURN similar.name, similar.description, r.confidence_score
ORDER BY r.confidence_score DESC
```

### Category Statistics
```cypher
MATCH (s:Server)
UNWIND s.categories as category
RETURN category, COUNT(s) as server_count
ORDER BY server_count DESC
```

## Extending the System

### Adding New Registries

1. Create a new scraper class inheriting from `BaseScraper`
2. Add the registry to the `RegistrySource` enum
3. Implement the `scrape()` method
4. Register the scraper in `ScrapingOrchestrator`

### Custom Relationship Types

1. Add new relationship types to the `RelationshipType` enum
2. Implement inference logic in `RelationshipInferencer`
3. Update Neo4j queries as needed

### Enhanced Categorization

1. Modify the `categorize_server()` method in `BaseScraper`
2. Add new categories to the `ServerCategory` enum
3. Update the ontology creation in `main.py`

## Troubleshooting

### Common Issues

1. **GitHub Rate Limiting**: Ensure you have a valid GitHub token configured
2. **Neo4j Connection**: Verify Neo4j is running and credentials are correct
3. **Missing Dependencies**: Install all required packages from `requirements.txt`
4. **Memory Issues**: For large datasets, consider increasing system memory or implementing pagination

### Debug Mode

Enable detailed logging by setting environment variables:
```bash
export PYTHONPATH=.
export DEBUG=1
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
>>>>>>> ba1fa0f (loading locally and remotely)
