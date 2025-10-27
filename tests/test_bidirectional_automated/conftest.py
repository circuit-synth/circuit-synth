"""
Pytest configuration and fixtures for automated bidirectional sync tests.

These tests validate Python ↔ KiCad bidirectional synchronization using
programmatic manipulation via kicad-sch-api.
"""

import tempfile
from pathlib import Path
from typing import Callable

import pytest
import kicad_sch_api as ksa


@pytest.fixture
def temp_project_dir(tmp_path):
    """
    Create temporary directory for test projects.

    Each test gets a fresh temporary directory that's automatically
    cleaned up after the test completes.

    Usage:
        def test_something(temp_project_dir):
            project_path = temp_project_dir / "my_project"
            ...
    """
    return tmp_path


@pytest.fixture
def parse_schematic():
    """
    Parse KiCad schematic file using kicad-sch-api.

    Returns a function that loads and parses a .kicad_sch file.

    Usage:
        def test_something(parse_schematic):
            sch = parse_schematic("path/to/file.kicad_sch")
            assert len(sch.components) == 1
    """
    def _parse(path):
        return ksa.Schematic(str(path))
    return _parse


@pytest.fixture
def assert_component_equal():
    """
    Helper to compare components semantically.

    Compares component properties while ignoring internal implementation
    details like UUIDs and exact positions (within tolerance).

    Usage:
        def test_something(assert_component_equal):
            assert_component_equal(comp1, comp2)
    """
    def _assert_equal(comp1, comp2, position_tolerance=0.5):
        assert comp1.reference == comp2.reference, \
            f"Reference mismatch: {comp1.reference} != {comp2.reference}"
        assert comp1.value == comp2.value, \
            f"Value mismatch: {comp1.value} != {comp2.value}"
        assert comp1.footprint == comp2.footprint, \
            f"Footprint mismatch: {comp1.footprint} != {comp2.footprint}"
        assert comp1.lib_id == comp2.lib_id, \
            f"Symbol mismatch: {comp1.lib_id} != {comp2.lib_id}"

        # Position check with tolerance
        if hasattr(comp1, 'position') and hasattr(comp2, 'position'):
            dx = abs(comp1.position[0] - comp2.position[0])
            dy = abs(comp1.position[1] - comp2.position[1])
            assert dx < position_tolerance and dy < position_tolerance, \
                f"Position mismatch: {comp1.position} != {comp2.position}"

    return _assert_equal


@pytest.fixture
def create_schematic(temp_project_dir):
    """
    Factory fixture for creating KiCad schematics.

    Creates a new schematic in the temp directory with the given name.

    Usage:
        def test_something(create_schematic):
            sch = create_schematic("my_circuit")
            sch.components.add(...)
            sch.save()
    """
    def _create(name):
        sch = ksa.create_schematic(name)
        # Save to temp directory
        sch_path = temp_project_dir / f"{name}.kicad_sch"
        sch._file_path = str(sch_path)
        return sch

    return _create
