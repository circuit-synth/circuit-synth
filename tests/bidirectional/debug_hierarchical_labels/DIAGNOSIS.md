# Hierarchical Label Generation Issue - Root Cause Diagnosis

**Date:** 2025-10-30
**Issue:** #427 - Hierarchical labels not generated for net connections in subcircuits
**Tests:** Test 1 (single resistor), Test 2 (nested dividers)

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** Hierarchical labels are only generated when a net has **2 or more connections** within the subcircuit. Nets with only 1 connection (e.g., single resistor connected to hierarchical port) do NOT generate hierarchical labels.

**Expected Behavior:** Hierarchical labels should be generated for ANY net in a subcircuit that connects to the parent, even if the net has only 1 component connection. The hierarchical label itself represents the connection to the parent circuit.

---

## Test Results

### Test 1: Single Resistor in Subcircuit (spi_subcircuit.py)

**Circuit Structure:**
```
Root (spi_subcircuit)
  └─ SPI_Driver (subcircuit)
      └─ R1[1] connected to DATA_IN net (from root)
```

**JSON Output:**
```json
"nets": {
  "DATA_IN": [
    {
      "component": "R1",
      "pin": {"number": "1", "name": "~", "type": "passive"}
    }
  ]
}
```

**Observations:**
- ❌ NO hierarchical labels generated
- ❌ Warning: `Net 'DATA_IN' has only 1 connection(s) - may indicate connection issue`
- ✅ JSON correctly serializes the net with 1 connection
- ❌ Schematic writer does NOT create hierarchical label

**File Check:**
```bash
$ grep "hierarchical_label" SPI_Driver.kicad_sch
# No results - NO LABELS
```

---

### Test 2: Nested Resistor Dividers (test2_nested_dividers.py)

**Circuit Structure:**
```
Root (nested_dividers)
  └─ Divider_Level1 (subcircuit)
      ├─ R1[1] → VIN (1 connection)
      ├─ R1[2] → VOUT1 (2 connections: R1+R2)
      ├─ R2[1] → VOUT1 (2 connections: R1+R2)
      ├─ R2[2] → GND (1 connection)
      └─ Divider_Level2 (nested subcircuit)
          ├─ R3[1] → VOUT1 (1 connection)
          ├─ R3[2] → VOUT2 (2 connections: R3+R4)
          ├─ R4[1] → VOUT2 (2 connections: R3+R4)
          └─ R4[2] → GND (1 connection)
```

**JSON Output (Level 1):**
```json
"nets": {
  "VIN": [
    {"component": "R1", "pin": {"number": "1"}}
  ],
  "VOUT1": [
    {"component": "R1", "pin": {"number": "2"}},
    {"component": "R2", "pin": {"number": "1"}}
  ],
  "GND": [
    {"component": "R2", "pin": {"number": "2"}}
  ]
}
```

**Observations:**

#### Level 1 (Divider_Level1.kicad_sch):
- ✅ Hierarchical label for **GND** generated (1 connection: R2)
- ✅ Hierarchical label for **VOUT1** generated (2 connections: R1+R2)
- ❌ NO hierarchical label for **VIN** (1 connection: R1)

Wait, this contradicts my hypothesis! Let me re-check:

```bash
$ grep "hierarchical_label" Divider_Level1.kicad_sch
  (hierarchical_label "GND"
  (hierarchical_label "VOUT1"
```

So GND has a label even with only 1 connection (R2[2])! But VIN with 1 connection (R1[1]) does NOT have a label.

#### Level 2 (Divider_Level2.kicad_sch):
- ❌ NO hierarchical labels at all

**File Check:**
```bash
$ grep "hierarchical_label" Divider_Level2.kicad_sch
# No results - NO LABELS
```

---

## Revised Hypothesis

The pattern is NOT simply "2+ connections = label".

Let me check what's different about GND vs VIN and VOUT1:

### Possible Factors:

1. **GND is a power net?**
   - GND might be treated specially as a global power net
   - Power nets may have different label generation rules

2. **Net direction (input vs output)?**
   - VIN is input to Level 1 (from root)
   - VOUT1 is output from Level 1 (to root)
   - GND is... both? (passed down from root)

3. **Connection count at subcircuit boundary?**
   - Maybe the algorithm counts connections across hierarchy levels?

4. **Position in circuit tree?**
   - Level 1 is directly under root
   - Level 2 is nested deeper - maybe deeper nesting breaks label generation?

---

## Data Structure Investigation

The JSON uses **ARRAY format** for nets:
```json
"nets": {
  "NET_NAME": [
    {component, pin},
    {component, pin}
  ]
}
```

But according to the PRD research, `circuit_loader.py` expects:
```json
"nets": {
  "NET_NAME": {
    "nodes": [
      {component, pin},
      {component, pin}
    ]
  }
}
```

