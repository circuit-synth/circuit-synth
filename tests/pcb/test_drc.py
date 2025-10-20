"""
Tests for DRC (Design Rule Check) functionality.

These tests verify that the enhanced DRC validator correctly identifies
layout violations including via placement, clearances, trace widths,
drill sizes, and copper on edge cuts.
"""

import pytest
from pathlib import Path

from circuit_synth.pcb import PCBBoard
from circuit_synth.pcb.drc import (
    DRCCategory,
    DRCRule,
    EnhancedDRCValidator,
    run_enhanced_drc,
)
from circuit_synth.pcb.types import Point, Track, Via
from circuit_synth.pcb.validation import ValidationSeverity


class TestDRCValidator:
    """Test the enhanced DRC validator."""

    def test_drc_rule_defaults(self):
        """Test that default DRC rules are properly initialized."""
        rule = DRCRule(name="test", description="Test rule")

        assert rule.min_trace_width == 0.15
        assert rule.min_clearance == 0.2
        assert rule.min_via_diameter == 0.4
        assert rule.min_via_drill == 0.2
        assert rule.min_via_annular_ring == 0.05

    def test_trace_width_validation(self):
        """Test that trace width violations are detected."""
        pcb = PCBBoard()
        pcb.set_board_outline_rect(0, 0, 100, 100)

        # Add a track that's too narrow
        narrow_track = Track(
            start=Point(10, 10),
            end=Point(20, 10),
            width=0.10,  # Below minimum of 0.15
            layer="F.Cu",
        )
        pcb.pcb_data["tracks"].append(narrow_track)

        # Run DRC
        result, fixes = run_enhanced_drc(pcb)

        # Should have at least one error for trace width
        assert result.error_count > 0
        assert any(
            DRCCategory.TRACE_WIDTH.value in issue.category
            for issue in result.issues
            if issue.severity == ValidationSeverity.ERROR
        )

        # Should have a fix suggestion
        assert len(fixes) > 0
        assert any(fix.fix_type == "adjust_track_width" for fix in fixes)

    def test_drill_size_validation(self):
        """Test that drill size violations are detected."""
        pcb = PCBBoard()
        pcb.set_board_outline_rect(0, 0, 100, 100)

        # Add a via with too small drill
        small_drill_via = Via(
            position=Point(50, 50),
            size=0.5,
            drill=0.10,  # Below minimum of 0.15
            layers=["F.Cu", "B.Cu"],
        )
        pcb.pcb_data["vias"].append(small_drill_via)

        # Run DRC
        result, fixes = run_enhanced_drc(pcb)

        # Should have error for drill size
        assert result.error_count > 0
        assert any(
            DRCCategory.DRILL_SIZE.value in issue.category
            for issue in result.issues
            if issue.severity == ValidationSeverity.ERROR
        )

    def test_via_annular_ring_validation(self):
        """Test that via annular ring violations are detected."""
        pcb = PCBBoard()
        pcb.set_board_outline_rect(0, 0, 100, 100)

        # Add a via with insufficient annular ring
        # Via size 0.4mm, drill 0.38mm -> annular ring 0.01mm (below 0.05mm minimum)
        bad_via = Via(
            position=Point(50, 50),
            size=0.4,
            drill=0.38,
            layers=["F.Cu", "B.Cu"],
        )
        pcb.pcb_data["vias"].append(bad_via)

        # Run DRC
        result, fixes = run_enhanced_drc(pcb)

        # Should have error for annular ring
        assert result.error_count > 0
        assert any(
            DRCCategory.ANNULAR_RING.value in issue.category
            for issue in result.issues
            if issue.severity == ValidationSeverity.ERROR
        )

        # Should suggest increasing via size
        assert len(fixes) > 0
        assert any(fix.fix_type == "adjust_via_size" for fix in fixes)

    def test_custom_drc_rules(self):
        """Test that custom DRC rules can be applied."""
        # Create custom rules with stricter requirements
        custom_rules = DRCRule(
            name="strict",
            description="Strict design rules",
            min_trace_width=0.20,  # Stricter than default
            min_clearance=0.30,  # Stricter than default
        )

        pcb = PCBBoard()
        pcb.set_board_outline_rect(0, 0, 100, 100)

        # Add a track that meets default rules but not strict rules
        track = Track(
            start=Point(10, 10),
            end=Point(20, 10),
            width=0.18,  # Meets default 0.15 but not strict 0.20
            layer="F.Cu",
        )
        pcb.pcb_data["tracks"].append(track)

        # Run DRC with custom rules
        validator = EnhancedDRCValidator(custom_rules)
        result = validator.validate_pcb(pcb)

        # Should fail with strict rules
        assert result.error_count > 0

    def test_clean_board_passes_drc(self):
        """Test that a properly designed board passes DRC."""
        pcb = PCBBoard()
        pcb.set_board_outline_rect(0, 0, 100, 100)

        # Add a properly sized track
        good_track = Track(
            start=Point(10, 10),
            end=Point(20, 10),
            width=0.20,  # Above minimum
            layer="F.Cu",
        )
        pcb.pcb_data["tracks"].append(good_track)

        # Add a properly sized via
        good_via = Via(
            position=Point(50, 50),
            size=0.6,  # Plenty of margin
            drill=0.3,  # Good annular ring
            layers=["F.Cu", "B.Cu"],
        )
        pcb.pcb_data["vias"].append(good_via)

        # Run DRC
        result, fixes = run_enhanced_drc(pcb)

        # Should pass with no errors (warnings may exist for edge clearance, etc.)
        assert result.error_count == 0

    def test_copper_on_edge_cuts_detection(self):
        """Test that copper on edge cuts layer is detected."""
        pcb = PCBBoard()
        pcb.set_board_outline_rect(0, 0, 100, 100)

        # Add a track on the wrong layer
        bad_track = Track(
            start=Point(0, 0),
            end=Point(100, 0),
            width=0.20,
            layer="Edge.Cuts",  # Wrong layer!
        )
        pcb.pcb_data["tracks"].append(bad_track)

        # Run DRC
        result, fixes = run_enhanced_drc(pcb)

        # Should have error for copper on edge cuts
        assert result.error_count > 0
        assert any(
            DRCCategory.COPPER_EDGE.value in issue.category
            for issue in result.issues
            if issue.severity == ValidationSeverity.ERROR
        )


class TestDRCIntegration:
    """Test DRC integration with PCB generation workflow."""

    def test_drc_validation_result_structure(self):
        """Test that DRC results have proper structure."""
        pcb = PCBBoard()
        pcb.set_board_outline_rect(0, 0, 100, 100)

        result, fixes = run_enhanced_drc(pcb)

        # Check result structure
        assert hasattr(result, "issues")
        assert hasattr(result, "error_count")
        assert hasattr(result, "warning_count")
        assert hasattr(result, "is_valid")

        # Check fixes structure
        assert isinstance(fixes, list)
        for fix in fixes:
            assert hasattr(fix, "fix_type")
            assert hasattr(fix, "description")
            assert hasattr(fix, "parameters")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
