# PCB Routing Module

This module provides tools for PCB routing integration with Circuit Synth, enabling automatic routing of PCB designs using external tools like Freerouting.

## Recent Updates (2025-06-24)

### 🎉 Complete Freerouting Workflow Fixed

All critical issues preventing end-to-end Freerouting integration have been resolved:

1. **DSN Placement Format** - Fixed component placement syntax for Freerouting compatibility
2. **Via Padstack Definitions** - Added missing via definitions preventing routing
3. **SES Parser Improvements** - Enhanced to handle various session formats
4. **Wire Parsing Fix** - Correctly parses network_out blocks with multi-line wires

The complete workflow (PCB → DSN → Freerouting → SES → Routed PCB) is now fully functional!

## Features

### 1. DSN Export
- Export KiCad PCB files to Specctra DSN format
- Support for multi-layer boards
- Configurable design rules (track width, clearance, via specs)
- Automatic net extraction and connectivity mapping
- Board outline detection with fallback defaults

### 2. Freerouting Integration
- Subprocess management for Freerouting JAR execution
- Docker-based execution option (no Java installation required)
- Progress tracking with real-time updates
- Configurable routing effort levels (fast, medium, high)
- Timeout handling for long operations
- Error handling and recovery

### 3. SES Import
- Import routed boards from Freerouting SES files
- Automatic track and via placement
- Layer mapping and conversion
- Net preservation and validation
- Support for protected/fixed routing

### 4. Configuration Options
- Java runtime path configuration
- Memory allocation settings
- Via cost optimization
- Layer restrictions
- Optimization pass control

## Installation

### 1. Install Circuit Synth Core
```bash
pip install circuit-synth-core
```

### 2. Install Freerouting

#### Option A: Docker (Recommended)
No installation required! The Docker-based runner will automatically pull the Freerouting image.

Requirements:
- Docker installed and running
- User has permissions to run Docker commands

#### Option B: Local JAR
See [FREEROUTING_SETUP.md](FREEROUTING_SETUP.md) for detailed installation instructions.

