# LangGraph MCP Server Orchestrator

## Overview

The LangGraph MCP Server Orchestrator is a system that creates composable pipelines by automatically finding and chaining MCP (Model Context Protocol) servers based on natural language tasks. It uses LangGraph to orchestrate multiple agents that interact with different MCP servers to accomplish complex multi-step tasks.

## Architecture

### Core Components

1. **SupervisorAgent** - Analyzes tasks and determines required capabilities
2. **PipelineBuilder** - Finds compatible MCP servers and builds execution pipelines
3. **MCPServerAgent** - Individual agents that wrap MCP server interactions
4. **PipelineCoordinator** - Manages the sequential execution of pipeline steps
5. **MCPOrchestrator** - Main orchestrator that sets up and runs the LangGraph

### Flow

```
User Task → Supervisor Agent → Pipeline Builder → MCP Server Agents → Result Aggregator
```

## Key Features

### Task Analysis
- Parses natural language tasks to identify required capabilities
- Determines necessary server categories (database, API, data processing, etc.)
- Identifies required operations (read, write, query, transform, etc.)

### Server Discovery
- Searches the MCP server knowledge graph for compatible servers
- Matches server capabilities to task requirements
- Considers server relationships and compatibility

### Pipeline Building
- Creates logical execution sequences based on data flow patterns
- Orders servers from data sources → processing → AI/ML → outputs
- Handles dependencies and data passing between steps

### Mock Execution
- Simulates MCP server calls for testing without actual server deployment
- Generates realistic mock responses based on server categories
- Provides detailed logging and progress tracking

## Expected MCP Server Result Types

Based on the ASKG models, MCP servers return:

### Tool Results
```json
{
  "type": "tool_result",
  "tool_name": "search_database",
  "parameters": {...},
  "result": {...}
}
```

### Resource Results
```json
{
  "type": "resource_result",
  "uri": "file://path/to/resource",
  "content": "...",
  "mime_type": "application/json"
}
```

### Data Processing Results
```json
{
  "type": "processed_data",
  "data": {...},
  "metrics": {
    "processing_time": 0.5,
    "records_processed": 1000
  }
}
```

### API Integration Results
```json
{
  "type": "api_response",
  "status": "success",
  "data": {...},
  "headers": {...}
}
```

## Example Call Chains

### 1. Cryptocurrency Analysis
```
Task: "Analyze cryptocurrency market trends"
Pipeline:
  1. CoinMarketCap MCP → fetch market data
  2. Data Processing MCP → analyze trends
  3. AI/ML MCP → generate predictions
  4. File System MCP → save report
```

### 2. Database Report Generation
```
Task: "Generate user activity report"
Pipeline:
  1. Database MCP → query user data
  2. Data Processing MCP → aggregate statistics
  3. Chart Generation MCP → create visualizations
  4. File System MCP → save report
```

### 3. API Data Integration
```
Task: "Sync customer data from multiple APIs"
Pipeline:
  1. REST API MCP → fetch from API 1
  2. GraphQL API MCP → fetch from API 2
  3. Data Processing MCP → merge and deduplicate
  4. Database MCP → store results
```

## Usage

### Basic Usage

```python
import asyncio
from langgraph_orchestrator import MCPOrchestrator
from neo4j_integration import Neo4jManager

async def main():
    # Initialize
    neo4j_manager = Neo4jManager(instance="local")
    orchestrator = MCPOrchestrator(neo4j_manager)
    
    # Execute task
    results = await orchestrator.execute_task(
        "Process customer feedback and generate insights"
    )
    
    print(f"Results: {results}")
    neo4j_manager.close()

asyncio.run(main())
```

### Running Tests

```bash
# Run the test suite
python test_orchestrator.py

# Or run specific components
python -c "from langgraph_orchestrator import main; import asyncio; asyncio.run(main())"
```

## Configuration

The system uses the existing `config.yaml` for Neo4j connection settings:

```yaml
neo4j:
  local:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "mcpservers"
  remote:
    uri: "bolt://remote-host:7687"
    user: "neo4j"
    password: "password"
```

## Mock vs Real MCP Calls

### Current Implementation (Mock)
- Prints "calling MCP server xxx" instead of actual calls
- Generates realistic mock responses based on server categories
- Useful for testing pipeline logic without MCP server deployment

### Future Real Implementation
- Would integrate with actual MCP client libraries
- Make real network calls to MCP servers
- Handle authentication, error recovery, and retries

## Server Categories and Capabilities

### Database Servers
- **Operations**: READ, WRITE, QUERY
- **Mock Response**: Database records with counts
- **Examples**: Neo4j, PostgreSQL, MongoDB MCP servers

### API Integration Servers
- **Operations**: READ, WRITE, EXECUTE
- **Mock Response**: API responses with status codes
- **Examples**: REST API, GraphQL, OAuth MCP servers

### Data Processing Servers
- **Operations**: TRANSFORM, ANALYZE
- **Mock Response**: Processed data with metrics
- **Examples**: Pandas, NumPy, ETL MCP servers

### File System Servers
- **Operations**: READ, WRITE
- **Mock Response**: File operation results
- **Examples**: Local filesystem, S3, Google Drive MCP servers

### AI/ML Servers
- **Operations**: EXECUTE, ANALYZE
- **Mock Response**: AI predictions with confidence scores
- **Examples**: OpenAI, Hugging Face, custom ML model servers

## Error Handling

The system handles errors at multiple levels:

1. **Agent Level**: Individual MCP server call failures
2. **Pipeline Level**: Step execution failures
3. **Orchestrator Level**: Overall task execution failures

Error information is collected and included in the final results:

```json
{
  "summary": {
    "status": "failed",
    "errors": [
      "Error in step 2 (Data Processing Server): Connection timeout",
      "Error in step 3 (AI Server): Invalid input format"
    ]
  }
}
```

## Future Enhancements

### 1. Real MCP Integration
- Integrate with actual MCP client libraries
- Handle authentication and connection management
- Implement retry logic and error recovery

### 2. Advanced Pipeline Optimization
- Use reinforcement learning to optimize pipeline selection
- Implement parallel execution for independent steps
- Add caching and memoization for expensive operations

### 3. Enhanced Task Analysis
- Use advanced NLP models for better task understanding
- Support multi-modal tasks (text, images, audio)
- Implement task decomposition for complex workflows

### 4. Monitoring and Observability
- Add comprehensive logging and metrics
- Implement distributed tracing for pipeline execution
- Create dashboards for monitoring system performance

### 5. Dynamic Server Discovery
- Real-time server capability detection
- Automatic server health monitoring
- Dynamic load balancing and failover

## Dependencies

```
pydantic>=2.0.0
neo4j>=5.0.0
langgraph>=0.0.40
langchain>=0.1.0
aiohttp>=3.8.0
pyyaml>=6.0
tqdm>=4.65.0
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.