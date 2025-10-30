# Circuit-Synth Documentation Audit Report

**Date:** 2025-10-30
**Auditor:** Claude Code
**Scope:** PyPI metadata, README.md, ReadTheDocs alignment

## Executive Summary

This audit addresses feedback from a user (Shan Zhao) who identified **documentation discordance** between PyPI and GitHub repo due to recent refactoring.

### Critical Findings

1. **PyPI Description**: Uses README.md directly (good!)
2. **Version Alignment**: README.md examples show outdated workflow patterns
3. **ReadTheDocs**: Configuration is modern and aligned
4. **Installation Instructions**: Inconsistent between sources

---

## 1. PyPI Metadata Audit (pyproject.toml)

### ✅ Correct Metadata

```toml
name = "circuit_synth"
description = "Pythonic circuit design for production-ready KiCad projects"
readme = "README.md"  # ✅ GOOD: Uses README.md as long_description
```

**Finding:** PyPI correctly uses README.md as the package description. This is the RIGHT approach.

### ✅ Project URLs

```toml
Homepage = "https://github.com/circuit-synth/circuit-synth"
Documentation = "https://circuit-synth.readthedocs.io"
Repository = "https://github.com/circuit-synth/circuit-synth"
Issues = "https://github.com/circuit-synth/circuit-synth/issues"
```

**Finding:** All URLs are correct and point to the right locations.

### ✅ Dependencies

**Finding:** Dependencies are comprehensive and include modern versions:
- kicad-sch-api>=0.4.5 (recent version)
- kicad-pcb-api>=0.1.0
- All other dependencies are current

---

## 2. README.md vs PyPI Alignment

### ⚠️ CRITICAL DISCREPANCIES FOUND

#### Issue 1: Installation Instructions Inconsistency

**README.md line 158-162:**
```bash
uv add circuit-synth
# or
pip install circuit-synth
```

**README.md line 127-129 (First Time User section):**
```bash
pip install circuit-synth
```

**Finding:** README shows TWO different installation methods in different sections. PyPI viewers see the full README, which has this inconsistency.

**Impact:** Confusing for new users - should we use `uv` or `pip`?

#### Issue 2: Example Project Path Confusion

**README.md line 132-139:**
```bash
# 2. Create a new project with working example
uv run cs-new-project my_first_board

# 3. Generate KiCad files from the example
cd my_first_board/circuit-synth
uv run python example_project/circuit-synth/main.py  # ❌ WRONG PATH

# 4. Open in KiCad (generated in ESP32_C6_Dev_Board/)
open ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro
```

**Finding:** The path `example_project/circuit-synth/main.py` is INCORRECT after running `cs-new-project`.

**Correct path should be:**
```bash
cd my_first_board/circuit-synth
uv run python main.py
```

#### Issue 3: Outdated Quick Start Instructions

**README.md line 167-172:**
```bash
# Create new project with ESP32-C6 example
cs-new-project

# Generate KiCad files
cd circuit-synth && uv run python circuit-synth/main.py  # ❌ NESTED PATH WRONG
```

**Finding:** This path structure is incorrect. After `cs-new-project`, there's no nested `circuit-synth/circuit-synth/`.

#### Issue 4: Circuit Patterns Import Examples

**README.md line 604:**
```python
from buck_converter import buck_converter
from thermistor import thermistor_sensor
```

**Finding:** Missing package prefix. Should be:
```python
from circuit_synth.circuit_patterns.buck_converter import buck_converter
```

---

## 3. ReadTheDocs Audit

### ✅ Configuration (.readthedocs.yaml)

```yaml
version: 2
build:
  os: ubuntu-22.04
  tools:
    python: "3.12"
sphinx:
  configuration: docs/conf.py
```

**Finding:** ReadTheDocs configuration is modern and correct.

### ✅ Sphinx Configuration (docs/conf.py)

```python
project = 'Circuit-Synth'
copyright = '2025, Circuit Synth Contributors'
```

**Finding:** Sphinx config correctly pulls version from package and has proper mocking for dependencies.

### ⚠️ Documentation Index Discrepancy

**docs/index.rst line 67:**
```bash
pip install circuit-synth
```

**README.md line 159:**
```bash
uv add circuit-synth
# or
pip install circuit-synth
```

**Finding:** ReadTheDocs shows ONLY `pip install`, while README shows BOTH `uv add` and `pip install`.

**Impact:** Documentation readers don't learn about `uv` workflow.

---

## 4. Release Command Audit

### ✅ release-pypi.md Has Good Validation

The `/dev:release-pypi` command includes:
- Website validation
- Test suite execution
- Full regression testing
- TestPyPI staging

### ❌ MISSING: Documentation Alignment Check

**Finding:** The release command does NOT validate that:
1. README.md installation instructions are consistent
2. Example paths are correct
3. Import statements work as documented
4. ReadTheDocs index.rst matches README.md

---

## 5. Complete Discrepancy List

### High Priority (Breaks User Experience)

