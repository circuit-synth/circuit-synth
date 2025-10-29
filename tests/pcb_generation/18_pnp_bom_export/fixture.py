#!/usr/bin/env python3
"""
Fixture: PCB with components including DNP (Do Not Populate) for PnP export.

Creates a PCB with:
- R1: 10k, 0603, MPN=ABC123, DNP=false
- R2: 22k, 0603, MPN=ABC456, DNP=false
- C1: 100nF, 0603, MPN=XYZ789, DNP=true (do not place)
- R3: 47k, 0805, MPN=DEF111, DNP=false

Used to validate that pick-and-place (PnP) files and bill of materials (BOM)
can be exported with correct component data, positions, and DNP flags.

Critical for assembly: PnP file guides the automatic assembly machine,
while BOM is used for component procurement.
"""

from circuit_synth import circuit, Component


@circuit(name="pnp_bom_export")
def pnp_bom_export():
    """Circuit with components for PnP and BOM export testing."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="22k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="47k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )

    # Note: DNP flags and MPN are typically added via schematic properties
    # or in manufacturing data management systems


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = pnp_bom_export()

    circuit_obj.generate_kicad_project(
        project_name="pnp_bom_export",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=200.0,
        board_height_mm=150.0,
    )

    print("✅ PnP/BOM export test circuit generated successfully!")
    print("📁 Open in KiCad: pnp_bom_export/pnp_bom_export.kicad_pro")
