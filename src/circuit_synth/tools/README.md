# Circuit-Synth CLI Tools

This directory contains command-line tools and utilities for professional circuit design workflows.

## Available Tools

### KiCad Integration
- **`kicad_to_python_sync.py`** - Synchronize changes from KiCad schematics back to Python code
- **`python_to_kicad_sync.py`** - Synchronize Python circuit definitions to KiCad schematics
- **`preload_symbols.py`** - Preload KiCad symbol libraries for faster access
- **`preparse_kicad_symbols.py`** - Parse and cache KiCad symbol definitions

### Development Tools
- **`pcb_tracker_basic.py`** - Track and analyze PCB design changes
- **`setup_claude.py`** - Set up Claude Code integration for AI-powered circuit design

## Usage

Most tools can be run directly as Python scripts:

```bash
# Preload KiCad symbols for faster access
python src/circuit_synth/tools/preload_symbols.py

# Set up Claude Code integration
python src/circuit_synth/tools/setup_claude.py

# Sync changes from KiCad schematic to Python
python src/circuit_synth/tools/kicad_to_python_sync.py project.kicad_sch circuit.py --preview
```

## Tool Categories

### Synchronization Tools
These tools enable bidirectional synchronization between Python circuit definitions and KiCad schematics, allowing designers to work in either environment while maintaining consistency.

### Performance Tools  
Symbol preloading and caching tools improve the performance of circuit generation by pre-processing KiCad libraries.

### Integration Tools
Setup and configuration tools for integrating circuit-synth with external tools like Claude Code and development environments.

## Development

When adding new tools:
1. Make scripts executable with appropriate shebang (`#!/usr/bin/env python3`)
2. Include comprehensive docstrings and help text
3. Follow the existing error handling and logging patterns
4. Add entry to this README with usage examples