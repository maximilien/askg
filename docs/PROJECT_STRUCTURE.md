# Project Structure Documentation

## Overview

The ASKG project follows a well-organized directory structure designed for maintainability, scalability, and clear separation of concerns. This document provides a comprehensive overview of the project organization and the purpose of each directory and file.

## 📁 Root Directory Structure

```
askg/
├── src/                    # Main Python source code
├── mcp/                    # MCP server implementation
├── frontend/               # Web-based chat interface
├── tests/                  # Test files (organized)
├── tools/                  # Utility and diagnostic tools
├── docs/                   # Project documentation
├── data/                   # Data storage and snapshots
├── logs/                   # Application logs
├── .config.yaml           # Main configuration file
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata
├── start.sh               # Service startup script
├── stop.sh                # Service management script
├── setup.sh               # Initial setup script
├── test.sh                # Test execution script
└── README.md              # Main project documentation
```

## 🐍 Source Code (`src/`)

### Core Application Logic
- **`models.py`**: Pydantic data models for servers, relationships, and ontology
- **`scrapers.py`**: Multi-registry scraping system with resumable operations
- **`neo4j_integration.py`**: Neo4j database integration and relationship inference
- **`text2cypher.py`**: AI-powered natural language to Cypher query conversion
- **`main.py`**: Main orchestration script for building the knowledge graph
- **`langgraph_orchestrator.py`**: LangGraph-based orchestration system
- **`master_data.py`**: Master data management and deduplication
- **`deduplication.py`**: Server deduplication and merging logic
- **`id_standardization.py`**: ID normalization and standardization
- **`scale_assessment.py`**: Performance and scalability assessment tools

### Data Processing
- **`analyze_deduplication.py`**: Analysis of deduplication results
- **`run_deduplication.py`**: Deduplication execution scripts
- **`run_full_deduplication.py`**: Complete deduplication pipeline
- **`run_sample_deduplication.py`**: Sample deduplication for testing
- **`glama_downloader.py`**: Glama.ai registry data downloader
- **`debug_scrapers.py`**: Debugging tools for scraper components

## 🔌 MCP Server (`mcp/`)

### Server Implementation
- **`server.py`**: Main MCP server with semantic search and text2cypher integration
- **`client_example.py`**: Example client for testing MCP server
- **`mcp_server.py`**: Core MCP server functionality
- **`requirements.txt`**: MCP server dependencies
- **`README.md`**: MCP server documentation

### Testing
- **`test_basic.py`**: Basic MCP server tests
- **`test_config.py`**: Configuration testing
- **`test_environment.py`**: Environment setup testing
- **`test_file_structure.py`**: File structure validation
- **`test_imports_simple.py`**: Import testing
- **`test_imports.py`**: Comprehensive import testing
- **`test_mcp_server.py`**: MCP server functionality tests
- **`test_requirements.py`**: Requirements validation
- **`test_yaml.py`**: YAML configuration testing

## 🌐 Frontend (`frontend/`)

### Application Structure
- **`package.json`**: Node.js dependencies and scripts
- **`package-lock.json`**: Dependency lock file
- **`tsconfig.json`**: TypeScript configuration
- **`README.md`**: Frontend documentation

### Source Code (`src/`)
- **`index.ts`**: Main application entry point
- **`components/`**: React components (if using React)
- **`styles/`**: CSS and styling files

### Public Assets (`public/`)
- **`index.html`**: Main HTML file with enhanced modal structure
- **`app.js`**: Main JavaScript application with comprehensive features:
  - Chat interface management
  - Real-time Socket.IO communication
  - D3.js graph visualization
  - Server details modal functionality
  - Graph resizing and interaction controls
  - Node and edge tooltips
  - Responsive design and animations
- **`styles.css`**: Comprehensive styling including:
  - Modal overlay and content styles
  - Graph visualization styling
  - Responsive design and animations
  - Dark theme and modern UI elements
- **`d3.v7.min.js`**: Local D3.js library for graph visualization

## 🧪 Tests (`tests/`)

### Core Functionality Tests
- **`test_ci_config.py`**: CI configuration testing
- **`test_ci_setup.py`**: CI setup validation
- **`test_config_detection.py`**: Configuration detection tests
- **`test_config_file.py`**: Configuration file validation
- **`test_config.py`**: General configuration testing
- **`test_direct_glama.py`**: Direct Glama integration testing
- **`test_fast_loading.py`**: Fast loading performance tests
- **`test_glama_detailed.py`**: Detailed Glama functionality tests
- **`test_global_ids.py`**: Global ID management testing
- **`test_mcp_search.py`**: MCP search functionality tests
- **`test_orchestrator.py`**: Orchestrator component testing
- **`test_uv_environment.py`**: UV environment validation

### Text2Cypher Tests
- **`test_text2cypher.py`**: Text2Cypher functionality testing
- **`test_cypher_cleaning.py`**: Cypher query cleaning validation
- **`test_text2cypher_integration.py`**: End-to-end integration testing

## 🛠️ Tools (`tools/`)

### Diagnostic and Utility Tools
- **`check_neo4j_server_count.py`**: Database diagnostic utility for checking server counts and statistics
- **`README.md`**: Tools directory documentation and guidelines

