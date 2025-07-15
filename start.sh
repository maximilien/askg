#!/bin/bash

# Check if Neo4j is running (assuming Neo4j Desktop is already started)
echo "Checking Neo4j connection..."
if ! python3 -c "
import sys
sys.path.append('src')
from neo4j_integration import Neo4jManager
try:
    with Neo4jManager(instance='local') as neo4j:
        with neo4j.driver.session() as session:
            session.run('RETURN 1')
    print('✅ Neo4j connection successful')
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    print('Please ensure Neo4j Desktop is running and accessible on localhost:7687')
    sys.exit(1)
" 2>/dev/null; then
    echo "❌ Neo4j is not accessible."
    echo "Please start Neo4j Desktop and ensure it's running on localhost:7687"
    echo "Default credentials: neo4j/mcpservers"
    exit 1
fi

# Start MCP server (Python backend)
echo "Starting MCP server..."
python3 mcp/server.py --port 8080 &
MCP_PID=$!
echo "MCP server started with PID $MCP_PID"

# Build and start frontend (Node/TypeScript)
echo "Building frontend..."
cd frontend
npm run build
echo "Starting frontend..."
npm start &
FRONTEND_PID=$!
cd ..
echo "Frontend started with PID $FRONTEND_PID"

# Save PIDs to .askg.pid (no Docker container ID needed)
echo "NEO4J_DESKTOP" > .askg.pid
echo "$MCP_PID" >> .askg.pid
echo "$FRONTEND_PID" >> .askg.pid

echo "All services started. PIDs saved to .askg.pid."
echo
# Print quick access URLs
echo "Access the Frontend UI at:   http://localhost:3000"
echo "Access the MCP server API at: http://localhost:8080"
echo "Access Neo4j Browser at:      http://localhost:7474 (Neo4j Desktop)" 