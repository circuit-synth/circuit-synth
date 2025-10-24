# Comprehensive Test Plan: cs-new-project CLI Invocations

## Overview

This document outlines all possible invocations of `cs-new-project` and the expected files generated for each. The goal is to ensure that users get exactly what they expect when creating new circuit-synth projects.

---

## Available Circuit Templates

| #  | Circuit | Difficulty | File | Description |
|----|---------|-----------|------|-------------|
| 1  | Resistor Divider | Beginner ⭐ | resistor_divider.py | 5V → 3.3V logic level shifter |
| 2  | LED Blinker | Beginner ⭐ | led_blinker.py | LED with current limiting resistor |
| 3  | Voltage Regulator | Intermediate ⭐⭐ | voltage_regulator.py | AMS1117-3.3 linear regulator |
| 4  | USB-C Basic | Intermediate ⭐⭐ | usb_c_basic.py | USB-C with CC resistors |
| 5  | Power Supply Module | Intermediate ⭐⭐ | power_supply_module.py | Dual-rail 5V/3.3V power supply |
| 6  | ESP32-C6 Dev Board | Advanced ⭐⭐⭐ | esp32_dev_board.py | Minimal ESP32 integration |
| 7  | STM32 Minimal Board | Advanced ⭐⭐⭐ | stm32_minimal.py | STM32F411 with USB/crystal/SWD |
| 8  | Minimal/Empty | Expert | minimal.py | Blank template for experts |

---

## CLI Invocation Paths

### 1. Default Interactive Mode
**Command:** `uv run cs-new-project`

**User Interaction:**
- Shown welcome banner
- KiCad check runs
- Shown circuit selection table
- User selects circuits (default: 1 = Resistor Divider)
- Confirmation

**Expected Files:**
- ✅ `circuit-synth/main.py` - Resistor Divider template
- ✅ `README.md` - With "Resistor Divider" in circuits section
- ✅ `CLAUDE.md` - Project guidance
- ✅ `.claude/agents/` - All 13 agents
- ✅ `.claude/commands/` - Command stubs (empty)
- ❌ `.claude/development/` - NOT included (user mode)

**Regression Tests:**
- [ ] No `workspace = true` in any generated file
- [ ] README contains circuit descriptions
- [ ] circuit-synth/main.py is valid Python
- [ ] .claude structure is correct

---

### 2. Quick Start Mode
**Command:** `uv run cs-new-project --quick`

**Behavior:**
- No KiCad check
- No interactive prompts
- Uses default: Resistor Divider
- Includes agents by default

**Expected Files:**
- ✅ `circuit-synth/main.py` - Resistor Divider template
- ✅ `README.md` - Standard template
- ✅ `CLAUDE.md` - Standard template
- ✅ `.claude/agents/` - All 13 agents

**Regression Tests:**
- [ ] Completes in <1 second (no user interaction)
- [ ] Identical output to interactive mode with default selection
- [ ] No prompts shown

---

### 3. Specific Circuits via Flag
**Command:** `uv run cs-new-project --circuits resistor,led,esp32 --skip-kicad-check`

**Behavior:**
- Parses comma-separated circuit list
- Skips KiCad check
- No interactive mode
- Includes agents by default

**Expected Files:**
- ✅ `circuit-synth/main.py` - Resistor Divider (first)
- ✅ `circuit-synth/led_blinker.py` - LED Blinker (second)
- ✅ `circuit-synth/esp32_dev_board.py` - ESP32 (third)
- ✅ `README.md` - With all 3 circuits listed
- ✅ `CLAUDE.md`
- ✅ `.claude/agents/`

**File Content Tests:**
- [ ] main.py contains Resistor Divider code
- [ ] led_blinker.py contains LED Blinker code
- [ ] esp32_dev_board.py contains ESP32 code
- [ ] README lists all 3 in order

---

### 4. No Agents Mode
**Command:** `uv run cs-new-project --quick --no-agents --skip-kicad-check`

**Expected Files:**
- ✅ `circuit-synth/main.py` - Resistor Divider
- ✅ `README.md`
- ✅ `CLAUDE.md`
- ❌ `.claude/` directory - NOT created

**Regression Tests:**
- [ ] .claude directory does not exist
- [ ] No agent files created
- [ ] Project still runs: `uv run python circuit-synth/main.py`

---

