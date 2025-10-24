# Implementation Plan: Comprehensive cs-new-project Testing

**Created:** 2025-10-23
**Branch:** `test/cs-new-project-unit-tests`
**Status:** Planning → Implementation

---

## Executive Summary

Currently, we have **23 unit tests** that validate `cs-new-project` file generation in isolation. However, we're missing comprehensive testing of **CLI invocation paths** - the actual user workflows.

This plan adds **30+ integration tests** that exercise all possible invocations with different circuit selections and flag combinations.

---

## Current State

### What Exists ✅
- **23 unit tests** (passing)
  - File generation (README.md, CLAUDE.md)
  - Claude agent directory structure
  - Template management
  - KiCad installation checking
  - Edge cases and error handling
  - Regression test for workspace bug

### What's Missing ❌
- Integration tests for **all 8 circuit templates**
- Tests for **all CLI flag combinations** (10+ combinations)
- Tests for **multi-circuit selection** (5 different combinations)
- Validation that **generated projects actually run**
- Tests for **edge cases in interactive mode**

---

## Available Circuits to Test

| # | Circuit | Difficulty | Test Path |
|---|---------|-----------|-----------|
| 1 | Resistor Divider | Beginner | ✓ (default/quick) |
| 2 | LED Blinker | Beginner | ✗ (need test) |
| 3 | Voltage Regulator | Intermediate | ✗ (need test) |
| 4 | USB-C Basic | Intermediate | ✗ (need test) |
| 5 | Power Supply Module | Intermediate | ✗ (need test) |
| 6 | ESP32-C6 Dev Board | Advanced | ✗ (need test) |
| 7 | STM32 Minimal | Advanced | ✗ (need test) |
| 8 | Minimal/Empty | Expert | ✗ (need test) |

---

## CLI Invocation Paths to Test

### A. Default Modes (3 tests)
```bash
# 1. Interactive mode (default behavior)
cs-new-project                                  → main.py + README + CLAUDE.md + agents

# 2. Quick start (no prompts, uses default)
cs-new-project --quick --skip-kicad-check       → same as above but instant

# 3. Skip KiCad (for CI environments)
cs-new-project --quick --skip-kicad-check       → (already covered above)
```

### B. Circuit Selection via Flags (8+ tests)
```bash
# Single circuits
cs-new-project --circuits resistor --skip-kicad-check      → main.py (resistor)
cs-new-project --circuits led --skip-kicad-check           → main.py (led)
cs-new-project --circuits esp32 --skip-kicad-check         → main.py (esp32)
...all 8 circuits

# Multiple circuits
cs-new-project --circuits resistor,led --skip-kicad-check  → main.py + led_blinker.py
cs-new-project --circuits resistor,led,esp32 --skip-kicad-check  → main.py + 2 others
cs-new-project --circuits resistor,led,voltage,usb,power,esp32,stm32,minimal  → all 8 files
```

### C. Agent Setup Modes (3 tests)
```bash
# Default (include agents)
cs-new-project --quick --skip-kicad-check                   → includes .claude/agents/

# No agents
cs-new-project --quick --no-agents --skip-kicad-check       → NO .claude/ directory

# Developer mode
cs-new-project --quick --developer --skip-kicad-check       → includes dev/ agents + commands
```

### D. Flag Combinations (6+ tests)
```bash
cs-new-project --circuits resistor,led --developer --skip-kicad-check
cs-new-project --circuits resistor,led --no-agents --skip-kicad-check
cs-new-project --circuits minimal --developer --skip-kicad-check
...etc
```

### E. Edge Cases (5+ tests)
```bash
# Invalid circuit names
cs-new-project --circuits invalid,resistor --skip-kicad-check  → should skip "invalid"

# Empty selection
cs-new-project --circuits "" --skip-kicad-check              → fallback to default

# Duplicate circuits
cs-new-project --circuits resistor,resistor,led              → handle gracefully
```

---

## Test Structure

