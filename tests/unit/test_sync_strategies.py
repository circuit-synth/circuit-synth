"""
Unit tests for component synchronization matching strategies.

Tests the various strategies used to match components between
Python Circuit Synth and KiCad schematics during synchronization.
"""

import pytest
from unittest.mock import Mock, MagicMock
from kicad_sch_api.core.types import Point

from circuit_synth.kicad.schematic.sync_strategies import (
    UUIDMatchStrategy,
    ReferenceMatchStrategy,
    PositionRenameStrategy,
    ValueFootprintStrategy,
    ConnectionMatchStrategy,
)


class TestUUIDMatchStrategy:
    """Test UUID-based component matching strategy."""

    @pytest.fixture
    def strategy(self):
        """Create UUIDMatchStrategy with mock search engine."""
        search_engine = Mock()
        return UUIDMatchStrategy(search_engine)

    def test_match_by_uuid_simple(self, strategy):
        """Test matching components by UUID with one match."""
        # Circuit components (from Python)
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "uuid": "uuid-1234",
            }
        }

        # KiCad components
        kicad_comp = Mock()
        kicad_comp.uuid = "uuid-1234"
        kicad_components = {"R1": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {"R1": "R1"}

    def test_match_by_uuid_after_rename(self, strategy):
        """Test UUID matching detects renamed component (R1 -> R2)."""
        # Circuit component still has old reference but same UUID
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "uuid": "uuid-1234",
            }
        }

        # KiCad component was renamed to R2 but has same UUID
        kicad_comp = Mock()
        kicad_comp.uuid = "uuid-1234"
        kicad_components = {"R2": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        # Should match R1 (circuit) to R2 (KiCad) by UUID
        assert matches == {"R1": "R2"}

    def test_no_match_when_uuid_missing_in_circuit(self, strategy):
        """Test no match when circuit component has no UUID."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                # No UUID field
            }
        }

        kicad_comp = Mock()
        kicad_comp.uuid = "uuid-1234"
        kicad_components = {"R1": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_no_match_when_uuid_missing_in_kicad(self, strategy):
        """Test no match when KiCad component has no UUID attribute."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "uuid": "uuid-1234",
            }
        }

        # KiCad component without uuid attribute
        kicad_comp = Mock(spec=[])  # No attributes
        kicad_components = {"R1": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_no_match_when_uuids_differ(self, strategy):
        """Test no match when UUIDs don't match."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "uuid": "uuid-1111",
            }
        }

        kicad_comp = Mock()
        kicad_comp.uuid = "uuid-2222"
        kicad_components = {"R1": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_multiple_components_matched_by_uuid(self, strategy):
        """Test matching multiple components by UUID."""
        circuit_components = {
            "R1": {"reference": "R1", "uuid": "uuid-r1"},
            "R2": {"reference": "R2", "uuid": "uuid-r2"},
            "C1": {"reference": "C1", "uuid": "uuid-c1"},
        }

        kicad_r1 = Mock()
        kicad_r1.uuid = "uuid-r1"
        kicad_r2 = Mock()
        kicad_r2.uuid = "uuid-r2"
        kicad_c1 = Mock()
        kicad_c1.uuid = "uuid-c1"

        kicad_components = {
            "R1": kicad_r1,
            "R2": kicad_r2,
            "C1": kicad_c1,
        }

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {"R1": "R1", "R2": "R2", "C1": "C1"}

    def test_partial_matching_some_components_have_uuid(self, strategy):
        """Test matching when only some components have UUIDs."""
        circuit_components = {
            "R1": {"reference": "R1", "uuid": "uuid-r1"},
            "R2": {"reference": "R2"},  # No UUID
            "C1": {"reference": "C1", "uuid": "uuid-c1"},
        }

        kicad_r1 = Mock()
        kicad_r1.uuid = "uuid-r1"
        kicad_r2 = Mock()
        kicad_r2.uuid = "uuid-r2"
        kicad_c1 = Mock()
        kicad_c1.uuid = "uuid-c1"

        kicad_components = {
            "R1": kicad_r1,
            "R2": kicad_r2,
            "C1": kicad_c1,
        }

        matches = strategy.match_components(circuit_components, kicad_components)

        # Only R1 and C1 should match (R2 has no UUID in circuit)
        assert matches == {"R1": "R1", "C1": "C1"}


class TestPositionRenameStrategy:
    """Test position-based rename detection strategy."""

    @pytest.fixture
    def strategy(self):
        """Create PositionRenameStrategy with mock search engine."""
        search_engine = Mock()
        return PositionRenameStrategy(search_engine)

    def test_match_by_position_after_rename(self, strategy):
        """Test detecting rename when component at same position."""
        # Circuit component expects R1
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(100.0, 50.0),
            }
        }

        # KiCad component renamed to R2 but same position/properties
        kicad_comp = Mock()
        kicad_comp.position = Point(100.0, 50.0)
        kicad_comp.lib_id = "Device:R"
        kicad_comp.value = "10k"
        kicad_comp.footprint = "R_0603_1608Metric"

        kicad_components = {"R2": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        # Should match R1 -> R2 based on position+properties
        assert matches == {"R1": "R2"}

    def test_no_match_when_position_differs(self, strategy):
        """Test no match when position is outside tolerance."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(100.0, 50.0),
            }
        }

        # Different position (>2.54mm away)
        kicad_comp = Mock()
        kicad_comp.position = Point(110.0, 50.0)  # 10mm away
        kicad_comp.lib_id = "Device:R"
        kicad_comp.value = "10k"
        kicad_comp.footprint = "R_0603_1608Metric"

        kicad_components = {"R2": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_no_match_when_value_differs(self, strategy):
        """Test no match when value differs."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(100.0, 50.0),
            }
        }

        # Same position but different value
        kicad_comp = Mock()
        kicad_comp.position = Point(100.0, 50.0)
        kicad_comp.lib_id = "Device:R"
        kicad_comp.value = "20k"  # Different!
        kicad_comp.footprint = "R_0603_1608Metric"

        kicad_components = {"R2": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_no_match_when_symbol_differs(self, strategy):
        """Test no match when symbol (lib_id) differs."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(100.0, 50.0),
            }
        }

        # Same position but different symbol
        kicad_comp = Mock()
        kicad_comp.position = Point(100.0, 50.0)
        kicad_comp.lib_id = "Device:C"  # Capacitor instead of resistor!
        kicad_comp.value = "10k"
        kicad_comp.footprint = "R_0603_1608Metric"

        kicad_components = {"C1": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_match_within_position_tolerance(self, strategy):
        """Test matching when position within 2.54mm tolerance."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                "footprint": "R_0603_1608Metric",
                "position": Point(100.0, 50.0),
            }
        }

        # Position slightly off but within tolerance (2.0mm away)
        kicad_comp = Mock()
        kicad_comp.position = Point(101.5, 50.5)  # ~2.12mm diagonal
        kicad_comp.lib_id = "Device:R"
        kicad_comp.value = "10k"
        kicad_comp.footprint = "R_0603_1608Metric"

        kicad_components = {"R2": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {"R1": "R2"}

    def test_skip_when_reference_already_matches(self, strategy):
        """Test skipping when reference already exists in KiCad (already matched by ReferenceMatchStrategy)."""
        # Circuit expects R1
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                "position": Point(100.0, 50.0),
            }
        }

        # KiCad has R1 at same position
        kicad_comp = Mock()
        kicad_comp.position = Point(100.0, 50.0)
        kicad_comp.lib_id = "Device:R"
        kicad_comp.value = "10k"

        kicad_components = {"R1": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        # Should not match (reference already exists, handled by ReferenceMatchStrategy)
        assert matches == {}

    def test_no_match_when_position_missing(self, strategy):
        """Test no match when circuit component has no position."""
        circuit_components = {
            "R1": {
                "reference": "R1",
                "value": "10k",
                "symbol": "Device:R",
                # No position field
            }
        }

        kicad_comp = Mock()
        kicad_comp.position = Point(100.0, 50.0)
        kicad_comp.lib_id = "Device:R"
        kicad_comp.value = "10k"

        kicad_components = {"R2": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}


class TestReferenceMatchStrategy:
    """Test reference-based component matching strategy."""

    @pytest.fixture
    def strategy(self):
        """Create ReferenceMatchStrategy with mock search engine."""
        search_engine = Mock()
        return ReferenceMatchStrategy(search_engine)

    def test_exact_reference_match(self, strategy):
        """Test matching by exact reference designator."""
        circuit_components = {
            "R1": {"reference": "R1", "value": "10k"}
        }

        # Mock search results
        search_result = Mock()
        search_result.reference = "R1"
        strategy.search_engine.search_components.return_value = [search_result]

        kicad_comp = Mock()
        kicad_components = {"R1": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {"R1": "R1"}
        strategy.search_engine.search_components.assert_called_once_with(reference="R1")

    def test_no_match_when_reference_differs(self, strategy):
        """Test no match when references differ."""
        circuit_components = {
            "R1": {"reference": "R1", "value": "10k"}
        }

        # Search returns R2, not R1
        search_result = Mock()
        search_result.reference = "R2"
        strategy.search_engine.search_components.return_value = [search_result]

        kicad_comp = Mock()
        kicad_components = {"R2": kicad_comp}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}

    def test_no_match_when_not_found(self, strategy):
        """Test no match when component not found in search."""
        circuit_components = {
            "R1": {"reference": "R1", "value": "10k"}
        }

        # No search results
        strategy.search_engine.search_components.return_value = []

        kicad_components = {}

        matches = strategy.match_components(circuit_components, kicad_components)

        assert matches == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
