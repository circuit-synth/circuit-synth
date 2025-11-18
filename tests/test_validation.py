"""
Tests for schematic validation utilities.

Tests the validation functions that check schematics for:
- Missing or incomplete component properties
- Manufacturing readiness
- Naming convention compliance
"""

import pytest

import circuit_synth as cs


class TestValidationIssue:
    """Test the ValidationIssue dataclass."""

    def test_validation_issue_creation(self):
        """Should create ValidationIssue with required fields."""
        issue = cs.ValidationIssue(
            severity="warning",
            message="Missing MPN",
            check_type="properties",
            component="R1",
        )

        assert issue.severity == "warning"
        assert issue.message == "Missing MPN"
        assert issue.check_type == "properties"
        assert issue.component == "R1"
        assert issue.location is None

    def test_validation_issue_str(self):
        """Should format issue as string."""
        issue = cs.ValidationIssue(
            severity="warning",
            message="Missing MPN",
            check_type="properties",
            component="R1",
        )

        result = str(issue)

        assert "[WARNING]" in result
        assert "R1:" in result
        assert "Missing MPN" in result

    def test_validation_issue_without_component(self):
        """Should format issue without component reference."""
        issue = cs.ValidationIssue(
            severity="info", message="Non-sequential numbering", check_type="naming"
        )

        result = str(issue)

        assert "[INFO]" in result
        assert "Non-sequential numbering" in result


