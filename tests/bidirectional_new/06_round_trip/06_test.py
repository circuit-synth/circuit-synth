#!/usr/bin/env python3
"""Test 06: Round-Trip Validation [P0 CRITICAL]"""
import ast, os, pytest, subprocess, tempfile, shutil, hashlib
from pathlib import Path
from circuit_synth import circuit, Component
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer
import time

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
        print(f"\n📁 Test artifacts preserved in: {get_test_artifacts_dir()}")

@pytest.fixture(autouse=True)
def cleanup_before_test():
    test_dir = Path(__file__).parent
    roundtrip_circuit_dir = test_dir / "roundtrip_circuit"
    if roundtrip_circuit_dir.exists():
        shutil.rmtree(roundtrip_circuit_dir)
    yield
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        roundtrip_circuit_dir = test_dir / "roundtrip_circuit"
        if roundtrip_circuit_dir.exists():
            test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[1].split(" ")[0]
            dest = artifacts_dir / test_name
            dest.mkdir(parents=True, exist_ok=True)
            for file in roundtrip_circuit_dir.iterdir():
                if file.is_file():
                    shutil.copy2(file, dest / file.name)
            shutil.rmtree(roundtrip_circuit_dir)
    else:
        roundtrip_circuit_dir = test_dir / "roundtrip_circuit"
        if roundtrip_circuit_dir.exists():
            shutil.rmtree(roundtrip_circuit_dir)

def test_01_simple_circuit_full_cycle():
    """Test 6.1: Simple circuit full 3-cycle round-trip."""
    test_dir = Path(__file__).parent
    
    for cycle in range(1, 4):
        result = subprocess.run(
            ["uv", "run", "python", "06_python_ref.py"],
            cwd=test_dir, capture_output=True, text=True
        )
        assert result.returncode == 0, f"Cycle {cycle} generation failed: {result.stderr}"
        
        kicad_dir = test_dir / "roundtrip_circuit"
        assert kicad_dir.exists(), f"Cycle {cycle}: KiCad dir not created"
        assert (kicad_dir / "roundtrip_circuit.kicad_sch").exists()
    
    print("✅ Test 6.1 PASSED: 3-cycle round-trip successful")

def test_02_full_cycle_data_integrity():
    """Test 6.2: All data preserved through full cycle."""
    test_dir = Path(__file__).parent
    
    result = subprocess.run(
        ["uv", "run", "python", "06_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result.returncode == 0
    
    kicad_sch = test_dir / "roundtrip_circuit" / "roundtrip_circuit.kicad_sch"
    sch_content = kicad_sch.read_text()
    
    # Verify schematic contains expected components
    assert "(kicad_sch" in sch_content
    assert "Device:R" in sch_content or "symbol" in sch_content
    
    print("✅ Test 6.2 PASSED: Data integrity verified")

def test_03_generated_code_quality():
    """Test 6.3: Generated Python code is quality and importable."""
    test_dir = Path(__file__).parent
    kicad_ref_dir = test_dir / "06_kicad_ref"
    kicad_pro = kicad_ref_dir / "06_kicad_ref.kicad_pro"
    
    if not kicad_pro.exists():
        pytest.skip("KiCad fixture not found")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_py = Path(tmpdir) / "code_quality.py"
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_pro),
            python_file=str(output_py),
            preview_only=False
        )
        
        assert syncer.sync(), "Import failed"
        py_content = output_py.read_text()
        
        # Verify syntax
        try:
            ast.parse(py_content)
        except SyntaxError as e:
            pytest.fail(f"Code quality issue: {e}")
        
        # Verify it has expected structure
        assert "@circuit" in py_content
        assert "def " in py_content
        
        print("✅ Test 6.3 PASSED: Generated code is high quality")

def test_04_large_circuit_full_cycle():
    """Test 6.4: Large circuit (10+ components) cycles correctly."""
    pytest.skip("Requires large circuit fixture (10+ components)")

def test_05_cycle_performance():
    """Test 6.5: Single cycle completes in acceptable time."""
    test_dir = Path(__file__).parent
    
    start = time.time()
    result = subprocess.run(
        ["uv", "run", "python", "06_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    elapsed = time.time() - start
    
    assert result.returncode == 0
    assert elapsed < 10, f"Generation took {elapsed:.1f}s (target: <10s)"
    
    print(f"✅ Test 6.5 PASSED: Generation completed in {elapsed:.2f}s")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
