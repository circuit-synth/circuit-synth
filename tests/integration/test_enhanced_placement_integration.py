"""
Integration tests for enhanced force-directed placement algorithm.

Tests with real circuit patterns to verify improvements over basic algorithm.
"""

import math
import pytest

from circuit_synth.pcb.placement.force_directed import ForceDirectedPlacer
from circuit_synth.pcb.placement.force_directed_enhanced import (
    EnhancedForceDirectedPlacer,
    NetInfo,
)
from circuit_synth.pcb.placement.base import ComponentWrapper
from circuit_synth.pcb.types import Footprint, Point


class TestRealCircuitPatterns:
    """Test with realistic circuit patterns."""

    def create_power_supply_circuit(self) -> tuple[list, list, dict]:
        """
        Create a power supply circuit pattern.

        Topology:
        - VIN -> Voltage Regulator (U1) -> VOUT
        - Decoupling caps on input (C1) and output (C2, C3)
        - Feedback resistors (R1, R2)
        """
        components = []

        # Voltage regulator
        fp = Footprint(
            library="Package_TO_SOT_SMD",
            name="SOT-23-5",
            reference="U1",
            value="LDO",
            position=Point(0, 0),
            pads=[],
        )
        components.append(ComponentWrapper(fp))

        # Input capacitor (power net)
        fp = Footprint(
            library="Capacitor_SMD",
            name="C_0805",
            reference="C1",
            value="10uF",
            position=Point(0, 0),
            pads=[],
        )
        components.append(ComponentWrapper(fp))

        # Output capacitors (power net)
        for i in [2, 3]:
            fp = Footprint(
                library="Capacitor_SMD",
                name="C_0805",
                reference=f"C{i}",
                value="22uF",
                position=Point(0, 0),
                pads=[],
            )
            components.append(ComponentWrapper(fp))

        # Feedback resistors
        for i in [1, 2]:
            fp = Footprint(
                library="Resistor_SMD",
                name="R_0603",
                reference=f"R{i}",
                value="10k",
                position=Point(0, 0),
                pads=[],
            )
            components.append(ComponentWrapper(fp))

        # Connections
        connections = [
            ("C1", "U1"),  # Input cap to regulator
            ("U1", "C2"),  # Regulator to output cap
            ("U1", "C3"),  # Regulator to output cap
            ("U1", "R1"),  # Feedback divider
            ("R1", "R2"),
        ]

        # Net info - power nets should be weighted higher
        net_info = {
            ("C1", "U1"): NetInfo(
                net_name="VIN", pin_count=3, is_power=True, trace_width=0.5
            ),
            ("U1", "C2"): NetInfo(
                net_name="VOUT", pin_count=4, is_power=True, trace_width=0.5
            ),
            ("U1", "C3"): NetInfo(
                net_name="VOUT", pin_count=4, is_power=True, trace_width=0.5
            ),
            ("U1", "R1"): NetInfo(net_name="FB", pin_count=3, is_high_speed=False),
            ("R1", "R2"): NetInfo(net_name="FB", pin_count=3, is_high_speed=False),
        }

        return components, connections, net_info

    def create_hierarchical_circuit(self) -> tuple[list, list]:
        """
        Create a circuit with hierarchical structure.

        Two subcircuits (amplifier stages), each with their own components.
        """
        components = []

        # Stage 1 components (amplifier A)
        for i in [1, 2]:
            fp = Footprint(
                library="Resistor_SMD",
                name="R_0603",
                reference=f"R{i}",
                value="10k",
                position=Point(0, 0),
                pads=[],
                path="amp_a",
            )
            components.append(ComponentWrapper(fp))

        fp = Footprint(
            library="Package_SO",
            name="SOIC-8",
            reference="U1",
            value="OPAMP",
            position=Point(0, 0),
            pads=[],
            path="amp_a",
        )
        components.append(ComponentWrapper(fp))

        # Stage 2 components (amplifier B)
        for i in [3, 4]:
            fp = Footprint(
                library="Resistor_SMD",
                name="R_0603",
                reference=f"R{i}",
                value="10k",
                position=Point(0, 0),
                pads=[],
                path="amp_b",
            )
            components.append(ComponentWrapper(fp))

        fp = Footprint(
            library="Package_SO",
            name="SOIC-8",
            reference="U2",
            value="OPAMP",
            position=Point(0, 0),
            pads=[],
            path="amp_b",
        )
        components.append(ComponentWrapper(fp))

        # Connections
        connections = [
            # Within stage A
            ("R1", "U1"),
            ("U1", "R2"),
            # Between stages
            ("U1", "U2"),
            # Within stage B
            ("R3", "U2"),
            ("U2", "R4"),
        ]

        return components, connections

    def test_power_supply_placement_improvement(self):
        """
        Test that enhanced algorithm produces better power supply layout.

        Expected improvements:
        - Input cap close to regulator input
        - Output caps close to regulator output
        - Feedback resistors close together
        """
        components, connections, net_info = self.create_power_supply_circuit()

        # Test basic algorithm
        basic_placer = ForceDirectedPlacer(iterations=100)
        basic_positions = basic_placer.place(
            components, connections, board_width=50, board_height=50
        )

        # Test enhanced algorithm with net weighting
        enhanced_placer = EnhancedForceDirectedPlacer(
            iterations=150,
            enable_net_weighting=True,
            enable_collision_resolution=True,
        )
        enhanced_positions = enhanced_placer.place(
            components, connections, board_width=50, board_height=50, net_info=net_info
        )

        # Calculate wire lengths for critical power nets
        def calc_wire_length(positions, conn_list):
            total = 0
            for ref1, ref2 in conn_list:
                dx = positions[ref1].x - positions[ref2].x
                dy = positions[ref1].y - positions[ref2].y
                total += math.sqrt(dx * dx + dy * dy)
            return total

        # Power connections (should be shorter with enhanced algorithm)
        power_conns = [("C1", "U1"), ("U1", "C2"), ("U1", "C3")]

        basic_power_length = calc_wire_length(basic_positions, power_conns)
        enhanced_power_length = calc_wire_length(enhanced_positions, power_conns)

        # Enhanced should have shorter power traces (or similar)
        # Allow for some variance due to random initialization
        assert enhanced_power_length <= basic_power_length * 1.2, \
            f"Enhanced power traces ({enhanced_power_length:.2f}mm) should be " \
            f"similar or shorter than basic ({basic_power_length:.2f}mm)"

        # Output caps should be close to each other
        c2_c3_dist_enhanced = math.sqrt(
            (enhanced_positions["C2"].x - enhanced_positions["C3"].x) ** 2 +
            (enhanced_positions["C2"].y - enhanced_positions["C3"].y) ** 2
        )

        # Both output caps connected to same net, should be close
        assert c2_c3_dist_enhanced < 20, \
            f"Output caps should be close together: {c2_c3_dist_enhanced:.2f}mm"

    def test_hierarchical_grouping_improvement(self):
        """
        Test that enhanced algorithm keeps hierarchical groups together.

        Each amplifier stage should be grouped tightly.
        """
        components, connections = self.create_hierarchical_circuit()

        # Enhanced algorithm with grouping
        placer = EnhancedForceDirectedPlacer(
            iterations=150,
            enable_grouping=True,
            grouping_strength=0.5,
        )

        positions = placer.place(components, connections, board_width=80, board_height=80)

        # Calculate centroid of each group
        def calc_centroid(refs, positions):
            x = sum(positions[ref].x for ref in refs)
            y = sum(positions[ref].y for ref in refs)
            return (x / len(refs), y / len(refs))

        amp_a_refs = ["R1", "R2", "U1"]
        amp_b_refs = ["R3", "R4", "U2"]

        centroid_a = calc_centroid(amp_a_refs, positions)
        centroid_b = calc_centroid(amp_b_refs, positions)

        # Calculate max distance from centroid within each group
        def max_dist_from_centroid(refs, positions, centroid):
            max_d = 0
            for ref in refs:
                dx = positions[ref].x - centroid[0]
                dy = positions[ref].y - centroid[1]
                d = math.sqrt(dx * dx + dy * dy)
                max_d = max(max_d, d)
            return max_d

        max_radius_a = max_dist_from_centroid(amp_a_refs, positions, centroid_a)
        max_radius_b = max_dist_from_centroid(amp_b_refs, positions, centroid_b)

        # Distance between group centroids
        inter_group_dist = math.sqrt(
            (centroid_a[0] - centroid_b[0]) ** 2 +
            (centroid_a[1] - centroid_b[1]) ** 2
        )

        # Groups should be more compact than the distance between them
        assert max_radius_a < inter_group_dist * 0.8, \
            f"Group A should be compact: radius={max_radius_a:.2f}, " \
            f"inter-group={inter_group_dist:.2f}"
        assert max_radius_b < inter_group_dist * 0.8, \
            f"Group B should be compact: radius={max_radius_b:.2f}, " \
            f"inter-group={inter_group_dist:.2f}"

    def test_trace_length_optimization(self):
        """Test that enhanced algorithm minimizes total trace length."""
        components, connections, net_info = self.create_power_supply_circuit()

        # Run both algorithms multiple times and compare average results
        # This accounts for random initialization
        basic_lengths = []
        enhanced_lengths = []

        for _ in range(3):
            # Reset positions
            for comp in components:
                comp.footprint.position = Point(0, 0)

            basic_placer = ForceDirectedPlacer(iterations=100)
            basic_positions = basic_placer.place(
                components, connections, board_width=50, board_height=50
            )

            # Calculate total wire length
            total_basic = 0
            for ref1, ref2 in connections:
                dx = basic_positions[ref1].x - basic_positions[ref2].x
                dy = basic_positions[ref1].y - basic_positions[ref2].y
                total_basic += math.sqrt(dx * dx + dy * dy)

            basic_lengths.append(total_basic)

            # Reset positions again
            for comp in components:
                comp.footprint.position = Point(0, 0)

            enhanced_placer = EnhancedForceDirectedPlacer(
                iterations=150,
                enable_net_weighting=True,
            )
            enhanced_positions = enhanced_placer.place(
                components,
                connections,
                board_width=50,
                board_height=50,
                net_info=net_info,
            )

            total_enhanced = 0
            for ref1, ref2 in connections:
                dx = enhanced_positions[ref1].x - enhanced_positions[ref2].x
                dy = enhanced_positions[ref1].y - enhanced_positions[ref2].y
                total_enhanced += math.sqrt(dx * dx + dy * dy)

            enhanced_lengths.append(total_enhanced)

        # Enhanced should have similar or better average length
        avg_basic = sum(basic_lengths) / len(basic_lengths)
        avg_enhanced = sum(enhanced_lengths) / len(enhanced_lengths)

        print(f"\nAverage wire lengths:")
        print(f"  Basic: {avg_basic:.2f}mm")
        print(f"  Enhanced: {avg_enhanced:.2f}mm")
        print(f"  Improvement: {(1 - avg_enhanced/avg_basic)*100:.1f}%")

        # Enhanced should be competitive (within 20%)
        assert avg_enhanced <= avg_basic * 1.2, \
            f"Enhanced ({avg_enhanced:.2f}mm) should be competitive with " \
            f"basic ({avg_basic:.2f}mm)"

    def test_collision_free_dense_circuit(self):
        """Test collision-free placement for dense circuits."""
        # Create a dense circuit with many components
        components = []
        for i in range(20):
            fp = Footprint(
                library="Resistor_SMD",
                name="R_0603",
                reference=f"R{i+1}",
                value="10k",
                position=Point(0, 0),
                pads=[],
            )
            components.append(ComponentWrapper(fp))

        # Create a mesh of connections
        connections = []
        for i in range(19):
            connections.append((f"R{i+1}", f"R{i+2}"))
        # Add some cross connections
        for i in range(0, 18, 3):
            connections.append((f"R{i+1}", f"R{i+3}"))

        placer = EnhancedForceDirectedPlacer(
            iterations=200,
            enable_collision_resolution=True,
            component_spacing=3.0,
        )

        positions = placer.place(
            components, connections, board_width=60, board_height=60
        )

        # Verify no overlaps
        refs = list(positions.keys())
        min_spacing = placer.component_spacing

        overlaps = 0
        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                dist = math.sqrt(
                    (positions[refs[i]].x - positions[refs[j]].x) ** 2 +
                    (positions[refs[i]].y - positions[refs[j]].y) ** 2
                )
                if dist < min_spacing * 0.8:  # Allow small tolerance
                    overlaps += 1

        assert overlaps == 0, f"Found {overlaps} component overlaps"

    def test_backward_compatibility(self):
        """
        Test that enhanced algorithm works with basic inputs.

        Should work without net_info and still produce valid results.
        """
        components, connections, _ = self.create_power_supply_circuit()

        placer = EnhancedForceDirectedPlacer(iterations=100)

        # Should work without net_info
        positions = placer.place(components, connections, board_width=50, board_height=50)

        # Should have positions for all components
        assert len(positions) == len(components)

        # All positions should be on board
        for ref, pos in positions.items():
            assert 0 <= pos.x <= 50
            assert 0 <= pos.y <= 50
