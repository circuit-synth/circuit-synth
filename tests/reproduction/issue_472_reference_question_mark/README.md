# Issue #472 Reproduction Test Suite

## Bug Description

Component reference designators become "R?" instead of "R1" after bidirectional synchronization.

## Test Results

### Test 1: Simple Regeneration ✅ PASS (Bug NOT reproduced)
```bash
pytest test_reference_preservation.py::test_reference_preserved_across_regeneration -v
```
**Result**: Reference correctly preserved as R1 → R1

**Hypothesis**: Bug may require specific conditions:
- Manual KiCad editing before regeneration
- Different preserve_user_components setting
- Specific component types or configurations
- External file modification

## Reproduction Attempts

### Scenario A: Basic Regeneration
- [x] Generate once
- [x] Regenerate without changes
- **Result**: R1 preserved ✅

### Scenario B: With Manual KiCad Edit (TODO)
- [ ] Generate once
- [ ] Open in KiCad, move component
- [ ] Save in KiCad
- [ ] Regenerate from Python
- **Expected**: R? bug might appear here

### Scenario C: preserve_user_components=False (TODO)
- [ ] Generate with preserve_user_components=False
- [ ] Regenerate
- **Expected**: Different sync path might trigger bug

### Scenario D: Component Annotation Reset (TODO)
- [ ] Generate circuit
- [ ] Manually unannotate in KiCad (change R1 to R?)
- [ ] Regenerate from Python
- **Expected**: Reference might stay as R?

## Next Steps

Need user input to identify exact reproduction steps:
1. Which test/example was running?
2. What was the workflow? (generate, edit KiCad, regenerate?)
3. Any KiCad manual edits?
4. What settings were used?

## Files

- `simple_resistor.py` - Minimal circuit (R1 with 4.7k)
- `test_reference_preservation.py` - Automated test suite
- This README - Reproduction tracking
