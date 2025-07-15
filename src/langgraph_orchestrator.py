"""
LangGraph-based MCP Server Orchestration System
Creates composable pipelines by finding and chaining MCP servers based on tasks.
"""

import asyncio
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
try:
    from langgraph.graph import Graph, END, START
    from langgraph.prebuilt import ToolInvocation, ToolExecutor
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Create simple stubs for when LangGraph is not available
    LANGGRAPH_AVAILABLE = False
    class Graph:
        def __init__(self):
            self.nodes = {}
            self.edges = []
        
        def add_node(self, name, func):
            self.nodes[name] = func
        
        def add_edge(self, from_node, to_node):
            self.edges.append((from_node, to_node))
        
        def compile(self):
            return SimpleWorkflow(self.nodes, self.edges)
    
    START = "START"
    END = "END"
    
    class SimpleWorkflow:
        def __init__(self, nodes, edges):
            self.nodes = nodes
            self.edges = edges
        
        async def ainvoke(self, state):
            # Simple sequential execution
            current_state = state
            for node_name, node_func in self.nodes.items():
                if node_name in ["supervisor", "coordinator", "aggregator"]:
                    current_state = await node_func(current_state)
            return current_state

from models import MCPServer, ServerCategory, OperationType, RelationshipType
from neo4j_integration import Neo4jManager


class AgentState(TypedDict):
    """State shared between all agents in the graph"""
    task: str
    current_data: Any
    pipeline_history: List[Dict[str, Any]]
    selected_servers: List[MCPServer]
    results: Dict[str, Any]
    errors: List[str]
    completed: bool


class PipelineStep(TypedDict):
    """Represents a single step in the execution pipeline"""
    agent_id: str
    server: MCPServer
    input_data: Any
    output_data: Any
    timestamp: datetime
    status: str


@dataclass
class MCPServerCapability:
    """Represents what an MCP server can do"""
    server_id: str
    name: str
    categories: List[ServerCategory]
    operations: List[OperationType]
    input_types: List[str]
    output_types: List[str]
    confidence_score: float = 0.0


class MCPServerAgent:
    """Individual agent that wraps MCP server interactions"""
    
    def __init__(self, server: MCPServer):
        self.server = server
        self.agent_id = f"mcp_agent_{server.id}"
    
    async def execute(self, input_data: Any) -> Dict[str, Any]:
        """Mock execution of MCP server - prints instead of actual call"""
        print(f"🤖 Agent {self.agent_id} calling MCP server: {self.server.name}")
        print(f"   📊 Input: {str(input_data)[:100]}...")
        print(f"   🔧 Categories: {[cat.value for cat in self.server.categories]}")
        print(f"   ⚙️  Operations: {[op.value for op in self.server.operations]}")
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Mock response based on server type
        mock_response = self._generate_mock_response(input_data)
        
        print(f"   ✅ Output: {str(mock_response)[:100]}...")
        return mock_response
    
    def _generate_mock_response(self, input_data: Any) -> Dict[str, Any]:
        """Generate realistic mock responses based on server category"""
        
        if ServerCategory.DATABASE in self.server.categories:
            return {
                "type": "database_result",
                "data": [{"id": 1, "name": "Sample Record", "value": 42}],
                "count": 1,
                "server": self.server.name
            }
        
        elif ServerCategory.API_INTEGRATION in self.server.categories:
            return {
                "type": "api_response",
                "status": "success",
                "data": {"message": "API call successful", "timestamp": datetime.now().isoformat()},
                "server": self.server.name
            }
        
        elif ServerCategory.DATA_PROCESSING in self.server.categories:
            return {
                "type": "processed_data",
                "data": {"processed": True, "result": "Data transformed successfully"},
                "metrics": {"processing_time": 0.1, "records_processed": 100},
                "server": self.server.name
            }
        
        elif ServerCategory.FILE_SYSTEM in self.server.categories:
            return {
                "type": "file_operation",
                "status": "success",
                "files": ["output.json", "result.txt"],
                "server": self.server.name
            }
        
        elif ServerCategory.AI_ML in self.server.categories:
            return {
                "type": "ai_result",
                "prediction": "Sample AI prediction",
                "confidence": 0.95,
                "model": "mock_model_v1",
                "server": self.server.name
            }
        
        else:
            return {
                "type": "generic_result",
                "message": f"Mock response from {self.server.name}",
                "data": str(input_data),
                "server": self.server.name
            }


