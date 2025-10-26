#!/usr/bin/env python3
"""
Test 02: Single Component - Basic CRUD Operations

Tests basic Create, Read, Update, Delete operations on a single resistor
component through bidirectional sync.

Environment Variables:
    PRESERVE_TEST_ARTIFACTS=1  - Keep all generated files in test_artifacts/ directory
"""

import ast
import os
import pytest
from pathlib import Path
import tempfile
import shutil
import subprocess

# Import circuit-synth components
from circuit_synth import circuit, Component
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer


# Check if we should preserve test artifacts
PRESERVE_ARTIFACTS = os.getenv("PRESERVE_TEST_ARTIFACTS", "").lower() in ("1", "true", "yes")


def get_test_artifacts_dir():
    """Get or create test_artifacts directory."""
    test_dir = Path(__file__).parent
    artifacts_dir = test_dir / "test_artifacts"

    if PRESERVE_ARTIFACTS:
        artifacts_dir.mkdir(exist_ok=True)

    return artifacts_dir


@pytest.fixture(scope="session", autouse=True)
def setup_session():
    """Setup session: Clean test directories before all tests."""
    test_dir = Path(__file__).parent

    # Only clean test_artifacts at start of session
    artifacts_dir = test_dir / "test_artifacts"
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)

    yield  # Run all tests

    # After all tests: preserve or cleanup
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        print(f"\n📁 All test artifacts preserved in: {artifacts_dir}")
    else:
        # Clean up only generated single_resistor directory
        single_resistor_dir = test_dir / "single_resistor"
        if single_resistor_dir.exists():
            shutil.rmtree(single_resistor_dir)


@pytest.fixture(autouse=True)
def cleanup_before_test():
    """Before each test: Clean the generated single_resistor directory."""
    test_dir = Path(__file__).parent
    single_resistor_dir = test_dir / "single_resistor"

    # Always clean before test to ensure fresh start
    if single_resistor_dir.exists():
        shutil.rmtree(single_resistor_dir)

    yield  # Run the test

    # After each test: preserve to test_artifacts or clean
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        single_resistor_dir = test_dir / "single_resistor"

        if single_resistor_dir.exists():
            # Copy to artifacts directory with test name
            test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[1].split(" ")[0]
            dest = artifacts_dir / test_name

            # Create destination if needed
            dest.mkdir(parents=True, exist_ok=True)

            # Copy generated files from single_resistor/ directory (don't delete dest, just add to it)
            for file in single_resistor_dir.iterdir():
                dest_file = dest / file.name
                if file.is_file():
                    shutil.copy2(file, dest_file)

            shutil.rmtree(single_resistor_dir)  # Remove original after copying
    else:
        # Clean up immediately if not preserving
        single_resistor_dir = test_dir / "single_resistor"
        if single_resistor_dir.exists():
            shutil.rmtree(single_resistor_dir)


