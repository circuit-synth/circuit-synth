# Test 33: Delete Label

## Test Operation
Remove input_sig parameter from amplifier (deletes SIG_IN hierarchical label).

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
   - Root sheet has R1, R2
   - Amplifier sheet has R3, R4
   - SIG_IN hierarchical label exists

4. Modify circuit (remove input_sig parameter):
   Edit `comprehensive_root.py`:
   ```python
   # Change function signature:
   def amplifier_stage(output_sig, vcc, gnd):  # Removed input_sig

   # Remove connection:
   # r3_amp[1] += input_sig  # Comment out

   # Change function call:
   amplifier_stage(output_sig=sig_out, vcc=vcc, gnd=gnd)  # Removed input_sig
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - SIG_IN hierarchical label removed
   - SIG_OUT, VCC, GND labels still exist
   - R1, R2, R3, R4 positions preserved

## Expected Result
✅ SIG_IN hierarchical label deleted
✅ All other labels preserved
✅ All component positions preserved

## Automated Test
```bash
pytest test_delete_label.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
