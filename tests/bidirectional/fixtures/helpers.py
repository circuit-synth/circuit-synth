"""Verification helper functions for bidirectional synchronization tests.

These helpers use kicad-sch-api to verify EXACT schematic contents,
ensuring that CRUD operations preserve all other elements.
"""

from pathlib import Path
from typing import Dict, Set, Optional, List, Tuple
from kicad_sch_api import Schematic


def verify_components(
    schematic_path: Path,
    expected_refs: Set[str],
    message: str = "Components"
) -> Dict[str, any]:
    """Verify EXACTLY the expected components exist in schematic.

    Note: Excludes power symbols (references starting with #PWR).

    Args:
        schematic_path: Path to .kicad_sch file
        expected_refs: Set of expected component references (e.g., {"R1", "R2", "C1"})
        message: Context message for assertion failures

    Returns:
        Dict mapping reference to component object for further verification

    Raises:
        AssertionError: If components don't match expected set
    """
    sch = Schematic.load(str(schematic_path))

    # Exclude power symbols from component list
    regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
    actual_refs = {c.reference for c in regular_components}

    assert actual_refs == expected_refs, (
        f"{message} mismatch:\n"
        f"  Expected: {sorted(expected_refs)}\n"
        f"  Actual:   {sorted(actual_refs)}\n"
        f"  Missing:  {sorted(expected_refs - actual_refs)}\n"
        f"  Extra:    {sorted(actual_refs - expected_refs)}"
    )

    # Return dict for easy lookup
    return {c.reference: c for c in regular_components}


def verify_power_symbols(
    schematic_path: Path,
    expected_power: Set[str],
    message: str = "Power symbols"
) -> Dict[str, any]:
    """Verify EXACTLY the expected power symbols exist in schematic.

    Note: Power symbols are components with references starting with #PWR.

    Args:
        schematic_path: Path to .kicad_sch file
        expected_power: Set of expected power symbol values (e.g., {"VCC", "GND"})
        message: Context message for assertion failures

    Returns:
        Dict mapping power value to power symbol component

    Raises:
        AssertionError: If power symbols don't match expected set
    """
    sch = Schematic.load(str(schematic_path))

    # Power symbols are components with references starting with #PWR
    power_components = [c for c in sch.components if c.reference.startswith("#PWR")]
    actual_power = {p.value for p in power_components}

    assert actual_power == expected_power, (
        f"{message} mismatch:\n"
        f"  Expected: {sorted(expected_power)}\n"
        f"  Actual:   {sorted(actual_power)}\n"
        f"  Missing:  {sorted(expected_power - actual_power)}\n"
        f"  Extra:    {sorted(actual_power - expected_power)}"
    )

    # Return dict for easy lookup
    return {p.value: p for p in power_components}


def verify_labels(
    schematic_path: Path,
    expected_labels: Set[str],
    message: str = "Labels"
) -> Dict[str, any]:
    """Verify EXACTLY the expected labels exist in schematic.

    Args:
        schematic_path: Path to .kicad_sch file
        expected_labels: Set of expected label texts (e.g., {"DATA", "CLK"})
        message: Context message for assertion failures

    Returns:
        Dict mapping label text to label object

    Raises:
        AssertionError: If labels don't match expected set
    """
    sch = Schematic.load(str(schematic_path))
    actual_labels = {l.text for l in sch.labels}

    assert actual_labels == expected_labels, (
        f"{message} mismatch:\n"
        f"  Expected: {sorted(expected_labels)}\n"
        f"  Actual:   {sorted(actual_labels)}\n"
        f"  Missing:  {sorted(expected_labels - actual_labels)}\n"
        f"  Extra:    {sorted(actual_labels - expected_labels)}"
    )

    # Return dict for easy lookup
    return {l.text: l for l in sch.labels}


def verify_component_properties(
    component: any,
    expected_ref: str,
    expected_value: Optional[str] = None,
    expected_footprint: Optional[str] = None,
    expected_symbol: Optional[str] = None,
    message: str = "Component properties"
) -> None:
    """Verify component has expected properties.

    Args:
        component: Component object from kicad-sch-api
        expected_ref: Expected reference (e.g., "R1")
        expected_value: Expected value (e.g., "10k"), None to skip check
        expected_footprint: Expected footprint substring (e.g., "0603"), None to skip check
        expected_symbol: Expected symbol (e.g., "Device:R"), None to skip check
        message: Context message for assertion failures

    Raises:
        AssertionError: If any property doesn't match
    """
    assert component.reference == expected_ref, (
        f"{message} - Reference mismatch:\n"
        f"  Expected: {expected_ref}\n"
        f"  Actual:   {component.reference}"
    )

    if expected_value is not None:
        assert component.value == expected_value, (
            f"{message} - Value mismatch for {expected_ref}:\n"
            f"  Expected: {expected_value}\n"
            f"  Actual:   {component.value}"
        )

    if expected_footprint is not None:
        assert expected_footprint in component.footprint, (
            f"{message} - Footprint mismatch for {expected_ref}:\n"
            f"  Expected substring: {expected_footprint}\n"
            f"  Actual:   {component.footprint}"
        )

    if expected_symbol is not None:
        assert component.symbol == expected_symbol, (
            f"{message} - Symbol mismatch for {expected_ref}:\n"
            f"  Expected: {expected_symbol}\n"
            f"  Actual:   {component.symbol}"
        )


