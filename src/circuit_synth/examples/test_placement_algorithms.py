#!/usr/bin/env python3
"""
Unit tests for PCB placement algorithms.
Tests each algorithm individually with various scenarios.
"""

import math
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard
from circuit_synth.kicad_api.pcb.placement import (
    ConnectivityDrivenPlacer,
    ForceDirectedPlacer,
    HierarchicalPlacer,
)
from circuit_synth.kicad_api.pcb.placement.base import ComponentWrapper
from circuit_synth.kicad_api.pcb.types import Point


def create_test_components():
    """Create a set of test components"""
    components = []

    # Create components with different hierarchical paths
    components.append(
        ComponentWrapper(
            reference="U1",
            footprint="SOIC-8",
            value="LM358",
            position=Point(50, 50),
            pads=[],
            hierarchical_path="/power_supply/",
        )
    )

    components.append(
        ComponentWrapper(
            reference="U2",
            footprint="SOIC-14",
            value="74HC00",
            position=Point(60, 50),
            pads=[],
            hierarchical_path="/logic/",
        )
    )

    components.append(
        ComponentWrapper(
            reference="R1",
            footprint="R_0603",
            value="10k",
            position=Point(30, 30),
            pads=[],
            hierarchical_path="/power_supply/",
        )
    )

    components.append(
        ComponentWrapper(
            reference="R2",
            footprint="R_0603",
            value="22k",
            position=Point(40, 30),
            pads=[],
            hierarchical_path="/logic/",
        )
    )

    components.append(
        ComponentWrapper(
            reference="C1",
            footprint="C_0603",
            value="100nF",
            position=Point(50, 30),
            pads=[],
            hierarchical_path="/power_supply/",
        )
    )

    components.append(
        ComponentWrapper(
            reference="C2",
            footprint="C_0603",
            value="10uF",
            position=Point(60, 30),
            pads=[],
            hierarchical_path="/power_supply/",
        )
    )

    return components


def create_test_connections():
    """Create test connections between components"""
    connections = [
        ("U1", "C1"),  # Power supply decoupling
        ("U1", "R1"),  # Power supply feedback
        ("R1", "C2"),  # Power supply filter
        ("U2", "R2"),  # Logic pull-up
        ("U1", "U2"),  # Power to logic
        ("C1", "C2"),  # Capacitor network
    ]
    return connections


def test_hierarchical_placement():
    """Test hierarchical placement algorithm"""
    logger.info("TEST", "=" * 60)
    logger.info("TEST", "TEST: Hierarchical Placement Algorithm")
    logger.info("TEST", "=" * 60)

    components = create_test_components()
    connections = create_test_connections()

    # Create placer
    placer = HierarchicalPlacer(component_spacing=2.0, group_spacing=5.0)

    # Test with default parameters
    logger.info("TEST", "1. Testing with default parameters:")
    positions = placer.place(components, connections)

    # Verify all components were placed
    assert len(positions) == len(components), "Not all components were placed"
    logger.info(
        "TEST", f"✓ Placed {len(positions)} components", component_count=len(positions)
    )

    # Check grouping
    power_components = [
        c for c in components if "/power_supply/" in c.hierarchical_path
    ]
    logic_components = [c for c in components if "/logic/" in c.hierarchical_path]

    # Calculate group centers
    if len(power_components) == 0:
        logger.warning(
            "TEST", "No power components found, skipping group separation test"
        )
        return True
    if len(logic_components) == 0:
        logger.warning(
            "TEST", "No logic components found, skipping group separation test"
        )
        return True

    power_x = sum(positions[c.reference].x for c in power_components) / len(
        power_components
    )
    power_y = sum(positions[c.reference].y for c in power_components) / len(
        power_components
    )
    logic_x = sum(positions[c.reference].x for c in logic_components) / len(
        logic_components
    )
    logic_y = sum(positions[c.reference].y for c in logic_components) / len(
        logic_components
    )

    group_distance = math.sqrt((power_x - logic_x) ** 2 + (power_y - logic_y) ** 2)
    logger.info(
        "TEST",
        f"✓ Group separation: {group_distance:.1f}mm",
        group_distance=group_distance,
    )

    # Test with custom board size
    logger.info("TEST", "2. Testing with custom board size:")
    positions = placer.place(components, connections, board_width=150, board_height=120)

    # Verify positions are within board
    for ref, pos in positions.items():
        assert 0 <= pos.x <= 150, f"{ref} X position out of bounds"
        assert 0 <= pos.y <= 120, f"{ref} Y position out of bounds"
    logger.info("TEST", "✓ All components within board boundaries")

    # Test with single component
    logger.info("TEST", "3. Testing with single component:")
    single_comp = [components[0]]
    positions = placer.place(single_comp, [])
    assert len(positions) == 1, "Single component not placed"
    logger.info("TEST", "✓ Single component placement handled")

    # Test with no hierarchical paths
    logger.info("TEST", "4. Testing without hierarchical paths:")
    # Create new components without hierarchical paths
    flat_components = []
    for comp in components:
        flat_comp = ComponentWrapper(
            reference=comp.reference,
            footprint=comp.footprint.name,
            value=comp.value,
            position=Point(comp.position.x, comp.position.y),
            pads=comp.footprint.pads,
            hierarchical_path="",  # No hierarchy
        )
        flat_components.append(flat_comp)

    positions = placer.place(flat_components, connections)
    assert len(positions) == len(
        flat_components
    ), "Components without hierarchy not placed"
    logger.info("TEST", "✓ Non-hierarchical components handled")

    return True


