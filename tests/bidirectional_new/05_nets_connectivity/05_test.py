#!/usr/bin/env python3
"""Test 05: Nets & Connectivity"""
import ast, os, pytest, subprocess, tempfile, shutil
from pathlib import Path
from circuit_synth import circuit, Component, Net
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer

PRESERVE_ARTIFACTS = os.getenv("PRESERVE_TEST_ARTIFACTS", "").lower() in ("1", "true", "yes")

def get_test_artifacts_dir():
    test_dir = Path(__file__).parent
    artifacts_dir = test_dir / "test_artifacts"
    if PRESERVE_ARTIFACTS:
        artifacts_dir.mkdir(exist_ok=True)
    return artifacts_dir

@pytest.fixture(scope="session", autouse=True)
def setup_session():
    test_dir = Path(__file__).parent
    artifacts_dir = test_dir / "test_artifacts"
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    yield
    if PRESERVE_ARTIFACTS:
        print(f"\n📁 All test artifacts preserved in: {get_test_artifacts_dir()}")

@pytest.fixture(autouse=True)
def cleanup_before_test():
    test_dir = Path(__file__).parent
    netted_circuit_dir = test_dir / "netted_circuit"
    if netted_circuit_dir.exists():
        shutil.rmtree(netted_circuit_dir)
    yield
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        netted_circuit_dir = test_dir / "netted_circuit"
        if netted_circuit_dir.exists():
            test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[1].split(" ")[0]
            dest = artifacts_dir / test_name
            dest.mkdir(parents=True, exist_ok=True)
            for file in netted_circuit_dir.iterdir():
                if file.is_file():
                    shutil.copy2(file, dest / file.name)
            shutil.rmtree(netted_circuit_dir)
    else:
        netted_circuit_dir = test_dir / "netted_circuit"
        if netted_circuit_dir.exists():
            shutil.rmtree(netted_circuit_dir)

def test_01_generate_single_net_to_kicad():
    """Test 5.1: Generate single net to KiCad."""
    test_dir = Path(__file__).parent
    result = subprocess.run(
        ["uv", "run", "python", "05_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    
    kicad_sch = test_dir / "netted_circuit" / "netted_circuit.kicad_sch"
    assert kicad_sch.exists(), "Schematic not created"
    print("✅ Test 5.1 PASSED: Single net generated to KiCad")

def test_02_import_nets_from_kicad():
    """Test 5.2: Import nets from KiCad."""
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "05_kicad_ref"
    kicad_pro = kicad_ref_dir / "05_kicad_ref.kicad_pro"
    
    if not kicad_pro.exists():
        pytest.skip("KiCad fixture not found")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_py = Path(tmpdir) / "imported.py"
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )
        assert syncer.sync(), "Import failed"
        py_content = output_py.read_text()
        assert "@circuit" in py_content
    print("✅ Test 5.2 PASSED: Nets imported from KiCad")

def test_03_multi_node_net_preservation():
    """Test 5.3: Multi-node net preservation."""
    pytest.skip("Requires fixture with 3+ pin connections to single net")

def test_04_net_round_trip_stability():
    """Test 5.4: Net round-trip stability."""
    pytest.skip("Requires net connectivity validation after round-trip")

def test_05_multiple_nets_independence():
    """Test 5.5: Multiple nets independence."""
    pytest.skip("Requires fixture with 3+ independent nets")

def test_06_named_nets_preservation():
    """Test 5.6: Named nets preservation."""
    pytest.skip("Requires fixture with named nets (VCC, GND, etc)")

def test_07_unconnected_components():
    """Test 5.7: Unconnected components handling."""
    pytest.skip("Requires fixture with unconnected components")

def test_08_net_connectivity_verification():
    """Test 5.8: Net connectivity verification."""
    pytest.skip("Requires detailed net connectivity analysis")

def test_09_net_connectivity_changes():
    """Test 5.9: Changing net connectivity (rewiring connections).

    IMPORTANT: Tests that we can change which pins are connected to which nets.
    This is distinct from position preservation - it's about electrical topology changes.

    Example: Change a resistor from connected to GND to connected to VCC
    - Before: R1.pin2 → GND
    - After: R1.pin2 → VCC

    This test validates:
    - Net connections can be modified in Python
    - Modified connections correctly exported to KiCad schematic
    - KiCad schematic shows updated connections
    - Reimporting preserves the new connectivity
    """
    pytest.skip("Requires fixture: Create schematic with components on nets, then modify connections in Python")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
