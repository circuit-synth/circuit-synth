# Test 23: Update Net in Subcircuit

## Test Operation
Change R4[1] connection from CLK to output_sig in the amplifier subcircuit.

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
   - R4[1] connected to CLK net

4. Modify circuit (change R4[1] connection):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   r4_amp[1] += clk
   # To:
   r4_amp[1] += output_sig
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - R4[1] now connected to output_sig
   - R3, R4 positions preserved
   - Root sheet unchanged

## Expected Result
✅ R4[1] connection updated from CLK to output_sig
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_update_net_hier.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
