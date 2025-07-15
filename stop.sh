#!/bin/bash

if [ ! -f .askg.pid ]; then
  echo ".askg.pid not found. Are the servers running?"
  exit 1
fi

# Read PIDs from file (more compatible than readarray)
NEO4J_TYPE=$(sed -n '1p' .askg.pid)
MCP_PID=$(sed -n '2p' .askg.pid)
FRONTEND_PID=$(sed -n '3p' .askg.pid)

# Handle Neo4j based on type
if [ "$NEO4J_TYPE" = "NEO4J_DESKTOP" ]; then
    echo "Neo4j Desktop detected - please stop it manually if needed."
else
    echo "Stopping Neo4j container (ID $NEO4J_TYPE)..."
    docker stop askg-neo4j 2>/dev/null && echo "Neo4j container stopped." || echo "Neo4j container not running."
    docker rm askg-neo4j 2>/dev/null && echo "Neo4j container removed." || echo "Neo4j container not found."
fi

echo "Stopping MCP server (PID $MCP_PID)..."
kill $MCP_PID 2>/dev/null && echo "MCP server stopped." || echo "MCP server not running."

echo "Stopping frontend (PID $FRONTEND_PID)..."
kill $FRONTEND_PID 2>/dev/null && echo "Frontend stopped." || echo "Frontend not running."

rm -f .askg.pid

echo "All services stopped and .askg.pid removed." 