**Key Question:** Is the JSON export using the wrong format? Should it be an object with "nodes" array instead of a direct array?

---

## Next Steps

1. **Check if GND is treated as power net:**
   ```bash
   grep -A 5 '"GND"' test2_nested_output/nested_dividers.json
   # Look for is_power or power_symbol fields
   ```

2. **Compare circuit_loader.py expectations:**
   - Read circuit_loader.py line 258-309
   - Check if it expects `net_data.get("nodes", [])` or direct array

3. **Check netlist_exporter.py:**
   - See how nets are serialized to JSON
   - Confirm if array format is intentional

4. **Add debug logs to schematic_writer.py:**
   - Log which nets are being processed in `_add_pin_level_net_labels()`
   - Log when hierarchical labels are created vs skipped
   - Log net.connections content

---

## Confirmed Observations

✅ **JSON serialization works** - Nets are serialized with component connections
✅ **Single-connection nets are serialized** - DATA_IN with R1 is in JSON
✅ **Warning message appears** - "Net 'X' has only 1 connection(s)"
✅ **Some labels ARE generated** - Test 2 Level 1 has GND and VOUT1 labels
❌ **Not all expected labels generated** - VIN missing in Level 1, all missing in Level 2
❌ **Inconsistent behavior** - GND (1 conn) gets label, VIN (1 conn) doesn't

---

## Files for Further Investigation

1. `src/circuit_synth/core/netlist_exporter.py` - How nets are serialized
2. `src/circuit_synth/kicad/sch_gen/circuit_loader.py` - How nets are loaded
3. `src/circuit_synth/kicad/sch_gen/schematic_writer.py:1261-1511` - Label generation logic
4. `src/circuit_synth/kicad/schematic/label_manager.py` - Label management

---

## Test Files

- **Test 1:** `tests/bidirectional/debug_hierarchical_labels/test1_failing_spi.py`
- **Test 2:** `tests/bidirectional/debug_hierarchical_labels/test2_nested_dividers.py`
- **Output 1:** `tests/bidirectional/debug_hierarchical_labels/test1_spi_output/`
- **Output 2:** `tests/bidirectional/debug_hierarchical_labels/test2_nested_output/`

---

## ✅ ROOT CAUSE IDENTIFIED & FIXED

### The Bug

**File:** `src/circuit_synth/kicad/schematic/component_manager.py`
**Method:** `find_component()` (line 384)

**Problem:** Components are stored in `_component_index` with keys like `"R1_unit1"`, but `find_component("R1")` was looking for key `"R1"` which doesn't exist.

```python
# In add_component() - line 109:
component_key = f"{reference}_unit{unit}"  # e.g., "R1_unit1"
self._component_index[component_key] = component  # line 185

# In find_component() - line 384 (BEFORE FIX):
return self._component_index.get(reference)  # Looks for "R1", not "R1_unit1"!
```

### The Fix

**File:** `src/circuit_synth/kicad/schematic/component_manager.py`
**Method:** `find_component()`

```python
def find_component(self, reference: str) -> Optional[SchematicSymbol]:
    """Find a component by reference."""
    # For multi-unit components, components are indexed as "{reference}_unit{n}"
    # Try unit 1 first (most common case)
    component_key = f"{reference}_unit1"
    comp = self._component_index.get(component_key)
    if comp:
        return comp

    # If not found with unit1, search for any unit with this reference
    for key, component in self._component_index.items():
        if key.startswith(f"{reference}_unit"):
            return component

    # Not found
    return None
```

### Test Results After Fix

**Test 1 (Single resistor):**
- ✅ Hierarchical label "DATA_IN" generated in SPI_Driver.kicad_sch

**Test 2 (Nested dividers):**
- ✅ Level 1: VIN, VOUT1, GND labels all present
- ✅ Level 2: VOUT1, VOUT2, GND labels all present

### Files Changed

1. `src/circuit_synth/kicad/schematic/component_manager.py` - Fixed `find_component()` method

### Verification

```bash
cd tests/bidirectional/debug_hierarchical_labels

# Test 1
uv run python test1_failing_spi.py
grep "hierarchical_label" test1_spi_output/SPI_Driver.kicad_sch
# Result: ✅ Label found

# Test 2
uv run python test2_nested_dividers.py
grep "hierarchical_label" test2_nested_output/Divider_Level1.kicad_sch
# Result: ✅ VIN, VOUT1, GND labels found
grep "hierarchical_label" test2_nested_output/Divider_Level2.kicad_sch
# Result: ✅ VOUT1, VOUT2, GND labels found
```

---

**Status:** ✅ **FIXED**
**Issue #427:** Ready to close after commit and testing
