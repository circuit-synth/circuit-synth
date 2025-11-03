#!/usr/bin/env python3
"""
Automated test for Test 10: Add Component (Root Sheet)

Tests adding component in Python → synchronizing to KiCad schematic
while preserving all other elements.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_10_add_component(request):
    """Test adding R2 component while preserving R1, C1, power, and labels.

    Workflow:
    1. Start with R1, C1 only (R2 commented out)
    2. Generate KiCad → validate R1, C1 only
    3. Uncomment R2 in Python
    4. Regenerate KiCad → validate R1, R2, C1 present
    5. Verify R1, C1 unchanged (position, value, footprint)
    6. Verify power and labels preserved
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with R1, C1 only (R2 commented)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1, C1 only")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate R1 and C1 in schematic
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Filter out power symbols
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        component_refs = {c.reference for c in regular_components}

        assert len(regular_components) == 2, (
            f"Step 1: Expected 2 components (R1, C1), found {len(regular_components)}: {component_refs}"
        )
        assert component_refs == {"R1", "C1"}

        # Store initial state for comparison
        r1_before = next(c for c in regular_components if c.reference == "R1")
        c1_before = next(c for c in regular_components if c.reference == "C1")

        print(f"✅ Step 1: KiCad generated with R1, C1 only")
        print(f"   - R1: {r1_before.value}")
        print(f"   - C1: {c1_before.value}")

        # =====================================================================
        # STEP 2: Uncomment R2 and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Uncomment R2 and regenerate")
        print("="*70)

        # Uncomment R2 definition and connections
        modified_code = original_code.replace(
            '    # r2 = Component(',
            '    r2 = Component('
        )
        modified_code = modified_code.replace(
            '    #     symbol="Device:R",',
            '        symbol="Device:R",'
        )
        modified_code = modified_code.replace(
            '    #     ref="R2",',
            '        ref="R2",'
        )
        modified_code = modified_code.replace(
            '    #     value="4.7k",',
            '        value="4.7k",'
        )
        modified_code = modified_code.replace(
            '    #     footprint="Resistor_SMD:R_0603_1608Metric"',
            '        footprint="Resistor_SMD:R_0603_1608Metric"'
        )
        modified_code = modified_code.replace(
            '    # )',
            '    )'
        )
        # Uncomment R2 connections
        modified_code = modified_code.replace(
            '    # r2[1] += data',
            '    r2[1] += data'
        )
        modified_code = modified_code.replace(
            '    # r2[2] += gnd',
            '    r2[2] += gnd'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Regeneration with R2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate R1, R2, C1 in schematic
        sch = Schematic.load(str(schematic_file))
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        component_refs = {c.reference for c in regular_components}

        assert len(regular_components) == 3, (
            f"Step 2: Expected 3 components (R1, R2, C1), found {len(regular_components)}: {component_refs}"
        )
        assert component_refs == {"R1", "R2", "C1"}

        # Verify R1 preserved
        r1_after = next(c for c in regular_components if c.reference == "R1")
        assert r1_after.value == r1_before.value, "R1 value changed"
        assert r1_after.footprint == r1_before.footprint, "R1 footprint changed"
        assert r1_after.position == r1_before.position, "R1 position changed"

        # Verify C1 preserved
        c1_after = next(c for c in regular_components if c.reference == "C1")
        assert c1_after.value == c1_before.value, "C1 value changed"
        assert c1_after.footprint == c1_before.footprint, "C1 footprint changed"
        assert c1_after.position == c1_before.position, "C1 position changed"

        # Verify R2 added
        r2_after = next(c for c in regular_components if c.reference == "R2")
        assert r2_after.value == "4.7k"

        # =====================================================================
        # STEP 3: Verify schematic file format (raw file check for instance data)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Verify instance data (project name & hierarchical path)")
        print("="*70)

        # Read raw schematic file to verify project name and paths are correct
        with open(schematic_file, "r") as f:
            schematic_content = f.read()

        expected_project = sch.name  # Should match schematic name
        expected_path_prefix = f"/{sch.uuid}"  # Should include UUID

        print(f"   Expected project name: {expected_project}")
        print(f"   Expected path prefix: {expected_path_prefix}")

        # Extract R1's instance data from file (baseline)
        r1_instance_match = re.search(
            r'reference "R1".*?\(instances\s+\(project "([^"]+)".*?\(path "([^"]+)"',
            schematic_content,
            re.DOTALL
        )
        assert r1_instance_match, "Could not find R1 instance block in schematic file"
        r1_project = r1_instance_match.group(1)
        r1_path = r1_instance_match.group(2)

        # Extract R2's instance data from file (component added during sync)
        r2_instance_match = re.search(
            r'reference "R2".*?\(instances\s+\(project "([^"]+)".*?\(path "([^"]+)"',
            schematic_content,
            re.DOTALL
        )
        assert r2_instance_match, "Could not find R2 instance block in schematic file"
        r2_project = r2_instance_match.group(1)
        r2_path = r2_instance_match.group(2)

        # Extract C1's instance data from file (ensure nothing broken)
        c1_instance_match = re.search(
            r'reference "C1".*?\(instances\s+\(project "([^"]+)".*?\(path "([^"]+)"',
            schematic_content,
            re.DOTALL
        )
        assert c1_instance_match, "Could not find C1 instance block in schematic file"
        c1_project = c1_instance_match.group(1)
        c1_path = c1_instance_match.group(2)

        # Verify R1 instance data (baseline - should be correct)
        assert r1_project == expected_project, f"R1 project mismatch: {r1_project} != {expected_project}"
        assert r1_path.startswith(expected_path_prefix), f"R1 path should start with UUID: {r1_path}"

        # Critical regression test for Issue #479: R2 must have correct project and path
        assert r2_project == expected_project, (
            f"R2 project name mismatch (Issue #479 regression):\n"
            f"  Expected: {expected_project}\n"
            f"  Got: {r2_project}\n"
            f"  This indicates the synchronizer is not setting the correct project name"
        )

        assert r2_path.startswith(expected_path_prefix), (
            f"R2 path missing UUID (Issue #479 regression):\n"
            f"  Expected path starting with: {expected_path_prefix}\n"
            f"  Got: {r2_path}\n"
            f"  This will cause KiCad to display 'R?' instead of 'R2'"
        )

        # Verify paths match exactly (for root schematic, should be identical)
        assert r2_path == r1_path, (
            f"R2 and R1 should have identical paths in root schematic:\n"
            f"  R1 path: {r1_path}\n"
            f"  R2 path: {r2_path}"
        )

        # Verify C1 instance data (ensure nothing was broken)
        assert c1_project == expected_project, f"C1 project mismatch: {c1_project} != {expected_project}"
        assert c1_path == r1_path, f"C1 path should match R1: {c1_path} != {r1_path}"

        print(f"✅ Step 3: Instance data verified from schematic file")
        print(f"   - R1: project={r1_project}, path={r1_path}")
        print(f"   - R2: project={r2_project}, path={r2_path} ✓ (matches R1)")
        print(f"   - C1: project={c1_project}, path={c1_path} ✓ (matches R1)")

        print(f"\n{'='*70}")
        print(f"✅ ALL TESTS PASSED: Component sync working correctly")
        print(f"   - R1: {r1_after.value} (preserved)")
        print(f"   - R2: {r2_after.value} (added with correct instance data)")
        print(f"   - C1: {c1_after.value} (preserved)")
        print(f"{'='*70}")

    finally:
        # Restore original Python file (R2 commented out)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


def test_11_add_multiple_components(request):
    """Test adding multiple components (R2 and R3) simultaneously during sync.

    Regression test for Issue #479: Ensures multiple components added at once
    all get correct instance data with proper project name and hierarchical path.
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with R1, C1 only
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1, C1 only")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, f"Step 1 failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not created"

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(regular_components) == 2, f"Expected 2 components, got {len(regular_components)}"

        print(f"✅ Step 1: Generated with R1, C1")

        # =====================================================================
        # STEP 2: Add R2 AND R3 to Python code and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add R2 and R3 simultaneously")
        print("="*70)

        # Add R2 and R3 after C1 definition
        modified_code = original_code.replace(
            '    c1 = Component(',
            '''    c1 = Component('''
        )

        # Insert R2 and R3 after C1
        c1_end = modified_code.find('    )\n\n    # Power nets')
        if c1_end == -1:
            c1_end = modified_code.find('    )\n\n    vcc =')

        r2_r3_code = '''    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
'''

        modified_code = modified_code[:c1_end] + r2_r3_code + modified_code[c1_end+4:]

        # Add connections for R2 and R3
        modified_code = modified_code.replace(
            '    r1[2] += vcc\n    c1[2] += gnd',
            '''    r1[2] += vcc
    c1[2] += gnd
    r2[1] += data
    r2[2] += gnd
    r3[1] += data
    r3[2] += vcc'''
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, f"Step 2 failed: {result.stderr}"

        # Validate all components present
        sch = Schematic.load(str(schematic_file))
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        component_refs = {c.reference for c in regular_components}

        assert len(regular_components) == 4, (
            f"Expected 4 components (R1, R2, R3, C1), found {len(regular_components)}: {component_refs}"
        )
        assert component_refs == {"R1", "R2", "R3", "C1"}, f"Component mismatch: {component_refs}"

        print(f"✅ Step 2: Added R2 and R3 successfully")

        # =====================================================================
        # STEP 3: Verify instance data for BOTH new components
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Verify instance data for R2 and R3")
        print("="*70)

        with open(schematic_file, "r") as f:
            schematic_content = f.read()

        expected_project = sch.name
        expected_path_prefix = f"/{sch.uuid}"

        # Extract instance data for all components
        r1_match = re.search(
            r'reference "R1".*?\(instances\s+\(project "([^"]+)".*?\(path "([^"]+)"',
            schematic_content, re.DOTALL
        )
        r2_match = re.search(
            r'reference "R2".*?\(instances\s+\(project "([^"]+)".*?\(path "([^"]+)"',
            schematic_content, re.DOTALL
        )
        r3_match = re.search(
            r'reference "R3".*?\(instances\s+\(project "([^"]+)".*?\(path "([^"]+)"',
            schematic_content, re.DOTALL
        )

        assert r1_match, "R1 instance not found"
        assert r2_match, "R2 instance not found (Issue #479 regression)"
        assert r3_match, "R3 instance not found (Issue #479 regression)"

        r1_project, r1_path = r1_match.groups()
        r2_project, r2_path = r2_match.groups()
        r3_project, r3_path = r3_match.groups()

        # Verify both R2 and R3 have correct instance data
        assert r2_project == expected_project, (
            f"R2 project mismatch: {r2_project} != {expected_project}"
        )
        assert r3_project == expected_project, (
            f"R3 project mismatch: {r3_project} != {expected_project}"
        )

        assert r2_path == r1_path, f"R2 path doesn't match R1: {r2_path} != {r1_path}"
        assert r3_path == r1_path, f"R3 path doesn't match R1: {r3_path} != {r1_path}"

        print(f"✅ Step 3: Both R2 and R3 have correct instance data")
        print(f"   - R2: project={r2_project}, path={r2_path}")
        print(f"   - R3: project={r3_project}, path={r3_path}")

        print(f"\n{'='*70}")
        print(f"✅ ALL TESTS PASSED: Multiple component sync working correctly")
        print(f"{'='*70}")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


def test_12_sync_preserves_special_project_names(request):
    """Test sync with project names containing special characters.

    Regression test for Issue #479: Ensures the fix handles project names
    with spaces, hyphens, underscores correctly.
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Modify Python to use special project name
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with special project name")
        print("="*70)

        # Change project name to include special characters
        special_name = "test-project_v1"
        modified_code = original_code.replace(
            'project_name="comprehensive_root"',
            f'project_name="{special_name}"'
        )

        # Also update the circuit decorator name to match
        modified_code = modified_code.replace(
            '@circuit(name="comprehensive_root")',
            f'@circuit(name="{special_name}")'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Generate with special name
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, f"Step 1 failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not created"

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        print(f"✅ Step 1: Generated with project name: {special_name}")

        # =====================================================================
        # STEP 2: Add R2 during sync
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add R2 during sync")
        print("="*70)

        # Uncomment R2
        modified_code2 = modified_code.replace(
            '    # r2 = Component(',
            '    r2 = Component('
        )
        modified_code2 = modified_code2.replace(
            '    #     symbol="Device:R",',
            '        symbol="Device:R",'
        )
        modified_code2 = modified_code2.replace(
            '    #     ref="R2",',
            '        ref="R2",'
        )
        modified_code2 = modified_code2.replace(
            '    #     value="4.7k",',
            '        value="4.7k",'
        )
        modified_code2 = modified_code2.replace(
            '    #     footprint="Resistor_SMD:R_0603_1608Metric"',
            '        footprint="Resistor_SMD:R_0603_1608Metric"'
        )
        modified_code2 = modified_code2.replace(
            '    # )',
            '    )'
        )
        modified_code2 = modified_code2.replace(
            '    # r2[1] += data',
            '    r2[1] += data'
        )
        modified_code2 = modified_code2.replace(
            '    # r2[2] += gnd',
            '    r2[2] += gnd'
        )

        with open(python_file, "w") as f:
            f.write(modified_code2)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, f"Step 2 failed: {result.stderr}"

        print(f"✅ Step 2: R2 added successfully")

        # =====================================================================
        # STEP 3: Verify R2 has special project name
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Verify R2 has correct special project name")
        print("="*70)

        with open(schematic_file, "r") as f:
            schematic_content = f.read()

        r2_match = re.search(
            r'reference "R2".*?\(instances\s+\(project "([^"]+)"',
            schematic_content, re.DOTALL
        )

        assert r2_match, "R2 instance not found"
        r2_project = r2_match.group(1)

        # Critical: R2 should have the special project name, not a default
        assert r2_project == special_name, (
            f"R2 project name incorrect with special characters:\n"
            f"  Expected: {special_name}\n"
            f"  Got: {r2_project}\n"
            f"  This indicates the synchronizer doesn't handle special characters correctly"
        )

        print(f"✅ Step 3: R2 has correct project name: {r2_project}")

        print(f"\n{'='*70}")
        print(f"✅ ALL TESTS PASSED: Special project names handled correctly")
        print(f"{'='*70}")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


def test_13_sync_performance_regression(request):
    """Test that the sync performance hasn't degraded significantly.

    Regression test for Issue #479 fix: Ensures the instance data fix
    doesn't significantly slow down sync operations.
    """
    import time

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Baseline - Generate initial schematic
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate baseline schematic")
        print("="*70)

        start = time.time()
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        baseline_time = time.time() - start

        assert result.returncode == 0, f"Baseline generation failed: {result.stderr}"
        print(f"✅ Baseline generation time: {baseline_time:.2f}s")

        # =====================================================================
        # STEP 2: Measure sync performance
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add R2 and measure sync time")
        print("="*70)

        # Uncomment R2
        modified_code = original_code.replace(
            '    # r2 = Component(',
            '    r2 = Component('
        )
        modified_code = modified_code.replace(
            '    #     symbol="Device:R",',
            '        symbol="Device:R",'
        )
        modified_code = modified_code.replace(
            '    #     ref="R2",',
            '        ref="R2",'
        )
        modified_code = modified_code.replace(
            '    #     value="4.7k",',
            '        value="4.7k",'
        )
        modified_code = modified_code.replace(
            '    #     footprint="Resistor_SMD:R_0603_1608Metric"',
            '        footprint="Resistor_SMD:R_0603_1608Metric"'
        )
        modified_code = modified_code.replace(
            '    # )',
            '    )'
        )
        modified_code = modified_code.replace(
            '    # r2[1] += data',
            '    r2[1] += data'
        )
        modified_code = modified_code.replace(
            '    # r2[2] += gnd',
            '    r2[2] += gnd'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Measure sync time
        start = time.time()
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        sync_time = time.time() - start

        assert result.returncode == 0, f"Sync failed: {result.stderr}"
        print(f"✅ Sync time: {sync_time:.2f}s")

        # =====================================================================
        # STEP 3: Verify performance is acceptable
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Verify performance")
        print("="*70)

        # Sync should not be significantly slower than initial generation
        # Allow up to 2x slower (generous margin for sync overhead)
        max_acceptable_time = baseline_time * 2.0

        print(f"   Baseline time: {baseline_time:.2f}s")
        print(f"   Sync time: {sync_time:.2f}s")
        print(f"   Ratio: {sync_time/baseline_time:.2f}x")
        print(f"   Max acceptable: {max_acceptable_time:.2f}s")

        assert sync_time < max_acceptable_time, (
            f"Sync performance regression detected:\n"
            f"  Baseline: {baseline_time:.2f}s\n"
            f"  Sync: {sync_time:.2f}s\n"
            f"  Ratio: {sync_time/baseline_time:.2f}x (should be < 2.0x)\n"
            f"  This may indicate the Issue #479 fix is too slow"
        )

        print(f"✅ Performance acceptable")

        print(f"\n{'='*70}")
        print(f"✅ ALL TESTS PASSED: No performance regression detected")
        print(f"{'='*70}")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
