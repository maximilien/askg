#!/bin/bash

# Test runner for ASKG (Agent-Server Knowledge Graph)
# Runs all tests using uv run pytest with proper configuration.

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

# Function to check if pytest is available
check_pytest() {
    uv run pytest --version >/dev/null 2>&1
}

# Function to install pytest if needed
install_pytest() {
    print_status "Installing pytest and pytest-asyncio"
    if uv pip install pytest pytest-asyncio; then
        print_success "pytest and pytest-asyncio installed"
        return 0
    else
        print_error "Failed to install pytest and pytest-asyncio"
        return 1
    fi
}

# Function to check for pytest-cov
check_pytest_cov() {
    uv run python -c "import pytest_cov" >/dev/null 2>&1
}

# Function to install pytest-cov if needed
install_pytest_cov() {
    print_status "Installing pytest-cov for coverage reporting"
    if uv pip install pytest-cov; then
        print_success "pytest-cov installed"
        return 0
    else
        print_warning "Failed to install pytest-cov, continuing without coverage reporting"
        return 1
    fi
}

echo "🧪 Running ASKG tests..."
echo "=========================="

# Check if uv is installed
if ! command_exists uv; then
    print_error "uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

print_success "uv is installed"

# Check if tests directory exists
if [ ! -d "tests" ]; then
    print_error "tests directory not found"
    echo "Please ensure you have test files in the tests/ directory"
    exit 1
fi

# Check if there are any test files
test_files=$(find tests -name "test_*.py" 2>/dev/null | wc -l)
if [ "$test_files" -eq 0 ]; then
    print_warning "No test files found in tests/ directory"
    echo "Available files in tests/:"
    ls -la tests/ || echo "No files found"
    exit 1
fi

echo "📁 Found $test_files test file(s):"
find tests -name "test_*.py" -exec basename {} \;
echo ""

# Check if pytest is available
if ! check_pytest; then
    print_warning "pytest not found. Installing pytest..."
    if ! install_pytest; then
        exit 1
    fi
fi

# Set up environment variables for testing
export PYTHONPATH=".:src"
export TESTING="1"

# Build pytest command with options
pytest_args=(
    "uv" "run" "pytest"
    "-v"               # Verbose output
    "--tb=short"       # Short traceback format
    "--color=yes"      # Colored output
    "--durations=10"   # Show 10 slowest tests
)

# Add coverage if available
if check_pytest_cov; then
    pytest_args+=("--cov=src" "--cov-report=term-missing")
    print_success "Coverage reporting enabled"
else
    print_status "Installing pytest-cov for better test reporting..."
    install_pytest_cov
    if check_pytest_cov; then
        pytest_args+=("--cov=src" "--cov-report=term-missing")
        print_success "Coverage reporting enabled"
    fi
fi

echo "🔍 Running: ${pytest_args[*]}"
echo ""

# Run the tests
if "${pytest_args[@]}"; then
    echo ""
    echo "=========================="
    print_success "All tests passed!"
    echo ""
    echo "🎉 Test run completed successfully!"
    exit 0
else
    exit_code=$?
    echo ""
    echo "=========================="
    print_error "Some tests failed!"
    echo "Exit code: $exit_code"
    echo ""
    echo "💡 Tips for fixing test failures:"
    echo "1. Check that all dependencies are installed: ./setup.sh"
    echo "2. Ensure Neo4j is running (if tests require it)"
    echo "3. Check test configuration and environment variables"
    echo "4. Run individual tests to isolate issues:"
    echo "   uv run pytest tests/test_specific_file.py -v"
    exit $exit_code
fi 