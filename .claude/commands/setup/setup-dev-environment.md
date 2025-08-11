# /setup-dev-environment

Set up a complete development environment for circuit-synth contribution and development.

## Usage
```
/setup-dev-environment [--full] [--kicad-check]
```

## Description
Configures a comprehensive development environment for circuit-synth, including all dependencies, development tools, testing frameworks, and external integrations required for effective contribution.

## Setup Components

### 1. Core Development Environment
```bash
# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup repository
git clone https://github.com/circuitsynth/circuit-synth.git
cd circuit-synth

# Install development dependencies
uv sync
uv pip install -e ".[dev]"
```

### 2. KiCad Integration Setup
```bash
# Verify KiCad CLI installation
kicad-cli version

# Setup symbol library paths
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5

# Configure KiCad library environment variables
export KICAD_SYMBOL_DIR=/usr/share/kicad/symbols
export KICAD_FOOTPRINT_DIR=/usr/share/kicad/footprints
```

### 3. Development Tools Configuration
```bash
# Code formatting and linting tools
uv add black isort flake8 mypy --group dev

# Testing framework and coverage
uv add pytest pytest-cov pytest-benchmark --group dev

# Documentation tools
uv add sphinx sphinx-rtd-theme --group dev

# Git hooks and pre-commit setup
uv add pre-commit --group dev
pre-commit install
```

### 4. External API Integration (Optional)
```bash
# DigiKey API configuration
python -m circuit_synth.manufacturing.digikey.config_manager

# JLCPCB integration test
python -c "from circuit_synth.manufacturing.jlcpcb import fast_search; print('JLCPCB OK')"
```

## Validation Steps

### Environment Validation
```bash
# Test core functionality
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth imported successfully')"

# Validate KiCad integration
uv run python -c "from circuit_synth.kicad import *; print('✅ KiCad integration ready')"

# Test manufacturing integrations
uv run python -c "from circuit_synth.manufacturing import *; print('✅ Manufacturing integrations loaded')"
```

### Development Workflow Test
```bash
# Run test suite
uv run pytest --cov=circuit_synth

# Test code formatting
black --check src/ tests/
isort --check-only src/ tests/

# Validate type checking
mypy src/ --ignore-missing-imports
```

## Development Environment Structure
```
circuit-synth/
├── src/circuit_synth/          # Main package source
├── tests/                      # Test suite
├── docs/                       # Documentation source
├── tools/                      # Development and maintenance tools
├── examples/                   # Usage examples
├── pyproject.toml             # Package configuration
├── uv.lock                    # Dependency lock file
└── .pre-commit-config.yaml    # Git hooks configuration
```

## IDE Configuration

### VS Code Setup
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true
}
```

### PyCharm Setup
- Configure Python interpreter to use `.venv/bin/python`
- Enable pytest as test runner
- Configure code style to use Black formatter
- Enable type checking with mypy

## Common Issues & Solutions

### KiCad Not Found
```bash
# macOS with Homebrew
brew install kicad

# Ubuntu/Debian
sudo apt install kicad kicad-libraries

# Verify installation
kicad-cli version
```

### Import Errors
```bash
# Reinstall in development mode
uv pip install -e ".[dev]"

# Clear Python cache
find . -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### Test Failures
```bash
# Update test data and references
git pull origin main
uv sync

# Clear test caches
rm -rf .pytest_cache/
rm -rf tests/__pycache__/
```

## Next Steps
After setup completion:
1. **Read Contributing Guidelines**: Review `docs/CONTRIBUTING.md`
2. **Explore Examples**: Run examples in `examples/` directory  
3. **Run Test Suite**: Execute `uv run pytest` to validate setup
4. **Start Development**: Create feature branch and begin contributing

This command ensures a complete, validated development environment for effective circuit-synth contribution.