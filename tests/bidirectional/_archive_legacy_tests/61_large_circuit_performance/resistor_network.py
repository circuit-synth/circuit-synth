#!/usr/bin/env python3
"""
Large 10x10 resistor grid network for performance testing.

Grid layout (100 resistors total):
- All 100 resistors in series-parallel grid
- Grid spacing: 5mm between nodes
- All resistors: 1k initially
- R50 can be modified to 10k for testing

Example topology (simplified):
    o--R1--o--R2--o--R3--o ... (10 resistors per row)
    o--R11-o--R12-o--R13-o ...
    ...
    (10 rows total = 100 resistors)
"""

from circuit_synth import circuit, Component


@circuit(name="resistor_network")
def resistor_network():
    """Circuit with 100 resistors in a 10x10 grid."""

    # Create 100 resistors (R1-R100)
    for i in range(1, 101):
        Component(
            symbol="Device:R",
            ref=f"R{i}",
            value="1k",
            footprint="Resistor_SMD:R_0805_2012Metric",
        )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = resistor_network()

    circuit_obj.generate_kicad_project(
        project_name="resistor_network",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Resistor network circuit generated successfully!")
    print(f"📁 Components: {len(circuit_obj.components)}")
    print("📁 Open in KiCad: resistor_network/resistor_network.kicad_pro")
