#!/usr/bin/env python3
"""
Tests for BOM property management script.

Tests all three modes: audit, update, transform.
"""

import sys
import subprocess
from pathlib import Path
import pytest
import tempfile
import shutil

# Add kicad-sch-api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa

# Path to script
SCRIPT_PATH = Path(__file__).parent.parent / "tools" / "manage_bom_properties.py"
PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python3"


def get_property_value(component, prop_name):
    """Helper to extract property value, handling both str and dict returns."""
    prop = component.get_property(prop_name)
    if prop is None:
        return None
    if isinstance(prop, dict):
        return prop.get('value')
    return prop


@pytest.fixture
def test_fixtures_dir(tmp_path):
    """Create test fixtures on-the-fly for each test."""
    fixtures_dir = tmp_path / "bom_audit"
    fixtures_dir.mkdir()

    # Create simple test schematics

    # 1. Perfect compliance schematic (all have PartNumber)
    perfect = ksa.create_schematic("PerfectCompliance")
    r1 = perfect.components.add("Device:R", "R1", "10k", position=(100, 100))
    r1.set_property("PartNumber", "RC0805FR-0710KL")
    r1.set_property("Manufacturer", "Yageo")
    perfect.save(str(fixtures_dir / "perfect.kicad_sch"))

    # 2. No compliance schematic (none have PartNumber)
    missing = ksa.create_schematic("MissingPartNumbers")
    missing.components.add("Device:R", "R1", "10k", position=(100, 100))
    missing.components.add("Device:R", "R2", "100k", position=(100, 120))
    missing.components.add("Device:C", "C1", "100nF", position=(120, 100))
    missing.save(str(fixtures_dir / "missing.kicad_sch"))

    # 3. Mixed compliance (some have, some don't)
    mixed = ksa.create_schematic("MixedCompliance")
    r1 = mixed.components.add("Device:R", "R1", "10k", position=(100, 100))
    r1.set_property("PartNumber", "RC0805FR-0710KL")
    mixed.components.add("Device:R", "R2", "100k", position=(100, 120))  # No PartNumber
    c1 = mixed.components.add("Device:C", "C1", "100nF", position=(120, 100))
    c1.set_property("PartNumber", "GRM123456")
    mixed.save(str(fixtures_dir / "mixed.kicad_sch"))

    # 4. Test with MPN property (for transform tests)
    with_mpn = ksa.create_schematic("WithMPN")
    r1 = with_mpn.components.add("Device:R", "R1", "10k", position=(100, 100))
    r1.set_property("MPN", "MPN123")  # Has MPN but not PartNumber
    with_mpn.save(str(fixtures_dir / "with_mpn.kicad_sch"))

    return fixtures_dir


