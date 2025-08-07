#!/usr/bin/env python3
"""
Test script demonstrating how to use the Rust KiCad integration
to create a schematic with various components and hierarchical labels.

This creates a simple voltage divider circuit with labels.
"""

import subprocess

import rust_kicad_schematic_writer as kicad


def main():
    print("=" * 60)
    print("KiCad Schematic Generation Test")
    print("Creating a voltage divider with hierarchical labels")
    print("=" * 60)

    # Create minimal schematic
    print("\n1. Creating base schematic...")
    schematic = kicad.create_minimal_schematic()
    print("   ✓ Base schematic created")

    # Add components for a voltage divider circuit
    components = [
        # Power input connector
        {
            "reference": "J1",
            "lib_id": "Connector:Conn_01x02_Pin",
            "value": "PWR_IN",
            "x": 50.0,
            "y": 50.0,
            "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        },
        # First resistor (R1)
        {
            "reference": "R1",
            "lib_id": "Device:R",
            "value": "10k",
            "x": 100.0,
            "y": 50.0,
            "footprint": "Resistor_SMD:R_0603_1608Metric",
        },
        # Second resistor (R2)
        {
            "reference": "R2",
            "lib_id": "Device:R",
            "value": "10k",
            "x": 100.0,
            "y": 80.0,
            "footprint": "Resistor_SMD:R_0603_1608Metric",
        },
        # Capacitor for filtering
        {
            "reference": "C1",
            "lib_id": "Device:C",
            "value": "100nF",
            "x": 130.0,
            "y": 80.0,
            "footprint": "Capacitor_SMD:C_0603_1608Metric",
        },
        # Output connector
        {
            "reference": "J2",
            "lib_id": "Connector:Conn_01x02_Socket",
            "value": "VOUT",
            "x": 160.0,
            "y": 65.0,
            "footprint": "Connector_PinSocket_2.54mm:PinSocket_1x02_P2.54mm_Vertical",
        },
    ]

    print("\n2. Adding components...")
    for comp in components:
        try:
            schematic = kicad.add_component_to_schematic(
                schematic,
                reference=comp["reference"],
                lib_id=comp["lib_id"],
                value=comp["value"],
                x=comp["x"],
                y=comp["y"],
                rotation=0.0,
                footprint=comp.get("footprint", ""),
            )
            print(
                f"   ✓ Added {comp['reference']}: {comp['value']} at ({comp['x']}, {comp['y']})"
            )
        except Exception as e:
            print(f"   ✗ Failed to add {comp['reference']}: {e}")

    # Add hierarchical labels for signals
    labels = [
        {"name": "VIN", "shape": "input", "x": 70.0, "y": 40.0, "rotation": 90.0},
        {"name": "GND", "shape": "passive", "x": 70.0, "y": 95.0, "rotation": 270.0},
        {"name": "VDIV", "shape": "output", "x": 115.0, "y": 65.0, "rotation": 0.0},
        {
            "name": "VOUT_FILTERED",
            "shape": "output",
            "x": 145.0,
            "y": 65.0,
            "rotation": 0.0,
        },
    ]

    print("\n3. Adding hierarchical labels...")
    for label in labels:
        try:
            schematic = kicad.add_hierarchical_label_to_schematic(
                schematic,
                name=label["name"],
                shape=label["shape"],
                x=label["x"],
                y=label["y"],
                rotation=label["rotation"],
            )
            print(
                f"   ✓ Added label '{label['name']}' ({label['shape']}) at ({label['x']}, {label['y']})"
            )
        except Exception as e:
            print(f"   ✗ Failed to add label '{label['name']}': {e}")

    # Save the schematic
    output_file = "voltage_divider_circuit.kicad_sch"
    print(f"\n4. Saving schematic to {output_file}...")
    with open(output_file, "w") as f:
        f.write(schematic)
    print(f"   ✓ Schematic saved")

    # Validate with KiCad
    print("\n5. Validating with KiCad...")
    try:
        result = subprocess.run(
            [
                "kicad-cli",
                "sch",
                "export",
                "pdf",
                output_file,
                "--output",
                "voltage_divider_circuit.pdf",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("   ✓ KiCad validation PASSED!")
            print("   ✓ PDF exported to voltage_divider_circuit.pdf")
            print("\n✅ SUCCESS! Schematic generated and validated.")
            print("\nYou can now:")
            print("  1. Open voltage_divider_circuit.kicad_sch in KiCad")
            print("  2. View voltage_divider_circuit.pdf to see the circuit")
        else:
            print(f"   ✗ KiCad validation failed: {result.stderr}")
    except FileNotFoundError:
        print("   ⚠️  kicad-cli not found - install KiCad to validate")
        print("\n✅ Schematic generated successfully (validation skipped)")
        print("\nYou can open voltage_divider_circuit.kicad_sch in KiCad")
    except subprocess.TimeoutExpired:
        print("   ⚠️  KiCad validation timed out")
    except Exception as e:
        print(f"   ⚠️  Validation error: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("Circuit Summary:")
    print(
        f"  • Components: {len(components)} ({', '.join([c['reference'] for c in components])})"
    )
    print(f"  • Labels: {len(labels)} ({', '.join([l['name'] for l in labels])})")
    print(f"  • Output: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
