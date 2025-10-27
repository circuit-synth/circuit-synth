#!/usr/bin/env python3
"""
Simplest possible test: Load schematic, remove component, save.
No circuit-synth logic - just pure kicad-sch-api.
"""

import kicad_sch_api as ksa

# Load the schematic
print("1. Loading schematic...")
sch = ksa.Schematic.load("position_test/position_test.kicad_sch")

# Check what components exist
print(f"2. Components BEFORE removal:")
for c in sch.components:
    print(f"   - {c.reference} (UUID: {c.uuid})")

print(f"\n3. Components in _data BEFORE removal: {len(sch._data.get('components', []))}")

# Find R2
r2 = None
for c in sch.components:
    if c.reference == "R2":
        r2 = c
        break

if r2:
    print(f"\n4. Found R2, attempting removal...")
    print(f"   R2 UUID: {r2.uuid}")

    # Method 1: Try collection remove
    print(f"   Before sch.components.remove(): {len(list(sch.components))} components")
    sch.components.remove(r2)
    print(f"   After sch.components.remove(): {len(list(sch.components))} components")

    # Method 2: Also try removing from _data directly
    print(f"\n5. Removing from _data['components']...")
    before = len(sch._data['components'])
    sch._data['components'] = [c for c in sch._data['components'] if c.get('uuid') != str(r2.uuid)]
    after = len(sch._data['components'])
    print(f"   Before: {before}, After: {after}")

    # Method 3: WORKAROUND - Manually clear and rebuild ComponentCollection from _data
    print(f"\n5b. Manually syncing ComponentCollection from _data...")
    print(f"   Accessing internal _components list...")

    # Access the internal storage directly (this is a hack but necessary)
    if hasattr(sch.components, '_components'):
        print(f"   Found _components list with {len(sch.components._components)} items")
        # Remove R2 from internal list
        sch.components._components = [c for c in sch.components._components if c.uuid != r2.uuid]
        print(f"   After manual removal: {len(sch.components._components)} items")
        print(f"   Components in collection now: {len(list(sch.components))}")

    # Save - try both methods
    print(f"\n6. Saving with preserve_format=True...")
    sch.save("position_test/position_test.kicad_sch", preserve_format=True)
    print("   Save complete!")

    # Reload and verify
    print(f"\n7. Reloading to verify...")
    sch2 = ksa.Schematic.load("position_test/position_test.kicad_sch")
    print(f"   Components AFTER reload:")
    for c in sch2.components:
        print(f"   - {c.reference}")

    if any(c.reference == "R2" for c in sch2.components):
        print("\n❌ FAILED: R2 still exists after save/reload")
    else:
        print("\n✅ SUCCESS: R2 was removed!")
else:
    print("R2 not found in schematic")
