# Development Setup Guide

Complete setup guide for circuit-synth contributors, covering everything from basic installation to advanced development workflows.

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites

**Required:**
- **Python 3.9+** (3.11+ recommended)
- **KiCad 8.0+** (required for symbol/footprint libraries)
- **Git** (for version control)

**Optional but Recommended:**
- **uv** (fastest Python package manager)
- **Rust** (for performance modules)
- **Claude Code** (best development experience)

### 2. Basic Installation

```bash
# Clone the repository
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Install with uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# OR install with pip (if uv unavailable)
pip install -e ".[dev]"

# Verify installation
uv run python example_project/circuit-synth/main.py
```

### 3. Verify Everything Works

```bash
# Test basic functionality
uv run python -c "import circuit_synth; print('✅ Circuit-synth imports successfully')"

# Test KiCad integration  
uv run python example_project/circuit-synth/main.py
# Should generate ESP32_C6_Dev_Board/ directory with KiCad files

# Run basic tests
./scripts/run_all_tests.sh --python-only
```

## 🤖 AI Agent Setup (Highly Recommended)

### Claude Code Integration

**Why Claude Code?** We've built specialized agents that understand circuit-synth deeply and can guide you through development tasks.

```bash
# 1. Install Claude Code (if not already installed)
# Visit: https://claude.ai/code

# 2. Register our specialized agents
uv run register-agents

# 3. Verify agent registration
# Claude Code will now have access to:
# - circuit-architect: Circuit design coordination
# - power-expert: Power supply specialist  
# - signal-integrity: High-speed design expert
# - component-guru: Manufacturing and sourcing
# - contributor: Development assistance (perfect for you!)
```

### GitHub MCP Server (Ultimate Workflow)

For seamless GitHub integration with Claude Code:

```bash
# Setup GitHub MCP server (enables Claude Code to manage issues/PRs)
# Follow: https://github.com/anthropics/mcp-servers/tree/main/src/github

# Benefits:
# ✅ Create and manage GitHub issues directly from Claude Code
# ✅ Review pull requests with AI assistance
# ✅ Check CI status and test results
# ✅ Navigate project history and structure
```

## 🦀 Rust Development Setup (Optional but High-Impact)

Rust modules provide significant performance improvements and are **perfect for high-impact contributions**.

### Install Rust Toolchain

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Install Python-Rust binding tools
pip install maturin

# Verify Rust installation
rustc --version
cargo --version
```

### Compile Rust Modules

```bash
# Option 1: Compile all modules (comprehensive)
./scripts/rebuild_all_rust.sh

# Option 2: Compile specific modules (faster)
cd rust_modules/rust_kicad_integration
maturin develop --release
cd ../..

# Option 3: Use our automated script
./scripts/enable_rust_acceleration.py
```

### Verify Rust Integration

```bash
# Test with Rust acceleration
uv run python example_project/circuit-synth/main.py

# Look for these log messages:
# ✅ "🦀 RUST_INTEGRATION: Using compiled Rust modules"
# ❌ "🐍 RUST_INTEGRATION: Falling back to Python implementation"
```

## 🧪 Testing Infrastructure

### Test Categories

```bash
# 1. Quick verification (30 seconds)
./scripts/run_all_tests.sh --python-only

# 2. Full test suite including Rust (2-3 minutes)
./scripts/run_all_tests.sh

# 3. Rust-specific tests (1 minute)
./scripts/test_rust_modules.sh

# 4. Specific test files
uv run pytest tests/unit/test_core_circuit.py -v
uv run pytest tests/rust_integration/ -v
```

### Test-Driven Development Setup

```bash
# Install test dependencies (included in [dev] extras)
uv sync

# Install pre-commit hooks for automatic testing
pre-commit install

# Run tests on every commit
git config core.hooksPath .githooks/
```

## 🛠️ Development Tools

### Code Quality Tools

```bash
# Format code (automatic with pre-commit)
black src/
isort src/

# Lint code
flake8 src/
mypy src/

# Check for security issues
bandit -r src/
```

### Performance Profiling

```bash
# Profile circuit generation
uv run python -m cProfile -o profile_output.prof example_project/circuit-synth/main.py

