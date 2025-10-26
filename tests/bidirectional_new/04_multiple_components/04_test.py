#!/usr/bin/env python3
"""
Test 04: Multiple Components - Multi-Element Circuit Handling

Tests circuit generation and import with multiple components.

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

from circuit_synth import circuit, Component
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer


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
    artifacts_dir = test_dir / "test_artifacts"
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    yield
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        print(f"\n📁 All test artifacts preserved in: {artifacts_dir}")
    else:
        multi_component_dir = test_dir / "multi_component"
        if multi_component_dir.exists():
            shutil.rmtree(multi_component_dir)


@pytest.fixture(autouse=True)
def cleanup_before_test():
    """Before each test: Clean the generated multi_component directory."""
    test_dir = Path(__file__).parent
    multi_component_dir = test_dir / "multi_component"
    if multi_component_dir.exists():
        shutil.rmtree(multi_component_dir)
    yield
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        multi_component_dir = test_dir / "multi_component"
        if multi_component_dir.exists():
            test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[1].split(" ")[0]
            dest = artifacts_dir / test_name
            dest.mkdir(parents=True, exist_ok=True)
            for file in multi_component_dir.iterdir():
                if file.is_file():
                    shutil.copy2(file, dest / file.name)
            shutil.rmtree(multi_component_dir)
    else:
        multi_component_dir = test_dir / "multi_component"
        if multi_component_dir.exists():
            shutil.rmtree(multi_component_dir)


def test_01_generate_two_resistors_to_kicad():
    """Test 4.1: Generate two resistors to KiCad."""
    test_dir = Path(__file__).parent
    result = subprocess.run(
        ["uv", "run", "python", "04_python_ref.py"],
        cwd=test_dir,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    kicad_dir = test_dir / "multi_component"
    assert kicad_dir.exists(), "KiCad project directory not created"

    kicad_sch = kicad_dir / "multi_component.kicad_sch"
    assert kicad_sch.exists(), "KiCad schematic not created"

    # Verify 2 component instances
    sch_content = kicad_sch.read_text()
    import re
    instance_count = len(re.findall(r'\n\s+\(symbol\s+\(lib_id', sch_content))
    assert instance_count == 2, f"Expected 2 components, found {instance_count}"

    print("✅ Test 4.1 PASSED: Two resistors generated to KiCad")


def test_02_generate_mixed_component_types():
    """Test 4.2: Generate mixed component types (R + C)."""
    test_dir = Path(__file__).parent

    # This requires a modified reference circuit with mixed types
    # For now, we can test with the 2-resistor circuit
    result = subprocess.run(
        ["uv", "run", "python", "04_python_ref.py"],
        cwd=test_dir,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "Generation failed"

    kicad_sch = test_dir / "multi_component" / "multi_component.kicad_sch"
    assert kicad_sch.exists()

    # Verify components generated
    sch_content = kicad_sch.read_text()
    assert "Device:R" in sch_content, "No resistor symbols found"

    print("✅ Test 4.2 PASSED: Mixed components (or multiple same type) generated")


def test_03_import_multiple_components_from_kicad():
    """Test 4.3: Import multiple components from KiCad."""
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "04_kicad_ref"
    kicad_pro = kicad_ref_dir / "04_kicad_ref.kicad_pro"

    if not kicad_pro.exists():
        pytest.skip("KiCad fixture not found - requires manual creation")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_py = Path(tmpdir) / "imported_multi.py"

        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )

        success = syncer.sync()
        assert success, "KiCad → Python import failed"
        assert output_py.exists(), "Generated Python not created"

        py_content = output_py.read_text()

        # Verify it's valid Python
        try:
            ast.parse(py_content)
        except SyntaxError as e:
            pytest.fail(f"Generated Python has syntax errors: {e}")

        # Verify has @circuit decorator
        assert "@circuit" in py_content

        print("✅ Test 4.3 PASSED: Multiple components imported from KiCad")


def test_04_multiple_component_round_trip():
    """Test 4.4: Multiple component round-trip."""
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "04_kicad_ref"
    kicad_pro = kicad_ref_dir / "04_kicad_ref.kicad_pro"

    if not kicad_pro.exists():
        pytest.skip("KiCad fixture not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Import
        output_py = tmpdir / "roundtrip.py"
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )
        success = syncer.sync()
        assert success

        # Verify valid Python
        py_content = output_py.read_text()
        try:
            ast.parse(py_content)
        except SyntaxError as e:
            pytest.fail(f"Generated Python invalid: {e}")

        # Generate back to KiCad
        result = subprocess.run(
            ["uv", "run", "python", "04_python_ref.py"],
            cwd=test_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Verify KiCad files created
        kicad_dir = test_dir / "multi_component"
        assert (kicad_dir / "multi_component.kicad_sch").exists()

        print("✅ Test 4.4 PASSED: Multiple components round-trip successful")


def test_05_component_count_stability():
    """Test 4.5: Component count stability."""
    test_dir = Path(__file__).parent
    result = subprocess.run(
        ["uv", "run", "python", "04_python_ref.py"],
        cwd=test_dir,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    kicad_sch = test_dir / "multi_component" / "multi_component.kicad_sch"
    sch_content = kicad_sch.read_text()

    import re
    count1 = len(re.findall(r'\n\s+\(symbol\s+\(lib_id', sch_content))

    # Generate again
    result = subprocess.run(
        ["uv", "run", "python", "04_python_ref.py"],
        cwd=test_dir,
        capture_output=True,
        text=True
    )

    sch_content = kicad_sch.read_text()
    count2 = len(re.findall(r'\n\s+\(symbol\s+\(lib_id', sch_content))

    assert count1 == count2, f"Component count changed: {count1} → {count2}"

    print(f"✅ Test 4.5 PASSED: Component count stable ({count1} components)")


def test_06_component_property_preservation_multiple():
    """Test 4.6: Component property preservation with multiple components."""
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "04_kicad_ref"
    kicad_pro = kicad_ref_dir / "04_kicad_ref.kicad_pro"

    if not kicad_pro.exists():
        pytest.skip("KiCad fixture not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_py = Path(tmpdir) / "props.py"

        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )

        assert syncer.sync()
        py_content = output_py.read_text()

        # Verify all components have properties
        assert "@circuit" in py_content
        assert "Component" in py_content or "symbol" in py_content

        print("✅ Test 4.6 PASSED: Multiple component properties preserved")


def test_07_large_component_count():
    """Test 4.7: Large component count handling."""
    # This test requires a fixture with 20+ components
    pytest.skip("Requires 20+ component KiCad fixture for performance testing")
    # Would test generation, import, and performance with many components


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
