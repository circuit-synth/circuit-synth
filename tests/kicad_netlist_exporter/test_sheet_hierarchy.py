import json
import os
import tempfile
from pathlib import Path

import pytest

from circuit_synth.kicad.sheet_hierarchy_manager import SheetHierarchyManager

CIRCUIT4_PATH = Path("tests/test_data/kicad9/kicad_projects/circuit4")


@pytest.fixture
def circuit4_data():
    """Create test data from circuit4 project structure."""
    return {
        "sheets": [
            {
                "uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "name": "Root",
                "root": True,
                "path": "/",
            },
            {
                "uuid": "298e8e74-5115-49a3-bd66-33f5e5afb060",
                "name": "usb",
                "parent_uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "path": "/usb",
            },
            {
                "uuid": "851d6119-49c7-43cf-ae69-8f9f82de33a0",
                "name": "regulator",
                "parent_uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "path": "/regulator",
            },
            {
                "uuid": "59c824d6-f757-4bdd-b1f0-c05be6b6ad73",
                "name": "led",
                "parent_uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "path": "/led",
            },
            {
                "uuid": "5533446b-ffe2-4200-984e-77bf5083f9ae",
                "name": "light_sensor",
                "parent_uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "path": "/light_sensor",
            },
        ]
    }


@pytest.fixture
def circuit4_pro():
    """Path to circuit4.kicad_pro file."""
    return str(CIRCUIT4_PATH / "circuit4.kicad_pro")


def test_parse_hierarchy_from_file(circuit4_pro):
    """Test parsing sheet hierarchy from circuit4.kicad_pro file."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_hierarchy(circuit4_pro)

    # Verify root sheet
    assert manager.root is not None
    assert manager.root.uuid == "80aeb67b-8f3b-4433-8a1c-8064bd60853c"
    assert manager.root.name == "Root"
    assert len(manager.root.children) == 4

    # Verify children
    child_names = {child.name for child in manager.root.children}
    assert child_names == {"usb", "regulator", "led", "light_sensor"}

    # Verify specific child
    usb = next(child for child in manager.root.children if child.name == "usb")
    assert usb.uuid == "298e8e74-5115-49a3-bd66-33f5e5afb060"
    assert usb.path == "/usb"


def test_parse_hierarchy_from_data(circuit4_data):
    """Test parsing sheet hierarchy from data structure."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_data(circuit4_data["sheets"])

    # Verify root sheet
    assert manager.root is not None
    assert manager.root.uuid == "80aeb67b-8f3b-4433-8a1c-8064bd60853c"
    assert manager.root.name == "Root"
    assert len(manager.root.children) == 4


def test_sheet_order(circuit4_data):
    """Test getting ordered list of sheet UUIDs."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_data(circuit4_data["sheets"])

    order = manager.get_sheet_order()
    assert len(order) == 5  # Root + 4 children
    assert order[0] == "80aeb67b-8f3b-4433-8a1c-8064bd60853c"  # Root should be first

    # Verify all sheets are present
    expected_uuids = {sheet["uuid"] for sheet in circuit4_data["sheets"]}
    assert set(order) == expected_uuids


def test_sheet_paths(circuit4_data):
    """Test getting map of paths to UUIDs."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_data(circuit4_data["sheets"])

    paths = manager.get_sheet_paths()
    assert len(paths) == 5  # Root + 4 children
    assert paths["root"] == "80aeb67b-8f3b-4433-8a1c-8064bd60853c"
    assert paths["root/usb"] == "298e8e74-5115-49a3-bd66-33f5e5afb060"
    assert paths["root/regulator"] == "851d6119-49c7-43cf-ae69-8f9f82de33a0"
    assert paths["root/led"] == "59c824d6-f757-4bdd-b1f0-c05be6b6ad73"
    assert paths["root/light_sensor"] == "5533446b-ffe2-4200-984e-77bf5083f9ae"


