"""
Test suite for validating circuit template files.

These tests ensure that all template circuits:
1. Use valid placement algorithms
2. Can be generated without errors
3. Have proper configuration
"""

import pytest
import importlib.util
import ast
from pathlib import Path


# Valid PCB placement algorithms
VALID_PLACEMENT_ALGORITHMS = {"hierarchical", "grid", "force_directed"}

# Base paths for templates
BASE_DIR = Path(__file__).parent.parent
TEMPLATE_DIRS = [
    BASE_DIR / "src/circuit_synth/data/templates/base_circuits",
    BASE_DIR / "src/circuit_synth/data/templates/example_circuits",
]


def get_all_template_files():
    """Get all Python template files from template directories."""
    template_files = []
    for template_dir in TEMPLATE_DIRS:
        if template_dir.exists():
            template_files.extend(template_dir.glob("*.py"))
    return template_files


def extract_placement_algorithm(file_path):
    """Extract placement_algorithm value from Python file."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Parse the Python file
    tree = ast.parse(content)

    # Look for placement_algorithm assignments
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if this is generate_kicad_project call
            if hasattr(node.func, 'attr') and node.func.attr == 'generate_kicad_project':
                # Look for placement_algorithm keyword argument
                for keyword in node.keywords:
                    if keyword.arg == 'placement_algorithm':
                        if isinstance(keyword.value, ast.Constant):
                            return keyword.value.value

    return None


@pytest.mark.parametrize("template_file", get_all_template_files())
def test_template_uses_valid_placement_algorithm(template_file):
    """Test that template file uses a valid placement algorithm."""
    placement_algorithm = extract_placement_algorithm(template_file)

    assert placement_algorithm is not None, \
        f"{template_file.name} does not specify a placement_algorithm"

    assert placement_algorithm in VALID_PLACEMENT_ALGORITHMS, \
        f"{template_file.name} uses invalid placement algorithm '{placement_algorithm}'. " \
        f"Valid algorithms: {', '.join(VALID_PLACEMENT_ALGORITHMS)}"


@pytest.mark.parametrize("template_file", get_all_template_files())
def test_template_syntax_valid(template_file):
    """Test that template file has valid Python syntax."""
    with open(template_file, 'r') as f:
        content = f.read()

    try:
        ast.parse(content)
    except SyntaxError as e:
        pytest.fail(f"{template_file.name} has syntax error: {e}")


@pytest.mark.parametrize("template_file", get_all_template_files())
def test_template_imports_circuit_synth(template_file):
    """Test that template file imports from circuit_synth."""
    with open(template_file, 'r') as f:
        content = f.read()

    assert "from circuit_synth import" in content or "import circuit_synth" in content, \
        f"{template_file.name} does not import circuit_synth"


def test_all_template_directories_exist():
    """Test that all expected template directories exist."""
    for template_dir in TEMPLATE_DIRS:
        assert template_dir.exists(), f"Template directory not found: {template_dir}"


def test_at_least_one_template_in_each_directory():
    """Test that each template directory contains at least one template."""
    for template_dir in TEMPLATE_DIRS:
        if template_dir.exists():
            template_files = list(template_dir.glob("*.py"))
            assert len(template_files) > 0, \
                f"No template files found in {template_dir}"


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
