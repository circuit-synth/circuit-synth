# PCB Generation Module

This module provides PCB generation functionality for Circuit Synth, creating PCB files from circuit definitions with automatic hierarchical component placement.

## Overview

The PCB generation module integrates with the schematic generation workflow to automatically create PCB files with components placed according to their hierarchical structure. It leverages the existing KiCad PCB API and placement algorithms.

## Features

- **Automatic PCB Generation**: Generate PCB files directly from circuit definitions
- **Hierarchical Placement**: Components are grouped and placed based on circuit hierarchy
- **Multiple Placement Algorithms**: Support for hierarchical, force-directed, and connectivity-driven placement
- **Footprint Mapping**: Automatic mapping from schematic symbols to PCB footprints
- **Board Outline Generation**: Automatic board outline creation
- **Integration with Schematic Flow**: Seamless integration with existing schematic generation

## Usage

### Basic Usage with Schematic Generation

```python
from circuit_synth_core.kicad.sch_gen.main_generator import SchematicGenerator

# Generate schematic and PCB together
generator = SchematicGenerator("output_dir", "my_project")
generator.generate_project("circuit.json", generate_pcb=True)
```

### Standalone PCB Generation

```python
from circuit_synth_core.kicad.pcb_gen import PCBGenerator

# Generate PCB from existing schematics
pcb_gen = PCBGenerator("project_dir", "my_project")
pcb_gen.generate_pcb(
    placement_algorithm="hierarchical",
    board_width=100.0,
    board_height=100.0,
    component_spacing=2.0,
    group_spacing=5.0
)
```

### Custom Footprint Mapping

```python
# Set custom footprint mappings
pcb_gen = PCBGenerator("project_dir", "my_project")
pcb_gen.set_footprint_mapping("Device:R", "Resistor_SMD:R_0805_2012Metric")
pcb_gen.set_footprint_mapping("Device:C", "Capacitor_SMD:C_0805_2012Metric")
pcb_gen.generate_pcb()
```

## Placement Algorithms

### Hierarchical Placement
Groups components by their schematic hierarchy and places them using a bounding box packing algorithm.

```python
pcb_gen.generate_pcb(
    placement_algorithm="hierarchical",
    component_spacing=2.0,    # Space between components in mm
    group_spacing=5.0         # Space between hierarchical groups in mm
)
```

### Force-Directed Placement
Uses physics-based spring forces to optimize component placement based on connections.

```python
pcb_gen.generate_pcb(
    placement_algorithm="force_directed",
    iterations=200,           # Simulation iterations
    temperature=80.0,         # Initial temperature
    spring_constant=0.15      # Spring force strength
)
```

### Connectivity-Driven Placement
Optimizes placement to minimize connection crossings and total wire length.

```python
pcb_gen.generate_pcb(
    placement_algorithm="connectivity_driven",
    critical_net_weight=2.5,  # Weight for power/ground nets
    crossing_penalty=1.8      # Penalty for crossing connections
)
```

## Default Footprint Mappings

The module includes default mappings for common components:

| Symbol | Default Footprint |
|--------|------------------|
| Device:R | Resistor_SMD:R_0603_1608Metric |
| Device:C | Capacitor_SMD:C_0603_1608Metric |
| Device:L | Inductor_SMD:L_0603_1608Metric |
| Device:D | Diode_SMD:D_SOD-123 |
| Device:LED | LED_SMD:LED_0603_1608Metric |
| Device:Q_NPN_BCE | Package_TO_SOT_SMD:SOT-23 |
| Device:Q_PNP_BCE | Package_TO_SOT_SMD:SOT-23 |
| Device:Q_NMOS | Package_TO_SOT_SMD:SOT-23 |
| Device:Q_PMOS | Package_TO_SOT_SMD:SOT-23 |

## Architecture

```
PCBGenerator
├── Extract components from schematics
│   └── SchematicReader → parse .kicad_sch files
├── Map symbols to footprints
│   └── Use mapping table or guess from symbol name
├── Create PCB using PCBBoard API
│   ├── Set board outline
│   ├── Add footprints with hierarchical paths
│   └── Apply placement algorithm
└── Save .kicad_pcb file
```

## Implementation Details

### Component Extraction
- Reads all .kicad_sch files in the project directory
- Extracts component reference, library ID, value, and hierarchical path
- Filters out power symbols and other non-physical components

### Hierarchical Path Preservation
- Extracts hierarchical paths from schematic component properties
- Stores paths in PCB footprint data for placement grouping
- Enables hierarchical placement algorithm to group related components

### Footprint Mapping
- Maintains a mapping table from symbol library IDs to footprint library IDs
- Provides default mappings for common components
- Allows custom mappings via `set_footprint_mapping()`
- Falls back to guessing based on symbol naming patterns

## Limitations

Current limitations that will be addressed in future updates:

1. **Connection Extraction**: Net connectivity extraction from schematics is simplified
2. **Footprint Database**: Limited default footprint mappings
3. **Placement Constraints**: No support for user-defined placement constraints yet
4. **Multi-board Support**: Single board generation only

## Future Enhancements

- Complete net extraction for accurate ratsnest generation
- Expanded footprint mapping database
- Support for placement constraints and keep-out zones
- Multi-board projects
- Integration with external footprint assignment tools
- Custom placement rules and templates

## Examples

See the `examples/pcb_gen/` directory for complete examples:

- `create_simple_pcb.py` - Basic voltage divider with PCB generation
- `create_hierarchical_pcb.py` - Multi-level hierarchy with grouped placement