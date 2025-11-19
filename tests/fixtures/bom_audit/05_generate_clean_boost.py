"""
Generate clean_boost.kicad_sch test fixture.

Scenario: Test property name variations and mixed properties.
Some use "PartNumber", some "MPN", some "CompanyPN".
Tests handling of multiple alternative property names.
Compliance: Varies based on which property names are checked.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa


def main():
    """Generate clean_boost test fixture."""
    print("Generating clean_boost.kicad_sch...")

    # Create schematic
    sch = ksa.create_schematic("CleanBoost")

    # U1: TL071 op-amp (has MPN but NOT PartNumber)
    u1 = sch.components.add(
        lib_id="Amplifier_Operational:TL071",
        reference="U1",
        value="TL071",
        position=(100, 100),
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )
    u1.set_property("MPN", "TL071CDR")  # Using MPN instead of PartNumber
    u1.set_property("Manufacturer", "Texas Instruments")

    # R1: 1M resistor (has PartNumber ✓)
    r1 = sch.components.add(
        lib_id="Device:R",
        reference="R1",
        value="1M",
        position=(80, 100),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r1.set_property("PartNumber", "RC0805FR-071ML")
    r1.set_property("Manufacturer", "Yageo")

    # R2: 10k resistor (has CompanyPN, different field name)
    r2 = sch.components.add(
        lib_id="Device:R",
        reference="R2",
        value="10k",
        position=(80, 120),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r2.set_property("CompanyPN", "ALG-R-10K-0805")  # Company's custom field
    r2.set_property("Manufacturer", "Yageo")

    # R3: 47k resistor (has PartNumber ✓)
    r3 = sch.components.add(
        lib_id="Device:R",
        reference="R3",
        value="47k",
        position=(120, 100),
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    r3.set_property("PartNumber", "RC0805FR-0747KL")
    r3.set_property("Manufacturer", "Yageo")

    # C1: 100nF cap (MISSING all property variations)
    c1 = sch.components.add(
        lib_id="Device:C",
        reference="C1",
        value="100nF",
        position=(80, 140),
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    # Missing PartNumber, MPN, CompanyPN - completely missing

    # C2: 10uF cap (has PartNumber ✓)
    c2 = sch.components.add(
        lib_id="Device:C_Polarized",
        reference="C2",
        value="10uF",
        position=(100, 140),
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    c2.set_property("PartNumber", "GRM31CR61E106KA12L")
    c2.set_property("Manufacturer", "Murata")

    # C3: 47pF cap (has PartNumber ✓)
    c3 = sch.components.add(
        lib_id="Device:C",
        reference="C3",
        value="47pF",
        position=(120, 140),
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    c3.set_property("PartNumber", "CC0603JRNPO9BN470")
    c3.set_property("Manufacturer", "Yageo")

    # J1: Input jack (has PartNumber ✓)
    j1 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x02",
        reference="J1",
        value="IN",
        position=(60, 100)
    )
    j1.set_property("PartNumber", "MJ-3536N")
    j1.set_property("Manufacturer", "CUI Devices")

    # J2: Output jack (has PartNumber ✓)
    j2 = sch.components.add(
        lib_id="Connector_Generic:Conn_01x02",
        reference="J2",
        value="OUT",
        position=(140, 100)
    )
    j2.set_property("PartNumber", "MJ-3536N")
    j2.set_property("Manufacturer", "CUI Devices")

    # Save schematic
    output_path = Path(__file__).parent / "clean_boost.kicad_sch"
    sch.save(str(output_path))

    print(f"✓ Generated: {output_path}")
    print(f"  Components: 9")
    print(f"  With PartNumber: 5 (R1, R3, C2, C3, J1, J2)")
    print(f"  With MPN: 1 (U1)")
    print(f"  With CompanyPN: 1 (R2)")
    print(f"  Missing all: 1 (C1)")
    print(f"  Compliance (checking only 'PartNumber'): 55.6% (5 of 9)")
    print(f"  Compliance (checking any of PartNumber/MPN/CompanyPN): 88.9% (8 of 9)")


if __name__ == "__main__":
    main()