### Tool Guidelines
- **Naming Convention**: `action_purpose.py` (e.g., `check_neo4j_server_count.py`)
- **Configuration**: Use relative paths and proper error handling
- **Documentation**: Each tool should be documented in `tools/README.md`
- **Dependencies**: Minimal dependencies, use existing project configuration

## 📚 Documentation (`docs/`)

### Core Documentation
- **`FRONTEND_CHAT_INTERFACE.md`**: Comprehensive chat interface documentation
- **`TEXT2CYPHER_SETUP.md`**: AI-powered query conversion setup guide
- **`PROJECT_STRUCTURE.md`**: This file - project organization documentation
- **`RECENT_UPDATES.md`**: Summary of recent changes and improvements

### Technical Documentation
- **`LANGGRAPH_ORCHESTRATOR.md`**: LangGraph Orchestrator documentation
- **`NEO4J_INSTANCES.md`**: Neo4j instance information and setup
- **`MCPMARKET_INTEGRATION.md`**: MCP Market integration guide

### Assessment and Progress
- **`ASSESSMENT_SUMMARY.md`**: Project assessment summary
- **`PROGRESS_BARS.md`**: Progress tracking documentation
- **`SCALE_IMPROVEMENT_PLAN.md`**: Performance improvement plans
- **`SCALE_IMPROVEMENT_RESULTS.md`**: Performance improvement results

### Claude Documentation
- **`Claude.md/Agent-Server Knowledge Graph`**: Claude agent-server knowledge graph notes

## 💾 Data Storage (`data/`)

### Registry Data
- **`registries/`**: Organized by registry source
  - **`github/`**: GitHub registry snapshots
  - **`glama/`**: Glama.ai registry data
  - **`mcp_so/`**: mcp.so registry snapshots
  - **`mastra/`**: Mastra.ai registry data

### Snapshots
- **`snapshots/`**: Combined data snapshots
  - **`combined_snapshots.json`**: Merged registry data
  - **`deduplication_results/`**: Deduplication analysis results

## 📋 Configuration Files

### Main Configuration
- **`.config.yaml`**: Primary configuration file
  - Neo4j connection settings
  - GitHub API configuration
  - Registry URLs and parameters
  - Scraping settings and timeouts

### Environment Configuration
- **`.env`**: Environment variables (not in version control)
  - OpenAI API key
  - Database credentials
  - Debug settings

### Project Configuration
- **`pyproject.toml`**: Python project metadata
- **`requirements.txt`**: Python dependencies
- **`ruff.toml`**: Code formatting configuration

## 🚀 Service Management Scripts

### Startup and Management
- **`start.sh`**: Enhanced service startup with validation
  - Conflict detection and resolution
  - Port availability checking
  - Neo4j connection validation
  - Process management and PID tracking

### Service Control
- **`stop.sh`**: Comprehensive service management
  - Status checking and monitoring
  - Graceful shutdown procedures
  - Process cleanup and restart capabilities
  - Help and usage information

### Setup and Testing
- **`setup.sh`**: Automated initial setup
  - Dependency installation
  - Directory creation
  - Configuration setup
  - Environment validation

- **`test.sh`**: Automated testing
  - Test discovery and execution
  - Coverage reporting
  - Error handling and reporting

## 🔧 Development Tools

### Code Quality
- **`lint.sh`**: Code linting and formatting
- **`setup-precommit.sh`**: Pre-commit hook setup
- **`test_fast.sh`**: Fast test execution for development

### Build and Deployment
- **`frontend/package.json`**: Frontend build scripts
- **`frontend/tsconfig.json`**: TypeScript compilation settings

## 📊 Logs and Monitoring

### Application Logs
- **`logs/`**: Application log files
  - Scraping operation logs
  - Error logs and debugging information
  - Performance monitoring data

## 🎯 Key Design Principles

### Organization
- **Separation of Concerns**: Clear boundaries between different components
- **Modularity**: Self-contained modules with well-defined interfaces
- **Scalability**: Structure supports growth and new features
- **Maintainability**: Easy to understand and modify

### File Naming
- **Descriptive Names**: Files clearly indicate their purpose
- **Consistent Conventions**: Standard naming patterns throughout
- **Hierarchical Organization**: Logical grouping of related files

### Configuration Management
- **Centralized Configuration**: Single source of truth for settings
- **Environment Separation**: Clear distinction between development and production
- **Security**: Sensitive data kept out of version control

### Testing Strategy
- **Comprehensive Coverage**: Tests for all major components
- **Organized Structure**: Tests mirror source code organization
- **Automated Execution**: Easy to run and maintain

## 🔄 Recent Structural Changes

### File Reorganization
- **Test Files**: Moved all Python test files from root to `tests/` directory
- **Utility Files**: Created `tools/` directory for diagnostic and utility scripts
- **Documentation**: Enhanced documentation structure with new guides

### Enhanced Organization
- **Clear Separation**: Distinct directories for different types of files
- **Improved Navigation**: Logical file placement and naming
- **Better Maintainability**: Easier to find and modify specific components

### Development Workflow
- **Streamlined Testing**: Organized test structure for better development experience
- **Tool Integration**: Dedicated space for development and diagnostic tools
- **Documentation**: Comprehensive guides for all project aspects

This project structure provides a solid foundation for continued development and maintenance of the ASKG system, with clear organization and comprehensive documentation supporting all aspects of the application. 