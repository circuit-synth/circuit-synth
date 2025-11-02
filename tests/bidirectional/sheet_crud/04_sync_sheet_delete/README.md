# Test 29: Delete Sheet

## Test Operation
Delete the "amplifier" hierarchical sheet.

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
   - amplifier.kicad_sch exists with R3
   - Hierarchical sheet symbol on root

4. Modify circuit (delete amplifier sheet):
   Edit `comprehensive_root.py`:
   ```python
   # Comment out:
   # @circuit(name="amplifier")
   # def amplifier_stage(input_sig, output_sig, vcc, gnd):
   #     ...

   # And comment out call:
   # amplifier_stage(input_sig=sig_in, output_sig=sig_out, vcc=vcc, gnd=gnd)
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - amplifier.kicad_sch removed
   - R1, R2, C1 on root sheet preserved
   - R1, R2, C1 positions unchanged
   - Hierarchical sheet symbol removed from root

## Expected Result
✅ amplifier sheet deleted
✅ Root sheet components (R1, R2, C1) positions preserved
✅ Only root sheet remains

## Automated Test
```bash
pytest test_delete_sheet.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
