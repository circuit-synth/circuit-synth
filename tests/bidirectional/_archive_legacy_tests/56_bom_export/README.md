# Test 56: BOM Export Integration

## What This Tests
Validates that Bill of Materials (BOM) export via kicad-cli works correctly with circuit-synth generated schematics, including component grouping, DNP flags, and quantity tracking.

## When This Situation Happens
- Designer needs to export BOM for manufacturing/procurement
- Multiple identical components should be grouped (e.g., 10x 10k resistors)
- Some components marked DNP (Do Not Populate) for prototype testing
- BOM must accurately reflect component counts and specifications
- Engineer modifies circuit, needs to regenerate BOM to see changes

## What Should Work
### Initial Generation:
- Python creates circuit with:
  - 10x 10k resistors (R1-R10) - should group
  - 2x 100nF capacitors (C1-C2) - should group
  - 1x LED (D1) marked DNP
  - 1x 1k resistor (R11) marked DNP
- Generate KiCad schematic
- Export BOM via kicad-cli
- Parse BOM CSV:
  - Resistors grouped: "R1,R2,R3,R4,R5,R6,R7,R8,R9,R10" with Qty=10
  - Capacitors grouped: "C1,C2" with Qty=2
  - D1 marked DNP
  - R11 marked DNP
  - Total: 4 BOM lines (grouped components)

### Modification:
- Add R12 (10k resistor) in Python
- Mark D1 as not DNP (populate it)
- Regenerate KiCad
- Export new BOM
- Validate changes:
  - Resistors grouped: "R1-R10,R12" with Qty=11
  - D1 no longer marked DNP
  - R11 still marked DNP
  - Total: 4 BOM lines

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/56_bom_export

# Step 1: Generate initial circuit with BOM components
uv run circuit_for_bom.py
open circuit_for_bom/circuit_for_bom.kicad_pro

# Verify in KiCad:
# - R1-R10 all present (10k resistors)
# - C1-C2 present (100nF capacitors)
# - D1 present (LED) with DNP flag
# - R11 present (1k resistor) with DNP flag

# Step 2: Export BOM using kicad-cli
kicad-cli sch export bom \
  --output circuit_for_bom/bom_initial.csv \
  --exclude-dnp \
  circuit_for_bom/circuit_for_bom.kicad_sch

# Step 3: Inspect BOM CSV
cat circuit_for_bom/bom_initial.csv

# Should show:
# Refs,Value,Footprint,Qty,DNP
# "R1,R2,R3,R4,R5,R6,R7,R8,R9,R10","10k","Resistor_SMD:R_0603_1608Metric","10",""
# "C1,C2","100nF","Capacitor_SMD:C_0603_1608Metric","2",""
# (D1 and R11 excluded due to DNP)

# Step 4: Modify circuit_for_bom.py
# - Uncomment R12 (add 11th 10k resistor)
# - Comment out the DNP flag on D1 (populate it)

# Step 5: Regenerate
uv run circuit_for_bom.py

# Step 6: Export modified BOM
kicad-cli sch export bom \
  --output circuit_for_bom/bom_modified.csv \
  --exclude-dnp \
  circuit_for_bom/circuit_for_bom.kicad_sch

# Step 7: Inspect modified BOM
cat circuit_for_bom/bom_modified.csv

# Should now show:
# "R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R12","10k","Resistor_SMD:R_0603_1608Metric","11",""
# "C1,C2","100nF","Capacitor_SMD:C_0603_1608Metric","2",""
# "D1","LED","LED_SMD:LED_0603_1608Metric","1",""
# (R11 still excluded due to DNP)

# Step 8: Export BOM including DNP components
kicad-cli sch export bom \
  --output circuit_for_bom/bom_with_dnp.csv \
  circuit_for_bom/circuit_for_bom.kicad_sch

# Should show all components including R11 marked as DNP
```

## Automated Test

The automated test validates:
1. **BOM Export** - kicad-cli successfully exports CSV BOM
2. **Component Grouping** - Identical components grouped by value/footprint
3. **Quantity Counting** - Correct quantity for grouped components
4. **DNP Handling** - DNP components excluded when flag set
5. **CSV Parsing** - BOM CSV parses correctly with expected fields
6. **Modification Tracking** - Changes in Python reflected in BOM
7. **kicad-cli Availability** - Skip test gracefully if kicad-cli not found

## Success Criteria
- ✅ kicad-cli BOM export completes without errors
- ✅ BOM CSV file generated with correct format
- ✅ CSV has expected headers (Refs, Value, Footprint, Qty, DNP)
- ✅ 10x 10k resistors grouped into single BOM line with Qty=10
- ✅ 2x 100nF capacitors grouped into single BOM line with Qty=2
- ✅ DNP components (D1, R11) excluded from BOM when --exclude-dnp flag used
- ✅ After modification: R12 added to resistor group (Qty=11)
- ✅ After modification: D1 no longer marked DNP, appears in BOM
- ✅ R11 remains marked DNP, still excluded from BOM
- ✅ Total BOM lines: 3 (resistors, capacitors, LED) after modification

## Why This Is Critical

**Real-World Use Cases:**
1. **Manufacturing BOM** - Send BOM to CM for PCB assembly
2. **Cost Estimation** - Calculate total component cost for production
3. **Procurement** - Generate purchase orders for components
4. **Inventory Management** - Track component usage across projects
5. **Design Iterations** - Compare BOMs between revisions
6. **DNP Testing** - Prototype with optional components unpopulated

**Technical Validation:**
- **kicad-cli Integration** - Confirms CLI BOM export works with circuit-synth
- **Grouping Logic** - Validates identical components group correctly
- **Quantity Tracking** - Ensures accurate component counts
- **DNP Flag Handling** - Tests DNP flag sets and reads correctly
- **CSV Format** - Confirms industry-standard CSV BOM format
- **Bidirectional Sync** - BOM reflects Python changes after regeneration

## Priority
**Priority 2** - Nice-to-have real-world integration. Essential for production workflows but not core circuit-synth functionality.

## Notes
- Test skips gracefully if kicad-cli not available
- Uses standard CSV format (RFC 4180 compliant)
- DNP flag is KiCad standard "Do Not Populate" field
- Grouping by value+footprint is standard BOM practice
- Reference ranges (R1-R10) improve readability but test accepts comma-separated refs too
