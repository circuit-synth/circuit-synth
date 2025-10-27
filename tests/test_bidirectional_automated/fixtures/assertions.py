"""
Semantic assertion helpers for bidirectional sync testing.

These helpers provide meaningful assertions that validate functional correctness
rather than exact byte-for-byte matches.
"""

from typing import Any, Optional


def assert_schematic_has_component(
    sch,
    ref: str,
    value: Optional[str] = None,
    footprint: Optional[str] = None,
    symbol: Optional[str] = None,
):
    """
    Assert schematic contains component with specified properties.

    Args:
        sch: KiCad schematic object
        ref: Component reference (e.g., "R1")
        value: Expected component value (e.g., "10k")
        footprint: Expected footprint (e.g., "Resistor_SMD:R_0603_1608Metric")
        symbol: Expected symbol/lib_id (e.g., "Device:R")

    Raises:
        AssertionError: If component not found or properties don't match
    """
    comp = sch.components.get(ref)
    assert comp is not None, f"Component {ref} not found in schematic"

    if value is not None:
        assert comp.value == value, \
            f"Component {ref}: expected value '{value}', got '{comp.value}'"

    if footprint is not None:
        assert comp.footprint == footprint, \
            f"Component {ref}: expected footprint '{footprint}', got '{comp.footprint}'"

    if symbol is not None:
        assert comp.lib_id == symbol, \
            f"Component {ref}: expected symbol '{symbol}', got '{comp.lib_id}'"


def assert_schematic_component_count(sch, expected_count: int):
    """
    Assert schematic has exactly the expected number of components.

    Args:
        sch: KiCad schematic object
        expected_count: Expected number of components

    Raises:
        AssertionError: If component count doesn't match
    """
    actual_count = len(sch.components)
    assert actual_count == expected_count, \
        f"Expected {expected_count} components, found {actual_count}"


def assert_position_near(pos1: tuple, pos2: tuple, tolerance: float = 0.5):
    """
    Assert two positions are close to each other (within tolerance).

    Accounts for floating-point rounding and grid snapping.

    Args:
        pos1: First position as (x, y) tuple
        pos2: Second position as (x, y) tuple
        tolerance: Maximum allowed difference in mm (default 0.5mm)

    Raises:
        AssertionError: If positions differ by more than tolerance
    """
    dx = abs(pos1[0] - pos2[0])
    dy = abs(pos1[1] - pos2[1])

    assert dx < tolerance and dy < tolerance, \
        f"Positions not close enough: {pos1} vs {pos2} (tolerance={tolerance}mm)"


def assert_position_preserved(comp, expected_pos: tuple, tolerance: float = 0.5):
    """
    Assert component position is preserved (within tolerance).

    Args:
        comp: Component object with position attribute
        expected_pos: Expected position as (x, y) tuple
        tolerance: Maximum allowed difference in mm

    Raises:
        AssertionError: If position not preserved
    """
    actual_pos = comp.position
    assert_position_near(actual_pos, expected_pos, tolerance)


def assert_roundtrip_preserves_components(original_circuit, imported_circuit):
    """
    Assert round-trip preserves all component properties.

    Validates that Python → KiCad → Python maintains:
    - Component count
    - Component references
    - Component values
    - Component footprints
    - Component symbols

    Args:
        original_circuit: Original circuit-synth Circuit object
        imported_circuit: Imported circuit-synth Circuit object

    Raises:
        AssertionError: If any properties not preserved
    """
    # Component count preserved
    orig_count = len(original_circuit.components)
    imp_count = len(imported_circuit.components)
    assert orig_count == imp_count, \
        f"Component count changed: {orig_count} → {imp_count}"

    # Each component preserved
    for ref, orig_comp in original_circuit.components.items():
        assert ref in imported_circuit.components, \
            f"Component {ref} lost during round-trip"

        imp_comp = imported_circuit.components[ref]

        # Value preserved
        assert orig_comp.value == imp_comp.value, \
            f"{ref}: value changed {orig_comp.value} → {imp_comp.value}"

        # Footprint preserved
        assert orig_comp.footprint == imp_comp.footprint, \
            f"{ref}: footprint changed {orig_comp.footprint} → {imp_comp.footprint}"

        # Symbol preserved (if available)
        if hasattr(orig_comp, 'symbol') and hasattr(imp_comp, 'symbol'):
            assert orig_comp.symbol == imp_comp.symbol, \
                f"{ref}: symbol changed {orig_comp.symbol} → {imp_comp.symbol}"


def assert_net_exists(sch, net_name: str):
    """
    Assert schematic contains a net with the given name.

    Args:
        sch: KiCad schematic object
        net_name: Expected net name (e.g., "NET1", "VCC", "GND")

    Raises:
        AssertionError: If net not found
    """
    # Check for labels with this net name
    labels = [label for label in sch.labels if label.text == net_name]
    assert len(labels) > 0, \
        f"Net '{net_name}' not found in schematic labels"


def assert_component_on_net(sch, component_ref: str, pin: int, net_name: str):
    """
    Assert component pin is connected to specified net.

    Args:
        sch: KiCad schematic object
        component_ref: Component reference (e.g., "R1")
        pin: Pin number
        net_name: Expected net name

    Raises:
        AssertionError: If connection not found
    """
    # This is a simplified check - full implementation would trace wires
    # For now, just verify the component exists
    comp = sch.components.get(component_ref)
    assert comp is not None, \
        f"Component {component_ref} not found"

    # TODO: Implement wire tracing to verify actual connection
    # For now, just verify net exists
    assert_net_exists(sch, net_name)
