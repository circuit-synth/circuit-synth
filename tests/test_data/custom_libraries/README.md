# Custom KiCad Libraries for Testing

This directory contains custom KiCad symbol libraries used for testing the custom library functionality.

## Structure

```
custom_libraries/
├── README.md
├── test_components.kicad_sym     # Simple test components
├── microcontrollers.kicad_sym    # Custom MCU symbols
├── power_modules.kicad_sym       # Custom power management
└── connectors.kicad_sym          # Custom connector symbols
```

## Usage

These libraries are used to test:
- Custom library loading and parsing
- Symbol override functionality
- Multi-path library resolution
- User-defined component libraries
- Library precedence and conflict resolution

## Environment Setup

Set `KICAD_SYMBOL_DIR` to include this directory:
```bash
export KICAD_SYMBOL_DIR="/usr/share/kicad/symbols:$(pwd)/tests/test_data/custom_libraries"
```

Or use the test fixtures that automatically configure paths.