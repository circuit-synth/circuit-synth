# Solution Architecture: Issue #406

**Issue:** Hierarchical Sheet Synchronization Failure
**Investigation Report:** INVESTIGATION_REPORT_ISSUE_406.md
**Date:** 2025-10-29

---

## Branch Strategy

### Repository 1: circuit-synth (PRIMARY)

**Branch Name:** `fix/issue-406-hierarchical-synchronizer`

**Base Branch:** `main`

**Purpose:** Fix the three bugs in hierarchical_synchronizer.py that cause crashes during regeneration

**Changes:**
- `src/circuit_synth/kicad/schematic/hierarchical_synchronizer.py` (MODIFIED)
- `tests/unit/test_hierarchical_synchronizer.py` (NEW - optional)
- `tests/integration/test_hierarchical_regeneration.py` (NEW - optional)

**Estimated LOC:** ~100 lines changed, ~200 lines added (with tests)

---

### Repository 2: kicad-sch-api (OPTIONAL)

**Branch Name:** `feat/public-sheets-property`

**Base Branch:** `main`

**Purpose:** Add public `sheets` property to Schematic class for cleaner API

**Changes:**
- `src/kicad_sch_api/core/schematic.py` (MODIFIED - add property)
- `tests/test_schematic.py` (MODIFIED - add tests)
- `docs/api.md` (MODIFIED - document property)

**Estimated LOC:** ~30 lines

**Priority:** LOW - Not required for fix, nice-to-have enhancement

**Timeline:** After circuit-synth fix is merged and tested

---

## Detailed Implementation Plan

### Phase 1: circuit-synth Fix (REQUIRED)

#### File: `src/circuit_synth/kicad/schematic/hierarchical_synchronizer.py`

**Changes Required:**

##### Change 1: Fix Line 110 - Use sheet_manager API

```python
# BEFORE (lines 108-161):
# Find hierarchical sheet instances
# Look for sheet elements in the schematic
if hasattr(schematic, "sheets") and schematic.sheets:  # ❌ ALWAYS FALSE
    logger.debug(f"Schematic has {len(schematic.sheets)} sheets")
    for sheet_elem in schematic.sheets:
        # ... (50 lines of unreachable code)

# AFTER:
# Find hierarchical sheet instances using sheet_manager API
if hasattr(schematic, '_sheet_manager'):
    logger.debug("Using sheet_manager to find hierarchical sheets")
    hierarchy = schematic._sheet_manager.get_sheet_hierarchy()

    if 'root' in hierarchy and 'children' in hierarchy['root']:
        children = hierarchy['root']['children']
        logger.debug(f"Found {len(children)} child sheets in hierarchy")

        for sheet_data in children:
            # sheet_data is a dict with keys: 'name', 'filename', 'uuid', etc.
            sheet_name = sheet_data.get('name')
            sheet_file = sheet_data.get('filename')

            logger.debug(f"Processing sheet: {sheet_name} -> {sheet_file}")

            if sheet_file:
                logger.info(f"Found sheet: {sheet_name} -> {sheet_file}")
                # Resolve the file path
                child_path = self.project_dir / sheet_file

                if child_path.exists():
                    # Create child sheet and load recursively
                    child = HierarchicalSheet(
                        sheet_name or sheet_file, child_path, sheet
                    )
                    sheet.add_child(child)
                    self._load_sheet_hierarchy(child)
                else:
                    logger.warning(
                        f"Hierarchical sheet file not found: {child_path}"
                    )
    else:
        logger.debug("No child sheets found in hierarchy")
```

**Reasoning:**
- Uses the public `get_sheet_hierarchy()` method
- Returns proper hierarchical structure
- sheet_data is a dict (correct type)
- Cleaner, more maintainable code

##### Change 2: Fix Lines 133-138 - Handle Dict Properties

```python
# BEFORE (lines 132-139):
# From properties
if hasattr(sheet_elem, "properties"):
    for prop in sheet_elem.properties:         # ❌ Iterates dict keys
        if prop.name == "Sheetfile":           # ❌ CRASH
            sheet_file = prop.value
        elif prop.name == "Sheetname":
            sheet_name = prop.value

# AFTER - REMOVE THIS CODE (unreachable after Change 1)
# This entire block (lines 120-140) becomes unreachable
# Can be deleted after Change 1 is working
```

**Reasoning:**
- This code is inside the `if hasattr(schematic, "sheets")` block
- After Change 1, this block is replaced entirely
- No need to fix, just remove

##### Change 3: Fix Lines 170-175 - Fallback Property Handling