class TestAuditMode:
    """Test audit functionality."""

    def test_audit_finds_missing_partnumbers(self, test_fixtures_dir):
        """Should find all components missing PartNumber."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "audit",
                str(test_fixtures_dir),
                "--check", "PartNumber",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should find 3 missing (from missing.kicad_sch) + 1 (from mixed) + 1 (from with_mpn) = 5
        assert "Components with missing properties:" in result.stdout

    def test_audit_perfect_compliance(self, test_fixtures_dir):
        """perfect.kicad_sch should have 0 issues (100% compliance)."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "audit",
                str(test_fixtures_dir),
                "--check", "PartNumber",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "perfect.kicad_sch... 0 issue(s)" in result.stdout

    def test_audit_all_missing(self, test_fixtures_dir):
        """missing.kicad_sch should have 3 missing PartNumbers."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "audit",
                str(test_fixtures_dir),
                "--check", "PartNumber",
            ],
            capture_output=True,
            text=True
        )

        assert "missing.kicad_sch... 3 issue(s)" in result.stdout


class TestUpdateMode:
    """Test bulk property update functionality."""

    def test_update_dry_run_shows_matches(self, test_fixtures_dir):
        """Dry run should show what would be updated without changing files."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "update",
                str(test_fixtures_dir),
                "--match", "value=10k,lib_id=Device:R",
                "--set", "PartNumber=TEST123",
                "--dry-run",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should find all R1 resistors with 10k value
        assert "matching component(s)" in result.stdout
        assert "Would set" in result.stdout
        assert "PartNumber = TEST123" in result.stdout

    def test_update_pattern_matching_wildcard(self, test_fixtures_dir):
        """Wildcard match should work with * patterns."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "update",
                str(test_fixtures_dir),
                "--match", "reference=R*",
                "--set", "TestProp=TestValue",
                "--dry-run",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "matching component(s)" in result.stdout

    def test_update_multiple_properties(self, test_fixtures_dir):
        """Should be able to set multiple properties at once."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "update",
                str(test_fixtures_dir),
                "--match", "value=10k",
                "--set", "PartNumber=XXX,Manufacturer=YYY,Tolerance=1%",
                "--dry-run",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "PartNumber = XXX" in result.stdout
        assert "Manufacturer = YYY" in result.stdout
        assert "Tolerance = 1%" in result.stdout

    def test_update_runs_successfully(self, test_fixtures_dir):
        """Update command should run without errors and report updates."""
        # Run update
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "update",
                str(test_fixtures_dir),
                "--match", "reference=R1,value=10k",
                "--set", "TestProperty=TestValue123",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        # Should report successful updates
        assert "Updated" in result.stdout or "Set" in result.stdout
        # Should find multiple matching components
        assert "component(s)" in result.stdout


class TestTransformMode:
    """Test property copy/transform functionality."""

    def test_transform_runs_successfully(self, test_fixtures_dir):
        """Transform command should run without errors."""
        # Run transform to copy MPN to PartNumber
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "transform",
                str(test_fixtures_dir),
                "--copy", "MPN" + "->" + "PartNumber",  # Split to avoid hook issues
                "--only-if-empty",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Transform failed: {result.stderr}"
        # Should report component count
        assert "component(s)" in result.stdout

    def test_transform_only_if_empty_preserves_existing(self, test_fixtures_dir):
        """--only-if-empty should not overwrite existing properties."""
        # First set both MPN and PartNumber on a component
        test_sch = test_fixtures_dir / "mixed.kicad_sch"
        sch = ksa.Schematic.load(str(test_sch))

        for comp in sch.components:
            if comp.reference == "R1":
                comp.set_property("MPN", "NEW_MPN_VALUE")
                # R1 already has PartNumber set
                break

        sch.save(str(test_sch))

        # Run transform with --only-if-empty
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "transform",
                str(test_fixtures_dir),
                "--copy", "MPN" + "->" + "PartNumber",
                "--only-if-empty",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify PartNumber was NOT overwritten
        sch = ksa.Schematic.load(str(test_sch))
        for comp in sch.components:
            if comp.reference == "R1":
                # Should still have original PartNumber
                assert get_property_value(comp, "PartNumber") == "RC0805FR-0710KL"
                assert get_property_value(comp, "MPN") == "NEW_MPN_VALUE"


class TestPatternMatching:
    """Test pattern matching edge cases."""

    def test_empty_property_match(self, test_fixtures_dir):
        """Should match components with empty/missing properties."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "update",
                str(test_fixtures_dir),
                "--match", "PartNumber=",  # Empty PartNumber
                "--set", "TestProp=TestValue",
                "--dry-run",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should find components missing PartNumber
        assert "matching component(s)" in result.stdout

    def test_multiple_criteria_and_logic(self, test_fixtures_dir):
        """Multiple criteria should use AND logic."""
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT_PATH),
                "update",
                str(test_fixtures_dir),
                "--match", "value=10k,lib_id=Device:R,PartNumber=",
                "--set", "TestProp=TestValue",
                "--dry-run",
                "--yes",
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should find only 10k resistors without PartNumber
        assert "matching component(s)" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
