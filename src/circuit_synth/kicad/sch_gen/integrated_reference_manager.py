"""
Integrated Reference Manager - Self-contained reference generation system.

This module provides reference generation without external dependencies.
"""

import logging
import re
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class IntegratedReferenceManager:
    """
    Self-contained reference manager for schematic generation workflow.
    """

    def __init__(self):
        # Track used references
        self.used_references: Set[str] = set()
        self.reference_counters: Dict[str, int] = {}

        # Mapping from old component types to KiCad library IDs
        self.type_to_lib_id = {
            # Basic components
            "resistor": "Device:R",
            "capacitor": "Device:C",
            "inductor": "Device:L",
            "diode": "Device:D",
            "led": "Device:LED",
            "transistor": "Device:Q",
            "mosfet": "Device:Q",
            "bjt": "Device:Q",
            # Connectors
            "connector": "Connector:Conn",
            "testpoint": "Connector:TestPoint",
            "jumper": "Connector:Jumper",
            # ICs
            "ic": "Device:U",
            "opamp": "Device:U",
            "regulator": "Device:U",
            "microcontroller": "Device:U",
            # Power
            "battery": "Device:Battery",
            "voltage_source": "Device:V",
            "current_source": "Device:I",
            # Mechanical
            "mounting_hole": "Mechanical:MountingHole",
            "fiducial": "Mechanical:Fiducial",
            # Default
            "unknown": "Device:U",
        }

    def get_reference_for_component(self, component) -> str:
        """
        Generate a reference for a component using the new API.

        Args:
            component: Component object from the current system

        Returns:
            Reference designator (e.g., "R1", "C2", "U3")
        """
        # Get the component type from various possible attributes
        comp_type = None
        if hasattr(component, "type"):
            comp_type = component.type.lower()
        elif hasattr(component, "component_type"):
            comp_type = component.component_type.lower()
        elif hasattr(component, "symbol_id"):
            # Try to extract type from symbol_id (e.g., "Device:R" -> "resistor")
            symbol_id = component.symbol_id
            if ":R" in symbol_id or symbol_id.endswith(":R"):
                comp_type = "resistor"
            elif ":C" in symbol_id or symbol_id.endswith(":C"):
                comp_type = "capacitor"
            elif ":L" in symbol_id or symbol_id.endswith(":L"):
                comp_type = "inductor"
            elif ":D" in symbol_id or symbol_id.endswith(":D"):
                comp_type = "diode"
            elif ":Q" in symbol_id or symbol_id.endswith(":Q"):
                comp_type = "transistor"
            elif ":U" in symbol_id or symbol_id.endswith(":U"):
                comp_type = "ic"
            else:
                comp_type = "unknown"
        else:
            comp_type = "unknown"

        # Map to library ID
        lib_id = self.type_to_lib_id.get(comp_type, "Device:U")

        # CRITICAL FIX: If component has a reference, ALWAYS use it
        # Don't check availability - that causes conflicts in hierarchical designs
        if hasattr(component, "reference") and component.reference:
            # Ensure it's tracked in the reference manager
            if component.reference not in self.used_references:
                self.used_references.add(component.reference)
            return component.reference

        # Only generate new reference if component has NO reference
        reference = self._generate_reference(lib_id)

        logger.debug(
            f"Generated reference '{reference}' for component type '{comp_type}' (lib_id: {lib_id})"
        )

        return reference

    def _generate_reference(self, lib_id: str) -> str:
        """Generate a new reference for a given library ID."""
        # Extract reference prefix from lib_id
        if ":" in lib_id:
            symbol_name = lib_id.split(":", 1)[1]
        else:
            symbol_name = lib_id

        # Map symbol names to reference prefixes
        prefix_map = {
            "R": "R",
            "C": "C",
            "L": "L",
            "D": "D",
            "LED": "D",
            "Q": "Q",
            "U": "U",
            "J": "J",
            "Conn": "J",
            "TestPoint": "TP",
            "Battery": "BT",
            "V": "V",
            "I": "I",
            "MountingHole": "H",
            "Fiducial": "FID",
        }

        prefix = prefix_map.get(symbol_name, "U")

        # Get next counter for this prefix
        if prefix not in self.reference_counters:
            self.reference_counters[prefix] = 0

        # Find next available reference
        while True:
            self.reference_counters[prefix] += 1
            ref = f"{prefix}{self.reference_counters[prefix]}"
            if ref not in self.used_references:
                self.used_references.add(ref)
                return ref

    def get_reference_for_symbol(self, symbol) -> str:
        """
        Generate a reference for a SchematicSymbol using the new API.

        Args:
            symbol: SchematicSymbol object from the new API

        Returns:
            Reference designator (e.g., "R1", "C2", "U3")
        """
        # Log current state before assignment
        logger.debug(f"    Reference manager state before assignment:")
        logger.debug(f"      Used references: {sorted(self.used_references)}")
        logger.debug(f"      Counters: {dict(self.reference_counters)}")

        # CRITICAL FIX: If symbol has a reference, ALWAYS use it
        # Don't check availability - that causes conflicts in hierarchical designs
        if symbol.reference:
            # Ensure it's tracked in the reference manager
            if symbol.reference not in self.used_references:
                self.used_references.add(symbol.reference)
            logger.debug(f"      Using pre-assigned reference: {symbol.reference}")
            return symbol.reference

        # Only generate new reference if component has NO reference
        reference = self._generate_reference(symbol.lib_id)

        logger.debug(f"      Generated new reference: {reference} for {symbol.lib_id}")

        return reference

    def reset(self):
        """Reset the reference manager for a new schematic."""
        self.used_references.clear()
        self.reference_counters.clear()

    def enable_reassignment_mode(self):
        """
        Enable reference reassignment mode.
        This forces all references to be reassigned based on processing order.
        """
        self.reassignment_mode = True
        # Reset the reference manager to start from 1
        self.reset()

    def should_reassign(self, reference: str) -> bool:
        """
        Check if a reference should be reassigned.
        In reassignment mode, all references are reassigned.
        """
        return hasattr(self, "reassignment_mode") and self.reassignment_mode

    def get_next_reference_for_type(self, lib_id: str) -> str:
        """
        Get the next available reference for a given library ID.
        This bypasses the normal reference checking and forces a new assignment.
        """
        # Generate a new reference
        return self._generate_reference(lib_id)


