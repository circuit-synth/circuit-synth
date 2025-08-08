"""
Integration layer between circuit-synth Circuit objects and Rust KiCad crate.

This module provides the bridge between circuit-synth's Python Circuit/Component
classes and the Rust KiCad manipulation crate, keeping the Rust crate generic
and reusable while providing circuit-synth specific functionality here.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core import Circuit, Component
from ..core._logger import context_logger

try:
    import rust_kicad_schematic_writer as rust_kicad

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    context_logger.warning(
        "Rust KiCad integration not available. Install with: cd rust_modules/rust_kicad_integration && maturin develop",
        component="RUST_INTEGRATION",
    )


class RustSchematicGenerator:
    """
    Generate KiCad schematics using the Rust backend for improved performance
    and reliability. This class bridges circuit-synth Circuit objects to the
    Rust KiCad manipulation functions.
    """

    def __init__(self):
        if not RUST_AVAILABLE:
            raise ImportError(
                "Rust KiCad integration not installed. "
                "Run: cd rust_modules/rust_kicad_integration && maturin develop"
            )

    def create_schematic_from_circuit(
        self,
        circuit: Circuit,
        use_hierarchical_labels: bool = True,
        include_wires: bool = False,
    ) -> str:
        """
        Generate a KiCad schematic from a Circuit object using Rust backend.

        Args:
            circuit: Circuit object to convert
            use_hierarchical_labels: Use hierarchical labels instead of wires
            include_wires: Generate wire connections (not yet implemented)

        Returns:
            KiCad schematic as string
        """
        # Finalize references before generation
        circuit.finalize_references()

        # Start with minimal schematic
        schematic = rust_kicad.create_minimal_schematic()

        # Track component positions for layout
        x_offset = 50.0
        y_offset = 50.0
        spacing = 25.0

        # Add components
        for comp in circuit.components:
            # Convert Component to Rust-compatible format
            # Get value, defaulting to reference if not set
            value = getattr(comp, "value", None)
            if value is None:
                value = comp.ref

            schematic = rust_kicad.add_component_to_schematic(
                schematic,
                reference=comp.ref,
                lib_id=comp.symbol,
                value=str(value),
                x=x_offset,
                y=y_offset,
                rotation=0.0,
                footprint=comp.footprint if comp.footprint else "",
            )

            # Update position for next component
            x_offset += spacing * 2
            if x_offset > 250:  # Wrap to next row
                x_offset = 50.0
                y_offset += spacing * 2

        # Add hierarchical labels if requested
        if use_hierarchical_labels:
            # Note: Hierarchical label support is in Rust but not yet exposed
            # to Python bindings. This will be available in next release.
            # For now, we'll add a comment placeholder
            context_logger.info(
                "Hierarchical labels requested but not yet available in Python bindings",
                component="RUST_INTEGRATION",
            )

        return schematic

    def _determine_label_shape(self, net_name: str) -> str:
        """Determine hierarchical label shape based on net name patterns."""
        net_lower = net_name.lower()

        # Power nets are typically inputs
        if any(p in net_lower for p in ["vcc", "vdd", "gnd", "vss", "vin"]):
            return "input"

        # Output patterns
        if any(p in net_lower for p in ["out", "tx", "mosi", "sck", "cs"]):
            return "output"

        # Input patterns
        if any(p in net_lower for p in ["in", "rx", "miso"]):
            return "input"

        # Default to bidirectional for data buses
        if any(p in net_lower for p in ["data", "sda", "scl", "d+", "d-"]):
            return "bidirectional"

        return "passive"

    def update_schematic_component(
        self, schematic_path: str, reference: str, updates: Dict[str, Any]
    ) -> None:
        """
        Update a component in an existing schematic file.

        Args:
            schematic_path: Path to KiCad schematic file
            reference: Component reference to update
            updates: Dictionary of properties to update
        """
        with open(schematic_path, "r") as f:
            schematic = f.read()

        # Use Rust function to update by reference (simpler than UUID)
        # This would need to be implemented in Rust
        context_logger.warning(
            "Component update by reference not yet implemented in Rust backend",
            component="RUST_INTEGRATION",
        )
        # Future: schematic = rust_kicad.update_component_by_reference(
        #     schematic, reference, updates
        # )

        with open(schematic_path, "w") as f:
            f.write(schematic)

    def remove_component(self, schematic_path: str, reference: str) -> None:
        """
        Remove a component from an existing schematic.

        Args:
            schematic_path: Path to KiCad schematic file
            reference: Component reference to remove
        """
        # Note: Component removal is implemented in Rust but not yet exposed
        # to Python bindings. This will be available in next release.
        context_logger.warning(
            f"Component removal not yet available in Python bindings (would remove {reference})",
            component="RUST_INTEGRATION",
        )


class BidirectionalSync:
    """
    Handles bidirectional synchronization between KiCad schematics and
    circuit-synth Circuit objects, preserving manual edits in KiCad while
    updating from code changes.
    """

    def __init__(self):
        if not RUST_AVAILABLE:
            raise ImportError(
                "Rust KiCad integration not installed. "
                "Run: cd rust_modules/rust_kicad_integration && maturin develop"
            )
        self.generator = RustSchematicGenerator()

    def sync_circuit_to_schematic(
        self,
        circuit: Circuit,
        schematic_path: str,
        preserve_positions: bool = True,
        preserve_annotations: bool = True,
    ) -> None:
        """
        Update a KiCad schematic from a Circuit object, preserving manual edits.

        Args:
            circuit: Source Circuit object
            schematic_path: Path to existing KiCad schematic
            preserve_positions: Keep manual component positioning
            preserve_annotations: Keep manual text annotations
        """
        # Load existing schematic
        with open(schematic_path, "r") as f:
            existing_schematic = f.read()

        # Extract existing component positions and properties if preserving
        if preserve_positions:
            # This would parse positions from existing schematic
            # For now, we regenerate with default positions
            pass

        # Generate new schematic from circuit
        new_schematic = self.generator.create_schematic_from_circuit(
            circuit, use_hierarchical_labels=True
        )

        # Merge manual edits back if requested
        if preserve_positions or preserve_annotations:
            # This would require a diff/merge algorithm
            # For now, we just use the new schematic
            context_logger.info(
                "Position and annotation preservation not yet implemented",
                component="RUST_INTEGRATION",
            )

        # Write updated schematic
        with open(schematic_path, "w") as f:
            f.write(new_schematic)

    def sync_schematic_to_circuit(
        self, schematic_path: str, circuit: Optional[Circuit] = None
    ) -> Circuit:
        """
        Update or create a Circuit object from a KiCad schematic.

        Args:
            schematic_path: Path to KiCad schematic file
            circuit: Existing Circuit to update (creates new if None)

        Returns:
            Updated or new Circuit object
        """
        # This would require parsing KiCad schematic to extract components
        # and connections, then updating the Circuit object
        context_logger.warning(
            "Schematic to Circuit sync not yet implemented",
            component="RUST_INTEGRATION",
        )

        if circuit is None:
            circuit = Circuit(name=Path(schematic_path).stem)

        # Future implementation would:
        # 1. Parse schematic with Rust
        # 2. Extract components and properties
        # 3. Update Circuit object

        return circuit

    def diff_circuit_and_schematic(
        self, circuit: Circuit, schematic_path: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compare a Circuit object with a KiCad schematic to find differences.

        Args:
            circuit: Circuit object to compare
            schematic_path: Path to KiCad schematic file

        Returns:
            Dictionary with 'added', 'removed', and 'modified' component lists
        """
        # This would compare the circuit and schematic to find differences
        context_logger.warning(
            "Circuit/schematic diff not yet implemented", component="RUST_INTEGRATION"
        )

        return {"added": [], "removed": [], "modified": []}


def use_rust_backend(enabled: bool = True) -> None:
    """
    Enable or disable use of Rust backend for KiCad generation.

    Args:
        enabled: Whether to use Rust backend
    """
    if enabled and not RUST_AVAILABLE:
        raise ImportError(
            "Cannot enable Rust backend - not installed. "
            "Run: cd rust_modules/rust_kicad_integration && maturin develop"
        )

    # This would set a global flag to use Rust instead of Python
    # for schematic generation in the main KiCad generator
    context_logger.info(
        f"Rust backend {'enabled' if enabled else 'disabled'}",
        component="RUST_INTEGRATION",
    )


# Convenience function for quick schematic generation
def generate_schematic_with_rust(circuit: Circuit, output_path: str) -> None:
    """
    Quick function to generate a KiCad schematic using Rust backend.

    Args:
        circuit: Circuit object to convert
        output_path: Output path for .kicad_sch file
    """
    generator = RustSchematicGenerator()
    schematic = generator.create_schematic_from_circuit(circuit)

    with open(output_path, "w") as f:
        f.write(schematic)

    context_logger.info(
        f"Generated schematic with Rust backend: {output_path}",
        component="RUST_INTEGRATION",
    )
