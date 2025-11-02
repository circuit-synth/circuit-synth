# Test 26: Add Hierarchical Sheet

## Test Operation
Add a new "power_supply" hierarchical sheet with R3 and C1 components.

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
   - Root sheet has R1, R2 only
   - No power_supply sheet exists

4. Modify circuit (add power_supply subcircuit):
   Edit `comprehensive_root.py`:
   ```python
   # Uncomment:
   @circuit(name="power_supply")
   def power_supply(vcc, gnd):
       # ... (uncomment entire function)

   # And uncomment call:
   power_supply(vcc=vcc, gnd=gnd)
   ```

5. Regenerate:
   ```bash
   uv run comprehensive_root.py
   ```

6. Verify:
   - New power_supply.kicad_sch file created
   - power_supply sheet contains R3, C1
   - R1, R2 positions on root sheet preserved
   - Hierarchical sheet symbol added to root

## Expected Result
✅ power_supply sheet added
✅ Root sheet components (R1, R2) positions preserved
✅ Hierarchical structure created

## Automated Test
```bash
pytest test_add_sheet.py -v
```

**Note**: Full bidirectional position preservation for hierarchical circuits is pending implementation.
