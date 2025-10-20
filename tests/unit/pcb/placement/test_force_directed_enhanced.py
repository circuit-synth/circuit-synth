"""
Unit tests for enhanced force-directed placement algorithm.

Tests cover:
- Net weighting based on type (power, ground, clock)
- Component grouping by hierarchical paths
- Trace length optimization
- Physical constraints (board boundaries)
- Collision resolution
- Multi-phase optimization
"""

import math
import pytest

from circuit_synth.pcb.placement.base import ComponentWrapper
from circuit_synth.pcb.placement.force_directed_enhanced import (
    EnhancedForceDirectedPlacer,
    NetInfo,
    ComponentNode,
    Connection,
)
from circuit_synth.pcb.types import Footprint, Point


class TestNetInfo:
    """Test NetInfo weight calculation."""

    def test_basic_net_weight(self):
        """Basic 2-pin net should have weight of 1.0."""
        net = NetInfo(net_name="test", pin_count=2)
        assert net.get_weight() == pytest.approx(1.0)

    def test_power_net_weight(self):
        """Power nets should have higher weight."""
        net = NetInfo(net_name="VCC", pin_count=2, is_power=True)
        assert net.get_weight() > 1.5

    def test_ground_net_weight(self):
        """Ground nets should have higher weight."""
        net = NetInfo(net_name="GND", pin_count=2, is_ground=True)
        assert net.get_weight() > 1.5

    def test_clock_net_weight(self):
        """Clock nets should have higher weight."""
        net = NetInfo(net_name="CLK", pin_count=2, is_clock=True)
        assert net.get_weight() > 1.5

    def test_multi_pin_net_weight(self):
        """Multi-pin nets should have higher weight."""
        net2 = NetInfo(net_name="test", pin_count=2)
        net4 = NetInfo(net_name="test", pin_count=4)
        net8 = NetInfo(net_name="test", pin_count=8)

        assert net4.get_weight() > net2.get_weight()
        assert net8.get_weight() > net4.get_weight()

    def test_wide_trace_weight(self):
        """Wider traces should have higher weight."""
        net_thin = NetInfo(net_name="test", pin_count=2, trace_width=0.25)
        net_thick = NetInfo(net_name="test", pin_count=2, trace_width=1.0)

        assert net_thick.get_weight() > net_thin.get_weight()

    def test_combined_weights(self):
        """Combined critical factors should multiply weights."""
        net_basic = NetInfo(net_name="test", pin_count=2)
        net_critical = NetInfo(
            net_name="VCC",
            pin_count=8,
            is_power=True,
            trace_width=1.0
        )

        # Critical net should have significantly higher weight
        assert net_critical.get_weight() > net_basic.get_weight() * 3


class TestComponentNode:
    """Test ComponentNode behavior."""

    def create_test_component(self, ref: str, x: float = 0, y: float = 0) -> ComponentWrapper:
        """Helper to create a test component."""
        fp = Footprint(
            library="Test",
            name="TestFootprint",
            reference=ref,
            value="10k",
            position=Point(x, y),
            pads=[],
        )
        return ComponentWrapper(fp)

    def test_node_creation(self):
        """Test creating a component node."""
        comp = self.create_test_component("R1", 10, 20)
        node = ComponentNode(component=comp, position=Point(10, 20))

        assert node.reference == "R1"
        assert node.position.x == 10
        assert node.position.y == 20
        assert not node.locked

    def test_force_reset(self):
        """Test force reset functionality."""
        comp = self.create_test_component("R1")
        node = ComponentNode(component=comp)

        node.add_force(10, 20)
        assert node.force.x != 0
        assert node.force.y != 0

        node.reset_force()
        assert node.force.x == 0
        assert node.force.y == 0

    def test_force_accumulation(self):
        """Test that forces accumulate correctly."""
        comp = self.create_test_component("R1")
        node = ComponentNode(component=comp)

        node.add_force(10, 20)
        node.add_force(5, -10)

        assert node.force.x == pytest.approx(15)
        assert node.force.y == pytest.approx(10)

    def test_position_update(self):
        """Test position updates from forces."""
        comp = self.create_test_component("R1", 0, 0)
        node = ComponentNode(component=comp, position=Point(0, 0))

        # Apply force to the right
        node.add_force(10, 0)
        node.update_position(damping=1.0, max_displacement=5.0)

        # Should move right, limited by max displacement
        assert node.position.x > 0
        assert node.position.x <= 5.0

    def test_locked_node_doesnt_move(self):
        """Locked nodes should not move."""
        comp = self.create_test_component("R1", 0, 0)
        node = ComponentNode(component=comp, position=Point(0, 0), locked=True)

        node.add_force(100, 100)
        node.update_position(damping=1.0, max_displacement=10.0)

        # Should not move
        assert node.position.x == 0
        assert node.position.y == 0


