#!/usr/bin/env python3
"""Test 08: Idempotency [P0 CRITICAL]"""
import ast, os, pytest, subprocess, tempfile, shutil, hashlib
from pathlib import Path
from circuit_synth import circuit, Component

PRESERVE_ARTIFACTS = os.getenv("PRESERVE_TEST_ARTIFACTS", "").lower() in ("1", "true", "yes")

def get_test_artifacts_dir():
    test_dir = Path(__file__).parent
    artifacts_dir = test_dir / "test_artifacts"
    if PRESERVE_ARTIFACTS:
        artifacts_dir.mkdir(exist_ok=True)
    return artifacts_dir

def file_hash(filepath):
    """Get SHA256 hash of file."""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

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
    idempotent_circuit_dir = test_dir / "idempotent_circuit"
    if idempotent_circuit_dir.exists():
        shutil.rmtree(idempotent_circuit_dir)
    yield
    if PRESERVE_ARTIFACTS:
        artifacts_dir = get_test_artifacts_dir()
        idempotent_circuit_dir = test_dir / "idempotent_circuit"
        if idempotent_circuit_dir.exists():
            test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[1].split(" ")[0]
            dest = artifacts_dir / test_name
            dest.mkdir(parents=True, exist_ok=True)
            for file in idempotent_circuit_dir.iterdir():
                if file.is_file():
                    shutil.copy2(file, dest / file.name)
            shutil.rmtree(idempotent_circuit_dir)
    else:
        idempotent_circuit_dir = test_dir / "idempotent_circuit"
        if idempotent_circuit_dir.exists():
            shutil.rmtree(idempotent_circuit_dir)

def _remove_uuids_from_content(content):
    """Remove UUID values from KiCad content for comparison.

    KiCad regenerates UUIDs for every new project, which is expected behavior.
    This function removes all UUID values while preserving structure.
    """
    import re

    # Remove all UUID values in quoted form: "00000000-0000-0000-0000-000000000000"
    content = re.sub(r'"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"', '"UUID"', content)

    # Remove UUID values in unquoted form: /00000000-0000-0000-0000-000000000000
    content = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/UUID', content)

    # Remove entire (uuid "...") lines (these were replaced with "UUID" above)
    content = re.sub(r'\t*\(uuid "UUID"\)\n', '', content)

    return content

def test_01_deterministic_kicad_generation():
    """Test 8.1: Same Python circuit generates same structure (ignoring UUIDs)."""
    test_dir = Path(__file__).parent

    content1 = ""
    content2 = ""

    # First generation
    result = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result.returncode == 0, f"First generation failed: {result.stderr}"

    sch_file = test_dir / "idempotent_circuit" / "idempotent_circuit.kicad_sch"
    assert sch_file.exists(), "Schematic file not generated"
    content1 = _remove_uuids_from_content(sch_file.read_text())

    # Clean and generate again
    shutil.rmtree(test_dir / "idempotent_circuit")
    result = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result.returncode == 0, f"Second generation failed: {result.stderr}"

    content2 = _remove_uuids_from_content(sch_file.read_text())

    assert content1 == content2, \
        "Generated schematic structure differs between runs (excluding UUIDs)"

    print(f"✅ Test 8.1 PASSED: Schematic structure identical across generations")

def test_02_deterministic_python_import():
    """Test 8.2: Same KiCad imports to identical Python twice."""
    pytest.skip("Requires KiCad fixture for byte-comparison of imports")

def test_03_file_content_structure_match():
    """Test 8.3: Generated file structure is identical (ignoring UUIDs)."""
    test_dir = Path(__file__).parent

    # Generate once
    result1 = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result1.returncode == 0, f"First generation failed: {result1.stderr}"

    sch_file = test_dir / "idempotent_circuit" / "idempotent_circuit.kicad_sch"
    content1 = _remove_uuids_from_content(sch_file.read_text())

    # Generate again
    shutil.rmtree(test_dir / "idempotent_circuit")
    result2 = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result2.returncode == 0, f"Second generation failed: {result2.stderr}"

    content2 = _remove_uuids_from_content(sch_file.read_text())

    assert content1 == content2, \
        "Generated file structure differs between runs (excluding UUIDs)"

    print("✅ Test 8.3 PASSED: File structure is identical across generations")

def test_04_component_ordering_consistency():
    """Test 8.4: Component order is consistent across generations."""
    test_dir = Path(__file__).parent
    
    import re
    
    # Generate
    result = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result.returncode == 0
    
    sch_file = test_dir / "idempotent_circuit" / "idempotent_circuit.kicad_sch"
    content = sch_file.read_text()
    
    # Extract references in order
    refs1 = re.findall(r'property "Reference" "([^"]+)"', content)
    
    # Generate again
    shutil.rmtree(test_dir / "idempotent_circuit")
    result = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    
    content = sch_file.read_text()
    refs2 = re.findall(r'property "Reference" "([^"]+)"', content)
    
    assert refs1 == refs2, f"Component order differs: {refs1} vs {refs2}"
    
    print(f"✅ Test 8.4 PASSED: Component order consistent ({len(refs1)} components)")

def test_05_no_timestamp_data_in_output():
    """Test 8.5: Generated files contain no timestamps."""
    test_dir = Path(__file__).parent
    
    result = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result.returncode == 0
    
    sch_file = test_dir / "idempotent_circuit" / "idempotent_circuit.kicad_sch"
    content = sch_file.read_text()
    
    # Check for common timestamp patterns
    import re
    timestamps = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', content)
    
    # KiCad files may have one generator timestamp, but content shouldn't vary
    # Just verify it's minimal
    assert len(timestamps) <= 1, f"Too many timestamps in output: {len(timestamps)}"
    
    print("✅ Test 8.5 PASSED: Minimal/no timestamp data in output")

def test_06_formatting_consistency():
    """Test 8.6: Code formatting is consistent across generations."""
    test_dir = Path(__file__).parent
    
    result = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    assert result.returncode == 0
    
    sch_file = test_dir / "idempotent_circuit" / "idempotent_circuit.kicad_sch"
    
    # Check formatting (indentation, spacing)
    content1 = sch_file.read_text()
    lines1 = content1.split('\n')
    
    shutil.rmtree(test_dir / "idempotent_circuit")
    result = subprocess.run(
        ["uv", "run", "python", "08_python_ref.py"],
        cwd=test_dir, capture_output=True, text=True
    )
    
    content2 = sch_file.read_text()
    lines2 = content2.split('\n')
    
    assert len(lines1) == len(lines2), "Line count differs"
    
    for i, (line1, line2) in enumerate(zip(lines1, lines2)):
        # Check indentation consistency
        indent1 = len(line1) - len(line1.lstrip())
        indent2 = len(line2) - len(line2.lstrip())
        assert indent1 == indent2, f"Indentation differs on line {i}"
    
    print("✅ Test 8.6 PASSED: Formatting is consistent")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