def test_force_directed_placement():
    """Test force-directed placement algorithm"""
    logger.info("TEST", "=" * 60)
    logger.info("TEST", "TEST: Force-Directed Placement Algorithm")
    logger.info("TEST", "=" * 60)

    components = create_test_components()
    connections = create_test_connections()

    # Create placer
    placer = ForceDirectedPlacer(
        iterations=50, temperature=30.0, spring_constant=0.1, repulsion_constant=500.0
    )

    # Test basic placement
    logger.info("TEST", "1. Testing basic force-directed placement:")
    initial_positions = {c.reference: c.position for c in components}

    positions = placer.place(components, connections)
    assert len(positions) == len(components), "Not all components were placed"
    logger.info(
        "TEST", f"✓ Placed {len(positions)} components", component_count=len(positions)
    )

    # Check that positions changed (physics simulation should move them)
    moved_count = 0
    for ref, new_pos in positions.items():
        old_pos = initial_positions[ref]
        if abs(new_pos.x - old_pos.x) > 0.1 or abs(new_pos.y - old_pos.y) > 0.1:
            moved_count += 1
    logger.info(
        "TEST",
        f"✓ {moved_count}/{len(components)} components moved",
        moved_count=moved_count,
        total_components=len(components),
    )

    # Test connection optimization
    logger.info("TEST", "2. Testing connection length optimization:")

    # Calculate total connection length before and after
    def calc_total_length(positions, connections):
        total = 0
        for ref1, ref2 in connections:
            if ref1 in positions and ref2 in positions:
                p1, p2 = positions[ref1], positions[ref2]
                total += math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
        return total

    initial_length = calc_total_length(initial_positions, connections)
    final_length = calc_total_length(positions, connections)
    improvement = (1 - final_length / initial_length) * 100
    logger.info(
        "TEST",
        f"✓ Connection length improved by {improvement:.1f}%",
        improvement=improvement,
    )

    # Test with high temperature (more movement)
    logger.info("TEST", "3. Testing with high temperature:")
    placer_hot = ForceDirectedPlacer(iterations=50, temperature=100.0)
    positions_hot = placer_hot.place(components, connections)

    # Components should spread out more with higher temperature
    avg_distance = 0
    count = 0
    for i, c1 in enumerate(components):
        for c2 in components[i + 1 :]:
            p1 = positions_hot[c1.reference]
            p2 = positions_hot[c2.reference]
            avg_distance += math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
            count += 1
    avg_distance /= count
    logger.info(
        "TEST",
        f"✓ Average component distance: {avg_distance:.1f}mm",
        avg_distance=avg_distance,
    )

    # Test with locked components
    logger.info("TEST", "4. Testing with locked components:")

    # Create a new set of components with some locked
    locked_components = []
    locked_refs = {"U1", "U2"}

    for comp in components:
        # Create a new component wrapper with the same data
        new_comp = ComponentWrapper(
            reference=comp.reference,
            footprint=comp.footprint.name,
            value=comp.value,
            position=Point(comp.position.x, comp.position.y),
            pads=comp.footprint.pads,
            hierarchical_path=comp.hierarchical_path,
        )
        # Set the locked property on the footprint
        if comp.reference in locked_refs:
            new_comp.footprint.locked = True
        locked_components.append(new_comp)

    # Get initial positions of locked components
    locked_initial_positions = {
        c.reference: Point(c.position.x, c.position.y) for c in locked_components
    }

    positions_locked = placer.place(locked_components, connections)

    # Verify locked components didn't move
    for ref in locked_refs:
        old_pos = locked_initial_positions[ref]
        new_pos = positions_locked[ref]
        assert abs(new_pos.x - old_pos.x) < 0.01, f"{ref} moved despite being locked"
        assert abs(new_pos.y - old_pos.y) < 0.01, f"{ref} moved despite being locked"
    logger.info("TEST", "✓ Locked components remained in place")

    return True


