#!/usr/bin/env python3
"""Test 01: Blank circuit generation and import"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir, run_python_circuit, import_kicad_to_python,
    assert_kicad_project_exists, get_test_output_dir,
    print_test_header, print_test_footer
)

def test_blank():
    """Test: Blank circuit with no components"""
    print_test_header("01: Blank Circuit")
    
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "01_blank")
    clean_output_dir(output_dir)
    
    # Create blank circuit
    blank_py = output_dir / "blank.py"
    blank_py.write_text('''#!/usr/bin/env python3
from circuit_synth import circuit

@circuit(name="blank")
def blank():
    """Blank circuit."""
    pass

if __name__ == "__main__":
    circuit_obj = blank()
    circuit_obj.generate_kicad_project(project_name="blank")
''')
    
    # Generate KiCad
    exit_code, _, stderr = run_python_circuit(blank_py)
    assert exit_code == 0, f"Generation failed: {stderr}"
    
    kicad_dir = output_dir / "blank"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "blank")
    
    # Check JSON has correct name
    json_file = kicad_dir / "blank.json"
    json_content = json_file.read_text()
    assert '"name": "blank"' in json_content, "JSON has wrong name"
    
    print("✅ Blank circuit works")
    print_test_footer(success=True)

if __name__ == "__main__":
    test_blank()
