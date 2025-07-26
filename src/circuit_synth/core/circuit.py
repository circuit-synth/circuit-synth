# FILE: src/circuit_synth/core/circuit.py

import re
from typing import List, Dict, Optional, Any
import json
import tempfile
import os
from pathlib import Path # Import Path

from .net import Net
from .exception import ValidationError, CircuitSynthError
from .reference_manager import ReferenceManager
from .json_encoder import CircuitSynthJSONEncoder
# Import the exporter function
from .netlist_exporter import NetlistExporter
from ._logger import context_logger


class Circuit:
    from .component import Component  # for type-hinting

    def __init__(self, name=None, description=None):
        self.name = name or "UnnamedCircuit"
        self.description = description
        self._components = {}
        self._nets = {}
        # self._unnamed_net_counter = 1 # Removed: Counter is now managed by ReferenceManager
        self._parent = None
        self._subcircuits = []
        self._component_list = []
        self._reference_manager = ReferenceManager()


    def validate_reference(self, ref: str) -> bool:
        """Check if reference is available in this circuit's scope"""
        return self._reference_manager.validate_reference(ref)

    def register_reference(self, ref: str) -> None:
        """Register a new reference in this circuit's scope"""
        self._reference_manager.register_reference(ref)

    def add_subcircuit(self, subcirc: "Circuit"):
        """Add a subcircuit and establish parent-child relationship"""
        subcirc._parent = self
        self._subcircuits.append(subcirc)
        # NEW: Link reference managers
        subcirc._reference_manager.set_parent(self._reference_manager)
        context_logger.debug(
            "Added subcircuit to parent",
            component="CIRCUIT",
            subcircuit_name=subcirc.name,
            parent_name=self.name
        )

    def add_component(self, comp: "Component"):
        """Register a Component with this Circuit."""
        user_ref = comp._user_reference
        
        # Handle components with no reference - generate a default prefix
        if not user_ref:
            # Generate a default prefix based on the component symbol
            symbol_parts = comp.symbol.split(":")
            if len(symbol_parts) >= 2:
                # Use the symbol name as prefix (e.g., "Device:R" -> "R")
                default_prefix = symbol_parts[1]
                # Clean up the prefix to be a valid reference
                default_prefix = re.sub(r'[^A-Za-z0-9_]', '', default_prefix)
                if default_prefix and default_prefix[0].isalpha():
                    user_ref = default_prefix
                else:
                    user_ref = "U"  # Generic fallback
            else:
                user_ref = "U"  # Generic fallback
            
            # Update the component's reference
            comp._user_reference = user_ref
            comp._is_prefix = True
        
        # Check if reference is final (has trailing digits)
        has_trailing_digits = bool(re.search(r"\d+$", user_ref))
        
        if has_trailing_digits:
            # For final references, validate through hierarchy
            if not self._reference_manager.validate_reference(user_ref):
                existing = self._components.get(user_ref)
                msg = (
                    f"Reference collision: final reference '{user_ref}' is already used in circuit hierarchy\n"
                    f"Existing component => {existing}\n"
                    f"New component => {comp}\n"
                    "Please specify a different final reference."
                )
                context_logger.error(msg, component="CIRCUIT")
                raise ValidationError(msg)

            # Register and store with final reference
            self._reference_manager.register_reference(user_ref)
            comp.ref = user_ref
            comp._is_prefix = False  # Mark as final reference
            self._components[user_ref] = comp
            self._component_list.append(comp)
            
            context_logger.debug(
                "Component with final reference registered",
                component="CIRCUIT",
                reference=user_ref,
                symbol=comp.symbol,
                circuit_name=self.name
            )
        else:
            # For prefix references, store with placeholder
            placeholder_key = f"(prefix){id(comp)}"
            context_logger.debug(
                "Component with prefix reference stored as placeholder",
                component="CIRCUIT",
                prefix_reference=user_ref,
                placeholder_key=placeholder_key,
                symbol=comp.symbol,
                circuit_name=self.name
            )
            comp.ref = user_ref
            comp._is_prefix = True  # Mark as prefix reference
            self._components[placeholder_key] = comp
            self._component_list.append(comp)

    def finalize_references(self):
        """Auto-assign references for any components that only had a prefix."""
        context_logger.debug("Starting reference finalization", component="CIRCUIT", circuit_name=self.name)

        newly_assigned = {}
        to_remove = []
        
        for key, comp in self._components.items():
            # Only process components with prefix references
            if key.startswith("(prefix)") and comp._is_prefix:
                prefix = comp._user_reference
                final_ref = self._reference_manager.generate_next_reference(prefix)
                comp.ref = final_ref
                comp._is_prefix = False  # Mark as final reference
                newly_assigned[final_ref] = comp
                to_remove.append(key)
                
                context_logger.debug(
                    "Assigned final reference for prefix",
                    component="CIRCUIT",
                    final_reference=final_ref,
                    prefix=prefix,
                    circuit_name=self.name
                )

        # Update component dictionaries
        for placeholder_key in to_remove:
            del self._components[placeholder_key]
        for final_key, comp in newly_assigned.items():
            self._components[final_key] = comp

        context_logger.debug(
            "Finished reference finalization",
            component="CIRCUIT",
            circuit_name=self.name,
            total_components=len(self._components)
        )

        # Recursively finalize subcircuits
        for sc in self._subcircuits:
            sc.finalize_references()


    def generate_text_netlist(self) -> str:
        """
        Generate a textual netlist for display or debugging.
        """
        exporter = NetlistExporter(self)
        return exporter.generate_text_netlist()

    def generate_full_netlist(self) -> str:
        """
        Print a hierarchical netlist showing:
          1) Each circuit + subcircuit (name, components, and optional description)
          2) A single combined net listing from all circuits
        """
        exporter = NetlistExporter(self)
        return exporter.generate_full_netlist()


    def add_net(self, net: Net):
        if not net.name:
            # Use the ReferenceManager to get a globally unique name
            net.name = self._reference_manager.generate_next_unnamed_net_name()
        if net.name not in self._nets:
            context_logger.debug(
                "Registering net in circuit",
                component="CIRCUIT",
                net_name=net.name,
                circuit_name=self.name
            )
            self._nets[net.name] = net

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a hierarchical dictionary representation of this circuit,
        including subcircuits, components (as a dictionary keyed by reference),
        and net connections.
        """
        exporter = NetlistExporter(self)
        return exporter.to_dict()

    def generate_json_netlist(self, filename: str) -> None:
        """
        Generate a JSON representation of this circuit and its hierarchy,
        then write it out to 'filename'.
        """
        exporter = NetlistExporter(self)
        return exporter.generate_json_netlist(filename)

    # --------------------------------------------------------------------------
    # UPDATED FLATTENED JSON LOGIC (SHOWING ALL NETS USED BY LOCAL COMPONENTS)
    # --------------------------------------------------------------------------
    def to_flattened_list(
        self,
        parent_name: str = None,
        flattened: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build or update a shared `flattened` list of circuit data dicts.
        """
        exporter = NetlistExporter(self)
        return exporter.to_flattened_list(parent_name, flattened)

    def generate_flattened_json_netlist(self, filename: str) -> None:
        """
        Produce a flattened JSON representation for this circuit + subcircuits.
        """
        exporter = NetlistExporter(self)
        return exporter.generate_flattened_json_netlist(filename)


    def generate_kicad_netlist(self, filename: str) -> None:
        """
        Generate a KiCad netlist (.net) file for this circuit and its hierarchy.
        """
        exporter = NetlistExporter(self)
        return exporter.generate_kicad_netlist(filename)

    def generate_kicad_project(self, path: str, project_name: Optional[str] = None,
                             force_create: bool = False, preserve_user_components: bool = True) -> None:
        """
        Generate or update a KiCad project (schematic files) from this circuit.
        """
        exporter = NetlistExporter(self)
        return exporter.generate_kicad_project(path, project_name, force_create, preserve_user_components)
    
    def simulate(self):
        """
        Create a simulator instance for this circuit.
        
        This method provides access to circuit simulation capabilities using
        PySpice as the backend. The returned simulator object can be used to
        run various analyses such as DC operating point, transient, and AC.
        
        Returns:
            CircuitSimulator: Simulator object for running analyses
            
        Example:
            >>> circuit = voltage_divider()
            >>> sim = circuit.simulate()
            >>> result = sim.operating_point()
            >>> print(f"Output voltage: {result.get_voltage('VOUT'):.3f} V")
            
        Raises:
            ImportError: If simulation dependencies are not installed
            CircuitSynthError: If circuit cannot be converted for simulation
        """
        try:
            from ..simulation import CircuitSimulator
        except ImportError as e:
            context_logger.error("Simulation module not available", component="CIRCUIT", error=str(e))
            raise ImportError(
                "Circuit simulation requires PySpice and its dependencies. "
                "Install with: pip install circuit-synth[simulation]"
            ) from e
            
        context_logger.info("Creating simulator for circuit", component="CIRCUIT", circuit_name=self.name)
        return CircuitSimulator(self)
    
    @property
    def components(self):
        """
        Return a list of all components in this circuit.
        
        This property provides access to components as a list, which is expected
        by many parts of the codebase that iterate over circuit.components.
        
        Returns:
            List[Component]: List of all components in this circuit
        """
        return list(self._components.values())
    
    @property
    def nets(self):
        """
        Return a dictionary of all nets in this circuit.
        
        Returns:
            Dict[str, Net]: Dictionary of nets keyed by net name
        """
        return self._nets
