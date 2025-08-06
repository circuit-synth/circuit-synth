# Existing Project Integration Demo

**Addressing forum feedback**: "The example in the readme seems to show starting a new project from scratch. You might want to show how it works with existing projects and workflows."

This demo shows how circuit-synth can import existing KiCad projects to Python. Note: Bidirectional sync (updating existing projects) is experimental and has limitations.

## Workflow Demonstration

### Step 1: Import Existing KiCad Project
```python
# Import existing KiCad schematic to Python
from circuit_synth.io import import_kicad_project

circuit = import_kicad_project("my_existing_project.kicad_sch")
```

### Step 2: Modify in Python
```python 
# Add new functionality using Python
@circuit(name="New_Feature")
def add_sensor_interface(vcc, gnd):
    # Add I2C temperature sensor
    sensor = Component(
        symbol="Sensor_Temperature:DS18B20",
        ref="U",
        footprint="Package_TO_SOT_THT:TO-92_Inline"
    )
    # Connect to existing nets
    sensor["VDD"] += vcc
    sensor["GND"] += gnd
    return sensor

# Integrate with existing circuit
existing_circuit.add_subcircuit(add_sensor_interface(vcc_3v3, gnd))
```

### Step 3: Generate New Project (Recommended)
```python
# Generate new KiCad project with added functionality
existing_circuit.generate_kicad_project("enhanced_circuit")
```

**Note**: Updating existing KiCad projects in-place is experimental. The recommended workflow is:
1. Import existing KiCad → Python ✅ (works well)
2. Modify circuit in Python ✅ (works well)  
3. Generate new KiCad project ✅ (works well)
4. Manually merge changes if needed

## Current Limitations

⚠️ **Bidirectional sync limitations:**
- Project updates (vs new generation) are experimental
- Manual component placement may not be preserved
- Custom routing and traces are not preserved
- Works best for generating new projects from imported circuits

## Files in This Demo

- `before/` - Original KiCad project (simple LED circuit)
- `modify_existing.py` - Python script that adds functionality
- `after/` - Updated KiCad project (LED + sensor)
- `comparison.md` - Side-by-side diff showing changes

This addresses the "seamless KiCad integration" claim with concrete proof.