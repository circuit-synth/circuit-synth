# Corrected Understanding: Round-Trip Update System

**Date**: 2025-10-12
**Status**: Under Review

## Executive Summary

After code review, here's what **actually** happens:

### TWO Distinct Systems

1. **Canonical Circuit Matching** (`canonical.py`)
   - **Used**: Position preservation during INITIAL GENERATION
   - **When**: Existing schematic detected during `generate_project()`
   - **Location**: `main_generator.py:728-809`
   - **How**: Matches components by connection topology, preserves positions

2. **APISynchronizer Matching** (`synchronizer.py`)
   - **Used**: Component updates during UPDATE mode
   - **When**: `_update_existing_project()` called
   - **Accessed via**: `SyncAdapter` or `HierarchicalSynchronizer`
   - **How**: 3 strategies (Reference, Connection, ValueFootprint)

## Critical Discovery: Parser Bug

**PROBLEM FOUND** in `synchronizer.py:361-370`:

```python
def _save_schematic(self):
    """Save the modified schematic."""
    # Convert schematic to S-expression
    sexp_data = self.parser.from_schematic(self.schematic)  # ❌ self.parser NOT INITIALIZED

    # Add lib_symbols definitions for all components
    self._add_lib_symbols_to_sexp(sexp_data)

    # Write to file
    self.parser.write_file(sexp_data, str(self.schematic_path))
```

`self.parser` is **NEVER initialized** in `__init__`! This would cause `AttributeError`.

**This means the save path is broken or not being used.**

## Actual Update Flow

From `main_generator.py:412-478`:

```python
def _update_existing_project(self, json_file: str, draw_bounding_boxes: bool = False):
    """Update existing project using synchronizer to preserve manual work"""

    # Load circuits
    from .circuit_loader import load_circuit_hierarchy
    top_circuit, sub_dict = load_circuit_hierarchy(json_file)

    # Check if hierarchical
    has_subcircuits = bool(sub_dict)

    if has_subcircuits:
        # Uses HierarchicalSynchronizer
        synchronizer = HierarchicalSynchronizer(
            project_path=str(project_path),
            preserve_user_components=True
        )
    else:
        # Uses SyncAdapter (wraps APISynchronizer)
        synchronizer = SyncAdapter(
            project_path=str(project_path),
            preserve_user_components=True
        )

    # Perform sync
    sync_report = synchronizer.sync_with_circuit(top_circuit)

    # Post-processing
    self._fix_all_schematic_project_names()
```

## Key Questions to Answer

### 1. Does Wire/Label Preservation Actually Work?

**Evidence**:
- Lines 138-144 in `synchronizer.py` show wires and labels ARE loaded
- But `_save_schematic()` has a parser bug - may not be called
- Need to check what `SyncAdapter` and `HierarchicalSynchronizer` actually do

### 2. How Does Saving Actually Happen?

Since `self.parser` is not initialized, one of these must be true:
- A) `APISynchronizer._save_schematic()` is never called (dead code)
- B) `SyncAdapter`/`HierarchicalSynchronizer` use a different save method
- C) They use kicad-sch-api's `schematic.save()` directly

**Need to check**: `SyncAdapter` and `HierarchicalSynchronizer` implementation

### 3. What About Position Preservation?

**TWO SEPARATE MECHANISMS**:

**During Initial Generation** (`main_generator.py:728-809`):
```python
# Check if existing schematic file exists
existing_sch_path = self.project_dir / f"{c_name}.kicad_sch"
if existing_sch_path.exists():
    # Load existing schematic
    schematic = ksa.Schematic.load(str(existing_sch_path))

    # Create canonical circuits
    existing_canonical = CanonicalCircuit(existing_connections)
    new_canonical = CanonicalCircuit.from_circuit(circ)

    # Match using canonical matching
    matcher = CircuitMatcher()
    matches = matcher.match(existing_canonical, new_canonical)

    # Preserve positions for matches
    for existing_ref, new_ref in matches.items():
        existing_positions[new_ref] = (x, y)
```

**During Update** (via `APISynchronizer`):
- Uses 3 matching strategies
- Updates component values/footprints
- **Does NOT explicitly handle positions** (assumes schematic.components keeps positions?)

## What We Need to Verify

1. ✅ **Canonical matching for position preservation** - EXISTS, used during generation
2. ❓ **Wire preservation in update mode** - Code loads wires but save path unclear
3. ❓ **Label preservation in update mode** - Same as wires
4. ❌ **APISynchronizer save is broken** - Parser not initialized
5. ❓ **How do SyncAdapter/HierarchicalSynchronizer save?** - Need to check

## Next Steps

1. Read `SyncAdapter` implementation to see how it saves
2. Read `HierarchicalSynchronizer` implementation
3. Verify if they use `kicad-sch-api`'s `schematic.save()` directly
4. Test wire/label preservation with a real example
5. Fix or remove dead `_save_schematic()` code in APISynchronizer

## Corrected Architecture Diagram

```
User runs Python → generate_kicad_project()
    ↓
_check_existing_project()
    ↓
    ├─ NO EXISTING → GENERATION PATH
    │   └─> _collision_place_all_circuits()
    │       ├─> Check for existing schematic
    │       ├─> If exists: Use CANONICAL MATCHING for positions
    │       └─> Place new components collision-free
    │   └─> SchematicWriter.generate_s_expr()
    │   └─> Write files
    │
    └─ YES EXISTING → UPDATE PATH
        └─> _update_existing_project()
            ├─> HierarchicalSynchronizer (if has subcircuits)
            │   └─> ??? (need to check implementation)
            │
            └─> SyncAdapter (if flat)
                └─> APISynchronizer.sync_with_circuit()
                    ├─> Load existing schematic (with wires/labels)
                    ├─> Match using 3 strategies
                    ├─> Update matched components
                    ├─> Add/preserve/remove unmatched
                    └─> Save somehow (NOT via _save_schematic!)
```

## Summary

**What We Thought**: Canonical circuits used for matching in update mode
**Reality**: Canonical circuits ONLY for position preservation in generation mode

**What We Thought**: APISynchronizer is the core update engine
**Reality**: It's wrapped by SyncAdapter/HierarchicalSynchronizer

**What We Thought**: _save_schematic() handles saving
**Reality**: It's broken (parser not initialized) - likely dead code

**What We Need**: Check how SyncAdapter/HierarchicalSynchronizer actually save changes!
