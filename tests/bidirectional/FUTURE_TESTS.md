# Future Bidirectional Test Suite

This document outlines comprehensive bidirectional test scenarios for circuit-synth.
Tests are organized by category and prioritized by practical importance.

## Current Status (Tests 01-08 Complete)

- ✅ 01: Blank circuit
- ✅ 02: KiCad → Python (basic import)
- ✅ 03: Python → KiCad (incremental addition)
- ✅ 04: Round-trip (full cycle)
- ✅ 05: Add resistor KiCad → Python
- ✅ 06: Add component Python → KiCad
- ✅ 07: Delete component Python → KiCad
- ✅ 07_b: Delete component KiCad → Python
- ✅ 08: Modify component attributes + position preservation

## High Priority Tests (Next Batch)

### Net/Connection Tests
**Why important:** Nets are fundamental to circuit functionality. Connection bugs break designs.

- **09: Add net between components**
  - Python → KiCad: Connect two resistors in series programmatically
  - KiCad → Python: Draw wire between components, sync to Python
  - Validates: Net creation, pin connectivity

- **10: Remove net**
  - Python → KiCad: Remove connection between components
  - KiCad → Python: Delete wire in schematic, sync to Python
  - Validates: Net deletion, component isolation

- **11: Rename net**
  - Python → KiCad: Change net name via label
  - KiCad → Python: Edit label in KiCad, sync name change
  - Validates: Net naming, label synchronization

- **12: Change pin connection**
  - Python → KiCad: Move wire from pin 1 to pin 2 on component
  - KiCad → Python: Reconnect wire to different pin
  - Validates: Pin-level connection accuracy

- **13: Merge nets**
  - Python → KiCad: Connect two separate nets into one
  - KiCad → Python: Draw wire connecting two nets
  - Validates: Net merging logic, naming precedence

- **14: Split net**
  - Python → KiCad: Break one net into two
  - KiCad → Python: Delete wire segment, creating split
  - Validates: Net splitting, automatic renaming

### Power/Ground Tests
**Why important:** Power connections are critical and often have special handling.

- **15: Add power symbol**
  - Python → KiCad: Connect component to VCC
  - KiCad → Python: Place power symbol, connect wire
  - Validates: Power net recognition, power symbols

- **16: Add ground symbol**
  - Python → KiCad: Connect component to GND
  - KiCad → Python: Place ground symbol
  - Validates: Ground net recognition

- **17: Multiple power domains**
  - Python → KiCad: Add VCC, 3V3, 5V power rails
  - KiCad → Python: Create multiple power nets
  - Validates: Multiple power net handling

### Component Modification Tests
**Why important:** Real designs evolve with component swaps and changes.

- **18: Swap component type**
  - Python → KiCad: Change resistor to capacitor keeping connections
  - KiCad → Python: Replace component symbol in KiCad
  - Validates: Component type changes, connection preservation

- **19: Component orientation**
  - Python → KiCad: Rotate component 90/180/270 degrees
  - KiCad → Python: Rotate/mirror in KiCad
  - Validates: Orientation preservation, pin position recalculation

- **20: Multi-unit components**
  - Python → KiCad: Add quad op-amp with all 4 units
  - KiCad → Python: Place multi-unit component, use different units
  - Validates: Multi-unit handling, unit assignment

## Medium Priority Tests

### Hierarchical/Subcircuit Tests
**Why important:** Real projects use hierarchy for organization.

- **21: Add subcircuit sheet**
  - Python → KiCad: Create hierarchical sheet from Python
  - KiCad → Python: Add sheet in KiCad, import to Python
  - Validates: Hierarchical sheet creation

- **22: Remove subcircuit sheet**
  - Python → KiCad: Remove sheet from hierarchy
  - KiCad → Python: Delete sheet in KiCad
  - Validates: Sheet deletion, connection cleanup

- **23: Component changes subcircuits**
  - Python → KiCad: Move component from root to subcircuit
  - KiCad → Python: Cut/paste component between sheets
  - Validates: Cross-sheet component movement

- **24: Rename subcircuit**
  - Python → KiCad: Rename sheet
  - KiCad → Python: Edit sheet name in KiCad
  - Validates: Sheet name synchronization

- **25: Nested subcircuits**
  - Python → KiCad: Create 3-level hierarchy
  - KiCad → Python: Add nested sheets
  - Validates: Deep hierarchy handling

### Label/Annotation Tests
**Why important:** Labels enable cross-sheet connections and net naming.

- **26: Add global label**
  - Python → KiCad: Create global label for cross-sheet connection
  - KiCad → Python: Place global label in KiCad
  - Validates: Global label creation, net naming

