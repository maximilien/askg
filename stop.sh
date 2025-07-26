#!/bin/bash

# Function to show usage
show_usage() {
    echo "Usage: $0 [status|restart|stop]"
    echo "  status  - Show status of all services"
    echo "  restart - Restart all services"
    echo "  stop    - Stop all services (default)"
    echo ""
    echo "Examples:"
    echo "  $0 status    # Show current status"
    echo "  $0 restart   # Restart all services"
    echo "  $0 stop      # Stop all services"
}

# Function to check if a process is running
is_process_running() {
    local pid=$1
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check port status
check_port() {
    local port=$1
    local service_name=$2
    if lsof -i :$port >/dev/null 2>&1; then
        echo "✅ $service_name is running on port $port"
        return 0
    else
        echo "❌ $service_name is not running on port $port"
        return 1
    fi
}

# Function to show status
show_status() {
    echo "🔍 Checking service status..."
    echo ""
    
    # Check if .askg.pid exists
    if [ ! -f .askg.pid ]; then
        echo "📄 No .askg.pid file found - services may not be running"
        echo ""
        echo "Checking for orphaned processes..."
        
        # Check for processes on known ports
        check_port 3200 "Frontend"
        check_port 8200 "MCP Server"
        
        # Check for Neo4j
        if lsof -i :7474 >/dev/null 2>&1; then
            echo "✅ Neo4j Browser is accessible on port 7474"
        else
            echo "❌ Neo4j Browser is not accessible on port 7474"
        fi
        
        if lsof -i :7687 >/dev/null 2>&1; then
            echo "✅ Neo4j Bolt is accessible on port 7687"
        else
            echo "❌ Neo4j Bolt is not accessible on port 7687"
        fi
        
        return
    fi
    
    # Read PIDs from file
    NEO4J_TYPE=$(sed -n '1p' .askg.pid 2>/dev/null)
    MCP_PID=$(sed -n '2p' .askg.pid 2>/dev/null)
    FRONTEND_PID=$(sed -n '3p' .askg.pid 2>/dev/null)
    
    echo "📄 PID file found: .askg.pid"
    echo "🏗️  Neo4j Type: $NEO4J_TYPE"
    echo "🔧 MCP Server PID: $MCP_PID"
    echo "🌐 Frontend PID: $FRONTEND_PID"
    echo ""
    
    # Check MCP server
    if is_process_running "$MCP_PID"; then
        echo "✅ MCP server is running (PID: $MCP_PID)"
    else
        echo "❌ MCP server is not running (PID: $MCP_PID)"
    fi
    
    # Check frontend
    if is_process_running "$FRONTEND_PID"; then
        echo "✅ Frontend is running (PID: $FRONTEND_PID)"
    else
        echo "❌ Frontend is not running (PID: $FRONTEND_PID)"
    fi
    
    echo ""
    echo "🔍 Checking port availability..."
    
    # Check ports
    check_port 3200 "Frontend"
    check_port 8200 "MCP Server"
    
    # Check Neo4j based on type
    if [ "$NEO4J_TYPE" = "NEO4J_LOCAL" ]; then
        echo "🏠 Using local Neo4j Desktop"
        if lsof -i :7474 >/dev/null 2>&1; then
            echo "✅ Neo4j Browser is accessible on port 7474"
        else
            echo "❌ Neo4j Browser is not accessible on port 7474"
        fi
        
        if lsof -i :7687 >/dev/null 2>&1; then
            echo "✅ Neo4j Bolt is accessible on port 7687"
        else
            echo "❌ Neo4j Bolt is not accessible on port 7687"
        fi
    elif [ "$NEO4J_TYPE" = "NEO4J_REMOTE" ]; then
        echo "📡 Using remote Neo4j instance"
    else
        echo "❓ Unknown Neo4j type: $NEO4J_TYPE"
    fi
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping all services..."
    
    # Check if .askg.pid exists
    if [ ! -f .askg.pid ]; then
        echo "📄 No .askg.pid file found. Checking for orphaned processes..."
        
        # Kill any processes on port 3200 (frontend)
        echo "🔍 Looking for frontend processes on port 3200..."
        FRONTEND_PIDS=$(lsof -ti :3200 2>/dev/null)
        if [ -n "$FRONTEND_PIDS" ]; then
            echo "🛑 Killing frontend processes: $FRONTEND_PIDS"
            echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null
            echo "✅ Frontend processes killed"
        else
            echo "ℹ️  No frontend processes found on port 3200"
        fi
        
        # Kill any processes on port 8200 (MCP server)
        echo "🔍 Looking for MCP server processes on port 8200..."
        MCP_PIDS=$(lsof -ti :8200 2>/dev/null)
        if [ -n "$MCP_PIDS" ]; then
            echo "🛑 Killing MCP server processes: $MCP_PIDS"
            echo "$MCP_PIDS" | xargs kill -9 2>/dev/null
            echo "✅ MCP server processes killed"
        else
            echo "ℹ️  No MCP server processes found on port 8200"
        fi
        
        echo "✅ All orphaned processes cleaned up"
        return
    fi
    
    # Read PIDs from file
    NEO4J_TYPE=$(sed -n '1p' .askg.pid)
    MCP_PID=$(sed -n '2p' .askg.pid)
    FRONTEND_PID=$(sed -n '3p' .askg.pid)
    
    # Handle Neo4j based on type
    if [ "$NEO4J_TYPE" = "NEO4J_LOCAL" ]; then
        echo "🏠 Neo4j Desktop detected - please stop it manually if needed."
    elif [ "$NEO4J_TYPE" = "NEO4J_REMOTE" ]; then
        echo "📡 Remote Neo4j instance detected - connection will be closed automatically."
    else
        echo "❓ Unknown Neo4j type: $NEO4J_TYPE"
    fi
    
    # Stop MCP server
    echo "🛑 Stopping MCP server (PID $MCP_PID)..."
    if is_process_running "$MCP_PID"; then
        kill "$MCP_PID" 2>/dev/null && echo "✅ MCP server stopped." || echo "❌ Failed to stop MCP server."
    else
        echo "ℹ️  MCP server not running."
    fi
    
    # Stop frontend
    echo "🛑 Stopping frontend (PID $FRONTEND_PID)..."
    if is_process_running "$FRONTEND_PID"; then
        kill "$FRONTEND_PID" 2>/dev/null && echo "✅ Frontend stopped." || echo "❌ Failed to stop frontend."
    else
        echo "ℹ️  Frontend not running."
    fi
    
    # Additional cleanup for frontend on port 3200
    echo "🔍 Additional cleanup for frontend on port 3200..."
    FRONTEND_PIDS=$(lsof -ti :3200 2>/dev/null)
    if [ -n "$FRONTEND_PIDS" ]; then
        echo "🛑 Killing remaining frontend processes on port 3200: $FRONTEND_PIDS"
        echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null
        echo "✅ Remaining frontend processes killed"
    fi
    
    # Additional cleanup for MCP server on port 8200
    echo "🔍 Additional cleanup for MCP server on port 8200..."
    MCP_PIDS=$(lsof -ti :8200 2>/dev/null)
    if [ -n "$MCP_PIDS" ]; then
        echo "🛑 Killing remaining MCP server processes on port 8200: $MCP_PIDS"
        echo "$MCP_PIDS" | xargs kill -9 2>/dev/null
        echo "✅ Remaining MCP server processes killed"
    fi
    
    # Remove PID file
    rm -f .askg.pid
    echo "🗑️  .askg.pid file removed."
    
    echo "✅ All services stopped and cleaned up."
}

# Function to restart services
restart_services() {
    echo "🔄 Restarting all services..."
    
    # Stop services first
    stop_services
    
    # Wait a moment
    sleep 2
    
    # Start services
    echo "🚀 Starting services..."
    ./start.sh
}

# Main script logic
case "${1:-stop}" in
    "status")
        show_status
        ;;
    "restart")
        restart_services
        ;;
    "stop")
        stop_services
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_usage
        exit 1
        ;;
esac 