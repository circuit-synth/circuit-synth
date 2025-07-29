#\!/bin/bash
# Setup automatic code formatting

set -e

echo "🔧 Setting up automatic code formatting..."

# Install pre-commit if not already installed
if \! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    uv add --dev pre-commit
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
uv run pre-commit install

# Run pre-commit on all files to ensure current state is clean
echo "Running pre-commit on all files..."
uv run pre-commit run --all-files

echo "✅ Formatting automation setup complete\!"
echo ""
echo "📋 What this does:"
echo "• Automatically formats Python code with Black before commits"
echo "• Sorts Python imports with isort"  
echo "• Formats Rust code with rustfmt"
echo "• Fixes trailing whitespace and line endings"
echo ""
echo "🚀 To format code manually:"
echo "• Python: uv run black src/"
echo "• Rust: cargo fmt --all (in each rust_modules subdirectory)"
echo "• All: uv run pre-commit run --all-files"
