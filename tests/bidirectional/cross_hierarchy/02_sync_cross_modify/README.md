# Test 39: Modify Cross-Sheet Connection

## Test Operation
Change power_supply control_sig connection from sig_out to sig_in.

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
   - Root sheet has two hierarchical sheets
   - power_supply connected to SIG_OUT

4. Modify circuit (change connection):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   power_supply(control_sig=sig_out, vcc=vcc, gnd=gnd)
   # To:
   power_supply(control_sig=sig_in, vcc=vcc, gnd=gnd)
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - power_supply now connected to SIG_IN instead of SIG_OUT
   - All component positions preserved
   - Hierarchical structure maintained

## Expected Result
✅ Cross-sheet connection modified (sig_out → sig_in)
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_cross_modify.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
