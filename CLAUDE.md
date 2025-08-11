# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when developing and contributing to the circuit-synth project.

## 🚀 Project Overview

Circuit-synth is an open-source Python library for professional circuit design with AI-powered component intelligence and manufacturing integration. This repository focuses on **development and contribution** to the library itself.

## ⚡ Development Commands

### Essential Development Workflow
```bash
# Setup complete development environment
/setup-dev-environment --full --kicad-check

# Run comprehensive test suite
/dev-run-tests

# Update docs and commit changes
/dev-update-and-commit "description of changes"
```

### Git & GitHub Operations
```bash
# Create PR (Claude excels at git operations)
git add . && git commit -m "your message" && git push && gh pr create

# View recent commits and changes
git log --oneline -10
git diff HEAD~1

# Check GitHub issues and PRs
gh issue list
gh pr list
```

### Installation and Development Setup

**Primary method (recommended) - using uv:**
```bash
# Install the project in development mode
uv pip install -e ".[dev]"

# Install dependencies
uv sync

# Register Claude Code agents for AI-assisted development
uv run register-agents
```

**Alternative method - using pip:**
```bash
# If uv is not available
pip install -e ".[dev]"

# Register agents (after installation)
register-agents
```

## 🧪 Testing & Quality Assurance

**IMPORTANT: Always run linting and tests after making changes**

**🚨 PRE-RELEASE TESTING (CRITICAL for PyPI):**
```bash
# Comprehensive regression test - MUST run before ANY release
./tools/testing/run_full_regression_tests.py

# This performs COMPLETE environment reconstruction:
# - Reinstalls Python environment from scratch
# - Runs comprehensive functionality tests
# - Takes ~2 minutes, prevents broken releases

# Quick test during development (skip reinstall)
./tools/testing/run_full_regression_tests.py --skip-install --quick
```

**🚀 AUTOMATED TESTING (Recommended):**
```bash
./tools/testing/run_all_tests.sh

# Run with verbose output for debugging
./tools/testing/run_all_tests.sh --verbose

# Run only Python tests (fast)
./tools/testing/run_all_tests.sh --python-only

# Stop on first failure (for debugging)
./tools/testing/run_all_tests.sh --fail-fast
```

**🐍 TRADITIONAL PYTHON TESTING:**
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/

# Run tests with coverage (preferred)
uv run pytest --cov=circuit_synth

# Run specific test file
uv run pytest tests/unit/test_core_circuit.py -v
```

### Building and Distribution

**Using uv (recommended):**
```bash
# Build package
uv build

# Install locally in development mode
uv pip install -e .
```

**Using traditional tools:**
```bash
# Build package
python -m build

