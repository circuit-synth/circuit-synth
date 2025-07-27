# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup

**Primary method (recommended) - using uv:**
```bash
# Install the project in development mode
uv pip install -e ".[dev]"

# Install dependencies
uv sync
```

**Alternative method - using pip:**
```bash
# If uv is not available
pip install -e ".[dev]"
```

### Code Quality and Testing
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/

# Run tests (recommended with uv)
uv run pytest

# Run tests with coverage
uv run pytest --cov=circuit_synth

# Alternative with pip
pytest
pytest --cov=circuit_synth
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

## Agent Workflow

This repository uses a structured agent workflow for handling complex tasks. Always start in **orchestrator** mode, which coordinates other specialized agents.

### Standard Workflow

1. **orchestrator**: Entry point for all complex tasks
   - Analyzes the overall request and breaks it down into coordinated subtasks
   - Delegates specialized work to appropriate agents
   - Manages dependencies and ensures proper sequencing

2. **architect**: Planning and analysis phase
   - Breaks down complex or unclear tasks into actionable steps
   - Gathers requirements and asks clarifying questions
   - Creates structured todo lists and implementation plans
   - Provides architectural guidance and design decisions

3. **code**: Implementation phase  
   - Performs actual coding changes following best practices
   - Reviews code against SOLID, KISS, YAGNI, and DRY principles
   - Implements solutions based on architect's plans
   - Ensures code quality and maintainability

### When to Use Each Agent

- **Start with orchestrator** for any multi-step or complex request
- Use **architect** when you need to plan, analyze requirements, or break down tasks
- Use **code** when you need to implement, review, or refactor code
- Let **orchestrator** coordinate the handoffs between agents

### Example Flow

```
User Request: "Add a new placement algorithm for PCB components"

orchestrator → architect (analyze requirements, plan implementation)
architect → code (implement the algorithm following the plan)  
orchestrator → (coordinate testing, documentation, integration)
```

## Repository Structure

### CRITICAL: Two Circuit-Synth Repositories

There are **TWO** distinct circuit-synth repositories that you must be aware of:

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
