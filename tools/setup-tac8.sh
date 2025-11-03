#!/bin/bash
# setup-tac8.sh - Quick setup for TAC-8 autonomous development system

set -e

echo "🤖 Setting up TAC-8..."
echo ""

# 1. Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 required"
    echo "   Install: sudo apt install python3 python3-pip"
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "❌ Git required"
    echo "   Install: sudo apt install git"
    exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
    echo "❌ GitHub CLI required"
    echo "   Install: https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
    echo "❌ Claude CLI required"
    echo "   Install: npm install -g @anthropic-ai/claude-cli"
    echo "   Or: pip install claude-cli"
    exit 1
fi

echo "✅ All prerequisites met"
echo ""

# 2. Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.9+ required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"
echo ""

# 3. Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --quiet toml requests python-dotenv rich blessed 2>/dev/null || {
    echo "⚠️  Some dependencies may already be installed"
}
echo "✅ Dependencies installed"
echo ""

# 4. Authenticate GitHub
echo "Checking GitHub authentication..."
if gh auth status >/dev/null 2>&1; then
    echo "✅ GitHub already authenticated"
else
    echo "⚠️  GitHub not authenticated"
    echo "   Run: gh auth login"
    exit 1
fi
echo ""

# 5. Create required directories
echo "Creating directories..."
mkdir -p trees logs exports
echo "✅ Directories created"
echo ""

# 6. Configure bashrc aliases
echo "Configuring bashrc aliases..."
BASHRC_LINE="source ~/Desktop/circuit-synth/tools/bashrc-aliases.sh"

if grep -qF "$BASHRC_LINE" ~/.bashrc; then
    echo "✅ Bashrc aliases already configured"
else
    echo "" >> ~/.bashrc
    echo "# TAC-8 Monitoring Tools" >> ~/.bashrc
    echo "$BASHRC_LINE" >> ~/.bashrc
    echo "✅ Bashrc aliases added to ~/.bashrc"
    echo "   Run: source ~/.bashrc"
fi
echo ""

# 7. Check for config file
if [ ! -f adws/config.toml ]; then
    echo "⚠️  adws/config.toml not found"
    echo "   Please create config.toml before starting coordinator"
    echo ""
    echo "   Example config.toml:"
    echo "   ---"
    cat <<'CONFIG_EXAMPLE'
[coordinator]
poll_interval = 30
max_concurrent_workers = 1
github_repo = "circuit-synth/circuit-synth"
github_label = "rpi-auto"

[worker]
provider = "anthropic"
model = "claude-sonnet-4"
timeout = 3600
max_retries = 3

[paths]
trees_dir = "trees"
logs_dir = "logs"
tasks_file = "tasks.md"
CONFIG_EXAMPLE
    echo "   ---"
    echo ""
else
    echo "✅ Config file exists: adws/config.toml"
fi
echo ""

# 8. Check for API credentials
echo "Checking API credentials..."
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ ANTHROPIC_API_KEY is set"
elif [ -f ~/.aws/credentials ]; then
    echo "✅ AWS credentials found (for Bedrock)"
elif command -v gcloud >/dev/null 2>&1; then
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
        echo "✅ GCP credentials found (for Vertex)"
    else
        echo "⚠️  No active GCP credentials"
    fi
else
    echo "⚠️  No API credentials detected"
    echo "   Set one of:"
    echo "   - export ANTHROPIC_API_KEY=your_key"
    echo "   - Configure ~/.aws/credentials (for Bedrock)"
    echo "   - Run: gcloud auth login (for Vertex)"
fi
echo ""

# 9. Make tools executable
echo "Making tools executable..."
chmod +x tools/*.py 2>/dev/null || true
echo "✅ Tools are executable"
echo ""

# 10. Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 TAC-8 setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo ""
echo "  1. Reload bashrc:"
echo "     source ~/.bashrc"
echo ""
echo "  2. Verify tools:"
echo "     tac-help"
echo ""
echo "  3. Configure coordinator (if needed):"
echo "     vim adws/config.toml"
echo ""
echo "  4. Set API credentials (if needed):"
echo "     export ANTHROPIC_API_KEY=your_key"
echo ""
echo "  5. Start coordinator:"
echo "     tac-start"
echo ""
echo "  6. Monitor activity:"
echo "     tac-monitor"
echo ""
echo "  7. Add label to issue to trigger work:"
echo "     tac-label-add 471"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Full documentation: docs/TAC8-SETUP.md"
echo ""
