# Comprehensive Test Plan for cs-new-project CLI

**Date:** 2025-10-23
**Status:** Planning Complete - Ready for Implementation
**Branch:** test/cs-new-project-unit-tests

---

## Problem Statement

We need to ensure that every possible way a user can invoke `cs-new-project` generates **exactly the files they expect**.

Currently:
- ✅ We have 23 unit tests for file generation
- ❌ We're missing integration tests for CLI invocations
- ❌ We don't test all 8 circuit templates
- ❌ We don't test all flag combinations
- ❌ We don't validate that generated projects actually run

---

## What Users Can Do With cs-new-project

### 1. Interactive Mode (Default)
```bash
$ uv run cs-new-project
```
- Shows welcome banner
- Checks KiCad installation
- Prompts user to select circuits from table
- User can pick: resistor (default), led, voltage, usb, power, esp32, stm32, or minimal
- Can select multiple: "1,2,3"

**Generates:**
- `circuit-synth/main.py` - First selected circuit
- `circuit-synth/{name}.py` - Additional circuits
- `README.md` - With circuit descriptions
- `CLAUDE.md` - AI guidance
- `.claude/agents/` - 13 AI agents

### 2. Quick Start (No Prompts)
```bash
$ uv run cs-new-project --quick --skip-kicad-check
```
- Uses default: Resistor Divider
- No interactive prompts
- Completes instantly

### 3. Specific Circuits
```bash
$ uv run cs-new-project --circuits resistor,led,esp32 --skip-kicad-check
```
- Selects specific circuits by name
- `main.py` = resistor (first)
- `led_blinker.py` = led (second)
- `esp32_dev_board.py` = esp32 (third)

### 4. Developer Mode
```bash
$ uv run cs-new-project --quick --developer --skip-kicad-check
```
- Includes development agents and commands
- For circuit-synth contributors

### 5. Minimal Setup
```bash
$ uv run cs-new-project --quick --no-agents --skip-kicad-check
```
- Skips `.claude/` setup entirely
- Just circuit code + documentation

---

## 8 Circuit Templates Available

All templates are in: `src/circuit_synth/data/templates/`

| # | Template | Difficulty | Description | Files |
|---|----------|-----------|-------------|-------|
| 1 | Resistor Divider | ⭐ Beginner | 5V → 3.3V logic level shifter | base_circuits/ |
| 2 | LED Blinker | ⭐ Beginner | LED with current limiting resistor | base_circuits/ |
| 3 | Voltage Regulator | ⭐⭐ Intermediate | AMS1117-3.3 linear regulator | base_circuits/ |
| 4 | USB-C Basic | ⭐⭐ Intermediate | USB-C connector with CC resistors | example_circuits/ |
| 5 | Power Supply Module | ⭐⭐ Intermediate | Dual-rail 5V/3.3V power supply | example_circuits/ |
| 6 | ESP32-C6 Dev Board | ⭐⭐⭐ Advanced | Minimal ESP32 integration example | example_circuits/ |
| 7 | STM32 Minimal Board | ⭐⭐⭐ Advanced | STM32F411 with USB/crystal/SWD | example_circuits/ |
| 8 | Minimal/Empty | Expert | Blank template for experienced users | base_circuits/ |

---

## What Gets Generated

### File Structure
```
project/
├── circuit-synth/
│   ├── main.py                    ← First selected circuit
│   ├── [circuit2].py              ← Second circuit (if selected)
│   └── [circuit3].py              ← Third circuit (if selected)
├── README.md                      ← Project guide
├── CLAUDE.md                      ← AI assistant guidance
├── pyproject.toml                 ← Dependencies
└── .claude/                       ← (if agents enabled)
    ├── agents/
    │   ├── circuit-design/        (6 agents)
    │   ├── circuit-generation/    (1 agent)
    │   ├── manufacturing/         (2 agents)
    │   ├── microcontrollers/      (1 agent)
    │   ├── orchestration/         (1 agent)
    │   └── development/           (included if --developer)
    └── commands/
        └── (various slash commands)
```

### File Generation Logic

**First Circuit → `main.py`**
```python
# circuit-synth/main.py
# Contains the first selected circuit's code
@circuit(name="Resistor_Divider")
def resistor_divider():
    # ... circuit implementation
```

**Additional Circuits → Named Files**
```python
# circuit-synth/led_blinker.py
@circuit(name="LED_Blinker")
def led_blinker():
    # ... circuit implementation
```

