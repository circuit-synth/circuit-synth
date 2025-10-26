#!/usr/bin/env python3
"""
Test 01: Blank Projects - Bidirectional Sync Foundation

Tests the absolute foundation of bidirectional sync with empty circuits.

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
from circuit_synth import circuit
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
        # Clean up only generated blank directory
        blank_dir = test_dir / "blank"
        if blank_dir.exists():
            shutil.rmtree(blank_dir)


@pytest.fixture(autouse=True)
def cleanup_before_test():
    """Before each test: Clean the generated blank directory."""
    test_dir = Path(__file__).parent
    blank_dir = test_dir / "blank"

    # Always clean before test to ensure fresh start
    if blank_dir.exists():
        shutil.rmtree(blank_dir)

    yield  # Run the test

    # After each test: preserve to test_artifacts or clean
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        blank_dir = test_dir / "blank"

        if blank_dir.exists():
            # Copy to artifacts directory with test name
            test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[1].split(" ")[0]
            dest = artifacts_dir / test_name

            # Create destination if needed
            dest.mkdir(parents=True, exist_ok=True)

            # Copy KiCad files from blank/ directory (don't delete dest, just add to it)
            for file in blank_dir.iterdir():
                dest_file = dest / file.name
                if file.is_file():
                    shutil.copy2(file, dest_file)

            shutil.rmtree(blank_dir)  # Remove original after copying
    else:
        # Clean up immediately if not preserving
        blank_dir = test_dir / "blank"
        if blank_dir.exists():
            shutil.rmtree(blank_dir)


def test_01_generate_blank_kicad_from_python():
    """
    Test 1.1: Generate blank KiCad project from blank Python circuit.

    Validates:
    - Python → KiCad generation works with empty circuit
    - Valid project files created
    - Schematic structure matches expected format using kicad-sch-api
    """
    test_dir = Path(__file__).parent

    # Run the Python circuit to generate KiCad
    result = subprocess.run(
        ["uv", "run", "python", "01_python_ref.py"],
        cwd=test_dir,
        capture_output=True,
        text=True
    )

    # Verify generation succeeded
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    # Verify KiCad files were created
    kicad_dir = test_dir / "blank"
    assert kicad_dir.exists(), "KiCad project directory not created"

    kicad_pro = kicad_dir / "blank.kicad_pro"
    kicad_sch = kicad_dir / "blank.kicad_sch"
    kicad_pcb = kicad_dir / "blank.kicad_pcb"

    assert kicad_pro.exists(), "KiCad project file (.kicad_pro) not created"
    assert kicad_sch.exists(), "KiCad schematic file (.kicad_sch) not created"
    assert kicad_pcb.exists(), "KiCad PCB file (.kicad_pcb) not created"

    # Use kicad-sch-api to parse and verify schematic structure
    import kicad_sch_api as ksa

    schematic = ksa.Schematic.load(str(kicad_sch))
    assert schematic is not None, "Failed to parse schematic with kicad-sch-api"

    # Exercise kicad-sch-api: Verify schematic is blank (no components)
    components = schematic.components
    assert len(components) == 0, f"Blank circuit should have no components, found {len(components)}"
    print(f"  ✓ kicad-sch-api: Found {len(components)} components (expected 0)")

    # Exercise kicad-sch-api: Verify no wires/junctions
    wires = schematic.wires
    assert len(wires) == 0, f"Blank circuit should have no wires, found {len(wires)}"
    print(f"  ✓ kicad-sch-api: Found {len(wires)} wires (expected 0)")

    junctions = schematic.junctions
    assert len(junctions) == 0, f"Blank circuit should have no junctions, found {len(junctions)}"
    print(f"  ✓ kicad-sch-api: Found {len(junctions)} junctions (expected 0)")

    # Exercise kicad-sch-api: Verify basic schematic properties
    version = schematic.version
    assert version is not None, "Schematic should have a version"
    print(f"  ✓ kicad-sch-api: Version = {version}")

    uuid = schematic.uuid
    assert uuid is not None, "Schematic should have a UUID"
    print(f"  ✓ kicad-sch-api: UUID = {uuid}")

    generator = schematic.generator
    print(f"  ✓ kicad-sch-api: Generator = {generator}")

    title_block = schematic.title_block
    assert isinstance(title_block, dict), "Title block should be a dictionary"
    print(f"  ✓ kicad-sch-api: Title block is dict with {len(title_block)} properties")

    # Exercise kicad-sch-api: Access additional schematic elements via _data
    # These are currently only accessible through _data, not public properties
    texts = schematic._data.get('texts', [])
    print(f"  ✓ kicad-sch-api: Found {len(texts)} text elements (via _data)")

    text_boxes = schematic._data.get('text_boxes', [])
    print(f"  ✓ kicad-sch-api: Found {len(text_boxes)} text boxes (via _data)")

    labels = schematic._data.get('labels', [])
    print(f"  ✓ kicad-sch-api: Found {len(labels)} labels (via _data)")

    hierarchical_labels = schematic._data.get('hierarchical_labels', [])
    print(f"  ✓ kicad-sch-api: Found {len(hierarchical_labels)} hierarchical labels (via _data)")

    rectangles = schematic._data.get('rectangles', [])
    print(f"  ✓ kicad-sch-api: Found {len(rectangles)} rectangles (via _data)")

    polylines = schematic._data.get('polylines', [])
    print(f"  ✓ kicad-sch-api: Found {len(polylines)} polylines (via _data)")

    circles = schematic._data.get('circles', [])
    print(f"  ✓ kicad-sch-api: Found {len(circles)} circles (via _data)")

    arcs = schematic._data.get('arcs', [])
    print(f"  ✓ kicad-sch-api: Found {len(arcs)} arcs (via _data)")

    beziers = schematic._data.get('beziers', [])
    print(f"  ✓ kicad-sch-api: Found {len(beziers)} beziers (via _data)")

    images = schematic._data.get('images', [])
    print(f"  ✓ kicad-sch-api: Found {len(images)} images (via _data)")

    print("✅ Test 1.1 PASSED: Blank KiCad project generated successfully")


def test_02_import_blank_python_from_kicad():
    """
    Test 1.2: Generate blank Python from blank KiCad project.

    Validates:
    - KiCad → Python import works with empty schematic
    - Valid Python code generated
    - Code is syntactically valid
    """
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "01_kicad_ref"

    # Find the KiCad project file
    kicad_pro = kicad_ref_dir / "01_kicad_ref.kicad_pro"
    assert kicad_pro.exists(), f"Reference KiCad project not found: {kicad_pro}"

    # Create temp directory for generated Python
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated_python"
        output_dir.mkdir()

        # Import KiCad → Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_dir / "imported_blank.py"),
            preview_only=False
        )

        success = syncer.sync()
        assert success, "KiCad → Python import failed"

        # Verify Python file was created
        generated_py = output_dir / "imported_blank.py"
        assert generated_py.exists(), "Generated Python file not found"

        # Verify Python code is syntactically valid
        py_content = generated_py.read_text()
        try:
            tree = ast.parse(py_content)
        except SyntaxError as e:
            pytest.fail(f"Generated Python has syntax errors: {e}")

        # Verify has @circuit decorator
        assert "@circuit" in py_content, "Generated code missing @circuit decorator"

        # Verify has no component definitions (blank circuit)
        assert "Device_R" not in py_content, "Blank circuit should have no components"
        assert "Device_C" not in py_content, "Blank circuit should have no components"

        # Preserve artifacts if requested
        if PRESERVE_ARTIFACTS:
            artifacts_dir = get_test_artifacts_dir()
            test_name = "test_02_import_blank_python_from_kicad"
            dest = artifacts_dir / test_name
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)

            # Copy generated Python file
            shutil.copy(generated_py, dest / "imported_blank.py")

        print("✅ Test 1.2 PASSED: Blank Python imported successfully from KiCad")


def test_03_blank_round_trip():
    """
    Test 1.3: Round-trip blank circuit Python → KiCad → Python.

    Validates:
    - No data accumulation
    - Stable round-trip behavior
    - Idempotency on blank projects
    """
    test_dir = Path(__file__).parent

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Generate KiCad from Python
        result = subprocess.run(
            ["uv", "run", "python", "01_python_ref.py"],
            cwd=test_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Initial KiCad generation failed: {result.stderr}"

        kicad_dir = test_dir / "blank"
        kicad_pro = kicad_dir / "blank.kicad_pro"

        # Step 2: Import KiCad → Python
        output_py = tmpdir / "round_trip_blank.py"
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

        # Verify no components added/lost
        assert "Device_R" not in py_content, "Round-trip should maintain blank circuit"
        assert "@circuit" in py_content, "Round-trip should preserve @circuit decorator"

        # Check file size didn't grow (no accumulation)
        original_py = test_dir / "01_python_ref.py"
        original_size = original_py.stat().st_size
        roundtrip_size = output_py.stat().st_size

        # Allow some size difference for formatting, but not massive growth
        size_ratio = roundtrip_size / original_size
        assert size_ratio < 3.0, f"Round-trip file grew too much: {size_ratio:.1f}x original size"

        # Preserve artifacts if requested
        if PRESERVE_ARTIFACTS:
            artifacts_dir = get_test_artifacts_dir()
            test_name = "test_03_blank_round_trip"
            dest = artifacts_dir / test_name
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)

            # Copy generated Python file
            shutil.copy(output_py, dest / "round_trip_blank.py")
            # Also copy the reference Python file for comparison
            shutil.copy(test_dir / "01_python_ref.py", dest / "01_python_ref.py")

        print("✅ Test 1.3 PASSED: Blank round-trip stable and idempotent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