Quick install:
- Download from [Freerouting Releases](https://github.com/freerouting/freerouting/releases)
- Install Java 21 JRE if not already installed
- Place `freerouting-2.1.0.jar` in `~/freerouting/` or `C:\freerouting\`

## Quick Start

### Basic Usage

```python
from circuit_synth.pcb.routing import (
    export_pcb_to_dsn, route_pcb, import_ses_to_pcb
)

# Step 1: Export PCB to DSN format
export_pcb_to_dsn("my_board.kicad_pcb", "my_board.dsn")

# Step 2: Run auto-routing
success, result = route_pcb("my_board.dsn", "my_board.ses")

if success:
    print(f"Routing complete! Session file: {result}")
    
    # Step 3: Import the routed board back
    import_ses_to_pcb("my_board.kicad_pcb", "my_board.ses", "my_board_routed.kicad_pcb")
else:
    print(f"Routing failed: {result}")
```

### Using Docker (No Java Required)

```python
from circuit_synth.pcb.routing import route_pcb_docker

# Route using Docker - no Java installation needed!
success, result = route_pcb_docker("my_board.dsn", "my_board.ses")

if success:
    print(f"Routing complete! Session file: {result}")
    import_ses_to_pcb("my_board.kicad_pcb", "my_board.ses", "my_board_routed.kicad_pcb")
```

### With Progress Tracking

```python
def show_progress(progress, status):
    print(f"Progress: {progress:.1f}% - {status}")

success, result = route_pcb(
    "my_board.dsn",
    "my_board.ses",
    effort='medium',
    optimization_passes=10,
    progress_callback=show_progress
)
```

## Advanced Usage

### Custom DSN Export

```python
from circuit_synth.pcb.routing import DSNExporter

# Create exporter with custom rules
exporter = DSNExporter(
    pcb_file="my_board.kicad_pcb",
    track_width=0.2,      # 0.2mm tracks
    clearance=0.15,       # 0.15mm clearance
    via_diameter=0.6,     # 0.6mm via diameter
    via_drill=0.3         # 0.3mm via drill
)

# Export to DSN
exporter.export("my_board.dsn")
```

### Advanced Routing Configuration

```python
from circuit_synth.pcb.routing import (
    FreeroutingRunner, FreeroutingConfig, RoutingEffort
)

# Configure routing parameters
config = FreeroutingConfig(
    # Routing quality
    effort=RoutingEffort.HIGH,
    optimization_passes=20,
    
    # Via optimization (higher = fewer vias)
    via_costs=100.0,
    
    # Restrict to 2-layer board
    allowed_layers=[0, 31],  # F.Cu and B.Cu
    
    # Performance settings
    memory_mb=2048,
    timeout_seconds=3600,
    
    # Custom JAR location
    freerouting_jar="/opt/freerouting/freerouting-2.1.0.jar"
)

# Create runner and route
runner = FreeroutingRunner(config)
success, result = runner.route("my_board.dsn", "my_board.ses")
```

### Docker-based Routing

```python
from circuit_synth.pcb.routing import (
    FreeroutingDockerRunner, FreeroutingConfig, RoutingEffort
)

# Configure routing parameters
config = FreeroutingConfig(
    effort=RoutingEffort.HIGH,
    optimization_passes=20,
    via_costs=100.0,
    timeout_seconds=3600
)

# Create Docker runner (no Java required!)
runner = FreeroutingDockerRunner(config)
success, result = runner.route("my_board.dsn", "my_board.ses")
```

### Batch Processing

```python
import os
from pathlib import Path

def route_all_boards(directory):
    """Route all PCB files in a directory"""
    pcb_files = Path(directory).glob("*.kicad_pcb")
    
    for pcb_file in pcb_files:
        print(f"Processing {pcb_file.name}...")
        
        # File paths
        dsn_file = pcb_file.with_suffix('.dsn')
        ses_file = pcb_file.with_suffix('.ses')
        
        # Export and route
        try:
            export_pcb_to_dsn(str(pcb_file), str(dsn_file))
            success, result = route_pcb(
                str(dsn_file),
                str(ses_file),
                effort='fast'  # Fast for batch processing
            )
            
            if success:
                print(f"  ✓ Routed successfully")
            else:
                print(f"  ✗ Failed: {result}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
```

## API Reference

### DSN Export

#### `export_pcb_to_dsn(pcb_file, output_file, **kwargs)`
Convenience function to export a PCB to DSN format.

**Parameters:**
- `pcb_file` (str): Path to KiCad PCB file
- `output_file` (str): Path for output DSN file
- `**kwargs`: Additional parameters for DSNExporter

#### `DSNExporter`
Main class for DSN export functionality.

**Constructor Parameters:**
- `pcb_file` (str): Path to KiCad PCB file
- `track_width` (float): Default track width in mm (default: 0.25)
- `clearance` (float): Default clearance in mm (default: 0.2)
- `via_diameter` (float): Via diameter in mm (default: 0.8)
- `via_drill` (float): Via drill size in mm (default: 0.4)

### Freerouting Runner

#### `route_pcb(dsn_file, output_file, **kwargs)`
Convenience function to route a PCB using Freerouting.

**Parameters:**
- `dsn_file` (str): Path to input DSN file
- `output_file` (str): Path for output SES file (optional)
- `effort` (str): Routing effort - 'fast', 'medium', 'high' (default: 'medium')
- `optimization_passes` (int): Number of optimization passes (default: 10)
- `timeout_seconds` (int): Timeout in seconds (default: 3600)
- `progress_callback` (callable): Function called with (progress, status)

**Returns:**
- Tuple[bool, str]: (success, output_file_or_error_message)

#### `route_pcb_docker(dsn_file, output_file, **kwargs)`
Docker-based routing function that doesn't require Java installation.

**Parameters:**
Same as `route_pcb()`

**Returns:**
Same as `route_pcb()`

#### `FreeroutingRunner`
Main class for managing Freerouting execution.

**Methods:**
- `route(dsn_file, output_file)`: Run routing on a DSN file
- `stop()`: Stop the routing process
- `get_progress()`: Get current progress (percentage, status)

#### `FreeroutingConfig`
Configuration dataclass for Freerouting.

**Fields:**
- `java_path` (str): Path to Java executable
- `freerouting_jar` (str): Path to Freerouting JAR
- `effort` (RoutingEffort): Routing effort level
- `optimization_passes` (int): Number of optimization passes
- `via_costs` (float): Via cost factor
- `allowed_layers` (list): List of allowed routing layers
- `memory_mb` (int): Java heap size in MB
- `timeout_seconds` (int): Timeout in seconds
- `progress_callback` (callable): Progress callback function

#### `FreeroutingDockerRunner`
Docker-based runner for Freerouting (no Java required).

**Methods:**
Same as `FreeroutingRunner`

**Docker Image:**
Uses `ghcr.io/freerouting/freerouting:nightly`

### SES Import

#### `import_ses_to_pcb(pcb_file, ses_file, output_file)`
Convenience function to import SES routing into a PCB.

**Parameters:**
- `pcb_file` (str): Path to original KiCad PCB file
- `ses_file` (str): Path to SES file with routing data
- `output_file` (str): Path for output PCB file (optional)

**Returns:**
- str: Path to the output PCB file

#### `SESImporter`
Main class for importing SES routing data.

**Constructor Parameters:**
- `pcb_file` (str): Path to original KiCad PCB file
- `ses_file` (str): Path to SES file with routing data

**Methods:**
- `import_routing(output_file)`: Import routing and save to output file

## Workflow Integration

### Complete PCB Routing Workflow

1. **Generate PCB with Circuit Synth**
   ```python
   from circuit_synth import generate_pcb
   generate_pcb(circuit, "my_board")
   ```

2. **Export to DSN**
   ```python
   export_pcb_to_dsn("my_board.kicad_pcb", "my_board.dsn")
   ```

3. **Run Auto-routing**
   ```python
   success, ses_file = route_pcb("my_board.dsn", "my_board.ses")
   ```

4. **Import Back to KiCad (Automated)**
   ```python
   # Programmatic import
   import_ses_to_pcb("my_board.kicad_pcb", "my_board.ses", "my_board_routed.kicad_pcb")
   ```
   
   Or manually in KiCad:
   - Open PCB in KiCad PCB Editor
   - File → Import → Specctra Session
   - Select the .ses file
   - Review and adjust as needed

## Examples

See the [examples directory](../examples/) for complete examples:
- `dsn_export_example.py` - DSN export examples
- `freerouting_example.py` - Freerouting runner examples
- `complete_routing_example.py` - Complete automated routing workflow with SES import

## Troubleshooting

### Common Issues

1. **Freerouting not found**
   - For Docker: Ensure Docker is installed and running
   - For JAR: Check installation with `java -jar freerouting.jar -help`
   - Set explicit path in config
   - See [FREEROUTING_SETUP.md](FREEROUTING_SETUP.md)

2. **Java errors (JAR version only)**
   - Ensure Java 21 is installed
   - Check JAVA_HOME environment variable
   - Increase memory if needed
   - Consider using Docker version instead

3. **Docker errors**
   - Ensure Docker daemon is running
   - Check user has Docker permissions
   - Verify Docker can pull images

3. **Routing failures**
   - Simplify design rules
   - Increase timeout
   - Try different effort levels
   - Check for unroutable nets

4. **DSN export issues**
   - Ensure PCB has valid board outline
   - Check for special characters in net names
   - Verify all footprints have pads

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This module is part of Circuit Synth Core and follows the same license terms.