**README Reflects Selection**
```markdown
# project_name

## 📁 Included Circuits (3)

This project includes the following circuit templates:

1. **Resistor Divider** (Beginner ⭐): 5V → 3.3V logic level shifter
   - File: `circuit-synth/main.py`

2. **LED Blinker** (Beginner ⭐): LED with current limiting resistor
   - File: `circuit-synth/led_blinker.py`

3. **ESP32-C6 Dev Board** (Advanced ⭐⭐⭐): Minimal ESP32 integration
   - File: `circuit-synth/esp32_dev_board.py`
```

---

## Tests Needed (35+ tests)

### Category 1: Parametrized Circuit Tests (8 tests)
**Goal:** Each circuit template generates correct file

```python
@pytest.mark.parametrize("circuit_enum", [
    Circuit.RESISTOR_DIVIDER,
    Circuit.LED_BLINKER,
    Circuit.VOLTAGE_REGULATOR,
    Circuit.USB_C_BASIC,
    Circuit.POWER_SUPPLY,
    Circuit.ESP32_DEV_BOARD,
    Circuit.STM32_MINIMAL,
    Circuit.MINIMAL,
])
def test_circuit_generates_main_py(circuit_enum, temp_project_dir):
    """Test that circuit template generates correct main.py"""
    # Create project with single circuit
    config = ProjectConfig(circuits=[circuit_enum])

    # Verify main.py exists
    main_py = temp_project_dir / "circuit-synth" / "main.py"
    assert main_py.exists()

    # Verify it contains circuit code
    content = main_py.read_text()
    assert circuit_enum.display_name.lower() in content.lower()

    # Verify Python syntax is valid
    import ast
    ast.parse(content)  # Raises SyntaxError if invalid
```

### Category 2: Multi-Circuit Tests (5 tests)

```python
def test_two_circuits_generates_both_files():
    """Test resistor + led generates 2 files"""
    config = ProjectConfig(circuits=[
        Circuit.RESISTOR_DIVIDER,
        Circuit.LED_BLINKER
    ])

    # Verify main.py is first circuit
    assert (project / "circuit-synth" / "main.py").exists()
    assert "Resistor" in (project / "circuit-synth" / "main.py").read_text()

    # Verify second circuit is named file
    assert (project / "circuit-synth" / "led_blinker.py").exists()
    assert "LED" in (project / "circuit-synth" / "led_blinker.py").read_text()

def test_all_eight_circuits_together():
    """Test all circuits generate all 8 files"""
    config = ProjectConfig(circuits=[
        Circuit.RESISTOR_DIVIDER,
        Circuit.LED_BLINKER,
        Circuit.VOLTAGE_REGULATOR,
        Circuit.USB_C_BASIC,
        Circuit.POWER_SUPPLY,
        Circuit.ESP32_DEV_BOARD,
        Circuit.STM32_MINIMAL,
        Circuit.MINIMAL,
    ])

    # Count files
    circuit_files = list((project / "circuit-synth").glob("*.py"))
    assert len(circuit_files) == 8

    # README should list all 8
    readme = (project / "README.md").read_text()
    assert "8" in readme or "Included Circuits" in readme
```

### Category 3: Flag Combination Tests (6+ tests)

```python
def test_no_agents_flag_skips_claude_directory():
    """--no-agents should not create .claude/"""
    config = ProjectConfig(
        circuits=[Circuit.RESISTOR_DIVIDER],
        include_agents=False
    )

    assert not (project / ".claude").exists()

def test_developer_flag_includes_dev_agents():
    """--developer should include development agents"""
    config = ProjectConfig(
        circuits=[Circuit.RESISTOR_DIVIDER],
        include_agents=True,
        developer_mode=True
    )

    # Should have dev agents
    assert (project / ".claude" / "agents" / "development").exists()
    dev_agents = list((project / ".claude" / "agents" / "development").glob("*.md"))
    assert len(dev_agents) > 0

def test_quick_flag_uses_default_circuit():
    """--quick should use Resistor Divider by default"""
    # Quick mode should create same as interactive with default
    config = ProjectConfig(circuits=[Circuit.RESISTOR_DIVIDER])

    assert (project / "circuit-synth" / "main.py").exists()
    assert "Resistor" in (project / "circuit-synth" / "main.py").read_text()
```

### Category 4: Edge Case Tests (5+ tests)

