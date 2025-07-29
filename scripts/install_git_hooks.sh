#\!/bin/bash
# Install git hooks for automatic formatting

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "🔧 Installing git hooks for automatic formatting..."

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'HOOK_EOF'
#\!/bin/bash
# Auto-format code before commit

echo "🔧 Auto-formatting code before commit..."

# Check if we're in the right directory
if [ \! -f "pyproject.toml" ]; then
    echo "❌ Not in circuit-synth root directory"
    exit 1
fi

# Format Python code
echo "🐍 Formatting Python..."
if command -v uv &> /dev/null; then
    uv run black src/ || echo "⚠️  Black formatting failed"
    uv run isort src/ || echo "⚠️  isort failed"
else
    echo "⚠️  uv not found, skipping Python formatting"
fi

# Format Rust code  
echo "🦀 Formatting Rust..."
for dir in rust_modules/*/; do
    if [ -f "$dir/Cargo.toml" ]; then
        echo "  Formatting $dir"
        (cd "$dir" && cargo fmt) || echo "⚠️  Rust formatting failed for $dir"
    fi
done

# Stage the formatted files
git add -u

echo "✅ Code formatted and staged\!"
HOOK_EOF

# Make hook executable
chmod +x "$HOOKS_DIR/pre-commit"

# Create post-commit hook to verify formatting
cat > "$HOOKS_DIR/post-commit" << 'HOOK_EOF'
#\!/bin/bash
# Verify formatting after commit

echo "🔍 Verifying code formatting..."

# Quick format check (don't change files)
PYTHON_CHECK=0
RUST_CHECK=0

# Check Python formatting
if command -v uv &> /dev/null; then
    if \! uv run black --check src/ >/dev/null 2>&1; then
        PYTHON_CHECK=1
    fi
    if \! uv run isort --check-only src/ >/dev/null 2>&1; then
        PYTHON_CHECK=1
    fi
fi

# Check Rust formatting
for dir in rust_modules/*/; do
    if [ -f "$dir/Cargo.toml" ]; then
        if \! (cd "$dir" && cargo fmt --check >/dev/null 2>&1); then
            RUST_CHECK=1
        fi
    fi
done

if [ $PYTHON_CHECK -eq 1 ] || [ $RUST_CHECK -eq 1 ]; then
    echo "⚠️  Some files may still need formatting"
else
    echo "✅ All code properly formatted\!"
fi
HOOK_EOF

chmod +x "$HOOKS_DIR/post-commit"

echo "✅ Git hooks installed successfully\!"
echo ""
echo "📋 Installed hooks:"
echo "• pre-commit: Auto-formats code before commits"
echo "• post-commit: Verifies formatting after commits"
echo ""
echo "🚀 To disable hooks temporarily:"
echo "  git commit --no-verify"
