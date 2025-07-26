# KiCad PCB API

A comprehensive Python API for creating and manipulating KiCad PCB files with advanced features including footprint library integration, placement algorithms, and design rule checking.

## Overview

This API provides complete PCB design capabilities for working with KiCad PCB files (.kicad_pcb) without requiring KiCad to be running. It uses S-expression parsing to directly read and write PCB files and includes advanced features like:

- **Footprint Library Integration**: Search and use KiCad's extensive footprint libraries
- **Advanced Placement Algorithms**: Hierarchical, force-directed, and connectivity-driven placement
- **Design Rule Checking**: Integrated DRC with KiCad CLI
- **Board Features**: Outlines, zones, and multi-layer support
- **Manufacturing Export**: Gerber and drill file generation
- **Auto-Routing**: Integration with Freerouting for automatic PCB routing

## Installation

The API is part of the Circuit Synth project and uses the existing `sexpdata` dependency.

## Basic Usage

```python
from circuit_synth.kicad_api.pcb import PCBBoard

# Create a new PCB
pcb = PCBBoard()

# Add a footprint
pcb.add_footprint("R1", "Resistor_SMD:R_0603_1608Metric", x=50, y=50, value="10k")

# Move a footprint
pcb.move_footprint("R1", x=60, y=50)

# Remove a footprint
pcb.remove_footprint("R1")

# Save the PCB
pcb.save("output.kicad_pcb")
```

## API Reference

### PCBBoard Class

The main class for working with PCB files.

#### Constructor

```python
pcb = PCBBoard(filepath=None)
```

- `filepath` (optional): Path to an existing PCB file to load

#### Methods

##### add_footprint()

Add a footprint to the PCB.

```python
footprint = pcb.add_footprint(
    reference="R1",
    footprint_lib="Resistor_SMD:R_0603_1608Metric",
    x=50,
    y=50,
    rotation=0.0,
    value="10k",
    layer="F.Cu"
)
```

Parameters:
- `reference` (str): Component reference (e.g., "R1", "C1", "U1")
- `footprint_lib` (str): Footprint library ID (e.g., "Resistor_SMD:R_0603_1608Metric")
- `x` (float): X position in millimeters
- `y` (float): Y position in millimeters
- `rotation` (float, optional): Rotation in degrees (default: 0.0)
- `value` (str, optional): Component value (e.g., "10k", "100nF")
- `layer` (str, optional): PCB layer (default: "F.Cu" for front copper)

Returns: The created Footprint object

##### move_footprint()

Move a footprint to a new position.

```python
success = pcb.move_footprint("R1", x=60, y=50, rotation=90)
```

Parameters:
- `reference` (str): Component reference to move
- `x` (float): New X position in millimeters
- `y` (float): New Y position in millimeters
- `rotation` (float, optional): New rotation in degrees

Returns: True if footprint was found and moved, False otherwise

##### remove_footprint()

Remove a footprint from the PCB.

```python
success = pcb.remove_footprint("R1")
```

Parameters:
- `reference` (str): Component reference to remove

Returns: True if footprint was found and removed, False otherwise

##### save()

Save the PCB to a file.

```python
pcb.save("output.kicad_pcb")
```

Parameters:
- `filepath` (str or Path): Path to save the PCB file

##### load()

Load a PCB from a file.

```python
pcb.load("existing.kicad_pcb")
```

Parameters:
- `filepath` (str or Path): Path to the PCB file to load

#### Utility Methods

##### list_footprints()

Get a list of all footprints on the board.

```python
footprints = pcb.list_footprints()
# Returns: [("R1", "10k", 50.0, 50.0), ("C1", "100nF", 60.0, 50.0)]
```

Returns: List of tuples (reference, value, x, y)

##### get_footprint()

Get a footprint by reference.

```python
footprint = pcb.get_footprint("R1")
```

Returns: Footprint object if found, None otherwise

##### update_footprint_value()

Update the value of a footprint.

```python
success = pcb.update_footprint_value("R1", "4.7k")
```

Returns: True if footprint was found and updated, False otherwise

##### get_board_info()

Get general information about the board.

```python
info = pcb.get_board_info()
# Returns: {
#     'version': 20241229,
#     'generator': 'pcbnew',
#     'footprint_count': 2,
#     'net_count': 3,
#     ...
# }
```

#### Connectivity Methods

##### get_ratsnest()

Get the ratsnest (unrouted connections) for the board.

