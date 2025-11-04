---
name: make-test
description: Wrap manual test into automated pytest test
---

# Make Test Command

**Purpose:** Convert validated manual tests into automated pytest tests, leveraging existing reference material.

## Usage
```bash
/dev:make-test <test-description-or-path>
```

## The Pattern

circuit-synth testing follows this workflow:
1. **Create manual test** - Document steps, create reference
2. **Validate manually** - Run through steps, verify correctness
3. **Wrap in pytest** - Automate the validated manual test
4. **Mark as verified** - Update MANUAL_TEST_CHECKLIST.md

**This command helps with step 3.**

## What This Does

1. **Review Manual Test**
   - Read manual test README.md
   - Understand test steps
   - Identify reference files
   - Check what's being validated

2. **Create pytest Structure**
   - Generate test_*.py file
   - Use existing reference files
   - Follow circuit-synth test patterns
   - Include comprehensive assertions

3. **Implement Test Logic**
   - Subprocess calls to run circuit generation
   - Load and compare against reference using kicad-sch-api
   - Assert expected behavior
   - Clean up generated files

4. **Verify Test Works**
   - Run the new test
   - Ensure it passes
   - Check coverage
   - Add to test suite

## Example: Manual Test → Automated Test

### Input: Manual Test

```bash
User: /dev:make-test tests/bidirectional/component_crud_root/03_sync_component_root_update_ref/

Agent: [Reads README.md]

Manual test steps:
1. Generate circuit (R1, R2, C1)
2. Change R1 reference to R100 in code
3. Regenerate
4. Verify R1 → R100, positions preserved

Reference files found:
- tests/reference/component-ref-update/circuit.kicad_sch
- comprehensive_root.py (test circuit)
```

### Output: Automated pytest

```python
#!/usr/bin/env python3
"""
Test 12: Update Component Reference (Rename) - Automated

Validates that renaming a component (R1 → R100) preserves ALL other
schematic elements using kicad-sch-api verification.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_12_update_component_ref(request):
    """Test renaming R1 → R100 while preserving R2, C1, power, and labels."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate initial circuit with R1
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Initial generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Load and verify initial state
        sch = Schematic.load(str(schematic_file))

        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(regular_components) == 3

        r1_before = next(c for c in regular_components if c.reference == "R1")
        r2_before = next(c for c in regular_components if c.reference == "R2")
        c1_before = next(c for c in regular_components if c.reference == "C1")

        # Store properties for preservation check
        r1_pos_before = r1_before.position
        r1_value_before = r1_before.value

        # STEP 2: Modify circuit to rename R1 → R100
        original_code = circuit_file.read_text()
        modified_code = original_code.replace('ref="R1"', 'ref="R100"')
        circuit_file.write_text(modified_code)

        # STEP 3: Regenerate circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Regeneration failed: {result.stderr}"

        # STEP 4: Load and verify
        sch_after = Schematic.load(str(schematic_file))

        regular_components_after = [c for c in sch_after.components if not c.reference.startswith("#PWR")]
        assert len(regular_components_after) == 3, "Component count changed"

        # Verify R1 renamed to R100
        refs = {c.reference for c in regular_components_after}
        assert "R100" in refs, "R100 not found after rename"
        assert "R1" not in refs, "R1 still exists after rename"

        r100 = next(c for c in regular_components_after if c.reference == "R100")

        # Verify R100 properties preserved
        assert r100.value == r1_value_before, "R100 value changed"
        assert r100.position.x == r1_pos_before.x, "R100 X position changed"
        assert r100.position.y == r1_pos_before.y, "R100 Y position changed"

        print("\n✅ Test 12 PASSED: Component rename preserved all properties")

    finally:
        if 'original_code' in locals():
            circuit_file.write_text(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
```

### Agent continues:

```bash
Created: tests/bidirectional/component_crud_root/03_sync_component_root_update_ref/test_update_ref.py

Running test to verify...
$ pytest test_update_ref.py -v

============================= test session starts ==============================
tests/.../test_update_ref.py::test_12_update_component_ref PASSED       [100%]

============================== 1 passed in 3.20s ===============================

✅ Test created and passing!

Would you like me to:
1. Add more test cases (e.g., test_12b_with_moved_components)?
2. Update MANUAL_TEST_CHECKLIST.md?
3. Create PR with this test?
```

## Test Patterns We Follow

### 1. Subprocess Circuit Generation

