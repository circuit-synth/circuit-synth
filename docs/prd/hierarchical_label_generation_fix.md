# PRD: Fix Hierarchical Label Generation in Subcircuits (Issue #427)

## Executive Summary

**Issue:** Hierarchical labels are not being generated in KiCad schematics when nets are defined in Python code and connected to components in subcircuits. This affects all hierarchical circuit workflows and makes net connections invisible in KiCad.

**Impact:** CRITICAL - Core hierarchical circuit feature is broken. Subcircuits cannot have visible connections, making them essentially unusable.

**Tests Affected:**
- Test 28: Multi-unit components (no net connections visible)
- Test 59: Hierarchical pin renaming (no hierarchical labels generated) **[Currently has separate fixture bug]**
- All hierarchical circuits with net passing between parent/child

**Priority:** P0 - Blocks all hierarchical circuit development

---

## Problem Statement

### What Should Happen

When a user writes Python code like this in a subcircuit:

```python
root = Circuit("spi_subcircuit")
data_in = Net("DATA_IN")

spi_driver = Circuit("SPI_Driver")
resistor = Component(symbol="Device:R", ref="R1", value="10k")
spi_driver.add_component(resistor)

# This should create hierarchical label
resistor[1] += data_in  # Connect R1 pin 1 to DATA_IN net

root.add_subcircuit(spi_driver, connections={"DATA_IN": data_in})
root.generate_kicad_project("spi_subcircuit")
```

**Expected Result:**
1. In `SPI_Driver.kicad_sch` (subcircuit): A hierarchical label "DATA_IN" should appear connected to R1 pin 1
2. In `spi_subcircuit.kicad_sch` (parent): A sheet symbol with hierarchical pin "DATA_IN" should appear
3. Visual connection should be visible in KiCad between the label and component pin
4. Netlist should show R1 connected to DATA_IN net

### What Actually Happens

**Actual Result:**
1. R1 appears in the subcircuit schematic
2. **NO hierarchical labels are generated** - pins appear unconnected
3. Warning in logs: `Net 'DATA_IN' has only 1 connection(s) - may indicate connection issue`
4. Netlist may be missing the connection or show it incorrectly

### Manual Reproduction

```bash
cd tests/bidirectional/59_modify_hierarchical_pin_name
rm -rf spi_subcircuit/
uv run spi_subcircuit.py  # Will currently fail with "No active circuit" error

# Expected: Subcircuit generated with hierarchical labels
# Actual: Generation fails, or if it succeeds, no labels appear
```

---

## Root Cause Analysis

### Architecture Overview

Circuit-synth uses two different Net classes during the generation pipeline:

1. **Core Python Net** (`src/circuit_synth/core/net.py`)
   - Used when writing Python circuits with `@circuit` decorator
   - Stores connections as `_pins` set containing Pin objects
   - Access pattern: `for pin in net.pins: pin._component.ref, pin.num`

2. **Circuit Loader Net** (`src/circuit_synth/kicad/sch_gen/circuit_loader.py`)
   - Used when loading from JSON for KiCad generation
   - Stores connections as `connections` list of `(comp_ref, pin_id)` tuples
   - Access pattern: `for comp_ref, pin_id in net.connections`

### Data Flow Pipeline

```
Python Code (Core Net)
    ↓
NetlistExporter → JSON serialization
    ↓
{"nets": {"DATA_IN": {"nodes": [(comp, pin), ...]}}}
    ↓
circuit_loader.py → Circuit Loader Net
    ↓
schematic_writer.py → KiCad hierarchical labels
```

### Where Hierarchical Labels Are Generated

**File:** `src/circuit_synth/kicad/sch_gen/schematic_writer.py`
**Method:** `_add_pin_level_net_labels()` (lines 1261-1511)

