# Test 08: Idempotency

## Purpose

🔴 **CRITICAL TEST** - Validates deterministic, stable behavior across multiple generations.

## Why This is Critical

**Version Control**: Non-deterministic output makes git diffs meaningless. Every generation would show changes even if nothing actually changed.

**CI/CD**: Automated testing requires deterministic output. Random UUIDs or timestamps break testing.

**User Confidence**: If output changes randomly, users can't trust the tool.

## Test Cases

### Test 8.1: Triple Generation (Same Python → Same KiCad 3x)
```python
# Input: resistor_divider.py

# Generate 1:
$ python resistor_divider.py
# Output: resistor_divider_gen1/

# Generate 2:
$ python resistor_divider.py
# Output: resistor_divider_gen2/

# Generate 3:
$ python resistor_divider.py
# Output: resistor_divider_gen3/

# Expected: gen1 == gen2 == gen3 (byte-for-byte identical, except timestamps)
```

**Validates**:
- No random UUIDs
- No random placement
- No random ordering
- Deterministic output

### Test 8.2: Round-Trip Idempotency (P→K→P→K == P→K)
```python
Cycle 1: Python → KiCad → Python → KiCad
Cycle 2: Python → KiCad

Expected: Cycle 1 final = Cycle 2 final
```

**Validates**:
- No data accumulation
- Round-trip doesn't introduce changes

### Test 8.3: No Whitespace Accumulation
```python
# Run 10 round-trips
# Expected: File size stable, no growing blank lines
```

**Validates**:
- No blank line accumulation
- No comment duplication
- No indent drift

### Test 8.4: No Comment Duplication
```python
# Input Python with comment:
r1 = Device_R()(value="10k")  # Main resistor

# After 5 round-trips:
r1 = Device_R()(value="10k")  # Main resistor  ← Single comment (not 5x)
```

**Validates**:
- Comments not duplicated
- Content preservation doesn't accumulate

### Test 8.5: Stable Component Ordering
```python
# Input: R1, R2, R3, R4, R5
# Generate 10 times
# Expected: Always R1, R2, R3, R4, R5 (same order)
```

**Validates**:
- Deterministic component ordering
- No random shuffling

### Test 8.6: Stable Net Ordering
```python
# Input: VCC, GND, SIG1, SIG2
# Generate 10 times
# Expected: Always same net order in netlist
```

**Validates**:
- Deterministic net ordering

## Allowed Differences

**Timestamps**: KiCad files have timestamps - these will differ
**UUIDs**: If UUIDs are required by KiCad format, should use deterministic generation

## Not Allowed

**Random Data**:
- Random UUIDs each run
- Random component placement
- Random net ordering
- Random file structure

**Accumulation**:
- Growing file sizes
- Duplicate comments
- Extra blank lines

## Testing Strategy

**Byte-for-Byte Comparison**:
```python
import filecmp
assert filecmp.cmp("gen1/circuit.kicad_sch", "gen2/circuit.kicad_sch")
```

**Semantic Comparison** (if byte-for-byte too strict):
```python
# Compare netlists (ignore UUIDs, timestamps)
# Compare component lists
# Compare net lists
```

## Success Criteria

- ✅ Triple generation produces identical output
- ✅ Round-trip doesn't introduce changes
- ✅ No data accumulation over cycles
- ✅ Deterministic ordering
- ✅ Git diffs show only real changes

---

**Status**: 🚧 Setup required
**Priority**: P0 🔴 CRITICAL
**Time**: 20 min
