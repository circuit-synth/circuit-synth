# Bidirectional Sync Tests (v2)

Comprehensive test suite for validating bidirectional synchronization between Python circuit definitions and KiCad schematics.

## Overview

This test suite validates the complete workflow:
- **Python → KiCad**: Generate KiCad schematics from Python code
- **KiCad → Python**: Import KiCad schematics to Python code
- **Round-Trip**: Maintain consistency through multiple sync cycles
- **Preservation**: User edits survive sync operations (CRITICAL)
- **Idempotency**: Deterministic, stable behavior (CRITICAL)

## Test Organization

Tests are organized by complexity and functionality, numbered for clear progression:

| # | Directory | Focus | Priority | Status |
|---|-----------|-------|----------|--------|
| 01 | `01_blank_projects/` | Empty circuits (foundation) | P0 | 🚧 Setup |
| 02 | `02_single_component/` | Add/remove/modify one component | P0 | 🚧 Setup |
| 03 | `03_position_preservation/` | Component positions survive sync | P0 | 🚧 Setup |
| 04 | `04_multiple_components/` | Multiple components + connections | P1 | 🚧 Setup |
| 05 | `05_nets_connectivity/` | Named nets, complex topologies | P1 | 🚧 Setup |
| 06 | `06_round_trip/` | Full cycle validation | P0 | 🚧 Setup |
| 07 | `07_user_content_preservation/` | Comments, annotations preserved | P0 | 🚧 Setup |
| 08 | `08_idempotency/` | Deterministic behavior | P0 | 🚧 Setup |
| 09 | `09_hierarchical_basic/` | 2-3 level hierarchies | P2 | 🚧 Setup |
| 10 | `10_hierarchical_restructuring/` | Moving components between subcircuits | P3 | 🚧 Setup |
| 11 | `11_edge_cases/` | Error handling, invalid data | P1 | 🚧 Setup |
| 12 | `12_performance/` | Speed and scale tests | P3 | 🚧 Setup |

## Priority Levels

- **P0 (Must Work)**: Core functionality - blank projects, single component, preservation, idempotency
- **P1 (Core Features)**: Multiple components, nets, round-trip, edge cases
- **P2 (Advanced)**: Basic hierarchy, complex topologies
- **P3 (Nice to Have)**: Hierarchical restructuring, performance tests

## Critical Test Areas

### 🔴 CRITICAL: Position Preservation (Test 03)
**Why Critical**: Users manually arrange components in KiCad. If positions reset on every Python update, the tool is unusable.

**Tests**:
- Move component in KiCad → rerun Python script → position preserved
- Add component in Python → KiCad auto-places without disturbing existing
- Rearrange 5 components → all positions preserved

### 🔴 CRITICAL: User Content Preservation (Test 07)
**Why Critical**: Users add comments, annotations, and documentation. Losing this destroys trust.

**Tests**:
- Python comments survive KiCad sync
- KiCad text annotations survive Python sync
- Manual wire routing preserved
- Mixed edits (Python comments + KiCad positions) both preserved

### 🔴 CRITICAL: Idempotency (Test 08)
**Why Critical**: Non-deterministic behavior makes diffs impossible and destroys version control workflow.

**Tests**:
- Generate 3x from same Python → identical output
- Round-trip P→K→P→K produces same as P→K
- No data drift over multiple cycles
- No whitespace/comment duplication

## Running Tests

### Run all tests:
```bash
pytest tests/bidirectional_new/ -v
```

### Run specific priority:
```bash
# P0 tests only (critical path)
pytest tests/bidirectional_new/ -v -k "01_blank or 02_single or 03_position or 06_round_trip or 07_user_content or 08_idempotency"
```

### Run specific category:
```bash
pytest tests/bidirectional_new/03_position_preservation/ -v
```

### Run with detailed output:
```bash
pytest tests/bidirectional_new/ -v -s
```

## Test Development Workflow

### 1. Manual Setup Required
Many tests require manually creating reference KiCad projects:
- Open KiCad
- Create schematic with specific components/layout
- Save as reference project in `fixtures/`
- Document in test README

### 2. Test Pattern
Each test follows this structure:
```python
def test_specific_behavior():
    """Test X.Y: Brief description

    Validates:
    - Specific behavior 1
    - Specific behavior 2
    """
    # Arrange - setup test data
    # Act - perform operation
    # Assert - verify behavior
```

### 3. Fixtures Organization
```
fixtures/
├── blank/                  # Empty projects
│   ├── blank.py           # Blank Python circuit
│   └── blank.kicad_pro    # Blank KiCad project
├── single_resistor/       # One component
├── resistor_divider/      # Classic multi-component
├── hierarchical_simple/   # 2-level hierarchy
└── hierarchical_complex/  # 3-level hierarchy
```

## Test Validation Checklist

For each test to be considered "passing":
- ✅ Test runs without errors
- ✅ Assertions validate expected behavior
- ✅ Test is deterministic (same result every run)
- ✅ Test cleans up temp files
- ✅ README documents what's being tested
- ✅ Manual setup steps documented (if needed)

## Known Limitations

### Current Implementation Gaps:
1. **Hierarchical Restructuring**: Moving components between subcircuits not yet implemented
2. **KiCad Annotations**: Text notes on schematics not yet preserved in Python sync
3. **Wire Routing**: Manual wire paths not yet preserved
4. **Component Rotation**: Rotation angles may not be fully preserved

These are documented in respective test READMEs and marked with appropriate skip decorators.

## Adding New Tests

1. **Choose appropriate directory** based on what's being tested
2. **Create test file** following naming convention: `test_<specific_behavior>.py`
3. **Write README entry** explaining test purpose
4. **Add fixtures** if new reference projects needed
5. **Document manual steps** required for setup
6. **Mark WIP** with `pytest.mark.skip` until ready

## Debugging Failed Tests

### Common Issues:

**Test fails: "No connections found"**
- Check KiCad schematic has wires connecting components
- Verify netlist export is working (`kicad-cli` available)
- Check component pins are actually connected

**Test fails: "Component not found"**
- Verify component reference matches (R1 vs r1)
- Check component library is accessible
- Ensure footprint is valid

**Test fails: "Position changed"**
- Check if position tolerance is too strict
- Verify KiCad schematic has position data
- Ensure sync isn't regenerating positions

**Idempotency fails**
- Look for timestamp/UUID changes
- Check for random number generation
- Verify no external state dependency

## Related Documentation

- `/docs/KICAD_SCH_API_INTEGRATION.md` - KiCad integration architecture
- `/docs/ARCHITECTURE.md` - Overall system design
- Original test suite: `/tests/bidirectional/` (deprecated, kept for reference)

## Test Status Legend

- 🚧 Setup - Directory created, tests not yet implemented
- 📝 WIP - Tests written but not passing
- ⚠️ Partial - Some tests passing, some failing
- ✅ Passing - All tests in category passing
- 🔴 Critical - Must pass for release

---

**Last Updated**: 2025-10-25
**Version**: 2.0 (Clean rewrite)
**Status**: Initial setup phase
