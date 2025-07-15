#!/bin/bash

# Setup script for ASKG (Agent-Server Knowledge Graph)
# Automates the setup process for the project.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run command with error handling
run_command() {
    local description="$1"
    local command="$2"
    
    print_status "$description"
    if eval "$command"; then
        print_success "$description completed successfully"
        return 0
    else
        print_error "$description failed"
        return 1
    fi
}

echo "🚀 Setting up ASKG (Agent-Server Knowledge Graph)"
echo "=================================================="

# Check if uv is installed
if ! command_exists uv; then
    print_error "uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

print_success "uv is installed"

# Create necessary directories
print_status "Creating necessary directories"
mkdir -p data/registries data/snapshots logs
print_success "Created directories: data/, data/registries/, data/snapshots/, logs/"

# Install dependencies
if ! run_command "Installing dependencies" "uv pip install -r requirements.txt"; then
    print_error "Failed to install dependencies"
    exit 1
fi

# Create config file from example if it doesn't exist
if [ ! -f ".config.yaml" ]; then
    if [ -f ".config.example.yaml" ]; then
        print_status "Creating .config.yaml from .config.example.yaml"
        cp .config.example.yaml .config.yaml
        print_success ".config.yaml created"
        print_warning "Please edit .config.yaml to set your GitHub token and other configuration"
    else
        print_error ".config.example.yaml not found"
        exit 1
    fi
else
    print_success ".config.yaml already exists"
fi

echo ""
echo "📋 Next steps:"
echo "1. Edit .config.yaml to set your GitHub token and Neo4j credentials"
echo "2. Start Neo4j database (if using Docker):"
echo "   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/mcpservers neo4j:latest"
echo "3. Run tests: ./test.sh"
echo "4. Start the application: python src/main.py"
echo ""
print_success "Setup completed successfully!" 