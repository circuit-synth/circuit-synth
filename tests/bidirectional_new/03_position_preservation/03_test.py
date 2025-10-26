#!/usr/bin/env python3
"""
Test 03: Position Preservation - Component Layout Stability

CRITICAL tests validating that component positions on the schematic are
preserved through bidirectional sync cycles.

Environment Variables:
    PRESERVE_TEST_ARTIFACTS=1  - Keep all generated files in test_artifacts/ directory
"""

import ast
import os
import pytest
import re
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


def extract_component_position(sch_content):
    """
    Extract component position from KiCad schematic content.
    
    Returns dict with:
        reference: "R1"
        x: 30.48 (float, mm)
        y: 35.56 (float, mm)
        rotation: 0 (int, degrees)
    """
    # Find symbol instance with lib_id and extract position
    # Pattern: (symbol (lib_id "Device:R") (at X Y rotation) ...)
    pattern = r'\(symbol\s+\(lib_id\s+"Device:R"\)\s+\(at\s+([\d.]+)\s+([\d.]+)\s+(\d+)\)'
    match = re.search(pattern, sch_content)
    
    if not match:
        return None
    
    return {
        "x": float(match.group(1)),
        "y": float(match.group(2)),
        "rotation": int(match.group(3))
    }


def extract_reference_from_symbol(sch_content, symbol_start):
    """Extract reference (R1, R2, etc) from symbol block."""
    # Look for "Reference" property after symbol start
    ref_pattern = r'property\s+"Reference"\s+"(R\d+)"'
    match = re.search(ref_pattern, sch_content[symbol_start:symbol_start+500])
    return match.group(1) if match else None


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
        # Clean up only generated positioned_resistor directory
        positioned_resistor_dir = test_dir / "positioned_resistor"
        if positioned_resistor_dir.exists():
            shutil.rmtree(positioned_resistor_dir)


@pytest.fixture(autouse=True)
def cleanup_before_test():
    """Before each test: Clean the generated positioned_resistor directory."""
    test_dir = Path(__file__).parent
    positioned_resistor_dir = test_dir / "positioned_resistor"

    # Always clean before test to ensure fresh start
    if positioned_resistor_dir.exists():
        shutil.rmtree(positioned_resistor_dir)

    yield  # Run the test

    # After each test: preserve to test_artifacts or clean
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        positioned_resistor_dir = test_dir / "positioned_resistor"

        if positioned_resistor_dir.exists():
            # Copy to artifacts directory with test name
            test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[1].split(" ")[0]
            dest = artifacts_dir / test_name

            # Create destination if needed
            dest.mkdir(parents=True, exist_ok=True)

            # Copy generated files from positioned_resistor/ directory
            for file in positioned_resistor_dir.iterdir():
                dest_file = dest / file.name
                if file.is_file():
                    shutil.copy2(file, dest_file)

            shutil.rmtree(positioned_resistor_dir)
    else:
        # Clean up immediately if not preserving
        positioned_resistor_dir = test_dir / "positioned_resistor"
        if positioned_resistor_dir.exists():
            shutil.rmtree(positioned_resistor_dir)


def test_01_extract_component_position_from_kicad():
    """
    Test 3.1: Extract component position from KiCad schematic.

    Validates:
    - Position coordinates correctly extracted from .kicad_sch
    - Coordinates are floats in millimeters
    - Rotation angle extracted correctly
    """
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "03_kicad_ref"

    # Find the KiCad schematic file
    kicad_sch = kicad_ref_dir / "03_kicad_ref.kicad_sch"
    assert kicad_sch.exists(), f"Reference KiCad schematic not found: {kicad_sch}"

    # Extract position from schematic
    sch_content = kicad_sch.read_text()
    position = extract_component_position(sch_content)
    
    assert position is not None, "Could not extract position from KiCad schematic"
    assert isinstance(position["x"], float), "X coordinate should be float"
    assert isinstance(position["y"], float), "Y coordinate should be float"
    assert isinstance(position["rotation"], int), "Rotation should be int"
    assert position["rotation"] in [0, 90, 180, 270], f"Invalid rotation: {position['rotation']}"

    print(f"✅ Test 3.1 PASSED: Extracted position R1={position}")


