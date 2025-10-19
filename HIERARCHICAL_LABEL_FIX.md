# Hierarchical Label Bug - Analysis and Fix Plan

## Problem Statement

### Issue
Labels in KiCad schematics are incorrectly classified as all HIERARCHICAL when some should be LOCAL.

**Example**: ESP32_C6_MCU sheet shows:
- 53 hierarchical labels
- 0 local labels

**Expected**: Should have:
- Hierarchical labels for nets shared with parent OR children
- Local labels for internal-only nets (e.g., USB_DP_MCU, USB_DM_MCU)

### User Impact
- Incorrect sheet pins being generated
- Poor schematic readability
- Confusion about signal flow in hierarchical designs

---

## Root Cause Analysis

### 1. Code Path Discovery

The issue affects the JSON-based generation flow:

```
Circuit.generate_kicad_project()
  → SchematicGenerator.generate_project()
  → load_circuit_hierarchy(json_file)  # Loads from JSON
  → assign_subcircuit_instance_labels()
  → SchematicWriter.__init__()
  → SchematicWriter.generate_s_expr()
  → SchematicWriter._add_pin_level_net_labels()
  → SchematicWriter._is_net_hierarchical()  # BUG HERE
```

### 2. The JSON Round-Trip Problem

**Critical Insight**: When circuits are loaded from JSON, `Net` objects are recreated:
- **Direct Python creation**: `Net` objects are passed by reference between parent/child
- **JSON loading**: New `Net` objects created with same names
- **Result**: Object identity checks (`if net_a is net_b`) fail after JSON loading

### 3. Current Implementation Issues

Location: `/src/circuit_synth/kicad/sch_gen/schematic_writer.py:843-900`

```python
def _is_net_hierarchical(self, net_obj):
    # ✓ Check parent (works with name matching fallback)
    if parent_circuit:
        if net_obj.name in parent_net_names:
            return True

    # ✗ Check children (TOO BROAD - matches ALL child nets)
    for child_info in self.circuit.child_instances:
        child_nets = child_circ.nets.values()
        for child_net in child_nets:
            if child_net.name == net_obj.name:  # BUG: Matches ANY child net with same name
                return True
```

**The Bug**: Name matching with children is too broad. It matches ANY net with the same name in a child circuit, even if that child net isn't actually connected to the parent.

### 4. Test Case Analysis

**ESP32_C6_MCU** (parent) has these nets:
- `DEBUG_EN`, `DEBUG_TX`, `LED_CONTROL` → passed to children → HIERARCHICAL ✓
- `VCC_3V3`, `GND`, `USB_DP`, `USB_DM` → from parent → HIERARCHICAL ✓
- `USB_DP_MCU`, `USB_DM_MCU` → internal only → should be LOCAL ✗

**Debug_Header** (child) has:
- `DEBUG_EN`, `DEBUG_TX`, `DEBUG_RX`, `DEBUG_IO0`, `VCC_3V3`, `GND`

**LED_Blinker** (child) has:
- `LED_CONTROL`, `VCC_3V3`, `N$3`

**Why USB_DP_MCU should be LOCAL**:
- Only exists in ESP32_C6_MCU
- Not in parent (main circuit)
- Not in children (Debug_Header, LED_Blinker)
- Pure internal signal routing

---

## Solution Design

### Core Principle
**A net needs a hierarchical label if and only if it crosses hierarchy boundaries.**

That means:
1. **UP**: Net is shared with parent (parent has same-named net)
2. **DOWN**: Net is shared with child (child has same-named net)

### Why Name Matching Works

After JSON loading, object identity is lost, but name matching is semantically correct because:

1. **Circuit-synth design pattern**: When you pass a `Net` to a subcircuit function, that exact `Net` object is used in the child circuit
2. **JSON serialization**: Both parent and child serialize the same `Net` object to JSON with the same name
3. **JSON loading**: Both parent and child recreate `Net` objects with matching names
4. **Conclusion**: If parent and child both have a net named "VCC_3V3", it's the SAME logical net

### Edge Cases to Handle

1. **Net only in parent**: Check parent, not in children → Local in parent context
2. **Net only in one child**: Check children, not in parent → Local in child context
3. **Net in parent AND child**: Shared connection → Hierarchical
4. **Net in multiple children**: Likely shared if in parent too → Hierarchical
5. **Internal net in child**: Only in child, not in parent or siblings → Local

---

## Implementation Plan

### Step 1: Understand Existing Sheet Pin Logic

The sheet pin generation code (lines 1090-1169) already implements correct shared net detection:

```python
# First try object identity
for child_net in child_nets:
    for parent_net in parent_nets:
        if parent_net is child_net:  # Direct object match
            shared_net_names.append(child_net.name)

# Fallback to name matching (for JSON-loaded circuits)
if not shared_net_names:
    parent_net_names_set = {n.name for n in parent_nets}
    for child_net in child_nets:
        if child_net.name in parent_net_names_set:  # Name in BOTH
            shared_net_names.append(child_net.name)
```

**Key insight**: It checks if a net name exists in BOTH parent AND child, not just one or the other.

### Step 2: Fix `_is_net_hierarchical()` Logic

