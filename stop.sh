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
if [ "$NEO4J_TYPE" = "NEO4J_LOCAL" ]; then
    echo "Neo4j Desktop detected - please stop it manually if needed."
elif [ "$NEO4J_TYPE" = "NEO4J_REMOTE" ]; then
    echo "Remote Neo4j instance detected - connection will be closed automatically."
else
    echo "Unknown Neo4j type: $NEO4J_TYPE"
fi

echo "Stopping MCP server (PID $MCP_PID)..."
kill $MCP_PID 2>/dev/null && echo "MCP server stopped." || echo "MCP server not running."

echo "Stopping frontend (PID $FRONTEND_PID)..."
kill $FRONTEND_PID 2>/dev/null && echo "Frontend stopped." || echo "Frontend not running."

rm -f .askg.pid

echo "All services stopped and .askg.pid removed." 