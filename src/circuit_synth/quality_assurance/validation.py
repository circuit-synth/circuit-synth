"""
Schematic validation utilities for design checking.

Provides validation functions to check schematics for:
- Missing or incomplete component properties
- Manufacturing readiness
- Naming convention compliance
- Design standards

Example:
    >>> import circuit_synth as cs
    >>> circuit = cs.Circuit("MyCircuit")
    >>> r1 = cs.Component("Device:R", ref="R", value="10k")
    >>> circuit.add_component(r1)
    >>> circuit.finalize_references()
    >>>
    >>> # Validate properties
    >>> issues = cs.validate_properties(circuit, required=['MPN', 'Package'])
    >>> for issue in issues:
    ...     print(f"[{issue.severity}] {issue.component}: {issue.message}")
    >>>
    >>> # Validate manufacturing readiness
    >>> mfg_issues = cs.validate_manufacturing(circuit)
    >>>
    >>> # Run all validations
    >>> all_issues = cs.validate(circuit)
"""

from dataclasses import dataclass
from typing import List, Optional

from ..core.circuit import Circuit


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found in a schematic.

    Attributes:
        severity: Issue severity ('error', 'warning', 'info')
        component: Component reference (if applicable)
        message: Human-readable issue description
        location: Position in schematic (if applicable)
        check_type: Type of check that found this issue
    """

    severity: str
    message: str
    check_type: str
    component: Optional[str] = None
    location: Optional[tuple] = None

    def __str__(self) -> str:
        """Format issue as string."""
        comp_str = f"{self.component}: " if self.component else ""
        return f"[{self.severity.upper()}] {comp_str}{self.message}"


def validate_properties(
    circuit: Circuit, required: Optional[List[str]] = None
) -> List[ValidationIssue]:
    """
    Check components have required properties.

    Validates that all components in the circuit have the specified properties.
    Default required properties are MPN, Package, and Datasheet.

    Args:
        circuit: Circuit to validate
        required: List of required property names. If None, uses default list.

    Returns:
        List of validation issues found

    Example:
        >>> circuit = cs.Circuit("Test")
        >>> r1 = cs.Component("Device:R", ref="R", value="10k")
        >>> circuit.add_component(r1)
        >>> circuit.finalize_references()
        >>> issues = cs.validate_properties(circuit, required=['MPN', 'Tolerance'])
        >>> for issue in issues:
        ...     print(issue)
        [WARNING] R1: Missing property: MPN
        [WARNING] R1: Missing property: Tolerance
    """
    issues = []
    required = required or ["MPN", "Package", "Datasheet"]

    # Iterate over component objects (not keys)
    for comp in circuit.components.values():
        for prop in required:
            # Check if component has this property (stored in _extra_fields)
            # Properties are accessed as attributes via __getattr__
            if not hasattr(comp, prop) or getattr(comp, prop, None) is None:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        component=comp.ref,
                        message=f"Missing property: {prop}",
                        check_type="properties",
                    )
                )

    return issues


def validate_manufacturing(circuit: Circuit) -> List[ValidationIssue]:
    """
    Check manufacturing readiness.

    Validates that the circuit is ready for manufacturing by checking:
    - All components have footprints (ERROR if missing)
    - All components have MPN (WARNING if missing)
    - Resistors have power ratings (WARNING if missing)
    - Capacitors have voltage ratings (WARNING if missing)

    Args:
        circuit: Circuit to validate

    Returns:
        List of validation issues found

    Example:
        >>> circuit = cs.Circuit("Test")
        >>> r1 = cs.Component("Device:R", ref="R", value="10k")
        >>> circuit.add_component(r1)
        >>> circuit.finalize_references()
        >>> issues = cs.validate_manufacturing(circuit)
        >>> errors = [i for i in issues if i.severity == 'error']
        >>> if errors:
        ...     print(f"Found {len(errors)} manufacturing errors")
    """
    issues = []

    for comp in circuit.components.values():
        # Missing footprint is an error (blocks manufacturing)
        if not comp.footprint:
            issues.append(
                ValidationIssue(
                    severity="error",
                    component=comp.ref,
                    message="Missing footprint (required for manufacturing)",
                    check_type="manufacturing",
                )
            )

        # Missing MPN is a warning (makes sourcing harder)
        if not hasattr(comp, "MPN") or not getattr(comp, "MPN", None):
            issues.append(
                ValidationIssue(
                    severity="warning",
                    component=comp.ref,
                    message="Missing MPN",
                    check_type="manufacturing",
                )
            )

        # Component-specific checks based on symbol
        if "Device:R" in comp.symbol or "Resistor" in comp.symbol:
            # Resistors should have power rating
            if not hasattr(comp, "Power") or not getattr(comp, "Power", None):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        component=comp.ref,
                        message="Missing power rating",
                        check_type="manufacturing",
                    )
                )

        elif "Device:C" in comp.symbol or "Capacitor" in comp.symbol:
            # Capacitors should have voltage rating
            if not hasattr(comp, "Voltage") or not getattr(comp, "Voltage", None):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        component=comp.ref,
                        message="Missing voltage rating",
                        check_type="manufacturing",
                    )
                )

    return issues


def validate_naming(circuit: Circuit) -> List[ValidationIssue]:
    """
    Validate reference designator naming conventions.

    Checks that components follow standard naming conventions:
    - Resistors start with 'R'
    - Capacitors start with 'C'
    - Inductors start with 'L'
    - Diodes start with 'D'
    - ICs start with 'U'
    - Connectors start with 'J'

    Args:
        circuit: Circuit to validate

    Returns:
        List of validation issues found

    Example:
        >>> circuit = cs.Circuit("Test")
        >>> r1 = cs.Component("Device:R", ref="R", value="10k")
        >>> circuit.add_component(r1)
        >>> circuit.finalize_references()
        >>> issues = cs.validate_naming(circuit)
        >>> for issue in issues:
        ...     print(issue)
    """
    issues = []

    # Expected prefix mapping
    prefix_map = {
        "Device:R": "R",
        "Resistor": "R",
        "Device:C": "C",
        "Capacitor": "C",
        "Device:L": "L",
        "Inductor": "L",
        "Device:D": "D",
        "Diode": "D",
        "Device:LED": "D",  # LEDs typically use D prefix
        "Connector": "J",
    }

    for comp in circuit.components.values():
        # Check if symbol matches any known patterns
        expected_prefix = None
        for lib_pattern, prefix in prefix_map.items():
            if lib_pattern in comp.symbol:
                expected_prefix = prefix
                break

        if expected_prefix:
            if not comp.ref.startswith(expected_prefix):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        component=comp.ref,
                        message=f"Expected prefix '{expected_prefix}' for {comp.symbol}",
                        check_type="naming",
                    )
                )

    # Check for sequential numbering gaps (informational)
    by_prefix = {}
    for comp in circuit.components.values():
        # Extract prefix and number
        prefix = "".join(c for c in comp.ref if not c.isdigit())
        number_str = "".join(c for c in comp.ref if c.isdigit())
        if number_str:
            by_prefix.setdefault(prefix, []).append(int(number_str))

    for prefix, numbers in by_prefix.items():
        numbers.sort()
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            issues.append(
                ValidationIssue(
                    severity="info",
                    message=f"Non-sequential numbering for {prefix}: {numbers}",
                    check_type="naming",
                )
            )

    return issues


def validate(
    circuit: Circuit, checks: Optional[List[str]] = None
) -> List[ValidationIssue]:
    """
    Run multiple validation checks on a circuit.

    Convenience function that runs specified validation checks and returns
    all issues found.

    Args:
        circuit: Circuit to validate
        checks: List of check types to run. Available:
            - 'properties': Check required properties
            - 'manufacturing': Check manufacturing readiness
            - 'naming': Check naming conventions
            - 'all': Run all checks (default)

    Returns:
        List of all validation issues found

    Example:
        >>> circuit = cs.Circuit("Test")
        >>> r1 = cs.Component("Device:R", ref="R", value="10k")
        >>> circuit.add_component(r1)
        >>> circuit.finalize_references()
        >>>
        >>> # Run all checks
        >>> all_issues = cs.validate(circuit)
        >>>
        >>> # Run specific checks
        >>> mfg_issues = cs.validate(circuit, checks=['manufacturing'])
        >>>
        >>> # Display results
        >>> for issue in all_issues:
        ...     print(issue)
    """
    checks = checks or ["all"]
    all_issues = []

    if "all" in checks or "properties" in checks:
        all_issues.extend(validate_properties(circuit))

    if "all" in checks or "manufacturing" in checks:
        all_issues.extend(validate_manufacturing(circuit))

    if "all" in checks or "naming" in checks:
        all_issues.extend(validate_naming(circuit))

    return all_issues
