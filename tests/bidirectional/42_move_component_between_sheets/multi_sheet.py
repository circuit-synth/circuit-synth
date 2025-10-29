#!/usr/bin/env python3
"""
Fixture: Multi-sheet circuit for testing component movement between sheets.

This fixture creates circuits demonstrating component movement:
1. Initial state: R1, R2 on root; R3 on subcircuit
2. After move: R1 on root; R3, R4 on subcircuit (R2 moved and renumbered)

Circuit: Two resistors on root, one on subcircuit
"""

from circuit_synth import circuit, Component, Net, Circuit


@circuit(name="multi_sheet")
def multi_sheet_initial():
    """
    Create initial hierarchical circuit before moving component.

    Root sheet: R1 (10k), R2 (10k)
    Subcircuit: R3 (1k)

    R2 will be moved to subcircuit in next step.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Root nets
    net1 = Net(name="NET1")
    net2 = Net(name="NET2")

    net1 += r1[1]
    net2 += r1[2]
    net2 += r2[1]

    # Create subcircuit with existing component
    subcircuit = Circuit("SubCircuit")

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    subcircuit.add_component(r3)

    # Add subcircuit to root
    root.add_subcircuit(subcircuit)


@circuit(name="multi_sheet")
def multi_sheet_after_move():
    """
    Create circuit after moving R2 from root to subcircuit.

    Root sheet: R1 (10k) only
    Subcircuit: R3 (1k), R4 (10k) - R4 is R2 moved and renumbered

    This represents the state after user moves R2 to subcircuit.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet - only R1 remains
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Root nets - R2 connection now goes to subcircuit
    net1 = Net(name="NET1")
    net2 = Net(name="NET2")

    net1 += r1[1]
    net2 += r1[2]

    # Create subcircuit with R3 and moved R4
    subcircuit = Circuit("SubCircuit")

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R4 is R2 moved from root and renumbered
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Subcircuit nets - R4 connects to NET2 from root
    net2_sub = Net(name="NET2")  # Continues from root
    net3 = Net(name="NET3")

    net2_sub += r4[1]
    net3 += r4[2]

    subcircuit.add_component(r3)
    subcircuit.add_component(r4)
    subcircuit.add_net(net2_sub)
    subcircuit.add_net(net3)

    # Add subcircuit to root
    root.add_subcircuit(subcircuit)


@circuit(name="multi_sheet")
def multi_sheet_move_with_nets():
    """
    Create circuit demonstrating component move with net reassignment.

    Root sheet: R1 (10k) on NET1 and VOUT
    Subcircuit: R3 (1k), R4 (10k moved from root)

    This version explicitly shows net changes when moving R2 → R4.
    VOUT net is broken on root when R2 moves to subcircuit.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet - R1 only
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Root nets - VOUT now terminates at R1 (R2 moved away)
    vin = Net(name="VIN")
    vout = Net(name="VOUT")

    vin += r1[1]
    vout += r1[2]

    # Create subcircuit with R3 and moved R4
    subcircuit = Circuit("SubCircuit")

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R4 is R2 moved from root with new net assignments
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Subcircuit nets - R4 has independent nets in subcircuit
    vout_sub = Net(name="VOUT_SUB")
    gnd_sub = Net(name="GND_SUB")

    vout_sub += r4[1]
    gnd_sub += r4[2]

    subcircuit.add_component(r3)
    subcircuit.add_component(r4)
    subcircuit.add_net(vout_sub)
    subcircuit.add_net(gnd_sub)

    # Add subcircuit to root
    root.add_subcircuit(subcircuit)


if __name__ == "__main__":
    # Test initial state
    print("Testing initial multi-sheet circuit...")
    circuit_initial = multi_sheet_initial()

    circuit_initial.generate_kicad_project(
        project_name="multi_sheet_initial",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Initial circuit generated!")
    print("   Root: R1, R2")
    print("   Subcircuit: R3")
    print("📁 Open in KiCad: multi_sheet_initial/multi_sheet.kicad_pro")

    # Test after move
    print("\nTesting circuit after moving R2 to subcircuit...")
    circuit_after = multi_sheet_after_move()

    circuit_after.generate_kicad_project(
        project_name="multi_sheet_after",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ After-move circuit generated!")
    print("   Root: R1 only")
    print("   Subcircuit: R3, R4 (R2 moved and renumbered)")
    print("📁 Open in KiCad: multi_sheet_after/multi_sheet.kicad_pro")

    # Test with explicit net changes
    print("\nTesting circuit with net reassignment...")
    circuit_nets = multi_sheet_move_with_nets()

    circuit_nets.generate_kicad_project(
        project_name="multi_sheet_nets",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Net reassignment circuit generated!")
    print("   Root: R1 on VIN/VOUT")
    print("   Subcircuit: R3, R4 on VOUT_SUB/GND_SUB")
    print("📁 Open in KiCad: multi_sheet_nets/multi_sheet.kicad_pro")
