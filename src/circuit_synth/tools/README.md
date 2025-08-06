# Circuit-Synth CLI Tools

This directory contains user-facing command-line tools and utilities that are installed with the circuit-synth package.

## 📁 Directory Structure

### `kicad_integration/`
**KiCad Synchronization and Integration**
- `kicad_to_python_sync.py` - Sync KiCad schematics to Python code
- `python_to_kicad_sync.py` - Sync Python circuits to KiCad schematics  
- `preload_symbols.py` - Preload KiCad symbol libraries
- `preparse_kicad_symbols.py` - Parse and cache symbol definitions

### `project_management/`
**Project Setup and Management**
- `new_project.py` - Create new circuit-synth projects
- `init_existing_project.py` - Set up circuit-synth in existing projects
- `init_pcb.py` - Initialize PCB generation for existing circuits

### `development/`
**Development and Setup Tools**
- `setup_claude.py` - Configure Claude Code integration
- `setup_kicad_plugins.py` - Install and configure KiCad plugins
- `pcb_tracker_basic.py` - Track PCB design changes

### `utilities/`
**General Utilities and Parsers**
- `kicad_netlist_parser.py` - Parse KiCad netlist files
- `kicad_parser.py` - General KiCad file parser
- `python_code_generator.py` - Generate Python from circuit data
- `ai_design_manager.py` - AI-powered design management
- `circuit_creator_cli.py` - Command-line circuit creation
- `llm_code_updater.py` - LLM-assisted code updates

## Usage

Most tools can be run directly as Python scripts:

```bash
# KiCad Integration
python src/circuit_synth/cli/kicad_integration/preload_symbols.py
python src/circuit_synth/cli/kicad_integration/kicad_to_python_sync.py project.kicad_sch circuit.py --preview

# Project Management
python src/circuit_synth/cli/project_management/new_project.py my_circuit
python src/circuit_synth/cli/project_management/init_existing_project.py

# Development Setup
python src/circuit_synth/cli/development/setup_claude.py
python src/circuit_synth/cli/development/setup_kicad_plugins.py

# Utilities
python src/circuit_synth/cli/utilities/python_code_generator.py input.json output.py
```

## 🎯 Tool Categories

### KiCad Integration
Bidirectional synchronization between Python circuit definitions and KiCad schematics, plus symbol management for improved performance.

### Project Management  
Tools for creating new projects, initializing circuit-synth in existing projects, and setting up PCB workflows.

### Development Tools
Setup and configuration utilities for integrating with external tools and development environments.

### General Utilities
Parsers, generators, and AI-powered tools for circuit design and code management.

## 🔗 Related Directories

- **`/tools/`** - Development tools (build, test, CI) - not installed with package
- **`/examples/`** - Usage examples and reference implementations  
- **`/docs/`** - API documentation and user guides

## Development Guidelines

When adding new CLI tools:
1. Place in appropriate subdirectory based on function
2. Include comprehensive docstrings and `--help` text
3. Follow existing error handling and logging patterns
4. Add entry to this README with usage examples
5. Consider whether tool belongs in CLI (user-facing) or tools/ (development)