```python
def _add_pin_level_net_labels(self):
    """Add local net labels or power symbols at component pins for all nets."""

    for net in circuit_nets:
        net_name = net.name

        # CRITICAL: Iterates through net.connections
        for comp_ref, pin_identifier in net.connections:
            # ... calculates pin position ...

            # Determines label type
            is_hierarchical = self._is_net_hierarchical(net)
            label_type = LabelType.HIERARCHICAL if is_hierarchical else LabelType.LOCAL

            # Creates hierarchical label
            label = Label(
                position=Point(global_x, global_y),
                text=net_name,
                label_type=label_type,
                rotation=float(global_angle),
            )

            self.schematic._data["hierarchical_labels"].append(label_dict)
```

### Potential Root Causes

Based on exploration and code analysis, the issue is likely one of:

#### Hypothesis 1: Net.connections is Empty (MOST LIKELY)
- The Python `Net` object has pins connected via `resistor[1] += data_in`
- But when serialized to JSON by `NetlistExporter`, the `"nodes"` array might be empty
- When `circuit_loader.py` loads the JSON, `net.connections` list is empty
- Result: The loop `for comp_ref, pin_id in net.connections` never executes
- **Evidence:** Warning message "Net 'DATA_IN' has only 1 connection(s)"

**Debug Action:** Check if JSON file contains `"nodes"` array for DATA_IN net

#### Hypothesis 2: Component Reference Mismatch
- The net connection references the Python component object
- In JSON it's stored as "R1" (after reference finalization)
- The lookup `comp = self.component_manager.find_component(actual_ref)` fails
- Result: Label position cannot be calculated, label not created

**Debug Action:** Add logs in `_add_pin_level_net_labels()` to check component lookups

#### Hypothesis 3: Subcircuit Nets Not Processed
- Each subcircuit schematic is generated with a separate `SchematicWriter` instance
- The subcircuit's nets might not be properly passed to its writer
- Result: Parent circuit has nets, but subcircuit writer doesn't see them

**Debug Action:** Check if subcircuit `SchematicWriter` receives subcircuit's nets

#### Hypothesis 4: Circuit Context Issue (Test 59 Specific)
- Test 59 fixture has bug: `Net("DATA_IN")` created outside active circuit
- Raises `CircuitSynthError: Cannot create Net('DATA_IN'): No active circuit found`
- This is a **separate bug** in the test fixture itself

**Debug Action:** Fix test fixture to use `@circuit` decorator properly

---

## Proposed Solution

### Phase 1: Investigation & Root Cause Confirmation (2-3 cycles, ~10 min)

**Cycle 1: Check JSON serialization**
```python
# Add logs in NetlistExporter
logger.debug(f"🔍 CYCLE 1: Serializing net {net.name}")
logger.debug(f"🔍 Net has {len(net._pins)} pins")
for pin in net._pins:
    logger.debug(f"🔍   Pin: {pin._component.ref}[{pin.num}]")
```

**Expected Output:** Should see pins being serialized

**Cycle 2: Check JSON output**
```bash
# Generate the circuit and inspect JSON
cat spi_subcircuit/spi_subcircuit.json | jq '.circuits[].nets'
```

**Expected:** Should see `"nodes": [{"component": "R1", "pin": {"number": "1"}}]`

**Cycle 3: Check circuit_loader parsing**
```python
# Add logs in circuit_loader.py _parse_circuit()
logger.debug(f"🔍 CYCLE 3: Loading net {net_name}")
logger.debug(f"🔍 Nodes in JSON: {net_data.get('nodes', [])}")
logger.debug(f"🔍 Parsed connections: {net_obj.connections}")
```

**Expected Output:** Should see connections list populated

### Phase 2: Implement Fix (4-6 cycles, ~15 min)

Based on root cause identified in Phase 1, apply one of these fixes:

#### Fix Option A: JSON Serialization Issue
If net pins aren't being serialized:

**Location:** `src/circuit_synth/core/netlist_exporter.py`

```python
# Current code (hypothetical bug):
net_data = {
    "name": net.name,
    # Missing: "nodes": [...]
}

# Fixed code:
nodes = []
for pin in net._pins:
    nodes.append({
        "component": pin._component.ref,
        "pin": {"number": str(pin.num)}
    })

net_data = {
    "name": net.name,
    "nodes": nodes  # ← Add this
}
```

#### Fix Option B: Circuit Context Issue
If subcircuit nets aren't visible to the writer:

