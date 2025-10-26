#!/usr/bin/env python3
"""
Shared test utilities for bidirectional sync tests.

This module provides common functions used across all bidirectional tests:
- Running Python circuits
- Importing KiCad to Python
- Directory management
- Validation helpers

Goal: Keep individual tests simple and focused on testing ONE thing.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def clean_output_dir(output_dir: Path) -> None:
    """
    Clean and recreate an output directory.

    Args:
        output_dir: Directory to clean and recreate
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)


def run_python_circuit(
    python_file: Path,
    cwd: Optional[Path] = None
) -> Tuple[int, str, str]:
    """
    Run a Python circuit file using 'uv run python'.

    Args:
        python_file: Path to Python circuit file
        cwd: Working directory (defaults to parent of python_file)

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if cwd is None:
        cwd = python_file.parent

    result = subprocess.run(
        ["uv", "run", "python", python_file.name],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


def import_kicad_to_python(
    kicad_project: Path,
    output_py: Path
) -> Tuple[int, str, str]:
    """
    Import a KiCad project to Python using 'kicad-to-python' command.

    Args:
        kicad_project: Path to .kicad_pro file
        output_py: Path where Python file should be created

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        ["uv", "run", "kicad-to-python", str(kicad_project), str(output_py)],
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


def copy_to_output(source_file: Path, output_dir: Path, new_name: Optional[str] = None) -> Path:
    """
    Copy a file to an output directory.

    Args:
        source_file: Source file to copy
        output_dir: Destination directory
        new_name: Optional new filename (defaults to original name)

    Returns:
        Path to copied file
    """
    if new_name is None:
        new_name = source_file.name

    dest = output_dir / new_name
    shutil.copy(source_file, dest)
    return dest


# Validation Helpers

def assert_kicad_project_exists(kicad_dir: Path, project_name: str) -> Path:
    """
    Assert that a KiCad project directory and .kicad_pro file exist.

    Args:
        kicad_dir: Expected KiCad project directory
        project_name: Expected project name

    Returns:
        Path to .kicad_pro file

    Raises:
        AssertionError: If project doesn't exist or is incomplete
    """
    assert kicad_dir.exists(), f"KiCad directory not found: {kicad_dir}"

    kicad_pro = kicad_dir / f"{project_name}.kicad_pro"
    assert kicad_pro.exists(), f"KiCad project file not found: {kicad_pro}"

    kicad_sch = kicad_dir / f"{project_name}.kicad_sch"
    assert kicad_sch.exists(), f"KiCad schematic not found: {kicad_sch}"

    return kicad_pro


def assert_python_file_exists(py_file: Path) -> None:
    """
    Assert that a Python file exists and is not empty.

    Args:
        py_file: Path to Python file

    Raises:
        AssertionError: If file doesn't exist or is empty
    """
    assert py_file.exists(), f"Python file not found: {py_file}"

    content = py_file.read_text()
    assert len(content) > 0, f"Python file is empty: {py_file}"


def assert_component_in_schematic(kicad_sch: Path, reference: str) -> None:
    """
    Assert that a component with given reference exists in KiCad schematic.

    Args:
        kicad_sch: Path to .kicad_sch file
        reference: Component reference (e.g., "R1")

    Raises:
        AssertionError: If component not found
    """
    content = kicad_sch.read_text()

    # Look for property with this reference
    assert f'"Reference" "{reference}"' in content, \
        f"Component {reference} not found in schematic {kicad_sch}"


def assert_component_in_python(py_file: Path, reference: str) -> None:
    """
    Assert that a component with given reference exists in Python file.

    Args:
        py_file: Path to Python file
        reference: Component reference (e.g., "R1")

    Raises:
        AssertionError: If component not found
    """
    content = py_file.read_text()

    # Look for ref="R1" or ref='R1'
    assert f'ref="{reference}"' in content or f"ref='{reference}'" in content, \
        f"Component {reference} not found in Python file {py_file}"


def assert_component_properties(
    py_file: Path,
    reference: str,
    value: Optional[str] = None,
    footprint: Optional[str] = None
) -> None:
    """
    Assert that a component has expected properties in Python file.

    Args:
        py_file: Path to Python file
        reference: Component reference (e.g., "R1")
        value: Expected value (e.g., "10k")
        footprint: Expected footprint (e.g., "R_0603_1608Metric")

    Raises:
        AssertionError: If properties don't match
    """
    content = py_file.read_text()

    # Assert component exists
    assert_component_in_python(py_file, reference)

    # Check value if provided
    if value is not None:
        assert f'value="{value}"' in content or f"value='{value}'" in content, \
            f"Component {reference} doesn't have value={value} in {py_file}"

    # Check footprint if provided
    if footprint is not None:
        # Just check that the footprint name appears (could be partial match)
        assert footprint in content, \
            f"Component {reference} doesn't have footprint containing '{footprint}' in {py_file}"


def get_test_output_dir(test_file: Path, subdir_name: str) -> Path:
    """
    Get standardized output directory for a test.

    Args:
        test_file: Path to test file (__file__)
        subdir_name: Name of subdirectory for this test's output

    Returns:
        Path to output directory (parent_dir/generated_<subdir_name>)
    """
    test_dir = Path(test_file).parent
    return test_dir / f"generated_{subdir_name}"


def print_test_header(test_name: str) -> None:
    """Print a formatted test header."""
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    print("=" * 60)


def print_test_footer(success: bool = True) -> None:
    """Print a formatted test footer."""
    status = "✅ PASSED" if success else "❌ FAILED"
    print("=" * 60)
    print(f"Result: {status}")
    print("=" * 60 + "\n")
