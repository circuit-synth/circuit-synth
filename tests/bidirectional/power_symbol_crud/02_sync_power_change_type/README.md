# Test 35: Change Power Symbol Type

## Test Operation
Change +3V3 power symbol to +5V.

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

4. Modify circuit (change +3V3 to +5V):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   v3v3 = Net(name="+3V3")
   # To:
   v5v = Net(name="+5V")

   # Update variable reference:
   c1[1] += v5v
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - +5V power symbol now exists
   - +3V3 power symbol removed
   - C1[1] connected to +5V
   - R1, R2, C1 positions preserved
   - VCC, GND still exist

## Expected Result
✅ Power symbol changed from +3V3 to +5V
✅ All component positions preserved
✅ Other power symbols maintained

## Automated Test
```bash
pytest test_change_power_type.py -v
```