class PipelineBuilder:
    """Builds execution pipelines by finding compatible MCP servers"""
    
    def __init__(self, neo4j_manager: Neo4jManager):
        self.neo4j = neo4j_manager
        self.server_capabilities = {}
    
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """Analyze task to determine required capabilities"""
        task_lower = task.lower()
        
        # Simple keyword-based analysis (could be enhanced with NLP)
        required_capabilities = {
            "categories": [],
            "operations": [],
            "keywords": [],
            "data_flow": []
        }
        
        # Category detection
        if any(word in task_lower for word in ["database", "sql", "query", "data"]):
            required_capabilities["categories"].append(ServerCategory.DATABASE)
        
        if any(word in task_lower for word in ["api", "rest", "http", "web"]):
            required_capabilities["categories"].append(ServerCategory.API_INTEGRATION)
        
        if any(word in task_lower for word in ["process", "transform", "analyze"]):
            required_capabilities["categories"].append(ServerCategory.DATA_PROCESSING)
        
        if any(word in task_lower for word in ["file", "storage", "save", "load"]):
            required_capabilities["categories"].append(ServerCategory.FILE_SYSTEM)
        
        if any(word in task_lower for word in ["ai", "ml", "predict", "model"]):
            required_capabilities["categories"].append(ServerCategory.AI_ML)
        
        # Operation detection
        if any(word in task_lower for word in ["read", "get", "fetch", "retrieve"]):
            required_capabilities["operations"].append(OperationType.READ)
        
        if any(word in task_lower for word in ["write", "save", "store", "update"]):
            required_capabilities["operations"].append(OperationType.WRITE)
        
        if any(word in task_lower for word in ["query", "search", "find"]):
            required_capabilities["operations"].append(OperationType.QUERY)
        
        if any(word in task_lower for word in ["execute", "run", "process"]):
            required_capabilities["operations"].append(OperationType.EXECUTE)
        
        if any(word in task_lower for word in ["transform", "convert", "change"]):
            required_capabilities["operations"].append(OperationType.TRANSFORM)
        
        return required_capabilities
    
    def find_compatible_servers(self, required_capabilities: Dict[str, Any]) -> List[MCPServer]:
        """Find MCP servers that match the required capabilities"""
        print(f"🔍 Searching for servers with capabilities: {required_capabilities}")
        
        # Mock server selection based on categories
        compatible_servers = []
        
        # In a real implementation, this would query Neo4j
        # For now, we'll create mock servers based on requirements
        
        if ServerCategory.DATABASE in required_capabilities["categories"]:
            compatible_servers.append(MCPServer(
                id="neo4j_server",
                name="Neo4j MCP Server",
                description="Provides graph database access",
                categories=[ServerCategory.DATABASE],
                operations=[OperationType.READ, OperationType.WRITE, OperationType.QUERY],
                registry_source="github"
            ))
        
        if ServerCategory.API_INTEGRATION in required_capabilities["categories"]:
            compatible_servers.append(MCPServer(
                id="rest_api_server",
                name="REST API MCP Server",
                description="Generic REST API integration",
                categories=[ServerCategory.API_INTEGRATION],
                operations=[OperationType.READ, OperationType.WRITE, OperationType.EXECUTE],
                registry_source="glama"
            ))
        
        if ServerCategory.DATA_PROCESSING in required_capabilities["categories"]:
            compatible_servers.append(MCPServer(
                id="pandas_server",
                name="Pandas Data Processing Server",
                description="Data processing and transformation",
                categories=[ServerCategory.DATA_PROCESSING],
                operations=[OperationType.TRANSFORM, OperationType.ANALYZE],
                registry_source="mcp.so"
            ))
        
        if ServerCategory.FILE_SYSTEM in required_capabilities["categories"]:
            compatible_servers.append(MCPServer(
                id="file_server",
                name="File System MCP Server",
                description="File operations and storage",
                categories=[ServerCategory.FILE_SYSTEM],
                operations=[OperationType.READ, OperationType.WRITE],
                registry_source="github"
            ))
        
        if ServerCategory.AI_ML in required_capabilities["categories"]:
            compatible_servers.append(MCPServer(
                id="openai_server",
                name="OpenAI MCP Server",
                description="AI/ML model integration",
                categories=[ServerCategory.AI_ML],
                operations=[OperationType.EXECUTE, OperationType.ANALYZE],
                registry_source="glama"
            ))
        
        print(f"✅ Found {len(compatible_servers)} compatible servers")
        for server in compatible_servers:
            print(f"   - {server.name} ({server.id})")
        
        return compatible_servers
    
    def build_pipeline(self, task: str, servers: List[MCPServer]) -> List[MCPServer]:
        """Build an execution pipeline by ordering servers logically"""
        print(f"🔗 Building pipeline for task: {task}")
        
        # Simple ordering based on typical data flow patterns
        # In a real implementation, this would use the relationship graph
        
        ordered_servers = []
        
        # 1. Data sources first (databases, APIs)
        for server in servers:
            if any(cat in server.categories for cat in [ServerCategory.DATABASE, ServerCategory.API_INTEGRATION]):
                ordered_servers.append(server)
        
        # 2. Processing servers
        for server in servers:
            if ServerCategory.DATA_PROCESSING in server.categories:
                ordered_servers.append(server)
        
        # 3. AI/ML servers
        for server in servers:
            if ServerCategory.AI_ML in server.categories:
                ordered_servers.append(server)
        
        # 4. Output servers (file system, etc.)
        for server in servers:
            if ServerCategory.FILE_SYSTEM in server.categories and server not in ordered_servers:
                ordered_servers.append(server)
        
        # Add any remaining servers
        for server in servers:
            if server not in ordered_servers:
                ordered_servers.append(server)
        
        print(f"📋 Pipeline order:")
        for i, server in enumerate(ordered_servers, 1):
            print(f"   {i}. {server.name}")
        
        return ordered_servers


