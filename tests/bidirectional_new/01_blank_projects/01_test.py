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


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup: Clean generated directories. Cleanup: Remove or preserve artifacts."""
    test_dir = Path(__file__).parent

    # Directories to clean before each test
    generated_dirs = [
        test_dir / "blank",  # Generated KiCad project
        test_dir / "test_artifacts",  # Preserved artifacts
    ]

    # Clean up before test
    for dir_path in generated_dirs:
        if dir_path.exists():
            shutil.rmtree(dir_path)

    yield  # Run the test

    # After test: preserve or cleanup
    if PRESERVE_ARTIFACTS:
        # Preserve all artifacts in test_artifacts/
        artifacts_dir = test_dir / "test_artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        # Move generated files to artifacts directory
        blank_dir = test_dir / "blank"
        if blank_dir.exists():
            dest = artifacts_dir / "blank"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(blank_dir, dest)

        print(f"\n📁 Test artifacts preserved in: {artifacts_dir}")
    else:
        # Clean up generated directories
        for dir_path in generated_dirs:
            if dir_path.exists():
                shutil.rmtree(dir_path)


def test_01_generate_blank_kicad_from_python():
    """
    Test 1.1: Generate blank KiCad project from blank Python circuit.

    Validates:
    - Python → KiCad generation works with empty circuit
    - Valid project files created
    - No crashes on minimal input
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

    # Verify schematic is valid and has no components
    sch_content = kicad_sch.read_text()
    assert "(kicad_sch" in sch_content, "Invalid KiCad schematic format"
    assert "(symbol" not in sch_content, "Blank circuit should have no components"

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

        print("✅ Test 1.3 PASSED: Blank round-trip stable and idempotent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