```python
ratsnest = pcb.get_ratsnest()
# Returns: [
#     {
#         'from_ref': 'R1',
#         'from_pad': '2',
#         'to_ref': 'R2',
#         'to_pad': '1',
#         'net_name': 'Net-(R1-Pad2)',
#         'net_number': 1,
#         'distance': 10.5
#     },
#     ...
# ]
```

##### get_connections()

Get all connections for a specific component.

```python
connections = pcb.get_connections("R1")
# Returns: [
#     {
#         'pad': '2',
#         'net': 1,
#         'net_name': 'Net-(R1-Pad2)',
#         'connected_to': [
#             {'reference': 'R2', 'pad': '1', 'value': '2.2k'}
#         ]
#     }
# ]
```

##### connect_pads()

Connect two pads with a net.

```python
success = pcb.connect_pads("R1", "2", "R2", "1", "RESISTOR_NET")
```

Parameters:
- `ref1` (str): First component reference
- `pad1` (str): First component pad number
- `ref2` (str): Second component reference
- `pad2` (str): Second component pad number
- `net_name` (str, optional): Net name (auto-generated if not provided)

Returns: True if connection was made, False otherwise

##### disconnect_pad()

Disconnect a pad from its net.

```python
success = pcb.disconnect_pad("R1", "2")
```

Returns: True if pad was disconnected, False otherwise

##### get_net_info()

Get information about a specific net.

```python
net_info = pcb.get_net_info("RESISTOR_NET")
# Returns: {
#     'number': 1,
#     'name': 'RESISTOR_NET',
#     'pad_count': 2,
#     'connected_pads': [
#         {
#             'reference': 'R1',
#             'pad': '2',
#             'value': '10k',
#             'position': {'x': 50.825, 'y': 50}
#         },
#         ...
#     ]
# }
```

#### Routing Methods

##### add_track()

Add a track (copper trace) to the PCB.

```python
track = pcb.add_track(start_x=50, start_y=50, end_x=60, end_y=50,
                      width=0.25, layer="F.Cu", net=1)
```

Parameters:
- `start_x`, `start_y`: Starting position in mm
- `end_x`, `end_y`: Ending position in mm
- `width` (float, optional): Track width in mm (default: 0.25)
- `layer` (str, optional): PCB layer (default: "F.Cu")
- `net` (int, optional): Net number

Returns: The created Track object

##### route_connection()

Route a connection between two pads with a track.

```python
tracks = pcb.route_connection("R1", "2", "R2", "1", width=0.3, layer="F.Cu")
```

Returns: List of created tracks

##### route_ratsnest()

Automatically route all connections in the ratsnest.

```python
tracks = pcb.route_ratsnest(width=0.25, layer="F.Cu")
```

Returns: List of all created tracks

##### add_via()

Add a via to the PCB.

```python
via = pcb.add_via(x=55, y=50, size=0.8, drill=0.4, net=1)
```

Parameters:
- `x`, `y`: Position in mm
- `size` (float, optional): Via diameter in mm (default: 0.8)
- `drill` (float, optional): Drill diameter in mm (default: 0.4)
- `net` (int, optional): Net number
- `layers` (list, optional): Layers to connect (default: ["F.Cu", "B.Cu"])

Returns: The created Via object

##### get_tracks()

Get all tracks on the board.

```python
tracks = pcb.get_tracks()
```

Returns: List of Track objects

##### clear_tracks()

Remove all tracks from the board.

```python
pcb.clear_tracks()
```

#### Placement Methods

##### auto_place_components()

Automatically place components using advanced algorithms.

```python
pcb.auto_place_components(algorithm="connectivity_driven", **kwargs)
```

Parameters:
- `algorithm` (str): Placement algorithm to use
  - `"hierarchical"`: Groups by schematic hierarchy
  - `"force_directed"`: Physics-based spring forces
  - `"connectivity_driven"`: Optimizes by connection patterns
- `**kwargs`: Algorithm-specific parameters

**Hierarchical Placement Parameters:**
- `component_spacing` (float): Minimum spacing between components (default: 2.0mm)
- `group_spacing` (float): Spacing between hierarchical groups (default: 5.0mm)

**Force-Directed Placement Parameters:**
- `iterations` (int): Number of simulation iterations (default: 100)
- `temperature` (float): Initial temperature for annealing (default: 100.0)
- `spring_constant` (float): Spring force strength (default: 0.1)
- `repulsion_constant` (float): Repulsion force strength (default: 1000.0)
- `gravity_constant` (float): Gravity toward center (default: 0.01)
- `min_distance` (float): Minimum component distance (default: 2.0mm)

