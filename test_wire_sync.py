#!/usr/bin/env python3
"""
Test to verify if wire sync issue exists.

This script tests whether wires added via the WireCollection properly
sync to _data["wire"] without needing manual sync.
"""

import kicad_sch_api as ksa
import tempfile
import os

def test_wire_sync():
    # Create a blank schematic
    print("Creating blank schematic...")
    sch = ksa.create_schematic("test_wire_sync")

    # Add a wire using the public API
    print("\nAdding wire using schematic.add_wire()...")
    wire_uuid = sch.add_wire(start=(100, 100), end=(200, 100))
    print(f"  Wire UUID: {wire_uuid}")

    # Check if wire is in collection
    wires_in_collection = list(sch.wires)
    print(f"\n  Wires in collection: {len(wires_in_collection)}")
    for w in wires_in_collection:
        print(f"    - {w.uuid}: {w.points}")

    # Check if wire is in _data
    wires_in_data = sch._data.get("wire", [])
    print(f"\n  Wires in _data: {len(wires_in_data)}")
    for w in wires_in_data:
        print(f"    - {w.get('uuid')}: {w.get('points', [])}")

    # Save and reload
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "test.kicad_sch")
        print(f"\nSaving to: {test_path}")
        sch.save(test_path)

        print("\nReloading schematic...")
        sch2 = ksa.load_schematic(test_path)

        # Check if wire survived the round-trip
        wires_after_reload = list(sch2.wires)
        print(f"\n  Wires after reload: {len(wires_after_reload)}")
        for w in wires_after_reload:
            print(f"    - {w.uuid}: {w.points}")

    # Now test removal
    print("\n\nTesting wire removal...")
    sch3 = ksa.create_schematic("test_wire_removal")

    # Add two wires
    wire1_uuid = sch3.add_wire(start=(100, 100), end=(200, 100))
    wire2_uuid = sch3.add_wire(start=(100, 200), end=(200, 200))

    print(f"  Added wires: {wire1_uuid}, {wire2_uuid}")
    print(f"  Wires in collection: {len(list(sch3.wires))}")
    print(f"  Wires in _data: {len(sch3._data.get('wire', []))}")

    # Remove one wire
    print(f"\nRemoving wire: {wire1_uuid}")
    removed = sch3.remove_wire(wire1_uuid)
    print(f"  Removal successful: {removed}")

    print(f"\n  Wires in collection after removal: {len(list(sch3.wires))}")
    print(f"  Wires in _data after removal: {len(sch3._data.get('wire', []))}")

    # Check UUIDs
    print("\n  Collection UUIDs:")
    for w in sch3.wires:
        print(f"    - {w.uuid}")

    print("\n  _data UUIDs:")
    for w in sch3._data.get('wire', []):
        print(f"    - {w.get('uuid')}")

    # Test save/reload after removal
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "test_removal.kicad_sch")
        print(f"\nSaving to: {test_path}")
        sch3.save(test_path)

        print("\nReloading schematic...")
        sch4 = ksa.load_schematic(test_path)

        print(f"\n  Wires after reload: {len(list(sch4.wires))}")
        for w in sch4.wires:
            print(f"    - {w.uuid}")

if __name__ == "__main__":
    test_wire_sync()
