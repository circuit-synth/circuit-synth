#!/usr/bin/env python3
"""
Test fixture: Connected multi-level hierarchy with nets spanning all levels.

Demonstrates incremental hierarchical circuit development with electrical
connections passed through hierarchy levels.

This combines:
- Progressive subcircuit addition (1→2→3 levels)
- Net passing for cross-sheet connectivity
- Hierarchical pins and labels at each level

Used to test the complete hierarchical workflow with electrical connections.

Each step builds on previous:
- Step 1: main with R1 (1 level, no connections)
- Step 2: main → level1 with R1—R2 connected via passed net (2 levels)
- Step 3: main → level1 → level2 with R1—R2—R3 all connected (3 levels)
"""

from circuit_synth import circuit, Component, Net


# STEP 3 circuits (uncomment to enable):
# @circuit(name="level2")
# def level2(signal_net):
#     """Level 2 subcircuit - accepts signal_net from level1."""
#     r3 = Component(
#         symbol="Device:R",
#         ref="R3",
#         value="20k",
#         footprint="Resistor_SMD:R_0603_1608Metric",
#     )
#     # Connect R3 to signal passed from level1
#     r3[1] += signal_net


# STEP 2 circuits (uncomment to enable):
# @circuit(name="level1")
# def level1(signal_net):
#     """Level 1 subcircuit - accepts signal_net from main."""
#     r2 = Component(
#         symbol="Device:R",
#         ref="R2",
#         value="4.7k",
#         footprint="Resistor_SMD:R_0603_1608Metric",
#     )
#     # Connect R2 to signal passed from main
#     r2[1] += signal_net
#
#     # STEP 3: Pass signal to level2
#     # level2(signal_net=signal_net)


@circuit(name="main")
def main():
    """Main circuit (root level)."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # STEP 2: Uncomment to create signal and pass to level1
    # signal = Net("SIGNAL")
    # r1[1] += signal
    # level1(signal_net=signal)


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = main()

    circuit_obj.generate_kicad_project(
        project_name="connected_hierarchy",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Connected hierarchy circuit generated!")
    print("📁 Open in KiCad: connected_hierarchy/connected_hierarchy.kicad_pro")
