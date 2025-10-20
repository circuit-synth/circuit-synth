"""
Test suite for automatic board outline generation feature.

Tests the auto-generate board outline functionality including:
- Bounding box calculation
- Margin application
- Rounded corners
- Integration with PCB generation
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from circuit_synth.core import Circuit, Component, Net
from circuit_synth.pcb import PCBBoard
from circuit_synth.pcb.types import Point


class TestAutoBoardOutline:
    """Test automatic board outline generation."""

    def test_calculate_component_bounding_box(self):
        """Test calculation of component bounding box."""
        pcb = PCBBoard()

        # Add some footprints at known positions
        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0805_2012Metric",
            reference="R1",
            x=10.0,
            y=10.0,
            rotation=0,
            value="10k"
        )

        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0805_2012Metric",
            reference="R2",
            x=30.0,
            y=20.0,
            rotation=0,
            value="10k"
        )

        # Calculate bounding box with no margin
        bbox = pcb.calculate_component_bounding_box(margin=0.0)

        assert bbox is not None
        # The bounding box should encompass both components
        # with approximate footprint sizes added
        assert bbox.min_x < 10.0
        assert bbox.min_y < 10.0
        assert bbox.max_x > 30.0
        assert bbox.max_y > 20.0

    def test_calculate_component_bounding_box_with_margin(self):
        """Test bounding box calculation with margin."""
        pcb = PCBBoard()

        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0805_2012Metric",
            reference="R1",
            x=10.0,
            y=10.0,
            rotation=0,
            value="10k"
        )

        # Calculate with 5mm margin
        bbox_no_margin = pcb.calculate_component_bounding_box(margin=0.0)
        bbox_with_margin = pcb.calculate_component_bounding_box(margin=5.0)

        assert bbox_with_margin is not None
        assert bbox_no_margin is not None

        # With margin should be larger
        assert bbox_with_margin.min_x < bbox_no_margin.min_x
        assert bbox_with_margin.min_y < bbox_no_margin.min_y
        assert bbox_with_margin.max_x > bbox_no_margin.max_x
        assert bbox_with_margin.max_y > bbox_no_margin.max_y

    def test_auto_generate_board_outline_basic(self):
        """Test basic auto board outline generation."""
        pcb = PCBBoard()

        # Add components
        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0805_2012Metric",
            reference="R1",
            x=10.0,
            y=10.0,
            rotation=0,
            value="10k"
        )

        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0805_2012Metric",
            reference="R2",
            x=30.0,
            y=20.0,
            rotation=0,
            value="10k"
        )

        # Auto-generate outline
        success = pcb.auto_generate_board_outline(margin=5.0)

        assert success is True

        # Check that outline was created
        outline = pcb.get_board_outline()
        assert len(outline) > 0

    def test_auto_generate_board_outline_no_components(self):
        """Test auto outline with no components."""
        pcb = PCBBoard()

        # Try to generate outline with no components
        success = pcb.auto_generate_board_outline(margin=5.0)

        # Should fail gracefully
        assert success is False

    def test_auto_generate_board_outline_custom_margin(self):
        """Test auto outline with custom margin."""
        pcb = PCBBoard()

        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0805_2012Metric",
            reference="R1",
            x=10.0,
            y=10.0,
            rotation=0,
            value="10k"
        )

        # Generate with different margins
        success_5mm = pcb.auto_generate_board_outline(margin=5.0)
        bbox_5mm = pcb.get_board_outline_bbox()

        # Clear and regenerate with larger margin
        pcb.clear_edge_cuts()
        success_10mm = pcb.auto_generate_board_outline(margin=10.0)
        bbox_10mm = pcb.get_board_outline_bbox()

        assert success_5mm is True
        assert success_10mm is True

        # Larger margin should create larger board
        assert bbox_10mm.width() > bbox_5mm.width()
        assert bbox_10mm.height() > bbox_5mm.height()


class TestAutoBoardOutlineIntegration:
    """Test auto board outline integration with circuit generation."""

    def test_circuit_with_auto_outline(self):
        """Test full circuit generation with auto board outline."""
        # Create a simple circuit
        circuit = Circuit(name="test_auto_outline")

        # Add a couple components
        r1 = Component("Device:R", ref="R1", value="10k",
                      footprint="Resistor_SMD:R_0805_2012Metric")
        r2 = Component("Device:R", ref="R2", value="10k",
                      footprint="Resistor_SMD:R_0805_2012Metric")

        # Connect them
        net = Net("signal")
        r1["1"] += net
        r2["1"] += net

        # Add components to circuit
        circuit.add_component(r1)
        circuit.add_component(r2)

        # Create temp directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            project_name = "test_auto_outline"

            # Generate with auto outline (default)
            circuit.generate_kicad_project(
                project_name,
                generate_pcb=True,
                board_outline="auto",
                board_margin_mm=10.0,
                corner_radius_mm=0.0,
            )

            # Check that PCB file was created
            pcb_path = Path(project_name) / f"{project_name}.kicad_pcb"
            assert pcb_path.exists()

            # Cleanup
            if Path(project_name).exists():
                shutil.rmtree(project_name)

    def test_circuit_with_manual_outline(self):
        """Test circuit generation with manual board outline mode."""
        circuit = Circuit(name="test_manual_outline")

        r1 = Component("Device:R", ref="R1", value="10k",
                      footprint="Resistor_SMD:R_0805_2012Metric")
        circuit.add_component(r1)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_name = "test_manual_outline"

            # Generate with manual outline
            circuit.generate_kicad_project(
                project_name,
                generate_pcb=True,
                board_outline="manual",
            )

            pcb_path = Path(project_name) / f"{project_name}.kicad_pcb"
            assert pcb_path.exists()

            # Cleanup
            if Path(project_name).exists():
                shutil.rmtree(project_name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
