# Circuit-Synth Examples

This directory contains examples, demos, and utilities for Circuit-Synth.

## Directory Structure

### `basic/` - Basic Usage Examples
Simple examples demonstrating core Circuit-Synth functionality:
- Basic circuit creation and component usage
- Simple PCB operations and CLI integration
- Introduction to schematic generation

### `advanced/` - Advanced Feature Examples  
Complex examples showcasing advanced features:
- Complete PCB routing workflows with FreeRouting
- Force-directed placement algorithms
- Advanced KiCad integration patterns
- Multi-sheet hierarchical designs

### `testing/` - Test and Validation Scripts
Scripts for testing functionality and validating integrations:
- Component management tests
- Footprint library validation
- Search and discovery functionality tests
- Wire management and hierarchy tests

### `tools/` - Utility Scripts
Helpful tools for development and debugging:
- Footprint library browsing and search
- Component detail inspection
- Visualization tools for placement algorithms

## Running Examples

Most examples can be run directly:

```bash
# Run a basic example
python examples/basic/simple_cli_test.py

# Run an advanced routing example
python examples/advanced/complete_routing_example.py

# Use a utility tool
python examples/tools/list_footprint_libraries.py
```

Note: Some examples may require KiCad to be installed and properly configured.

## Contributing Examples

When adding new examples:
1. Place in the appropriate category directory
2. Include clear documentation and comments
3. Add any required dependencies to the example docstring
4. Test the example works with a clean circuit-synth installation