def test_validate_hierarchy_valid(circuit4_data):
    """Test hierarchy validation with valid structure."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_data(circuit4_data["sheets"])
    assert manager.validate_hierarchy() is True


def test_validate_hierarchy_cycle():
    """Test hierarchy validation with cyclic structure."""
    data = {
        "sheets": [
            {
                "uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "name": "Root",
                "root": True,
            },
            {
                "uuid": "298e8e74-5115-49a3-bd66-33f5e5afb060",
                "name": "child",
                "parent_uuid": "5533446b-ffe2-4200-984e-77bf5083f9ae",
            },
            {
                "uuid": "5533446b-ffe2-4200-984e-77bf5083f9ae",
                "name": "grandchild",
                "parent_uuid": "298e8e74-5115-49a3-bd66-33f5e5afb060",
            },
        ]
    }

    manager = SheetHierarchyManager(test_mode=True)
    with pytest.raises(ValueError, match="Cycle detected"):
        manager.parse_sheet_data(data["sheets"])


def test_validate_hierarchy_disconnected():
    """Test hierarchy validation with disconnected sheets."""
    data = {
        "sheets": [
            {
                "uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "name": "Root",
                "root": True,
            },
            {
                "uuid": "298e8e74-5115-49a3-bd66-33f5e5afb060",
                "name": "disconnected",
                # Missing parent_uuid makes this sheet disconnected
            },
        ]
    }

    manager = SheetHierarchyManager(test_mode=True)
    with pytest.raises(ValueError, match="Non-root sheet missing parent_uuid"):
        manager.parse_sheet_data(data["sheets"])


def test_validate_hierarchy_invalid_parent():
    """Test hierarchy validation with invalid parent reference."""
    data = {
        "sheets": [
            {
                "uuid": "80aeb67b-8f3b-4433-8a1c-8064bd60853c",
                "name": "Root",
                "root": True,
            },
            {
                "uuid": "298e8e74-5115-49a3-bd66-33f5e5afb060",
                "name": "child",
                "parent_uuid": "nonexistent-uuid",
            },
        ]
    }

    manager = SheetHierarchyManager(test_mode=True)
    with pytest.raises(ValueError, match="Invalid parent UUID"):
        manager.parse_sheet_data(data["sheets"])


@pytest.fixture
def complex_kicad_pro():
    """Create test data matching real KiCad project structure."""
    data = {
        "sheets": [
            {
                "uuid": "root-uuid",
                "name": "root",
                "root": True,
                "path": "/",
                "tstamps": "/",
            },
            {
                "uuid": "e6f5f316-cb92-4d26-9a5c-0bb6c841d4b0",
                "name": "esp32",
                "parent_uuid": "root-uuid",
                "path": "/esp32",
                "tstamps": "/e6f5f316-cb92-4d26-9a5c-0bb6c841d4b0/",
            },
            {
                "uuid": "2f4f6a02-1a48-4022-bfc4-46247ef3684a",
                "name": "debug_header",
                "parent_uuid": "e6f5f316-cb92-4d26-9a5c-0bb6c841d4b0",
                "path": "/esp32/debug_header",
                "tstamps": "/e6f5f316-cb92-4d26-9a5c-0bb6c841d4b0/2f4f6a02-1a48-4022-bfc4-46247ef3684a/",
            },
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".kicad_pro", delete=False) as f:
        json.dump(data, f)
        return f.name


def test_complex_hierarchy_parsing(complex_kicad_pro):
    """Test parsing complex hierarchical structure."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_hierarchy(complex_kicad_pro)

    # Verify root sheet
    assert manager.root is not None
    assert manager.root.uuid == "root-uuid"
    assert manager.root.name == "root"
    assert len(manager.root.children) == 1

    # Verify esp32 sheet
    esp32 = manager.root.children[0]
    assert esp32.uuid == "e6f5f316-cb92-4d26-9a5c-0bb6c841d4b0"
    assert esp32.name == "esp32"
    assert len(esp32.children) == 1

    # Verify debug_header sheet
    debug_header = esp32.children[0]
    assert debug_header.uuid == "2f4f6a02-1a48-4022-bfc4-46247ef3684a"
    assert debug_header.name == "debug_header"
    assert debug_header.path == "/esp32/debug_header"