### 5. Developer Mode
**Command:** `uv run cs-new-project --quick --developer --skip-kicad-check`

**Expected Files:**
- ✅ `circuit-synth/main.py`
- ✅ `README.md`
- ✅ `CLAUDE.md`
- ✅ `.claude/agents/` - All 13 agents INCLUDING development/
- ✅ `.claude/commands/` - INCLUDING development/ commands

**File Count Tests:**
- [ ] `.claude/agents/` has 13+ agent files (includes contributor.md)
- [ ] `.claude/commands/` includes dev-* commands
- [ ] Can find: dev-run-tests.md, dev-review-branch.md, etc.

---

### 6. Minimal/Empty Template
**Command:** `uv run cs-new-project --circuits minimal --skip-kicad-check`

**Expected Files:**
- ✅ `circuit-synth/main.py` - Minimal template (empty circuit function)
- ✅ `README.md`
- ✅ `CLAUDE.md`
- ✅ `.claude/agents/`

**Content Tests:**
- [ ] main.py contains a blank `circuit()` decorated function
- [ ] main.py is syntactically valid Python
- [ ] Function signature is: `@circuit(name="...")`

---

### 7. Multiple Circuits (All 8)
**Command:** `uv run cs-new-project --circuits resistor,led,voltage,usb,power,esp32,stm32,minimal --skip-kicad-check`

**Expected Files:**
- ✅ `circuit-synth/main.py` - Resistor Divider
- ✅ `circuit-synth/led_blinker.py`
- ✅ `circuit-synth/voltage_regulator.py`
- ✅ `circuit-synth/usb_c_basic.py`
- ✅ `circuit-synth/power_supply_module.py`
- ✅ `circuit-synth/esp32_dev_board.py`
- ✅ `circuit-synth/stm32_minimal.py`
- ✅ `circuit-synth/minimal.py`
- ✅ `README.md` - Lists all 8
- ✅ `CLAUDE.md`
- ✅ `.claude/agents/`

**File Count Tests:**
- [ ] Exactly 8 files in circuit-synth/ directory (main.py + 7 others)
- [ ] README lists all 8 circuits
- [ ] All files are valid Python

---

## Flag Combinations to Test

| Test # | Flags | Interactive? | Agents? | Dev Tools? | Description |
|--------|-------|---|---|---|---|
| 1 | None | Yes | Yes | No | Full interactive |
| 2 | --quick | No | Yes | No | Quick default |
| 3 | --quick --developer | No | Yes | Yes | Quick with dev tools |
| 4 | --quick --no-agents | No | No | No | Minimal setup |
| 5 | --circuits SPEC | No | Yes | No | Specific circuits |
| 6 | --circuits SPEC --developer | No | Yes | Yes | Circuits + dev |
| 7 | --circuits SPEC --no-agents | No | No | No | Circuits only |
| 8 | --skip-kicad-check | Yes | Yes | No | Skip KiCad (for CI) |
| 9 | --quick --skip-kicad-check | No | Yes | No | CI friendly quick start |

---

## Edge Cases to Test

### 1. No Circuits Selected (Interactive)
**User Action:** Presses Enter without selecting circuits

**Expected Behavior:**
- [ ] Falls back to Resistor Divider
- [ ] Shows warning message
- [ ] Creates project successfully

---

### 2. Invalid Circuit Names
**Command:** `uv run cs-new-project --circuits invalid,resistor,notreal`

**Expected Behavior:**
- [ ] Skips invalid circuits
- [ ] Uses valid circuits (resistor)
- [ ] Shows warning for invalid ones
- [ ] Creates project with valid circuits

---

### 3. Duplicate Circuit Selection
**Command:** `uv run cs-new-project --circuits resistor,resistor,led`

**Expected Behavior:**
- [ ] Handles duplicates gracefully
- [ ] Either includes duplicates OR deduplicates
- [ ] Documents behavior in error message

---

### 4. Empty Circuit List
**Command:** `uv run cs-new-project --circuits ""`

**Expected Behavior:**
- [ ] Falls back to default (Resistor Divider)
- [ ] Shows warning
- [ ] Creates project successfully

---

### 5. Project Already Has circuit-synth/
**Scenario:** User runs cs-new-project in directory with existing project

**Expected Behavior:**
- [ ] Overwrites existing circuit files
- [ ] Preserves other files
- [ ] Shows warning about overwriting

---