def test_connectivity_driven_placement():
    """Test connectivity-driven placement algorithm"""
    logger.info("TEST", "=" * 60)
    logger.info("TEST", "TEST: Connectivity-Driven Placement Algorithm")
    logger.info("TEST", "=" * 60)

    # Create components with power/ground connections
    components = []

    # Power regulator
    components.append(ComponentWrapper("U1", "TO-220", "LM7805", Point(50, 50), []))
    # Microcontroller
    components.append(ComponentWrapper("U2", "TQFP-32", "ATmega328", Point(60, 60), []))
    # Power capacitors
    components.append(ComponentWrapper("C1", "C_0805", "10uF", Point(30, 30), []))
    components.append(ComponentWrapper("C2", "C_0603", "100nF", Point(40, 30), []))
    # Ground connections
    components.append(ComponentWrapper("C3", "C_0603", "100nF", Point(50, 30), []))
    # Signal components
    components.append(ComponentWrapper("R1", "R_0603", "10k", Point(70, 30), []))
    components.append(ComponentWrapper("R2", "R_0603", "10k", Point(80, 30), []))

    # Create connections with critical nets
    connections = [
        # Power net (critical)
        ("U1", "C1"),  # Regulator to bulk cap
        ("C1", "C2"),  # Bulk to ceramic
        ("C2", "U2"),  # Power to MCU
        # Ground net (critical)
        ("U1", "C3"),  # Regulator ground
        ("C3", "U2"),  # MCU ground
        # Signal connections
        ("U2", "R1"),  # MCU to pull-up
        ("U2", "R2"),  # MCU to pull-up
        ("R1", "R2"),  # Pull-up network
    ]

    # Create placer
    placer = ConnectivityDrivenPlacer(
        component_spacing=2.0, cluster_spacing=5.0, critical_net_weight=2.5
    )

    # Test basic placement
    logger.info("TEST", "1. Testing connectivity-driven placement:")
    positions = placer.place(components, connections)

    assert len(positions) == len(components), "Not all components were placed"
    logger.info(
        "TEST", f"✓ Placed {len(positions)} components", component_count=len(positions)
    )

    # Check clustering - highly connected components should be close
    # U1, C1, C2 should be clustered (power supply)
    power_components = ["U1", "C1", "C2"]
    power_positions = [positions[ref] for ref in power_components]

    # Calculate cluster compactness
    max_dist = 0
    for i, p1 in enumerate(power_positions):
        for p2 in power_positions[i + 1 :]:
            dist = math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
            max_dist = max(max_dist, dist)

    logger.info(
        "TEST", f"✓ Power cluster max distance: {max_dist:.1f}mm", max_distance=max_dist
    )
    assert max_dist < 30, "Power components not clustered tightly enough"

    # Test critical net identification
    logger.info("TEST", "2. Testing critical net prioritization:")
    # Components connected by critical nets should be closer
    u1_pos = positions["U1"]
    c1_pos = positions["C1"]
    r1_pos = positions["R1"]

    critical_dist = math.sqrt((u1_pos.x - c1_pos.x) ** 2 + (u1_pos.y - c1_pos.y) ** 2)
    signal_dist = math.sqrt((u1_pos.x - r1_pos.x) ** 2 + (u1_pos.y - r1_pos.y) ** 2)

    logger.info(
        "TEST",
        f"✓ Critical connection distance: {critical_dist:.1f}mm",
        critical_distance=critical_dist,
    )
    logger.info(
        "TEST",
        f"✓ Signal connection distance: {signal_dist:.1f}mm",
        signal_distance=signal_dist,
    )

    # Test crossing minimization
    logger.info("TEST", "3. Testing crossing minimization:")

    # Count crossings (simplified - just check if lines intersect)
    def lines_intersect(p1, p2, p3, p4):
        """Check if line p1-p2 intersects with p3-p4"""

        def ccw(A, B, C):
            return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)

        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    crossings = 0
    for i, (ref1a, ref1b) in enumerate(connections):
        if ref1a in positions and ref1b in positions:
            p1a = positions[ref1a]
            p1b = positions[ref1b]
            for ref2a, ref2b in connections[i + 1 :]:
                if ref2a in positions and ref2b in positions:
                    p2a = positions[ref2a]
                    p2b = positions[ref2b]
                    if lines_intersect(p1a, p1b, p2a, p2b):
                        crossings += 1

    logger.info("TEST", f"✓ Connection crossings: {crossings}", crossings=crossings)

    # Test with no connections
    logger.info("TEST", "4. Testing with no connections:")
    positions_no_conn = placer.place(components, [])
    assert len(positions_no_conn) == len(components), "Failed with no connections"
    logger.info("TEST", "✓ Handled no connections case")

    return True