# Analyze performance bottlenecks
uv run python -c "
import pstats
p = pstats.Stats('profile_output.prof')
p.sort_stats('cumulative').print_stats(20)
"
```

### Development Commands

Our specialized development commands (available through Claude Code):

```bash
# Circuit-synth specific commands
/dev-review-branch          # Review your branch before PR
/dev-review-repo           # Review entire repository for issues
/find-symbol STM32         # Search KiCad symbols  
/find-footprint LQFP       # Search KiCad footprints
/jlc-search "ESP32"        # Search JLCPCB for components

# STM32 integration example
/stm32-search "3 spi 2 uart jlcpcb"  # Find STM32s with specific peripherals
```

## 📁 Development Environment Structure

### Recommended Directory Layout

```bash
~/Development/
├── circuit-synth/          # Main repository
│   ├── src/               # Python source code
│   ├── rust_modules/      # Rust performance modules
│   ├── Contributors/      # This documentation
│   └── example_project/   # Test/example projects
├── test-projects/         # Your test circuits
└── kicad-libraries/       # Custom KiCad libraries (optional)
```

### IDE Configuration

**VS Code (Recommended):**
```json
// .vscode/settings.json
{
    "python.defaultInterpreter": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "rust-analyzer.enable": true,
    "files.associations": {
        "*.kicad_sch": "lisp",
        "*.kicad_pcb": "lisp"
    }
}
```

**Extensions:**
- Python (Microsoft)
- Rust Analyzer
- GitLens
- Claude Code (if using Claude Code)

## 🔧 Advanced Development Setup

### Custom KiCad Libraries

```bash
# Add custom symbol libraries (optional)
export KICAD_SYMBOL_DIR="$HOME/kicad-libraries/symbols"
export KICAD_FOOTPRINT_DIR="$HOME/kicad-libraries/footprints"

# Test custom library integration
uv run python -c "
from circuit_synth.core.symbol_cache import get_available_libraries
print(get_available_libraries())
"
```

### Docker Development Environment

```bash
# Build development container
docker build -t circuit-synth-dev .

# Run with mounted source
docker run -it -v $(pwd):/workspace circuit-synth-dev bash

# Test inside container
cd /workspace
uv run python example_project/circuit-synth/main.py
```

### Performance Monitoring

```bash
# Enable performance logging
export CIRCUIT_SYNTH_LOG_LEVEL=DEBUG
export CIRCUIT_SYNTH_PROFILE=true

# Run with detailed performance data
uv run python example_project/circuit-synth/main.py

# Analyze logs
tail -f logs/performance.log
```

## 🎯 Contribution-Specific Setup

### For Rust Integration Contributors

```bash
# Install additional Rust tools
cargo install cargo-watch     # Auto-rebuild on changes
cargo install cargo-flamegraph # Performance profiling
cargo install cargo-bloat     # Binary size analysis

# Development workflow
cd rust_modules/rust_kicad_integration
cargo watch -x "test --lib --no-default-features"
```

### For Python Contributors

```bash
# Install additional Python tools
pip install pytest-cov       # Coverage reporting
pip install pytest-benchmark # Performance testing
pip install memory-profiler  # Memory usage analysis

# Development workflow
pytest --cov=circuit_synth tests/ --cov-report=html
```

### For Documentation Contributors

```bash
# Install documentation tools
pip install sphinx sphinx-rtd-theme
pip install myst-parser       # Markdown support

# Build documentation locally
cd docs/
make html
open _build/html/index.html
```

## 🚨 Troubleshooting

### Common Issues

**KiCad libraries not found:**
```bash
# Verify KiCad installation
kicad-cli version

# Check library paths
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5
```

**Rust compilation errors:**
```bash
# Clean and rebuild
cd rust_modules/rust_kicad_integration
cargo clean
maturin develop --release
```

**Python import errors:**
```bash
# Reinstall in development mode
uv pip install -e ".[dev]" --force-reinstall
```

**Test failures:**
```bash
# Run tests with verbose output
./scripts/run_all_tests.sh --verbose --fail-fast

# Check specific test categories
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
```

### Getting Help

1. **Check existing issues**: Search GitHub issues for similar problems
2. **Use Claude Code agents**: Our contributor agent can help diagnose problems
3. **Ask in discussions**: GitHub Discussions for general questions
4. **Review logs**: Check `logs/` directory for detailed error information

---

**Ready to contribute?** With this setup, you have everything needed to make meaningful contributions to circuit-synth! 🚀