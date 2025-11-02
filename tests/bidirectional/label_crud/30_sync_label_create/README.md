# Test 30: Add Hierarchical Label

## Test Operation
Add ENABLE signal with hierarchical label connecting root to amplifier subcircuit.

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
   - Existing hierarchical labels: SIG_IN, SIG_OUT, VCC, GND

4. Modify circuit (add ENABLE signal):
   Edit `comprehensive_root.py`:
   ```python
   # Uncomment:
   enable = Net("ENABLE")

   # Change function signature:
   def amplifier_stage(input_sig, output_sig, vcc, gnd, enable):

   # Change function call:
   amplifier_stage(..., enable=enable)
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - ENABLE hierarchical label added on root sheet
   - ENABLE label appears in amplifier sheet
   - R1, R2, R3, R4 positions preserved

## Expected Result
✅ ENABLE hierarchical label added
✅ All component positions preserved
✅ Hierarchical connection established

## Automated Test
```bash
pytest test_add_label.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
