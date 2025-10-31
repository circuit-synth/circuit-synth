---
name: validate-docs
description: Validate documentation alignment across PyPI, GitHub, ReadTheDocs
---

# Documentation Validation Command

Validates that all critical documentation files are aligned and consistent.

## Purpose

Prevents documentation drift between:
- **PyPI** (uses README.md via pyproject.toml)
- **GitHub** (README.md landing page)
- **ReadTheDocs** (docs/ directory)

## What This Checks

1. **Installation Instructions** - README.md, docs/index.rst, docs/installation.rst must be consistent
2. **File Paths** - Detects incorrect paths in examples (e.g., `example_project/circuit-synth/main.py`)
3. **Import Statements** - Verifies circuit pattern imports are correct
4. **PyPI Metadata** - Checks pyproject.toml configuration
5. **Code Examples** - Basic syntax validation for Python code blocks in README

## Common Issues Detected

| Issue | Example | Fix |
|-------|---------|-----|
| Wrong path after cs-new-project | `cd project/circuit-synth` | `cd project` |
| Missing uv installation | Only shows `pip install` | Show both `uv add` and `pip install` |
| Incorrect imports | `from buck_converter import ...` | Add comment explaining where it comes from |
| Bad nested paths | `circuit-synth/circuit-synth/main.py` | `cd my_project` then `python main.py` |

## Usage

```bash
/dev:validate-docs
```

## Implementation

The command runs the automated validator script that checks all critical documentation files:

```bash
#!/bin/bash

echo "🔍 Validating circuit-synth documentation alignment..."
echo ""

# Run the validation script
python3 tools/documentation/validate_docs.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Documentation validation complete - all checks passed!"
    echo "📚 README.md, docs/index.rst, and pyproject.toml are aligned"
else
    echo ""
    echo "❌ Documentation validation failed!"
    echo ""
    echo "📖 For guidance on fixing documentation issues, see:"
    echo "   docs/DOCUMENTATION_MAINTENANCE.md"
    echo ""
    echo "Common fixes:"
    echo "  • Update file paths to match current project structure"
    echo "  • Ensure installation instructions show both 'uv add' and 'pip install'"
    echo "  • Add clarifying comments to import statements"
    exit 1
fi
```

## What Gets Validated

### 1. Installation Consistency

**Checks:**
- README.md has both `uv add circuit-synth` AND `pip install circuit-synth`
- docs/index.rst matches README installation commands
- docs/installation.rst is comprehensive and up-to-date

**Why:** Users see different docs depending on where they land (PyPI, GitHub, ReadTheDocs). All must show the same installation steps.

### 2. File Path Correctness

**Checks for these WRONG patterns:**
- `example_project/circuit-synth/main.py` (doesn't exist after cs-new-project)
- `circuit-synth/circuit-synth/main.py` (wrong nested path)
- `cd circuit-synth && uv run python circuit-synth/main.py` (incorrect)

**Correct patterns:**
- `cs-new-project my_project`
- `cd my_project`
- `uv run python main.py`

### 3. PyPI Metadata

**Checks:**
- `pyproject.toml` has `readme = "README.md"` (uses README as long_description)
- All required URLs present (Homepage, Documentation, Repository, Issues)
- Description is concise and accurate

### 4. Code Example Syntax

**Checks:**
- Python code blocks in README.md compile without syntax errors
- Incomplete examples (with `...`) are skipped
- Import statements are valid Python syntax

## Output Examples

### ✅ All Checks Pass

```
🔍 Running documentation validation...

✅ All documentation validation checks passed!
```

### ❌ Errors Found

```
🔍 Running documentation validation...

❌ ERRORS FOUND:
  • README.md:136 contains bad path 'example_project/circuit-synth/main.py'.
    Wrong path after cs-new-project. Should be just 'python main.py' after cd to project

⚠️  WARNINGS:
  • docs/index.rst missing 'uv add circuit-synth' (present in README.md)

❌ Found 1 error(s), 1 warning(s)
Fix errors before release!
```

## When to Run

**Always run before:**
- Creating a pull request
- Making a release
- Updating documentation

**Run automatically in:**
- Pre-commit hooks (recommended)
- `/dev:release-pypi` command (required)
- CI/CD pipeline (optional but good)

## Integration with Release Process

This command is now part of `/dev:release-pypi` - all releases automatically validate documentation before publishing to PyPI.

See `.claude/commands/dev/release-pypi.md` for the full release workflow.

## For Maintainers

### Adding New Checks

To add a new validation check:

1. Edit `tools/documentation/validate_docs.py`
2. Add a new method to `DocValidator` class
3. Call it from `run_all_checks()`
4. Update this documentation

Example:

```python
def check_new_thing(self):
    """Check for some new documentation pattern."""
    readme = Path("README.md").read_text()

    if "bad_pattern" in readme:
        self.errors.append("Found bad_pattern in README.md")
```

### Common Fixes

**Fix 1: Wrong Path**
```python
# BAD
cd my_first_board/circuit-synth
uv run python example_project/circuit-synth/main.py

# GOOD
cd my_first_board
uv run python main.py
```

**Fix 2: Missing uv Installation**
```rst
.. code-block:: bash

   # Recommended: uv
   uv add circuit-synth

   # Alternative: pip
   pip install circuit-synth
```

## Related Documentation

- **Maintenance Guide:** `docs/DOCUMENTATION_MAINTENANCE.md`
- **Validation Script:** `tools/documentation/validate_docs.py`
- **Documentation Inventory:** `DOCUMENTATION_INVENTORY.md`
- **Audit Report:** `DOCUMENTATION_AUDIT_REPORT.md`

## Exit Codes

- **0**: All checks passed ✅
- **1**: Errors found, must fix before release ❌

---

**Remember:** Documentation is code. Treat it with the same care as Python code - test it, validate it, keep it DRY.
