"""
Generate di_box.kicad_sch test fixture.

Scenario: Test DNP components and component filtering.
Has DNP test resistor, connectors without PartNumber, mechanical parts.
Compliance: 70% (without DNP), 66.7% (with DNP)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa


def main():
    """Generate di_box test fixture."""
    print("Generating di_box.kicad_sch...")

    # Create schematic
    sch = ksa.create_schematic("DIBox")

    # U1: DRV134 balanced line driver (HAVE PartNumber ✓)
    u1 = sch.components.add(
        lib_id="Amplifier_Operational:TL072",  # Using TL072 as stand-in for DRV134
        reference="U1",
        value="DRV134",
        position=(100, 100),
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )
    u1.set_property("PartNumber", "DRV134UA")
    u1.set_property("Manufacturer", "Texas Instruments")

    # R1, R2: Input resistors (HAVE PartNumber ✓)
    r1 = sch.components.add(
        lib_id="Device:R",
        reference="R1",
        value="10k",
        position=(80, 100),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r1.set_property("PartNumber", "RC0805FR-0710KL")
    r1.set_property("Manufacturer", "Yageo")

    r2 = sch.components.add(
        lib_id="Device:R",
        reference="R2",
        value="10k",
        position=(80, 120),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r2.set_property("PartNumber", "RC0805FR-0710KL")
    r2.set_property("Manufacturer", "Yageo")

    # R3: Test point resistor (DNP - Do Not Populate)
    r3 = sch.components.add(
        lib_id="Device:R",
        reference="R3",
        value="100",
        position=(120, 100),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    # Missing PartNumber AND marked DNP
    r3.in_bom = False  # Mark as DNP (Do Not Populate)

    # C1, C2: Capacitors (HAVE PartNumber ✓)
    c1 = sch.components.add(
        lib_id="Device:C",
        reference="C1",
        value="100nF",
        position=(80, 140),
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c1.set_property("PartNumber", "CC0805KRX7R9BB104")
    c1.set_property("Manufacturer", "Yageo")

    c2 = sch.components.add(
        lib_id="Device:C_Polarized",
        reference="C2",
        value="47uF",
        position=(120, 140),
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    c2.set_property("PartNumber", "GRM31CR61A476KE19L")
    c2.set_property("Manufacturer", "Murata")

    # J1, J2: XLR connectors (MISSING PartNumber - needs update)
    j1 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x03",
        reference="J1",
        value="XLR_IN",
        position=(60, 100)
    )
    # Missing PartNumber

    j2 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x03",
        reference="J2",
        value="XLR_OUT",
        position=(140, 100)
    )
    # Missing PartNumber

    # J3: 1/4" instrument input (HAVE PartNumber ✓)
    j3 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x02",
        reference="J3",
        value="1/4\"",
        position=(60, 120)
    )
    j3.set_property("PartNumber", "MJ-3536N")
    j3.set_property("Manufacturer", "CUI Devices")

    # H1: Mounting hole (MISSING PartNumber - mechanical part)
    h1 = sch.components.add(
        lib_id="Mechanical:MountingHole",
        reference="H1",
        value="MountingHole",
        position=(100, 180)
    )
    # Missing PartNumber

    # Save schematic
    output_path = Path(__file__).parent / "di_box.kicad_sch"
    sch.save(str(output_path))

    print(f"✓ Generated: {output_path}")
    print(f"  Components: 10 total")
    print(f"  DNP components: 1 (R3)")
    print(f"  With PartNumber: 6")
    print(f"  Missing PartNumber: 4 (including DNP R3)")
    print(f"  Compliance (excluding DNP): 66.7% (6 of 9)")
    print(f"  Compliance (including DNP): 60% (6 of 10)")


if __name__ == "__main__":
    main()