### New Test File Location
```
tests/unit/tools/project_management/
├── test_new_project.py          # Existing (23 tests) ✓
└── test_new_project_cli.py       # NEW: CLI invocation tests (30+ tests)
```

### Test Categories in New File

#### 1. **Parametrized Circuit Tests** (8 tests)
```python
@pytest.mark.parametrize("circuit", [
    Circuit.RESISTOR_DIVIDER,
    Circuit.LED_BLINKER,
    Circuit.VOLTAGE_REGULATOR,
    # ... all 8
])
def test_circuit_template_generation(circuit, temp_project_dir):
    """Test each circuit generates correct file"""
    config = ProjectConfig(circuits=[circuit], include_agents=False)
    # ... assertions
```

**Validates:**
- ✓ Correct filename (main.py for first, {name}.py for others)
- ✓ File contains circuit code
- ✓ Python syntax is valid
- ✓ File is not empty

#### 2. **Multi-Circuit Tests** (5 tests)
```python
def test_multiple_circuits_generates_multiple_files():
    """Test resistor + led generates 2 files"""

def test_all_circuits_together():
    """Test all 8 circuits generates 8 files"""

def test_three_circuit_combination():
    """Test resistor + led + esp32 combination"""
```

**Validates:**
- ✓ Exactly N files created
- ✓ Each has correct content
- ✓ README lists all N circuits
- ✓ First becomes main.py, rest use names

#### 3. **Flag Combination Tests** (6+ tests)
```python
def test_no_agents_flag():
    """--no-agents skips .claude/ creation"""

def test_developer_flag():
    """--developer includes dev agents"""

def test_quick_flag_is_fast():
    """--quick completes instantly without prompts"""

def test_circuit_and_agent_combinations():
    """Various --circuits + agent flag combos"""
```

**Validates:**
- ✓ Flag logic works correctly
- ✓ Combinations don't conflict
- ✓ Agent setup respects flags
- ✓ Developer tools included only when requested

#### 4. **Edge Case Tests** (5+ tests)
```python
def test_invalid_circuit_names_skipped():
    """Invalid names are skipped with warning"""

def test_empty_circuit_selection_fallback():
    """Empty selection uses default"""

def test_duplicate_circuits_handled():
    """Duplicates are handled gracefully"""

def test_special_characters_in_paths():
    """Projects with special chars work"""
```

**Validates:**
- ✓ Error handling is robust
- ✓ Graceful fallbacks work
- ✓ User is informed of issues
- ✓ Project still works despite errors

#### 5. **File Content Validation Tests** (5+ tests)
```python
def test_readme_lists_all_circuits():
    """README mentions all included circuits"""

def test_circuit_files_have_valid_syntax():
    """All generated .py files are valid Python"""

def test_no_workspace_configuration():
    """Regression: no 'workspace = true' in generated files"""

def test_main_py_is_executable():
    """main.py can be imported and executed"""
```

**Validates:**
- ✓ Generated files are syntactically correct
- ✓ README is accurate
- ✓ No regressions from previous bugs
- ✓ Project matches user expectations

---

## Implementation Steps

### Step 1: Create CLI Integration Test File ✓
```bash
tests/unit/tools/project_management/test_new_project_cli.py
```

### Step 2: Add Parametrized Circuit Tests
- One test per circuit × 3 scenarios = 24 tests
- Validates: filename, content, Python syntax

### Step 3: Add Multi-Circuit Tests
- Multiple circuit combinations
- Validates: file counts, content, README

### Step 4: Add Flag Combination Tests
- All meaningful flag combinations
- Validates: agent setup, developer mode, skips

### Step 5: Add Edge Case Tests
- Invalid inputs, empty selections, duplicates
- Validates: error handling, fallbacks

### Step 6: Add File Content Validation
- Python syntax checking
- Regression testing
- Project executability

### Step 7: Verify All Tests Pass
```bash
uv run pytest tests/unit/tools/project_management/ -v --tb=short
```