class TestEnhancedForceDirectedPlacer:
    """Test the enhanced force-directed placer."""

    def create_test_components(self, n: int = 3) -> list[ComponentWrapper]:
        """Create test components."""
        components = []
        for i in range(n):
            fp = Footprint(
                library="Test",
                name="TestFootprint",
                reference=f"R{i+1}",
                value="10k",
                position=Point(0, 0),
                pads=[],
            )
            components.append(ComponentWrapper(fp))
        return components

    def test_placer_initialization(self):
        """Test placer can be initialized with default parameters."""
        placer = EnhancedForceDirectedPlacer()

        assert placer.spring_constant > 0
        assert placer.repulsion_constant > 0
        assert placer.iterations > 0

    def test_basic_placement(self):
        """Test basic placement of components."""
        placer = EnhancedForceDirectedPlacer(iterations=50)
        components = self.create_test_components(3)

        # Connect them in a line: R1 - R2 - R3
        connections = [("R1", "R2"), ("R2", "R3")]

        positions = placer.place(components, connections, board_width=100, board_height=100)

        # Should have positions for all components
        assert len(positions) == 3
        assert "R1" in positions
        assert "R2" in positions
        assert "R3" in positions

        # R2 should be between R1 and R3 (roughly)
        assert positions["R1"].x < positions["R2"].x < positions["R3"].x or \
               positions["R3"].x < positions["R2"].x < positions["R1"].x or \
               positions["R1"].y < positions["R2"].y < positions["R3"].y or \
               positions["R3"].y < positions["R2"].y < positions["R1"].y

    def test_net_weighting_affects_placement(self):
        """Test that net weighting affects placement."""
        # Create two separate pairs of components
        components = self.create_test_components(4)

        # R1-R2 is a critical power connection
        # R3-R4 is a basic signal connection
        connections = [("R1", "R2"), ("R3", "R4")]

        # Create net info with one critical connection
        net_info = {
            ("R1", "R2"): NetInfo(net_name="VCC", pin_count=2, is_power=True),
            ("R3", "R4"): NetInfo(net_name="SIG", pin_count=2),
        }

        placer = EnhancedForceDirectedPlacer(
            iterations=100,
            enable_net_weighting=True
        )

        positions = placer.place(
            components,
            connections,
            board_width=100,
            board_height=100,
            net_info=net_info
        )

        # Calculate distances
        dist_r1_r2 = math.sqrt(
            (positions["R1"].x - positions["R2"].x) ** 2 +
            (positions["R1"].y - positions["R2"].y) ** 2
        )
        dist_r3_r4 = math.sqrt(
            (positions["R3"].x - positions["R4"].x) ** 2 +
            (positions["R3"].y - positions["R4"].y) ** 2
        )

        # Critical connection should result in closer placement
        assert dist_r1_r2 < dist_r3_r4 * 1.5

    def test_grouping_keeps_components_together(self):
        """Test that hierarchical grouping keeps components together."""
        components = []

        # Create two groups
        for i in range(2):
            fp = Footprint(
                library="Test",
                name="TestFootprint",
                reference=f"R{i+1}",
                value="10k",
                position=Point(0, 0),
                pads=[],
                path="group_a",  # Both in group A
            )
            components.append(ComponentWrapper(fp))

        for i in range(2, 4):
            fp = Footprint(
                library="Test",
                name="TestFootprint",
                reference=f"R{i+1}",
                value="10k",
                position=Point(0, 0),
                pads=[],
                path="group_b",  # Both in group B
            )
            components.append(ComponentWrapper(fp))

        # Connect within groups
        connections = [("R1", "R2"), ("R3", "R4")]

        placer = EnhancedForceDirectedPlacer(
            iterations=100,
            enable_grouping=True,
            grouping_strength=0.5
        )

        positions = placer.place(components, connections, board_width=100, board_height=100)

        # Calculate intra-group distances
        dist_r1_r2 = math.sqrt(
            (positions["R1"].x - positions["R2"].x) ** 2 +
            (positions["R1"].y - positions["R2"].y) ** 2
        )
        dist_r3_r4 = math.sqrt(
            (positions["R3"].x - positions["R4"].x) ** 2 +
            (positions["R3"].y - positions["R4"].y) ** 2
        )

        # Calculate inter-group distances
        dist_r1_r3 = math.sqrt(
            (positions["R1"].x - positions["R3"].x) ** 2 +
            (positions["R1"].y - positions["R3"].y) ** 2
        )

        # Components within groups should be closer than between groups
        assert dist_r1_r2 < dist_r1_r3
        assert dist_r3_r4 < dist_r1_r3

    def test_boundary_forces_keep_components_on_board(self):
        """Test that components stay within board boundaries."""
        placer = EnhancedForceDirectedPlacer(
            iterations=150,
            board_margin=5.0,
            boundary_strength=25.0  # Stronger boundary forces
        )

        components = self.create_test_components(5)
        connections = [("R1", "R2"), ("R2", "R3"), ("R3", "R4"), ("R4", "R5")]

        board_width = 50
        board_height = 50

        positions = placer.place(
            components,
            connections,
            board_width=board_width,
            board_height=board_height
        )

        # All components should be within board bounds with margin
        # Allow small tolerance for edge cases
        margin = placer.board_margin
        tolerance = 1.0  # Allow 1mm tolerance for edge components
        for ref, pos in positions.items():
            assert margin - tolerance <= pos.x <= board_width - margin + tolerance, \
                f"{ref} x={pos.x} outside bounds [{margin-tolerance}, {board_width-margin+tolerance}]"
            assert margin - tolerance <= pos.y <= board_height - margin + tolerance, \
                f"{ref} y={pos.y} outside bounds [{margin-tolerance}, {board_height-margin+tolerance}]"

    def test_locked_components_dont_move(self):
        """Test that locked components stay in place."""
        components = self.create_test_components(3)

        # Lock R2 at a specific position
        components[1].footprint.locked = True
        components[1].footprint.position = Point(50, 50)

        connections = [("R1", "R2"), ("R2", "R3")]

        placer = EnhancedForceDirectedPlacer(iterations=100)
        positions = placer.place(components, connections, board_width=100, board_height=100)

        # R2 should not have moved
        assert positions["R2"].x == pytest.approx(50)
        assert positions["R2"].y == pytest.approx(50)

        # R1 and R3 should be attracted to R2
        dist_r1_r2 = math.sqrt(
            (positions["R1"].x - positions["R2"].x) ** 2 +
            (positions["R1"].y - positions["R2"].y) ** 2
        )
        dist_r3_r2 = math.sqrt(
            (positions["R3"].x - positions["R2"].x) ** 2 +
            (positions["R3"].y - positions["R2"].y) ** 2
        )

        # Connected components should be relatively close to locked component
        assert dist_r1_r2 < 40  # Within reasonable distance
        assert dist_r3_r2 < 40

    def test_auto_detection_of_power_nets(self):
        """Test automatic detection of power nets from component values."""
        components = []

        # Create component connected to VCC
        fp1 = Footprint(
            library="Test",
            name="TestFootprint",
            reference="C1",
            value="VCC",
            position=Point(0, 0),
            pads=[],
        )
        components.append(ComponentWrapper(fp1))

        # Create component connected to GND
        fp2 = Footprint(
            library="Test",
            name="TestFootprint",
            reference="C2",
            value="GND",
            position=Point(0, 0),
            pads=[],
        )
        components.append(ComponentWrapper(fp2))

        connections = [("C1", "C2")]

        placer = EnhancedForceDirectedPlacer(
            iterations=50,
            enable_net_weighting=True
        )

        # Build connections and check auto-detection
        placer._build_nodes(components)
        placer._build_connections(connections, net_info=None)

        # Should have auto-detected power/ground
        assert len(placer.connections) == 1
        conn = placer.connections[0]

        # Weight should be higher due to power/ground detection
        assert conn.weight > 1.5

    def test_trace_length_optimization(self):
        """Test that algorithm minimizes total trace length."""
        components = self.create_test_components(4)

        # Create a star topology: R1 connects to R2, R3, R4
        connections = [("R1", "R2"), ("R1", "R3"), ("R1", "R4")]

        placer = EnhancedForceDirectedPlacer(iterations=100)
        positions = placer.place(components, connections, board_width=100, board_height=100)

        # R1 should be roughly in the center of the other components
        center_x = (positions["R2"].x + positions["R3"].x + positions["R4"].x) / 3
        center_y = (positions["R2"].y + positions["R3"].y + positions["R4"].y) / 3

        dist_to_center = math.sqrt(
            (positions["R1"].x - center_x) ** 2 +
            (positions["R1"].y - center_y) ** 2
        )

        # R1 should be close to the geometric center
        max_deviation = 15.0  # Allow some deviation
        assert dist_to_center < max_deviation

    def test_collision_resolution(self):
        """Test that collision resolution prevents overlaps."""
        placer = EnhancedForceDirectedPlacer(
            iterations=100,
            enable_collision_resolution=True,
            component_spacing=5.0
        )

        # Create components that might collide
        components = self.create_test_components(10)

        # Dense connectivity that might cause overlaps
        connections = []
        for i in range(9):
            connections.append((f"R{i+1}", f"R{i+2}"))

        positions = placer.place(
            components,
            connections,
            board_width=50,
            board_height=50
        )

        # Check that no components are too close
        min_spacing = placer.component_spacing
        refs = list(positions.keys())

        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                dist = math.sqrt(
                    (positions[refs[i]].x - positions[refs[j]].x) ** 2 +
                    (positions[refs[i]].y - positions[refs[j]].y) ** 2
                )
                # Allow small violations due to approximation
                assert dist >= min_spacing * 0.5, \
                    f"{refs[i]} and {refs[j]} too close: {dist:.2f}mm"

    def test_multi_phase_optimization(self):
        """Test that multi-phase optimization produces good results."""
        placer = EnhancedForceDirectedPlacer(
            iterations=150,  # 3 phases of 50 each
            enable_grouping=True,
            enable_net_weighting=True,
            enable_collision_resolution=True
        )

        components = self.create_test_components(6)

        # Create a more complex topology
        connections = [
            ("R1", "R2"),
            ("R2", "R3"),
            ("R3", "R4"),
            ("R4", "R1"),  # Create a cycle
            ("R2", "R5"),
            ("R4", "R6"),
        ]

        positions = placer.place(components, connections, board_width=100, board_height=100)

        # Should have valid positions for all components
        assert len(positions) == 6

        # Components should be well-distributed (not all clumped)
        xs = [pos.x for pos in positions.values()]
        ys = [pos.y for pos in positions.values()]

        x_range = max(xs) - min(xs)
        y_range = max(ys) - min(ys)

        # Should use at least some of the board space
        assert x_range > 20
        assert y_range > 20

    def test_empty_component_list(self):
        """Test handling of empty component list."""
        placer = EnhancedForceDirectedPlacer()
        positions = placer.place([], [], board_width=100, board_height=100)
        assert positions == {}

    def test_single_component(self):
        """Test placement of single component."""
        placer = EnhancedForceDirectedPlacer()
        components = self.create_test_components(1)
        positions = placer.place(components, [], board_width=100, board_height=100)

        assert len(positions) == 1
        assert "R1" in positions

        # Should be on the board
        assert 0 <= positions["R1"].x <= 100
        assert 0 <= positions["R1"].y <= 100
