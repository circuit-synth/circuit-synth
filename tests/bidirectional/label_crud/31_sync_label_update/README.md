# Test 31: Update Label Properties

## Test Operation
Change input_sig hierarchical label connection from SIG_IN to ALT_IN.

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
   - input_sig hierarchical label connects to SIG_IN

4. Modify circuit (change label connection):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   amplifier_stage(input_sig=sig_in, output_sig=sig_out, vcc=vcc, gnd=gnd)
   # To:
   amplifier_stage(input_sig=alt_in, output_sig=sig_out, vcc=vcc, gnd=gnd)
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - input_sig now connects to ALT_IN instead of SIG_IN
   - R1, R2, R3, R4 positions preserved
   - Hierarchical structure maintained

## Expected Result
✅ Hierarchical label connection updated
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_update_label.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
