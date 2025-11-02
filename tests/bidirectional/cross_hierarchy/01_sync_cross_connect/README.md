# Test 38: Connect Across Sheets

## Test Operation
Connect amplifier output (sig_out) to power_supply input (control_sig) across hierarchical sheets.

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
   - Root sheet has R1, R2 and two hierarchical sheet symbols
   - Amplifier sheet has R3, R4
   - Power supply sheet has R5, C2
   - SIG_OUT net appears on both root and in both subcircuits

4. Verify cross-sheet connection:
   - sig_out hierarchical label on amplifier sheet
   - control_sig hierarchical label on power_supply sheet
   - Both connect to SIG_OUT on root sheet

## Expected Result
✅ Cross-sheet connection established (amplifier → power_supply)
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_cross_connect.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
