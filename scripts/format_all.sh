#\!/bin/bash
# Format all code in the repository

set -e

echo "🔧 Formatting all code..."

# Format Python
echo "🐍 Formatting Python code..."
uv run black src/
uv run isort src/

# Format Rust  
echo "🦀 Formatting Rust code..."
for dir in rust_modules/*/; do
    if [ -f "$dir/Cargo.toml" ]; then
        module_name=$(basename "$dir")
        echo "  Formatting $module_name..."
        (cd "$dir" && cargo fmt)
    fi
done

echo "✅ All code formatted\!"
echo ""
echo "📋 Next steps:"
echo "• git add -A"
echo "• git commit -m 'Apply code formatting'"
echo "• git push"
