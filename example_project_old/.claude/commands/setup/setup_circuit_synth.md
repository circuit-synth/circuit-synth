# Setup Circuit-Synth Environment

**Command**: `/setup_circuit_synth`

**Purpose**: Comprehensive setup of circuit-synth development environment including KiCad plugins, Claude Code integration, and validation testing.

## What This Command Does

### 🔍 Environment Assessment
- Detects platform (macOS/Linux/Windows) and adapts setup accordingly
- Checks Python version (requires 3.8+) and recommends uv if not installed
- Validates KiCad installation and version compatibility
- Verifies Claude CLI installation and authentication status
- Assesses Node.js/npm environment for Claude CLI functionality

### 📦 Circuit-Synth Installation
- Installs circuit-synth package with all dependencies via pip/uv
- Initializes JLCPCB component database and modm-devices integration
- Sets up symbol/footprint library path detection and validation
- Configures manufacturing integration (JLCPCB caching, etc.)

### 🔌 KiCad Plugin Setup
- Automatically installs KiCad plugins using cross-platform installer
- **PCB Editor Plugin**: "Circuit-Synth AI (Simple)" - board analysis and recommendations
- **Schematic Editor Plugin**: "Circuit-Synth BOM Plugin" - full Claude AI chat interface
- Tests plugin installation and Claude CLI integration
- Validates plugins appear correctly in KiCad interface

### 🤖 Claude Code Integration
- Copies circuit-synth specific agents to user's `.claude/agents/` directory
- Installs circuit-synth slash commands in `.claude/commands/`
- Sets up memory bank structure for project context persistence
- Configures circuit-synth specific Claude Code settings and workflows

### ✅ Comprehensive Validation
- Runs `examples/example_kicad_project.py` to verify core circuit generation
- Tests KiCad project opening and schematic rendering
- Validates both PCB and Schematic plugins launch correctly
- Confirms Claude AI integration works through KiCad plugins
- Tests component search and JLCPCB availability checking

## Usage

```bash
# In Claude Code, run:
/setup_circuit_synth

# Or with options:
/setup_circuit_synth --project-dir ~/circuits --skip-kicad-test
```

## Options
- `--project-dir <path>`: Specify target directory for circuit-synth projects
- `--skip-kicad-test`: Skip KiCad plugin testing (useful if KiCad not available)
- `--verbose`: Enable detailed logging for troubleshooting
- `--install-prerequisites`: Guide through prerequisite installations

## Expected Output

```
🚀 Circuit-Synth Environment Setup
================================

✅ Platform: macOS (Darwin)
✅ Python: 3.11.7 (uv available)
✅ KiCad: 9.0.1 detected at /Applications/KiCad/KiCad.app
✅ Claude CLI: 0.8.1 authenticated and ready

📦 Installing circuit-synth...
✅ circuit-synth installed successfully

🔌 Installing KiCad plugins...
✅ PCB Editor plugin: Circuit-Synth AI (Simple)
✅ Schematic Editor plugin: Circuit-Synth BOM Plugin
✅ Plugin installation completed

🤖 Setting up Claude Code integration...
✅ Agents copied to ~/.claude/agents/
✅ Commands installed in ~/.claude/commands/
✅ Memory bank initialized

✅ Running validation tests...
✅ Circuit generation: PASSED (ESP32 dev board created)
✅ KiCad integration: PASSED (project opens correctly)
✅ Plugin functionality: PASSED (Claude chat launches)
✅ Component search: PASSED (STM32 search working)

🎉 Setup Complete! You're ready to design circuits with AI assistance.

📖 Quick Start:
1. Run: uv run python examples/example_kicad_project.py
2. Open generated .kicad_pro file in KiCad
3. Try the plugins: Tools → Circuit-Synth AI
4. Chat with Claude about your circuits!
```

## Prerequisites

### Required
- **Python 3.8+** (uv recommended for dependency management)
- **KiCad 9.0+** (8.x may work but not officially supported)
- **Claude CLI** (install: `npm install -g @anthropic-ai/claude-cli`)

### Recommended
- **uv** for Python package management
- **Git** for repository cloning and updates
- **Node.js 18+** for Claude CLI functionality

## Troubleshooting

### KiCad Not Found
```bash
# macOS: Install via Homebrew
brew install kicad

# Or download from: https://www.kicad.org/download/
```

### Claude CLI Issues
```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-cli

# Verify installation
claude --version

# Authenticate (follow prompts)
claude auth login
```

### Python Environment Issues
```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip
pip install circuit-synth
```

## Success Criteria

After running this command, you should be able to:
1. ✅ Generate circuits using circuit-synth Python syntax
2. ✅ Open generated KiCad projects without errors
3. ✅ Access AI assistance through KiCad plugins
4. ✅ Search for components with JLCPCB availability
5. ✅ Chat with Claude about circuit design decisions

This command transforms a blank system into a fully functional circuit-synth development environment in minutes.