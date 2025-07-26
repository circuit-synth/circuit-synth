# KiCad Schematic API - Component Management

A comprehensive API for programmatic manipulation of KiCad schematics, focusing on component management operations. This module is designed to be modular and could potentially become its own repository.

## Overview

The KiCad Schematic API provides a high-level interface for:
- Adding, removing, moving, and modifying components
- Automatic component placement with collision detection
- Reference designator management
- Multi-unit symbol support
- Bulk operations on multiple components
- Advanced component search and filtering

## Installation

The API is part of the Circuit Synth project. Ensure you have the required dependencies:

```python
# The API uses the existing Circuit Synth infrastructure
from circuit_synth.kicad.sch_api import ComponentManager
```

## Quick Start

```python
from circuit_synth.kicad.sch_editor.schematic_reader import SchematicReader
from circuit_synth.kicad.sch_api import ComponentManager

# Load an existing schematic
reader = SchematicReader()
schematic = reader.read_schematic("my_project.kicad_sch")

# Create component manager
manager = ComponentManager(schematic)

# Add a resistor
resistor = manager.add_component(
    lib_id="Device:R",
    value="10k",
    position=(100, 50)  # Optional - auto-placed if not specified
)

# Add a capacitor with automatic placement
capacitor = manager.add_component(
    lib_id="Device:C",
    value="100nF"
)

# Update component properties
manager.update_component_property("R1", "Tolerance", "1%")

# Save the modified schematic
from circuit_synth.kicad.sch_editor.schematic_exporter import SchematicExporter
exporter = SchematicExporter(schematic)
exporter.export("my_project_modified.kicad_sch")
```

## Core Components

### ComponentManager

The main class for component operations:

```python
manager = ComponentManager(schematic)

# Add component with all options
component = manager.add_component(
    lib_id="Device:R",              # Required: Symbol library ID
    reference="R10",                # Optional: Auto-generated if not provided
    value="10k",                    # Component value
    position=(100, 50),             # Position in mm (auto-placed if None)
    rotation=90,                    # Rotation in degrees (0, 90, 180, 270)
    properties={                    # Additional properties
        "Tolerance": "1%",
        "Power": "0.25W"
    },
    footprint="Resistor_SMD:R_0603_1608Metric",
    in_bom=True,                    # Include in BOM
    on_board=True,                  # Place on board
    unit=1,                         # Unit number for multi-unit symbols
    dnp=False                       # Do Not Populate flag
)

# Get component by reference
comp = manager.get_component("R1")

# Update properties
manager.update_component_property("R1", "Value", "22k")

# Validate schematic
issues = manager.validate_schematic()
for issue in issues:
    print(f"Warning: {issue}")
```

### ReferenceManager

Handles unique reference designator generation:

```python
from circuit_synth.kicad.sch_api import ReferenceManager

ref_manager = ReferenceManager()

# Add existing references from schematic
ref_manager.add_existing_references(["R1", "R2", "C1"])

# Generate new reference
new_ref = ref_manager.generate_reference("Device:R")  # Returns "R3"

# Use preferred reference if available
ref = ref_manager.generate_reference("Device:R", preferred="R10")

# Release reference for reuse
ref_manager.release_reference("R2")
```

### PlacementEngine

Automatic component placement with multiple strategies:

```python
from circuit_synth.kicad.sch_api import PlacementEngine
from circuit_synth.kicad.sch_api.models import PlacementStrategy

engine = PlacementEngine()

# Find next position using default strategy
position = engine.find_next_position(schematic, symbol_data)

# Use specific placement strategy
position = engine.find_next_position(
    schematic, 
    symbol_data,
    strategy=PlacementStrategy.EDGE  # or GRID, CONTEXTUAL
)

# Check for collisions
collision = engine.check_collision(
    position=(100, 50),
    size=(20, 10),
    exclude_refs={"R1"}  # Exclude specific components
)

# Snap to grid
grid_pos = engine.snap_to_grid((100.5, 50.7))  # Returns (101.6, 50.8)
```

### ComponentSearch

Advanced search and filtering capabilities:

```python
from circuit_synth.kicad.sch_api import ComponentSearch
from circuit_synth.kicad.sch_api.models import SearchCriteria

search = ComponentSearch(schematic)

# Find by reference
comp = search.find_by_reference("R1")

# Find by pattern
resistors = search.find_by_reference_pattern("R*")  # All resistors
caps = search.find_by_reference_pattern(r"C\d+", use_regex=True)

# Find by value
ten_k_resistors = search.find_by_value("10k")
all_10_values = search.find_by_value("10", case_sensitive=False)

# Find by library ID
all_resistors = search.find_by_lib_id("Device:R", exact_match=True)
all_devices = search.find_by_lib_id("Device:", exact_match=False)

# Find by property
tolerance_parts = search.find_by_property("Tolerance", "1%")

# Find in area
area_components = search.find_in_area(x1=0, y1=0, x2=100, y2=100)

# Find nearest components
nearest = search.find_nearest(x=50, y=50, count=5, max_distance=100)

# Complex search with criteria
criteria = SearchCriteria(
    reference_pattern="R*",
    value_pattern="*k",
    property_filters={"Tolerance": "1%"}
)
results = search.find_by_criteria(criteria)

# Get statistics
stats = search.get_statistics()
print(f"Total components: {stats['total_components']}")
print(f"By type: {stats['components_by_type']}")
```

