#!/usr/bin/env python3
"""
Tests for BOM Property Manager.

Tests the circuit-synth wrapper around kicad-sch-api BOM functionality.
"""

import sys
from pathlib import Path

import pytest

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import kicad_sch_api as ksa
from circuit_synth.kicad.bom_manager import BOMPropertyManager


def get_property_value(component, prop_name):
    """Helper to extract property value, handling both str and dict returns."""
    prop = component.get_property(prop_name)
    if prop is None:
        return None
    if isinstance(prop, dict):
        return prop.get("value")
    return prop


@pytest.fixture
def test_fixtures_dir(tmp_path):
    """Create test fixtures on-the-fly for each test."""
    fixtures_dir = tmp_path / "bom_manager_test"
    fixtures_dir.mkdir()

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


class TestBOMPropertyManager:
    """Test BOMPropertyManager class."""

    def test_initialization(self):
        """Should initialize successfully."""
        manager = BOMPropertyManager()
        assert manager is not None
        assert manager.auditor is not None

    def test_audit_directory(self, test_fixtures_dir):
        """Should audit directory for missing properties."""
        manager = BOMPropertyManager()

        issues = manager.audit_directory(
            test_fixtures_dir, required_properties=["PartNumber"], recursive=False
        )

        # Should find at least 5 components missing PartNumber
        assert len(issues) >= 5

    def test_audit_schematic(self, test_fixtures_dir):
        """Should audit single schematic."""
        manager = BOMPropertyManager()

        # Perfect compliance
        issues = manager.audit_schematic(
            test_fixtures_dir / "perfect.kicad_sch", required_properties=["PartNumber"]
        )
        assert len(issues) == 0

        # Missing compliance
        issues = manager.audit_schematic(
            test_fixtures_dir / "missing.kicad_sch", required_properties=["PartNumber"]
        )
        assert len(issues) == 3

    def test_generate_report(self, test_fixtures_dir, tmp_path):
        """Should generate CSV report."""
        manager = BOMPropertyManager()

        issues = manager.audit_directory(
            test_fixtures_dir, required_properties=["PartNumber"], recursive=False
        )

        report_path = tmp_path / "test_report.csv"
        manager.generate_report(issues, report_path)

        assert report_path.exists()

        # Verify CSV content
        content = report_path.read_text()
        assert "Schematic" in content
        assert "Reference" in content

    def test_update_properties_dry_run(self, test_fixtures_dir):
        """Should preview updates in dry-run mode."""
        manager = BOMPropertyManager()

        count = manager.update_properties(
            test_fixtures_dir,
            match={"value": "10k", "lib_id": "Device:R"},
            set_properties={"PartNumber": "TEST123"},
            dry_run=True,
            recursive=False,
        )

        # Should find matching components
        assert count > 0

        # Verify no actual changes (dry-run)
        sch = ksa.Schematic.load(str(test_fixtures_dir / "missing.kicad_sch"))
        for comp in sch.components:
            if comp.reference == "R1" and comp.value == "10k":
                assert get_property_value(comp, "PartNumber") is None

    def test_update_properties_actual(self, test_fixtures_dir):
        """Should actually update properties."""
        manager = BOMPropertyManager()

        count = manager.update_properties(
            test_fixtures_dir,
            match={"reference": "R1", "value": "10k"},
            set_properties={"TestProperty": "TestValue123"},
            dry_run=False,
            recursive=False,
        )

        assert count > 0

        # Verify actual changes
        sch = ksa.Schematic.load(str(test_fixtures_dir / "missing.kicad_sch"))
        for comp in sch.components:
            if comp.reference == "R1" and comp.value == "10k":
                assert get_property_value(comp, "TestProperty") == "TestValue123"

    def test_update_multiple_properties(self, test_fixtures_dir):
        """Should update multiple properties at once."""
        manager = BOMPropertyManager()

        count = manager.update_properties(
            test_fixtures_dir,
            match={"value": "10k"},
            set_properties={
                "PartNumber": "XXX",
                "Manufacturer": "YYY",
                "Tolerance": "1%",
            },
            dry_run=True,
            recursive=False,
        )

        assert count > 0

    def test_transform_properties(self, test_fixtures_dir):
        """Should transform properties successfully."""
        manager = BOMPropertyManager()

        # Run transform to copy MPN to PartNumber
        count = manager.transform_properties(
            test_fixtures_dir,
            transformations=[("MPN", "PartNumber")],
            only_if_empty=False,
            dry_run=False,
            recursive=False,
        )

        assert count > 0

        # Verify transformation happened
        sch = ksa.Schematic.load(str(test_fixtures_dir / "with_mpn.kicad_sch"))
        for comp in sch.components:
            if comp.reference == "R1":
                assert get_property_value(comp, "PartNumber") == "MPN123"

    def test_transform_only_if_empty(self, test_fixtures_dir):
        """Should respect only_if_empty flag."""
        manager = BOMPropertyManager()

        # Set both MPN and PartNumber
        test_sch = test_fixtures_dir / "mixed.kicad_sch"
        sch = ksa.Schematic.load(str(test_sch))
        for comp in sch.components:
            if comp.reference == "R1":
                comp.set_property("MPN", "NEW_MPN_VALUE")
                break
        sch.save(str(test_sch))

        # Transform with only_if_empty
        count = manager.transform_properties(
            test_fixtures_dir,
            transformations=[("MPN", "PartNumber")],
            only_if_empty=True,
            dry_run=False,
            recursive=False,
        )

        # Verify PartNumber was NOT overwritten
        sch = ksa.Schematic.load(str(test_sch))
        for comp in sch.components:
            if comp.reference == "R1":
                # Should still have original PartNumber
                assert get_property_value(comp, "PartNumber") == "RC0805FR-0710KL"
                assert get_property_value(comp, "MPN") == "NEW_MPN_VALUE"

    def test_parse_match_criteria(self):
        """Should parse match criteria string."""
        criteria = BOMPropertyManager.parse_match_criteria(
            "value=10k,footprint=*0805*"
        )
        assert criteria == {"value": "10k", "footprint": "*0805*"}

    def test_parse_properties(self):
        """Should parse property string."""
        props = BOMPropertyManager.parse_properties("PartNumber=XXX,Manufacturer=YYY")
        assert props == {"PartNumber": "XXX", "Manufacturer": "YYY"}

    def test_exclude_dnp(self, test_fixtures_dir):
        """Should exclude DNP components when requested."""
        # Create schematic with DNP component
        dnp_sch = ksa.create_schematic("WithDNP")
        r1 = dnp_sch.components.add("Device:R", "R1", "10k", position=(100, 100))
        r1.set_property("PartNumber", "RC0805FR-0710KL")
        r2 = dnp_sch.components.add("Device:R", "R2", "100k", position=(100, 120))
        r2.set_property("dnp", "1")  # DNP component without PartNumber
        dnp_sch.save(str(test_fixtures_dir / "with_dnp.kicad_sch"))

        manager = BOMPropertyManager()

        # Without exclude_dnp
        issues_with_dnp = manager.audit_schematic(
            test_fixtures_dir / "with_dnp.kicad_sch",
            required_properties=["PartNumber"],
            exclude_dnp=False,
        )

        # With exclude_dnp
        issues_without_dnp = manager.audit_schematic(
            test_fixtures_dir / "with_dnp.kicad_sch",
            required_properties=["PartNumber"],
            exclude_dnp=True,
        )

        # Should find DNP component without exclude flag
        assert len(issues_with_dnp) > len(issues_without_dnp)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
