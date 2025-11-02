# Test 43: Update Multiple Components

## Test Operation
Update values of R3, R4, R5 simultaneously (1k→10k, 2.2k→22k, 3.3k→33k).

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
   - Root sheet has R1-R5, C1, C2
   - R3=1k, R4=2.2k, R5=3.3k

4. Modify circuit (update values):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   value="1k",  # R3
   value="2.2k",  # R4
   value="3.3k",  # R5
   # To:
   value="10k",  # R3
   value="22k",  # R4
   value="33k",  # R5
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - R3=10k, R4=22k, R5=33k
   - All 7 component positions preserved
   - R1, R2, C1, C2 unchanged

## Expected Result
✅ 3 component values updated successfully
✅ All component positions preserved
✅ Unmodified components unchanged

## Automated Test
```bash
pytest test_bulk_update.py -v
```
