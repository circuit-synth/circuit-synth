# Documentation Maintenance Guide

**Purpose:** Guide for Claude Code (and humans) on maintaining circuit-synth documentation alignment

**Last Updated:** 2025-10-30

---

## 🎯 Documentation Philosophy

**Single Source of Truth:** `README.md` is the PRIMARY documentation source.
- PyPI uses `README.md` as long_description (via `readme = "README.md"` in pyproject.toml)
- ReadTheDocs supplements README with deeper technical guides
- All user-facing docs must align with README

**Why this matters:** Users see PyPI, GitHub, and ReadTheDocs. If they contradict each other, trust is lost.

---

## 📋 Critical Documentation Files (The Alignment Set)

These 5 files MUST be kept in sync at all times:

### 1. README.md (Primary Source)
**Location:** `/README.md`
**Purpose:** Main project documentation, PyPI long_description, GitHub landing page
**Audience:** New users, PyPI visitors, GitHub explorers
**Update Frequency:** Every release, every feature

**Critical Sections:**
- Installation instructions (lines 127-129, 158-162)
- Quick Start / First Time User (lines 123-172)
- Example code snippets (lines 175-214, 604-620)
- Command examples (lines 167-172, 709)

**Common Errors to Check:**
- [ ] Incorrect file paths after `cs-new-project`
- [ ] Inconsistent installation commands (uv vs pip)
- [ ] Wrong import statements for circuit patterns
- [ ] Outdated API usage in examples

### 2. docs/index.rst (ReadTheDocs Landing)
**Location:** `/docs/index.rst`
**Purpose:** ReadTheDocs homepage, Quick Start for RTD visitors
**Audience:** Users seeking detailed documentation
**Update Frequency:** When README changes significantly

**Must Match README:**
- [ ] Installation commands (pip AND uv)
- [ ] Quick Start code example
- [ ] Core features list
- [ ] Version badges

### 3. docs/installation.rst
**Location:** `/docs/installation.rst`
**Purpose:** Detailed installation guide
**Audience:** Users with special installation needs
**Update Frequency:** When installation process changes

**Must Match README:**
- [ ] Primary installation command
- [ ] Alternative installation methods
- [ ] Prerequisites (Python version, KiCad)
- [ ] Troubleshooting common issues

### 4. docs/quickstart.rst
**Location:** `/docs/quickstart.rst`
**Purpose:** Expanded quick start tutorial
**Audience:** Users learning circuit-synth for first time
**Update Frequency:** When Quick Start workflow changes

**Must Match README:**
- [ ] Example circuit code
- [ ] Command sequence (cs-new-project, python main.py, etc.)
- [ ] Expected output/results
- [ ] File paths after project creation

### 5. pyproject.toml
**Location:** `/pyproject.toml`
**Purpose:** Package metadata, PyPI configuration
**Audience:** Package managers, developers
**Update Frequency:** Every release

**Critical Fields:**
- `description` - One-line project description
- `readme = "README.md"` - MUST point to README.md
- `[project.urls]` - Homepage, Documentation, Repository, Issues
- `requires-python` - Python version requirement
- `dependencies` - Must match actual code requirements

---

## 🔍 How to Validate Documentation Alignment

### Manual Check (5 minutes before any release)

Run this checklist:

```bash
# 1. Check installation instructions consistency
echo "=== Installation Instructions Check ==="
echo "README.md installation commands:"
grep -A 2 "pip install circuit-synth" README.md
grep -A 2 "uv add circuit-synth" README.md

echo "docs/index.rst installation commands:"
grep -A 2 "pip install circuit-synth" docs/index.rst
grep -A 2 "uv add circuit-synth" docs/index.rst

# 2. Check for incorrect paths
echo "=== Path Error Check ==="
echo "Checking for 'example_project/circuit-synth/main.py' (WRONG):"
grep -n "example_project/circuit-synth/main.py" README.md && echo "❌ FOUND BAD PATH" || echo "✅ No bad paths"

echo "Checking for 'circuit-synth/circuit-synth/main.py' (WRONG):"
grep -n "circuit-synth/circuit-synth/main.py" README.md && echo "❌ FOUND BAD PATH" || echo "✅ No bad paths"

# 3. Check for correct paths
echo "=== Correct Path Verification ==="
echo "Checking for correct path after cs-new-project:"
grep -n "cd my_first_board" README.md
grep -n "uv run python main.py" README.md

# 4. Verify import statements
echo "=== Import Statement Check ==="
echo "Circuit pattern imports:"
grep -n "from.*import.*converter" README.md
```

### Automated Validation Script

**Location:** `/tools/documentation/validate_docs.py`

