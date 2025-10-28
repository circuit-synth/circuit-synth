# Test 51: Sync After External Edit

**Priority:** Priority 1 (Important - Real-world workflow)

## Test Scenario

This test validates the critical workflow where a circuit is:
1. Generated from Python
2. Modified externally in KiCad GUI (simulated by programmatic .kicad_sch edit)
3. Synchronized back to Python
4. Modified again in Python
5. Regenerated without losing external changes

## Real-World Use Case

**Collaborative Workflow:**
- Engineer A generates circuit from Python
- Engineer B opens in KiCad, adds decoupling caps, adjusts layout
- Engineer A pulls changes, adds more components in Python
- Both sets of changes should coexist

**GUI Enhancement Workflow:**
- Generate basic circuit from Python
- Use KiCad GUI for detailed placement, routing, annotations
- Continue adding components in Python
- GUI enhancements should persist

## Test Steps

### Phase 1: Initial Generation (Python → KiCad)
1. Create circuit in Python with R1 (1k) and R2 (2k)
2. Generate KiCad schematic
3. Validate Level 1: Schematic files exist
4. Validate Level 3: Netlist contains R1, R2

### Phase 2: External Edit (Simulate KiCad GUI)
1. Programmatically modify .kicad_sch file to simulate KiCad edits:
   - Add R3 (3.3k) component with proper UUID, position, properties
   - Change R1 value from 1k to 1.5k
   - Move R2 to new position (x+10, y+10)
2. Validate file changes were applied

### Phase 3: Sync to Python (KiCad → Python)
1. Use synchronizer to import external changes back to Python
2. Validate Level 2: Python circuit now contains:
   - R1 with value 1.5k (updated)
   - R2 at new position (moved)
   - R3 with value 3.3k (new component from external edit)
3. Validate component properties match external edits

### Phase 4: Python Modification (Python → KiCad)
1. Add R4 (4.7k) in Python
2. Regenerate KiCad schematic
3. Validate Level 1: Schematic regenerated
4. Validate Level 2: All components present:
   - R1 (1.5k) - preserved from external edit
   - R2 at new position - preserved from external edit
   - R3 (3.3k) - preserved from external edit
   - R4 (4.7k) - newly added from Python

### Phase 5: Final Validation
1. Validate Level 3: Netlist contains all four resistors
2. Validate component values correct
3. Validate positions preserved from external edits
4. Validate Python circuit object reflects all changes

## Expected Behavior

**Synchronization Should:**
- Import external components (R3) into Python circuit
- Update modified properties (R1 value change)
- Preserve position changes (R2 movement)
- Not lose external changes on regeneration

**Key Validation Points:**
- External edits are detected and imported
- Python circuit object updated correctly
- Subsequent Python changes don't overwrite external edits
- All components coexist in final schematic

## Technical Implementation

**External Edit Simulation:**
```python
# Programmatically modify .kicad_sch file
# Add component with proper KiCad s-expression format
# Update existing component properties
# Change component positions
```

**Synchronization:**
```python
# Use Synchronizer to import changes
syncer = Synchronizer(circuit, kicad_project_path)
syncer.sync_from_kicad()  # Import external changes to Python
```

## Validation Levels

- **Level 1:** File existence (schematic files present)
- **Level 2:** Bidirectional sync (external edits imported to Python)
- **Level 3:** Netlist correctness (all components in netlist)

## Success Criteria

1. External component (R3) appears in Python circuit after sync
2. Modified property (R1 value) updated in Python circuit
3. Position change (R2) captured in Python circuit
4. Python-added component (R4) coexists with external edits
5. Final netlist contains all four components with correct values
6. No data loss during sync cycles

## Failure Scenarios to Detect

- External edits not imported (R3 missing)
- Property changes ignored (R1 still shows 1k)
- Position changes lost (R2 at original position)
- Regeneration overwrites external edits
- Sync conflicts causing data loss

## Related Test Cases

- **Test 12:** Basic regeneration (foundation)
- **Test 14:** Modify and regenerate (Python-only changes)
- **Test 27:** Round-trip conversion (data integrity)
- **Test 51:** External edit sync (this test - collaborative workflow)
