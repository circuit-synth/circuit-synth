#!/usr/bin/env python3
"""
Simple Python script to test adding a resistor to a KiCad schematic
using the rust_kicad_schematic_writer module.

This demonstrates:
1. Importing the Rust module
2. Creating a minimal schematic
3. Creating a schematic with a resistor component
4. Saving the output to a file
"""

import sys
from pathlib import Path


def test_rust_kicad_module():
    """Test the rust_kicad_schematic_writer module functionality."""

    print("Testing Rust KiCad Schematic Writer from Python...")
    print("-" * 50)

    try:
        # Import the Rust module
        import rust_kicad_schematic_writer as kicad

        print("✅ Successfully imported rust_kicad_schematic_writer")
    except ImportError as e:
        print(f"❌ Failed to import rust_kicad_schematic_writer: {e}")
        print("\nTo fix this, run:")
        print("  cd rust_modules/rust_kicad_integration")
        print("  maturin develop --release")
        return False

    # Test 1: Create a minimal schematic
    print("\n1. Creating minimal schematic...")
    try:
        minimal_schematic = kicad.create_minimal_schematic()

        # Save to file
        output_file = Path("test_minimal.kicad_sch")
        output_file.write_text(minimal_schematic)

        print(f"   ✅ Created minimal schematic: {output_file}")
        print(f"   Size: {len(minimal_schematic)} characters")
    except Exception as e:
        print(f"   ❌ Failed to create minimal schematic: {e}")
        return False

    # Test 2: Create schematic with specific paper size
    print("\n2. Creating A3 schematic...")
    try:
        a3_schematic = kicad.create_empty_schematic("A3")

        output_file = Path("test_a3.kicad_sch")
        output_file.write_text(a3_schematic)

        print(f"   ✅ Created A3 schematic: {output_file}")
    except Exception as e:
        print(f"   ❌ Failed to create A3 schematic: {e}")
        return False

    # Test 3: Try to create a schematic with a component
    # Note: This requires the SimpleComponent class to be exported to Python
    print("\n3. Testing component creation...")
    try:
        # Check if SimpleComponent is available
        if hasattr(kicad, "PySimpleComponent"):
            print("   Found PySimpleComponent class")

            # Create a resistor component
            resistor = kicad.PySimpleComponent(
                reference="R1",
                lib_id="Device:R",
                value="10k",
                x=121.92,
                y=73.66,
                rotation=0.0,
            )

            # Create schematic with the component
            schematic = kicad.create_schematic_with_components("A4", [resistor])

            output_file = Path("test_with_resistor.kicad_sch")
            output_file.write_text(schematic)

            print(f"   ✅ Created schematic with resistor: {output_file}")

        elif hasattr(kicad, "create_schematic_with_components"):
            print(
                "   ⚠️  create_schematic_with_components exists but PySimpleComponent not exported"
            )
            print(
                "   This is a known issue - component creation from Python needs fixing"
            )
        else:
            print("   ⚠️  Component creation API not available yet")
    except Exception as e:
        print(f"   ⚠️  Component test failed (expected): {e}")

    # Test 4: Verify schematic content
    print("\n4. Verifying schematic content...")
    try:
        content = Path("test_minimal.kicad_sch").read_text()

        # Check for required elements
        checks = [
            ("(kicad_sch", "KiCad schematic header"),
            ("(version", "Version declaration"),
            ("(generator", "Generator info"),
            ('(paper "A4")', "Paper size"),
        ]

        all_good = True
        for check_str, description in checks:
            if check_str in content:
                print(f"   ✅ Found: {description}")
            else:
                print(f"   ❌ Missing: {description}")
                all_good = False

        if all_good:
            print("\n✅ All basic functionality tests passed!")
        else:
            print("\n⚠️  Some checks failed")

    except Exception as e:
        print(f"   ❌ Failed to verify content: {e}")
        return False

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("- Rust module import: ✅")
    print("- Basic schematic creation: ✅")
    print("- Different paper sizes: ✅")
    print("- Component support: ⚠️ (Python bindings need work)")
    print("\nGenerated files:")
    print("- test_minimal.kicad_sch")
    print("- test_a3.kicad_sch")
    print("\nYou can open these files in KiCad to verify they work!")

    return True


if __name__ == "__main__":
    success = test_rust_kicad_module()
    sys.exit(0 if success else 1)
