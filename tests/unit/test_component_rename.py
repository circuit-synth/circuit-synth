"""
Unit tests for component rename detection in bidirectional sync.

Tests the PositionRenameStrategy and rename_component functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock
from kicad_sch_api.core.types import Point, SchematicSymbol

from circuit_synth.kicad.schematic.sync_strategies import PositionRenameStrategy
from circuit_synth.kicad.schematic.component_manager import ComponentManager
from circuit_synth.kicad.schematic.search_engine import SearchEngine


class TestPositionRenameStrategy:
    """Test position-based rename detection strategy."""

    @pytest.fixture
    def search_engine(self):
        """Mock search engine."""
        return Mock(spec=SearchEngine)

    @pytest.fixture
    def strategy(self, search_engine):
        """Create PositionRenameStrategy instance."""
        return PositionRenameStrategy(search_engine)

    def test_detects_rename_same_position(self, strategy):
        """Test that strategy detects rename when component at same position."""
        # Circuit has R2 at position (30.48, 35.56)
        circuit_components = {
            "R2_uuid": {
                "reference": "R2",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(30.48, 35.56),
            }
        }

        # KiCad has R1 at same position
        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "10k"
        kicad_r1.lib_id = "Device:R"
        kicad_r1.footprint = "R_0603_1608Metric"
        kicad_r1.position = Point(30.48, 35.56)

        kicad_components = {"R1": kicad_r1}

        # Should match R2 (circuit) to R1 (kicad) - indicating a rename
        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {"R2_uuid": "R1"}

    def test_no_match_different_position(self, strategy):
        """Test that strategy doesn't match components at different positions."""
        circuit_components = {
            "R2_uuid": {
                "reference": "R2",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(30.48, 35.56),
            }
        }

        # KiCad component at different position (>2.54mm away)
        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "10k"
        kicad_r1.lib_id = "Device:R"
        kicad_r1.footprint = "R_0603_1608Metric"
        kicad_r1.position = Point(50.0, 50.0)  # Far away

        kicad_components = {"R1": kicad_r1}

        matches = strategy.match_components(circuit_components, kicad_components)

        # Should not match due to position difference
        assert matches == {}

    def test_no_match_different_value(self, strategy):
        """Test that strategy doesn't match if value differs."""
        circuit_components = {
            "R2_uuid": {
                "reference": "R2",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(30.48, 35.56),
            }
        }

        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "4.7k"  # Different value
        kicad_r1.lib_id = "Device:R"
        kicad_r1.footprint = "R_0603_1608Metric"
        kicad_r1.position = Point(30.48, 35.56)

        kicad_components = {"R1": kicad_r1}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_no_match_different_symbol(self, strategy):
        """Test that strategy doesn't match if symbol differs."""
        circuit_components = {
            "C1_uuid": {
                "reference": "C1",
                "value": "10uF",
                "symbol": "Device:C",
                "footprint": "C_0603_1608Metric",
                "position": Point(30.48, 35.56),
            }
        }

        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "10uF"
        kicad_r1.lib_id = "Device:R"  # Different symbol
        kicad_r1.footprint = "C_0603_1608Metric"
        kicad_r1.position = Point(30.48, 35.56)

        kicad_components = {"R1": kicad_r1}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_position_tolerance(self, strategy):
        """Test that position matching uses 2.54mm tolerance."""
        circuit_components = {
            "R2_uuid": {
                "reference": "R2",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(30.48, 35.56),
            }
        }

        # Component within tolerance (2.0mm away)
        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "10k"
        kicad_r1.lib_id = "Device:R"
        kicad_r1.footprint = "R_0603_1608Metric"
        kicad_r1.position = Point(31.0, 36.0)  # 2mm away

        kicad_components = {"R1": kicad_r1}

        matches = strategy.match_components(circuit_components, kicad_components)

        # Should match within tolerance
        assert matches == {"R2_uuid": "R1"}

    def test_skips_exact_reference_match(self, strategy):
        """Test that strategy skips components with matching references."""
        # Circuit has R1
        circuit_components = {
            "R1_uuid": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(30.48, 35.56),
            }
        }

        # KiCad also has R1 at same position
        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "10k"
        kicad_r1.lib_id = "Device:R"
        kicad_r1.footprint = "R_0603_1608Metric"
        kicad_r1.position = Point(30.48, 35.56)

        kicad_components = {"R1": kicad_r1}

        matches = strategy.match_components(circuit_components, kicad_components)

        # Should not match because reference is the same (handled by ReferenceMatchStrategy)
        assert matches == {}

    def test_handles_multiple_components(self, strategy):
        """Test matching multiple renamed components."""
        circuit_components = {
            "R2_uuid": {
                "reference": "R2",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(30.48, 35.56),
            },
            "C2_uuid": {
                "reference": "C2",
                "value": "10uF",
                "symbol": "Device:C",
                "footprint": "C_0603_1608Metric",
                "position": Point(50.0, 40.0),
            },
        }

        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "10k"
        kicad_r1.lib_id = "Device:R"
        kicad_r1.footprint = "R_0603_1608Metric"
        kicad_r1.position = Point(30.48, 35.56)

        kicad_c1 = Mock(spec=SchematicSymbol)
        kicad_c1.reference = "C1"
        kicad_c1.value = "10uF"
        kicad_c1.lib_id = "Device:C"
        kicad_c1.footprint = "C_0603_1608Metric"
        kicad_c1.position = Point(50.0, 40.0)

        kicad_components = {"R1": kicad_r1, "C1": kicad_c1}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {"R2_uuid": "R1", "C2_uuid": "C1"}

    def test_no_match_missing_position(self, strategy):
        """Test that components without position data are skipped."""
        circuit_components = {
            "R2_uuid": {
                "reference": "R2",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                # Missing position
            }
        }

        kicad_r1 = Mock(spec=SchematicSymbol)
        kicad_r1.reference = "R1"
        kicad_r1.value = "10k"
        kicad_r1.lib_id = "Device:R"
        kicad_r1.footprint = "R_0603_1608Metric"
        kicad_r1.position = Point(30.48, 35.56)

        kicad_components = {"R1": kicad_r1}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}