**Location:** `src/circuit_synth/kicad/sch_gen/main_generator.py`

```python
# When generating subcircuit schematic, ensure nets are passed:
subcircuit_writer = SchematicWriter(
    circuit=subcircuit,  # ← Ensure this contains nets
    output_path=subcircuit_path,
    # ...
)
```

#### Fix Option C: Component Reference Resolution
If component lookups fail:

**Location:** `src/circuit_synth/kicad/sch_gen/schematic_writer.py`

```python
# Add fallback lookup or better error handling:
comp = self.component_manager.find_component(actual_ref)
if not comp:
    logger.warning(f"Component {actual_ref} not found for net {net_name}")
    continue  # ← Skip this connection instead of silently failing
```

### Phase 3: Fix Test 59 Fixture (2 cycles, ~5 min)

**Issue:** Test fixture creates Net outside active circuit context

**Fix Location:** `tests/bidirectional/59_modify_hierarchical_pin_name/spi_subcircuit.py`

```python
# Current code (BROKEN):
def main():
    root = Circuit("spi_subcircuit")
    data_in = Net("DATA_IN")  # ← ERROR: No active circuit
    # ...

# Fixed code:
@circuit
def main():
    root = Circuit("spi_subcircuit")
    data_in = Net("DATA_IN")  # ← Now in circuit context
    # ...
```

OR use circuit context explicitly:

```python
def main():
    root = Circuit("spi_subcircuit")
    with root:  # Enter circuit context
        data_in = Net("DATA_IN")  # ← Now valid
        # ...
```

### Phase 4: Verification (3 cycles, ~10 min)

**Cycle 1: Unit test**
```bash
# Run schematic writer tests
uv run pytest tests/unit/test_schematic_writer.py -xvs -k hierarchical
```

**Cycle 2: Integration test**
```bash
# Run Test 59 (after fixing fixture)
uv run pytest tests/bidirectional/59_modify_hierarchical_pin_name/test_59_rename_pin.py -xvs --runxfail
```

**Cycle 3: Manual verification**
```bash
cd tests/bidirectional/59_modify_hierarchical_pin_name
rm -rf spi_subcircuit/
uv run spi_subcircuit.py
open spi_subcircuit/spi_subcircuit.kicad_pro

# Verify in KiCad:
# 1. Open SPI_Driver sheet
# 2. See hierarchical label "DATA_IN" connected to R1
# 3. Label should be visually connected with a wire
```

---

## Test Plan

### Test Cases to Validate Fix

#### Test 1: Basic Hierarchical Label Generation
```python
# Subcircuit with single component and net
root = Circuit("test")
sub = Circuit("SubCircuit")
resistor = Component("Device:R", "R1", "10k")
data_net = Net("DATA")

sub.add_component(resistor)
resistor[1] += data_net

root.add_subcircuit(sub, connections={"DATA": data_net})
root.generate_kicad_project("test")

# Verify:
# - SubCircuit.kicad_sch has hierarchical_label "DATA"
# - Label is at same position as R1 pin 1
# - Wire connects label to pin
```

#### Test 2: Multiple Nets in Subcircuit
```python
# Multiple nets should create multiple hierarchical labels
net_a = Net("NET_A")
net_b = Net("NET_B")

resistor[1] += net_a
resistor[2] += net_b

# Verify:
# - Two hierarchical labels: "NET_A" and "NET_B"
# - Each connected to correct pin
```

#### Test 3: Deeply Nested Subcircuits
```python
# Test hierarchical labels at multiple levels
root = Circuit("root")
level1 = Circuit("level1")
level2 = Circuit("level2")

# Verify:
# - Hierarchical labels appear at each level
# - Labels correctly reference parent nets
```

#### Test 4: Test 59 - Hierarchical Pin Renaming
```python
# After fixing basic generation, validate renaming works
# This is the original Test 59 scenario

# Verify:
# - DATA_IN label generated initially
# - After rename, SPI_MOSI label appears
# - Old DATA_IN label removed (Issue #380 check)
```

### Regression Tests

Run full bidirectional test suite to ensure fix doesn't break existing functionality:

