# circuit-synth

Pythonic circuit design for professional KiCad projects

## Overview

Circuit Synth is an open-source Python library that fits seamlessly into normal EE workflows without getting too fancy. Unlike domain-specific languages that require learning new syntax, circuit-synth uses simple, transparent Python code that any engineer can understand and modify.

**Core Principles:**
- **Simple Python Code**: No special DSL to learn - just Python classes and functions
- **Transparent to Users**: Generated KiCad files are clean and human-readable
- **Bidirectional Updates**: KiCad can remain the source of truth - import existing projects and export changes back
- **Normal EE Workflow**: Integrates with existing KiCad-based development processes

**Current Status**: Circuit-synth is ready for professional use with the following capabilities:
- Places components functionally (not yet optimized for intelligent board layout)
- Places schematic parts (without intelligent placement algorithms)
- Generates working KiCad projects suitable for professional development

## Example

```python
from circuit_synth import *

@circuit(name="esp32s3_simple")
def esp32s3_simple():
    """Simple ESP32-S3 circuit with decoupling capacitor and debug header"""
    
    # Create power nets
    _3V3 = Net('3V3')
    GND = Net('GND')
    
    # ESP32-S3 module
    esp32s3 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-S2-MINI-1"
    )
    
    # Decoupling capacitor
    cap_power = Component(
        symbol="Device:C",
        ref="C", 
        value="10uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Debug header
    debug_header = Component(
        symbol="Connector_Generic:Conn_02x03_Odd_Even",
        ref="J",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical"
    )
    
    # Power connections
    esp32s3["3V3"] += _3V3  # Power pin
    esp32s3["GND"] += GND   # Ground pin
    
    # Decoupling capacitor connections
    cap_power[1] += _3V3
    cap_power[2] += GND
    
    # Debug header connections
    debug_header[1] += esp32s3['EN']
    debug_header[2] += _3V3
    debug_header[3] += esp32s3['TXD0']
    debug_header[4] += GND
    debug_header[5] += esp32s3['RXD0']
    debug_header[6] += esp32s3['IO0']

if __name__ == '__main__':
    circuit = esp32s3_simple()
    circuit.generate_kicad_project("esp32s3_simple")
```

## Key Differentiators

### Bidirectional KiCad Integration
Unlike other circuit design tools that generate KiCad files as output only, circuit-synth provides true bidirectional updates:
- **Import existing KiCad projects** into Python for programmatic modification
- **Export Python circuits** to clean, readable KiCad projects
- **KiCad remains source of truth** - make manual changes in KiCad and sync back to Python
- **Hybrid workflows** - combine manual design with automated generation

### Engineering-Friendly Approach
- **No Domain-Specific Language**: Uses standard Python syntax that any engineer can read and modify
- **Transparent Output**: Generated KiCad files are clean and human-readable, not machine-generated gibberish
- **Fits Existing Workflows**: Designed to integrate with normal EE development processes, not replace them
- **Professional Development**: Built for real engineering teams, not just hobbyists

### Additional Features
- **Pythonic Circuit Design**: Define circuits using intuitive Python classes and decorators
- **Component Management**: Built-in component library with easy extensibility  
- **Smart Placement**: Automatic component placement algorithms
- **Type Safety**: Full type hints support for better IDE integration
- **Extensible Architecture**: Clean interfaces for custom implementations

## AI-Powered Development

Circuit-synth includes a specialized Claude agent for expert guidance on circuit-synth syntax, structure, and best practices. The agent helps with:

- **Code Reviews**: Analyzing circuit-synth projects for proper structure and conventions
- **Best Practices**: Guidance on component reuse, net management, and circuit organization  
- **Syntax Help**: Examples and patterns for proper circuit-synth implementation
- **Refactoring**: Suggestions for improving code maintainability and clarity

### Using the Circuit-Synth Agent

The agent is available in `.claude/agents/circuit-synth.md` and specializes in:

```python
# Component reuse patterns the agent recommends
C_10uF_0805 = Component(
    symbol="Device:C", ref="C", value="10uF",
    footprint="Capacitor_SMD:C_0805_2012Metric"
)

# Then instantiate with unique references
cap_input = C_10uF_0805()
cap_input.ref = "C4"  # Override ref for specific instance
```

The agent provides structured feedback on:
- Component definition and reuse patterns
- Circuit structure and @circuit decorator usage
- Net management and naming conventions
- Pin connection syntax (integer vs string access)
- Code organization and maintainability

## Quick Start

Try circuit-synth immediately without installation:

```bash
# Clone the repository
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Run the example (automatically installs dependencies with uv)
uv run python examples/example_kicad_project.py
```

This will generate a complete KiCad project in the `example_kicad_project/` directory.

## Installation

### Using uv (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install circuit-synth for development
uv pip install -e ".[dev]"
```

### Using pip (in virtual environment)

Since this package isn't published to PyPI yet, install from source:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Clone and install
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
pip install -e ".[dev]"
```

### Development Setup

For development work:

```bash
# Clone the repository
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Install with development dependencies using uv
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Using Docker

Circuit-synth can be run in Docker containers with full KiCad library support:

```bash
# Build the Docker image
./docker/build-docker.sh

# Run any circuit-synth command in Docker
./scripts/circuit-synth-docker python examples/example_kicad_project.py

# Run with interactive shell
./scripts/circuit-synth-docker --interactive bash

# Run without KiCad libraries (faster startup)
./scripts/circuit-synth-docker --no-libs python -c "import circuit_synth; print('Ready!')"
```

**Docker Features:**
- Pre-configured environment with all dependencies
- Official KiCad symbol and footprint libraries included
- Automatic file persistence to local `output/` directory
- Security through non-root user execution
- Two Dockerfile options: simplified Python-only (main) and full Rust build (`docker/Dockerfile.rust-build`)

**Docker Commands:**
```bash
# Universal command runner
./scripts/circuit-synth-docker <any-python-command>

# KiCad library-specific runner
./scripts/run-with-kicad.sh --official-libs

# Docker Compose services (from docker/ directory)
cd docker && docker-compose up circuit-synth        # Basic service
cd docker && docker-compose up circuit-synth-dev    # Development mode
cd docker && docker-compose up circuit-synth-test   # Test runner
```

**Docker Build Options:**
```bash
# Quick Python-only build (recommended)
./docker/build-docker.sh

# Full build with Rust modules (advanced users)
docker build -f docker/Dockerfile.rust-build -t circuit-synth-rust .

# Windows users
./docker/build-docker.bat
```

#### Docker Attribution

The Docker implementation is a collaborative effort:
- **Original implementation**: Kumuda Subramanyam Govardhanam (@KumudaSG) - comprehensive Rust module compilation support
- **Enhancements**: KiCad library integration, simplified Python-only build, universal command runners, and build automation

## Documentation

Full documentation is available at [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

**Prerequisites:**
- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Git

**Getting Started:**

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/circuit-synth.git
   cd circuit-synth
   ```

2. **Install dependencies (recommended with uv):**
   ```bash
   # Install the project in development mode
   uv pip install -e ".[dev]"
   
   # Install dependencies
   uv sync
   ```

3. **Alternative installation with pip:**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install in development mode
   pip install -e ".[dev]"
   ```

**Development Guidelines:**
- Follow existing code style and patterns
- Write tests for new functionality
- Update documentation as needed
- Test your changes with `uv run python examples/example_kicad_project.py`
- Use the Docker environment for testing: `./scripts/circuit-synth-docker python examples/example_kicad_project.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues)
- Discussions: [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions)
