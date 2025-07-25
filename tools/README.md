# Tools Directory

This directory contains utility scripts and diagnostic tools for the ASKG project.

## Available Tools

### `check_neo4j_server_count.py`
A diagnostic utility that connects to the Neo4j database and provides statistics about:
- Total number of nodes in the database
- Number of Server nodes
- Distribution of servers by registry source
- Sample server information
- Node types and their counts

#### Usage
```bash
# From project root
cd tools
python check_neo4j_server_count.py

# Or from anywhere
python tools/check_neo4j_server_count.py
```

#### Requirements
- Neo4j database running and accessible
- `.config.yaml` file with proper Neo4j configuration
- Required Python packages: `neo4j`, `pyyaml`

## Adding New Tools

When adding new utility scripts to this directory:

1. **Use descriptive names**: Prefix with the tool's purpose (e.g., `check_`, `analyze_`, `export_`)
2. **Include documentation**: Add a brief description in this README
3. **Handle dependencies**: Ensure required packages are listed in `requirements.txt`
4. **Error handling**: Include proper error handling and user-friendly messages
5. **Configuration**: Use the project's configuration system when possible

## Examples of Future Tools

- `analyze_data_quality.py` - Check data consistency and quality
- `export_server_list.py` - Export server data to various formats
- `backup_database.py` - Create database backups
- `migrate_schema.py` - Database schema migration utilities
- `performance_benchmark.py` - Performance testing tools 