#!/bin/bash

echo "🚀 Running FAST ASKG tests (skipping slow tests)..."
echo "=========================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first."
    exit 1
fi
echo "✅ uv is installed"

# Check if pytest is available
if ! uv run python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing pytest..."
    uv pip install pytest pytest-asyncio pytest-cov
fi

# Find test files
echo "📁 Found $(find tests -name "test_*.py" | wc -l | tr -d ' ') test file(s):"
find tests -name "test_*.py" -exec basename {} \;

echo "✅ Fast test mode enabled"
echo "🔍 Running: uv run pytest -v --tb=short --disable-warnings --durations=5 -m 'not slow' --maxfail=3"

# Run fast tests only (skip slow ones)
uv run pytest -v \
    --tb=short \
    --disable-warnings \
    --durations=5 \
    -m "not slow" \
    --maxfail=3 \
    tests/

exit_code=$?

echo "=========================="
if [ $exit_code -eq 0 ]; then
    echo "✅ Fast tests completed successfully!"
    echo ""
    echo "💡 To run all tests (including slow ones):"
    echo "   ./test.sh"
    echo ""
    echo "💡 To run specific test categories:"
    echo "   uv run pytest tests/test_config.py -v"
    echo "   uv run pytest tests/test_global_ids.py -v"
else
    echo "❌ Some fast tests failed!"
    echo ""
    echo "💡 Tips for fixing test failures:"
    echo "1. Check that all dependencies are installed: ./setup.sh"
    echo "2. Ensure Neo4j is running (if tests require it)"
    echo "3. Check test configuration and environment variables"
    echo "4. Run individual tests to isolate issues:"
    echo "   uv run pytest tests/test_specific_file.py -v"
fi

exit $exit_code 