**Connectivity-Driven Placement Parameters:**
- `component_spacing` (float): Minimum spacing (default: 2.0mm)
- `cluster_spacing` (float): Spacing between clusters (default: 5.0mm)
- `critical_net_weight` (float): Weight for power/ground/clock nets (default: 2.0)
- `crossing_penalty` (float): Penalty for crossing connections (default: 1.5)

##### get_placement_bbox()

Get the bounding box of all placed components.

```python
bbox = pcb.get_placement_bbox()
# Returns: (min_x, min_y, max_x, max_y) or None
```

#### Board Outline Methods

##### set_board_outline_rect()

Set a rectangular board outline.

```python
pcb.set_board_outline_rect(x=0, y=0, width=100, height=80, corner_radius=0)
```

Parameters:
- `x`, `y`: Top-left corner position in mm
- `width`, `height`: Board dimensions in mm
- `corner_radius` (float, optional): Corner radius for rounded rectangles

##### set_board_outline_polygon()

Set a polygonal board outline.

```python
points = [(10, 10), (90, 10), (90, 90), (10, 90)]
pcb.set_board_outline_polygon(points)
```

Parameters:
- `points`: List of (x, y) tuples defining the polygon vertices

##### get_board_outline()

Get the current board outline.

```python
outline = pcb.get_board_outline()
# Returns: {'rect': {...}} or {'polygon': [...]} or None
```

#### Zone Methods

##### add_zone()

Add a zone (copper pour) to the PCB.

```python
zone = pcb.add_zone(polygon, layer, net_name="", filled=True)
```

Parameters:
- `polygon`: List of (x, y) tuples defining the zone boundary
- `layer` (str): Layer(s) for the zone (e.g., "F.Cu", "B.Cu", "F.Cu B.Cu")
- `net_name` (str, optional): Net to connect the zone to
- `filled` (bool, optional): Whether zone is filled (default: True)

Returns: The created Zone object

##### get_zones()

Get all zones on a specific layer.

```python
zones = pcb.get_zones(layer="F.Cu")
```

##### remove_zone()

Remove a zone by UUID.

```python
success = pcb.remove_zone(zone_uuid)
```

#### Footprint Library Methods

##### search_footprints()

Search for footprints in the library cache.

```python
results = pcb.search_footprints(query="0603", filters={
    "footprint_type": "SMD",
    "pad_count": {"min": 2, "max": 2}
})
```

Parameters:
- `query` (str): Search query for name/description/tags
- `filters` (dict, optional): Filter criteria
  - `footprint_type`: "SMD", "THT", or "Mixed"
  - `pad_count`: Exact number or {"min": x, "max": y}
  - `library`: Specific library name

Returns: List of FootprintInfo objects

##### add_footprint_from_library()

Add a footprint from the KiCad library.

```python
footprint = pcb.add_footprint_from_library(
    "Resistor_SMD:R_0603_1608Metric",
    "R1", x=50, y=50, rotation=0, value="10k"
)
```

Parameters:
- `footprint_id` (str): Library footprint ID (library:name)
- Other parameters same as `add_footprint()`

##### get_footprint_info()

Get detailed information about a library footprint.

```python
info = pcb.get_footprint_info("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
print(f"Pads: {info.pad_count}, Size: {info.body_size}")
```

##### list_available_libraries()

List all available footprint libraries.

```python
libraries = pcb.list_available_libraries()
```

#### Design Rule Checking Methods

##### run_drc()

Run KiCad design rule check.

```python
result = pcb.run_drc(output_format="json")
```

Parameters:
- `output_format` (str, optional): "json" or "report" (default: "json")

Returns: DRCResult object with violations, warnings, and unconnected items

##### check_basic_rules()

Perform basic rule checking without KiCad.

```python
issues = pcb.check_basic_rules()
# Returns: {
#     'overlapping_footprints': [...],
#     'off_board_components': [...],
#     'missing_connections': [...]
# }
```

##### export_gerbers()

Export Gerber files for manufacturing.

```python
pcb.export_gerbers(output_dir="gerbers/", layers=None)
```

Parameters:
- `output_dir` (str): Directory for output files
- `layers` (list, optional): Specific layers to export

##### export_drill()

Export drill files.

```python
pcb.export_drill(output_dir="drill/", format="excellon")
```

## Examples

### Creating a Simple PCB