```python
#!/usr/bin/env python3
"""
Automated documentation alignment validator.

Usage:
    python tools/documentation/validate_docs.py

Returns:
    Exit code 0: All docs aligned
    Exit code 1: Alignment issues found
"""

import sys
from pathlib import Path
import re

class DocValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def check_installation_consistency(self):
        """Verify installation commands match across docs."""
        readme = Path("README.md").read_text()
        index_rst = Path("docs/index.rst").read_text()

        # README must have both pip and uv
        has_pip_in_readme = "pip install circuit-synth" in readme
        has_uv_in_readme = "uv add circuit-synth" in readme

        if not (has_pip_in_readme and has_uv_in_readme):
            self.errors.append(
                "README.md missing complete installation instructions. "
                "Must include both 'pip install circuit-synth' AND 'uv add circuit-synth'"
            )

        # docs/index.rst should match
        if has_pip_in_readme and "pip install circuit-synth" not in index_rst:
            self.errors.append(
                "docs/index.rst missing 'pip install circuit-synth' "
                "(present in README.md)"
            )

    def check_bad_paths(self):
        """Check for known incorrect file paths."""
        readme = Path("README.md").read_text()

        bad_paths = [
            ("example_project/circuit-synth/main.py",
             "Wrong path after cs-new-project. Should be just 'python main.py'"),
            ("circuit-synth/circuit-synth/main.py",
             "Wrong nested path. Should be 'cd my_project' then 'python main.py'"),
        ]

        for bad_path, explanation in bad_paths:
            if bad_path in readme:
                line_num = None
                for i, line in enumerate(readme.split('\n'), 1):
                    if bad_path in line:
                        line_num = i
                        break
                self.errors.append(
                    f"README.md:{line_num} contains bad path '{bad_path}'. "
                    f"{explanation}"
                )

    def check_correct_paths(self):
        """Verify correct paths are documented."""
        readme = Path("README.md").read_text()

        correct_patterns = [
            # After cs-new-project, should cd to project then run main.py
            (r"cd (my_first_board|my_project)\s*\n.*python main\.py",
             "Correct workflow: cd PROJECT then python main.py"),
        ]

        for pattern, description in correct_patterns:
            if not re.search(pattern, readme):
                self.warnings.append(
                    f"README.md may be missing correct pattern: {description}"
                )

    def check_pyproject_metadata(self):
        """Verify pyproject.toml has correct metadata."""
        pyproject = Path("pyproject.toml").read_text()

        # Must use README.md as readme
        if 'readme = "README.md"' not in pyproject:
            self.errors.append(
                "pyproject.toml must have 'readme = \"README.md\"' "
                "to use README as PyPI long_description"
            )

        # Check required URLs
        required_urls = [
            "Homepage",
            "Documentation",
            "Repository",
            "Issues"
        ]
        for url_name in required_urls:
            if url_name not in pyproject:
                self.warnings.append(
                    f"pyproject.toml missing [project.urls] entry: {url_name}"
                )

    def run_all_checks(self):
        """Run all validation checks."""
        print("🔍 Running documentation validation...")
        print()

        self.check_installation_consistency()
        self.check_bad_paths()
        self.check_correct_paths()
        self.check_pyproject_metadata()

        # Report results
        if self.errors:
            print("❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ All documentation validation checks passed!")
            return 0
        elif self.errors:
            print(f"❌ Found {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
            print("Fix errors before release!")
            return 1
        else:
            print(f"⚠️  Found {len(self.warnings)} warning(s) (no blocking errors)")
            return 0

if __name__ == "__main__":
    validator = DocValidator()
    sys.exit(validator.run_all_checks())
```

---

## 🤖 Claude Code Integration

### Slash Command: /dev:validate-docs

**Location:** `.claude/commands/dev/validate-docs.md`

```markdown
---
name: validate-docs
description: Validate documentation alignment across PyPI, GitHub, ReadTheDocs
---

# Documentation Validation Command

Validates that all critical documentation files are aligned and consistent.

## What This Checks

1. **Installation Instructions** - README.md, docs/index.rst, docs/installation.rst
2. **File Paths** - Detects incorrect paths in examples
3. **Import Statements** - Verifies circuit pattern imports are correct
4. **PyPI Metadata** - Checks pyproject.toml configuration
5. **Code Examples** - Validates example code syntax

## Usage

```bash
/dev:validate-docs
```

## Implementation

Runs the automated validator:
```bash
python tools/documentation/validate_docs.py
```

Returns:
- Exit 0: All checks passed ✅
- Exit 1: Errors found, fix before release ❌
```

### Integration with /dev:release-pypi

Add to `.claude/commands/dev/release-pypi.md` at line ~193 (before "Core Functionality Test"):

```bash
# Documentation validation (CRITICAL: prevents broken docs on PyPI)
echo "📚 Validating documentation alignment..."
python tools/documentation/validate_docs.py || {
    echo "❌ Documentation validation failed!"
    echo "Run: /dev:validate-docs to see errors"
    echo "Run: python tools/documentation/validate_docs.py for details"
    exit 1
}
echo "✅ Documentation validation passed"
```

---

## 📝 Common Documentation Fixes

### Fix 1: Incorrect Path After cs-new-project

**Bad:**
```bash
cs-new-project my_first_board
cd my_first_board/circuit-synth
uv run python example_project/circuit-synth/main.py  # ❌ WRONG
```

**Good:**
```bash
cs-new-project my_first_board
cd my_first_board
uv run python main.py  # ✅ CORRECT
```

### Fix 2: Inconsistent Installation Instructions

