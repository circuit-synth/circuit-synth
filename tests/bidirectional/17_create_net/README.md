# Test 17: Create Net Connection

## What This Tests

Validates that creating a connection (net) between two components in Python code correctly appears in the generated KiCad schematic.

## When This Situation Happens

- Developer has two unconnected components in circuit
- Needs to connect them electrically
- Adds Net() in Python to connect component pins
- Regenerates KiCad project expecting connection to be present

## What Should Work

1. Initial circuit with two unconnected resistors (R1, R2) generates valid KiCad project
2. Python code modified to add Net connecting R1 pin to R2 pin
3. Regenerated KiCad schematic shows electrical connection (wire) between components
4. Net is properly represented with correct pin connections

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/17_create_net

# Step 1: Create initial Python script with two unconnected resistors
cat > two_resistors.py << 'EOF'
from circuit_synth import Circuit, Component

circuit = Circuit("two_resistors")

# Two resistors, not connected
r1 = Component(symbol="Device:R", ref="R1", value="10k",
               footprint="Resistor_SMD:R_0603_1608Metric")
r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
               footprint="Resistor_SMD:R_0603_1608Metric")

circuit.add_components(r1, r2)
circuit.to_kicad()
EOF

# Step 2: Generate initial KiCad project (no connection)
uv run two_resistors.py
open two_resistors/two_resistors.kicad_pro
# Verify: schematic has R1 and R2 but no wire between them

# Step 3: Edit two_resistors.py to add a net connection
# Add before circuit.to_kicad():
#   from circuit_synth import Net
#   net1 = Net("connection")
#   net1.connect(r1["2"], r2["1"])
#   circuit.add_nets(net1)

# Step 4: Regenerate KiCad project with connection
uv run two_resistors.py

# Step 5: Open regenerated KiCad project
open two_resistors/two_resistors.kicad_pro

# Step 6: Verify schematic shows wire connection
#   - R1 and R2 still present
#   - Wire connecting R1 pin 2 to R2 pin 1
#   - Net name "connection" appears in schematic
```

## Expected Result

- ✅ Initial KiCad project has R1 and R2 unconnected
- ✅ After adding Net in Python and regenerating, wire appears
- ✅ Wire connects R1 pin 2 to R2 pin 1
- ✅ Both components preserved with correct positions
- ✅ Net name "connection" visible in schematic

## Why This Is Important

Creating nets programmatically allows developers to define circuit connectivity in Python code. The bidirectional sync must correctly translate Python Net objects into KiCad wire connections.