### BulkOperations

Operations on multiple components:

```python
from circuit_synth.kicad.sch_api import BulkOperations

bulk = BulkOperations(manager)

# Move multiple components
components = [comp1, comp2, comp3]
results = bulk.move_components(
    components,
    delta=(10, 20),  # Move by 10mm right, 20mm down
    maintain_relative_positions=True
)

# Align components
results = bulk.align_components(
    components,
    alignment="horizontal",  # or "vertical", "grid"
    spacing=25.4,  # 1 inch spacing
    reference_component=comp1  # Optional reference
)

# Update properties on multiple components
results = bulk.update_property_bulk(
    components,
    property_name="Tolerance",
    property_value="5%"  # Or a function: lambda comp: f"{comp.value}_tol"
)

# Distribute evenly
results = bulk.distribute_evenly(
    components,
    direction="horizontal",
    bounds=(0, 0, 200, 100)  # Optional bounds
)

# Rotate group
results = bulk.rotate_group(
    components,
    angle=90,  # 90, 180, or 270 degrees
    center=(100, 100)  # Optional rotation center
)

# Mirror group
results = bulk.mirror_group(
    components,
    axis="vertical",  # or "horizontal"
    axis_position=100  # Optional axis position
)
```

## Error Handling

The API uses custom exceptions for better error handling:

```python
from circuit_synth.kicad.sch_api import (
    ComponentNotFoundError,
    InvalidLibraryError,
    DuplicateReferenceError,
    PlacementError
)

try:
    manager.add_component("Invalid:Symbol")
except InvalidLibraryError as e:
    print(f"Invalid library: {e}")

try:
    manager.add_component("Device:R", reference="R1")  # R1 already exists
except DuplicateReferenceError as e:
    print(f"Duplicate reference: {e}")

try:
    manager.update_component_property("R99", "Value", "1k")
except ComponentNotFoundError as e:
    print(f"Component not found: {e}")
```

## Advanced Usage

### Custom Placement Strategy

```python
# Implement custom placement logic
def custom_placement(schematic, symbol_data):
    # Your custom logic here
    return (x, y)

# Use with placement engine
position = custom_placement(schematic, symbol_data)
component = manager.add_component(
    lib_id="Device:R",
    position=position
)
```

### Batch Processing

```python
# Add multiple components efficiently
components_to_add = [
    {"lib_id": "Device:R", "value": "1k"},
    {"lib_id": "Device:R", "value": "10k"},
    {"lib_id": "Device:C", "value": "100n"},
]

added_components = []
for comp_data in components_to_add:
    comp = manager.add_component(**comp_data)
    added_components.append(comp)

# Then align them
bulk.align_components(added_components, alignment="grid")
```

### Component Templates

```python
# Create reusable component templates
def add_bypass_capacitor(manager, ic_ref, value="100n"):
    """Add bypass capacitor near an IC."""
    ic = manager.get_component(ic_ref)
    if not ic:
        raise ComponentNotFoundError(ic_ref)
    
    # Place capacitor near IC
    cap_pos = (ic.position[0] + 10, ic.position[1])
    
    return manager.add_component(
        lib_id="Device:C",
        value=value,
        position=cap_pos,
        properties={
            "Description": f"Bypass capacitor for {ic_ref}"
        }
    )

# Use the template
cap = add_bypass_capacitor(manager, "U1")
```

## Best Practices

1. **Always validate** the schematic after bulk operations:
   ```python
   issues = manager.validate_schematic()
   ```

2. **Use transactions** for complex operations (future feature):
   ```python
   # Future API
   with manager.transaction():
       # Multiple operations
       # Rollback on error
   ```

3. **Snap to grid** for consistent layouts:
   ```python
   position = engine.snap_to_grid(calculated_position)
   ```

4. **Check collisions** before placement:
   ```python
   if not engine.check_collision(position, size):
       manager.add_component(lib_id, position=position)
   ```

5. **Use search before modify** to ensure components exist:
   ```python
   if search.find_by_reference("R1"):
       manager.update_component_property("R1", "Value", "10k")
   ```

## Future Enhancements

- Wire management API (Phase 3)
- Hierarchical sheet operations (Phase 4)
- Undo/redo support
- Transaction support
- Event notifications
- Plugin system for custom operations

## Contributing

This module is designed to be modular and extensible. When contributing:

1. Follow the existing patterns for new operations
2. Add comprehensive unit tests
3. Update documentation
4. Ensure KiCad file format compatibility

## License

Part of the Circuit Synth project. See main project license.