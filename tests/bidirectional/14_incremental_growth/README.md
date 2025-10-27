# Test 14: Incremental Growth (Multiple Round-Trips)

## What This Tests
Validates circuit stability through realistic development workflow - multiple cycles of edit, generate, import, edit without loss or corruption.

## When This Situation Happens
- Day 1: Developer creates basic circuit with R1, R2
- Day 2: Adds capacitor to circuit
- Day 3: Adds IC chip
- Day 4: Adds power regulation components
- Each step involves round-trips between Python and KiCad
- Circuit must accumulate components correctly without corruption

## What Should Work
- Starting circuit with 2 resistors generates correctly
- Round-trip 1: Adding capacitor preserves existing components
- Round-trip 2: Adding another resistor preserves all previous components
- Round-trip 3: Adding connections maintains component integrity
- Round-trip 4: Modifying values doesn't corrupt other properties
- All changes accumulate correctly without loss

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/14_incremental_growth

# Step 1: Create initial circuit with two resistors
cat > base_circuit.py << 'EOF'
#!/usr/bin/env python3
from circuit_synth import circuit, Component

@circuit(name="growing_circuit")
def growing_circuit():
    """Initial circuit with two resistors."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

if __name__ == "__main__":
    circuit_obj = growing_circuit()
    circuit_obj.generate_kicad_project(
        project_name="growing_circuit",
        placement_algorithm="simple",
        generate_pcb=True,
    )
    print("✅ Circuit generated successfully!")
EOF

# Step 2: Generate initial KiCad project
uv run base_circuit.py
open growing_circuit/growing_circuit.kicad_pro
# Verify: schematic has R1 and R2 only

# Step 3: Import to Python and add capacitor (Round-trip 1)
uv run kicad-to-python growing_circuit -o stage1.py
# Manually edit stage1.py to add capacitor C1

# Step 4: Regenerate and verify
uv run stage1.py
# Open growing_circuit/growing_circuit.kicad_pro
# Verify: schematic has R1, R2, and C1
# Check: R1 and R2 positions preserved

# Step 5: Import again and add resistor (Round-trip 2)
uv run kicad-to-python growing_circuit -o stage2.py
# Manually edit stage2.py to add R3

# Step 6: Regenerate and verify
uv run stage2.py
# Verify: schematic has R1, R2, C1, and R3
# Check: All previous component positions preserved

# Step 7: Import and modify value (Round-trip 3)
uv run kicad-to-python growing_circuit -o stage3.py
# Manually edit stage3.py to change R1 value to "100k"

# Step 8: Final regeneration and verification
uv run stage3.py
# Open growing_circuit/growing_circuit.kicad_pro
# Verify: All 4 components present
# Check: R1 value = "100k", positions preserved
```

## Expected Result

- ✅ Initial circuit generates with R1 and R2
- ✅ Round-trip 1: C1 added, R1 and R2 preserved
- ✅ Round-trip 2: R3 added, all previous components preserved
- ✅ Round-trip 3: R1 value modified, all components intact
- ✅ All component positions preserved through multiple cycles
- ✅ No data loss or corruption after 3 round-trips

## Why This Is Important

Real-world circuit development involves many iterations. The system must handle repeated Python ↔ KiCad cycles without accumulating errors or losing information.