```python
# BEFORE (lines 163-194):
# Alternative: Look in components for sheet instances
if len(sheet.children) == 0:
    for comp in schematic.components:
        # Check if this is a sheet (has Sheetfile property)
        sheet_file = None
        sheet_name = None

        if hasattr(comp, "properties"):
            for prop in comp.properties:           # ❌ prop is string key
                if prop.name == "Sheetfile":       # ❌ CRASH
                    sheet_file = prop.value
                elif prop.name == "Sheetname":
                    sheet_name = prop.value

# AFTER:
# Alternative: Look in components for sheet instances (fallback)
if len(sheet.children) == 0:
    logger.debug("No sheets found via sheet_manager, trying component fallback")
    for comp in schematic.components:
        # Check if this is a sheet (has Sheetfile property)
        sheet_file = None
        sheet_name = None

        if hasattr(comp, "properties") and isinstance(comp.properties, dict):
            # Properties is a dict in kicad-sch-api v0.4.3+
            sheet_file = comp.properties.get("Sheetfile")
            sheet_name = comp.properties.get("Sheetname")

            if sheet_file:
                logger.debug(
                    f"Found sheet in component properties: {sheet_name} -> {sheet_file}"
                )

        if sheet_file:
            # ... rest of code unchanged (lines 177-194)
```

**Reasoning:**
- Defensive coding - keep fallback path
- Handles dict properties correctly
- Adds logging for debugging
- No crash on property access

##### Change 4: Add Defensive Version Checking (NEW)

```python
# ADD at top of _load_sheet_hierarchy() method (after line 93):

def _load_sheet_hierarchy(self, sheet: HierarchicalSheet):
    """Recursively load sheet hierarchy."""
    logger.debug(f"Loading sheet: {sheet.file_path}")

    try:
        # Parse the schematic using kicad-sch-api
        schematic = ksa.Schematic.load(str(sheet.file_path))
        sheet.schematic = schematic

        logger.debug(f"Parsed schematic has {len(schematic.components)} components")

        # ADD VERSION CHECK:
        # Check kicad-sch-api version for compatibility
        if hasattr(ksa, '__version__'):
            version = ksa.__version__
            logger.debug(f"Using kicad-sch-api version: {version}")

            # Warn if version is very old
            try:
                from packaging import version as pkg_version
                if pkg_version.parse(version) < pkg_version.parse('0.4.0'):
                    logger.warning(
                        f"kicad-sch-api {version} is older than 0.4.0. "
                        "Hierarchical sheet detection may not work correctly."
                    )
            except:
                pass  # Ignore if packaging not available

        # ... continue with existing logic
```

**Reasoning:**
- Helps diagnose issues with old kicad-sch-api versions
- Non-breaking - just adds warning
- Uses existing `packaging` dependency

---

### Testing Changes

#### Manual Testing Script

```bash
#!/bin/bash
# test_hierarchical_regeneration.sh

set -e  # Exit on error

echo "============================================================"
echo "Testing Hierarchical Regeneration (Issue #406)"
echo "============================================================"

cd tests/bidirectional/22_add_subcircuit_sheet

# Test 1: Clean generation
echo -e "\n[Test 1] Clean generation..."
rm -rf hierarchical_circuit
uv run hierarchical_circuit.py

# Verify files exist
if [ ! -f "hierarchical_circuit/hierarchical_circuit.kicad_sch" ]; then
    echo "❌ FAIL: Root schematic not generated"
    exit 1
fi

if [ ! -f "hierarchical_circuit/ChildSheet.kicad_sch" ]; then
    echo "❌ FAIL: Child schematic not generated"
    exit 1
fi

echo "✅ PASS: Both schematics generated"

# Test 2: Regeneration (THE BUG FIX)
echo -e "\n[Test 2] Regeneration (testing synchronizer)..."
uv run hierarchical_circuit.py 2>&1 | tee regeneration.log

# Check for crash
if grep -q "'str' object has no attribute 'name'" regeneration.log; then
    echo "❌ FAIL: Synchronizer still crashing"
    exit 1
fi

echo "✅ PASS: No crash during regeneration"

# Verify files still exist
if [ ! -f "hierarchical_circuit/ChildSheet.kicad_sch" ]; then
    echo "❌ FAIL: Child schematic disappeared after regeneration"
    exit 1
fi

echo "✅ PASS: Hierarchical structure preserved"

# Test 3: KiCad validation (requires KiCad CLI)
if command -v kicad-cli &> /dev/null; then
    echo -e "\n[Test 3] KiCad validation..."
    kicad-cli sch export pdf hierarchical_circuit/hierarchical_circuit.kicad_pro \
        --output hierarchical_circuit/test_export.pdf

    if [ -f "hierarchical_circuit/test_export.pdf" ]; then
        echo "✅ PASS: KiCad can load and export project"
    else
        echo "⚠️  WARN: PDF export failed, but schematic may be valid"
    fi
else
    echo -e "\n[Test 3] Skipped (kicad-cli not available)"
fi

echo -e "\n============================================================"
echo "All Tests Passed! ✅"
echo "============================================================"

# Cleanup
rm -f regeneration.log
```