def verify_component_unchanged(
    component_before: any,
    component_after: any,
    message: str = "Component preservation"
) -> None:
    """Verify component properties are completely unchanged.

    Args:
        component_before: Component object from initial state
        component_after: Component object from updated state
        message: Context message for assertion failures

    Raises:
        AssertionError: If any property changed
    """
    ref = component_before.reference

    assert component_after.reference == component_before.reference, (
        f"{message} - Reference changed:\n"
        f"  Before: {component_before.reference}\n"
        f"  After:  {component_after.reference}"
    )

    assert component_after.value == component_before.value, (
        f"{message} - Value changed for {ref}:\n"
        f"  Before: {component_before.value}\n"
        f"  After:  {component_after.value}"
    )

    assert component_after.footprint == component_before.footprint, (
        f"{message} - Footprint changed for {ref}:\n"
        f"  Before: {component_before.footprint}\n"
        f"  After:  {component_after.footprint}"
    )

    assert component_after.symbol == component_before.symbol, (
        f"{message} - Symbol changed for {ref}:\n"
        f"  Before: {component_before.symbol}\n"
        f"  After:  {component_after.symbol}"
    )

    assert component_after.position == component_before.position, (
        f"{message} - Position changed for {ref}:\n"
        f"  Before: {component_before.position}\n"
        f"  After:  {component_after.position}"
    )

    # Note: Rotation comparison may need tolerance
    assert component_after.rotation == component_before.rotation, (
        f"{message} - Rotation changed for {ref}:\n"
        f"  Before: {component_before.rotation}°\n"
        f"  After:  {component_after.rotation}°"
    )


def verify_sync_log(
    stdout: str,
    expected_operation: str,
    expected_ref: str,
    message: str = "Sync log"
) -> None:
    """Verify synchronization log shows expected operation.

    Args:
        stdout: Subprocess stdout output
        expected_operation: Expected operation ("Add", "Update", "Delete")
        expected_ref: Expected component reference (e.g., "R2")
        message: Context message for assertion failures

    Raises:
        AssertionError: If expected operation not found in log
    """
    # Check for both emoji and plain text versions
    emoji_map = {
        "Add": "➕",
        "Update": "🔄",
        "Delete": "❌",
    }

    emoji_pattern = f"{emoji_map.get(expected_operation, '')} {expected_operation}: {expected_ref}"
    plain_pattern = f"{expected_operation}: {expected_ref}"

    found = emoji_pattern in stdout or plain_pattern in stdout

    assert found, (
        f"{message} - Expected operation not found:\n"
        f"  Looking for: '{emoji_pattern}' or '{plain_pattern}'\n"
        f"  STDOUT:\n{stdout}"
    )


def verify_comprehensive_fixture_state(
    schematic_path: Path,
    message: str = "Comprehensive fixture state"
) -> Tuple[Dict[str, any], Dict[str, any], Dict[str, any]]:
    """Verify the complete initial state of comprehensive_root fixture.

    This is the standard initial state for all Phase 1 tests.

    Expected state:
    - Components: R1, R2, C1
    - Power: VCC, GND
    - Labels: DATA, CLK

    Args:
        schematic_path: Path to .kicad_sch file
        message: Context message for assertion failures

    Returns:
        Tuple of (components_dict, power_dict, labels_dict)

    Raises:
        AssertionError: If state doesn't match expected fixture
    """
    components = verify_components(
        schematic_path,
        expected_refs={"R1", "R2", "C1"},
        message=f"{message} - Components"
    )

    power = verify_power_symbols(
        schematic_path,
        expected_power={"VCC", "GND"},
        message=f"{message} - Power"
    )

    labels = verify_labels(
        schematic_path,
        expected_labels={"DATA", "CLK"},
        message=f"{message} - Labels"
    )

    return components, power, labels


def print_verification_summary(
    test_name: str,
    components: Dict[str, any],
    power: Dict[str, any],
    labels: Dict[str, any],
    modified_component: Optional[str] = None
) -> None:
    """Print a summary of verification results.

    Args:
        test_name: Name of the test
        components: Component dict from verification
        power: Power dict from verification
        labels: Labels dict from verification
        modified_component: Reference of component that was modified (if any)
    """
    print(f"\n{'='*70}")
    print(f"✅ {test_name} - Verification Summary")
    print(f"{'='*70}")
    print(f"Components: {sorted(components.keys())}")
    print(f"Power:      {sorted(power.keys())}")
    print(f"Labels:     {sorted(labels.keys())}")

    if modified_component:
        comp = components[modified_component]
        print(f"\nModified component: {modified_component}")
        print(f"  Value:     {comp.value}")
        print(f"  Footprint: {comp.footprint}")
        print(f"  Symbol:    {comp.symbol}")
        print(f"  Position:  {comp.position}")

    print(f"\n{'='*70}")
    print(f"🎉 PRESERVATION TEST PASSED")
    print(f"{'='*70}\n")
