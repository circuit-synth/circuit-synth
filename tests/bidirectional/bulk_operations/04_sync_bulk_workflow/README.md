# Test 45: Complex Multi-Operation Workflow

## Test Operation
Perform 5 operations in one workflow:
1. Add R5 to root
2. Update R2 value (4.7k → 47k)
3. Delete C1 from root
4. Rename VCC → VBAT (propagates through hierarchy)
5. Add C2 to amplifier subcircuit

## Manual Test Steps

1. Generate initial circuit:
   ```bash
   uv run comprehensive_root.py
   ```

2. Open in KiCad:
   ```bash
   open comprehensive_root/comprehensive_root.kicad_pro
   ```

3. Verify initial state:
   - Root: R1, R2 (4.7k), C1
   - Amplifier: R3, R4
   - Power: VCC, GND

4. Modify circuit (perform all 5 operations):
   Edit `comprehensive_root.py`:
   ```python
   # 1. Add R5 (uncomment)
   r5 = Component(...)
   r5[1] += vcc
   r5[2] += gnd

   # 2. Update R2
   value="47k",  # Was 4.7k

   # 3. Delete C1 (comment out)
   # c1 = Component(...)
   # c1[1] += vcc
   # c1[2] += gnd

   # 4. Rename VCC → VBAT
   vbat = Net(name="VBAT")
   # Update all vcc → vbat

   # 5. Add C2 to amplifier (uncomment in amplifier_stage)
   c2_amp = Component(...)
   c2_amp[1] += vcc
   c2_amp[2] += gnd
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify all changes:
   - Root: R1, R2 (47k), R5 (C1 removed)
   - Amplifier: R3, R4, C2
   - Power: VBAT, GND (VCC renamed)
   - All positions preserved

## Expected Result
✅ All 5 operations applied successfully
✅ All component positions preserved
✅ Hierarchical structure maintained
✅ Net rename propagated correctly

## Automated Test
```bash
pytest test_bulk_workflow.py -v
```

**Note**: This test demonstrates the full power of bidirectional sync with complex, multi-faceted changes across root and hierarchical sheets.
