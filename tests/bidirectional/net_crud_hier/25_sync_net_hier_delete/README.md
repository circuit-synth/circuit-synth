# Test 25: Delete Net in Subcircuit

## Test Operation
Delete CLK net from the amplifier subcircuit.

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
   - CLK net connects R4[1]

4. Modify circuit (delete CLK net):
   Edit `comprehensive_root.py`:
   ```python
   # Comment out:
   # clk = Net("CLK")
   # r4_amp[1] += clk
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - CLK net removed
   - R3, R4 still present
   - R3, R4 positions preserved
   - Root sheet unchanged

## Expected Result
✅ CLK net deleted from subcircuit
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_delete_net_hier.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
