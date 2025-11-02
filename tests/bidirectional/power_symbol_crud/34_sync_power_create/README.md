# Test 34: Add Power Symbol

## Test Operation
Add +3V3 power net/symbol to the circuit.

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
   - VCC and GND power symbols exist

4. Modify circuit (add +3V3 power):
   Edit `comprehensive_root.py`:
   ```python
   # Uncomment:
   v3v3 = Net(name="+3V3")

   # Change C1 connection:
   c1[1] += v3v3  # Instead of vcc
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - +3V3 power symbol added
   - C1 now connected to +3V3
   - R1, R2, C1 positions preserved
   - VCC, GND still exist

## Expected Result
✅ +3V3 power symbol added
✅ All component positions preserved
✅ Existing power symbols maintained

## Automated Test
```bash
pytest test_add_power.py -v
```