# Install locally
pip install -e .
```

## 🤖 Development Agents

This repository uses specialized development agents:

### **👨‍💻 contributor Agent**
- **Expertise**: Code review, architecture guidance, and open-source project management
- **Usage**: `@Task(subagent_type="contributor", description="Review code", prompt="Review this new component placement algorithm for code quality")`
- **Capabilities**: 
  - SOLID principles validation and clean architecture
  - Test-driven development (TDD) guidance
  - Documentation and contribution workflow support
  - Community engagement and knowledge sharing

### **⚙️ code Agent**
- **Expertise**: Software engineering best practices and clean implementation
- **Usage**: `@Task(subagent_type="code", description="Implement feature", prompt="Implement a new JSON processing pipeline following clean architecture")`
- **Capabilities**: 
  - Modern Python patterns with type hints and dataclasses
  - Performance optimization and algorithm improvement
  - Refactoring and technical debt resolution
  - Design pattern application and architectural decisions

### **🔍 general-purpose Agent**
- **Expertise**: Complex research, codebase analysis, and multi-step problem solving
- **Usage**: `@Task(subagent_type="general-purpose", description="Analyze codebase", prompt="Research how component placement algorithms work across the codebase")`
- **Capabilities**: 
  - Deep codebase exploration and cross-file dependency analysis
  - Architecture analysis and design pattern identification
  - Multi-round investigation and comprehensive reporting
  - Cross-component impact assessment

## 📋 Code Style Guidelines

**IMPORTANT: Follow these conventions exactly**
- Use modern Python with type hints and dataclasses
- NO inheritance complexity or global state management
- Follow SOLID, KISS, YAGNI, and DRY principles
- Prefer composition over inheritance
- Use descriptive variable and function names
- Write comprehensive docstrings for public APIs

## 🔄 Development Workflow

**Test-Driven Development (TDD) - MANDATORY APPROACH:**
1. **Write tests first** based on expected input/output behavior
2. **Run tests to confirm they fail** (red phase)
3. **Write minimal code** to make tests pass (green phase)
4. **Refactor and improve** while keeping tests passing
5. **Test thoroughly at each step** - don't assume code works
6. **YOU MUST run linting and type checking** before committing

**Incremental Development Philosophy:**
- **Make slow, steady progress** - small incremental changes are better than large jumps
- **Test every assumption** - don't assume your code does what you think it does
- **Validate behavior continuously** - run tests after every small change
- **Confirm expectations** - manually verify outputs match what you expect
- **One feature at a time** - complete and thoroughly test one feature before moving to the next
- **Example workflow**: Write test → Run test (fails) → Write minimal code → Run test (passes) → Manually verify output → Move to next small piece

**Planning Before Coding:**
- Always ask Claude to make a plan before implementing
- Use "think" keywords for extended thinking mode
- Break complex tasks into smaller, actionable steps

## 🏗️ Architecture Understanding

### JSON-Centric Architecture

Circuit-synth uses **JSON as the canonical intermediate representation** for all circuit data:

### Data Flow
```
Python Circuit Code ←→ JSON (Central Format) ←→ KiCad Files
```

- **Python → JSON**: `circuit.to_dict()` or `circuit.generate_json_netlist()`
- **JSON → KiCad**: Internal JSON processing generates .kicad_* files
- **KiCad → JSON**: Parser extracts circuit structure to JSON format
- **JSON → Python**: `json_to_python_project` generates Python code

### Key Points
1. **Hierarchical circuits are stored as nested JSON** with subcircuits preserved
2. **Round-trip conversion is lossless** - no information lost in any direction
3. **JSON is the single source of truth** - all conversions go through JSON
4. **One JSON format** - consistent structure for all operations

For detailed architecture information, see `docs/ARCHITECTURE.md`.

### Scalable Directory Structure

The repository is organized with a scalable directory structure to support multiple chip families and manufacturers:

```
circuit-synth/
├── src/circuit_synth/
│   ├── component_info/           # Component-specific integrations
│   │   ├── microcontrollers/    # MCU families (STM32, ESP32, PIC, AVR)
│   │   ├── analog/              # Analog components (op-amps, ADCs, etc.)
│   │   ├── power/               # Power management components
│   │   ├── rf/                  # RF/wireless components
│   │   ├── passives/            # Passive components (future)
│   │   └── sensors/             # Sensors and measurement (future)
│   ├── manufacturing/           # Manufacturing integrations  
│   │   ├── jlcpcb/             # JLCPCB integration
│   │   ├── pcbway/             # PCBWay (future)
│   │   ├── oshpark/            # OSH Park (future)
│   │   └── digikey/            # DigiKey sourcing (implemented)
│   ├── tools/                  # CLI tools and utilities
│   └── [core modules...]       # Core circuit-synth functionality
├── examples/                   # User examples organized by complexity
├── tests/                      # Comprehensive test suite
├── docs/                       # Technical documentation
└── tools/                      # Development and build tools
```

## 🔧 Development Environment Setup

### KiCad Integration Requirements
```bash
# Ensure KiCad is installed locally (required dependency)
kicad-cli version

