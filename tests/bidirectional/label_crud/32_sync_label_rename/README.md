# Test 32: Rename Label

## Test Operation
Rename SIG_IN net to INPUT (renames the hierarchical label).

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

4. Modify circuit (rename SIG_IN to INPUT):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   sig_in = Net("SIG_IN")
   # To:
   input_net = Net("INPUT")

   # Update all references:
   r1[1] += input_net
   amplifier_stage(input_sig=input_net, ...)
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - INPUT hierarchical label now exists
   - SIG_IN label removed
   - R1, R2, R3, R4 positions preserved
   - All connections maintained

## Expected Result
✅ Hierarchical label renamed from SIG_IN to INPUT
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_rename_label.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