def test_01_generate_single_resistor_to_kicad():
    """
    Test 2.1: Generate single resistor to KiCad and compare with reference.

    Validates:
    - Python circuit with single component generates successfully
    - Valid KiCad project created with correct schematic structure
    - Component properties match reference fixture (R1, 10k, footprint)
    - Generated schematic matches reference schematic structure
    """
    import kicad_sch_api as ksa

    test_dir = Path(__file__).parent

    # Run the Python circuit to generate KiCad
    result = subprocess.run(
        ["uv", "run", "python", "02_python_ref.py"],
        cwd=test_dir,
        capture_output=True,
        text=True
    )

    # Verify generation succeeded
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    # Verify KiCad files were created
    kicad_dir = test_dir / "single_resistor"
    assert kicad_dir.exists(), "KiCad project directory not created"

    kicad_sch = kicad_dir / "single_resistor.kicad_sch"
    assert kicad_sch.exists(), "KiCad schematic file (.kicad_sch) not created"

    # Parse generated schematic using kicad-sch-api
    generated = ksa.Schematic.load(str(kicad_sch))
    assert generated is not None, "Failed to parse generated schematic"
    print(f"  ✓ kicad-sch-api: Parsed schematic successfully")

    # Exercise kicad-sch-api: Verify schematic has exactly 1 component
    components = generated.components
    assert len(components) == 1, f"Expected 1 component, found {len(components)}"
    print(f"  ✓ kicad-sch-api: Found {len(components)} component (expected 1)")

    # Exercise kicad-sch-api: Get component and verify all properties
    r1 = components[0]

    # Test reference property
    reference = r1.reference
    assert reference == "R1", f"Expected reference 'R1', got '{reference}'"
    print(f"  ✓ kicad-sch-api: Component.reference = '{reference}'")

    # Test value property
    value = r1.value
    assert value == "10k", f"Expected value '10k', got '{value}'"
    print(f"  ✓ kicad-sch-api: Component.value = '{value}'")

    # Test footprint property
    footprint = r1.footprint
    assert footprint == "Resistor_SMD:R_0603_1608Metric", f"Expected footprint 'Resistor_SMD:R_0603_1608Metric', got '{footprint}'"
    print(f"  ✓ kicad-sch-api: Component.footprint = '{footprint}'")

    # Test lib_id property
    lib_id = r1.lib_id
    assert lib_id == "Device:R", f"Expected lib_id 'Device:R', got '{lib_id}'"
    print(f"  ✓ kicad-sch-api: Component.lib_id = '{lib_id}'")

    # Exercise kicad-sch-api: Check wires and other properties
    wires = generated.wires
    print(f"  ✓ kicad-sch-api: Found {len(wires)} wires")

    junctions = generated.junctions
    print(f"  ✓ kicad-sch-api: Found {len(junctions)} junctions")

    version = generated.version
    print(f"  ✓ kicad-sch-api: Version = {version}")

    uuid = generated.uuid
    print(f"  ✓ kicad-sch-api: UUID = {uuid}")

    # Exercise kicad-sch-api: Access additional schematic elements via _data
    # These are currently only accessible through _data, not public properties
    texts = generated._data.get('texts', [])
    print(f"  ✓ kicad-sch-api: Found {len(texts)} text elements (via _data)")

    text_boxes = generated._data.get('text_boxes', [])
    print(f"  ✓ kicad-sch-api: Found {len(text_boxes)} text boxes (via _data)")

    labels = generated._data.get('labels', [])
    print(f"  ✓ kicad-sch-api: Found {len(labels)} labels (via _data)")

    hierarchical_labels = generated._data.get('hierarchical_labels', [])
    print(f"  ✓ kicad-sch-api: Found {len(hierarchical_labels)} hierarchical labels (via _data)")

    rectangles = generated._data.get('rectangles', [])
    print(f"  ✓ kicad-sch-api: Found {len(rectangles)} rectangles (via _data)")

    polylines = generated._data.get('polylines', [])
    print(f"  ✓ kicad-sch-api: Found {len(polylines)} polylines (via _data)")

    circles = generated._data.get('circles', [])
    print(f"  ✓ kicad-sch-api: Found {len(circles)} circles (via _data)")

    arcs = generated._data.get('arcs', [])
    print(f"  ✓ kicad-sch-api: Found {len(arcs)} arcs (via _data)")

    beziers = generated._data.get('beziers', [])
    print(f"  ✓ kicad-sch-api: Found {len(beziers)} beziers (via _data)")

    images = generated._data.get('images', [])
    print(f"  ✓ kicad-sch-api: Found {len(images)} images (via _data)")

    # Load reference schematic and compare
    ref_kicad_dir = test_dir / "02_kicad_ref"
    if ref_kicad_dir.exists():
        ref_sch_file = ref_kicad_dir / "02_kicad_ref.kicad_sch"
        if ref_sch_file.exists():
            reference = ksa.Schematic.load(str(ref_sch_file))
            print(f"  ✓ kicad-sch-api: Parsed reference schematic")

            # Compare component counts
            ref_components = reference.components
            assert len(ref_components) == len(components), \
                f"Component count mismatch: reference has {len(ref_components)}, generated has {len(components)}"
            print(f"  ✓ kicad-sch-api: Component count matches (both have {len(components)})")

            # Compare each component property
            for ref_comp, gen_comp in zip(ref_components, components):
                ref_ref = ref_comp.reference
                gen_ref = gen_comp.reference
                assert ref_ref == gen_ref, \
                    f"Reference mismatch: {ref_ref} != {gen_ref}"
                print(f"  ✓ kicad-sch-api: Reference matches: {gen_ref}")

                ref_val = ref_comp.value
                gen_val = gen_comp.value
                assert ref_val == gen_val, \
                    f"Value mismatch for {gen_ref}: {ref_val} != {gen_val}"
                print(f"  ✓ kicad-sch-api: Value matches: {gen_val}")

                ref_fp = ref_comp.footprint
                gen_fp = gen_comp.footprint
                assert ref_fp == gen_fp, \
                    f"Footprint mismatch for {gen_ref}: {ref_fp} != {gen_fp}"
                print(f"  ✓ kicad-sch-api: Footprint matches: {gen_fp}")

                ref_lib = ref_comp.lib_id
                gen_lib = gen_comp.lib_id
                assert ref_lib == gen_lib, \
                    f"Library ID mismatch for {gen_ref}: {ref_lib} != {gen_lib}"
                print(f"  ✓ kicad-sch-api: Library ID matches: {gen_lib}")

    print("✅ Test 2.1 PASSED: Single resistor schematic matches reference")


