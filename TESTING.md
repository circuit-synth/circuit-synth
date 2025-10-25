# Circuit-Synth Testing Documentation

This document tracks all testing performed on circuit-synth, both automated and manual.

## Test Categories

- **Unit Tests**: Automated tests in `tests/unit/`
- **Integration Tests**: Automated tests in `tests/bidirectional/`
- **Manual Tests**: Human-verified functionality tests
- **Regression Tests**: Tests ensuring previously fixed bugs stay fixed

---

## Manual Testing Log

### Bidirectional Sync - Component Addition (2025-10-25)

**Branch**: `test/bidirectional-component-sync`
**Status**: ✅ PASSED
**Tester**: Manual verification

**Test Scenario**:
1. Create blank Python circuit with `pass` statement
2. Generate KiCad project
3. Manually add component in KiCad schematic
4. Run `kicad-to-python` to sync back to Python
5. Verify component appears correctly in Python code

**Steps**:
```bash
# 1. Create blank circuit
cat > bidirectional_test/main.py <<EOF
@circuit(name="BidirectionalTest")
def main():
    """Bidirectional sync test circuit"""
    pass
EOF

# 2. Generate KiCad project
uv run python bidirectional_test/main.py

# 3. Open KiCad, add R1 (Device:R, 10k, R_0603_1608Metric)

# 4. Sync back to Python
uv run kicad-to-python bidirectional_test/BidirectionalTest/ bidirectional_test/main.py
```

**Expected Result**:
- `pass` statement removed
- R1 component added with correct parameters
- Proper indentation maintained
- No duplicate code

**Actual Result**:
```python
@circuit(name="BidirectionalTest")
def main():
    """Bidirectional sync test circuit"""

    # Create components
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
```

**Issues Found**: None

**Commits**:
- `c7ee464` - Fix: Remove 'pass' statements when syncing components from KiCad
- `4f9700b` - Test: Verify bidirectional sync with R1 component

---

## Automated Test Results

### Unit Tests - Comment Preservation

**File**: `tests/unit/test_comment_extractor.py`
**Tests**: 17
**Status**: ✅ ALL PASSING
**Last Run**: 2025-10-25

**Coverage**:
- Function docstring preservation
- Inline docstring preservation
- Blank line preservation between comment groups
- Trailing blank line control (max 2)
- Content outside function preservation
- Module-level content preservation
- Custom function name detection
- Pass statement filtering

### Integration Tests - Phase 6 Preservation

**File**: `tests/bidirectional/test_phase6_preservation.py`
**Tests**: 5
**Status**: ✅ 4/5 PASSING (1 unrelated failure)
**Last Run**: 2025-10-25

**Passing Tests**:
1. `test_6_1_python_comments_preserved` - Python comments survive round-trip
2. `test_6_2_kicad_positions_preserved` - KiCad component positions preserved
3. `test_6_3_component_updates_idempotent` - Component updates are idempotent
4. `test_6_5_user_comments_idempotency` - User comments idempotent across multiple imports

**Known Failure**:
- `test_6_4_wire_routing_idempotency` - Wire routing preservation (unrelated to current work)

---

## Test Coverage Summary

| Feature Area | Unit Tests | Integration Tests | Manual Tests | Status |
|--------------|------------|-------------------|--------------|--------|
| Comment Preservation | 17 | 4 | - | ✅ Complete |
| Custom Function Names | 1 | - | - | ✅ Complete |
| Pass Statement Filtering | - | - | 1 | ✅ Complete |
| Bidirectional Sync | - | 4 | 1 | ✅ Complete |
| Component Addition | - | - | 1 | ✅ Complete |
| Wire Routing | - | 1 | - | ⚠️ Known Issue |

---

## Test Execution Guide

### Running Automated Tests

```bash
# All unit tests
uv run pytest tests/unit/ -v

# All integration tests
uv run pytest tests/bidirectional/ -v

# Specific test file
uv run pytest tests/unit/test_comment_extractor.py -v

# With coverage
uv run pytest tests/unit/test_comment_extractor.py --cov=circuit_synth.tools.utilities.comment_extractor
```

### Running Manual Tests

See specific test scenarios above for step-by-step instructions.

---

## Test Templates

### Manual Test Template

```markdown
### [Test Name] ([Date])

**Branch**: [branch-name]
**Status**: ⏳ IN PROGRESS | ✅ PASSED | ❌ FAILED
**Tester**: [Name/Manual]

**Test Scenario**:
[Description]

**Steps**:
[Numbered steps]

**Expected Result**:
[What should happen]

**Actual Result**:
[What actually happened]

**Issues Found**:
[List of issues or "None"]

**Commits**:
[Related commits]
```

---

## Testing Standards

1. **All code must have unit tests** - Target >80% coverage
2. **Integration tests for workflows** - Round-trip scenarios
3. **Manual tests for UI/UX** - KiCad integration, file generation
4. **Document all manual tests** - Add to this file immediately after testing
5. **Regression tests for bugs** - Every bug fix gets a test

---

## Test Maintenance

- **Update this file** after every testing session
- **Archive old test results** quarterly (move to `docs/testing/archive/`)
- **Review test coverage** monthly
- **Update test scenarios** when features change

---

*Last Updated: 2025-10-25*