class TestValidateProperties:
    """Test validate_properties function."""

    def test_validate_properties_missing_mpn(self):
        """Should detect missing MPN property."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate_properties(circuit)

        # Should have warning for missing MPN
        mpn_issues = [i for i in issues if "MPN" in i.message and i.component == "R1"]
        assert len(mpn_issues) > 0
        assert all(i.severity == "warning" for i in mpn_issues)

    def test_validate_properties_missing_package(self):
        """Should detect missing Package property."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate_properties(circuit)

        # Should have warning for missing Package
        package_issues = [
            i for i in issues if "Package" in i.message and i.component == "R1"
        ]
        assert len(package_issues) > 0

    def test_validate_properties_missing_datasheet(self):
        """Should detect missing Datasheet property."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate_properties(circuit)

        # Should have warning for missing Datasheet
        datasheet_issues = [
            i for i in issues if "Datasheet" in i.message and i.component == "R1"
        ]
        assert len(datasheet_issues) > 0

    def test_validate_properties_custom_required(self):
        """Should check custom required properties."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate_properties(circuit, required=["Tolerance"])

        # Should have warning for missing Tolerance
        tolerance_issues = [
            i for i in issues if "Tolerance" in i.message and i.component == "R1"
        ]
        assert len(tolerance_issues) > 0

    def test_validate_properties_all_present(self):
        """Should pass when all properties present."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()
        r1.MPN = "RC0603FR-0710KL"
        r1.Package = "0603"
        r1.Datasheet = "https://example.com/datasheet.pdf"

        issues = cs.validate_properties(circuit)

        # Should have no issues for R1
        r1_issues = [i for i in issues if i.component == "R1"]
        assert len(r1_issues) == 0


class TestValidateManufacturing:
    """Test validate_manufacturing function."""

    def test_validate_manufacturing_missing_footprint_error(self):
        """Should error on missing footprint."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()
        # Clear footprint
        r1.footprint = ""

        issues = cs.validate_manufacturing(circuit)

        # Should have ERROR for missing footprint
        footprint_issues = [
            i
            for i in issues
            if i.component == "R1" and "footprint" in i.message.lower()
        ]
        assert len(footprint_issues) > 0
        assert any(i.severity == "error" for i in footprint_issues)

    def test_validate_manufacturing_missing_mpn_warning(self):
        """Should warn on missing MPN."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate_manufacturing(circuit)

        # Should have WARNING for missing MPN
        mpn_issues = [
            i for i in issues if i.component == "R1" and "MPN" in i.message
        ]
        assert len(mpn_issues) > 0
        assert all(i.severity == "warning" for i in mpn_issues)

    def test_validate_manufacturing_resistor_missing_power(self):
        """Should warn on resistor missing power rating."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate_manufacturing(circuit)

        # Should have WARNING for missing power rating
        power_issues = [
            i for i in issues if i.component == "R1" and "power" in i.message.lower()
        ]
        assert len(power_issues) > 0
        assert all(i.severity == "warning" for i in power_issues)

    def test_validate_manufacturing_capacitor_missing_voltage(self):
        """Should warn on capacitor missing voltage rating."""
        circuit = cs.Circuit("Test")
        c1 = cs.Component("Device:C", ref="C", value="10uF")
        circuit.add_component(c1)
        circuit.finalize_references()

        issues = cs.validate_manufacturing(circuit)

        # Should have WARNING for missing voltage rating
        voltage_issues = [
            i for i in issues if i.component == "C1" and "voltage" in i.message.lower()
        ]
        assert len(voltage_issues) > 0
        assert all(i.severity == "warning" for i in voltage_issues)

    def test_validate_manufacturing_all_checks_pass(self):
        """Should pass when all manufacturing checks satisfied."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        circuit.add_component(r1)
        circuit.finalize_references()
        r1.MPN = "RC0603FR-0710KL"
        r1.Power = "0.1W"

        issues = cs.validate_manufacturing(circuit)

        # Should have no manufacturing errors
        r1_errors = [i for i in issues if i.component == "R1" and i.severity == "error"]
        assert len(r1_errors) == 0


class TestValidateNaming:
    """Test validate_naming function."""

    def test_validate_naming_resistor_correct_prefix(self):
        """Should accept correct R prefix for resistor."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate_naming(circuit)

        # Should have no prefix issues for R1
        r1_prefix_issues = [
            i for i in issues if i.component == "R1" and "prefix" in i.message.lower()
        ]
        assert len(r1_prefix_issues) == 0

    def test_validate_naming_resistor_wrong_prefix(self):
        """Should detect wrong prefix for resistor."""
        circuit = cs.Circuit("Test")
        # Manually create component with wrong reference
        r1 = cs.Component("Device:R", ref="X1", value="10k")
        circuit.add_component(r1)

        issues = cs.validate_naming(circuit)

        # Should have warning for wrong prefix
        prefix_issues = [
            i
            for i in issues
            if i.component == "X1" and "Expected prefix 'R'" in i.message
        ]
        assert len(prefix_issues) > 0
        assert all(i.severity == "warning" for i in prefix_issues)

    def test_validate_naming_capacitor_correct_prefix(self):
        """Should accept correct C prefix for capacitor."""
        circuit = cs.Circuit("Test")
        c1 = cs.Component("Device:C", ref="C", value="10uF")
        circuit.add_component(c1)
        circuit.finalize_references()

        issues = cs.validate_naming(circuit)

        # Should have no prefix issues for C1
        c1_prefix_issues = [
            i for i in issues if i.component == "C1" and "prefix" in i.message.lower()
        ]
        assert len(c1_prefix_issues) == 0

    def test_validate_naming_sequential_numbering(self):
        """Should detect non-sequential numbering."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R1", value="10k")
        r5 = cs.Component("Device:R", ref="R5", value="20k")  # Gap in numbering
        circuit.add_component(r1)
        circuit.add_component(r5)

        issues = cs.validate_naming(circuit)

        # Should have info about non-sequential numbering
        sequential_issues = [
            i for i in issues if "Non-sequential" in i.message and i.severity == "info"
        ]
        assert len(sequential_issues) > 0

    def test_validate_naming_sequential_numbering_ok(self):
        """Should accept sequential numbering."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r2 = cs.Component("Device:R", ref="R", value="20k")
        r3 = cs.Component("Device:R", ref="R", value="30k")
        circuit.add_component(r1)
        circuit.add_component(r2)
        circuit.add_component(r3)
        circuit.finalize_references()

        issues = cs.validate_naming(circuit)

        # Should have no sequential numbering issues for R
        sequential_issues = [
            i for i in issues if "Non-sequential" in i.message and "R" in i.message
        ]
        assert len(sequential_issues) == 0


