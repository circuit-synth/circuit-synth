# Product Requirements Document: Component Rename Detection

## Overview

**Feature**: Intelligent component rename detection for bidirectional synchronization
**Priority**: HIGH (blocks Test 13 and common user workflow)
**Issue**: #338, Test 13
**Status**: In Development

## Problem Statement

### Current Behavior (BROKEN)

When a user renames a component reference in Python code (e.g., R1 → R2), the bidirectional sync:
1. ❌ Does NOT update the reference in the schematic
2. ❌ Incorrectly reports "Keep: R1 (matches Python)"
3. ❌ Leaves schematic with old reference "R1"

**Example:**
```python
# Before: r1 = Component(ref="R1", value="10k", ...)
# After:  r2 = Component(ref="R2", value="10k", ...)
# Result in schematic: Still shows "R1" ❌
```

### Root Cause

The `ValueFootprintStrategy` matches components by value+footprint similarity, causing it to match R2→R1 because they have the same electrical properties. This prevents the reference from being updated.

### User Impact

- **Severity**: HIGH
- **Frequency**: Common (users rename components during iterative design)
- **Workaround**: Delete schematic and regenerate (loses manual layout work)
- **User Pain**: "I renamed R1 to R2 in my code, why is KiCad still showing R1?"

## Goals

### Primary Goals

