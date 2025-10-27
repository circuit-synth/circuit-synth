# Test 20: Delete Net Connection

## What This Tests
Validates that removing a connection (net) between components in Python code correctly removes it from the regenerated KiCad schematic while preserving the components.

## When This Situation Happens
- Developer has two connected components in circuit
- Decides the connection is no longer needed
- Removes Net() from Python code
- Regenerates KiCad expecting connection to be removed while components remain

## What Should Work
- Initial circuit with two connected resistors (R1, R2) generates valid KiCad project with wire
- Python code modified to remove the Net connection
- Regenerated KiCad schematic shows components but no wire between them
- Both components preserved with their original positions and properties

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/20_delete_net

# Step 1: Generate initial KiCad project (with connection)
uv run connected_resistors.py
open connected_resistors/connected_resistors.kicad_pro
# Verify: schematic has R1 and R2 with wire between them

# Step 2: Edit connected_resistors.py to remove the net
# Delete or comment out these lines:
#   net1 = Net("connection")
#   net1.connect(r1["2"], r2["1"])
#   circuit.add_nets(net1)

# Step 3: Regenerate KiCad project without connection
uv run connected_resistors.py

# Step 4: Open regenerated KiCad project
open connected_resistors/connected_resistors.kicad_pro
# Verify: R1 and R2 still present, no wire connecting them
```

## Expected Result

- ✅ Initial KiCad project has R1 and R2 connected with wire
- ✅ After removing Net from Python and regenerating, wire disappears
- ✅ R1 and R2 components still present in schematic
- ✅ Component positions preserved (not moved)
- ✅ Component values and properties unchanged
- ✅ No connection/wire between components