class TestComponentManagerRename:
    """Test ComponentManager.rename_component() method."""

    @pytest.fixture
    def schematic(self):
        """Mock schematic."""
        schematic = Mock()
        schematic.components = []
        return schematic

    @pytest.fixture
    def component_manager(self, schematic):
        """Create ComponentManager instance."""
        return ComponentManager(schematic)

    def test_rename_component_success(self, component_manager):
        """Test successful component rename."""
        # Add a component with ref R1
        component_manager._component_index["R1"] = Mock(reference="R1")

        result = component_manager.rename_component("R1", "R2")

        assert result is True
        assert "R1" not in component_manager._component_index
        assert "R2" in component_manager._component_index
        assert component_manager._component_index["R2"].reference == "R2"

    def test_rename_component_old_not_found(self, component_manager):
        """Test rename fails when old reference doesn't exist."""
        result = component_manager.rename_component("R1", "R2")

        assert result is False

    def test_rename_component_new_already_exists(self, component_manager):
        """Test rename fails when new reference already exists."""
        component_manager._component_index["R1"] = Mock(reference="R1")
        component_manager._component_index["R2"] = Mock(reference="R2")

        result = component_manager.rename_component("R1", "R2")

        assert result is False
        # R1 should still exist
        assert "R1" in component_manager._component_index

    def test_rename_updates_internal_index(self, component_manager):
        """Test that rename updates the internal component index correctly."""
        component = Mock(reference="R1")
        component_manager._component_index["R1"] = component

        component_manager.rename_component("R1", "R100")

        # Old reference gone
        assert "R1" not in component_manager._component_index
        # New reference present
        assert "R100" in component_manager._component_index
        # Same component object
        assert component_manager._component_index["R100"] is component
        # Reference updated
        assert component.reference == "R100"
