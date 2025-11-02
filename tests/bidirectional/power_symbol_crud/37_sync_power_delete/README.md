# Test 37: Delete Power Symbol

## Test Operation
Delete +3V3 power net/symbol from the circuit.

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
   - Power symbols: VCC, GND, +3V3
   - C1[1] connected to +3V3

4. Modify circuit (delete +3V3 power):
   Edit `comprehensive_root.py`:
   ```python
   # Comment out:
   # v3v3 = Net(name="+3V3")

   # Remove connection:
   # c1[1] += v3v3
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - +3V3 power symbol removed
   - R1, R2, C1 positions preserved
   - VCC, GND still exist
   - C1[1] no longer connected to +3V3

## Expected Result
✅ +3V3 power symbol deleted
✅ All component positions preserved
✅ Other power symbols maintained

## Automated Test
```bash
pytest test_delete_power.py -v
```