**Bad:**
```markdown
## Installation

```bash
pip install circuit-synth
```

(elsewhere in same doc)

```bash
uv add circuit-synth
```
```

**Good:**
```markdown
## Installation

Install using your preferred package manager:

```bash
# Recommended: uv (faster, better dependency resolution)
uv add circuit-synth

# Alternative: pip
pip install circuit-synth
```
```

### Fix 3: Circuit Pattern Import Statements

**Bad:**
```python
from buck_converter import buck_converter  # ❌ Where is this from?
```

**Good - Option A (if in installed package):**
```python
from circuit_synth.circuit_patterns.buck_converter import buck_converter
```

**Good - Option B (if in user project created with cs-new-project):**
```python
# In projects created with cs-new-project, patterns are copied to your project
from buck_converter import buck_converter  # Works because file is in project
```

---

## 🔄 Documentation Update Workflow

### When Making Code Changes:

1. **Update README.md first** - This is the source of truth
2. **Run validation:** `python tools/documentation/validate_docs.py`
3. **Update docs/index.rst** if Quick Start changed
4. **Update docs/installation.rst** if installation changed
5. **Update docs/quickstart.rst** if workflow changed
6. **Run validation again:** Ensure alignment
7. **Test examples:** Actually run the code you documented

### When Preparing a Release:

```bash
# 1. Validate docs
python tools/documentation/validate_docs.py

# 2. Test README examples in fresh environment
python -m venv test_docs
source test_docs/bin/activate
pip install circuit-synth
# Follow README "First Time User" section exactly
deactivate
rm -rf test_docs

# 3. Build and check ReadTheDocs locally
cd docs
make clean html
# Check docs/_build/html/index.html

# 4. Verify PyPI rendering
pip install twine
python -m build
twine check dist/*

# 5. Only then proceed with release
/dev:release-pypi VERSION
```

---

## 🚨 Red Flags - Signs of Documentation Drift

Watch for these indicators that docs are out of sync:

1. **User issues** mentioning "the docs say X but it doesn't work"
2. **Multiple installation sections** with different commands
3. **Code examples that don't run** as written
4. **Import errors** when following documentation
5. **Path errors** (file not found) when following Quick Start
6. **Version mismatches** between README and pyproject.toml

---

## 📚 Documentation Sources Reference

### What Lives Where

| Content Type | Location | Audience | Update Frequency |
|-------------|----------|----------|------------------|
| Quick Start | README.md + docs/quickstart.rst | New users | Every feature |
| Installation | README.md + docs/installation.rst | New users | When install changes |
| API Reference | docs/api.rst (auto-generated) | Developers | Auto from code |
| Architecture | docs/ARCHITECTURE.md | Contributors | When design changes |
| Features | README.md (BOM, PDF, Gerber sections) | Users evaluating | When features added |
| Examples | README.md + docs/examples.rst | Learning users | When API changes |
| Contributing | docs/CONTRIBUTING.md | Contributors | Rarely |
| Release Notes | GitHub Releases (auto-generated) | All users | Every release |

### Documentation NOT in Git

- **PyPI Page:** Auto-generated from README.md + pyproject.toml
- **ReadTheDocs:** Auto-built from docs/ on every commit to main
- **GitHub Releases:** Created by /dev:release-pypi command

---

## 🎓 For Claude Code: How to Fix Documentation Issues

When you encounter documentation alignment issues:

### Step 1: Identify the Scope

```bash
# Run validation to see all issues
python tools/documentation/validate_docs.py
```

### Step 2: Fix in Order of Priority

1. **README.md** - Fix first (source of truth)
2. **docs/index.rst** - Update to match README
3. **docs/installation.rst** - Sync installation instructions
4. **docs/quickstart.rst** - Sync workflow examples
5. **pyproject.toml** - Only if metadata wrong

### Step 3: Validate Fixes

```bash
# Re-run validation
python tools/documentation/validate_docs.py

# Test examples actually work
cd /tmp
python -m venv test_env
source test_env/bin/activate
pip install circuit-synth
# Run the exact commands from README
```

### Step 4: Update This Guide

If you discover a new type of documentation error:

1. Add it to the "Common Documentation Fixes" section
2. Add a check to `validate_docs.py`
3. Update the validation checklist

This guide should grow smarter with every documentation fix!

---

## ✅ Checklist: Before Every Release

- [ ] Run `python tools/documentation/validate_docs.py` - No errors
- [ ] Test README "First Time User" section in fresh venv - Works
- [ ] Check PyPI rendering with `twine check dist/*` - Valid
- [ ] Build ReadTheDocs locally: `cd docs && make clean html` - Builds
- [ ] Verify installation commands are consistent - pip AND uv shown
- [ ] Check all file paths in examples - No nonexistent paths
- [ ] Verify import statements - All imports work
- [ ] Compare README.md vs docs/index.rst - Aligned

---

**Remember:** Documentation is code. It should be tested, validated, and maintained with the same rigor as the Python code itself.

**Principle:** If documentation and code disagree, documentation is wrong (users see broken examples, lose trust).

**Goal:** Zero documentation bugs on PyPI/GitHub/ReadTheDocs. Every example works as written.