# Example integration into SchematicWriter
def integrate_into_schematic_writer_example():
    """
    Shows how to modify SchematicWriter to use the integrated reference manager.
    """
    # In schematic_writer.py, add this to __init__:
    # self.integrated_ref_manager = IntegratedReferenceManager()

    # In _add_symbol_instances method, replace:
    # OLD:
    # ref = comp.reference if hasattr(comp, 'reference') else f"U{comp_idx + 1}"

    # NEW:
    # ref = self.integrated_ref_manager.get_reference_for_component(comp)

    example_code = '''
    def _add_symbol_instances(self, schematic: list):
        """Modified to use integrated reference manager."""
        # Initialize integrated reference manager if not already done
        if not hasattr(self, 'integrated_ref_manager'):
            self.integrated_ref_manager = IntegratedReferenceManager()
        
        for comp_idx, comp in enumerate(self.circuit.components):
            # Use new reference generation
            ref = self.integrated_ref_manager.get_reference_for_component(comp)
            
            # Rest of the method remains the same...
            symbol_instance = [
                Symbol("symbol"),
                [Symbol("lib_id"), comp.symbol_id],
                [Symbol("at"), comp.x, comp.y, comp.rotation],
                [Symbol("unit"), 1]
            ]
            # ... continue with existing logic
    '''
    return example_code


# Standalone function for testing
def test_integrated_reference_generation():
    """Test the integrated reference manager."""
    manager = IntegratedReferenceManager()

    # Mock component objects
    class MockComponent:
        def __init__(self, comp_type, symbol_id=None):
            self.type = comp_type
            self.symbol_id = symbol_id or f"Device:{comp_type[0].upper()}"

    # Test various component types
    components = [
        MockComponent("resistor", "Device:R"),
        MockComponent("resistor", "Device:R"),
        MockComponent("capacitor", "Device:C"),
        MockComponent("inductor", "Device:L"),
        MockComponent("transistor", "Device:Q"),
        MockComponent("ic", "Device:U"),
        MockComponent("connector", "Connector:Conn_01x04"),
    ]

    print("Testing integrated reference generation:")
    for comp in components:
        ref = manager.get_reference_for_component(comp)
        print(f"  {comp.type} ({comp.symbol_id}) -> {ref}")


if __name__ == "__main__":
    test_integrated_reference_generation()
