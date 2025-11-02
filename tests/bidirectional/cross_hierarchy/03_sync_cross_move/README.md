# Test 40: Move Component Between Sheets

## Test Operation
Move C1 from root sheet to amplifier subcircuit.

## Manual Test Steps

1. Generate initial circuit:
   ```bash
   uv run comprehensive_root.py
   ```

2. Open in KiCad:
   ```bash
   open comprehensive_root/comprehensive_root.kicad_pro
   ```

3. Verify structure:
   - Root sheet has R1, R2, C1
   - Amplifier sheet has R3, R4 (no C1)

4. Modify circuit (move C1 to amplifier):
   Edit `comprehensive_root.py`:
   ```python
   # In amplifier_stage function, uncomment:
   c1 = Component(...)
   c1[1] += vcc
   c1[2] += gnd

   # In comprehensive_root function, comment out:
   # c1 = Component(...)
   # c1[1] += vcc
   # c1[2] += gnd
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - C1 now in amplifier sheet
   - C1 removed from root sheet
   - R1, R2, R3, R4 positions preserved

## Expected Result
✅ C1 moved from root to amplifier
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_cross_move.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
