# Round-Trip Schematic Updates - PRD

**Status:** ✅ **IMPLEMENTED & TESTED**
**Version:** 1.0
**Date:** 2025-10-12

---

## Overview

Users can now modify KiCad schematics manually (move components, route wires, add annotations) and those changes are preserved when re-generating from updated Python circuit definitions.

## User Workflow

```python
# 1. Generate initial circuit
@circuit(name="my_circuit")
def my_circuit():
    r1 = Component("Device:R", ref="R1", value="10k", ...)
    # ... more components

c = my_circuit()
c.generate_kicad_project("my_project")  # Creates KiCad files

# 2. User opens KiCad and makes manual edits:
#    - Moves R1 to better position
#    - Routes wires between components
#    - Adds labels and annotations

# 3. Update Python code
@circuit(name="my_circuit")
def my_circuit():
    r1 = Component("Device:R", ref="R1", value="22k", ...)  # Changed value
    # ... same components

c = my_circuit()
c.generate_kicad_project("my_project", force_regenerate=False)  # Update mode

# 4. Manual edits preserved! R1 is still in moved position, value updated to 22k
```

## What's Preserved

| Element | Preserved? | Notes |
|---------|-----------|-------|
| Component positions | ✅ Yes | Via canonical circuit matching |
| Component values | ✅ Updated | Updates propagate from Python |
| Component footprints | ✅ Updated | Updates propagate from Python |
| Manual wires | ✅ Yes | Preserved in schematic |
| Manual labels | ✅ Yes | Preserved in schematic |
| Annotations | ✅ Yes | Text boxes, notes, etc. |
| Power symbols | ✅ Yes | User-added power flags |

## Technical Implementation

### Architecture

Two systems work together:

1. **Position Preservation** (during generation)
   - Uses canonical circuit matching (`canonical.py`)
   - Matches components by connection topology
   - Extracts positions from existing schematic
   - Applies preserved positions during placement
   - Location: `main_generator.py:728-809`

2. **Update System** (during re-generation)
   - Uses `APISynchronizer` for component updates
   - Three matching strategies: Reference, Connection, ValueFootprint
   - Updates component properties while preserving positions
   - Preserves wires/labels via kicad-sch-api's native save
   - Location: `synchronizer.py`

### The Bug That Was Fixed

**Problem:**
```python
def _save_schematic(self):
    sexp_data = self.parser.from_schematic(self.schematic)  # ❌ self.parser doesn't exist
    self._add_lib_symbols_to_sexp(sexp_data)
    self.parser.write_file(sexp_data, str(self.schematic_path))
```

**Solution:**
```python
def _save_schematic(self):
    """Save using kicad-sch-api's native save."""
    self.schematic.save(str(self.schematic_path), preserve_format=True)
    logger.info(f"Saved schematic to {self.schematic_path}")
```

**Benefits:**
- Fixes AttributeError (parser was never initialized)
- Reduces complexity from 60+ lines to 3 lines
- Uses kicad-sch-api's proven save mechanism
- Automatically preserves all schematic elements

## Testing

### Test Pattern (Generate → Modify → Generate → Verify)

```python
# 1. Generate initial circuit
c.generate_kicad_project("test", force_regenerate=True)

# 2. Modify schematic manually
sch = kicad_sch_api.Schematic.load("test.kicad_sch")
r1 = sch.components.get("R1")
r1.position = Point(180.0, 120.0)  # Move component
sch.save("test.kicad_sch", preserve_format=True)

# 3. Re-generate in update mode
c.generate_kicad_project("test", force_regenerate=False)

# 4. Verify position preserved
sch_after = kicad_sch_api.Schematic.load("test.kicad_sch")
r1_after = sch_after.components.get("R1")
assert r1_after.position == Point(180.0, 120.0)  # ✅ Preserved!
```

### Test Coverage

**Integration Tests** (`tests/integration/test_roundtrip_preservation.py`):
- ✅ Component position preservation
- ✅ Value updates with position preservation
- ✅ Wire preservation across updates
- ✅ Label preservation across updates

**Manual Scripts:**
- `test_manual_roundtrip.py` - Interactive test with KiCad visualization
- `test_automated_roundtrip.py` - Quick automated verification

**Results:**
```bash
$ uv run pytest tests/integration/test_roundtrip_preservation.py -v
test_component_position_preservation PASSED
test_value_update_with_position_preservation PASSED
test_wire_preservation PASSED
test_label_preservation PASSED
```

## Known Limitations

1. **Component type changes** - Changing symbol (e.g., R → custom resistor) requires regeneration
2. **Pin count changes** - Changing footprint with different pins requires regeneration
3. **Hierarchical sheets** - Minor logging issue (`'Schematic' object has no attribute 'sheets'`) but doesn't affect functionality

## Future Enhancements (Post-v1)

- [ ] Net name change detection and warning
- [ ] Dry-run preview of changes before applying
- [ ] Automatic backup before risky updates
- [ ] Change summary report ("Updated 3 values, preserved 45 edits")
- [ ] Performance optimization for 500+ component schematics

## References

- **Main Generator:** `src/circuit_synth/kicad/sch_gen/main_generator.py`
- **Synchronizer:** `src/circuit_synth/kicad/schematic/synchronizer.py`
- **Canonical Matching:** `src/circuit_synth/kicad/canonical.py`
- **Tests:** `tests/integration/test_roundtrip_preservation.py`
- **PR:** https://github.com/circuit-synth/circuit-synth/pull/152
