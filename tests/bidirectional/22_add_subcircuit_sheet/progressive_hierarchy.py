#!/usr/bin/env python3
"""
Test fixture: Progressive subcircuit addition (1→2→3 hierarchy levels).

Demonstrates incremental hierarchical circuit development:
- Step 1: Single circuit with one resistor (1 level)
- Step 2: Add level 1 subcircuit (2 levels: main → level1)
- Step 3: Add level 2 subcircuit (3 levels: main → level1 → level2)

Used to test that adding subcircuits incrementally works and hierarchical
sheet symbols are generated correctly.

Each step builds on the previous, simulating real iterative development.
"""

from circuit_synth import circuit, Component


# STEP 3 circuits (uncomment to enable):
# @circuit(name="level2")
# def level2():
#     """Level 2 subcircuit (deepest level)."""
#     r3 = Component(
#         symbol="Device:R",
#         ref="R3",
#         value="20k",
#         footprint="Resistor_SMD:R_0603_1608Metric",
#     )


# STEP 2 circuits (uncomment to enable):
# @circuit(name="level1")
# def level1():
#     """Level 1 subcircuit."""
#     r2 = Component(
#         symbol="Device:R",
#         ref="R2",
#         value="4.7k",
#         footprint="Resistor_SMD:R_0603_1608Metric",
#     )
#     # STEP 3: Uncomment to add level 2 nesting
#     # level2()


@circuit(name="main")
def main():
    """Main circuit (root level)."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # STEP 2: Uncomment to add level 1 subcircuit
    # level1()


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = main()

    circuit_obj.generate_kicad_project(
        project_name="progressive_hierarchy",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Progressive hierarchy circuit generated!")
    print("📁 Open in KiCad: progressive_hierarchy/progressive_hierarchy.kicad_pro")
