# Test 27: Update Sheet Properties

## Test Operation
Update R3 value from 1k to 2.2k in the amplifier hierarchical sheet.

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
   - Root sheet has R1 (10k), R2 (4.7k)
   - Amplifier sheet has R3 (1k)

4. Modify circuit (update R3 value):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   value="1k",
   # To:
   value="2.2k",
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - R3 value updated to 2.2k
   - R3 position preserved
   - R1, R2 on root sheet unchanged

## Expected Result
✅ R3 value updated in amplifier sheet
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_update_sheet.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
