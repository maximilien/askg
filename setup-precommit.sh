#!/bin/bash

# Setup pre-commit hooks for ASKG project

echo "🔧 Setting up pre-commit hooks..."

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
else
    echo "✅ pre-commit already installed"
fi

# Install the pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Run pre-commit on all files to ensure everything is set up
echo "🧹 Running pre-commit on all files..."
pre-commit run --all-files

echo "✅ Pre-commit setup complete!"
echo ""
echo "💡 Pre-commit hooks will now run automatically on every commit."
echo "   To run manually: pre-commit run --all-files"
echo "   To skip hooks: git commit --no-verify" 