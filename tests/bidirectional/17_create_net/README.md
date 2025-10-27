# Test 17: Create Net Connection

## What This Tests
Validates that creating a connection (net) between two components in Python code correctly appears in the generated KiCad schematic.

## When This Situation Happens
- Developer has two unconnected components in circuit
- Needs to connect them electrically
- Adds Net() in Python to connect component pins
- Regenerates KiCad project expecting connection to be present

## What Should Work
- Initial circuit with two unconnected resistors (R1, R2) generates valid KiCad project
- Python code modified to add Net connecting R1 pin to R2 pin
- Regenerated KiCad schematic shows electrical connection (wire) between components
- Net is properly represented with correct pin connections

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/17_create_net

# Step 1: Generate initial KiCad project (no connection)
uv run two_resistors.py
open two_resistors/two_resistors.kicad_pro
# Verify: schematic has R1 and R2 but no wire between them

# Step 2: Edit two_resistors.py to add a net connection
# Add import: from circuit_synth import Net
# Add before circuit.to_kicad():
#   net1 = Net("connection")
#   net1.connect(r1["2"], r2["1"])
#   circuit.add_nets(net1)

# Step 3: Regenerate KiCad project with connection
uv run two_resistors.py

# Step 4: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro
# Verify: wire connecting R1 pin 2 to R2 pin 1, net name "connection" visible
```

## Expected Result

- ✅ Initial KiCad project has R1 and R2 unconnected
- ✅ After adding Net in Python and regenerating, wire appears
- ✅ Wire connects R1 pin 2 to R2 pin 1
- ✅ Both components preserved with correct positions
- ✅ Net name "connection" visible in schematic
