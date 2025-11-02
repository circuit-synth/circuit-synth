# Test 47: Duplicate Component References

## Test Operation
Attempt to create two components with same reference (R1).

## Expected Result
Either:
- ✅ Auto-rename second R1 to R2
- ✅ Error message preventing duplicate

## Automated Test
```bash
pytest test_duplicate_refs.py -v
```
