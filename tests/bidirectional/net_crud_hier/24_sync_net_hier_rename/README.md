# Test 24: Rename Net in Subcircuit

## Test Operation
Rename CLK net to ENABLE in the amplifier subcircuit.

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
   - CLK net connects R4[1] to GND via R4[2]

4. Modify circuit (rename CLK to ENABLE):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   clk = Net("CLK")
   r4_amp[1] += clk
   # To:
   enable = Net("ENABLE")
   r4_amp[1] += enable
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - ENABLE net now exists
   - CLK net removed
   - R3, R4 positions preserved
   - Root sheet unchanged

## Expected Result
✅ CLK net renamed to ENABLE
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_rename_net_hier.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
