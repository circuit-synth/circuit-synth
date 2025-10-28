# Test Fixtures

This directory contains centralized test data used across circuit-synth tests.

## Organization

```
fixtures/
├── circuits/          # Python circuit definitions
├── kicad_projects/    # KiCad project files (.kicad_sch, .kicad_pcb)
├── components/        # Component libraries
└── README.md          # This file
```

## Current Status

**Phase 1 Complete:** Directory structure created and pytest markers added.

**Pending:** Fixture consolidation (Phase 3) will move fixtures from scattered locations:
- `tests/bidirectional/*` → `fixtures/bidirectional/`
- `tests/test_data/kicad9/` → `fixtures/kicad_projects/`
- Other fixtures → organized by category

## Test Organization

The circuit-synth test suite is organized into three categories:

### Unit Tests (`tests/unit/`)
- **Speed:** Very fast (<100ms per test)
- **Dependencies:** Pure Python, no file I/O
- **Tools:** No external tools (no kicad-cli)
- **Markers:** `@pytest.mark.unit`
- **Purpose:** Test individual functions and classes in isolation

### Integration Tests (`tests/integration/`)
- **Speed:** Moderate (can be slow)
- **Dependencies:** File I/O allowed
- **Tools:** No external tools (no kicad-cli)
- **Markers:** `@pytest.mark.integration`
- **Purpose:** Test component interaction, workflows, and roundtrip preservation

### End-to-End Tests (`tests/e2e/`)
- **Speed:** Can be very slow
- **Dependencies:** File I/O allowed
- **Tools:** External tools allowed (kicad-cli, KiCad plugins)
- **Markers:** `@pytest.mark.e2e`
- **Purpose:** Test complete workflows including external tool integration

## Running Tests by Category

```bash
# Run only unit tests (fast feedback)
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run end-to-end tests
pytest tests/e2e/ -v

# Run all tests
pytest tests/ -v

# Run tests by marker
pytest -m unit tests/
pytest -m integration tests/
pytest -m e2e tests/
```

## Contributing

When adding new tests:

1. **Choose the right directory:**
   - Pure Python logic → `tests/unit/`
   - File I/O workflows → `tests/integration/`
   - External tool integration → `tests/e2e/`

2. **Add the appropriate marker:**
   ```python
   import pytest

   @pytest.mark.unit
   def test_my_function():
       assert True
   ```

3. **If you need test data:**
   - Store it in `tests/fixtures/` with clear documentation
   - Reference it in your test

## Fixture Consolidation Plan

See `TEST_REORGANIZATION_PLAN.md` in the project root for the complete plan to consolidate fixtures.