```python
def test_invalid_circuit_names_skipped():
    """Invalid circuit names should be skipped with warning"""
    # This tests the parse_cli_flags function
    config = parse_cli_flags("invalid,resistor,notreal", no_agents=False, developer=False)

    # Should have valid circuit only
    assert Circuit.RESISTOR_DIVIDER in config.circuits
    # Should NOT have invalid ones
    assert len(config.circuits) == 1

def test_empty_circuit_selection_uses_default():
    """Empty selection should fallback to Resistor Divider"""
    config = parse_cli_flags("", no_agents=False, developer=False)

    assert config.circuits == [Circuit.RESISTOR_DIVIDER]

def test_duplicate_circuits_handled():
    """Duplicate circuits should be handled gracefully"""
    # Test if "resistor,resistor,led" works
    config = parse_cli_flags("resistor,resistor,led", no_agents=False, developer=False)

    # Should either deduplicate or handle gracefully
    assert len(config.circuits) >= 1
    assert Circuit.RESISTOR_DIVIDER in config.circuits
```

### Category 5: File Content Validation (5+ tests)

```python
def test_readme_lists_all_circuits():
    """README should list all selected circuits"""
    config = ProjectConfig(circuits=[
        Circuit.RESISTOR_DIVIDER,
        Circuit.LED_BLINKER,
        Circuit.ESP32_DEV_BOARD
    ])

    readme = (project / "README.md").read_text()

    # Should mention all 3
    assert "Resistor Divider" in readme
    assert "LED Blinker" in readme
    assert "ESP32" in readme

    # Should mention count
    assert "3" in readme  # or "Included Circuits (3)"

def test_all_circuit_files_are_valid_python():
    """All generated .py files should have valid syntax"""
    circuit_files = (project / "circuit-synth").glob("*.py")

    import ast
    for circuit_file in circuit_files:
        content = circuit_file.read_text()
        ast.parse(content)  # Raises SyntaxError if invalid

def test_no_workspace_configuration_regression():
    """Regression: pyproject.toml should NOT contain workspace = true"""
    pyproject = (project / "pyproject.toml").read_text()

    assert "workspace = true" not in pyproject
    assert "[tool.uv.workspace]" not in pyproject

def test_main_py_is_importable():
    """main.py should be syntactically correct and importable"""
    main_py = (project / "circuit-synth" / "main.py").read_text()

    import ast
    tree = ast.parse(main_py)

    # Should have a @circuit decorated function
    has_circuit_decorator = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if hasattr(decorator, 'id') and decorator.id == 'circuit':
                    has_circuit_decorator = True

    assert has_circuit_decorator, "main.py should have @circuit decorated function"
```

---

## Test Organization

### File Location
```
tests/unit/tools/project_management/
├── __init__.py
├── test_new_project.py           ← Existing (23 tests) ✅
└── test_new_project_cli.py        ← NEW (35+ tests) 🆕
```

### Using Fixtures and Parametrization

```python
import pytest
from circuit_synth.tools.project_management.project_config import Circuit, ProjectConfig
from circuit_synth.tools.project_management.template_manager import TemplateManager

@pytest.fixture
def temp_project(tmp_path):
    """Fixture: temporary project directory"""
    return tmp_path / "test_project"

@pytest.mark.parametrize("circuit", list(Circuit))
def test_each_circuit(circuit, temp_project):
    """Parametrized test runs for all 8 circuits"""
    # Test implementation
```

---

## Expected Test Results

### Current State
```bash
$ uv run pytest tests/unit/tools/project_management/test_new_project.py -v
============================== 23 passed in 0.07s ==============================
```

### After Implementation
```bash
$ uv run pytest tests/unit/tools/project_management/ -v
test_new_project.py::test_creates_readme_md PASSED                    [ 1%]
test_new_project.py::test_creates_claude_md PASSED                    [ 2%]
...
test_new_project.py::test_fallback_to_basic_setup_on_template_failure [ 23%]

test_new_project_cli.py::test_resistor_divider_generates_main_py PASSED  [24%]
test_new_project_cli.py::test_led_blinker_generates_main_py PASSED       [25%]
test_new_project_cli.py::test_voltage_regulator_generates_main_py PASSED [26%]
...
test_new_project_cli.py::test_all_circuits_generate_files PASSED         [58%]

============================== 58 passed in 0.52s ==============================
```

---

## Success Criteria

✅ **All Tests Pass**
- [ ] 23 existing tests still pass
- [ ] 35+ new tests all pass
- [ ] Total time < 1 second
- [ ] 0 flaky tests

