# Test 58: Hierarchical Pin to Global Label (Mixed Labeling Strategy)

## Overview

**Priority 0 MIXED LABELING Test** - Tests the critical real-world scenario where hierarchical pins and global labels coexist in the same design.

This validates that circuit-synth correctly handles:
- Hierarchical labels for structured power distribution (parent → child via hierarchy)
- Global labels for flat signal buses (peer-to-peer across sheets)
- Mixed usage of both labeling types in the same sheet
- Netlist correctness for both connectivity mechanisms

## Test Scenario

### Initial Circuit

1. **Parent Sheet**
   - Power nets (VCC, GND) connected to Subcircuit A via hierarchical pins
   - Component R1 on parent sheet

2. **Subcircuit A (Child of Parent)**
   - Receives VCC/GND from parent via hierarchical labels
   - Has local component R2 connected to power
   - **Critical**: Also has SPI_CLK global label for peer connectivity

3. **Subcircuit B (Peer to A)**
   - Independent subcircuit with SPI bus using global labels
   - Component R3 connected to SPI_CLK global label

### Connectivity Mechanisms

**Hierarchical (Parent → Child):**
```
Parent Sheet:
  - VCC power net → Hierarchical sheet pin on Subcircuit A

Subcircuit A:
  - hierarchical_label "VCC" (Input) ← receives from parent
  - R2 pin 1 connected to VCC
```

**Global (Peer-to-Peer):**
```
Subcircuit A:
  - global_label "SPI_CLK" (Input)
  - R2 pin 2 connected to SPI_CLK

Subcircuit B:
  - global_label "SPI_CLK" (Output)
  - R3 pin 1 connected to SPI_CLK
```

## Why This Matters

### Real-World Use Case

This is how complex designs actually work:
- **Power distribution**: Hierarchical (flows down from parent)
- **Signal buses**: Global labels (connect across peer sheets)
- **Mixed in same sheet**: Same subcircuit uses both mechanisms

Common patterns:
- Power supply subcircuit (hierarchical) + SPI bus (global)
- MCU subcircuit receives power hierarchically, shares I2C globally
- Memory bank receives power hierarchically, shares data bus globally

### Technical Challenge

Circuit-synth must support **both label types in the same sheet**:

```s-expr
(kicad_sch
  (hierarchical_label "VCC" (at 50 50) (input))
  (global_label "SPI_CLK" (at 75 75) (input))
  ...
)
```

This requires the synchronizer to:
1. Track hierarchical connections (parent → child)
2. Track global connections (peer → peer)
3. Not conflate the two mechanisms
4. Generate correct netlist entries for each

## Test Workflow

### Step 1: Generate Initial Mixed-Label Circuit
- Create parent with power nets → Subcircuit A (hierarchical)
- Create Subcircuit B with SPI_CLK global label
- Connect R2 in Subcircuit A to SPI_CLK (global)

### Step 2: Validate Mixed Labels (Level 2)
- Subcircuit A sheet has both:
  - `hierarchical_label "VCC"`
  - `global_label "SPI_CLK"`
- Parent sheet has hierarchical sheet pin for VCC
- Subcircuit B sheet has `global_label "SPI_CLK"`

### Step 3: Validate Netlist Connectivity (Level 3)
- VCC net connects parent R1 → Subcircuit A R2 (hierarchical path)
- SPI_CLK net connects Subcircuit A R2 → Subcircuit B R3 (global path)
- Nets are distinct and correctly routed

### Step 4: Add Parent Component Using Global Label
- Add R4 to parent sheet connected to SPI_CLK global label
- Regenerate circuit

### Step 5: Validate Global Label Propagation
- Parent sheet now has `global_label "SPI_CLK"`
- R4 correctly connected to SPI_CLK net
- Subcircuit A and B still have SPI_CLK global labels
- Netlist shows R4 connected to same SPI_CLK net

## Expected Outcomes

### ✅ Success Criteria

1. **Mixed Labels in Same Sheet**
   - Subcircuit A has both hierarchical_label and global_label entries
   - No conflicts between label types

2. **Hierarchical Connectivity Works**
   - VCC flows from parent to Subcircuit A
   - Netlist shows parent → child connection

3. **Global Connectivity Works**
   - SPI_CLK connects across Subcircuit A and B
   - Adding global label in parent propagates correctly

4. **Netlist Correctness**
   - Two distinct nets (VCC and SPI_CLK)
   - Each net uses correct connectivity mechanism
   - No cross-contamination between hierarchical and global

### ⚠️ Possible Failures (Known Issues)

**Issue #380: Synchronizer may not handle mixed labels**
- Symptom: Generation succeeds but only one label type appears
- Symptom: Netlist shows incorrect connectivity
- Symptom: Global labels converted to hierarchical or vice versa

If this occurs, test should be marked `@pytest.mark.xfail` with reference to Issue #380.

## Validation Levels

- **Level 1**: Files generated (schematic exists)
- **Level 2**: Schematic structure correct (both label types present)
- **Level 3**: Netlist shows correct connectivity for both mechanisms

## Files

- `mixed_labels.py` - Fixture with hierarchical power + global signals
- `test_58_mixed_labels.py` - Automated test validating mixed labeling
- `README.md` - This documentation

## Dependencies

- `kicad-sch-api` - Schematic parsing for Level 2 validation
- `kicad-cli` - Netlist export for Level 3 validation
- `circuit-synth` - Must support both label types in same sheet

## Related Tests

- Test 22: Add Subcircuit Sheet (hierarchical labels only)
- Test 24: Add Global Label (global labels only)
- Test 58: **THIS TEST** (mixed labels in same design)

## Common Patterns This Enables

1. **Power + Communication**
   - Power hierarchical (1.8V, 3.3V, 5V)
   - I2C/SPI/UART global (cross-sheet)

2. **Memory Architecture**
   - Power hierarchical (VDD, VDDIO, GND)
   - Address/Data bus global (shared across banks)

3. **Multi-MCU Systems**
   - Each MCU gets power hierarchically
   - CAN/Ethernet global for communication

---

*Test Priority: 0 (Critical - Mixed labeling is essential for complex designs)*
*Expected Result: Should work (if synchronizer supports mixed labels)*
*Fallback: XFAIL with Issue #380 if mixed labels not supported*
