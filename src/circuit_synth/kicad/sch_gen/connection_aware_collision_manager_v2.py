"""
Enhanced connection-aware collision manager with component rotation support.
"""

import logging
import math
from typing import Dict, List, Optional, Set, Tuple

from .collision_manager import MIN_COMPONENT_SPACING, BBox, CollisionManager
from .connection_analyzer import ConnectionAnalyzer

logger = logging.getLogger(__name__)


class ConnectionAwareCollisionManagerV2(CollisionManager):
    """
    Enhanced collision manager that places components based on their electrical connections
    and supports component rotation for optimal pin alignment.
    """

    def __init__(self, sheet_size: Tuple[float, float] = (297.0, 210.0)):
        """
        Initialize the connection-aware collision manager.

        Args:
            sheet_size: (width, height) in mm
        """
        super().__init__(sheet_size)
        self.connection_analyzer = ConnectionAnalyzer()
        self.placed_components = {}  # ref -> (x, y, rotation)
        self.component_rotations = {}  # ref -> rotation angle (0, 90, 180, 270)

        # Parameters for placement
        self.search_radius_increment = 10.0  # mm
        self.max_search_radius = 100.0  # mm
        self.angular_steps = 8  # Number of angles to try in spiral search

    def analyze_connections(self, circuit) -> None:
        """
        Analyze the circuit to build connection information.

        Args:
            circuit: Circuit object to analyze
        """
        self.connection_analyzer.analyze_circuit(circuit)
        logger.info(
            f"Analyzed {len(self.connection_analyzer.connection_matrix)} connections"
        )

    def place_component_connection_aware(
        self, comp_ref: str, symbol_width: float, symbol_height: float
    ) -> Tuple[float, float, int]:
        """
        Place a component considering its connections to already placed components.
        Also determines optimal rotation.

        Args:
            comp_ref: Component reference
            symbol_width: Component width
            symbol_height: Component height

        Returns:
            (x, y, rotation) where rotation is in degrees (0, 90, 180, 270)
        """
        # Get connected components that are already placed
        placed_connections = []
        for (comp1, comp2), count in self.connection_analyzer.connection_matrix.items():
            if comp1 == comp_ref and comp2 in self.placed_components:
                placed_connections.append((comp2, count))
            elif comp2 == comp_ref and comp1 in self.placed_components:
                placed_connections.append((comp1, count))

        if placed_connections:
            # Calculate ideal position and rotation
            ideal_x, ideal_y, ideal_rotation = (
                self._calculate_ideal_position_and_rotation(
                    comp_ref, placed_connections, symbol_width, symbol_height
                )
            )

            # Try different rotations to find best fit
            best_position = None
            best_rotation = ideal_rotation

            for rotation in [ideal_rotation, 0, 90, 180, 270]:
                # Swap dimensions if rotated 90 or 270 degrees
                if rotation in [90, 270]:
                    test_width, test_height = symbol_height, symbol_width
                else:
                    test_width, test_height = symbol_width, symbol_height

                # Find nearest valid position for this rotation
                position = self._find_nearest_valid_position(
                    ideal_x, ideal_y, test_width, test_height
                )

                if position and (
                    not best_position
                    or self._is_better_position(
                        position,
                        best_position,
                        placed_connections,
                        rotation,
                        best_rotation,
                    )
                ):
                    best_position = position
                    best_rotation = rotation

            if best_position:
                x, y = best_position
                self.placed_components[comp_ref] = (x, y, best_rotation)
                self.component_rotations[comp_ref] = best_rotation
                logger.info(
                    f"Placed {comp_ref} at ({x:.1f}, {y:.1f}) with {best_rotation}° rotation "
                    f"(connected to {len(placed_connections)} components)"
                )
                return x, y, best_rotation

        # Fallback to sequential placement if no connections or no valid position found
        logger.info(
            f"Using sequential placement for {comp_ref} (no connections or valid position)"
        )
        x, y = self.place_symbol(symbol_width, symbol_height)
        rotation = 0
        self.placed_components[comp_ref] = (x, y, rotation)
        self.component_rotations[comp_ref] = rotation
        return x, y, rotation

    def _calculate_ideal_position_and_rotation(
        self,
        comp_ref: str,
        placed_connections: List[Tuple[str, int]],
        symbol_width: float,
        symbol_height: float,
    ) -> Tuple[float, float, int]:
        """
        Calculate ideal position and rotation based on connected components.

        Returns:
            (ideal_x, ideal_y, ideal_rotation)
        """
        # Calculate weighted center of connected components
        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0

        # Also track connection directions for rotation
        connection_vectors = []

        for connected_ref, connection_count in placed_connections:
            pos_x, pos_y, _ = self.placed_components[connected_ref]
            weight = float(connection_count)

            weighted_x += pos_x * weight
            weighted_y += pos_y * weight
            total_weight += weight

            # Store vector to this connection for rotation calculation
            connection_vectors.append((pos_x, pos_y, weight))

        if total_weight > 0:
            ideal_x = weighted_x / total_weight
            ideal_y = weighted_y / total_weight
        else:
            ideal_x = self.sheet_size[0] / 2
            ideal_y = self.sheet_size[1] / 2

        # Calculate ideal rotation based on connection directions
        ideal_rotation = self._calculate_ideal_rotation(
            ideal_x, ideal_y, connection_vectors
        )

        return ideal_x, ideal_y, ideal_rotation

    def _calculate_ideal_rotation(
        self,
        comp_x: float,
        comp_y: float,
        connection_vectors: List[Tuple[float, float, float]],
    ) -> int:
        """
        Calculate the ideal rotation to minimize connection angles.

        Returns:
            Rotation in degrees (0, 90, 180, or 270)
        """
        if not connection_vectors:
            return 0

        # Calculate the weighted average angle of connections
        total_weight = 0.0
        weighted_angle = 0.0

        for conn_x, conn_y, weight in connection_vectors:
            # Calculate angle from component to connection
            dx = conn_x - comp_x
            dy = conn_y - comp_y

            if dx != 0 or dy != 0:
                angle = math.atan2(dy, dx)
                weighted_angle += angle * weight
                total_weight += weight

        if total_weight > 0:
            avg_angle = weighted_angle / total_weight
            # Convert to degrees and snap to nearest 90-degree increment
            degrees = math.degrees(avg_angle)
            # Normalize to 0-360 range
            degrees = (degrees + 360) % 360
            # Snap to nearest 90 degrees
            rotation = int(round(degrees / 90) * 90) % 360
            return rotation

        return 0

    def _is_better_position(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float],
        connections: List[Tuple[str, int]],
        rot1: int,
        rot2: int,
    ) -> bool:
        """
        Determine if position 1 with rotation 1 is better than position 2 with rotation 2.

        Returns:
            True if pos1/rot1 is better than pos2/rot2
        """
        # Calculate total weighted distance for each position
        dist1 = 0.0
        dist2 = 0.0

        for connected_ref, weight in connections:
            conn_x, conn_y, _ = self.placed_components[connected_ref]

            # Manhattan distance for pos1
            dist1 += weight * (abs(pos1[0] - conn_x) + abs(pos1[1] - conn_y))
            # Manhattan distance for pos2
            dist2 += weight * (abs(pos2[0] - conn_x) + abs(pos2[1] - conn_y))

        # Prefer positions with shorter total connection distance
        # Add small penalty for non-zero rotations to prefer standard orientation when distances are similar
        rotation_penalty = 0.1  # Small penalty per 90 degrees of rotation
        dist1 += (rot1 / 90) * rotation_penalty
        dist2 += (rot2 / 90) * rotation_penalty

        return dist1 < dist2

    def get_placement_metrics(self) -> Dict[str, float]:
        """
        Calculate metrics for the current placement including rotation statistics.
        """
        metrics = super().get_placement_metrics()

        # Add rotation statistics
        rotation_counts = {0: 0, 90: 0, 180: 0, 270: 0}
        for rotation in self.component_rotations.values():
            rotation_counts[rotation] = rotation_counts.get(rotation, 0) + 1

        metrics["rotated_components"] = sum(
            1 for r in self.component_rotations.values() if r != 0
        )
        metrics["rotation_distribution"] = rotation_counts

        return metrics