class SupervisorAgent:
    """Main supervisor agent that orchestrates the entire pipeline"""
    
    def __init__(self, neo4j_manager: Neo4jManager):
        self.neo4j = neo4j_manager
        self.pipeline_builder = PipelineBuilder(neo4j_manager)
        self.agents = {}
    
    async def supervise(self, state: AgentState) -> AgentState:
        """Main supervision logic"""
        print(f"🎯 Supervisor: Analyzing task '{state['task']}'")
        
        # Step 1: Analyze the task
        required_capabilities = self.pipeline_builder.analyze_task(state['task'])
        print(f"📊 Required capabilities: {required_capabilities}")
        
        # Step 2: Find compatible servers
        compatible_servers = self.pipeline_builder.find_compatible_servers(required_capabilities)
        
        # Step 3: Build execution pipeline
        pipeline = self.pipeline_builder.build_pipeline(state['task'], compatible_servers)
        
        # Update state
        state['selected_servers'] = pipeline
        state['results'] = {}
        state['errors'] = []
        
        print(f"✅ Supervisor: Pipeline ready with {len(pipeline)} servers")
        return state
    
    def create_agent_for_server(self, server: MCPServer) -> MCPServerAgent:
        """Create or get an agent for a specific server"""
        if server.id not in self.agents:
            self.agents[server.id] = MCPServerAgent(server)
        return self.agents[server.id]


