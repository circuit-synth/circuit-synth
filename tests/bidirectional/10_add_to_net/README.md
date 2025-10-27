# Test 10: Add Component to Existing Net

## What This Tests
Validates that adding a third component to an existing connection between two components works correctly in KiCad.

## When This Situation Happens
- Developer has two components connected via a named net (R1-R2 on NET1)
- Needs to add another component to the same connection (R3)
- Modifies Python to connect R3 to the existing NET1
- Regenerates KiCad expecting all three components on the same net

## What Should Work
- Initial circuit with R1-R2 connected via NET1 generates correctly
- Python modified to add R3 connected to same NET1
- Regenerated KiCad shows all three components on the same net
- Net connections are properly maintained across all components

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/10_add_to_net

# Step 1: Create initial circuit with R1 and R2 connected via NET1
cat > two_resistors_on_net.py << 'EOF'
from circuit_synth import circuit, Component, Net

@circuit(name="two_resistors_on_net")
def two_resistors_on_net():
    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

    # Connect R1 and R2 via NET1
    net1 = Net(name="NET1")
    net1.connect(r1[1])
    net1.connect(r2[1])

if __name__ == "__main__":
    circuit_obj = two_resistors_on_net()
    circuit_obj.generate_kicad_project(project_name="two_resistors_on_net",
                                      placement_algorithm="simple",
                                      generate_pcb=True)
    print("✅ Two resistors on NET1 generated!")
EOF

# Step 2: Generate initial KiCad project
uv run two_resistors_on_net.py
open two_resistors_on_net/two_resistors_on_net.kicad_pro
# Verify: schematic shows R1 and R2 connected via NET1
# Check: NET1 label appears on the connection between components

# Step 3: Add R3 to the existing NET1
# Edit two_resistors_on_net.py to add R3:
cat > two_resistors_on_net.py << 'EOF'
from circuit_synth import circuit, Component, Net

@circuit(name="two_resistors_on_net")
def two_resistors_on_net():
    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r3 = Component(symbol="Device:R", ref="R3", value="2.2k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

    # Connect R1, R2, and R3 via NET1
    net1 = Net(name="NET1")
    net1.connect(r1[1])
    net1.connect(r2[1])
    net1.connect(r3[1])  # Added R3 to existing NET1

if __name__ == "__main__":
    circuit_obj = two_resistors_on_net()
    circuit_obj.generate_kicad_project(project_name="two_resistors_on_net",
                                      placement_algorithm="simple",
                                      generate_pcb=True)
    print("✅ Three resistors on NET1 generated!")
EOF

# Step 4: Regenerate KiCad with R3 added to NET1
uv run two_resistors_on_net.py

# Step 5: Open regenerated KiCad project
open two_resistors_on_net/two_resistors_on_net.kicad_pro

# Step 6: Verify all three components on same net
# Check in KiCad schematic:
#   - R1, R2, R3 all present
#   - All three connected to NET1
#   - NET1 label appears on connections
#   - No orphaned nets or connections
#   - R1 and R2 positions preserved (not moved)
#   - R3 placed without overlapping existing components
```

## Expected Result

- ✅ Initial KiCad project has R1 and R2 connected via NET1
- ✅ After adding R3 and regenerating, all three resistors on NET1
- ✅ NET1 connections properly maintained across all components
- ✅ R1 and R2 positions preserved (not moved)
- ✅ R3 placed in available space
- ✅ No duplicate nets or connection issues
- ✅ KiCad schematic shows clear NET1 connections to all three components

## Why This Is Important

Real circuits often require adding components to existing connections. This test validates that the net system correctly handles growing connections and maintains proper electrical relationships across multiple components.
