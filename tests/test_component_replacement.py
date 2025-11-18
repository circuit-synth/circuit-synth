"""
Tests for bulk component replacement utilities.

Tests the component replacement functions that allow users to replace
components based on property values across entire circuits.
"""

import pytest

import circuit_synth as cs


class TestReplacementResult:
    """Test ReplacementResult dataclass."""

    def test_replacement_result_creation(self):
        """Should create ReplacementResult with all fields."""
        result = cs.ReplacementResult(
            count=3,
            affected_components=["R1", "R2", "R3"],
            warnings=["Warning 1"],
            errors=["Error 1"],
        )

        assert result.count == 3
        assert len(result.affected_components) == 3
        assert len(result.warnings) == 1
        assert len(result.errors) == 1

    def test_replacement_result_str(self):
        """Should format result as string."""
        result = cs.ReplacementResult(
            count=2, affected_components=["R1", "R2"], warnings=[], errors=[]
        )

        result_str = str(result)

        assert "Replaced 2 components" in result_str
        assert "R1" in result_str
        assert "R2" in result_str


class TestReplaceComponents:
    """Test replace_components function."""

    def test_replace_single_property(self):
        """Should replace property on matching components."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        circuit.add_component(r1)
        circuit.finalize_references()

        result = cs.replace_components(
            circuit, match={"MPN": "ASD123"}, update={"MPN": "FGS032"}
        )

        assert result.count == 1
        assert "R1" in result.affected_components
        assert r1.MPN == "FGS032"

    def test_replace_multiple_properties(self):
        """Should replace multiple properties at once."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        r1.Manufacturer = "OldCo"
        circuit.add_component(r1)
        circuit.finalize_references()

        result = cs.replace_components(
            circuit,
            match={"MPN": "ASD123"},
            update={"MPN": "FGS032", "Manufacturer": "NewCo"},
        )

        assert result.count == 1
        assert r1.MPN == "FGS032"
        assert r1.Manufacturer == "NewCo"

    def test_replace_multiple_components(self):
        """Should replace properties on all matching components."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        r2 = cs.Component("Device:R", ref="R", value="20k")
        r2.MPN = "ASD123"
        r3 = cs.Component("Device:R", ref="R", value="30k")
        r3.MPN = "DIFFERENT"
        circuit.add_component(r1)
        circuit.add_component(r2)
        circuit.add_component(r3)
        circuit.finalize_references()

        result = cs.replace_components(
            circuit, match={"MPN": "ASD123"}, update={"MPN": "FGS032"}
        )

        assert result.count == 2
        assert "R1" in result.affected_components
        assert "R2" in result.affected_components
        assert "R3" not in result.affected_components
        assert r1.MPN == "FGS032"
        assert r2.MPN == "FGS032"
        assert r3.MPN == "DIFFERENT"

    def test_replace_with_multiple_match_criteria(self):
        """Should match on multiple criteria."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        r1.Package = "0603"
        r2 = cs.Component("Device:R", ref="R", value="20k")
        r2.MPN = "ASD123"
        r2.Package = "0805"
        circuit.add_component(r1)
        circuit.add_component(r2)
        circuit.finalize_references()

        result = cs.replace_components(
            circuit,
            match={"MPN": "ASD123", "Package": "0603"},
            update={"MPN": "FGS032"},
        )

        assert result.count == 1
        assert "R1" in result.affected_components
        assert "R2" not in result.affected_components
        assert r1.MPN == "FGS032"
        assert r2.MPN == "ASD123"  # Not changed

    def test_replace_no_matches(self):
        """Should handle case with no matching components."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "DIFFERENT"
        circuit.add_component(r1)
        circuit.finalize_references()

        result = cs.replace_components(
            circuit, match={"MPN": "NOTFOUND"}, update={"MPN": "FGS032"}
        )

        assert result.count == 0
        assert len(result.affected_components) == 0
        assert r1.MPN == "DIFFERENT"  # Unchanged

    def test_replace_dry_run(self):
        """Should not modify components in dry run mode."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        circuit.add_component(r1)
        circuit.finalize_references()

        result = cs.replace_components(
            circuit, match={"MPN": "ASD123"}, update={"MPN": "FGS032"}, dry_run=True
        )

        assert result.count == 1
        assert "R1" in result.affected_components
        assert r1.MPN == "ASD123"  # Should not be changed in dry run

    def test_replace_nonexistent_property(self):
        """Should not match components without the specified property."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        # r1 does not have MPN property
        circuit.add_component(r1)
        circuit.finalize_references()

        result = cs.replace_components(
            circuit, match={"MPN": "ASD123"}, update={"MPN": "FGS032"}
        )

        assert result.count == 0


class TestReplaceMultiple:
    """Test replace_multiple function."""

    def test_replace_multiple_operations(self):
        """Should apply multiple replacement operations."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        r2 = cs.Component("Device:R", ref="R", value="20k")
        r2.MPN = "OLD456"
        circuit.add_component(r1)
        circuit.add_component(r2)
        circuit.finalize_references()

        replacements = [
            {"match": {"MPN": "ASD123"}, "update": {"MPN": "FGS032"}},
            {"match": {"MPN": "OLD456"}, "update": {"MPN": "NEW789"}},
        ]

        result = cs.replace_multiple(circuit, replacements)

        assert result.count == 2
        assert r1.MPN == "FGS032"
        assert r2.MPN == "NEW789"

    def test_replace_multiple_with_overlapping_updates(self):
        """Should handle multiple operations on same components."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        r1.Manufacturer = "OldCo"
        circuit.add_component(r1)
        circuit.finalize_references()

        replacements = [
            {"match": {"MPN": "ASD123"}, "update": {"MPN": "FGS032"}},
            {"match": {"Manufacturer": "OldCo"}, "update": {"Manufacturer": "NewCo"}},
        ]

        result = cs.replace_multiple(circuit, replacements)

        # First operation changes MPN, second changes Manufacturer
        # Both should match their original values
        assert result.count == 2
        assert r1.MPN == "FGS032"
        assert r1.Manufacturer == "NewCo"

    def test_replace_multiple_dry_run(self):
        """Should not modify in dry run mode."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        circuit.add_component(r1)
        circuit.finalize_references()

        replacements = [{"match": {"MPN": "ASD123"}, "update": {"MPN": "FGS032"}}]

        result = cs.replace_multiple(circuit, replacements, dry_run=True)

        assert result.count == 1
        assert r1.MPN == "ASD123"  # Unchanged in dry run

    def test_replace_multiple_invalid_spec(self):
        """Should handle invalid replacement specs gracefully."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        circuit.add_component(r1)
        circuit.finalize_references()

        replacements = [
            {"match": {"MPN": "ASD123"}},  # Missing 'update'
            {"update": {"MPN": "FGS032"}},  # Missing 'match'
            {"match": {"MPN": "ASD123"}, "update": {"MPN": "FGS032"}},  # Valid
        ]

        result = cs.replace_multiple(circuit, replacements)

        assert result.count == 1  # Only valid operation executed
        assert len(result.warnings) == 2  # Two invalid specs


class TestFindReplaceableComponents:
    """Test find_replaceable_components function."""

    def test_find_matching_components(self):
        """Should find all components matching criteria."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        r2 = cs.Component("Device:R", ref="R", value="20k")
        r2.MPN = "ASD123"
        r3 = cs.Component("Device:R", ref="R", value="30k")
        r3.MPN = "DIFFERENT"
        circuit.add_component(r1)
        circuit.add_component(r2)
        circuit.add_component(r3)
        circuit.finalize_references()

        matches = cs.find_replaceable_components(circuit, match={"MPN": "ASD123"})

        assert len(matches) == 2
        assert "R1" in matches
        assert "R2" in matches
        assert "R3" not in matches

    def test_find_no_matches(self):
        """Should return empty list when no matches."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "DIFFERENT"
        circuit.add_component(r1)
        circuit.finalize_references()

        matches = cs.find_replaceable_components(circuit, match={"MPN": "NOTFOUND"})

        assert len(matches) == 0

    def test_find_does_not_modify(self):
        """Should not modify components."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        circuit.add_component(r1)
        circuit.finalize_references()

        matches = cs.find_replaceable_components(circuit, match={"MPN": "ASD123"})

        assert len(matches) == 1
        assert r1.MPN == "ASD123"  # Should not be modified


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_obsolete_part_replacement(self):
        """User replaces obsolete parts across design."""
        circuit = cs.Circuit("ProductionBoard")
        # Create components with obsolete part
        for i in range(5):
            r = cs.Component("Device:R", ref="R", value="10k")
            r.MPN = "OBSOLETE_PART"
            r.Manufacturer = "OldVendor"
            circuit.add_component(r)
        circuit.finalize_references()

        # Replace with new part
        result = cs.replace_components(
            circuit,
            match={"MPN": "OBSOLETE_PART"},
            update={"MPN": "NEW_PART", "Manufacturer": "NewVendor"},
        )

        assert result.count == 5
        for comp in circuit.components.values():
            assert comp.MPN == "NEW_PART"
            assert comp.Manufacturer == "NewVendor"

    def test_preview_before_replace(self):
        """User previews what would be affected before replacing."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "ASD123"
        r2 = cs.Component("Device:R", ref="R", value="20k")
        r2.MPN = "ASD123"
        circuit.add_component(r1)
        circuit.add_component(r2)
        circuit.finalize_references()

        # Preview what would be affected
        matches = cs.find_replaceable_components(circuit, match={"MPN": "ASD123"})
        print(f"Would affect: {matches}")

        # User confirms, proceed with replacement
        result = cs.replace_components(
            circuit, match={"MPN": "ASD123"}, update={"MPN": "FGS032"}
        )

        assert result.count == len(matches)

    def test_batch_part_updates(self):
        """User updates multiple different parts in one operation."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r1.MPN = "PART_A"
        c1 = cs.Component("Device:C", ref="C", value="10uF")
        c1.MPN = "PART_B"
        l1 = cs.Component("Device:L", ref="L", value="10uH")
        l1.MPN = "PART_C"
        circuit.add_component(r1)
        circuit.add_component(c1)
        circuit.add_component(l1)
        circuit.finalize_references()

        # Batch update
        replacements = [
            {"match": {"MPN": "PART_A"}, "update": {"MPN": "NEW_A"}},
            {"match": {"MPN": "PART_B"}, "update": {"MPN": "NEW_B"}},
            {"match": {"MPN": "PART_C"}, "update": {"MPN": "NEW_C"}},
        ]

        result = cs.replace_multiple(circuit, replacements)

        assert result.count == 3
        assert r1.MPN == "NEW_A"
        assert c1.MPN == "NEW_B"
        assert l1.MPN == "NEW_C"
