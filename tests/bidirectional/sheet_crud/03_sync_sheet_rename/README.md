# Test 28: Rename Sheet

## Test Operation
Rename "amplifier" hierarchical sheet to "signal_stage".

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
   - amplifier.kicad_sch exists with R3

4. Modify circuit (rename sheet):
   Edit `comprehensive_root.py`:
   ```python
   # Change:
   @circuit(name="amplifier")
   # To:
   @circuit(name="signal_stage")
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - signal_stage.kicad_sch now exists
   - amplifier.kicad_sch removed (or renamed)
   - R3 content preserved in renamed sheet
   - R1, R2 on root sheet unchanged

## Expected Result
✅ Sheet renamed from amplifier to signal_stage
✅ All component positions preserved
✅ Hierarchical structure maintained

## Automated Test
```bash
pytest test_rename_sheet.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
