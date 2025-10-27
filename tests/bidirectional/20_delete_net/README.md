# Test 20: Delete Net Connection

## What This Tests

Validates that removing a connection (net) between components in Python code correctly removes it from the regenerated KiCad schematic while preserving the components.

## When This Situation Happens

- Developer has two connected components in circuit
- Decides the connection is no longer needed
- Removes Net() from Python code
- Regenerates KiCad expecting connection to be removed while components remain

## What Should Work

1. Initial circuit with two connected resistors (R1, R2) generates valid KiCad project with wire
2. Python code modified to remove the Net connection
3. Regenerated KiCad schematic shows components but no wire between them
4. Both components preserved with their original positions and properties

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/20_delete_net

# Step 1: Create initial Python script with two connected resistors
cat > connected_resistors.py << 'EOF'
from circuit_synth import Circuit, Component, Net

circuit = Circuit("connected_resistors")

# Two resistors with a connection
r1 = Component(symbol="Device:R", ref="R1", value="10k",
               footprint="Resistor_SMD:R_0603_1608Metric")
r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
               footprint="Resistor_SMD:R_0603_1608Metric")

# Create net connecting them
net1 = Net("connection")
net1.connect(r1["2"], r2["1"])

circuit.add_components(r1, r2)
circuit.add_nets(net1)
circuit.to_kicad()
EOF

# Step 2: Generate initial KiCad project (with connection)
uv run connected_resistors.py
open connected_resistors/connected_resistors.kicad_pro
# Verify: schematic has R1 and R2 with wire between them

# Step 3: Edit connected_resistors.py to remove the net
# Delete or comment out these lines:
#   net1 = Net("connection")
#   net1.connect(r1["2"], r2["1"])
#   circuit.add_nets(net1)

# Step 4: Regenerate KiCad project without connection
uv run connected_resistors.py

# Step 5: Open regenerated KiCad project
open connected_resistors/connected_resistors.kicad_pro

# Step 6: Verify schematic shows no wire connection
#   - R1 still present with original position
#   - R2 still present with original position
#   - No wire connecting them
#   - Both components have correct values
```

## Expected Result

- ✅ Initial KiCad project has R1 and R2 connected with wire
- ✅ After removing Net from Python and regenerating, wire disappears
- ✅ R1 and R2 components still present in schematic
- ✅ Component positions preserved (not moved)
- ✅ Component values and properties unchanged
- ✅ No connection/wire between components

## Why This Is Important

Removing nets should only affect connectivity, not components themselves. The bidirectional sync must correctly handle net deletion without corrupting or removing the components that were connected. This tests that Python Net removal translates to wire removal in KiCad.
