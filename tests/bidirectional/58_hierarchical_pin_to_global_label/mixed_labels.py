#!/usr/bin/env python3
"""
Fixture: Mixed hierarchical and global labels in same design.

Demonstrates MIXED LABELING strategy:
- Parent sheet with power distribution (VCC, GND) via hierarchical pins
- Subcircuit A receives power hierarchically AND connects to SPI_CLK globally
- Subcircuit B provides SPI_CLK via global label (peer-to-peer connectivity)

This is the REAL-WORLD pattern for complex designs:
- Power flows hierarchically (parent → children)
- Signal buses connect globally (peer-to-peer across sheets)

Key validation: Subcircuit A must have BOTH hierarchical_label (for VCC)
and global_label (for SPI_CLK) in the same sheet.
"""

from circuit_synth import circuit, Component, Circuit, Net


@circuit(name="mixed_labels")
def mixed_labels():
    """Root circuit with mixed hierarchical and global labeling.

    Architecture:
    - Parent: R1 on VCC power net, hierarchical connection to Subcircuit A
    - Subcircuit A: R2 receives VCC hierarchically, connects to SPI_CLK globally
    - Subcircuit B: R3 provides SPI_CLK globally

    Mixed labeling in Subcircuit A:
    - hierarchical_label "VCC" (from parent)
    - global_label "SPI_CLK" (to peer Subcircuit B)
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # =========================================================================
    # Parent Sheet: Power Distribution (Hierarchical)
    # =========================================================================

    # Create power net on parent sheet
    vcc_net = Net("VCC")
    gnd_net = Net("GND")

    # Parent component on VCC net
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r1[1] += vcc_net  # R1 pin 1 to VCC
    r1[2] += gnd_net  # R1 pin 2 to GND

    # =========================================================================
    # Subcircuit A: Receives Power Hierarchically, Connects to SPI Globally
    # =========================================================================

    subcircuit_a = Circuit("SubcircuitA")

    # R2 receives power hierarchically from parent
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect R2 to hierarchical power (will become hierarchical_label in KiCad)
    # Using the parent's vcc_net automatically creates hierarchical connection
    r2[1] += vcc_net  # Receives VCC from parent hierarchically

    # Create net for SPI_CLK (peer-to-peer connectivity)
    # NOTE: circuit-synth currently only supports hierarchical_label, not global_label
    # This is Issue #380 - for now this will create hierarchical_label
    # But the TEST validates whether global_label support exists
    spi_clk_net = Net("SPI_CLK")

    # Connect R2 to SPI_CLK net
    r2[2] += spi_clk_net  # R2 pin 2 to SPI_CLK (will be hierarchical_label in current version)

    subcircuit_a.add_component(r2)

    root.add_subcircuit(subcircuit_a)

    # =========================================================================
    # Subcircuit B: Provides SPI_CLK Globally (Peer to A)
    # =========================================================================

    subcircuit_b = Circuit("SubcircuitB")

    # R3 provides SPI_CLK
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect R3 to SPI_CLK net
    r3[1] += spi_clk_net  # R3 pin 1 to SPI_CLK (will be hierarchical_label in current version)

    subcircuit_b.add_component(r3)

    root.add_subcircuit(subcircuit_b)

    # START_MARKER: Test will add parent component with global label here
    # END_MARKER


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = mixed_labels()

    circuit_obj.generate_kicad_project(
        project_name="mixed_labels",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Mixed labels circuit generated successfully!")
    print("📁 Open in KiCad: mixed_labels/mixed_labels.kicad_pro")
    print()
    print("🔍 Key Validation Points:")
    print("   - Parent sheet has hierarchical sheet pin for VCC → SubcircuitA")
    print("   - SubcircuitA has hierarchical_label 'VCC' (from parent)")
    print("   - SubcircuitA SHOULD have global_label 'SPI_CLK' (to peer)")
    print("   - SubcircuitB SHOULD have global_label 'SPI_CLK' (from peer)")
    print()
    print("⚠️  NOTE: circuit-synth currently only supports hierarchical_label (Issue #380)")
    print("   This test validates whether mixed label support has been implemented.")
    print("   Expected to XFAIL until Issue #380 is resolved.")
