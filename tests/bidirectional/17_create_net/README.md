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
- Regenerated KiCad schematic shows electrical connection via hierarchical labels
- Net is properly represented with hierarchical labels on both pins

**Note**: Circuit-synth generates hierarchical labels (not physical wires) to establish electrical connections.

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/17_create_net

# Step 1: Generate initial KiCad project (no connection)
uv run two_resistors.py
open two_resistors/two_resistors.kicad_pro
# Verify: schematic has R1 and R2 but no wire between them

# Step 2: Edit two_resistors.py to add a net connection
# Add to imports: from circuit_synth import Net
# Add inside function after component definitions:
#   net1 = Net(name="NET1")
#   net1 += r1[2]
#   net1 += r2[1]

# Step 3: Regenerate KiCad project with connection
uv run two_resistors.py

# Step 4: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro
# Verify:
#   - Hierarchical label "NET1" on R1 pin 2 (small square flag)
#   - Hierarchical label "NET1" on R2 pin 1 (small square flag)
#   - NO physical wire between components
#   - Electrical connection established by matching label names
```

## Expected Result

- ✅ Initial KiCad project has R1 and R2 unconnected
- ✅ After adding Net in Python and regenerating, hierarchical labels appear
- ✅ Label "NET1" on R1 pin 2 and R2 pin 1
- ✅ Both components preserved with correct positions
- ✅ Electrical connection established (no physical wire needed)
