"""
Unit tests for orthogonal routing feature (PR #230).

Tests the routing_style and via_size parameters in DSNExporter.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from circuit_synth.pcb.routing.dsn_exporter import DSNExporter, DSNLayer
from circuit_synth.pcb.pcb_board import PCBBoard
from circuit_synth.pcb.types import Point, Line


class TestOrthogonalRoutingParameters:
    """Test orthogonal routing parameter handling."""

    def test_routing_style_none_default_behavior(self):
        """Test that routing_style=None uses default layer directions."""
        # Create mock PCB board
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Create exporter without routing_style
        exporter = DSNExporter(board, routing_style=None, via_size=None)
        exporter._extract_layers()

        # Should use default horizontal/vertical pattern
        assert len(exporter.layers) == 2
        assert exporter.layers[0].name == "front"
        assert exporter.layers[0].direction == "horizontal"
        assert exporter.layers[1].name == "back"
        assert exporter.layers[1].direction == "vertical"

    def test_routing_style_orthogonal_sets_all_layers(self):
        """Test that routing_style='orthogonal' sets all layers to orthogonal."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Create exporter with orthogonal routing
        exporter = DSNExporter(board, routing_style="orthogonal", via_size=None)
        exporter._extract_layers()

        # All layers should be orthogonal
        assert len(exporter.layers) == 2
        assert exporter.layers[0].direction == "orthogonal"
        assert exporter.layers[1].direction == "orthogonal"

    def test_routing_style_orthogonal_with_inner_layers(self):
        """Test orthogonal routing with 4-layer board."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {
            "footprints": [],
            "layers": [
                {"canonical_name": "In1.Cu"},
                {"canonical_name": "In2.Cu"},
            ]
        }
        board.footprints = {}

        exporter = DSNExporter(board, routing_style="orthogonal", via_size=None)
        exporter._extract_layers()

        # Should have 4 layers: front, inner1, inner2, back
        assert len(exporter.layers) == 4
        assert all(layer.direction == "orthogonal" for layer in exporter.layers)

    def test_routing_style_default_with_inner_layers(self):
        """Test default routing direction alternates for inner layers."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {
            "footprints": [],
            "layers": [
                {"canonical_name": "In1.Cu"},
                {"canonical_name": "In2.Cu"},
            ]
        }
        board.footprints = {}

        exporter = DSNExporter(board, routing_style=None, via_size=None)
        exporter._extract_layers()

        # Should alternate: front(h), inner1(h), inner2(v), back(v)
        assert len(exporter.layers) == 4
        assert exporter.layers[0].direction == "horizontal"  # front
        assert exporter.layers[1].direction == "horizontal"  # inner1
        assert exporter.layers[2].direction == "vertical"    # inner2
        assert exporter.layers[3].direction == "vertical"    # back


class TestViaSizeParsing:
    """Test via size parameter parsing."""

    def test_via_size_parsing_valid_format(self):
        """Test via size parsing with valid 'drill/annular' format."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board, routing_style=None, via_size="0.6/0.3")

        # Check parsed values
        assert exporter.DEFAULT_VIA_DRILL == 0.6
        assert exporter.DEFAULT_VIA_SIZE == 1.2  # 0.6 + 2*0.3

    def test_via_size_parsing_different_values(self):
        """Test via size parsing with different values."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board, routing_style=None, via_size="0.8/0.4")

        assert exporter.DEFAULT_VIA_DRILL == 0.8
        assert exporter.DEFAULT_VIA_SIZE == 1.6  # 0.8 + 2*0.4

    def test_via_size_parsing_invalid_format_fallback(self):
        """Test that invalid via_size format falls back to defaults with warning."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Should not raise exception, should use defaults
        exporter = DSNExporter(board, routing_style=None, via_size="invalid")

        # Should use class defaults (not changed)
        assert exporter.DEFAULT_VIA_SIZE == DSNExporter.DEFAULT_VIA_SIZE
        assert exporter.DEFAULT_VIA_DRILL == DSNExporter.DEFAULT_VIA_DRILL

    def test_via_size_parsing_missing_annular(self):
        """Test via_size with missing annular ring value."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Should fall back to defaults
        exporter = DSNExporter(board, routing_style=None, via_size="0.6")

        assert exporter.DEFAULT_VIA_SIZE == DSNExporter.DEFAULT_VIA_SIZE
        assert exporter.DEFAULT_VIA_DRILL == DSNExporter.DEFAULT_VIA_DRILL

    def test_via_size_parsing_non_numeric(self):
        """Test via_size with non-numeric values."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Should fall back to defaults
        exporter = DSNExporter(board, routing_style=None, via_size="abc/def")

        assert exporter.DEFAULT_VIA_SIZE == DSNExporter.DEFAULT_VIA_SIZE
        assert exporter.DEFAULT_VIA_DRILL == DSNExporter.DEFAULT_VIA_DRILL

    def test_via_size_none_uses_class_defaults(self):
        """Test that via_size=None uses class default values."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board, routing_style=None, via_size=None)

        # Should have class defaults
        assert exporter.DEFAULT_VIA_SIZE == 0.8
        assert exporter.DEFAULT_VIA_DRILL == 0.4