1. **README line 136:** Wrong path `example_project/circuit-synth/main.py` after `cs-new-project`
2. **README line 171:** Wrong nested path `circuit-synth/circuit-synth/main.py`
3. **README line 604:** Missing package prefix in circuit pattern imports
4. **README line 709:** Wrong path in circuit generation command

### Medium Priority (Confusing)

5. **README:** Inconsistent installation instructions (`uv add` vs `pip install`)
6. **docs/index.rst:** Missing `uv` installation method
7. **README:** Installation appears in multiple places with slight variations

### Low Priority (Documentation Quality)

8. **README:** Could use more explicit "After running cs-new-project" sections
9. **README:** Circuit pattern section could clarify where patterns live in created projects

---

## 6. Recommended Fixes

### Fix 1: Standardize Installation Instructions

**Create single source of truth:**

```markdown
## Installation

Install circuit-synth using your preferred package manager:

```bash
# Recommended: Using uv (faster, better dependency resolution)
uv add circuit-synth

# Alternative: Using pip
pip install circuit-synth
```

### Fix 2: Correct All Example Paths

**README.md "First Time User" section:**

```bash
# 1. Install circuit-synth
pip install circuit-synth

# 2. Create a new project
cs-new-project my_first_board

# 3. Generate KiCad files from the example
cd my_first_board
uv run python main.py

# 4. Open in KiCad
open ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro
```

**README.md "Quick Start" section:**

```bash
# Create new project with ESP32-C6 example
cs-new-project my_project

# Generate KiCad files
cd my_project
uv run python main.py
```

### Fix 3: Correct Circuit Pattern Imports

**README.md line 604:**

```python
from circuit_synth.circuit_patterns.buck_converter import buck_converter
from circuit_synth.circuit_patterns.thermistor import thermistor_sensor
```

**OR** (if patterns are copied to user project):

```python
# In your project created with cs-new-project
from buck_converter import buck_converter  # These are copied to your project
from thermistor import thermistor_sensor
```

### Fix 4: Add Documentation Validation to Release Command

Add to `.claude/commands/dev/release-pypi.md`:

```bash
# Documentation validation (before release)
echo "📚 Validating documentation alignment..."

# Check installation instructions consistency
if ! grep -q "uv add circuit-synth" README.md || ! grep -q "pip install circuit-synth" README.md; then
    echo "⚠️ README missing complete installation instructions"
fi

# Check for common path errors
if grep -q "example_project/circuit-synth/main.py" README.md; then
    echo "❌ README contains incorrect example path"
    exit 1
fi

if grep -q "circuit-synth/circuit-synth/main.py" README.md; then
    echo "❌ README contains incorrect nested path"
    exit 1
fi

# Verify ReadTheDocs config
if [ ! -f ".readthedocs.yaml" ]; then
    echo "❌ Missing .readthedocs.yaml"
    exit 1
fi

echo "✅ Documentation validation passed"
```

---

## 7. Action Items

### Immediate (Before Next Release)

- [ ] Fix all 4 incorrect file paths in README.md
- [ ] Standardize installation instructions across README and docs/index.rst
- [ ] Clarify circuit pattern import statements (where do they come from?)
- [ ] Add documentation validation to `/dev:release-pypi` command

### Short Term

- [ ] Create INSTALLATION.md with canonical installation instructions
- [ ] Add "After Installation" section to README with correct paths
- [ ] Test all README examples in fresh environment
- [ ] Add automated doc validation to CI/CD

### Long Term

- [ ] Generate README sections from tested code examples
- [ ] Add doc validation to pre-commit hooks
- [ ] Create "Common Mistakes" section in docs

---

## 8. Testing Plan

### Manual Testing

```bash
# Test 1: Fresh install and follow README "First Time User"
pip uninstall circuit-synth
pip install circuit-synth
# Follow README steps EXACTLY - do they work?

# Test 2: Verify all import statements
python -c "from circuit_synth.circuit_patterns.buck_converter import buck_converter"

# Test 3: Check ReadTheDocs build
cd docs
make clean html
# Any warnings about missing modules?
```

### Automated Testing

```python
# Add to test suite:
def test_readme_examples():
    """Verify all code examples in README.md are valid"""
    readme = Path("README.md").read_text()
    code_blocks = extract_python_blocks(readme)
    for block in code_blocks:
        # Validate syntax and imports
        compile(block, '<readme>', 'exec')
```

---

## Conclusion

The core infrastructure is GOOD:
- ✅ PyPI correctly uses README.md
- ✅ ReadTheDocs configuration is modern
- ✅ Dependencies are up to date

The PROBLEMS are:
- ❌ README contains outdated/incorrect example paths (4 instances)
- ❌ Inconsistent installation instructions
- ❌ Missing documentation validation in release process

**Root Cause:** Recent refactoring changed project structure, but documentation wasn't updated to match.

**Solution:** Fix the 4 critical path errors, standardize installation instructions, and add automated doc validation to prevent future drift.

**Estimated Time to Fix:** 30-45 minutes
**Impact of Not Fixing:** New users will be confused, follow wrong paths, and have poor first experience
