# Test 61: Large Circuit Performance

## Objective
Validate performance and scalability of bidirectional synchronization with large circuits containing 100 components.

## Test Scenario

### Initial State
Create a large circuit with 100 resistors (R1-R100) arranged in a 10x10 grid network:
- Each resistor connects adjacent nodes in grid
- Horizontal resistors: R1-R90 (9 per row, 10 rows)
- Vertical resistors: R91-R100 (10 resistors connecting rows)
- All resistors: 1k value
- Grid spacing: 5mm between nodes

### Grid Layout
```
  C1    C2    C3    C4    C5    C6    C7    C8    C9    C10
  o-----o-----o-----o-----o-----o-----o-----o-----o-----o
  |     |     |     |     |     |     |     |     |     |
  o-----o-----o-----o-----o-----o-----o-----o-----o-----o
  |     |     |     |     |     |     |     |     |     |
  o-----o-----o-----o-----o-----o-----o-----o-----o-----o
  ...
  (10 rows total)
```

### Modifications
1. Change R50 (middle of grid) value from 1k to 10k
2. Regenerate and synchronize

## Performance Targets

### Timing Requirements
- Initial generation: < 10 seconds
- Initial synchronization: < 5 seconds
- Regeneration after modification: < 10 seconds
- Resynchronization: < 5 seconds

### Resource Requirements
- Peak memory usage: < 500MB
- Total test execution: < 30 seconds

## Validation Levels

### Level 2: Component Count and Positions
- All 100 components present after synchronization
- All component positions preserved within 0.1mm tolerance
- All component values correct

### Level 3: Netlist Correctness
- All 100 components in netlist
- All connections correct (grid topology)
- Net names preserved

### Performance Validation
- Generation time logged and within target
- Synchronization time logged and within target
- Memory usage monitored
- All timing metrics reported

## Expected Behavior

### Initial Generation
1. Create 100 resistors in Python
2. Connect in 10x10 grid pattern
3. Generate to KiCad
4. **Performance:** < 10 seconds
5. **Result:** Valid .kicad_sch file with 100 components

### Initial Synchronization
1. Read back generated .kicad_sch
2. Parse all 100 components
3. Validate positions and connections
4. **Performance:** < 5 seconds
5. **Result:** All components match Python circuit

### Modification
1. Change R50 value in Python (1k → 10k)
2. Regenerate to KiCad
3. **Performance:** < 10 seconds
4. **Result:** R50 value updated, others unchanged

### Resynchronization
1. Read back modified .kicad_sch
2. Validate R50 value changed
3. Validate other 99 components unchanged
4. **Performance:** < 5 seconds
5. **Result:** R50=10k, others=1k

## Test Files

1. `resistor_network.py` - Creates 10x10 resistor grid
2. `test_61_large_circuit.py` - Performance and validation test

## Success Criteria

- All 100 components generated correctly
- All positions preserved within tolerance
- Grid connectivity preserved (all nets correct)
- R50 value modification synchronized
- All performance targets met
- Test completes in < 30 seconds total

## Notes

- Uses `time.perf_counter()` for accurate timing
- May be marked with `pytest.mark.slow` if exceeds 30s
- Validates scalability for production use
- Tests realistic circuit size (100 components is typical small board)
- Grid pattern ensures complex connectivity (not isolated components)
