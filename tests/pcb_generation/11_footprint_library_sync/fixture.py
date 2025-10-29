#!/usr/bin/env python3
"""
Fixture: PCB with footprint library management.

Creates a PCB with a single resistor using standard 0603 package.
Used to validate that:
1. Footprints are correctly assigned from library
2. Footprint can be changed to different package
3. PCB regenerates with new footprint
4. Component position is preserved despite footprint change

Footprints used:
- Initial: Resistor_SMD:R_0603_1608Metric (0603 package)
- Modified: Resistor_SMD:R_0805_2012Metric (0805 package - larger)
"""

from circuit_synth import circuit, Component


@circuit(name="footprint_test_pcb")
def footprint_test_pcb():
    """Circuit with single resistor for footprint testing."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",  # 0603 package (small)
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = footprint_test_pcb()

    circuit_obj.generate_kicad_project(
        project_name="footprint_test_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Footprint test PCB generated successfully!")
    print("📁 Open in KiCad: footprint_test_pcb/footprint_test_pcb.kicad_pro")