# Verify KiCad libraries are accessible
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5
```

### Development Dependencies
All development dependencies are managed through `uv` and defined in `pyproject.toml`:
- **Testing**: pytest, pytest-cov, pytest-benchmark
- **Code Quality**: black, isort, flake8, mypy
- **Documentation**: sphinx, sphinx-rtd-theme
- **Build Tools**: build, twine

## 🚧 Debugging Strategy

**Development Flow Pattern:**
- **Always use uv for running Python scripts**: Use `uv run python script.py` instead of just `python script.py`
- **Add extensive logging during development**: Use Python's `logging` module liberally when troubleshooting or implementing new features
- **Log key data points**: Component creation, net connections, file operations, API calls
- **Redirect logs to files for analysis**: When logs grow too large for terminal, use `uv run python script.py > debug_output.log 2>&1` to capture all output
- **Remove non-essential logs when feature is complete**: Keep only critical error logs and high-level status messages
- **Example**: `logging.debug(f"Creating component {ref} with symbol {symbol}")` during development, remove when stable

**Multi-Attempt Problem Solving Protocol:**
When you have attempted to fix the same issue 3+ times without success, **STOP** and follow this systematic approach:

1. **Document the Problem State**:
   - Write a clear problem statement
   - List all attempted solutions with outcomes
   - Identify recurring patterns in failures
   - Note any error messages, symptoms, or clues

2. **Context Management**:
   - Use `/compact` to compress the conversation context
   - Save important findings to `memory-bank/issues/` if needed
   - Clear mental context to approach fresh

3. **Deep Analysis Phase**:
   - Break the problem into smaller, isolated components
   - Identify root causes vs. symptoms
   - Question initial assumptions about the problem
   - Consider alternative approaches or architectures

4. **Research Phase**:
   - Use WebSearch to research similar problems, error messages, or techniques
   - Look for official documentation, Stack Overflow solutions, GitHub issues
   - Research best practices for the specific technology or domain
   - Investigate whether the approach itself is fundamentally flawed

5. **Systematic Solution**:
   - Based on research, create a new approach plan
   - Test each component in isolation
   - Implement incrementally with verification at each step
   - Document the successful solution for future reference

**Example trigger scenarios:**
- Same CI test failing after 3+ different fix attempts
- Repeatedly encountering the same error with different "solutions"
- Multiple approaches to the same feature all hitting similar roadblocks
- Environment or dependency issues that persist across multiple fixes

## 📝 Memory Bank System

**CRITICAL: Use memory-bank/ effectively for context preservation**

The `memory-bank/` directory maintains project context and technical knowledge across development sessions:

### Memory Bank Structure
```
memory-bank/
├── progress/          # Development progress tracking
├── decisions/         # Technical decisions and rationale  
├── patterns/          # Reusable code patterns and solutions
├── issues/           # Known issues and workarounds
└── knowledge/        # Domain-specific insights and learnings
```

### How to Use Memory Bank

**1. Progress Tracking (`memory-bank/progress/`):**
- Create focused entries for significant technical milestones
- Document **what** was implemented and **why** it was needed
- Keep entries concise (2-3 sentences maximum)
- Use date-based filenames: `2025-08-10-feature-name.md`

**2. Technical Decisions (`memory-bank/decisions/`):**
- Record architectural choices and trade-offs
- Document **why** you chose one approach over alternatives
- Include context about constraints and requirements

**3. Reusable Patterns (`memory-bank/patterns/`):**
- Save common implementation patterns
- Document successful architectural solutions
- Record effective testing and validation strategies

**4. Issue Tracking (`memory-bank/issues/`):**
- Document known bugs with workarounds
- Track compatibility issues between tools and dependencies
- Record debugging strategies that worked

## 🏗️ Repository Structure

### CRITICAL: Two Circuit-Synth Repositories

There are **TWO** distinct circuit-synth repositories that contributors must be aware of:

1. **Private Repository**: `Circuit_Synth2/` (closed source)
   - This is the original project where most functionality was initially developed
   - Contains the complete, mature implementation
   - Located at `/Users/shanemattner/Desktop/Circuit_Synth2/`
   - This is the private, closed-source version

2. **Open Source Repository**: `Circuit_Synth2/submodules/circuit-synth/` (open source)
   - This is the open-source version created as a submodule
   - Some functionality from the private repo was **not copied over properly**
   - Located at `/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth/`
   - **This is where all new development should happen**

### Development Guidelines

- **ALWAYS work in the open source repo**: `/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth/`
- When referencing functionality, be explicit about which repo you're looking at
- If functionality exists in the private repo but is missing from the open source repo, it needs to be ported over
- **Never make changes to the private repo** - all development goes in the open source version
- Keep track of which repo contains which functionality to avoid confusion

### Repository References

When discussing code or functionality:
- **Private repo**: Reference as "private Circuit_Synth2 repo" or "closed source repo"
- **Open source repo**: Reference as "open source circuit-synth repo" or "submodule repo"
- **Default assumption**: Unless specified otherwise, all work should be done in the **open source repo**

## 📦 PyPI Release Process

**IMPORTANT: Clean repository before releasing to PyPI**

The repository includes an automated release script that handles the complete PyPI release pipeline:

```bash
# Release to PyPI (from develop or main branch)
./tools/release/release_to_pypi.sh 0.5.1
```

### Pre-Release Checklist

**1. Clean up test/temporary files:**
The release script will check for and warn about files that shouldn't be in the main branch:
- Top-level Python scripts (test_*.py, *_test.py, debug scripts)
- Generated directories (*_generated/, *_reference/, *_Dev_Board/)
- Temporary files (*.log, *.tmp, *.txt)
- Debug/analysis files (*.md except README.md, CLAUDE.md, Contributors.md)

**2. Ensure clean working directory:**
```bash
git status  # Should show no uncommitted changes
```

**3. Update from develop branch:**
```bash
git checkout develop
git pull origin develop
```

### What the Release Script Does

1. **Validates** version format and clean working directory
2. **Checks** for test/temporary files that shouldn't be released
3. **Updates** version in pyproject.toml and __init__.py
4. **Runs** test suite to ensure everything works
5. **Merges** develop → main (if releasing from develop)
6. **Tags** the release with semantic version
7. **Builds** source and wheel distributions
8. **Cleans** build artifacts and caches
9. **Uploads** to PyPI
10. **Creates** GitHub release with changelog

### Post-Release

After successful release:
- Package available at: https://pypi.org/project/circuit-synth/
- GitHub release created with changelog
- Users can install with: `pip install circuit-synth==VERSION`

## 🎯 Contributing Guidelines

### Development Focus Areas

**Circuit Design & EDA Integration:**
- KiCad symbol/footprint parsing and integration
- Component placement and routing algorithms
- Hierarchical circuit design patterns
- PCB generation and manufacturing optimization

**Manufacturing Intelligence:**
- JLCPCB and DigiKey API integration
- Component availability and pricing optimization
- Design for Manufacturing (DFM) analysis
- Supply chain management and alternatives

**AI Integration:**
- Claude Code agent development and optimization
- Natural language to circuit code generation
- Component intelligence and recommendation systems
- Circuit validation and quality assurance

### Code Contribution Workflow

1. **Fork and Clone**: Fork the repository and create a feature branch
2. **Setup Environment**: Use `/setup-dev-environment` for complete setup
3. **Write Tests First**: Follow TDD approach with comprehensive test coverage
4. **Implement Feature**: Follow clean architecture and coding standards
5. **Run Quality Checks**: Use `/dev-run-tests` and `/dev-update-and-commit`
6. **Create Pull Request**: Submit PR with detailed description and testing evidence

---

**This repository is optimized for professional circuit-synth development and contribution!** 🛠️