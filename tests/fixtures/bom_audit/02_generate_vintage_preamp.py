"""
Generate vintage_preamp.kicad_sch test fixture.

Scenario: Legacy design (2018), predates company part numbering system.
NO components have PartNumber or Manufacturer properties.
Compliance: 0%
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa


def main():
    """Generate vintage_preamp test fixture."""
    print("Generating vintage_preamp.kicad_sch...")

    # Create schematic
    sch = ksa.create_schematic("VintagePreamp")

    # U1: TL072 op-amp (NO PartNumber)
    u1 = sch.components.add(
        lib_id="Amplifier_Operational:TL072",
        reference="U1",
        value="TL072",
        position=(100, 100),
        footprint="Package_DIP:DIP-8_W7.62mm"
    )
    # Intentionally NO PartNumber or Manufacturer

    # R1-R4: Resistors (NO PartNumber)
    r1 = sch.components.add(
        lib_id="Device:R",
        reference="R1",
        value="10k",
        position=(80, 100),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r1.set_property("Tolerance", "1%")  # Has tolerance but not PartNumber

    r2 = sch.components.add(
        lib_id="Device:R",
        reference="R2",
        value="10k",
        position=(120, 100),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r2.set_property("Tolerance", "1%")

    r3 = sch.components.add(
        lib_id="Device:R",
        reference="R3",
        value="100k",
        position=(80, 120),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r3.set_property("Tolerance", "1%")

    r4 = sch.components.add(
        lib_id="Device:R",
        reference="R4",
        value="47k",
        position=(120, 120),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r4.set_property("Tolerance", "1%")

    # C1-C5: Capacitors (NO PartNumber)
    c1 = sch.components.add(
        lib_id="Device:C",
        reference="C1",
        value="100nF",
        position=(80, 140),
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c1.set_property("Tolerance", "10%")

    c2 = sch.components.add(
        lib_id="Device:C",
        reference="C2",
        value="100nF",
        position=(120, 140),
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c2.set_property("Tolerance", "10%")

    c3 = sch.components.add(
        lib_id="Device:C_Polarized",
        reference="C3",
        value="10uF",
        position=(100, 140),
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    c3.set_property("Tolerance", "20%")

    c4 = sch.components.add(
        lib_id="Device:C_Polarized",
        reference="C4",
        value="10uF",
        position=(100, 160),
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    c4.set_property("Tolerance", "20%")

    c5 = sch.components.add(
        lib_id="Device:C",
        reference="C5",
        value="100nF",
        position=(100, 180),
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    c5.set_property("Tolerance", "10%")

    # J1-J2: Audio jacks (NO PartNumber)
    j1 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x02",
        reference="J1",
        value="Audio_In",
        position=(60, 100)
    )

    j2 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x02",
        reference="J2",
        value="Audio_Out",
        position=(140, 100)
    )

    # Save schematic
    output_path = Path(__file__).parent / "vintage_preamp.kicad_sch"
    sch.save(str(output_path))

    print(f"✓ Generated: {output_path}")
    print(f"  Components: 12")
    print(f"  Compliance: 0% (none have PartNumber)")


if __name__ == "__main__":
    main()