#### Automated Test Addition

**File:** `tests/integration/test_hierarchical_regeneration.py` (NEW)

```python
"""Integration tests for hierarchical circuit regeneration."""

import shutil
from pathlib import Path
import subprocess


def test_hierarchical_regeneration_preserves_structure():
    """
    Test that regenerating a hierarchical circuit preserves child sheets.

    This is the regression test for issue #406.
    """
    test_dir = Path(__file__).parent.parent / "bidirectional" / "22_add_subcircuit_sheet"
    python_file = test_dir / "hierarchical_circuit.py"
    output_dir = test_dir / "hierarchical_circuit"

    # Clean state
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # First generation
    result = subprocess.run(
        ["uv", "run", "hierarchical_circuit.py"],
        cwd=test_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"First generation failed: {result.stderr}"
    assert (output_dir / "hierarchical_circuit.kicad_sch").exists()
    assert (output_dir / "ChildSheet.kicad_sch").exists(), "Child sheet not generated"

    # Second generation (THE BUG)
    result = subprocess.run(
        ["uv", "run", "hierarchical_circuit.py"],
        cwd=test_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"Regeneration failed: {result.stderr}"
    assert "'str' object has no attribute 'name'" not in result.stderr, \
        "Synchronizer crashed with attribute error"

    # Verify hierarchy preserved
    assert (output_dir / "ChildSheet.kicad_sch").exists(), \
        "Child sheet disappeared after regeneration (BUG #406)"

    # Verify no error logs
    assert "ERROR" not in result.stderr or "Failed to load sheet" not in result.stderr, \
        "Synchronizer logged errors during hierarchy loading"

    # Cleanup
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_hierarchical_regeneration_multiple_times():
    """Test that multiple regenerations are stable."""
    test_dir = Path(__file__).parent.parent / "bidirectional" / "22_add_subcircuit_sheet"
    output_dir = test_dir / "hierarchical_circuit"

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Generate 5 times
    for i in range(5):
        result = subprocess.run(
            ["uv", "run", "hierarchical_circuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Generation {i+1} failed"
        assert (output_dir / "ChildSheet.kicad_sch").exists(), \
            f"Child sheet missing after generation {i+1}"

    # Cleanup
    if output_dir.exists():
        shutil.rmtree(output_dir)
```

---

### Phase 2: kicad-sch-api Enhancement (OPTIONAL)

#### File: `src/kicad_sch_api/core/schematic.py`

**Add Property:**

```python
@property
def sheets(self) -> list[dict]:
    """
    Get list of hierarchical sheets in this schematic.

    Returns a list of sheet dictionaries containing hierarchical sheet
    information. Each sheet dictionary contains:

    - name (str): Sheet name/title
    - filename (str): Referenced .kicad_sch file
    - uuid (str): Unique identifier for the sheet
    - position (dict): Top-left corner position {x, y}
    - size (dict): Sheet dimensions {width, height}
    - pins (list): List of hierarchical pins on the sheet
    - project_name (str): Project name for this sheet
    - page_number (str): Page number in schematic hierarchy

    Returns:
        List of sheet dictionaries. Empty list if no hierarchical sheets.

    Example:
        >>> sch = Schematic.load("my_circuit.kicad_sch")
        >>> for sheet in sch.sheets:
        ...     print(f"{sheet['name']} -> {sheet['filename']}")
        SubCircuit -> SubCircuit.kicad_sch

    See Also:
        - `_sheet_manager.get_sheet_hierarchy()`: Full hierarchical structure
        - `_sheet_manager.get_sheet_by_name()`: Find specific sheet
        - `_sheet_manager.get_sheet_statistics()`: Sheet count and stats

    Note:
        This is a convenience property that provides direct access to the
        internal sheet data. For more advanced sheet operations, use the
        `_sheet_manager` methods which provide additional functionality like
        hierarchical traversal and sheet modification.
    """
    return self._data.get('sheets', [])
```

**Update Tests:**

```python
def test_sheets_property():
    """Test the sheets property accessor."""
    sch = Schematic.create()

    # Initially no sheets
    assert sch.sheets == []
    assert isinstance(sch.sheets, list)

    # Add a sheet
    sch.add_sheet(
        name="TestSheet",
        filename="test.kicad_sch",
        position=(30, 40),
        size=(50, 40)
    )

    # Check sheets property
    assert len(sch.sheets) == 1
    assert sch.sheets[0]['name'] == "TestSheet"
    assert sch.sheets[0]['filename'] == "test.kicad_sch"
    assert 'uuid' in sch.sheets[0]

def test_sheets_property_with_hierarchical_schematic():
    """Test sheets property with real hierarchical schematic."""
    # Load a schematic with hierarchical sheets
    sch = Schematic.load("tests/fixtures/hierarchical_circuit.kicad_sch")

    # Should have child sheets
    assert len(sch.sheets) > 0

    # First sheet should have expected structure
    sheet = sch.sheets[0]
    assert 'name' in sheet
    assert 'filename' in sheet
    assert 'uuid' in sheet
    assert 'position' in sheet
    assert 'size' in sheet
```

