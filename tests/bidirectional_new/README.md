# Bidirectional Sync Tests

Comprehensive test suite for validating bidirectional synchronization between Python circuit definitions and KiCad schematics.

## Overview

This test suite validates the complete workflow:
- **Python → KiCad**: Generate KiCad schematics from Python code
- **KiCad → Python**: Import KiCad schematics to Python code
- **Round-Trip**: Maintain consistency through multiple sync cycles
- **Preservation**: User edits survive sync operations (CRITICAL)
- **Idempotency**: Deterministic, stable behavior (CRITICAL)

## Status

**✅ Core Tests Passing: 11/11 (100%)**

Tests 01-04 have been fully validated and integrated with robust round-trip validation. Tests 05-08 exist but require additional validation.

## Test Organization

Tests are organized by complexity and functionality:

| # | Directory | Focus | Tests | Status |
|---|-----------|-------|-------|--------|
| 01 | `01_blank_projects/` | Empty circuits (foundation) | 3 | ✅ Passing |
| 02 | `02_single_component/` | Single component operations | 3 | ✅ Passing |
| 03 | `03_position_preservation/` | Component positions survive sync | 3 | ✅ Passing |
| 04 | `04_multiple_components/` | Multiple components + connections | 2 | ✅ Passing |
| 05 | `05_nets_connectivity/` | Named nets, complex topologies | 8 | 🚧 Needs validation |
| 06 | `06_round_trip/` | Full cycle validation | 5 | 🚧 Needs validation |
| 07 | `07_user_content_preservation/` | Comments, annotations | 7 | 🚧 Needs validation |
| 08 | `08_idempotency/` | Deterministic behavior | 6 | 🚧 Needs validation |

**Total**: 37 tests (11 validated, 26 need validation)

## Running Tests

```bash
# Run validated tests (01-04)
uv run pytest 01_blank_projects/ 02_single_component/ 03_position_preservation/ 04_multiple_components/ -v

# Run all tests
uv run pytest . -v
```

## Robust Validation Infrastructure

### Round-Trip Validator (`round_trip_validator.py`)

Production-ready validation module with three-phase validation:

1. **CircuitJSONComparator** - Validates electrical correctness
   - Order-independent component/net comparison
   - Floating-point tolerance for positions (0.01mm)
   - Metadata filtering (UUIDs, timestamps)

2. **CommentPreservationValidator** - Validates documentation preservation (CRITICAL)
   - Tokenize-based comment extraction
   - Order-independent comparison
   - Detects context loss

3. **PythonASTComparator** - Code quality validation (optional)
   - Function and import verification
   - Structure validation

### Documentation

- **`ROUND_TRIP_VALIDATION_STRATEGY.md`** - Complete validation strategy with production-ready functions
- **`COMMENT_PRESERVATION_ANALYSIS.md`** - Deep technical analysis of comment preservation with solution roadmap

## Known Issues

**Comment Preservation**: Currently comments are not preserved through KiCad→Python import. This is a known issue documented in `COMMENT_PRESERVATION_ANALYSIS.md` with:
- Root cause analysis
- 8 critical weaknesses identified
- Recommended solution (JSON metadata + structured annotations)
- 3-4 week implementation timeline

The robust validator correctly detects this issue, as demonstrated in test 01.

## Test Details

Each test directory contains:
- `README.md` - Detailed test documentation
- `XX_test.py` - Test implementation
- `XX_python_ref.py` - Reference Python circuit
- `XX_kicad_ref/` - Reference KiCad project (where applicable)

See individual test READMEs for detailed information about what each test validates.