- **27: Add local label**
  - Python → KiCad: Add local label to name net within sheet
  - KiCad → Python: Place local label
  - Validates: Local label handling

- **28: Change label scope**
  - Python → KiCad: Convert local label to global
  - KiCad → Python: Change label type in KiCad
  - Validates: Label type conversion

- **29: Add junction**
  - Python → KiCad: Create junction on T-connection
  - KiCad → Python: Place junction dot
  - Validates: Junction creation, multi-point nets

- **30: Remove junction**
  - Python → KiCad: Remove junction (may split net)
  - KiCad → Python: Delete junction
  - Validates: Junction removal, net topology

### Text/Documentation Tests
**Why important:** Design documentation and notes need to survive round-trips.

- **31: Add text annotation**
  - Python → KiCad: Add design notes to schematic
  - KiCad → Python: Place text in KiCad
  - Validates: Text preservation

- **32: Add graphic elements**
  - Python → KiCad: Add boxes/lines for organization
  - KiCad → Python: Draw graphics in KiCad
  - Validates: Graphical element handling

- **33: Add no-connect flag**
  - Python → KiCad: Mark unused pins as NC
  - KiCad → Python: Place NC flag in KiCad
  - Validates: No-connect handling

## Lower Priority Tests

### Complex Workflow Tests
**Why important:** Real design changes involve bulk operations.

- **34: Bulk component add**
  - Python → KiCad: Add 10 resistors at once
  - KiCad → Python: Place multiple components
  - Validates: Bulk operations, performance

- **35: Bulk component remove**
  - Python → KiCad: Remove multiple components
  - KiCad → Python: Select and delete multiple components
  - Validates: Bulk deletion

- **36: Copy-paste component**
  - Python → KiCad: Duplicate component with connections
  - KiCad → Python: Copy/paste in KiCad
  - Validates: Component duplication, connection copying

- **37: Replace subcircuit contents**
  - Python → KiCad: Change entire subcircuit implementation
  - KiCad → Python: Redesign inside sheet
  - Validates: Sheet content replacement, port preservation

### Edge Cases
**Why important:** Edge cases reveal synchronization bugs.

- **38: Empty subcircuit**
  - Python → KiCad: Create sheet with no components
  - KiCad → Python: Empty sheet
  - Validates: Empty sheet handling

- **39: Disconnected component**
  - Python → KiCad: Component with no nets
  - KiCad → Python: Unconnected component
  - Validates: Isolated component handling

- **40: Component with missing footprint**
  - Python → KiCad: Component without footprint assigned
  - KiCad → Python: Symbol with no footprint
  - Validates: Missing data handling

- **41: Component with custom properties**
  - Python → KiCad: DNP, manufacturer part number, etc.
  - KiCad → Python: Custom properties in KiCad
  - Validates: Custom property preservation

- **42: Bus connections**
  - Python → KiCad: 8-bit data bus
  - KiCad → Python: Bus notation in KiCad
  - Validates: Bus handling, array notation

- **43: Differential pairs**
  - Python → KiCad: USB D+/D- differential pair
  - KiCad → Python: Paired nets with naming
  - Validates: Differential pair recognition

## Test Implementation Priority

### Phase 1 (Immediate - Nets are critical)
- 09: Add net
- 10: Remove net
- 11: Rename net
- 12: Change pin connection

### Phase 2 (Power handling)
- 15: Add power symbol
- 16: Add ground symbol
- 17: Multiple power domains

### Phase 3 (Component changes)
- 18: Swap component type
- 19: Component orientation
- 13: Merge nets
- 14: Split net

### Phase 4 (Hierarchical designs)
- 21: Add subcircuit sheet
- 22: Remove subcircuit sheet
- 23: Component changes subcircuits
- 26: Add global label

### Phase 5 (Advanced features)
- 20: Multi-unit components
- 29: Add junction
- 30: Remove junction
- 33: Add no-connect flag

### Phase 6 (Edge cases and polish)
- Remaining tests as needed based on bug reports

## Test Template

Each test should follow this structure:

```python
def test_XX_feature_name(request):
    """Test feature in direction → syncs correctly.

    Workflow:
    1. Initial state
    2. Make change
    3. Sync
    4. Validate change propagated
    5. (Optional) Round-trip to verify bidirectional

    Level 2 Semantic Validation:
    - kicad-sch-api for KiCad validation
    - AST parsing for Python validation
    """
    # Setup, execute, validate, cleanup
```

## Notes

- Each test should be independently runnable
- Use `--keep-output` flag for debugging
- Prefer semantic validation (AST, kicad-sch-api) over text matching
- All tests should restore original state in finally block
- Document known limitations (e.g., reference change issue #369)
