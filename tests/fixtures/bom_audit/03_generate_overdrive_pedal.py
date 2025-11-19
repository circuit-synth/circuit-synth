"""
Generate overdrive_pedal.kicad_sch test fixture.

Scenario: Partially migrated (2022), passives updated but ICs pending.
Resistors and most caps have PartNumber, ICs and connectors don't.
Compliance: 60% (9 out of 15)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa


def main():
    """Generate overdrive_pedal test fixture."""
    print("Generating overdrive_pedal.kicad_sch...")

    # Create schematic
    sch = ksa.create_schematic("OverdrivePedal")

    # U1, U2: Op-amps (MISSING PartNumber - need update)
    u1 = sch.components.add(
        lib_id="Amplifier_Operational:TL072",
        reference="U1",
        value="TL072",
        position=(100, 100),
        footprint="Package_DIP:DIP-8_W7.62mm"
    )
    # Missing PartNumber

    u2 = sch.components.add(
        lib_id="Amplifier_Operational:TL072",  # Using TL072 as stand-in for 4558
        reference="U2",
        value="4558",
        position=(120, 100),
        footprint="Package_DIP:DIP-8_W7.62mm"
    )
    # Missing PartNumber

    # D1, D2: Clipping diodes (HAVE PartNumber ✓)
    d1 = sch.components.add(
        lib_id="Device:D",
        reference="D1",
        value="1N4148",
        position=(80, 80),
        footprint="Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
    )
    d1.set_property("PartNumber", "1N4148-TAP")
    d1.set_property("Manufacturer", "Diodes Inc")

    d2 = sch.components.add(
        lib_id="Device:D",
        reference="D2",
        value="1N4148",
        position=(120, 80),
        footprint="Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
    )
    d2.set_property("PartNumber", "1N4148-TAP")
    d2.set_property("Manufacturer", "Diodes Inc")

    # R1-R4: Resistors (HAVE PartNumber ✓)
    r1 = sch.components.add(
        lib_id="Device:R",
        reference="R1",
        value="10k",
        position=(80, 100),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r1.set_property("PartNumber", "RC0805FR-0710KL")
    r1.set_property("Manufacturer", "Yageo")
    r1.set_property("Tolerance", "1%")

    r2 = sch.components.add(
        lib_id="Device:R",
        reference="R2",
        value="100k",
        position=(80, 120),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r2.set_property("PartNumber", "RC0805FR-07100KL")
    r2.set_property("Manufacturer", "Yageo")
    r2.set_property("Tolerance", "1%")

    r3 = sch.components.add(
        lib_id="Device:R",
        reference="R3",
        value="47k",
        position=(80, 140),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r3.set_property("PartNumber", "RC0805FR-0747KL")
    r3.set_property("Manufacturer", "Yageo")
    r3.set_property("Tolerance", "1%")

    r4 = sch.components.add(
        lib_id="Device:R",
        reference="R4",
        value="4.7k",
        position=(120, 120),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r4.set_property("PartNumber", "RC0805FR-074K7L")
    r4.set_property("Manufacturer", "Yageo")
    r4.set_property("Tolerance", "1%")

    # C1, C2, C4: Capacitors (HAVE PartNumber ✓)
    c1 = sch.components.add(
        lib_id="Device:C",
        reference="C1",
        value="100nF",
        position=(100, 120),
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c1.set_property("PartNumber", "CC0805KRX7R9BB104")
    c1.set_property("Manufacturer", "Yageo")
    c1.set_property("Tolerance", "10%")

    c2 = sch.components.add(
        lib_id="Device:C",
        reference="C2",
        value="47nF",
        position=(120, 140),
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c2.set_property("PartNumber", "CC0805KRX7R9BB473")
    c2.set_property("Manufacturer", "Yageo")
    c2.set_property("Tolerance", "10%")

    c4 = sch.components.add(
        lib_id="Device:C",
        reference="C4",
        value="100nF",
        position=(140, 120),
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    c4.set_property("PartNumber", "CC0603KRX7R9BB104")
    c4.set_property("Manufacturer", "Yageo")
    c4.set_property("Tolerance", "10%")

    # C3: Power cap (MISSING PartNumber - needs update)
    c3 = sch.components.add(
        lib_id="Device:C_Polarized",
        reference="C3",
        value="10uF",
        position=(100, 140),
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    c3.set_property("Tolerance", "20%")
    # Missing PartNumber

    # J1, J2: Audio jacks (MISSING PartNumber - needs update)
    j1 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x02",
        reference="J1",
        value="IN",
        position=(60, 100)
    )
    # Missing PartNumber

    j2 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x02",
        reference="J2",
        value="OUT",
        position=(160, 100)
    )
    # Missing PartNumber

    # SW1: Bypass switch (MISSING PartNumber - needs update)
    sw1 = sch.components.add(
        lib_id="Switch:SW_DPDT_x2",
        reference="SW1",
        value="DPDT",
        position=(110, 160)
    )
    # Missing PartNumber

    # Save schematic
    output_path = Path(__file__).parent / "overdrive_pedal.kicad_sch"
    sch.save(str(output_path))

    print(f"✓ Generated: {output_path}")
    print(f"  Components: 15")
    print(f"  With PartNumber: 9 (resistors, diodes, most caps)")
    print(f"  Missing PartNumber: 6 (ICs, connectors, switch, one cap)")
    print(f"  Compliance: 60%")


if __name__ == "__main__":
    main()
