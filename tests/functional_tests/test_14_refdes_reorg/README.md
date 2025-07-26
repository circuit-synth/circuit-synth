# Test Case 14: Reference Designator Reorganization

## Objective
Test the ability to renumber and reorganize reference designators in KiCad and sync back to Python.

## Test Scenario
1. Create a circuit with randomly ordered reference designators in Python
2. Generate KiCad project
3. In KiCad:
   - Renumber components geographically (left to right, top to bottom)
   - Handle multi-unit components correctly
   - Ensure sequential numbering within component types
   - Update any component groups
4. Import changes back to Python
5. Verify all reference designators are updated correctly

## Expected Results
- New reference designators appear in Python code
- All connections remain intact with new references
- Multi-unit components maintain unit associations
- Component values and properties are preserved

## Key Aspects Tested
- Reference designator synchronization
- Geographic renumbering
- Multi-unit component handling
- Connection integrity with new references