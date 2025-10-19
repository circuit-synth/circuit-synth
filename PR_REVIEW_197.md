# PR #197: Refactor - Use kicad-sch-api geometry module

**Branch:** `refactor/use-kicad-sch-api-geometry`
**Target:** `main`
**Reviewer:** Claude Code
**Review Date:** 2025-10-19
**Commit:** `2404004` (single commit)

---

## Executive Summary

### Recommendation: ❌ **DO NOT MERGE** - Blocking Dependency Issue

This PR refactors geometry calculations by migrating `SymbolBoundingBoxCalculator` from circuit-synth to kicad-sch-api. While the architectural direction is sound, **the PR has a critical blocking issue that prevents it from being merged**.

### Critical Blocking Issue

**kicad-sch-api v0.3.3 is not published to PyPI**

- PR requires: `kicad-sch-api >= 0.3.3` (contains geometry module)
- Latest PyPI version: `0.3.2` (does NOT contain geometry module)
- Impact: **Anyone installing circuit-synth will get import errors**

```python
# This import will fail for users installing from PyPI:
from kicad_sch_api.geometry import SymbolBoundingBoxCalculator
# ModuleNotFoundError: No module named 'kicad_sch_api.geometry'
```

### Required Actions Before Merge

1. **Publish kicad-sch-api v0.3.3 to PyPI** (contains geometry module from PR #7)
2. **Verify installation** from PyPI works with the new dependency
3. **Run full test suite** after installing from PyPI (not from submodule)

---

## Detailed Analysis

### Changes Overview

| Metric | Value |
|--------|-------|
| Files Changed | 5 |
| Lines Added | 7 |
| Lines Deleted | 366 |
| Net Change | -359 lines |

**Core Changes:**
1. Delete `src/circuit_synth/kicad/sch_gen/symbol_geometry.py` (358 lines)
2. Update imports in `main_generator.py` (3 lines)
3. Update imports in `schematic_writer.py` (6 lines)
4. Update `pyproject.toml` dependency: `kicad-sch-api >= 0.3.2` → `>= 0.3.3`
5. Update `submodules/kicad-sch-api` pointer: `298f293` → `e4fee62`

### Architectural Assessment

#### ✅ Strengths

1. **Code Deduplication**: Eliminates 358 lines of duplicated geometry logic
2. **Proper Separation of Concerns**: Geometry calculations belong in kicad-sch-api
3. **Clean Refactor**: Simple import changes, no logic modifications
4. **Maintains Functionality**: Same `SymbolBoundingBoxCalculator` class, just moved

#### ⚠️ Concerns

1. **Dependency Management**
   - **Critical**: kicad-sch-api v0.3.3 not published to PyPI
   - Creates hard dependency on unpublished package version
   - Breaks installation from PyPI

2. **Submodule vs. Package Confusion**
   - Submodule points to unreleased commit `e4fee62`
   - Package dependency requires v0.3.3 (doesn't exist on PyPI)
   - Development works (using submodule), production breaks (using PyPI)

3. **Import Path Change**
   - Old: `from .symbol_geometry import SymbolBoundingBoxCalculator`
   - New: `from kicad_sch_api.geometry import SymbolBoundingBoxCalculator`
   - Works if kicad-sch-api installed in editable mode or from source
   - **Fails if installed from PyPI v0.3.2**

### Dependency Chain Analysis

```
circuit-synth (this PR)
  └─ requires kicad-sch-api >= 0.3.3
       └─ kicad-sch-api v0.3.3
            └─ includes geometry module (PR #7, commit e4fee62)
                 └─ SymbolBoundingBoxCalculator
```

**Current State:**
- ✅ kicad-sch-api submodule: commit `e4fee62` (has geometry module)
- ✅ kicad-sch-api repository: v0.3.3 tagged and merged
- ❌ kicad-sch-api PyPI: v0.3.2 (missing geometry module)

**What Happens When Users Install:**

```bash
# User installs circuit-synth from PyPI
pip install circuit-synth

# pip resolves dependencies:
# - Finds pyproject.toml requires kicad-sch-api >= 0.3.3
# - Latest PyPI version is 0.3.2
# - ERROR: No matching distribution found for kicad-sch-api>=0.3.3
```

OR (if dependency constraint is relaxed):

```bash
# If kicad-sch-api 0.3.2 is installed (doesn't meet >=0.3.3):
pip install circuit-synth

# circuit-synth loads:
from kicad_sch_api.geometry import SymbolBoundingBoxCalculator
# ERROR: ModuleNotFoundError: No module named 'kicad_sch_api.geometry'
```

---

## Code Quality Review

### Import Changes

**main_generator.py** (Line 62):
```python
# Old:
from .symbol_geometry import SymbolBoundingBoxCalculator

# New:
from kicad_sch_api.geometry import SymbolBoundingBoxCalculator
```

**schematic_writer.py** (Lines 693, 1392, 1541):
```python
# Old:
from .symbol_geometry import SymbolBoundingBoxCalculator

# New:
from kicad_sch_api.geometry import SymbolBoundingBoxCalculator
```

✅ **Analysis:** Clean import changes, no logic modifications

### Deleted Code Review

**symbol_geometry.py** (358 lines deleted)
- `SymbolBoundingBoxCalculator` class with all methods
- Font metrics constants
- Bounding box calculation logic

✅ **Analysis:** Code is NOT lost - migrated to kicad-sch-api PR #7

### Dependency Update

**pyproject.toml**:
```toml
# Old:
"kicad-sch-api>=0.3.2",

# New:
"kicad-sch-api>=0.3.3",  # (>= 0.3.3 for geometry module)
```

❌ **Analysis:** Requires unpublished version

### Submodule Update

```diff
-Subproject commit 298f2931756cd5a4d59bc344cbdbb87752255d97
+Subproject commit e4fee62cd396515e1f60a3b7d4225aedb0f8f0a9
```

✅ **Analysis:** Points to correct commit with geometry module

---

## Testing Assessment

### Test Status: ⚠️ **Cannot Verify**

**Why tests cannot be verified:**
1. kicad-sch-api v0.3.3 not installed in system
2. Import errors prevent running test suite
3. Need to test with PyPI installation, not submodule

**Expected Test Results After Publishing v0.3.3:**
- All existing tests should pass (no logic changes)
- Import tests should verify geometry module import
- Bounding box calculations should remain identical

**Manual Verification Needed:**
```bash
# After v0.3.3 is published to PyPI:
pip install kicad-sch-api==0.3.3
python -c "from kicad_sch_api.geometry import SymbolBoundingBoxCalculator; print('OK')"
pytest tests/ -v
```

---

## Breaking Changes Assessment

### For End Users: ⚠️ **Breaking Until v0.3.3 Published**

**Impact:** Cannot install circuit-synth from PyPI until kicad-sch-api v0.3.3 is published

**Workaround (for developers):**
```bash
# Install kicad-sch-api from source:
cd submodules/kicad-sch-api
pip install -e .

# Then install circuit-synth:
cd ../..
pip install -e .
```

### For Developers: ✅ **No Breaking Changes**

- Import path changes are internal
- Public API unchanged
- Geometry calculations identical

---

## Risk Assessment

| Risk Category | Level | Mitigation |
|---------------|-------|------------|
| Dependency Availability | 🔴 **CRITICAL** | Publish kicad-sch-api v0.3.3 to PyPI |
| Installation Failures | 🔴 **HIGH** | Test installation from PyPI after publish |
| Runtime Import Errors | 🔴 **HIGH** | Verify imports work with PyPI version |
| Logic Changes | 🟢 **LOW** | No logic changes, only imports |
| Performance Impact | 🟢 **NONE** | Same code, different location |
| Backwards Compatibility | 🟡 **MEDIUM** | Internal refactor, but dependency change |

---

## Recommendations

### Immediate Actions Required

1. **❌ DO NOT MERGE** until kicad-sch-api v0.3.3 is published

2. **Publish kicad-sch-api v0.3.3 to PyPI**
   ```bash
   cd submodules/kicad-sch-api
   git checkout e4fee62  # Verify on correct commit
   python -m build
   python -m twine upload dist/*
   ```

3. **Verify Installation**
   ```bash
   # In clean virtual environment:
   python -m venv test_env
   source test_env/bin/activate
   pip install kicad-sch-api==0.3.3
   python -c "from kicad_sch_api.geometry import SymbolBoundingBoxCalculator"
   ```

4. **Run Full Test Suite**
   ```bash
   # After successful installation:
   pytest tests/ -v --tb=short
   ```

5. **Update PR Description** with installation requirements and dependency notes

### Optional Improvements

1. **Add Import Test**
   ```python
   # tests/unit/test_imports.py
   def test_geometry_import():
       """Verify kicad-sch-api geometry module import works"""
       from kicad_sch_api.geometry import SymbolBoundingBoxCalculator
       assert SymbolBoundingBoxCalculator is not None
   ```

2. **Add Dependency Check**
   ```python
   # src/circuit_synth/__init__.py
   try:
       from kicad_sch_api.geometry import SymbolBoundingBoxCalculator
   except ImportError as e:
       raise ImportError(
           "kicad-sch-api >= 0.3.3 required. "
           "Install with: pip install --upgrade kicad-sch-api"
       ) from e
   ```

3. **Documentation Update**
   - Update README with minimum kicad-sch-api version
   - Document dependency on geometry module
   - Add installation troubleshooting section

---

## Merge Checklist

Before merging this PR, verify:

- [ ] kicad-sch-api v0.3.3 is published to PyPI
- [ ] Installation from PyPI works (`pip install kicad-sch-api==0.3.3`)
- [ ] Geometry module imports successfully from installed package
- [ ] All tests pass with PyPI-installed dependency
- [ ] CI/CD builds pass
- [ ] Documentation updated with new dependency requirements
- [ ] CHANGELOG.md updated with dependency change
- [ ] Version number bumped appropriately (minor version recommended)

---

## Related Information

### Related PRs
- **circuit-synth #191**: Unified bounding box implementation
- **kicad-sch-api #7**: Add geometry module (commit `e4fee62`)

### Related Issues
- **circuit-synth #6**: Architectural separation of geometry calculations

### Dependency Information
- **kicad-sch-api repository**: https://github.com/circuit-synth/kicad-sch-api
- **kicad-sch-api PyPI**: https://pypi.org/project/kicad-sch-api/
- **Current PyPI version**: 0.3.2
- **Required version**: 0.3.3 (unpublished)
- **Commit with geometry module**: `e4fee62cd396515e1f60a3b7d4225aedb0f8f0a9`

---

## Conclusion

This PR represents a **clean architectural refactoring** that improves code organization and eliminates duplication. The code changes are minimal, focused, and well-structured.

However, the PR **CANNOT BE MERGED** until the blocking dependency issue is resolved. The required kicad-sch-api v0.3.3 package must be published to PyPI before this PR can be safely merged.

Once kicad-sch-api v0.3.3 is published and installation is verified, this PR can be approved and merged with confidence.

### Estimated Timeline

1. **Publish kicad-sch-api v0.3.3**: 30 minutes
2. **Verify installation**: 15 minutes
3. **Run test suite**: 10 minutes
4. **Update documentation**: 15 minutes
5. **Ready to merge**: ~1 hour total

### Final Recommendation

**Status:** ❌ **BLOCKED - Waiting for kicad-sch-api v0.3.3 PyPI Release**

After dependency is published: ✅ **APPROVE and MERGE**

---

**Review completed by:** Claude Code (Anthropic)
**Review tool version:** Claude Sonnet 4.5
**Methodology:** Comprehensive branch analysis, dependency verification, risk assessment
