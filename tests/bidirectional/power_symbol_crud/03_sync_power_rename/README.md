# Test 36: Rename Power Net

## Test Operation
Rename VCC power net to VBAT.

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
   - Power symbols: VCC, GND
   - R1[1], R2[1], C1[1] connected to VCC

4. Modify circuit (rename VCC to VBAT):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   vcc = Net(name="VCC")
   # To:
   vbat = Net(name="VBAT")

   # Update all references:
   r1[1] += vbat
   r2[1] += vbat
   c1[1] += vbat
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - VBAT power symbol now exists
   - VCC power symbol removed
   - R1[1], R2[1], C1[1] connected to VBAT
   - R1, R2, C1 positions preserved
   - GND still exists

## Expected Result
✅ Power net renamed from VCC to VBAT
✅ All component positions preserved
✅ All connections maintained on renamed net

## Automated Test
```bash
pytest test_rename_power.py -v
```