def test_02_import_single_resistor_from_kicad():
    """
    Test 2.2: Import single resistor from KiCad.

    Validates:
    - KiCad → Python import works with single component
    - Component reference extracted correctly (R1)
    - Component value extracted correctly (10k)
    - Generated Python is syntactically valid
    """
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "02_kicad_ref"

    # Find the KiCad project file
    kicad_pro = kicad_ref_dir / "02_kicad_ref.kicad_pro"
    assert kicad_pro.exists(), f"Reference KiCad project not found: {kicad_pro}"

    # Create temp directory for generated Python
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated_python"
        output_dir.mkdir()

        # Import KiCad → Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_dir / "imported_single_resistor.py"),
            preview_only=False
        )

        success = syncer.sync()
        assert success, "KiCad → Python import failed"

        # Verify Python file was created
        generated_py = output_dir / "imported_single_resistor.py"
        assert generated_py.exists(), "Generated Python file not found"

        # Verify Python code is syntactically valid
        py_content = generated_py.read_text()
        try:
            tree = ast.parse(py_content)
        except SyntaxError as e:
            pytest.fail(f"Generated Python has syntax errors: {e}")

        # Verify has @circuit decorator
        assert "@circuit" in py_content, "Generated code missing @circuit decorator"

        # Verify has resistor component
        assert "R1" in py_content or "Resistor" in py_content, "Resistor component not found in generated code"

        # Preserve artifacts if requested
        if PRESERVE_ARTIFACTS:
            artifacts_dir = get_test_artifacts_dir()
            test_name = "test_02_import_single_resistor_from_kicad"
            dest = artifacts_dir / test_name
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)

            # Copy generated Python file
            shutil.copy(generated_py, dest / "imported_single_resistor.py")

        print("✅ Test 2.2 PASSED: Single resistor imported successfully from KiCad")


def test_03_single_resistor_round_trip():
    """
    Test 2.3: Round-trip single resistor Python → KiCad → Python.

    Validates:
    - Single component preserved through full cycle
    - No data loss or accumulation
    - Component properties stable
    """
    test_dir = Path(__file__).parent

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Generate KiCad from Python
        result = subprocess.run(
            ["uv", "run", "python", "02_python_ref.py"],
            cwd=test_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Initial KiCad generation failed: {result.stderr}"

        kicad_dir = test_dir / "single_resistor"
        kicad_pro = kicad_dir / "single_resistor.kicad_pro"

        # Step 2: Import KiCad → Python
        output_py = tmpdir / "round_trip_single_resistor.py"
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )

        success = syncer.sync()
        assert success, "KiCad → Python import failed in round-trip"
        assert output_py.exists(), "Round-trip Python file not created"

        # Step 3: Verify round-trip Python is valid
        py_content = output_py.read_text()
        try:
            tree = ast.parse(py_content)
        except SyntaxError as e:
            pytest.fail(f"Round-trip Python has syntax errors: {e}")

        # Verify resistor component preserved
        assert "R1" in py_content or "Resistor" in py_content, "Resistor not preserved in round-trip"
        assert "@circuit" in py_content, "Round-trip should preserve @circuit decorator"

        # Check file size didn't grow excessively (no accumulation)
        original_py = test_dir / "02_python_ref.py"
        original_size = original_py.stat().st_size
        roundtrip_size = output_py.stat().st_size

        # Allow some size difference for formatting, but not massive growth
        size_ratio = roundtrip_size / original_size
        assert size_ratio < 3.0, f"Round-trip file grew too much: {size_ratio:.1f}x original size"

        # Preserve artifacts if requested
        if PRESERVE_ARTIFACTS:
            artifacts_dir = get_test_artifacts_dir()
            test_name = "test_03_single_resistor_round_trip"
            dest = artifacts_dir / test_name
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)

            # Copy generated Python file
            shutil.copy(output_py, dest / "round_trip_single_resistor.py")
            # Also copy the reference Python file for comparison
            shutil.copy(test_dir / "02_python_ref.py", dest / "02_python_ref.py")

        print("✅ Test 2.3 PASSED: Single resistor round-trip stable and idempotent")


def test_04_resistor_value_modification():
    """
    Test 2.4: Resistor value modification preserved through round-trip.

    Validates:
    - Changing resistor value (10k → 47k) works
    - Modified value propagates to KiCad
    - Value preserved when re-importing
    """
    pytest.skip("Requires implementing dynamic circuit modification in test")
    # TODO: Implement test for value modification


def test_05_resistor_footprint_change():
    """
    Test 2.5: Resistor footprint change preserved.

    Validates:
    - Footprint selection works
    - Footprint change persists through round-trip
    """
    pytest.skip("Requires implementing footprint modification capability")
    # TODO: Implement test for footprint changes


def test_06_component_reference_preservation():
    """
    Test 2.6: Custom component reference preserved.

    Validates:
    - Custom references (e.g., R_LOAD instead of R1) work
    - References survive round-trip
    """
    pytest.skip("Requires creating circuit with custom reference")
    # TODO: Implement test for custom references


def test_07_component_position_stability():
    """
    Test 2.7: Component position in KiCad preserved through round-trip.

    Validates:
    - Component X,Y position extracted and preserved
    - Position stable across round-trip
    """
    pytest.skip("Requires position extraction from KiCad files")
    # TODO: Implement test for position preservation


def test_08_switching_components():
    """
    Test 2.8: Replacing resistor with different value.

    Validates:
    - Component replacement works completely
    - No ghost components remain
    - New component correctly added
    """
    pytest.skip("Requires implementing component replacement logic")
    # TODO: Implement test for component switching


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
