# Test 08: Modify Component Value

## What This Tests
Validates that changing a component's value in Python code correctly updates the value in the regenerated KiCad schematic and survives round-trip.

## When This Situation Happens
- Developer has a circuit with a resistor (R1=10k)
- Design requirements change, needs different value (R1=20k)
- Updates the value in Python code
- Regenerates KiCad and verifies value persists through import/export cycle

## What Should Work
- Original circuit has R1 with value 10k
- Python code modified to change R1 value to 20k
- Regenerated KiCad shows R1=20k
- Round-trip import back to Python preserves the 20k value

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/08_modify_value

# Step 1: Create initial circuit with R1=10k
# Create a file called resistor_circuit.py with:
cat > resistor_circuit.py << 'EOF'
from circuit_synth import circuit, Component

@circuit(name="resistor_circuit")
def resistor_circuit():
    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

if __name__ == "__main__":
    circuit_obj = resistor_circuit()
    circuit_obj.generate_kicad_project(project_name="resistor_circuit",
                                      placement_algorithm="simple",
                                      generate_pcb=True)
    print("✅ Resistor circuit generated with R1=10k")
EOF

# Step 2: Generate initial KiCad project
uv run resistor_circuit.py
open resistor_circuit/resistor_circuit.kicad_pro
# Verify: schematic shows R1 with value 10k

# Step 3: Modify Python code to change R1 value to 20k
cat > resistor_circuit.py << 'EOF'
from circuit_synth import circuit, Component

@circuit(name="resistor_circuit")
def resistor_circuit():
    r1 = Component(symbol="Device:R", ref="R1", value="20k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

if __name__ == "__main__":
    circuit_obj = resistor_circuit()
    circuit_obj.generate_kicad_project(project_name="resistor_circuit",
                                      placement_algorithm="simple",
                                      generate_pcb=True)
    print("✅ Resistor circuit generated with R1=20k")
EOF

# Step 4: Regenerate KiCad with modified value
uv run resistor_circuit.py

# Step 5: Open regenerated KiCad project
open resistor_circuit/resistor_circuit.kicad_pro
# Verify: schematic now shows R1 with value 20k

# Step 6: Test round-trip - import back to Python
uv run kicad-to-python resistor_circuit imported_circuit.py

# Step 7: Verify imported code has R1=20k
# Open imported_circuit.py - should show R1 with value="20k"

# Step 8: Generate KiCad from imported Python (round-trip test)
uv run imported_circuit.py

# Step 9: Open round-trip KiCad project and verify R1=20k persists
# The imported Python should generate a project with R1=20k
```

## Expected Result

- ✅ Initial KiCad project has R1 with value 10k
- ✅ After changing to 20k in Python and regenerating, KiCad shows R1=20k
- ✅ R1 position preserved (not moved)
- ✅ Value update is the only change
- ✅ Round-trip import preserves R1=20k
- ✅ KiCad generated from imported Python shows R1=20k
