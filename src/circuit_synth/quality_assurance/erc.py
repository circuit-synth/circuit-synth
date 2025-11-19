"""
KiCAD Electrical Rules Check (ERC) integration.

Provides Python API to run KiCAD's built-in ERC via kicad-cli command.
Allows programmatic electrical rule checking without manual KiCAD GUI interaction.

Example:
    >>> import circuit_synth as cs
    >>>
    >>> # Run ERC on a schematic file
    >>> try:
    >>>     results = cs.run_erc("design.kicad_sch")
    >>>     print(f"Errors: {results.error_count}, Warnings: {results.warning_count}")
    >>>
    >>>     for violation in results.violations:
    >>>         print(f"[{violation.severity}] {violation.description}")
    >>> except cs.KiCADNotFoundError:
    >>>     print("KiCAD not installed")
"""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ..core.kicad_validator import get_kicad_paths, validate_kicad_installation
from .validation import ValidationIssue


@dataclass
class ERCViolation:
    """
    Represents a single ERC violation.

    Attributes:
        type: Violation type (e.g., 'unconnected_pin', 'pin_conflict')
        severity: 'error' or 'warning'
        description: Human-readable violation description
        location: (x, y) position in schematic (mm)
        component: Component reference (e.g., 'U1'), if applicable
        pin: Pin number, if applicable
        net: Net name, if applicable
    """

    type: str
    severity: str
    description: str
    location: Optional[Tuple[float, float]] = None
    component: Optional[str] = None
    pin: Optional[str] = None
    net: Optional[str] = None

    def to_validation_issue(self) -> ValidationIssue:
        """
        Convert ERC violation to ValidationIssue format.

        Allows integration with other validation utilities.

        Returns:
            ValidationIssue object
        """
        return ValidationIssue(
            severity=self.severity,
            message=self.description,
            check_type="erc",
            component=self.component,
            location=self.location,
        )


@dataclass
class ERCResults:
    """
    Results from KiCAD ERC check.

    Attributes:
        violations: List of ERC violations found
        error_count: Number of errors
        warning_count: Number of warnings
        schematic_path: Path to schematic file checked
    """

    violations: List[ERCViolation]
    error_count: int
    warning_count: int
    schematic_path: str

    def as_validation_issues(self) -> List[ValidationIssue]:
        """
        Convert all ERC violations to ValidationIssue format.

        Allows integration with other validation utilities.

        Returns:
            List of ValidationIssue objects
        """
        return [v.to_validation_issue() for v in self.violations]

    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return self.error_count > 0

    def has_warnings(self) -> bool:
        """Check if any warnings were found."""
        return self.warning_count > 0


class KiCADERCError(Exception):
    """Raised when KiCAD ERC execution fails."""

    pass


def run_erc(
    schematic_path: str,
    severity: str = "all",
    units: str = "mm",
    kicad_cli_path: Optional[str] = None,
) -> ERCResults:
    """
    Run KiCAD Electrical Rules Check on a schematic.

    Executes kicad-cli sch erc command and parses results.
    Requires KiCAD 8.0 or later to be installed.

    Args:
        schematic_path: Path to .kicad_sch file
        severity: Severity level to report ('all', 'error', 'warning')
        units: Measurement units for coordinates ('mm', 'in', 'mils')
        kicad_cli_path: Optional path to kicad-cli executable.
                       If None, will search standard locations.

    Returns:
        ERCResults object with violations and counts

    Raises:
        KiCADNotFoundError: If KiCAD CLI is not found
        KiCADERCError: If ERC execution fails
        FileNotFoundError: If schematic file doesn't exist

    Example:
        >>> results = cs.run_erc("design.kicad_sch")
        >>> if results.has_errors():
        ...     print(f"Found {results.error_count} errors!")
        ...     for v in results.violations:
        ...         if v.severity == 'error':
        ...             print(f"  {v.description}")
    """
    # Validate schematic file exists
    sch_path = Path(schematic_path)
    if not sch_path.exists():
        raise FileNotFoundError(f"Schematic file not found: {schematic_path}")

    # Find kicad-cli
    if kicad_cli_path is None:
        try:
            kicad_paths = get_kicad_paths()
            if not validate_kicad_installation():
                from ..core.kicad_validator import KiCadValidationError

                raise KiCadValidationError("KiCAD CLI not found")
            kicad_cli_path = kicad_paths.get("kicad-cli")
        except Exception as e:
            from ..core.kicad_validator import KiCadValidationError

            raise KiCadValidationError(f"KiCAD CLI not found: {e}")

    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as temp_file:
        temp_json_path = temp_file.name

    try:
        # Build kicad-cli command
        cmd = [
            str(kicad_cli_path),
            "sch",
            "erc",
            "--format",
            "json",
            "--output",
            temp_json_path,
            f"--severity-{severity}",
            "--units",
            units,
            str(sch_path),
        ]

        # Execute kicad-cli
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30  # 30 second timeout
        )

        # kicad-cli returns exit code 5 if violations exist (not an error)
        if result.returncode not in (0, 5):
            raise KiCADERCError(
                f"kicad-cli erc failed with exit code {result.returncode}: {result.stderr}"
            )

        # Parse JSON output
        with open(temp_json_path, "r") as f:
            erc_data = json.load(f)

        # Convert to ERCViolation objects
        violations = []
        for v_data in erc_data.get("violations", []):
            location = None
            if "location" in v_data:
                loc = v_data["location"]
                if "x" in loc and "y" in loc:
                    location = (loc["x"], loc["y"])

            violation = ERCViolation(
                type=v_data.get("type", "unknown"),
                severity=v_data.get("severity", "warning"),
                description=v_data.get("description", ""),
                location=location,
                component=v_data.get("reference"),
                pin=v_data.get("pin"),
                net=v_data.get("net"),
            )
            violations.append(violation)

        # Create results object
        results = ERCResults(
            violations=violations,
            error_count=erc_data.get("error_count", 0),
            warning_count=erc_data.get("warning_count", 0),
            schematic_path=str(schematic_path),
        )

        return results

    finally:
        # Clean up temp file
        Path(temp_json_path).unlink(missing_ok=True)