```python
from circuit_synth.kicad_api.pcb import PCBBoard

# Create a new PCB
pcb = PCBBoard()

# Add some components
pcb.add_footprint("R1", "Resistor_SMD:R_0805_2012Metric", x=100, y=100, value="10k")
pcb.add_footprint("R2", "Resistor_SMD:R_0805_2012Metric", x=110, y=100, value="22k")
pcb.add_footprint("C1", "Capacitor_SMD:C_0805_2012Metric", x=120, y=100, value="100nF")
pcb.add_footprint("U1", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", x=130, y=100, value="NE555")

# Save the PCB
pcb.save("my_circuit.kicad_pcb")
```

### Modifying an Existing PCB

```python
from circuit_synth.kicad_api.pcb import PCBBoard

# Load existing PCB
pcb = PCBBoard("existing_board.kicad_pcb")

# List current footprints
print("Current footprints:")
for ref, value, x, y in pcb.list_footprints():
    print(f"  {ref}: {value} at ({x}, {y})")

# Move a component
pcb.move_footprint("U1", x=150, y=120, rotation=90)

# Update a value
pcb.update_footprint_value("R1", "4.7k")

# Add a new component
pcb.add_footprint("C2", "Capacitor_SMD:C_0603_1608Metric", x=140, y=100, value="10uF")

# Save the modified PCB
pcb.save("modified_board.kicad_pcb")
```

### Working with Connections (Ratsnest)

```python
from circuit_synth.kicad_api.pcb import PCBBoard

# Create a PCB with connected components
pcb = PCBBoard()

# Add components
pcb.add_footprint("R1", "Resistor_SMD:R_0603_1608Metric", x=50, y=50, value="1k")
pcb.add_footprint("R2", "Resistor_SMD:R_0603_1608Metric", x=60, y=50, value="2.2k")
pcb.add_footprint("C1", "Capacitor_SMD:C_0603_1608Metric", x=70, y=50, value="100nF")

# Connect components
pcb.connect_pads("R1", "2", "R2", "1", "RESISTOR_NET")  # R1 pin 2 to R2 pin 1
pcb.connect_pads("R2", "2", "C1", "1", "RC_NET")       # R2 pin 2 to C1 pin 1

# Get ratsnest (unrouted connections)
ratsnest = pcb.get_ratsnest()
for conn in ratsnest:
    print(f"{conn['from_ref']}.{conn['from_pad']} -> {conn['to_ref']}.{conn['to_pad']}")
    print(f"  Net: {conn['net_name']}, Distance: {conn['distance']}mm")

# Query connections for a component
connections = pcb.get_connections("R2")
for conn in connections:
    print(f"R2 pad {conn['pad']} connects to:")
    for other in conn['connected_to']:
        print(f"  - {other['reference']}.{other['pad']}")

# Get net information
net_info = pcb.get_net_info("RESISTOR_NET")
print(f"Net '{net_info['name']}' has {net_info['pad_count']} pads")

# Disconnect a pad
pcb.disconnect_pad("R2", "1")

# Save the PCB
pcb.save("connected_circuit.kicad_pcb")
```

### Routing Tracks

```python
from circuit_synth.kicad_api.pcb import PCBBoard

# Create a routed PCB
pcb = PCBBoard()

# Add components
pcb.add_footprint("R1", "Resistor_SMD:R_0603_1608Metric", x=50, y=50, value="1k")
pcb.add_footprint("R2", "Resistor_SMD:R_0603_1608Metric", x=60, y=50, value="2.2k")

# Connect pads
pcb.connect_pads("R1", "2", "R2", "1", "NET1")

# Route the connection
tracks = pcb.route_connection("R1", "2", "R2", "1", width=0.25)
print(f"Created {len(tracks)} track(s)")

# Or auto-route all connections
all_tracks = pcb.route_ratsnest(width=0.3, layer="F.Cu")
print(f"Auto-routed {len(all_tracks)} connections")

# Manual routing with multiple segments
track1 = pcb.add_track(50, 50, 55, 50, width=0.4, net=1)  # Horizontal
track2 = pcb.add_track(55, 50, 55, 45, width=0.4, net=1)  # Vertical
track3 = pcb.add_track(55, 45, 60, 45, width=0.4, net=1)  # Horizontal

# Add a via
via = pcb.add_via(55, 45, size=0.8, drill=0.4, net=1)

# Save the routed PCB
pcb.save("routed_circuit.kicad_pcb")
```