class PipelineCoordinator:
    """Coordinates the execution of the pipeline"""
    
    def __init__(self, supervisor: SupervisorAgent):
        self.supervisor = supervisor
    
    async def execute_pipeline(self, state: AgentState) -> AgentState:
        """Execute the pipeline sequentially"""
        print(f"🚀 Pipeline Coordinator: Starting execution")
        
        current_data = {"task": state['task'], "initial_input": True}
        
        for i, server in enumerate(state['selected_servers']):
            print(f"\n--- Step {i+1}/{len(state['selected_servers'])} ---")
            
            # Create agent for this server
            agent = self.supervisor.create_agent_for_server(server)
            
            try:
                # Execute the agent
                result = await agent.execute(current_data)
                
                # Store result
                state['results'][server.id] = result
                
                # Pass result to next step
                current_data = result
                
                # Record pipeline step
                step = {
                    "step": i + 1,
                    "agent_id": agent.agent_id,
                    "server_name": server.name,
                    "server_id": server.id,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
                state['pipeline_history'].append(step)
                
            except Exception as e:
                error_msg = f"Error in step {i+1} ({server.name}): {str(e)}"
                state['errors'].append(error_msg)
                print(f"❌ {error_msg}")
                
                # Record failed step
                step = {
                    "step": i + 1,
                    "agent_id": agent.agent_id,
                    "server_name": server.name,
                    "server_id": server.id,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                state['pipeline_history'].append(step)
        
        state['current_data'] = current_data
        state['completed'] = True
        
        print(f"\n✅ Pipeline Coordinator: Execution completed")
        return state


class MCPOrchestrator:
    """Main orchestrator that sets up and runs the LangGraph"""
    
    def __init__(self, neo4j_manager: Neo4jManager):
        self.neo4j = neo4j_manager
        self.supervisor = SupervisorAgent(neo4j_manager)
        self.coordinator = PipelineCoordinator(self.supervisor)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Graph:
        """Build the LangGraph execution graph"""
        
        # Define the graph
        workflow = Graph()
        
        # Add nodes
        workflow.add_node("supervisor", self.supervisor.supervise)
        workflow.add_node("coordinator", self.coordinator.execute_pipeline)
        workflow.add_node("aggregator", self._aggregate_results)
        
        # Add edges
        workflow.add_edge(START, "supervisor")
        workflow.add_edge("supervisor", "coordinator")
        workflow.add_edge("coordinator", "aggregator")
        workflow.add_edge("aggregator", END)
        
        return workflow.compile()
    
    async def _aggregate_results(self, state: AgentState) -> AgentState:
        """Aggregate and format final results"""
        print(f"\n📊 Result Aggregator: Compiling final results")
        
        # Create summary
        summary = {
            "task": state['task'],
            "status": "completed" if state['completed'] and not state['errors'] else "failed",
            "servers_used": len(state['selected_servers']),
            "pipeline_steps": len(state['pipeline_history']),
            "errors": state['errors'],
            "execution_time": "mock_duration",
            "final_result": state['current_data']
        }
        
        state['results']['summary'] = summary
        
        print(f"📈 Execution Summary:")
        print(f"   Task: {summary['task']}")
        print(f"   Status: {summary['status']}")
        print(f"   Servers Used: {summary['servers_used']}")
        print(f"   Pipeline Steps: {summary['pipeline_steps']}")
        print(f"   Errors: {len(summary['errors'])}")
        
        return state
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a task using the orchestrated pipeline"""
        print(f"🎬 Starting task execution: {task}")
        print("=" * 80)
        
        # Initialize state
        initial_state = AgentState(
            task=task,
            current_data=None,
            pipeline_history=[],
            selected_servers=[],
            results={},
            errors=[],
            completed=False
        )
        
        # Execute the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        print("\n" + "=" * 80)
        print("✅ Task execution completed!")
        
        return final_state['results']


# Example usage and testing
async def main():
    """Main function to demonstrate the system"""
    
    # Initialize Neo4j manager (using local instance)
    neo4j_manager = Neo4jManager(instance="local")
    
    # Create orchestrator
    orchestrator = MCPOrchestrator(neo4j_manager)
    
    # Test different types of tasks
    test_tasks = [
        "Analyze cryptocurrency market trends from multiple sources",
        "Process customer data and generate insights report",
        "Deploy application code and set up monitoring",
        "Search for vulnerabilities in the codebase and create a report",
        "Transform JSON data into CSV format and save to file system"
    ]
    
    for task in test_tasks:
        print(f"\n{'='*80}")
        print(f"🎯 TESTING TASK: {task}")
        print(f"{'='*80}")
        
        try:
            results = await orchestrator.execute_task(task)
            print(f"\n✅ Task completed successfully")
            print(f"📊 Results summary: {results.get('summary', {})}")
        except Exception as e:
            print(f"\n❌ Task failed: {str(e)}")
        
        print(f"\n{'='*80}")
        await asyncio.sleep(1)  # Brief pause between tasks
    
    # Close Neo4j connection
    neo4j_manager.close()


if __name__ == "__main__":
    asyncio.run(main())