```bash
uv run pytest tests/bidirectional/ -xvs --runxfail
```

Focus on tests that involve hierarchical circuits:
- Test 22: Add subcircuit sheet
- Test 24: Global labels (ensure we didn't break global label generation)
- Test 28: Multi-unit components with nets
- Test 44: Subcircuit hierarchical ports
- Test 58: Mixed hierarchical + global labels

---

## Success Criteria

### Definition of Done

1. **Hierarchical labels generated correctly:**
   - When `component[pin] += net` is called in a subcircuit
   - Hierarchical label appears in .kicad_sch file
   - Label is positioned at component pin location
   - Wire connects label to pin

2. **Test 59 passes:**
   - Fixture bug fixed (Net created in proper circuit context)
   - Initial generation creates DATA_IN hierarchical label
   - Test can proceed to renaming validation (Issue #380 separate)

3. **No regression:**
   - All existing bidirectional tests pass
   - Test 28 (multi-unit components) shows net connections
   - Global label generation still works

4. **Warning message resolved:**
   - No more "Net 'X' has only 1 connection(s)" for connected nets
   - Nets correctly show 2+ connections when hierarchical labels are involved

### Verification Steps

```bash
# Step 1: Fix fixture and generate circuit
cd tests/bidirectional/59_modify_hierarchical_pin_name
rm -rf spi_subcircuit/
uv run spi_subcircuit.py
# ✅ Should complete without errors

# Step 2: Verify JSON has connections
cat spi_subcircuit/spi_subcircuit.json | jq '.circuits[] | select(.name=="SPI_Driver") | .nets'
# ✅ Should see "nodes" array with R1 connection

# Step 3: Verify KiCad schematic has label
grep "hierarchical_label" spi_subcircuit/SPI_Driver.kicad_sch
# ✅ Should find: (hierarchical_label "DATA_IN" ...)

# Step 4: Open in KiCad
open spi_subcircuit/spi_subcircuit.kicad_pro
# ✅ Should see hierarchical label in subcircuit
# ✅ Label should be connected to R1 with wire

# Step 5: Run tests
uv run pytest tests/bidirectional/59_modify_hierarchical_pin_name/test_59_rename_pin.py -xvs --runxfail
# ✅ Should pass initial generation (STEP 1-4)
# ⚠️  May still fail on Issue #380 (label removal) - that's separate

# Step 6: Run full test suite
uv run pytest tests/bidirectional/ -x
# ✅ All tests should pass
```

---

## Implementation Notes

### Files to Modify

1. **Primary Fix** (one of these based on root cause):
   - `src/circuit_synth/core/netlist_exporter.py` - If JSON serialization broken
   - `src/circuit_synth/kicad/sch_gen/circuit_loader.py` - If JSON parsing broken
   - `src/circuit_synth/kicad/sch_gen/schematic_writer.py` - If label generation logic broken
   - `src/circuit_synth/kicad/sch_gen/main_generator.py` - If subcircuit processing broken

2. **Test Fixture Fix** (required):
   - `tests/bidirectional/59_modify_hierarchical_pin_name/spi_subcircuit.py`

3. **Test Updates** (if needed):
   - `tests/bidirectional/59_modify_hierarchical_pin_name/test_59_rename_pin.py`
   - May need to split into two tests:
     - test_59a_hierarchical_label_generation (Issue #427)
     - test_59b_hierarchical_label_renaming (Issue #380)

### Logging Strategy

Add strategic 🔍 logs at key points (remove after fix confirmed):

```python
# In netlist_exporter.py
logger.debug(f"🔍 Exporting net {net.name} with {len(net._pins)} pins")

# In circuit_loader.py
logger.debug(f"🔍 Loading net {net_name} with {len(nodes)} nodes")
logger.debug(f"🔍 Net.connections after load: {net_obj.connections}")

# In schematic_writer.py
logger.debug(f"🔍 Processing net {net_name} with {len(net.connections)} connections")
logger.debug(f"🔍 Creating hierarchical label '{net_name}' at ({x}, {y})")
```

### Performance Considerations

This is not a performance-critical fix. The overhead of generating hierarchical labels is negligible compared to the overall schematic generation time. Focus on correctness first.

---

## Related Issues

- **Issue #427** (This PRD): Hierarchical labels not generated
- **Issue #380**: Synchronizer may not remove old hierarchical labels when pin names change
  - This is a SEPARATE issue that affects Test 59 after initial generation works
  - Should be addressed in a separate PR after #427 is fixed
- **Issue #385**: Related to hierarchical label validation (may be resolved)

---

## Timeline Estimate

Using the **small batch workflow** from CLAUDE.md:

| Phase | Estimated Time | Cycles |
|-------|---------------|--------|
| Phase 1: Investigation | 10 min | 3 cycles |
| Phase 2: Implement Fix | 15 min | 5 cycles |
| Phase 3: Fix Test 59 Fixture | 5 min | 2 cycles |
| Phase 4: Verification | 10 min | 3 cycles |
| **Total** | **40 min** | **13 cycles** |

This fits within a single 45-minute burst work session as described in CLAUDE.md.

---

## References

- **Issue #427:** https://github.com/circuit-synth/circuit-synth/issues/427
- **Test 59 README:** `tests/bidirectional/59_modify_hierarchical_pin_name/README.md`
- **Schematic Writer:** `src/circuit_synth/kicad/sch_gen/schematic_writer.py:1261-1511`
- **Circuit Loader:** `src/circuit_synth/kicad/sch_gen/circuit_loader.py:258-309`
- **Label Manager:** `src/circuit_synth/kicad/schematic/label_manager.py`

---

## Appendix: Code References

### Current Label Generation Logic

```python
# File: src/circuit_synth/kicad/sch_gen/schematic_writer.py
# Lines: 1261-1511

def _add_pin_level_net_labels(self):
    """Add local net labels or power symbols at component pins for all nets."""

    circuit_nets = []
    if hasattr(self.circuit, "nets"):
        circuit_nets = self.circuit.nets.values()

    for net in circuit_nets:
        net_name = net.name

        # Check if power net (handled differently)
        if getattr(net, "is_power", False):
            # ... power symbol logic ...
            continue

        # CRITICAL SECTION: Iterate through connections
        # THIS IS WHERE THE BUG LIKELY EXISTS
        for comp_ref, pin_identifier in net.connections:  # ← May be empty!

            # Find component
            actual_ref = comp_ref
            comp = self.component_manager.find_component(actual_ref)

            if not comp:
                logger.warning(f"Component {actual_ref} not found")
                continue

            # Calculate pin position
            # ... geometry calculations ...

            # Determine label type
            is_hierarchical = self._is_net_hierarchical(net)
            label_type = LabelType.HIERARCHICAL if is_hierarchical else LabelType.LOCAL

            # Create label
            label = Label(
                position=Point(global_x, global_y),
                text=net_name,
                label_type=label_type,
                rotation=float(global_angle),
            )

            # Add to schematic
            self.schematic._data["hierarchical_labels"].append(label_dict)
```

### Circuit Loader Net Class

```python
# File: src/circuit_synth/kicad/sch_gen/circuit_loader.py
# Lines: 51-86

class Net:
    """Represents an electrical net and pin connections."""

    def __init__(self, name: str):
        self.name = name
        self.connections: List[tuple] = []  # ← (comp_ref, pin_number)
        self.is_power = False
        self.power_symbol = None

    @classmethod
    def from_dict(cls, data: dict) -> "Net":
        """Create Net from dictionary (JSON)."""
        net = cls(name=data.get("name", ""))
        net.is_power = data.get("is_power", False)
        net.power_symbol = data.get("power_symbol", None)

        # Parse connections from "nodes" key
        for conn in data.get("nodes", []):  # ← THIS IS THE KEY!
            comp_ref = conn["component"]
            pin_data = conn["pin"]
            pin_identifier = pin_data.get("number", ...)
            net.connections.append((comp_ref, pin_identifier))

        return net
```

---

**Document Version:** 1.0
**Created:** 2025-10-30
**Author:** Claude (circuit-synth contributor agent)
**Status:** Draft - Ready for Implementation