### Board Outline and Zones

```python
from circuit_synth.kicad_api.pcb import PCBBoard

# Create PCB with board outline
pcb = PCBBoard()

# Set rectangular board outline
pcb.set_board_outline_rect(0, 0, 100, 80)  # 100x80mm board

# Or create a custom polygon outline
hexagon = [(50, 10), (90, 30), (90, 70), (50, 90), (10, 70), (10, 30)]
pcb.set_board_outline_polygon(hexagon)

# Add ground plane zone
ground_polygon = [(5, 5), (95, 5), (95, 75), (5, 75)]
pcb.add_zone(ground_polygon, "B.Cu", "GND", filled=True)

# Add keepout zone
keepout = [(40, 40), (60, 40), (60, 60), (40, 60)]
pcb.add_zone(keepout, "F.Cu B.Cu", "", filled=False)

pcb.save("board_with_zones.kicad_pcb")
```

### Footprint Library Integration

```python
from circuit_synth.kicad_api.pcb import PCBBoard

pcb = PCBBoard()

# Search for footprints
results = pcb.search_footprints("0603", filters={"footprint_type": "SMD"})
for info in results[:5]:
    print(f"{info.library}:{info.name} - {info.description}")

# Add footprint from library
pcb.add_footprint_from_library(
    "Resistor_SMD:R_0603_1608Metric",
    "R1", 50, 50, value="10k"
)

# Get detailed footprint information
info = pcb.get_footprint_info("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
print(f"Pads: {info.pad_count}, Size: {info.body_size}")

# List available libraries
libraries = pcb.list_available_libraries()
print(f"Found {len(libraries)} footprint libraries")
```

### Advanced Placement Algorithms

```python
from circuit_synth.kicad_api.pcb import PCBBoard

pcb = PCBBoard()
pcb.set_board_outline_rect(0, 0, 100, 80)

# Add components
pcb.add_footprint_from_library("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "U1", 50, 40)
pcb.add_footprint_from_library("Resistor_SMD:R_0603_1608Metric", "R1", 30, 40)
pcb.add_footprint_from_library("Capacitor_SMD:C_0603_1608Metric", "C1", 70, 40)

# Connect components
pcb.connect_pads("U1", "8", "C1", "1", "VCC")
pcb.connect_pads("U1", "3", "R1", "1", "SIGNAL")

# Apply hierarchical placement
pcb.auto_place_components(
    algorithm="hierarchical",
    component_spacing=2.0,
    group_spacing=5.0
)

# Or use force-directed placement
pcb.auto_place_components(
    algorithm="force_directed",
    iterations=200,
    temperature=80.0,
    spring_constant=0.15
)

# Or use connectivity-driven placement (NEW!)
pcb.auto_place_components(
    algorithm="connectivity_driven",
    critical_net_weight=2.5,    # Prioritize power/ground nets
    crossing_penalty=1.8        # Minimize crossing connections
)

pcb.save("auto_placed.kicad_pcb")
```

### Design Rule Checking and Manufacturing

```python
from circuit_synth.kicad_api.pcb import PCBBoard

pcb = PCBBoard("my_design.kicad_pcb")

# Run design rule check
result = pcb.run_drc()
print(f"DRC found {result.total_issues} issues:")
for issue in result.issues:
    print(f"  - {issue.severity}: {issue.description}")

# Export manufacturing files
pcb.export_gerbers("output/gerbers/")
pcb.export_drill("output/drill/")
pcb.export_pick_and_place("output/assembly/")

# Basic rule checking without KiCad
basic_issues = pcb.check_basic_rules()
for category, issues in basic_issues.items():
    print(f"{category}: {len(issues)} issues")
```

## Supported Features

### Basic Operations
- ✅ Load existing PCB files (KiCad 9 format)
- ✅ Create new PCB files from scratch
- ✅ Add footprints with position and rotation
- ✅ Move footprints
- ✅ Remove footprints
- ✅ Update component values
- ✅ List all footprints
- ✅ Query board information

### Connectivity Features
- ✅ Get ratsnest (unrouted connections)
- ✅ Query component connections
- ✅ Connect pads with nets
- ✅ Disconnect pads from nets
- ✅ Get net information
- ✅ Automatic pad creation for standard footprints

### Routing Features
- ✅ Add tracks (copper traces) between pads
- ✅ Route individual connections
- ✅ Auto-route all ratsnest connections
- ✅ Add vias for layer transitions
- ✅ Manual track routing with segments
- ✅ Track management (remove, clear)
- ✅ Auto-routing with Freerouting integration

