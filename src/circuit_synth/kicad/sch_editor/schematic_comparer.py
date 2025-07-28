"""
KiCad schematic comparer module.

This module compares a parsed KiCad schematic with a Circuit Synth circuit model
to identify components and connections that need to be added, modified, or removed.
It focuses on logical differences rather than visual layout changes.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set

from circuit_synth.core.circuit import Circuit
from circuit_synth.core.component import Component

from .schematic_reader import SchematicNet, SchematicSheet, SchematicSymbol

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of changes that can be made to a schematic."""

    ADD = auto()
    MODIFY = auto()
    REMOVE = auto()


@dataclass
class ComponentChange:
    """Represents a change to a component."""

    type: ChangeType
    reference: str
    original: Optional[SchematicSymbol] = None
    modified: Optional[Component] = None
    changes: Dict[str, Any] = field(default_factory=dict)  # Property changes


@dataclass
class NetChange:
    """Represents a change to a net."""

    type: ChangeType
    name: str
    original: Optional[SchematicNet] = None
    modified: Optional[Any] = None  # Net from Circuit model
    added_nodes: List[tuple] = field(default_factory=list)
    removed_nodes: List[tuple] = field(default_factory=list)


@dataclass
class ChangeSet:
    """Collection of all changes between schematic and circuit.

    Attributes:
        added_components: List of new components to be added
        modified_components: List of tuples containing (Component, changed properties dict)
        removed_components: List of components to be removed
        added_nets: List of new nets to be added
        modified_nets: List of tuples containing (Net, changed properties dict)
        removed_nets: List of nets to be removed
        sheet_changes: Dictionary of sheet changes by name
    """

    added_components: List[Component] = field(default_factory=list)
    modified_components: List[tuple[Component, Dict[str, Any]]] = field(
        default_factory=list
    )
    removed_components: List[Component] = field(default_factory=list)
    added_nets: List[Any] = field(default_factory=list)  # Circuit Net type
    modified_nets: List[tuple[Any, Dict[str, Any]]] = field(default_factory=list)
    removed_nets: List[Any] = field(default_factory=list)
    sheet_changes: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class SchematicComparer:
    """Compares KiCad schematics with Circuit Synth circuits."""

    def __init__(
        self,
        original_symbols: Dict[str, SchematicSymbol],
        original_nets: Dict[str, SchematicNet],
        original_sheets: Dict[str, SchematicSheet],
    ):
        """Initialize with original schematic data.

        Args:
            original_symbols: Dictionary of components from schematic
            original_nets: Dictionary of nets from schematic
            original_sheets: Dictionary of hierarchical sheets
        """
        self.original_symbols = original_symbols
        self.original_nets = original_nets
        self.original_sheets = original_sheets

    def compare_with_circuit(self, circuit: Circuit) -> ChangeSet:
        """Compare original schematic with a Circuit Synth circuit.

        Args:
            circuit: Circuit model to compare against

        Returns:
            ChangeSet containing all differences
        """
        changes = ChangeSet()

        # Compare components
        self._compare_components(circuit, changes)

        # Compare nets
        self._compare_nets(circuit, changes)

        # Compare sheets (if circuit has subcircuits)
        self._compare_sheets(circuit, changes)

        return changes

    def _compare_components(self, circuit: Circuit, changes: ChangeSet) -> None:
        """Compare components between schematic and circuit.

        Following the Schematic Modification Pattern:
        1. Only identify what has actually changed
        2. Preserve positions of existing components
        3. Track property changes for in-place updates
        4. Identify new components for edge placement
        """
        processed_refs = set()

        # Check each component in the circuit
        for comp in circuit._components.values():
            ref = comp.ref
            processed_refs.add(ref)

            if ref in self.original_symbols:
                # Component exists - check for modifications
                orig_symbol = self.original_symbols[ref]
                property_changes = self._compare_component_properties(orig_symbol, comp)

                if property_changes:
                    # Preserve original position
                    comp.position = orig_symbol.position
                    changes.modified_components.append((comp, property_changes))
            else:
                # New component - will be placed at edge
                changes.added_components.append(comp)

        # Find removed components
        for ref, symbol in self.original_symbols.items():
            if ref not in processed_refs:
                # Convert SchematicSymbol to Component for consistency
                removed_comp = Component(ref=ref, value=symbol.value)
                removed_comp.position = symbol.position
                changes.removed_components.append(removed_comp)

    def _compare_component_properties(
        self, original: SchematicSymbol, modified: Component
    ) -> Dict[str, Any]:
        """Compare properties between original and modified components."""
        changes = {}

        # Compare basic properties
        if original.value != modified.value:
            changes["value"] = modified.value

        # Compare other properties from Circuit model
        for key, value in modified.properties.items():
            if key not in original.properties or original.properties[key] != value:
                changes[key] = value

        return changes

    def _compare_nets(self, circuit: Circuit, changes: ChangeSet) -> None:
        """Compare nets between schematic and circuit.

        Preserves net hierarchy and tracks changes while maintaining existing structure.
        """
        processed_nets = set()

        # Check each net in the circuit
        for net_name, net in circuit._nets.items():
            processed_nets.add(net_name)

            if net_name in self.original_nets:
                # Net exists - check for modifications
                orig_net = self.original_nets[net_name]
                added_nodes, removed_nodes = self._compare_net_nodes(orig_net, net)

                if added_nodes or removed_nodes:
                    changes.modified_nets.append(
                        (
                            net,
                            {
                                "added_nodes": added_nodes,
                                "removed_nodes": removed_nodes,
                                "original_path": orig_net.path,  # Preserve hierarchy
                            },
                        )
                    )
            else:
                # New net
                changes.added_nets.append(net)

        # Find removed nets
        for net_name, net in self.original_nets.items():
            if net_name not in processed_nets:
                changes.removed_nets.append(net)

    def _compare_net_nodes(self, original: SchematicNet, modified: Any) -> tuple:
        """Compare nodes between original and modified nets."""
        # Convert original nodes to set for comparison
        original_nodes = set((ref, pin) for ref, pin in original.nodes)

        # Get modified nodes from Circuit net
        modified_nodes = set()
        for pin in modified._pins:
            modified_nodes.add((pin._component.ref, pin._component_pin_id))

        # Find differences
        added = list(modified_nodes - original_nodes)
        removed = list(original_nodes - modified_nodes)

        return added, removed

    def _compare_sheets(self, circuit: Circuit, changes: ChangeSet) -> None:
        """Compare hierarchical sheets between schematic and circuit.

        Creates proper SchematicSheet objects for new sheets and handles parent paths.
        """
        # Track which original sheets have been processed
        processed_sheets = set()

        # Check each subcircuit in the circuit
        for subcircuit in circuit._subcircuits:
            name = subcircuit.name
            processed_sheets.add(name)

            if name in self.original_sheets:
                # Sheet exists - might need to update pins
                sheet = self.original_sheets[name]
                changes.sheet_changes[name] = {
                    "type": ChangeType.MODIFY,
                    "original": sheet,
                    "modified": sheet,  # Preserve original sheet properties
                }
            else:
                # Create new SchematicSheet with proper parent path
                new_sheet = SchematicSheet(
                    name=name,
                    path=f"{name}.kicad_sch",
                    parent_path="/",  # Default to root sheet
                    uuid=None,  # Will be generated when added
                )

                # If subcircuit has parent info, update parent_path
                if hasattr(subcircuit, "parent") and subcircuit.parent:
                    parent_name = subcircuit.parent.name
                    new_sheet.parent_path = f"/{parent_name}"

                changes.sheet_changes[name] = {
                    "type": ChangeType.ADD,
                    "modified": new_sheet,
                }

        # Find removed sheets
        for name, sheet in self.original_sheets.items():
            if name not in processed_sheets:
                changes.sheet_changes[name] = {
                    "type": ChangeType.REMOVE,
                    "original": sheet,
                }