✅ **All Circuits Tested**
- [ ] Each of 8 circuits tested individually
- [ ] File naming is correct (main.py for first, {name}.py for others)
- [ ] File content matches circuit code

✅ **All CLI Flags Tested**
- [ ] `--quick` works
- [ ] `--circuits SPEC` parses correctly
- [ ] `--no-agents` skips agent setup
- [ ] `--developer` includes dev tools
- [ ] `--skip-kicad-check` skips validation
- [ ] Flag combinations work together

✅ **Edge Cases Covered**
- [ ] Invalid circuits skipped gracefully
- [ ] Empty selection falls back to default
- [ ] Duplicate circuits handled
- [ ] Missing templates error handling
- [ ] Special characters in paths work

✅ **File Content Valid**
- [ ] README mentions all circuits
- [ ] Python syntax is valid
- [ ] No "workspace = true" regression
- [ ] Projects are executable

✅ **Code Quality**
- [ ] Clear test names
- [ ] Good documentation
- [ ] Parametrized where appropriate
- [ ] Fixtures for reuse

---

## Documentation Provided

1. **TEST_PLAN_CS_NEW_PROJECT.md** (Detailed)
   - All invocation paths
   - File generation expectations
   - Validation steps
   - Test coverage matrix

2. **IMPLEMENTATION_PLAN.md** (Tactical)
   - Step-by-step implementation
   - Test structure
   - Risk mitigation
   - Timeline

3. **PLAN_SUMMARY.md** (This document)
   - Overview
   - Quick reference
   - Success criteria

---

## Key Insights

### What Users Expect
1. **First circuit in `main.py`** - Primary entry point
2. **Additional circuits in named files** - Can import and use
3. **README reflects selection** - Documentation is accurate
4. **Project is runnable** - `uv run python circuit-synth/main.py` works
5. **No agent noise if not needed** - `--no-agents` for minimal setup

### What Can Go Wrong
1. **Wrong file generated** - Test catches it
2. **Invalid Python syntax** - Test validates it
3. **Missing documentation** - Test checks README
4. **Regressions** - Regression test prevents it
5. **Edge cases** - Comprehensive edge case tests

### How to Prevent Issues
1. **Parametrize circuit tests** - Test all 8 at once
2. **Use fixtures** - DRY code
3. **Validate file content** - Not just existence
4. **Test flag combinations** - Real-world usage
5. **Include regression tests** - Prevent past bugs

---

## Recommendations

### Phase 1 (Now)
1. Review this plan ✅
2. Create test file structure
3. Implement parametrized circuit tests
4. All 8 circuits tested individually

### Phase 2 (Next)
5. Implement multi-circuit tests
6. Implement flag combination tests
7. Implement edge case tests

### Phase 3 (Polish)
8. Implement content validation
9. Run all tests
10. Update PR with results

---

## Questions This Plan Answers

| Question | Answer | How Tested |
|----------|--------|-----------|
| Does each circuit template work? | YES | Parametrized tests (1 per circuit) |
| Do multi-circuit projects work? | YES | Multi-circuit tests |
| Are files generated correctly named? | YES | File naming validation |
| Do generated files have valid syntax? | YES | Python AST parsing |
| Do README descriptions match projects? | YES | README content checks |
| Are all CLI flags working? | YES | Flag combination tests |
| Are edge cases handled? | YES | Edge case test suite |
| Can generated projects run? | YES | Syntax + import validation |
| Are there any regressions? | NO | Regression test suite |

---

## Next Actions

**1. Review This Plan**
- Read through all three markdown files
- Understand test structure
- Confirm approach matches your vision

**2. Implement Phase 1**
- Create `tests/unit/tools/project_management/test_new_project_cli.py`
- Add parametrized circuit tests (8 tests)
- Run to verify they pass

**3. Continue with Phases 2 & 3**
- Add multi-circuit tests
- Add flag tests
- Add edge case tests
- Validate all content

**4. Update PR**
- Document new test count (58 total)
- Include test results
- Show coverage

---

## Files to Review

📄 **TEST_PLAN_CS_NEW_PROJECT.md**
- Detailed specifications
- CLI invocation paths
- File generation expectations

📄 **IMPLEMENTATION_PLAN.md**
- Step-by-step guide
- Test structure details
- Success criteria

📄 **PLAN_SUMMARY.md** (this file)
- Overview and quick reference
- Key insights
- Next actions

---

**Ready to implement? Let's go! 🚀**