**Benefits:**
- Consistent with other collection accessors (components, wires, labels)
- Cleaner API for users
- Better encapsulation (don't access `_data` directly)
- Self-documenting code

---

## Rollout Plan

### Step 1: Implement circuit-synth Fix
**Timeline:** 1 day
1. Create branch `fix/issue-406-hierarchical-synchronizer`
2. Implement Changes 1-4
3. Run manual test script
4. Run test suite
5. Commit and push

### Step 2: Testing & Validation
**Timeline:** 1 day
1. Manual testing by developer
2. Run full bidirectional test suite (tests 22-65)
3. Request Shane to test manually
4. Fix any issues found

### Step 3: Merge to Main
**Timeline:** 1 day
1. Create PR with investigation report linked
2. Code review
3. Merge to main
4. Tag release (patch version bump)

### Step 4: kicad-sch-api Enhancement (Optional)
**Timeline:** 3-5 days (async)
1. Create branch `feat/public-sheets-property`
2. Implement property + tests
3. Create PR to kicad-sch-api repo
4. Wait for review/merge
5. Update circuit-synth to use new property (optional)

---

## Risk Mitigation

### Risk 1: sheet_manager API Changes Between Versions
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Add version checking (Change 4)
- Test with both kicad-sch-api 0.4.3 and 0.4.4
- Add fallback to component scanning if sheet_manager fails

### Risk 2: Unexpected Sheet Data Format
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Defensive dict.get() usage
- Log sheet_data structure for debugging
- Handle missing keys gracefully

### Risk 3: Regression in Flat Projects
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Test flat projects (tests 01-21) don't use hierarchical synchronizer
- Run full test suite before merge
- Add integration test for flat project regeneration

### Risk 4: Breaking Change in Future kicad-sch-api
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Pin kicad-sch-api to >=0.4.3,<0.5.0 until tested
- Monitor kicad-sch-api releases
- Add version compatibility checks

---

## Success Metrics

### Functional Metrics
- [ ] Test 22 passes (automated)
- [ ] Manual workflow works: generate → modify → regenerate
- [ ] No crash on second generation
- [ ] Both .kicad_sch files preserved after regeneration
- [ ] Sheet symbol remains on root schematic

### Quality Metrics
- [ ] No regressions in tests 01-21 (flat projects)
- [ ] Sample of tests 22-65 pass (10+ hierarchical tests)
- [ ] Code coverage >80% for modified code
- [ ] No new linting errors

### Performance Metrics
- [ ] Regeneration time unchanged (< 5% increase)
- [ ] Memory usage unchanged
- [ ] No new warnings in logs

---

## Documentation Updates

### Code Comments
- Add docstrings explaining kicad-sch-api API usage
- Document expected data structures (dict format)
- Explain fallback logic

### User Documentation
- No changes needed (internal fix)
- No API changes

### Developer Documentation
- Update ARCHITECTURE.md with kicad-sch-api integration notes
- Document synchronizer architecture
- Add troubleshooting guide for hierarchical sheets

---

## Rollback Plan

If the fix causes issues:

1. **Immediate:** Revert commit from main
2. **Short-term:** Add feature flag to disable hierarchical synchronizer
3. **Long-term:** Fallback to regeneration without sync for hierarchical projects

**Feature Flag Implementation:**

```python
# In config or environment
ENABLE_HIERARCHICAL_SYNC = os.getenv('CIRCUIT_SYNTH_HIERARCHICAL_SYNC', 'true').lower() == 'true'

# In main_generator.py
if has_subcircuits and ENABLE_HIERARCHICAL_SYNC:
    synchronizer = HierarchicalSynchronizer(...)
else:
    logger.warning("Hierarchical sync disabled, using full regeneration")
    return self._generate_from_scratch()
```

---

## Conclusion

**This is a well-scoped, low-risk fix with clear implementation path.**

- **Single repo change** (circuit-synth)
- **One file modified** (hierarchical_synchronizer.py)
- **~100 lines changed**
- **Clear testing strategy**
- **Optional enhancement** in separate repo

**Confidence: HIGH**

Ready to proceed with implementation!

---

**Architecture Generated:** 2025-10-29
**Implementation Ready:** ✅ YES
**Estimated Effort:** 4-6 hours (critical path)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
