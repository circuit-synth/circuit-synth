"""
Generate amp_power_supply.kicad_sch test fixture.

Scenario: Modern design (2024), fully compliant with company standards.
All components have PartNumber and Manufacturer properties.
Compliance: 100%
"""

import sys
from pathlib import Path

# Add kicad-sch-api to path (submodule)
sys.path.insert(0, str(Path(__file__).parents[3] / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa


def main():
    """Generate amp_power_supply test fixture."""
    print("Generating amp_power_supply.kicad_sch...")

    # Create schematic
    sch = ksa.create_schematic("AmpPowerSupply")

    # U1: AMS1117-3.3 voltage regulator
    u1 = sch.components.add(
        lib_id="Regulator_Linear:AMS1117-3.3",
        reference="U1",
        value="AMS1117-3.3",
        position=(100, 100),
        footprint="Package_TO_SOT_SMD:SOT-223"
    )
    u1.set_property("PartNumber", "AMS1117-3.3")
    u1.set_property("Manufacturer", "Advanced Monolithic")

    # U2: LM7815 +15V regulator
    u2 = sch.components.add(
        lib_id="Regulator_Linear:LM7815_TO220",
        reference="U2",
        value="LM7815",
        position=(100, 120),
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )
    u2.set_property("PartNumber", "LM7815CT")
    u2.set_property("Manufacturer", "Texas Instruments")

    # U3: LM7915 -15V regulator
    u3 = sch.components.add(
        lib_id="Regulator_Linear:LM7915_TO220",
        reference="U3",
        value="LM7915",
        position=(100, 140),
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )
    u3.set_property("PartNumber", "LM7915CT")
    u3.set_property("Manufacturer", "Texas Instruments")

    # C1: 100uF input filter capacitor
    c1 = sch.components.add(
        lib_id="Device:C_Polarized",
        reference="C1",
        value="100uF",
        position=(80, 100),
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    c1.set_property("PartNumber", "GRM31CR61E107KA12L")
    c1.set_property("Manufacturer", "Murata")
    c1.set_property("Tolerance", "10%")

    # C2: 100uF output filter capacitor
    c2 = sch.components.add(
        lib_id="Device:C_Polarized",
        reference="C2",
        value="100uF",
        position=(120, 100),
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    c2.set_property("PartNumber", "GRM31CR61E107KA12L")
    c2.set_property("Manufacturer", "Murata")
    c2.set_property("Tolerance", "10%")

    # C3: 10uF bypass capacitor
    c3 = sch.components.add(
        lib_id="Device:C",
        reference="C3",
        value="10uF",
        position=(80, 120),
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c3.set_property("PartNumber", "GRM21BR61E106KA73L")
    c3.set_property("Manufacturer", "Murata")
    c3.set_property("Tolerance", "10%")

    # C4: 100nF decoupling capacitor
    c4 = sch.components.add(
        lib_id="Device:C",
        reference="C4",
        value="100nF",
        position=(120, 120),
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    c4.set_property("PartNumber", "GRM188R71H104KA93D")
    c4.set_property("Manufacturer", "Murata")
    c4.set_property("Tolerance", "10%")

    # D1: 1N4001 reverse protection diode
    d1 = sch.components.add(
        lib_id="Device:D",
        reference="D1",
        value="1N4001",
        position=(80, 140),
        footprint="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
    )
    d1.set_property("PartNumber", "1N4001-T")
    d1.set_property("Manufacturer", "Diodes Inc")

    # Save schematic
    output_path = Path(__file__).parent / "amp_power_supply.kicad_sch"
    sch.save(str(output_path))

    print(f"✓ Generated: {output_path}")
    print(f"  Components: 8")
    print(f"  Compliance: 100% (all have PartNumber)")


if __name__ == "__main__":
    main()
