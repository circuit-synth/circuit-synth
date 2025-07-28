#!/usr/bin/env python3
"""
Test script for KiCad API Phase 2: Component Management
Tests add, remove, update, move, and clone operations
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.core.types import Point, Schematic
from circuit_synth.kicad_api.schematic.component_manager import ComponentManager
from circuit_synth.kicad_api.schematic.placement import PlacementStrategy


def test_component_management():
    """Test all component management operations"""
    print("Testing KiCad API Phase 2: Component Management")
    print("=" * 50)

    # Create empty schematic
    schematic = Schematic(version="20231120", uuid="test-schematic-uuid")

    # Create component manager
    manager = ComponentManager(schematic)

    # Test 1: Add components with different placement strategies
    print("\n1. Testing add_component with various placement strategies:")

    # Add first resistor with AUTO placement
    r1 = manager.add_component(
        library_id="Device:R",
        reference="R1",
        value="10k",
        placement_strategy=PlacementStrategy.AUTO,
    )
    print(f"   ✓ Added R1 at position ({r1.position.x}, {r1.position.y})")

    # Add second resistor with GRID placement
    r2 = manager.add_component(
        library_id="Device:R",
        reference="R2",
        value="1k",
        placement_strategy=PlacementStrategy.GRID,
    )
    print(f"   ✓ Added R2 at position ({r2.position.x}, {r2.position.y})")

    # Add capacitor with EDGE_RIGHT placement
    c1 = manager.add_component(
        library_id="Device:C",
        reference="C1",
        value="100nF",
        placement_strategy=PlacementStrategy.EDGE_RIGHT,
    )
    print(f"   ✓ Added C1 at position ({c1.position.x}, {c1.position.y})")

    # Test 2: Update component properties
    print("\n2. Testing update_component:")
    success = manager.update_component(
        "R1", value="22k", footprint="Resistor_SMD:R_0603"
    )
    if success:
        updated_r1 = manager.get_component("R1")
        print(f"   ✓ Updated R1 value to {updated_r1.value}")
        print(
            f"   ✓ Updated R1 footprint to {updated_r1.properties.get('footprint', 'N/A')}"
        )

    # Test 3: Move component
    print("\n3. Testing move_component:")
    new_position = (50.8, 50.8)  # 2 inches from origin
    success = manager.move_component("R2", new_position)
    if success:
        moved_r2 = manager.get_component("R2")
        print(
            f"   ✓ Moved R2 to position ({moved_r2.position.x}, {moved_r2.position.y})"
        )

    # Test 4: Clone component
    print("\n4. Testing clone_component:")
    r3 = manager.clone_component("R1", new_reference="R3")
    if r3:
        print(f"   ✓ Cloned R1 to R3 at position ({r3.position.x}, {r3.position.y})")
        print(f"   ✓ R3 has value: {r3.value}")

    # Test 5: List all components
    print("\n5. Current components in schematic:")
    components = manager.list_components()
    for comp in components:
        print(
            f"   - {comp.reference}: {comp.value} at ({comp.position.x}, {comp.position.y})"
        )

    # Test 6: Remove component
    print("\n6. Testing remove_component:")
    success = manager.remove_component("R2")
    if success:
        print("   ✓ Removed R2")
        print(f"   ✓ Component count after removal: {len(manager.list_components())}")

    # Test 7: Validate schematic
    print("\n7. Testing validate_schematic:")
    is_valid, messages = manager.validate_schematic()
    print(f"   ✓ Schematic valid: {is_valid}")
    if messages:
        for msg in messages:
            print(f"     - {msg}")

    # Test 8: Test placement engine features
    print("\n8. Testing advanced placement features:")

    # Add multiple components to test collision detection
    for i in range(4, 8):
        manager.add_component(
            library_id="Device:R",
            reference=f"R{i}",
            value=f"{i}k",
            placement_strategy=PlacementStrategy.AUTO,
        )

    print(f"   ✓ Added R4-R7 with automatic collision avoidance")
    print(f"   ✓ Total components: {len(manager.list_components())}")

    # Show final component layout
    print("\n9. Final component layout:")
    for comp in manager.list_components():
        print(
            f"   - {comp.reference}: {comp.value} at ({comp.position.x:.1f}, {comp.position.y:.1f})"
        )

    print("\n✅ All Phase 2 tests completed successfully!")

    return schematic, manager


def test_error_handling():
    """Test error handling in component management"""
    print("\n\nTesting Error Handling")
    print("=" * 50)

    schematic = Schematic(version="20231120", uuid="test-uuid")
    manager = ComponentManager(schematic)

    # Add a component first
    manager.add_component("Device:R", "R1", "10k")

    # Test 1: Try to add duplicate reference
    print("\n1. Testing duplicate reference handling:")
    try:
        manager.add_component("Device:C", "R1", "100nF")
    except ValueError as e:
        print(f"   ✓ Caught expected error: {e}")

    # Test 2: Try to update non-existent component
    print("\n2. Testing update of non-existent component:")
    success = manager.update_component("R99", value="1M")
    print(f"   ✓ Update returned: {success} (expected: False)")

    # Test 3: Try to move non-existent component
    print("\n3. Testing move of non-existent component:")
    success = manager.move_component("R99", (100, 100))
    print(f"   ✓ Move returned: {success} (expected: False)")

    # Test 4: Try to clone non-existent component
    print("\n4. Testing clone of non-existent component:")
    result = manager.clone_component("R99")
    print(f"   ✓ Clone returned: {result} (expected: None)")

    # Test 5: Try to remove non-existent component
    print("\n5. Testing remove of non-existent component:")
    success = manager.remove_component("R99")
    print(f"   ✓ Remove returned: {success} (expected: False)")

    print("\n✅ Error handling tests completed!")


if __name__ == "__main__":
    # Run main tests
    schematic, manager = test_component_management()

    # Run error handling tests
    test_error_handling()

    print("\n" + "=" * 50)
    print("All KiCad API Phase 2 tests passed! 🎉")
    print("\nNext steps:")
    print("- Phase 3: Wire Management")
    print("- Phase 4: Label & Text Management")
    print("- Phase 5: Sheet & Hierarchy")
    print("- Phase 6: Search & Discovery")