### Board Features
- ✅ Define rectangular board outlines
- ✅ Define polygonal board outlines
- ✅ Add edge cut lines
- ✅ Create zones (copper pours)
- ✅ Multi-layer zone support
- ✅ Keepout zones

### Footprint Library Integration
- ✅ Search KiCad footprint libraries
- ✅ Filter by type, pad count, size
- ✅ Add footprints from libraries
- ✅ Get detailed footprint information
- ✅ List available libraries
- ✅ Lazy-loading for performance

### Advanced Placement Algorithms
- ✅ Hierarchical placement (group by schematic hierarchy)
- ✅ Force-directed placement (physics-based optimization)
- ✅ Connectivity-driven placement (optimize by connection patterns)
- ✅ Configurable spacing and parameters
- ✅ Locked component support

### Design Rule Checking
- ✅ Integrated KiCad DRC via CLI
- ✅ Basic rule checking without KiCad
- ✅ Export manufacturing files (Gerbers, drill, pick & place)
- ✅ JSON and report output formats

### Auto-Routing with Freerouting
- ✅ Export PCB to DSN format for Freerouting
- ✅ Docker-based Freerouting integration
- ✅ Import routed SES files back to PCB
- ✅ Automatic via placement
- ✅ Multi-layer routing support

## Auto-Routing Usage

The PCB API includes integration with Freerouting for automatic PCB routing. This feature uses Docker to avoid Java compatibility issues.

### Basic Auto-Routing Example

```python
from circuit_synth_core.kicad_api.pcb import PCBBoard
from circuit_synth_core.kicad_api.pcb.routing import FreeroutingRunner

# Create or load a PCB with components and connections
pcb = PCBBoard()
pcb.add_footprint("R1", "Resistor_SMD:R_0603_1608Metric", x=50, y=50, value="10k")
pcb.add_footprint("R2", "Resistor_SMD:R_0603_1608Metric", x=60, y=50, value="22k")
pcb.connect_pads("R1", "2", "R2", "1", "NET1")

# Save the PCB
pcb.save("unrouted.kicad_pcb")

# Run auto-routing
runner = FreeroutingRunner()
success = runner.route_pcb("unrouted.kicad_pcb", "routed.kicad_pcb")

if success:
    print("PCB successfully routed!")
    # Load the routed PCB
    routed_pcb = PCBBoard("routed.kicad_pcb")
else:
    print("Routing failed")
```

### Advanced Auto-Routing Options

```python
# Configure routing parameters
success = runner.route_pcb(
    input_pcb="unrouted.kicad_pcb",
    output_pcb="routed.kicad_pcb",
    passes=5,              # Number of optimization passes
    via_costs=50,          # Cost for using vias
    timeout=300,           # Timeout in seconds
    docker_image="freerouting/freerouting:latest"
)
```

### Manual DSN/SES Workflow

For more control over the routing process:

```python
from circuit_synth_core.kicad_api.pcb.routing import DSNExporter, SESImporter

# Export to DSN
exporter = DSNExporter()
exporter.export_pcb("my_pcb.kicad_pcb", "my_pcb.dsn")

# Run Freerouting manually or with Docker
# ... routing happens here ...

# Import the routed result
importer = SESImporter()
importer.import_to_pcb("my_pcb.ses", "my_pcb.kicad_pcb", "routed_pcb.kicad_pcb")
```

### Setup Requirements

1. **Docker Installation**: Required for running Freerouting
   - Install Docker Desktop (Windows/Mac) or Docker Engine (Linux)
   - Ensure Docker daemon is running

2. **Pull Freerouting Image**:
   ```bash
   docker pull freerouting/freerouting:latest
   ```

For detailed setup instructions, see the [routing documentation](routing/README.md).

## Limitations

This API currently does not support:
- Complex routing algorithms (45-degree routing, push and shove)
- Differential pair routing
- Length matching
- Thermal relief connections
- 3D model management
- Custom design rules

These features may be added in future versions.

## File Format

The API generates PCB files compatible with KiCad 9.0 (version 20241229). Files can be opened directly in KiCad's PCB editor (pcbnew).

## Technical Details

- Uses S-expression parsing via the `sexpdata` library
- All coordinates are in millimeters
- Rotation is in degrees (counterclockwise)
- Default layer is "F.Cu" (front copper)
- Generates unique UUIDs for all elements