### Step 8: Update PR Description
- Add summary of new tests
- Include test results
- Document test coverage

---

## Expected Test Results

### Before Implementation
```
tests/unit/tools/project_management/test_new_project.py .... 23 passed
```

### After Implementation
```
tests/unit/tools/project_management/test_new_project.py .... 23 passed
tests/unit/tools/project_management/test_new_project_cli.py ... 35 passed
────────────────────────────────────────────────────────────
TOTAL: 58 passed in 0.50s
```

---

## Test Coverage Map

```
┌─────────────────────────────────────┬──────┬───────────┐
│ Feature                             │ Unit │ Integration│
├─────────────────────────────────────┼──────┼───────────┤
│ File generation                     │ ✓    │ ✓         │
│ Circuit selection (all 8)           │      │ ✓         │
│ Multi-circuit projects              │      │ ✓         │
│ CLI flags (--quick, --circuits)     │      │ ✓         │
│ Agent setup modes                   │ ✓    │ ✓         │
│ Developer mode                      │ ✓    │ ✓         │
│ No agents mode                      │ ✓    │ ✓         │
│ Edge cases & errors                 │ ✓    │ ✓         │
│ File content validation             │      │ ✓         │
│ Python syntax validation            │      │ ✓         │
│ Regression tests                    │ ✓    │ ✓         │
│ Project executability               │      │ ✓         │
└─────────────────────────────────────┴──────┴───────────┘
```

---

## Success Criteria

- [ ] All 35 new tests pass
- [ ] Each of 8 circuits tested individually
- [ ] All flag combinations tested
- [ ] Edge cases covered
- [ ] File content validated
- [ ] No regressions
- [ ] Test execution < 1 second
- [ ] Coverage > 85%

---

## Questions to Answer via Tests

1. **Does each circuit template generate the correct file?**
   - Answer: YES (tests validate file content)

2. **Do multi-circuit projects generate all expected files?**
   - Answer: YES (tests validate file counts)

3. **Does README accurately describe the project?**
   - Answer: YES (tests validate README content)

4. **Are all CLI flags working correctly?**
   - Answer: YES (tests exercise all flag combinations)

5. **Are edge cases handled gracefully?**
   - Answer: YES (tests for invalid inputs, empty selections)

6. **Can generated projects actually run?**
   - Answer: YES (syntax validation + import tests)

7. **Are there any regressions from previous bugs?**
   - Answer: NO (regression tests prevent known issues)

---

## Timeline

| Task | Effort | Status |
|------|--------|--------|
| Create test plan (this doc) | 30 min | ✓ Done |
| Create test file structure | 15 min | → Next |
| Implement parametrized circuit tests | 45 min | → Next |
| Implement multi-circuit tests | 30 min | → Next |
| Implement flag combination tests | 45 min | → Next |
| Implement edge case tests | 30 min | → Next |
| Implement content validation tests | 30 min | → Next |
| Run all tests & fix failures | 30 min | → Next |
| Update PR with results | 15 min | → Next |
| **Total** | **3.5 hours** | → In Progress |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Tests too slow | CI delays | Use mocking for file I/O where needed |
| Duplicate test code | Maintenance burden | Use parametrization & fixtures |
| Flaky tests | False failures | Use temp dirs, no external deps |
| Edge case coverage gaps | Regressions slip through | Comprehensive edge case matrix |

---

## Related Issues

- Previous bug #0.8.22: Workspace configuration error → **covered by regression test**
- User expectation: Generated files should match selection → **covered by parametrized tests**
- CI compatibility: Tests should run without KiCad → **uses --skip-kicad-check**

---

## References

- **Current tests:** `tests/unit/tools/project_management/test_new_project.py`
- **End-to-end tests:** `tools/testing/test_project_creation_end_to_end.py`
- **CLI source:** `src/circuit_synth/tools/project_management/new_project.py`
- **Templates:** `src/circuit_synth/data/templates/`
- **Circuit config:** `src/circuit_synth/tools/project_management/project_config.py`
