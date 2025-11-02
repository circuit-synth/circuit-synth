# Test 01: Basic Round-Trip Conversion

## Purpose
Validates that a simple circuit survives Python → KiCad → Python conversion without data loss.

## What is Tested
- Component references preserved
- Component values preserved
- Component footprints preserved
- Net connections preserved
- Power symbols preserved

## Expected Result
✅ All data matches after round-trip conversion

```bash
pytest test_roundtrip_basic.py -v
```
