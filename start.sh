#!/bin/bash

# Function to check if a port is already in use
check_port_available() {
    local port=$1
    local service_name=$2
    if lsof -i :$port >/dev/null 2>&1; then
        echo "❌ Port $port is already in use by another process"
        echo "   Please stop any existing $service_name processes first"
        echo "   You can use: ./stop.sh stop"
        return 1
    else
        echo "✅ Port $port is available for $service_name"
        return 0
    fi
}

# Function to check if .config.yaml exists and has remote Neo4j configuration
check_remote_config() {
    if [ -f ".config.yaml" ]; then
        if python3 -c "
import yaml
try:
    with open('.config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    if 'neo4j' in config and 'remote' in config['neo4j']:
        print('remote')
    else:
        print('local')
except:
    print('local')
" 2>/dev/null; then
            return 0
        fi
    fi
    echo "local"
}

# Function to validate that a process is actually running
validate_process() {
    local pid=$1
    local service_name=$2
    local port=$3
    
    # Wait a moment for the process to start
    sleep 2
    
    # Check if process is running
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "❌ $service_name process (PID: $pid) failed to start"
        return 1
    fi
    
    # Check if port is being used
    if ! lsof -i :$port >/dev/null 2>&1; then
        echo "❌ $service_name is not listening on port $port"
        return 1
    fi
    
    echo "✅ $service_name is running (PID: $pid, Port: $port)"
    return 0
}

# Check if services are already running
echo "🔍 Checking if services are already running..."
if [ -f ".askg.pid" ]; then
    echo "⚠️  Found existing .askg.pid file"
    echo "   Services may already be running. Checking status..."
    
    # Read existing PIDs
    NEO4J_TYPE=$(sed -n '1p' .askg.pid 2>/dev/null)
    MCP_PID=$(sed -n '2p' .askg.pid 2>/dev/null)
    FRONTEND_PID=$(sed -n '3p' .askg.pid 2>/dev/null)
    
    # Check if processes are actually running
    if kill -0 "$MCP_PID" 2>/dev/null && lsof -i :8200 >/dev/null 2>&1; then
        echo "❌ MCP server is already running (PID: $MCP_PID)"
        echo "   Please stop existing services first: ./stop.sh stop"
        exit 1
    fi
    
    if kill -0 "$FRONTEND_PID" 2>/dev/null && lsof -i :3200 >/dev/null 2>&1; then
        echo "❌ Frontend is already running (PID: $FRONTEND_PID)"
        echo "   Please stop existing services first: ./stop.sh stop"
        exit 1
    fi
    
    echo "ℹ️  Found stale .askg.pid file - will be replaced"
fi

# Check port availability
echo "🔍 Checking port availability..."
if ! check_port_available 8200 "MCP Server"; then
    exit 1
fi

if ! check_port_available 3200 "Frontend"; then
    exit 1
fi

# Determine which Neo4j instance to use
echo "🔍 Checking Neo4j configuration..."
NEO4J_INSTANCE=$(check_remote_config)

if [ "$NEO4J_INSTANCE" = "remote" ]; then
    echo "📡 Found remote Neo4j configuration in .config.yaml"
    echo "🔗 Attempting to connect to remote Neo4j instance..."
else
    echo "🏠 Using local Neo4j Desktop instance"
fi

# Check Neo4j connection
echo "🔍 Testing Neo4j connection..."
if ! python3 -c "
import sys
sys.path.append('src')
from neo4j_integration import Neo4jManager
instance = '$NEO4J_INSTANCE'
try:
    with Neo4jManager(instance=instance) as neo4j:
        with neo4j.driver.session() as session:
            result = session.run('RETURN 1 as test')
            print('✅ Neo4j connection successful')
            print(f'🎯 Connected to: {instance} instance')
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    if instance == 'remote':
        print('Please check your remote Neo4j configuration in .config.yaml')
        print('Ensure the URI, username, and password are correct')
    else:
        print('Please ensure Neo4j Desktop is running and accessible on localhost:7687')
        print('Default credentials: neo4j/mcpservers')
    sys.exit(1)
" 2>/dev/null; then
    echo "❌ Neo4j is not accessible."
    if [ "$NEO4J_INSTANCE" = "remote" ]; then
        echo "Please check your remote Neo4j configuration in .config.yaml"
        echo "Ensure the URI, username, and password are correct"
    else
        echo "Please start Neo4j Desktop and ensure it's running on localhost:7687"
        echo "Default credentials: neo4j/mcpservers"
    fi
    exit 1
fi

# Start MCP server (Python backend)
echo "🚀 Starting MCP server..."
python3 mcp/server.py --port 8200 --instance $NEO4J_INSTANCE &
MCP_PID=$!
echo "MCP server started with PID $MCP_PID (using $NEO4J_INSTANCE instance)"

# Validate MCP server started correctly
if ! validate_process "$MCP_PID" "MCP Server" 8200; then
    echo "❌ Failed to start MCP server"
    exit 1
fi

# Build and start frontend (Node/TypeScript)
echo "🚀 Building frontend..."
cd frontend
if ! npm run build; then
    echo "❌ Frontend build failed"
    exit 1
fi

echo "🚀 Starting frontend..."
PORT=3200 npm start &
FRONTEND_PID=$!
cd ..
echo "Frontend started with PID $FRONTEND_PID"

# Validate frontend started correctly
if ! validate_process "$FRONTEND_PID" "Frontend" 3200; then
    echo "❌ Failed to start frontend"
    echo "🛑 Stopping MCP server..."
    kill "$MCP_PID" 2>/dev/null
    exit 1
fi

# Save PIDs to .askg.pid
echo "💾 Saving process information..."
if [ "$NEO4J_INSTANCE" = "remote" ]; then
    echo "NEO4J_REMOTE" > .askg.pid
else
    echo "NEO4J_LOCAL" > .askg.pid
fi
echo "$MCP_PID" >> .askg.pid
echo "$FRONTEND_PID" >> .askg.pid

echo ""
echo "✅ All services started successfully!"
echo "📄 PIDs saved to .askg.pid"
echo ""
echo "🌐 Quick Access URLs:"
echo "   Frontend UI:     http://localhost:3200"
echo "   MCP Server API:  http://localhost:8200"
if [ "$NEO4J_INSTANCE" = "remote" ]; then
    echo "   Neo4j:          Remote instance"
else
    echo "   Neo4j Browser:  http://localhost:7474 (Neo4j Desktop)"
fi
echo ""
echo "🔧 Management Commands:"
echo "   ./stop.sh status  - Check service status"
echo "   ./stop.sh restart - Restart all services"
echo "   ./stop.sh stop    - Stop all services" 