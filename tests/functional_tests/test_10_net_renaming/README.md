# Test Case 10: Net Renaming and Merging

## Objective
Test synchronization of net name changes and net merging operations performed in KiCad.

## Test Scenario
1. Create a circuit with auto-generated net names in Python
2. Generate KiCad project
3. In KiCad:
   - Rename auto-generated nets to meaningful names
   - Add net labels for documentation
   - Merge redundant nets
   - Create global labels for inter-sheet connections
4. Import changes back to Python
5. Verify net naming is preserved and connections updated

## Expected Results
- Renamed nets should appear with new names in Python
- Merged nets should consolidate to single net
- Global labels should be recognized
- All component connections should remain correct

## Key Aspects Tested
- Net name synchronization
- Net merging logic
- Label preservation
- Connection integrity after renaming