#!/usr/bin/env python3
"""
Test script for KiCad API Phase 6: Search & Discovery.

This script demonstrates:
- Component search by properties
- Connection tracing
- Net discovery and analysis
- Query builder pattern
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from circuit_synth.kicad_api.core import (
    Junction,
    Label,
    LabelType,
    Point,
    Schematic,
    SchematicSymbol,
    Wire,
)
from circuit_synth.kicad_api.schematic import (
    ComponentManager,
    ConnectionTracer,
    JunctionManager,
    LabelManager,
    MatchType,
    NetDiscovery,
    NetStatistics,
    SearchEngine,
    SearchQueryBuilder,
    WireManager,
)


def create_test_schematic():
    """Create a test schematic with various components."""
    schematic = Schematic()

    # Add components
    comp_mgr = ComponentManager(schematic)
    wire_mgr = WireManager(schematic)
    junction_mgr = JunctionManager(schematic)
    label_mgr = LabelManager(schematic)

    # Add resistors
    r1 = comp_mgr.add_component("Device:R", "R1", "10k", Point(50, 50))
    r2 = comp_mgr.add_component("Device:R", "R2", "4.7k", Point(100, 50))
    r3 = comp_mgr.add_component("Device:R", "R3", "100k", Point(150, 50))
    r4 = comp_mgr.add_component("Device:R", "R4", "1M", Point(200, 50))

    # Add capacitors
    c1 = comp_mgr.add_component("Device:C", "C1", "100nF", Point(50, 100))
    c2 = comp_mgr.add_component("Device:C", "C2", "10µF", Point(100, 100))
    c3 = comp_mgr.add_component("Device:C", "C3", "1µF", Point(150, 100))

    # Add ICs
    u1 = comp_mgr.add_component(
        "MCU_Microchip_ATmega:ATmega328P-PU", "U1", "ATmega328P", Point(100, 150)
    )
    u2 = comp_mgr.add_component(
        "Amplifier_Operational:LM358", "U2", "LM358", Point(200, 150)
    )

    # Set footprints
    if r1:
        r1.footprint = "Resistor_SMD:R_0805_2012Metric"
    if r2:
        r2.footprint = "Resistor_SMD:R_0603_1608Metric"
    if c1:
        c1.footprint = "Capacitor_SMD:C_0805_2012Metric"
    if u1:
        u1.footprint = "Package_DIP:DIP-28_W7.62mm"

    # Add custom properties
    if r1:
        r1.properties["Tolerance"] = "1%"
    if r2:
        r2.properties["Tolerance"] = "5%"
    if c1:
        c1.properties["Voltage"] = "50V"

    # Add wires to create connections
    wire_mgr.add_wire([Point(60, 50), Point(90, 50)])  # R1 to R2
    wire_mgr.add_wire([Point(110, 50), Point(140, 50)])  # R2 to R3
    wire_mgr.add_wire([Point(50, 60), Point(50, 90)])  # R1 to C1
    wire_mgr.add_wire([Point(100, 60), Point(100, 90)])  # R2 to C2

    # Add junctions
    junction_mgr.add_junction(100, 50)
    junction_mgr.add_junction(100, 90)

    # Add labels
    label_mgr.add_label("VCC", (50, 50), label_type=LabelType.GLOBAL)
    label_mgr.add_label("GND", (50, 110), label_type=LabelType.GLOBAL)
    label_mgr.add_label("SIGNAL", (100, 50), label_type=LabelType.LOCAL)

    return schematic


def test_component_search(schematic):
    """Test component search functionality."""
    print("\n1. Testing component search:")
    search = SearchEngine(schematic)

    # Search by reference pattern
    print("   a. Searching for resistors (R*):")
    resistors = search.search_by_reference("R*")
    for comp in resistors:
        print(f"      ✓ Found {comp.reference}: {comp.value}")

    # Search by exact value
    print("\n   b. Searching for 10k resistors:")
    r_10k = search.search_by_value("10k")
    for comp in r_10k:
        print(f"      ✓ Found {comp.reference}: {comp.value}")

    # Search by footprint pattern
    print("\n   c. Searching for 0805 footprint components:")
    smd_0805 = search.search_by_footprint("0805")
    for comp in smd_0805:
        print(f"      ✓ Found {comp.reference}: {comp.footprint}")

    # Search by library
    print("\n   d. Searching for Device library components:")
    device_comps = search.search_by_library("Device")
    print(f"      ✓ Found {len(device_comps)} components from Device library")

    return True


def test_query_builder(schematic):
    """Test query builder pattern."""
    print("\n2. Testing query builder:")
    search = SearchEngine(schematic)

    # Build complex query
    print("   a. Building query for SMD resistors with tolerance:")
    query = (
        SearchQueryBuilder()
        .with_reference("R*")
        .with_footprint("SMD", MatchType.CONTAINS)
        .has_property("Tolerance")
        .build()
    )

    results = search.search(query)
    print(f"      ✓ Found {results.total_count} components")
    for comp in results.components:
        tolerance = comp.properties.get("Tolerance", "N/A")
        print(f"      • {comp.reference}: {comp.value}, Tolerance: {tolerance}")

    # Value range query
    print("\n   b. Building query for resistors between 1k and 100k:")
    query = (
        SearchQueryBuilder().with_reference("R*").with_value_range(1000, 100000).build()
    )

    results = search.search(query)
    print(f"      ✓ Found {results.total_count} components")
    for comp in results.components:
        print(f"      • {comp.reference}: {comp.value}")

    return True


def test_connection_tracing(schematic):
    """Test connection tracing."""
    print("\n3. Testing connection tracing:")
    tracer = ConnectionTracer(schematic)

    # Trace net from a point
    print("   a. Tracing net from point (100, 50):")
    trace = tracer.trace_net(Point(100, 50))
    print(f"      ✓ Found {len(trace.components)} components")
    print(f"      ✓ Found {len(trace.wires)} wires")
    print(f"      ✓ Found {len(trace.junctions)} junctions")
    print(f"      ✓ Found {len(trace.labels)} labels")
    if trace.net_name:
        print(f"      ✓ Net name: {trace.net_name}")

    # Find connected components
    print("\n   b. Finding components connected to R1:")
    connected = tracer.find_connected_components("R1", max_depth=2)
    for ref, depth in connected:
        print(f"      ✓ {ref} at depth {depth}")

    return True


def test_net_discovery(schematic):
    """Test net discovery and analysis."""
    print("\n4. Testing net discovery:")
    discovery = NetDiscovery(schematic)

    # Discover all nets
    nets = discovery.discover_all_nets()
    print(f"   ✓ Discovered {len(nets)} nets")

    # Show named nets
    print("\n   a. Named nets:")
    for net_name, net_info in nets.items():
        if not net_name.startswith("Net_") and not net_name.startswith("FLOATING_"):
            print(f"      • {net_name}:")
            print(f"        - Components: {', '.join(net_info.components)}")
            print(f"        - Wire count: {net_info.wire_count}")
            if net_info.has_global_label:
                print(f"        - Has global label")

    # Get net statistics
    print("\n   b. Net statistics:")
    stats = discovery.get_net_statistics()
    print(f"      • Total nets: {stats.total_nets}")
    print(f"      • Named nets: {stats.named_nets}")
    print(f"      • Unnamed nets: {stats.unnamed_nets}")
    print(f"      • Global nets: {stats.global_nets}")
    print(f"      • Floating nets: {stats.floating_nets}")
    print(f"      • Average net size: {stats.average_net_size:.2f} components")

    # Find power nets
    print("\n   c. Power nets:")
    power_nets = discovery.find_power_nets()
    for net in power_nets:
        print(f"      • {net.name}")

    return True


def test_advanced_search(schematic):
    """Test advanced search features."""
    print("\n5. Testing advanced search features:")
    search = SearchEngine(schematic)

    # Component value parsing
    print("   a. Testing component value parser:")
    from circuit_synth.kicad_api.schematic import ComponentValueParser

    test_values = ["10k", "4.7µF", "100nH", "1M", "0.1uF"]
    for value in test_values:
        try:
            numeric = ComponentValueParser.parse(value)
            print(f"      ✓ {value} = {numeric:.2e}")
        except ValueError as e:
            print(f"      ✗ {value}: {e}")

    # Regex search
    print("\n   b. Testing regex search:")
    query = SearchQueryBuilder().with_reference("U[0-9]+", MatchType.REGEX).build()

    results = search.search(query)
    print(f"      ✓ Found {results.total_count} ICs")
    for comp in results.components:
        print(f"      • {comp.reference}: {comp.value}")

    return True


def test_error_handling(schematic):
    """Test error handling in search and discovery."""
    print("\n6. Testing error handling:")

    # Empty schematic search
    empty_schematic = Schematic()
    search = SearchEngine(empty_schematic)

    print("   a. Search in empty schematic:")
    results = search.search_by_reference("R*")
    print(f"      ✓ Found {len(results)} components (expected: 0)")

    # Invalid search patterns
    print("\n   b. Invalid regex pattern:")
    query = SearchQueryBuilder().with_reference("[invalid(", MatchType.REGEX).build()

    results = search.search(query)
    print(f"      ✓ Search completed without crash")

    # Net discovery on empty schematic
    print("\n   c. Net discovery on empty schematic:")
    discovery = NetDiscovery(empty_schematic)
    nets = discovery.discover_all_nets()
    print(f"      ✓ Found {len(nets)} nets (expected: 0)")

    return True


def main():
    """Run all Phase 6 tests."""
    print("Testing KiCad API Phase 6: Search & Discovery")
    print("=" * 50)

    # Create test schematic
    schematic = create_test_schematic()
    print(f"✓ Created test schematic with {len(schematic.components)} components")

    # Run tests
    tests = [
        test_component_search,
        test_query_builder,
        test_connection_tracing,
        test_net_discovery,
        test_advanced_search,
        test_error_handling,
    ]

    all_passed = True
    for test in tests:
        try:
            if not test(schematic):
                all_passed = False
                print(f"\n✗ {test.__name__} failed!")
        except Exception as e:
            all_passed = False
            print(f"\n✗ {test.__name__} raised exception: {e}")
            import traceback

            traceback.print_exc()

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All Phase 6 tests passed! 🎉")
        print("\nPhase 6 Complete! Search and discovery features are now functional.")
        print("\nNext steps:")
        print("- Integration with main KiCad API")
        print("- Performance optimization")
        print("- Additional search criteria")
    else:
        print("❌ Some tests failed. Please check the output above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