1. **Detect renames accurately**: Identify when a component reference has changed
2. **Update references**: Change component reference in schematic to match Python code
3. **Preserve position**: Keep component in same location (don't re-layout)
4. **Preserve connections**: Maintain all net connections and labels

### Secondary Goals

5. **Handle batch renames**: Support renaming multiple components in one sync
6. **Detect reference conflicts**: Warn if new reference already exists
7. **Support undo**: Allow reverting renames if needed

### Non-Goals

- Automatic reference assignment
- Reference validation (e.g., checking R1 vs C1 for resistor)
- Cross-project reference tracking

## Success Criteria

### Test Case: Single Component Rename

**Setup:**
```python
# Initial circuit
r1 = Component(ref="R1", value="10k", footprint="R_0603")
```

**Action:**
```python
# Rename to R2
r2 = Component(ref="R2", value="10k", footprint="R_0603")
# Regenerate project
```

**Expected Result:**
- ✅ Schematic shows "R2" (not "R1")
- ✅ Component stays at same position
- ✅ All connections preserved
- ✅ Sync summary: "🔄 Rename: R1 → R2"

## Proposed Solution

### Approach: Position-Based Rename Detection Strategy

Add a new matching strategy that runs BEFORE ValueFootprintStrategy:

```python
class PositionRenameStrategy(SyncStrategy):
    """
    Detect renames by matching on position + properties.

    Logic: If a KiCad component matches Python component on:
    - Position (within tolerance)
    - Symbol
    - Value
    - Footprint
    But has DIFFERENT reference → This is a RENAME
    """
```

### Strategy Order (NEW)

```
1. ReferenceMatchStrategy      # Exact ref match (no rename)
2. ConnectionMatchStrategy      # Match by net topology
3. PositionRenameStrategy       # 🆕 Match by position (detect renames)
4. ValueFootprintStrategy       # Match by properties (fallback)
```

### Position Matching Logic

**Match Criteria:**
- Same position (within 2.54mm tolerance - one grid unit)
- Same symbol (Device:R)
- Same value (10k)
- Same footprint (R_0603_1608Metric)
- **Different reference** (R1 vs R2) ← This indicates rename

**Why Position is Reliable:**
- Users don't move components when just renaming
- Circuit-synth preserves positions during sync
- Position is unique within a schematic
- More reliable than value+footprint (not unique)

### Implementation Details

#### 1. Add PositionRenameStrategy

**Location:** `src/circuit_synth/kicad/schematic/sync_strategies.py`

```python
class PositionRenameStrategy(SyncStrategy):
    """Match components by position to detect renames."""

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine
        self.position_tolerance = 2.54  # mm (one KiCad grid unit)

    def match_components(
        self, circuit_components: Dict, kicad_components: Dict
    ) -> Dict[str, str]:
        matches = {}
        used_refs = set()

        for circuit_id, circuit_comp in circuit_components.items():
            circuit_ref = circuit_comp["reference"]

            # Skip if already matched by reference
            if circuit_ref in kicad_components:
                continue

            # Get position from circuit component
            circuit_pos = circuit_comp.get("position")
            if not circuit_pos:
                continue

            # Search for KiCad components at same position
            for kicad_ref, kicad_comp in kicad_components.items():
                if kicad_ref in used_refs:
                    continue

                # Check position match
                if not self._positions_match(circuit_pos, kicad_comp.position):
                    continue

                # Check properties match (symbol, value, footprint)
                if not self._properties_match(circuit_comp, kicad_comp):
                    continue

                # Found match at same position with different reference
                # This is a RENAME!
                matches[circuit_id] = kicad_ref
                used_refs.add(kicad_ref)
                break

        return matches

    def _positions_match(self, pos1, pos2) -> bool:
        """Check if positions match within tolerance."""
        dx = abs(pos1.x - pos2.x)
        dy = abs(pos1.y - pos2.y)
        return dx < self.position_tolerance and dy < self.position_tolerance

    def _properties_match(self, circuit_comp: Dict, kicad_comp) -> bool:
        """Check if electrical properties match."""
        return (
            circuit_comp["symbol"] == kicad_comp.lib_id
            and circuit_comp["value"] == kicad_comp.value
            and circuit_comp.get("footprint") == kicad_comp.footprint
        )
```

#### 2. Handle Reference Updates

**Problem:** `update_component(ref="R1", ...)` uses ref as KEY, not as updatable field.

**Solution:** Add `rename_component()` method:

**Location:** `src/circuit_synth/kicad/schematic/component_manager.py`

```python
def rename_component(
    self,
    old_ref: str,
    new_ref: str
) -> bool:
    """
    Rename a component's reference designator.

    Args:
        old_ref: Current reference (e.g., "R1")
        new_ref: New reference (e.g., "R2")

    Returns:
        True if renamed successfully
    """
    component = self.find_component(old_ref)
    if not component:
        logger.error(f"Cannot rename: component {old_ref} not found")
        return False

    # Check if new reference already exists
    if self.find_component(new_ref):
        logger.error(f"Cannot rename to {new_ref}: reference already exists")
        return False

    # Update the reference
    component.reference = new_ref

    # Update all references in schematic
    # - Update component instances
    # - Update hierarchical labels (if any reference the old ref)
    # - Update any text annotations

    logger.info(f"Renamed component {old_ref} → {new_ref}")
    return True
```

#### 3. Track Renames in Sync Report

**Location:** `src/circuit_synth/kicad/schematic/synchronizer.py`

```python
@dataclass
class SyncReport:
    """Report of synchronization operations."""
    matched: Dict[str, str] = field(default_factory=dict)
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    renamed: List[Tuple[str, str]] = field(default_factory=list)  # 🆕 (old, new)
    labels_added: List[Tuple[str, str, str]] = field(default_factory=list)
    labels_removed: List[Tuple[str, str, str]] = field(default_factory=list)
```

#### 4. Update Sync Summary Display

```python
# In _print_sync_summary()

# Components that were renamed
if report.renamed:
    for old_ref, new_ref in sorted(report.renamed):
        print(f"   🔄 Rename: {old_ref} → {new_ref}")
```

### Strategy Integration

**Update synchronizer initialization:**

```python
self.strategies = [
    ReferenceMatchStrategy(self.search_engine),
    ConnectionMatchStrategy(self.net_matcher),
    PositionRenameStrategy(self.search_engine),  # 🆕 Add before ValueFootprint
    ValueFootprintStrategy(self.search_engine),
]
```

**Update matching logic:**

```python
def _process_matches(self, circuit_components, kicad_components, matches, report):
    """Process matched components for updates or renames."""
    for circuit_id, kicad_ref in matches.items():
        circuit_comp = circuit_components[circuit_id]
        kicad_comp = kicad_components[kicad_ref]

        circuit_ref = circuit_comp["reference"]

        # Check if this is a rename
        if circuit_ref != kicad_ref:
            # This is a RENAME
            success = self.component_manager.rename_component(
                old_ref=kicad_ref,
                new_ref=circuit_ref
            )
            if success:
                report.renamed.append((kicad_ref, circuit_ref))
                # Update kicad_components dict key for subsequent operations
                kicad_components[circuit_ref] = kicad_components.pop(kicad_ref)
                kicad_comp.reference = circuit_ref

        # Check if update needed (value, footprint, etc.)
        if self._needs_update(circuit_comp, kicad_comp):
            success = self.component_manager.update_component(
                circuit_ref,  # Use NEW reference
                value=circuit_comp["value"],
                footprint=circuit_comp.get("footprint"),
            )
            if success:
                report.modified.append(circuit_ref)
```

## Edge Cases

### 1. Conflicting Renames

**Scenario:** User renames R1→R2, but R2 already exists

**Behavior:**
- Detect conflict during rename
- Log error: "Cannot rename R1 to R2: reference already exists"
- Keep R1 unchanged
- Report: "⚠️  Rename failed: R1 → R2 (conflict)"

### 2. Batch Renames

**Scenario:** User swaps references (R1→R2, R2→R1)

**Behavior:**
- Detect both as renames
- Use temporary references to avoid conflicts
- Perform renames in safe order
- Report both: "🔄 Rename: R1 → R2" and "🔄 Rename: R2 → R1"

### 3. Move + Rename

**Scenario:** User both renames R1→R2 AND moves component

**Behavior:**
- Position-based matching still works (tolerance allows small moves)
- For large moves (>2.54mm): may not match, treat as delete+add
- This is acceptable behavior (large move is effectively new placement)

### 4. Multiple Components at Same Position

**Scenario:** Two components accidentally at same position

**Behavior:**
- PositionRenameStrategy matches first one found
- Second component handled by ValueFootprintStrategy or added as new
- Position collision should be detected and warned separately

## Testing Plan

### Unit Tests

```python
def test_position_rename_strategy():
    """Test position-based rename detection."""
    circuit_comps = {
        "R2_uuid": {
            "reference": "R2",
            "value": "10k",
            "symbol": "Device:R",
            "footprint": "R_0603",
            "position": Point(30.48, 35.56),
        }
    }

    kicad_comps = {
        "R1": SchematicSymbol(
            reference="R1",
            value="10k",
            lib_id="Device:R",
            footprint="R_0603",
            position=Point(30.48, 35.56),  # Same position
        )
    }

    strategy = PositionRenameStrategy(search_engine)
    matches = strategy.match_components(circuit_comps, kicad_comps)

    assert matches == {"R2_uuid": "R1"}  # Detected rename
```

### Integration Tests

**Test 13: Component Rename**
- Initial: R1 at (30.48, 35.56)
- Rename: R1 → R2 in Python
- Regenerate
- Verify: Schematic shows R2 at (30.48, 35.56)

**Test 13b: Rename + Value Change**
- Initial: R1, 10k
- Change: R1 → R2, 4.7k
- Verify: Reference updated AND value updated

**Test 13c: Rename Conflict**
- Initial: R1, R2 (both exist)
- Change: R1 → R2 (conflict)
- Verify: Error reported, R1 unchanged

### Regression Tests

- Test 11: Add net to components (should still work)
- Test 12: Add component to net (should still work)
- Test 07: Delete component (should still work)

## Metrics

### Success Metrics

- ✅ Test 13 passes
- ✅ Issue #338 closed
- ✅ No regressions in Tests 1-12
- ✅ User feedback: "Rename works as expected"

### Performance Metrics

- Position search: O(n²) worst case, acceptable for <1000 components
- Rename operation: O(1) for reference update
- Total sync time increase: <10ms for typical circuits

## Rollout Plan

### Phase 1: Implementation (Current)
1. Add PositionRenameStrategy
2. Add rename_component() method
3. Update SyncReport for renames
4. Add unit tests

### Phase 2: Testing
1. Run Test 13
2. Run regression tests (1-12)
3. Test edge cases (conflicts, batch renames)

### Phase 3: Documentation
1. Update bidirectional sync documentation
2. Add rename example to user guide
3. Document strategy order and behavior

### Phase 4: Release
1. Merge to main
2. Include in next release (0.11.1)
3. Update changelog
4. Close issue #338

## Future Enhancements

### V2: Intelligent Reference Assignment

**Goal:** Suggest or auto-fix reference conflicts

**Example:**
```
User renames R1 → R2, but R2 exists
System suggests: "R2 already exists. Rename to R3 instead?"
```

### V3: Reference Validation

**Goal:** Warn about incorrect reference types

**Example:**
```
User creates capacitor with ref="R1"
System warns: "R1 is a resistor reference, did you mean C1?"
```

### V4: Undo Support

**Goal:** Allow reverting renames

**Example:**
```
After rename R1 → R2
User runs: circuit-synth undo
System reverts: R2 → R1
```

## Dependencies

- ✅ SchematicSymbol has position attribute
- ✅ ComponentManager exists
- ✅ SyncStrategy base class exists
- 🆕 Need: component_manager.rename_component()
- 🆕 Need: PositionRenameStrategy class

## Timeline

- **Day 1**: Implement PositionRenameStrategy (2 hours)
- **Day 1**: Add rename_component() (1 hour)
- **Day 1**: Update sync logic (1 hour)
- **Day 1**: Test and debug (1 hour)
- **Total**: ~5 hours

## Approval

- **Technical Lead**: [Pending]
- **Product Owner**: [Pending]
- **Stakeholders**: Shane Mattner (User feedback)