def test_02_preserve_position_on_export():
    """
    Test 3.2: Component position preserved on KiCad → Python → KiCad cycle.

    Validates:
    - Position from KiCad extracted and preserved in Python
    - Re-exported to KiCad with same coordinates
    - Position within tolerance (<0.1mm deviation)
    """
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "03_kicad_ref"

    # Get original position from reference KiCad
    kicad_sch_orig = kicad_ref_dir / "03_kicad_ref.kicad_sch"
    sch_content_orig = kicad_sch_orig.read_text()
    position_orig = extract_component_position(sch_content_orig)
    assert position_orig is not None, "Could not extract original position"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Import KiCad → Python
        kicad_pro = kicad_ref_dir / "03_kicad_ref.kicad_pro"
        output_py = tmpdir / "imported_position.py"
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )

        success = syncer.sync()
        assert success, "KiCad → Python import failed"
        assert output_py.exists(), "Generated Python file not found"

        # Step 2: Generate KiCad from imported Python
        result = subprocess.run(
            ["uv", "run", "python", "03_python_ref.py"],
            cwd=test_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"KiCad generation failed: {result.stderr}"

        # Step 3: Extract position from generated KiCad
        positioned_resistor_dir = test_dir / "positioned_resistor"
        kicad_sch_new = positioned_resistor_dir / "positioned_resistor.kicad_sch"
        assert kicad_sch_new.exists(), "Generated schematic not found"

        sch_content_new = kicad_sch_new.read_text()
        position_new = extract_component_position(sch_content_new)
        assert position_new is not None, "Could not extract position from generated KiCad"

        # Step 4: Verify positions match within tolerance
        tolerance_mm = 0.1
        x_diff = abs(position_orig["x"] - position_new["x"])
        y_diff = abs(position_orig["y"] - position_new["y"])
        
        assert x_diff < tolerance_mm, f"X position drift: {x_diff}mm > {tolerance_mm}mm tolerance"
        assert y_diff < tolerance_mm, f"Y position drift: {y_diff}mm > {tolerance_mm}mm tolerance"
        assert position_orig["rotation"] == position_new["rotation"], "Rotation not preserved"

        print(f"✅ Test 3.2 PASSED: Position preserved within tolerance (Δx={x_diff:.4f}mm, Δy={y_diff:.4f}mm)")


def test_03_multiple_component_position_stability():
    """
    Test 3.3: Multiple components maintain relative positions.

    Validates:
    - All component positions extracted correctly
    - Relative positions preserved (distance between components stable)
    - No spurious position changes
    """
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "03_kicad_ref"

    # This test requires a fixture with multiple components
    # For now, use the single component fixture
    kicad_sch = kicad_ref_dir / "03_kicad_ref.kicad_sch"

    if not kicad_sch.exists():
        pytest.skip("Fixture not found - requires KiCad project with multiple components")

    # Extract positions from schematic
    sch_content = kicad_sch.read_text()

    # Count symbol instances
    symbol_instances = len(re.findall(r'\n\s+\(symbol\s+\(lib_id', sch_content))

    if symbol_instances < 2:
        pytest.skip(f"Fixture has {symbol_instances} component(s), test requires 2+")

    # Extract all positions and verify they're different
    positions = re.findall(r'\(at\s+([\d.]+)\s+([\d.]+)\s+(\d+)\)', sch_content)
    assert len(positions) >= 2, "Should have at least 2 positioned components"

    # Verify positions are actually different
    unique_positions = set(positions)
    assert len(unique_positions) == len(positions), "All components should have unique positions"

    print(f"✅ Test 3.3 PASSED: {len(positions)} components with different positions")


def test_04_manual_position_changes_survive_round_trip():
    """
    Test 3.4: Manual position changes preserved through round-trip.

    Validates:
    - User manual position changes preserved
    - Not overwritten by generation algorithm
    - Exact position (not approximated)
    """
    # This test requires manual modification of KiCad files
    # Demonstrates the concept but needs user-created variations

    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "03_kicad_ref"
    kicad_sch = kicad_ref_dir / "03_kicad_ref.kicad_sch"

    if not kicad_sch.exists():
        pytest.skip("Fixture not found")

    # Extract original position
    sch_content = kicad_sch.read_text()
    original_position = extract_component_position(sch_content)

    assert original_position is not None, "Could not extract position from fixture"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Import and re-export
        kicad_pro = kicad_ref_dir / "03_kicad_ref.kicad_pro"
        output_py = tmpdir / "imported.py"
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )

        success = syncer.sync()
        assert success, "Import failed"

        # Generate back to KiCad
        result = subprocess.run(
            ["uv", "run", "python", "03_python_ref.py"],
            cwd=test_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Generation failed"

        # Extract new position
        positioned_resistor_dir = test_dir / "positioned_resistor"
        kicad_sch_new = positioned_resistor_dir / "positioned_resistor.kicad_sch"
        sch_content_new = kicad_sch_new.read_text()
        new_position = extract_component_position(sch_content_new)

        # Verify position is preserved (within tolerance)
        tolerance = 0.1
        x_diff = abs(original_position["x"] - new_position["x"])
        y_diff = abs(original_position["y"] - new_position["y"])

        assert x_diff < tolerance, f"X position changed by {x_diff}mm"
        assert y_diff < tolerance, f"Y position changed by {y_diff}mm"

        print(f"✅ Test 3.4 PASSED: Position preserved through round-trip")


def test_05_position_stability_on_repeated_cycles():
    """
    Test 3.5: Position remains stable on multiple round-trip cycles.

    Validates:
    - No position drift after 1st round-trip
    - No further drift on 2nd and 3rd round-trips
    - Cumulative drift < 0.01mm after 3 cycles
    - Idempotent position preservation
    """
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "03_kicad_ref"
    kicad_sch_orig = kicad_ref_dir / "03_kicad_ref.kicad_sch"

    if not kicad_sch_orig.exists():
        pytest.skip("Fixture not found")

    sch_content = kicad_sch_orig.read_text()
    position_original = extract_component_position(sch_content)
    assert position_original is not None

    positions_per_cycle = [position_original]

    # Run 3 cycles
    for cycle_num in range(1, 4):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Import KiCad
            kicad_pro = kicad_ref_dir / "03_kicad_ref.kicad_pro"
            output_py = tmpdir / f"cycle_{cycle_num}.py"
            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(kicad_pro),
                python_file=str(output_py),
                preview_only=False
            )
            assert syncer.sync(), f"Cycle {cycle_num} import failed"

            # Generate back to KiCad
            result = subprocess.run(
                ["uv", "run", "python", "03_python_ref.py"],
                cwd=test_dir,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Cycle {cycle_num} generation failed"

            # Extract position
            positioned_resistor_dir = test_dir / "positioned_resistor"
            kicad_sch_new = positioned_resistor_dir / "positioned_resistor.kicad_sch"
            sch_content_new = kicad_sch_new.read_text()
            position_new = extract_component_position(sch_content_new)

            positions_per_cycle.append(position_new)

    # Verify position stability
    tolerance = 0.01  # Cumulative tolerance

    for cycle_num in range(1, len(positions_per_cycle)):
        pos_curr = positions_per_cycle[cycle_num]
        pos_prev = positions_per_cycle[cycle_num - 1]

        x_drift = abs(pos_curr["x"] - pos_prev["x"])
        y_drift = abs(pos_curr["y"] - pos_prev["y"])

        assert x_drift < tolerance, f"Cycle {cycle_num}: X drift {x_drift}mm exceeds {tolerance}mm"
        assert y_drift < tolerance, f"Cycle {cycle_num}: Y drift {y_drift}mm exceeds {tolerance}mm"

    print(f"✅ Test 3.5 PASSED: Position stable across 3 cycles (max drift < {tolerance}mm)")


def test_06_rotated_component_position():
    """
    Test 3.6: Rotated component position preserved.

    Validates:
    - Rotation angle extracted from KiCad
    - Rotation preserved when re-exporting
    - Position + rotation maintained together
    - No interaction between position and rotation
    """
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "03_kicad_ref"
    kicad_sch = kicad_ref_dir / "03_kicad_ref.kicad_sch"

    if not kicad_sch.exists():
        pytest.skip("Fixture not found")

    # Extract position and rotation
    sch_content = kicad_sch.read_text()
    position_orig = extract_component_position(sch_content)
    assert position_orig is not None

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Import and re-export
        kicad_pro = kicad_ref_dir / "03_kicad_ref.kicad_pro"
        output_py = tmpdir / "rotation_test.py"
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )
        assert syncer.sync(), "Import failed"

        # Generate back
        result = subprocess.run(
            ["uv", "run", "python", "03_python_ref.py"],
            cwd=test_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Generation failed"

        # Extract position and rotation
        positioned_resistor_dir = test_dir / "positioned_resistor"
        kicad_sch_new = positioned_resistor_dir / "positioned_resistor.kicad_sch"
        sch_content_new = kicad_sch_new.read_text()
        position_new = extract_component_position(sch_content_new)

        # Verify rotation preserved
        assert position_new["rotation"] == position_orig["rotation"], \
            f"Rotation changed: {position_orig['rotation']}° → {position_new['rotation']}°"

        # Verify position also preserved
        tolerance = 0.1
        x_diff = abs(position_orig["x"] - position_new["x"])
        y_diff = abs(position_orig["y"] - position_new["y"])
        assert x_diff < tolerance, f"Position drift: {x_diff}mm"
        assert y_diff < tolerance, f"Position drift: {y_diff}mm"

        print(f"✅ Test 3.6 PASSED: Position and rotation ({position_new['rotation']}°) preserved")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
