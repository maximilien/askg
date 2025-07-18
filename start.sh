#!/bin/bash

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

# Determine which Neo4j instance to use
echo "Checking Neo4j configuration..."
NEO4J_INSTANCE=$(check_remote_config)

if [ "$NEO4J_INSTANCE" = "remote" ]; then
    echo "📡 Found remote Neo4j configuration in .config.yaml"
    echo "🔗 Attempting to connect to remote Neo4j instance..."
else
    echo "🏠 Using local Neo4j Desktop instance"
fi

# Check Neo4j connection
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
echo "Starting MCP server..."
python3 mcp/server.py --port 8200 --instance $NEO4J_INSTANCE &
MCP_PID=$!
echo "MCP server started with PID $MCP_PID (using $NEO4J_INSTANCE instance)"

# Build and start frontend (Node/TypeScript)
echo "Building frontend..."
cd frontend
npm run build
echo "Starting frontend..."
PORT=3200 npm start &
FRONTEND_PID=$!
cd ..
echo "Frontend started with PID $FRONTEND_PID"

# Save PIDs to .askg.pid
if [ "$NEO4J_INSTANCE" = "remote" ]; then
    echo "NEO4J_REMOTE" > .askg.pid
else
    echo "NEO4J_LOCAL" > .askg.pid
fi
echo "$MCP_PID" >> .askg.pid
echo "$FRONTEND_PID" >> .askg.pid

echo "All services started. PIDs saved to .askg.pid."
echo
# Print quick access URLs
echo "Access the Frontend UI at:   http://localhost:3200"
echo "Access the MCP server API at: http://localhost:8200"
if [ "$NEO4J_INSTANCE" = "remote" ]; then
    echo "Connected to remote Neo4j instance"
else
    echo "Access Neo4j Browser at:      http://localhost:7474 (Neo4j Desktop)"
fi 