## File Content Validation Tests

### All Projects Should Have:
```
project/
├── circuit-synth/
│   └── main.py              # Should be valid Python ✓
├── README.md                # Should contain project info ✓
├── CLAUDE.md                # Should contain guidance ✓
└── pyproject.toml           # Should be valid TOML ✓
```

### Validation Steps:
```python
def validate_project_files(project_path: Path):
    """Validate generated project structure and content"""

    # 1. Check all required files exist
    assert (project_path / "circuit-synth" / "main.py").exists()
    assert (project_path / "README.md").exists()
    assert (project_path / "CLAUDE.md").exists()

    # 2. Validate Python syntax
    import ast
    main_py = (project_path / "circuit-synth" / "main.py").read_text()
    ast.parse(main_py)  # Will raise SyntaxError if invalid

    # 3. Validate no workspace configuration
    pyproject = (project_path / "pyproject.toml").read_text()
    assert "workspace = true" not in pyproject
    assert "[tool.uv.workspace]" not in pyproject

    # 4. Check file permissions
    assert (project_path / "circuit-synth").is_dir()

    # 5. Validate README contains circuit info
    readme = (project_path / "README.md").read_text()
    assert "circuit" in readme.lower()
```

---

## Test Execution Commands

### Run All Generated Files Through Static Analysis
```bash
# All generated Python files
uv run python -m py_compile circuit-synth/*.py

# Type checking (optional)
uv run mypy circuit-synth/

# Linting
uv run flake8 circuit-synth/
```

### Run Actual Circuit Execution
```bash
# Try to import and execute first circuit
uv run python circuit-synth/main.py
```

### Check Generated TOML
```bash
# Validate pyproject.toml syntax
python -c "import toml; toml.load('pyproject.toml')"
```

---

## Test Implementation Strategy

### Unit Tests (Fast, 100% coverage)
- File existence checks
- File content validation (README mentions circuits)
- Python syntax validation
- No forbidden patterns (workspace = true)

### Integration Tests (Slower, realistic)
- Create actual temporary projects
- Run python -c to validate syntax
- Execute circuit generation (if KiCad available)

### Regression Tests (Prevent known bugs)
- Workspace configuration bug (#0.8.22)
- Empty circuit selection
- Template not found fallback
- Agent registration errors

---

## Test Coverage Matrix

```
┌─────────────────────────┬───────┬──────────┬──────────┐
│ Scenario                │ Unit? │ Integration? │ Regression? │
├─────────────────────────┼───────┼──────────┼──────────┤
│ File generation         │   ✓   │    ✓     │    ✓     │
│ Content validation      │   ✓   │    ✓     │          │
│ All circuits 1-by-1     │   ✓   │    ✓     │          │
│ Multi-circuit projects  │   ✓   │    ✓     │          │
│ Flag combinations       │       │    ✓     │          │
│ Edge cases              │   ✓   │    ✓     │    ✓     │
│ Agent setup             │   ✓   │    ✓     │          │
│ Developer mode          │   ✓   │    ✓     │          │
│ No agents mode          │   ✓   │    ✓     │          │
│ Project execution       │       │    ✓     │    ✓     │
└─────────────────────────┴───────┴──────────┴──────────┘
```

---

## Success Criteria

✅ **All Tests Pass**
- [ ] 23 unit tests passing (existing)
- [ ] 30+ new integration tests for CLI paths
- [ ] 0 regressions in existing functionality

✅ **File Generation is Correct**
- [ ] Each circuit template generates correct file
- [ ] Multi-circuit projects have all files
- [ ] README lists circuits in order
- [ ] No forbidden patterns in generated files

✅ **Edge Cases Handled**
- [ ] Empty selections fall back to default
- [ ] Invalid circuits skipped gracefully
- [ ] Missing templates handled
- [ ] All flag combinations work

✅ **User Experience**
- [ ] Interactive mode shows helpful prompts
- [ ] Quick mode is actually quick (<1s)
- [ ] Error messages are clear
- [ ] Generated project runs without errors

---

## Next Steps

1. **Expand unit tests** to cover each circuit template individually
2. **Add parametrized tests** for all 8 circuits × 3 flag sets = 24 combinations
3. **Add integration tests** using `click.testing.CliRunner`
4. **Add CLI invocation tests** that exercise all flag combinations
5. **Validate against existing end-to-end test** to ensure consistency