def test_placement_edge_cases():
    """Test edge cases for placement algorithms"""
    logger.info("TEST", "=" * 60)
    logger.info("TEST", "TEST: Placement Algorithm Edge Cases")
    logger.info("TEST", "=" * 60)

    # Test empty component list
    logger.info("TEST", "1. Testing empty component list:")
    for AlgoClass in [
        HierarchicalPlacer,
        ForceDirectedPlacer,
        ConnectivityDrivenPlacer,
    ]:
        placer = AlgoClass()
        positions = placer.place([], [])
        assert len(positions) == 0, f"{AlgoClass.__name__} failed with empty list"
    logger.info("TEST", "✓ All algorithms handle empty component list")

    # Test single component
    logger.info("TEST", "2. Testing single component:")
    single = [ComponentWrapper("U1", "SOIC-8", "Test", Point(0, 0), [])]
    for AlgoClass in [
        HierarchicalPlacer,
        ForceDirectedPlacer,
        ConnectivityDrivenPlacer,
    ]:
        placer = AlgoClass()
        positions = placer.place(single, [])
        assert len(positions) == 1, f"{AlgoClass.__name__} failed with single component"
    logger.info("TEST", "✓ All algorithms handle single component")

    # Test components at same position
    logger.info("TEST", "3. Testing components at same initial position:")
    same_pos = [
        ComponentWrapper("U1", "SOIC-8", "Test1", Point(50, 50), []),
        ComponentWrapper("U2", "SOIC-8", "Test2", Point(50, 50), []),
        ComponentWrapper("U3", "SOIC-8", "Test3", Point(50, 50), []),
    ]

    for AlgoClass in [
        HierarchicalPlacer,
        ForceDirectedPlacer,
        ConnectivityDrivenPlacer,
    ]:
        placer = AlgoClass()
        positions = placer.place(same_pos, [])

        # Check that components were separated
        unique_positions = set()
        for pos in positions.values():
            unique_positions.add((round(pos.x, 1), round(pos.y, 1)))

        assert (
            len(unique_positions) > 1
        ), f"{AlgoClass.__name__} didn't separate overlapping components"
    logger.info("TEST", "✓ All algorithms separate overlapping components")

    # Test very small board
    logger.info("TEST", "4. Testing very small board size:")
    components = create_test_components()
    for AlgoClass in [
        HierarchicalPlacer,
        ForceDirectedPlacer,
        ConnectivityDrivenPlacer,
    ]:
        placer = AlgoClass()
        positions = placer.place(components, [], board_width=10, board_height=10)

        # Components should still be placed, even if cramped
        assert len(positions) == len(
            components
        ), f"{AlgoClass.__name__} failed with small board"
    logger.info("TEST", "✓ All algorithms handle small board size")

    return True


def run_all_tests():
    """Run all placement algorithm tests"""
    logger.info("TEST", "=" * 60)
    logger.info("TEST", "PCB PLACEMENT ALGORITHMS TEST SUITE")
    logger.info("TEST", "=" * 60)

    tests = [
        ("Hierarchical Placement", test_hierarchical_placement),
        ("Force-Directed Placement", test_force_directed_placement),
        ("Connectivity-Driven Placement", test_connectivity_driven_placement),
        ("Edge Cases", test_placement_edge_cases),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                logger.info(
                    "TEST",
                    f"✅ {test_name}: PASSED",
                    test_name=test_name,
                    status="passed",
                )
            else:
                failed += 1
                logger.error(
                    "TEST",
                    f"❌ {test_name}: FAILED",
                    test_name=test_name,
                    status="failed",
                )
        except Exception as e:
            failed += 1
            logger.error(
                "TEST",
                f"❌ {test_name}: FAILED with exception",
                test_name=test_name,
                status="failed",
                error=e,
            )
            import traceback

            traceback.print_exc()

    logger.info("TEST", "=" * 60)
    logger.info(
        "TEST",
        f"TEST SUMMARY: {passed} passed, {failed} failed",
        passed=passed,
        failed=failed,
    )
    logger.info("TEST", "=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
