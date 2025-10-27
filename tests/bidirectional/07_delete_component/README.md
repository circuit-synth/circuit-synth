# Test 07: Delete Component from Circuit

## What This Tests
Validates that removing a component from Python code correctly removes it from the regenerated KiCad schematic.

## When This Situation Happens
- Developer has a circuit with multiple components (R1 and R2)
- Decides a component is no longer needed (R2)
- Removes the component from Python code
- Regenerates KiCad project to reflect the deletion

## What Should Work
- Circuit created with both R1 and R2
- Python code modified to remove R2
- Regenerated KiCad project contains only R1
- R2 is completely removed from the schematic

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/07_delete_component

# Step 1: Create a circuit with two resistors
# Create a file called two_resistors.py with:
cat > two_resistors.py << 'EOF'
from circuit_synth import circuit, Component

@circuit(name="two_resistors")
def two_resistors():
    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

if __name__ == "__main__":
    circuit_obj = two_resistors()
    circuit_obj.generate_kicad_project(project_name="two_resistors",
                                      placement_algorithm="simple",
                                      generate_pcb=True)
    print("✅ Two resistor circuit generated!")
EOF

# Step 2: Generate KiCad with both components
uv run two_resistors.py
open two_resistors/two_resistors.kicad_pro
# Verify: schematic has both R1 and R2

# Step 3: Edit the Python file to remove R2
# Comment out or delete the R2 line:
cat > two_resistors.py << 'EOF'
from circuit_synth import circuit, Component

@circuit(name="two_resistors")
def two_resistors():
    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    # r2 removed - component deleted from circuit

if __name__ == "__main__":
    circuit_obj = two_resistors()
    circuit_obj.generate_kicad_project(project_name="two_resistors",
                                      placement_algorithm="simple",
                                      generate_pcb=True)
    print("✅ Two resistor circuit generated!")
EOF

# Step 4: Regenerate KiCad
uv run two_resistors.py

# Step 5: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro

# Step 6: Verify schematic now has only R1
#   - R1 (10k) - still present
#   - R2 - completely removed from schematic
```

## Expected Result

- ✅ Initial KiCad project has both R1 and R2
- ✅ After removing R2 from Python and regenerating, KiCad has only R1
- ✅ R1 position preserved (not moved)
- ✅ R2 is completely removed from the schematic
- ✅ No orphaned connections or references to R2
