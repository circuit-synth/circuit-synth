# Test 22: Add Net in Subcircuit

## Test Operation
Add CLK net connecting R3-R4 in the amplifier subcircuit.

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
   - Components properly connected

4. Modify circuit (uncomment CLK net):
   Edit `comprehensive_root.py`:
   ```python
   # Uncomment:
   clk = Net("CLK")
   r4_amp[1] += clk
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - CLK net added
   - R3, R4 positions preserved
   - Root sheet unchanged

## Expected Result
✅ CLK net added to subcircuit
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_add_net.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