class TestValidate:
    """Test the main validate function."""

    def test_validate_runs_all_checks(self):
        """Should run all checks by default."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        # Add a component with wrong prefix to ensure naming check finds an issue
        x1 = cs.Component("Device:R", ref="X1", value="20k")
        circuit.add_component(r1)
        circuit.add_component(x1)
        circuit.finalize_references()

        issues = cs.validate(circuit)

        # Should have issues from multiple check types
        check_types = {i.check_type for i in issues}
        assert "properties" in check_types
        assert "manufacturing" in check_types
        assert "naming" in check_types

    def test_validate_runs_specific_checks(self):
        """Should run only specified checks."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate(circuit, checks=["properties"])

        # Should only have properties checks
        check_types = {i.check_type for i in issues}
        assert "properties" in check_types
        assert "manufacturing" not in check_types
        assert "naming" not in check_types

    def test_validate_multiple_specific_checks(self):
        """Should run multiple specified checks."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate(circuit, checks=["properties", "manufacturing"])

        # Should have properties and manufacturing checks
        check_types = {i.check_type for i in issues}
        assert "properties" in check_types
        assert "manufacturing" in check_types
        assert "naming" not in check_types

    def test_validate_returns_list(self):
        """Should return list of ValidationIssue objects."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate(circuit)

        assert isinstance(issues, list)
        assert all(isinstance(i, cs.ValidationIssue) for i in issues)

    def test_validate_empty_circuit(self):
        """Should handle empty circuit."""
        circuit = cs.Circuit("Test")

        issues = cs.validate(circuit)

        # Empty circuit should have no issues
        assert isinstance(issues, list)
        assert len(issues) == 0


class TestValidationWorkflow:
    """Test real-world validation workflows."""

    def test_workflow_find_all_errors(self):
        """User can find all errors in circuit."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()
        r1.footprint = ""  # Remove footprint

        issues = cs.validate(circuit)
        errors = [i for i in issues if i.severity == "error"]

        assert len(errors) > 0
        assert all(isinstance(e, cs.ValidationIssue) for e in errors)

    def test_workflow_filter_by_severity(self):
        """User can filter issues by severity."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate(circuit)

        # Filter warnings
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) > 0

    def test_workflow_filter_by_component(self):
        """User can filter issues by component."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        r2 = cs.Component("Device:R", ref="R", value="20k")
        circuit.add_component(r1)
        circuit.add_component(r2)
        circuit.finalize_references()

        issues = cs.validate(circuit)

        # Filter by component
        r1_issues = [i for i in issues if i.component == "R1"]
        r2_issues = [i for i in issues if i.component == "R2"]

        assert len(r1_issues) > 0
        assert len(r2_issues) > 0

    def test_workflow_print_formatted_report(self):
        """User can print formatted validation report."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)
        circuit.finalize_references()

        issues = cs.validate(circuit)

        # Print formatted report
        report = "\n".join(str(issue) for issue in issues)

        assert len(report) > 0
        assert "[" in report  # Has severity markers
        assert "R1" in report  # Has component references

    def test_workflow_manufacturing_readiness(self):
        """User can check manufacturing readiness."""
        circuit = cs.Circuit("Test")
        r1 = cs.Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        circuit.add_component(r1)
        circuit.finalize_references()
        r1.MPN = "RC0603FR-0710KL"
        r1.Power = "0.1W"

        issues = cs.validate_manufacturing(circuit)
        errors = [i for i in issues if i.severity == "error"]

        # Should have no manufacturing errors
        assert len(errors) == 0
