"""
Tests for KiCAD ERC integration.

Tests the ERC module that integrates with kicad-cli sch erc command.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

import circuit_synth as cs


class TestERCViolation:
    """Test ERCViolation dataclass."""

    def test_erc_violation_creation(self):
        """Should create ERCViolation with all fields."""
        violation = cs.ERCViolation(
            type="unconnected_pin",
            severity="warning",
            description="Unconnected Pin 1 on U1",
            location=(27.94, 17.78),
            component="U1",
            pin="1",
            net="GND",
        )

        assert violation.type == "unconnected_pin"
        assert violation.severity == "warning"
        assert violation.description == "Unconnected Pin 1 on U1"
        assert violation.location == (27.94, 17.78)
        assert violation.component == "U1"
        assert violation.pin == "1"
        assert violation.net == "GND"

    def test_erc_violation_to_validation_issue(self):
        """Should convert ERCViolation to ValidationIssue."""
        violation = cs.ERCViolation(
            type="unconnected_pin",
            severity="warning",
            description="Unconnected Pin 1 on U1",
            location=(27.94, 17.78),
            component="U1",
            pin="1",
        )

        issue = violation.to_validation_issue()

        assert isinstance(issue, cs.ValidationIssue)
        assert issue.severity == "warning"
        assert issue.message == "Unconnected Pin 1 on U1"
        assert issue.check_type == "erc"
        assert issue.component == "U1"
        assert issue.location == (27.94, 17.78)


class TestERCResults:
    """Test ERCResults dataclass."""

    def test_erc_results_creation(self):
        """Should create ERCResults with violations."""
        violations = [
            cs.ERCViolation(
                type="unconnected_pin",
                severity="warning",
                description="Unconnected Pin 1",
                component="U1",
            ),
            cs.ERCViolation(
                type="pin_conflict",
                severity="error",
                description="Output conflict",
                component="U2",
            ),
        ]

        results = cs.ERCResults(
            violations=violations,
            error_count=1,
            warning_count=1,
            schematic_path="test.kicad_sch",
        )

        assert len(results.violations) == 2
        assert results.error_count == 1
        assert results.warning_count == 1
        assert results.schematic_path == "test.kicad_sch"

    def test_has_errors(self):
        """Should detect if errors exist."""
        results_with_errors = cs.ERCResults(
            violations=[], error_count=1, warning_count=0, schematic_path="test.sch"
        )
        results_without_errors = cs.ERCResults(
            violations=[], error_count=0, warning_count=1, schematic_path="test.sch"
        )

        assert results_with_errors.has_errors() is True
        assert results_without_errors.has_errors() is False

    def test_has_warnings(self):
        """Should detect if warnings exist."""
        results_with_warnings = cs.ERCResults(
            violations=[], error_count=0, warning_count=1, schematic_path="test.sch"
        )
        results_without_warnings = cs.ERCResults(
            violations=[], error_count=0, warning_count=0, schematic_path="test.sch"
        )

        assert results_with_warnings.has_warnings() is True
        assert results_without_warnings.has_warnings() is False

    def test_as_validation_issues(self):
        """Should convert all violations to ValidationIssues."""
        violations = [
            cs.ERCViolation(
                type="unconnected_pin",
                severity="warning",
                description="Unconnected Pin 1",
                component="U1",
            ),
            cs.ERCViolation(
                type="pin_conflict",
                severity="error",
                description="Output conflict",
                component="U2",
            ),
        ]

        results = cs.ERCResults(
            violations=violations,
            error_count=1,
            warning_count=1,
            schematic_path="test.kicad_sch",
        )

        issues = results.as_validation_issues()

        assert len(issues) == 2
        assert all(isinstance(i, cs.ValidationIssue) for i in issues)
        assert issues[0].check_type == "erc"
        assert issues[1].check_type == "erc"


class TestRunERC:
    """Test run_erc function."""

    @patch("subprocess.run")
    @patch("circuit_synth.quality_assurance.erc.get_kicad_paths")
    @patch("circuit_synth.quality_assurance.erc.validate_kicad_installation")
    def test_run_erc_success(
        self, mock_validate, mock_get_paths, mock_subprocess, tmp_path
    ):
        """Should run ERC successfully and parse results."""
        # Create temp schematic file
        sch_file = tmp_path / "test.kicad_sch"
        sch_file.write_text("(kicad_sch)")

        # Mock KiCAD paths
        mock_get_paths.return_value = {"kicad-cli": "/usr/bin/kicad-cli"}
        mock_validate.return_value = True

        # Mock subprocess result
        mock_result = Mock()
        mock_result.returncode = 5  # Violations exist
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Mock JSON output
        erc_data = {
            "violations": [
                {
                    "type": "unconnected_pin",
                    "severity": "warning",
                    "description": "Unconnected Pin 1 on U1",
                    "location": {"x": 27.94, "y": 17.78},
                    "reference": "U1",
                    "pin": "1",
                }
            ],
            "error_count": 0,
            "warning_count": 1,
        }

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                json.dumps(erc_data)
            )

            results = cs.run_erc(str(sch_file))

        assert results.error_count == 0
        assert results.warning_count == 1
        assert len(results.violations) == 1
        assert results.violations[0].component == "U1"
        assert results.violations[0].location == (27.94, 17.78)

    def test_run_erc_file_not_found(self):
        """Should raise FileNotFoundError for missing schematic."""
        with pytest.raises(FileNotFoundError):
            cs.run_erc("nonexistent.kicad_sch")

    @patch("circuit_synth.quality_assurance.erc.get_kicad_paths")
    @patch("circuit_synth.quality_assurance.erc.validate_kicad_installation")
    def test_run_erc_kicad_not_found(
        self, mock_validate, mock_get_paths, tmp_path
    ):
        """Should raise error when KiCAD not installed."""
        # Create temp schematic file
        sch_file = tmp_path / "test.kicad_sch"
        sch_file.write_text("(kicad_sch)")

        # Mock KiCAD not found
        mock_validate.return_value = False
        mock_get_paths.return_value = {}

        with pytest.raises(Exception):  # Will raise KiCadValidationError
            cs.run_erc(str(sch_file))

    @patch("subprocess.run")
    @patch("circuit_synth.quality_assurance.erc.get_kicad_paths")
    @patch("circuit_synth.quality_assurance.erc.validate_kicad_installation")
    def test_run_erc_command_failure(
        self, mock_validate, mock_get_paths, mock_subprocess, tmp_path
    ):
        """Should raise error when kicad-cli fails."""
        # Create temp schematic file
        sch_file = tmp_path / "test.kicad_sch"
        sch_file.write_text("(kicad_sch)")

        # Mock KiCAD paths
        mock_get_paths.return_value = {"kicad-cli": "/usr/bin/kicad-cli"}
        mock_validate.return_value = True

        # Mock subprocess failure
        mock_result = Mock()
        mock_result.returncode = 1  # Error
        mock_result.stderr = "Command failed"
        mock_subprocess.return_value = mock_result

        with pytest.raises(cs.KiCADERCError):
            cs.run_erc(str(sch_file))


class TestERCIntegration:
    """Test ERC integration with validation utilities."""

    def test_erc_integration_with_validation(self):
        """Should integrate ERC results with other validation checks."""
        # Create mock ERC results
        erc_violations = [
            cs.ERCViolation(
                type="unconnected_pin",
                severity="warning",
                description="Unconnected Pin 1",
                component="U1",
            )
        ]

        erc_results = cs.ERCResults(
            violations=erc_violations,
            error_count=0,
            warning_count=1,
            schematic_path="test.kicad_sch",
        )

        # Convert to ValidationIssues
        all_issues = erc_results.as_validation_issues()

        # Should have ERC issues
        erc_issues = [i for i in all_issues if i.check_type == "erc"]
        assert len(erc_issues) == 1
        assert erc_issues[0].component == "U1"
        assert erc_issues[0].severity == "warning"