The current bug is in the child-checking section. Current code:

```python
# BUG: Returns True if net name exists in ANY child net
for child_net in child_nets:
    if child_net.name == net_obj.name:
        return True
```

This should check if the net is SHARED, not just present. The correct logic:

```python
# Check if THIS parent net exists in the child (shared connection)
# This is correct - if parent net "VCC_3V3" exists in child as "VCC_3V3", they're connected
for child_net in child_nets:
    if child_net.name == net_obj.name:
        return True  # This IS correct for shared nets!
```

**Wait - the logic IS correct!** Let me reconsider...

### Step 3: Re-analyze the Problem

Let me check what nets are actually present:

```
ESP32_C6_MCU nets:
  DEBUG_EN, DEBUG_IO0, LED_CONTROL, VCC_3V3, GND,
  DEBUG_TX, DEBUG_RX, USB_DP_MCU, USB_DM_MCU, USB_DP, USB_DM

Debug_Header nets:
  DEBUG_EN, DEBUG_TX, DEBUG_RX, DEBUG_IO0, VCC_3V3, GND

LED_Blinker nets:
  LED_CONTROL, VCC_3V3, N$3
```

For `USB_DP_MCU`:
- Check parent: Doesn't exist in parent → Not shared with parent
- Check Debug_Header: `USB_DP_MCU` not in Debug_Header → Not shared
- Check LED_Blinker: `USB_DP_MCU` not in LED_Blinker → Not shared
- **Conclusion**: Should return False → LOCAL ✓

The logic SHOULD work! Let me verify the actual behavior by testing.

### Step 4: Hypothesis - child_instances Not Populated

**New hypothesis**: Maybe `child_instances` is empty when `_is_net_hierarchical()` is called?

From the JSON data, ESP32_C6_MCU shows `child_instances: []` in the exported JSON. This suggests child_instances might not be serialized to JSON properly, or it's populated later.

Let me trace when it's populated:
- Line 752: `assign_subcircuit_instance_labels(top_circuit, sub_dict)`
- Line 810: `main_writer = SchematicWriter(...)`

So child_instances SHOULD be populated before SchematicWriter is created.

### Step 5: Verify child_instances Content

Need to check what `self.circuit.child_instances` actually contains when `_is_net_hierarchical()` runs.

---

## Testing Strategy

### 1. Add Logging to Verify Assumptions

```python
def _is_net_hierarchical(self, net_obj):
    # Log what we're checking
    if self.circuit.name == "ESP32_C6_MCU":
        print(f"Checking {net_obj.name}:")
        print(f"  child_instances: {[c['sub_name'] for c in self.circuit.child_instances]}")
```

### 2. Test Cases

1. **USB_DP_MCU**: Internal only → should be LOCAL
2. **DEBUG_EN**: Shared with Debug_Header → should be HIERARCHICAL
3. **VCC_3V3**: Shared with parent AND children → should be HIERARCHICAL

### 3. Expected Output

```
ESP32_C6_MCU.kicad_sch should have:
- Hierarchical: DEBUG_EN, DEBUG_IO0, DEBUG_TX, DEBUG_RX, LED_CONTROL, VCC_3V3, GND, USB_DP, USB_DM
- Local: USB_DP_MCU, USB_DM_MCU
```

---

## Implementation Steps

1. ✅ Add comprehensive logging to `_is_net_hierarchical()`
2. ⏳ Run test and capture logs
3. ⏳ Identify actual root cause from logs
4. ⏳ Implement fix based on findings
5. ⏳ Test with ESP32_C6 example
6. ⏳ Clean up debug code
7. ⏳ Create unit tests
8. ⏳ Release v0.10.3

---

## Root Cause FOUND!

### Investigation Results

1. ✅ `_is_net_hierarchical()` logic is **WORKING CORRECTLY**
   - USB_DP_MCU → LOCAL
   - DEBUG_EN → HIERARCHICAL
   - VCC_3V3 → HIERARCHICAL

2. ✅ Labels created with **CORRECT TYPES**
   - `Label(text="USB_DP_MCU", label_type=LabelType.LOCAL)` ✓

3. ✅ Local labels added to **CORRECT DATA STRUCTURE**
   - `schematic._data["labels"]` contains 8 local labels ✓
   - `schematic._data["hierarchical_labels"]` contains 44 hierarchical labels ✓

4. ❌ **BUG FOUND**: kicad-sch-api `_schematic_data_to_sexp()` **NOT WRITING LOCAL LABELS**
   - The parser method doesn't handle the "labels" key from _data
   - Only processes "hierarchical_labels"
   - Result: Local labels silently dropped during file writing

### Fix Required

**Location**: `submodules/kicad-sch-api/kicad_sch_api/core/parser.py`

**Action**: Add support for writing "labels" key to S-expression output

### Test Verification

Before fix:
- ESP32_C6_MCU.kicad_sch: 44 hierarchical, 0 local ❌
- schematic._data: 44 hierarchical, 8 local ✅

After fix (expected):
- ESP32_C6_MCU.kicad_sch: 44 hierarchical, 8 local ✅
- USB_DP_MCU and USB_DM_MCU should appear as local labels