```python
# Generate circuit using subprocess (not import)
result = subprocess.run(
    ["uv", "run", str(circuit_file)],
    cwd=test_dir,
    capture_output=True,
    text=True,
    timeout=30
)
assert result.returncode == 0, f"Generation failed: {result.stderr}"
```

**Why:** Ensures clean process, no side effects

### 2. kicad-sch-api for Validation

```python
from kicad_sch_api import Schematic

# Load schematic
sch = Schematic.load(str(schematic_file))

# Validate components
regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
assert len(regular_components) == 3

# Check specific component
r1 = next(c for c in regular_components if c.reference == "R1")
assert r1.value == "10k"
assert r1.position.x == pytest.approx(30.48, abs=0.1)
```

**Why:** Programmatic validation, no manual inspection

### 3. Cleanup and Restoration

```python
try:
    # Test logic here
    original_code = circuit_file.read_text()
    # ... modify code ...

finally:
    # Always restore original
    if 'original_code' in locals():
        circuit_file.write_text(original_code)

    # Optionally clean up outputs
    if cleanup and output_dir.exists():
        shutil.rmtree(output_dir)
```

**Why:** Tests don't leave artifacts, can run repeatedly

### 4. Comprehensive Assertions

```python
# Verify EVERYTHING that should be preserved
assert r1_after.value == r1_before.value, "Value changed"
assert r1_after.position.x == r1_before.position.x, "X position changed"
assert r1_after.position.y == r1_before.position.y, "Y position changed"
assert r1_after.rotation == r1_before.rotation, "Rotation changed"
assert r1_after.footprint == r1_before.footprint, "Footprint changed"

# Verify power symbols preserved
power_symbols = [c for c in sch_after.components if c.reference.startswith("#PWR")]
assert len(power_symbols) >= 2, "Power symbols missing"
```

**Why:** Catch unintended changes

## Test Organization

```
tests/bidirectional/component_crud_root/
├── 01_sync_component_root_create/
│   ├── README.md (manual test steps)
│   ├── comprehensive_root.py (test circuit)
│   ├── test_create_component.py (automated)
│   └── reference/ (if needed)
├── 02_sync_component_root_update_value/
│   ├── README.md
│   ├── comprehensive_root.py
│   └── test_update_value.py
└── 03_sync_component_root_update_ref/
    ├── README.md
    ├── comprehensive_root.py
    ├── test_update_ref.py
    └── test_update_ref_advanced.py (if multiple tests)
```

## Integration with Reference Material

If reference files exist (from `/dev:test-ref`):

```python
# Load reference schematic
ref_sch = Schematic.load("tests/reference/position-preservation/circuit.kicad_sch")

# Get expected positions
ref_r1 = next(c for c in ref_sch.components if c.reference == "R1")
expected_x = ref_r1.position.x
expected_y = ref_r1.position.y

# Validate against reference
assert r1.position.x == pytest.approx(expected_x, abs=0.1)
assert r1.position.y == pytest.approx(expected_y, abs=0.1)
```

## Common Test Patterns

### Pattern 1: Property Change Test
```python
# Generate → Modify property → Regenerate → Verify
```

### Pattern 2: Position Preservation Test
```python
# Generate → Move in KiCad → Change in Python → Regenerate → Verify positions preserved
```

### Pattern 3: Deletion Test
```python
# Generate → Delete in Python → Regenerate → Verify component gone, others preserved
```

### Pattern 4: Regression Test
```python
# Reproduce bug → Verify bug fixed → Ensure doesn't regress
```

## Options

- `--test-only` - Create test file, don't run it yet
- `--with-reference` - Use existing reference files from tests/reference/
- `--coverage` - Include coverage analysis in test

## Success Criteria

Test is "done" when:
- [ ] Test file created following patterns
- [ ] Test runs and passes
- [ ] All assertions comprehensive
- [ ] Cleanup logic works
- [ ] Test added to suite (conftest.py if needed)
- [ ] MANUAL_TEST_CHECKLIST.md updated (mark as verified)
- [ ] README.md updated with automated test info

## Tips

1. **Start with simplest case** - One scenario per test function
2. **Add test variants** - test_12a, test_12b for related scenarios
3. **Use reference files** - Don't hardcode expected values
4. **Test preservation** - Not just the change, but what didn't change
5. **Clean up always** - Use try/finally for restoration

---

**This command transforms validated manual tests into robust automated regression tests following circuit-synth testing patterns.**