def test_uuid_validation():
    """Test UUID format validation."""
    data = {
        "sheets": [
            {
                "uuid": "invalid-uuid",  # Invalid UUID format
                "name": "root",
                "root": True,
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".kicad_pro", delete=False) as f:
        json.dump(data, f)

    manager = SheetHierarchyManager(test_mode=True)
    with pytest.raises(ValueError, match="Invalid UUID format"):
        manager.parse_sheet_hierarchy(f.name)

    os.unlink(f.name)


def test_timestamp_handling(complex_kicad_pro):
    """Test sheet timestamp handling."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_hierarchy(complex_kicad_pro)

    # Verify timestamp format and hierarchy
    paths = manager.get_sheet_paths()
    for path, uuid in paths.items():
        if path == "root":
            assert manager._uuid_map[uuid].path == "/"
        elif path == "root/esp32":
            assert manager._uuid_map[uuid].path == "/esp32"
        elif path == "root/esp32/debug_header":
            assert manager._uuid_map[uuid].path == "/esp32/debug_header"


def test_malformed_data_handling():
    """Test handling of malformed sheet data."""
    # Test missing required fields
    data = {"sheets": [{"name": "root", "root": True}]}  # Missing uuid

    with tempfile.NamedTemporaryFile(mode="w", suffix=".kicad_pro", delete=False) as f:
        json.dump(data, f)

    manager = SheetHierarchyManager(test_mode=True)
    with pytest.raises(ValueError, match="Missing required field: uuid"):
        manager.parse_sheet_hierarchy(f.name)

    os.unlink(f.name)

    # Test invalid parent reference
    data = {
        "sheets": [
            {"uuid": "root-uuid", "name": "root", "root": True},
            {
                "uuid": "child-uuid",
                "name": "child",
                "parent_uuid": "nonexistent-uuid",  # Invalid parent reference
            },
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".kicad_pro", delete=False) as f:
        json.dump(data, f)

    manager = SheetHierarchyManager(test_mode=True)
    with pytest.raises(ValueError, match="Invalid parent UUID"):
        manager.parse_sheet_hierarchy(f.name)

    os.unlink(f.name)


def test_utility_methods(complex_kicad_pro):
    """Test utility methods for path and sheet manipulation."""
    manager = SheetHierarchyManager()
    manager.parse_sheet_hierarchy(complex_kicad_pro)

    # Test path normalization
    assert manager.normalize_path("esp32/debug_header") == "/esp32/debug_header"
    assert manager.normalize_path("/esp32//debug_header/") == "/esp32/debug_header"
    assert manager.normalize_path("/") == "/"

    # Test sheet lookup by path
    debug_header = manager.get_sheet_by_path("/esp32/debug_header")
    assert debug_header is not None
    assert debug_header.uuid == "2f4f6a02-1a48-4022-bfc4-46247ef3684a"

    # Test sheet lookup by UUID
    esp32 = manager.get_sheet_by_uuid("e6f5f316-cb92-4d26-9a5c-0bb6c841d4b0")
    assert esp32 is not None
    assert esp32.name == "esp32"

    # Test parent/child relationships
    parent = manager.get_parent_sheet(debug_header.uuid)
    assert parent == esp32

    children = manager.get_child_sheets(esp32.uuid)
    assert len(children) == 1
    assert children[0] == debug_header

    # Test non-existent sheets
    assert manager.get_sheet_by_path("/nonexistent") is None
    assert manager.get_sheet_by_uuid("nonexistent-uuid") is None
    assert manager.get_parent_sheet("root-uuid") is None
    assert manager.get_child_sheets("nonexistent-uuid") == []


def test_utility_methods(circuit4_data):
    """Test utility methods for path and sheet manipulation."""
    manager = SheetHierarchyManager(test_mode=True)
    manager.parse_sheet_data(circuit4_data["sheets"])

    # Test path normalization
    assert manager.normalize_path("usb") == "/usb"
    assert manager.normalize_path("/usb/") == "/usb"
    assert manager.normalize_path("//usb//") == "/usb"

    # Test sheet lookup by path
    usb = manager.get_sheet_by_path("/usb")
    assert usb is not None
    assert usb.uuid == "298e8e74-5115-49a3-bd66-33f5e5afb060"

    # Test sheet lookup by UUID
    led = manager.get_sheet_by_uuid("59c824d6-f757-4bdd-b1f0-c05be6b6ad73")
    assert led is not None
    assert led.name == "led"

    # Test parent/child relationships
    root = manager.root
    children = manager.get_child_sheets(root.uuid)
    assert len(children) == 4

    for child in children:
        parent = manager.get_parent_sheet(child.uuid)
        assert parent == root