class TestOrthogonalRoutingDefaults:
    """Test automatic via sizing for orthogonal routing."""

    def test_orthogonal_routing_without_via_size_uses_defaults(self):
        """Test that orthogonal routing without via_size uses 0.6/0.3 defaults."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board, routing_style="orthogonal", via_size=None)

        # Should use orthogonal routing defaults from issue #195
        assert exporter.DEFAULT_VIA_DRILL == 0.6
        assert exporter.DEFAULT_VIA_SIZE == 1.2  # 0.6 + 2*0.3

    def test_orthogonal_routing_with_explicit_via_size(self):
        """Test that explicit via_size overrides orthogonal defaults."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board, routing_style="orthogonal", via_size="0.8/0.4")

        # Should use explicit values, not orthogonal defaults
        assert exporter.DEFAULT_VIA_DRILL == 0.8
        assert exporter.DEFAULT_VIA_SIZE == 1.6

    def test_orthogonal_routing_priority_order(self):
        """Test priority: explicit via_size > orthogonal defaults > class defaults."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Priority 1: Explicit via_size (highest)
        exporter1 = DSNExporter(board, routing_style="orthogonal", via_size="0.5/0.25")
        assert exporter1.DEFAULT_VIA_DRILL == 0.5

        # Priority 2: Orthogonal defaults
        exporter2 = DSNExporter(board, routing_style="orthogonal", via_size=None)
        assert exporter2.DEFAULT_VIA_DRILL == 0.6

        # Priority 3: Class defaults (lowest)
        exporter3 = DSNExporter(board, routing_style=None, via_size=None)
        assert exporter3.DEFAULT_VIA_DRILL == 0.4


class TestDSNExportIntegration:
    """Integration tests for DSN export with orthogonal routing."""

    def test_dsn_export_parameters_initialization(self):
        """Test that DSN exporter correctly initializes with orthogonal routing parameters."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Test with orthogonal routing
        exporter = DSNExporter(board, routing_style="orthogonal", via_size="0.6/0.3")
        assert exporter.routing_style == "orthogonal"
        assert exporter.DEFAULT_VIA_DRILL == 0.6
        assert exporter.DEFAULT_VIA_SIZE == 1.2

    def test_dsn_export_parameters_default(self):
        """Test that DSN exporter works with default (non-orthogonal) parameters."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board, routing_style=None, via_size=None)
        assert exporter.routing_style is None
        assert exporter.DEFAULT_VIA_SIZE == 0.8
        assert exporter.DEFAULT_VIA_DRILL == 0.4


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_dsn_exporter_without_new_parameters(self):
        """Test that DSNExporter works without new parameters (backward compatible)."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Should work with just board parameter (original API)
        exporter = DSNExporter(board)

        # Should have default class values
        assert exporter.routing_style is None
        assert exporter.DEFAULT_VIA_SIZE == 0.8
        assert exporter.DEFAULT_VIA_DRILL == 0.4

    def test_layers_extraction_without_routing_style(self):
        """Test layer extraction maintains original behavior when routing_style not specified."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board)  # No routing_style parameter
        exporter._extract_layers()

        # Should use original horizontal/vertical pattern
        assert exporter.layers[0].direction == "horizontal"
        assert exporter.layers[1].direction == "vertical"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_via_size_with_zero_values(self):
        """Test via_size handling with zero drill or annular."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Zero drill - should fall back to defaults
        exporter1 = DSNExporter(board, routing_style=None, via_size="0/0.3")
        # Note: Current implementation doesn't validate positive values
        # This test documents current behavior

    def test_via_size_with_negative_values(self):
        """Test via_size handling with negative values."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Negative values should parse but may not be validated
        exporter = DSNExporter(board, routing_style=None, via_size="-0.6/0.3")
        # Note: Current implementation doesn't validate positive values

    def test_via_size_with_very_large_values(self):
        """Test via_size with very large values."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        # Large values should parse
        exporter = DSNExporter(board, routing_style=None, via_size="10.0/5.0")
        assert exporter.DEFAULT_VIA_DRILL == 10.0
        assert exporter.DEFAULT_VIA_SIZE == 20.0  # 10 + 2*5

    def test_routing_style_empty_string(self):
        """Test routing_style with empty string (should be treated as None)."""
        board = Mock(spec=PCBBoard)
        board.pcb_data = {"footprints": [], "layers": []}
        board.footprints = {}

        exporter = DSNExporter(board, routing_style="", via_size=None)
        exporter._extract_layers()

        # Empty string is falsy, should use default behavior
        # Note: Documents current behavior - may want validation in future


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
