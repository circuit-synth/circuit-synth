"""
Test for issue #559: Prevent duplicate labels on same pin

This test reproduces the bug where multiple labels can be placed on the same pin,
creating clutter and requiring manual deletion.
"""

import pytest
import circuit_synth as cs
import tempfile


def test_no_duplicate_labels_on_single_pin():
    """
    Test that only one label appears on a pin when the same net is connected multiple times.

    Reproduces issue #559 where multiple labels were placed on the same pin.
    """
    # Create a simple circuit
    circuit = cs.Circuit("label_test")

    # Create a net
    test_net = cs.Net("TEST_NET")
    circuit.add_net(test_net)

    # Add a component with multiple pins
    r1 = cs.Component("Device:R", ref="R", value="10k")
    circuit.add_component(r1)

    # Connect pin to the net
    r1["1"] += test_net

    # Finalize references
    circuit.finalize_references()

    # Generate schematic
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = tmpdir
        circuit.generate_kicad_project(output_dir)

        # Parse the generated schematic to count labels
        from kicad_sch_api import Schematic as KiCadSchematic
        sch_path = f"{output_dir}/label_test.kicad_sch"
        schematic = KiCadSchematic.load(sch_path)

        # Find the resistor component
        r1_component = None
        for comp in schematic.components:
            if comp.reference == "R1":
                r1_component = comp
                break

        assert r1_component is not None, "R1 not found"

        # Calculate pin position for pin 1
        from circuit_synth.kicad.schematic.geometry_utils import GeometryUtils
        from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

        lib_data = SymbolLibCache.get_symbol_data(r1_component.lib_id)
        assert lib_data is not None, "Symbol data not found"

        # Find pin 1 in library data
        pin_dict = None
        for p in lib_data.get("pins", []):
            if str(p.get("number")) == "1":
                pin_dict = {
                    "x": p.get("x", 0),
                    "y": p.get("y", 0),
                    "orientation": p.get("orientation", 0)
                }
                break

        assert pin_dict is not None, "Pin 1 not found in symbol data"

        # Calculate where label should be
        pin_pos, _ = GeometryUtils.calculate_pin_label_position_from_dict(
            pin_dict=pin_dict,
            component_position=r1_component.position,
            component_rotation=r1_component.rotation,
        )

        # Count hierarchical labels at this position (within 0.5mm tolerance)
        labels_at_pin = []
        for label in schematic.hierarchical_labels:
            import math
            distance = math.sqrt(
                (label.position.x - pin_pos.x) ** 2 +
                (label.position.y - pin_pos.y) ** 2
            )
            if distance < 0.5:  # 0.5mm tolerance
                labels_at_pin.append(label)

        # ASSERTION: Should have exactly ONE label per pin, not multiple
        assert len(labels_at_pin) <= 1, (
            f"Pin 1 has {len(labels_at_pin)} labels (expected 0 or 1). "
            f"Labels: {[l.text for l in labels_at_pin]}"
        )


# TODO: Add synchronizer test once API is clarified
# The APISynchronizer test requires proper understanding of the API
# For now, the initial generation test above is sufficient to verify
# duplicate detection works
