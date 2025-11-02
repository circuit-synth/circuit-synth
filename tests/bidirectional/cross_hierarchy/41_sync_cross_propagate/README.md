# Test 41: Propagate Changes Up/Down Hierarchy

## Test Operation
Rename VCC to VBAT on root - change should propagate to amplifier subcircuit.

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
   - VCC power net on both root and amplifier

4. Modify circuit (rename VCC to VBAT):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   vcc = Net(name="VCC")
   # To:
   vbat = Net(name="VBAT")

   # Update all references:
   r1[2] += vbat
   amplifier_stage(..., vcc=vbat, ...)
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - VBAT power symbol on root sheet
   - VBAT hierarchical label propagates to amplifier
   - R1[2] connected to VBAT on root
   - R3[2] connected to vcc parameter (now VBAT) in amplifier
   - All component positions preserved

## Expected Result
✅ VCC→VBAT rename propagates through hierarchy
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_cross_propagate.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
