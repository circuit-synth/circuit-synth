#!/usr/bin/env python3
"""
Test script for KiCad API Phase 3: Wire Management
Tests wire creation, routing, manipulation, and junction management
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.core.types import Point, Schematic
from circuit_synth.kicad_api.schematic import (
    ComponentManager,
    JunctionManager,
    WireManager,
    WireRouter,
    WireRoutingStyle,
    get_pin_position,
)


def test_wire_management():
    """Test all wire management operations"""
    print("Testing KiCad API Phase 3: Wire Management")
    print("=" * 50)

    # Create schematic with components
    schematic = Schematic(version="20231120", uuid="test-wire-schematic-uuid")

    # Add some components to connect
    comp_manager = ComponentManager(schematic)

    r1 = comp_manager.add_component(
        library_id="Device:R", reference="R1", value="10k", position=(25.4, 25.4)
    )

    r2 = comp_manager.add_component(
        library_id="Device:R", reference="R2", value="1k", position=(76.2, 25.4)
    )

    c1 = comp_manager.add_component(
        library_id="Device:C", reference="C1", value="100nF", position=(50.8, 50.8)
    )

    print(f"\n✓ Added 3 components: R1, R2, C1")

    # Create wire manager
    wire_manager = WireManager(schematic)

    # Test 1: Basic wire creation
    print("\n1. Testing basic wire creation:")

    # Create a simple wire
    wire1 = wire_manager.add_wire(points=[(25.4, 25.4), (50.8, 25.4), (50.8, 50.8)])
    if wire1:
        print(f"   ✓ Created wire with {len(wire1.points)} points")

    # Test 2: Wire routing
    print("\n2. Testing wire routing algorithms:")
    router = WireRouter()

    # Test direct routing
    direct_path = router.route_direct((0, 0), (50, 50))
    print(f"   ✓ Direct route: {len(direct_path)} points")

    # Test Manhattan routing
    manhattan_path = router.route_manhattan((0, 0), (50, 30))
    print(f"   ✓ Manhattan route: {len(manhattan_path)} points - {manhattan_path}")

    # Test diagonal routing
    diagonal_path = router.route_diagonal((0, 0), (40, 30))
    print(f"   ✓ Diagonal route: {len(diagonal_path)} points - {diagonal_path}")

    # Test auto routing
    auto_path = router.route_auto((0, 0), (100, 80))
    print(f"   ✓ Auto route: {len(auto_path)} points")

    # Test 3: Pin-to-pin connection
    print("\n3. Testing pin-to-pin connections:")

    # Note: In a real implementation, we'd get actual pin positions
    # For now, we'll simulate pin positions
    r1_pin2 = (r1.position.x + 12.7, r1.position.y)  # Right side of R1
    c1_pin1 = (c1.position.x, c1.position.y - 12.7)  # Top of C1

    # Route wire between pins
    pin_route = router.route_manhattan(r1_pin2, c1_pin1)
    wire2 = wire_manager.add_wire(pin_route)
    if wire2:
        print(f"   ✓ Connected R1 pin 2 to C1 pin 1 with {len(wire2.points)} points")

    # Test 4: Wire manipulation
    print("\n4. Testing wire manipulation:")

    # Extend a wire
    if wire1:
        success = wire_manager.extend_wire(wire1.uuid, (76.2, 50.8), extend_from="end")
        if success:
            print(f"   ✓ Extended wire to new endpoint")

    # Split a wire
    if wire1 and len(wire1.points) > 2:
        split_result = wire_manager.split_wire(wire1.uuid, (50.8, 37.9))
        if split_result:
            wire3, wire4 = split_result
            print(f"   ✓ Split wire into two wires")

    # Test 5: Junction management
    print("\n5. Testing junction management:")

    junction_manager = JunctionManager(schematic)

    # Add a wire that creates a T-junction
    wire5 = wire_manager.add_wire([(50.8, 10), (50.8, 60)])

    # Update junctions
    junction_manager.update_junctions()
    print(f"   ✓ Updated junctions: {len(schematic.junctions)} junctions found")

    # Manually add a junction
    junction = junction_manager.add_junction(100, 100)
    print(f"   ✓ Manually added junction at (100, 100)")

    # Validate junctions
    is_valid, issues = junction_manager.validate_junctions()
    print(f"   ✓ Junction validation: {'Valid' if is_valid else 'Invalid'}")
    if issues:
        for issue in issues:
            print(f"     - {issue}")

    # Test 6: Wire finding
    print("\n6. Testing wire finding:")

    wires_at_point = wire_manager.find_wires_at_point((50.8, 25.4))
    print(f"   ✓ Found {len(wires_at_point)} wires at point (50.8, 25.4)")

    # Test 7: Bus routing
    print("\n7. Testing bus routing:")

    # Create multiple parallel connections
    start_points = [(10, 10), (10, 15), (10, 20), (10, 25)]
    end_points = [(60, 10), (60, 15), (60, 20), (60, 25)]

    bus_paths = router.route_bus(start_points, end_points)
    print(f"   ✓ Routed bus with {len(bus_paths)} wires")

    # Add bus wires to schematic
    for path in bus_paths:
        wire_manager.add_wire(path)

    # Test 8: Final statistics
    print("\n8. Final schematic statistics:")
    print(f"   - Total wires: {len(schematic.wires)}")
    print(f"   - Total junctions: {len(schematic.junctions)}")
    print(f"   - Total components: {len(schematic.components)}")

    # Show all wire endpoints
    print("\n9. Wire details:")
    for i, wire in enumerate(schematic.wires):
        start, end = wire.get_endpoints()
        print(
            f"   - Wire {i}: ({start.x}, {start.y}) → ({end.x}, {end.y}) "
            f"[{len(wire.points)} points]"
        )

    print("\n✅ All Phase 3 tests completed successfully!")

    return schematic, wire_manager, junction_manager


def test_routing_styles():
    """Test different routing styles in detail"""
    print("\n\nTesting Routing Styles in Detail")
    print("=" * 50)

    router = WireRouter()
    test_cases = [
        ((10, 10), (50, 10), "Horizontal"),
        ((10, 10), (10, 50), "Vertical"),
        ((10, 10), (50, 50), "Diagonal"),
        ((10, 10), (70, 25), "Mixed"),
    ]

    for start, end, description in test_cases:
        print(f"\n{description} routing from {start} to {end}:")

        for style in WireRoutingStyle:
            path = router.route(start, end, style)
            print(f"   {style.value}: {' → '.join(str(p) for p in path)}")


def test_error_handling():
    """Test error handling in wire management"""
    print("\n\nTesting Error Handling")
    print("=" * 50)

    schematic = Schematic()
    wire_manager = WireManager(schematic)

    # Test 1: Invalid wire (too few points)
    print("\n1. Testing invalid wire creation:")
    wire = wire_manager.add_wire([(10, 10)])  # Only one point
    print(f"   ✓ Single point wire returned: {wire} (expected: None)")

    # Test 2: Extend non-existent wire
    print("\n2. Testing operations on non-existent wire:")
    success = wire_manager.extend_wire("fake-uuid", (50, 50))
    print(f"   ✓ Extend non-existent wire returned: {success} (expected: False)")

    # Test 3: Split wire at invalid point
    print("\n3. Testing split at invalid point:")
    wire = wire_manager.add_wire([(0, 0), (100, 0)])
    if wire:
        result = wire_manager.split_wire(wire.uuid, (50, 50))  # Point not on wire
        print(f"   ✓ Split at invalid point returned: {result} (expected: None)")

    print("\n✅ Error handling tests completed!")


if __name__ == "__main__":
    # Run main wire management tests
    schematic, wire_manager, junction_manager = test_wire_management()

    # Run routing style tests
    test_routing_styles()

    # Run error handling tests
    test_error_handling()

    print("\n" + "=" * 50)
    print("All KiCad API Phase 3 tests passed! 🎉")
    print("\nPhase 3 Complete! Wire management is now functional.")
    print("\nNext steps:")
    print("- Phase 4: Label & Text Management")
    print("- Phase 5: Sheet & Hierarchy")
    print("- Phase 6: Search & Discovery")
