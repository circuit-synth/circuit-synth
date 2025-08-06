"""
KiCad schematic differential update module.

This module compares Python circuit definition with existing KiCad schematic
and applies only the necessary changes while preserving manual edits.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from ..core._logger import context_logger


@dataclass
class ComponentState:
    """Minimal component state for comparison."""
    ref: str
    symbol: str
    nets: Dict[str, str]  # pin -> net mapping


@dataclass
class CircuitState:
    """Minimal circuit state for comparison."""
    components: Dict[str, ComponentState]  # ref -> component
    nets: Dict[str, Set[Tuple[str, str]]]  # net -> set of (ref, pin)


class SchematicDiffer:
    """Compares and updates KiCad schematics based on Python circuit changes."""
    
    @staticmethod
    def extract_circuit_from_json(json_path: Path) -> CircuitState:
        """
        Extract minimal circuit state from circuit-synth JSON.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            CircuitState with components and net connections
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            components = {}
            nets = {}
            
            # Extract components
            for ref, comp_data in data.get("components", {}).items():
                # Build net mapping from the component's perspective
                comp_nets = {}
                
                # Find which nets this component connects to
                for net_name, connections in data.get("nets", {}).items():
                    for conn in connections:
                        if conn["component"] == ref:
                            pin = conn["pin"]["number"]
                            comp_nets[pin] = net_name
                
                components[ref] = ComponentState(
                    ref=ref,
                    symbol=comp_data.get("symbol", ""),
                    nets=comp_nets
                )
            
            # Extract nets
            for net_name, connections in data.get("nets", {}).items():
                net_connections = set()
                for conn in connections:
                    ref = conn["component"]
                    pin = conn["pin"]["number"]
                    net_connections.add((ref, pin))
                nets[net_name] = net_connections
            
            context_logger.info(
                f"Extracted circuit from JSON",
                component="DIFF",
                components=len(components),
                nets=len(nets)
            )
            
            return CircuitState(components=components, nets=nets)
            
        except Exception as e:
            context_logger.error(f"Failed to extract circuit from JSON: {e}", component="DIFF")
            return CircuitState(components={}, nets={})
    
    @staticmethod
    def extract_circuit_from_kicad(sch_path: Path) -> CircuitState:
        """
        Extract minimal circuit state from KiCad schematic.
        
        This is simplified - a full implementation would properly parse
        the S-expression format and extract all connections.
        
        Args:
            sch_path: Path to .kicad_sch file
            
        Returns:
            CircuitState with components and net connections
        """
        try:
            with open(sch_path, 'r') as f:
                content = f.read()
            
            components = {}
            
            # Extract components from symbol blocks
            # Pattern to match symbol blocks with reference
            symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\).*?\(property\s+"Reference"\s+"([^"]+)"'
            
            for match in re.finditer(symbol_pattern, content, re.DOTALL):
                lib_id = match.group(1)
                ref = match.group(2)
                
                components[ref] = ComponentState(
                    ref=ref,
                    symbol=lib_id,
                    nets={}  # Would be extracted from wire analysis
                )
            
            # Note: Full implementation would extract wire connections
            # and build the complete net mapping
            
            context_logger.info(
                f"Extracted {len(components)} components from KiCad",
                component="DIFF",
                refs=list(components.keys())
            )
            
            return CircuitState(components=components, nets={})
            
        except Exception as e:
            context_logger.error(f"Failed to extract circuit from KiCad: {e}", component="DIFF")
            return CircuitState(components={}, nets={})
    
    @staticmethod
    def compare_circuits(python_circuit: CircuitState, kicad_circuit: CircuitState) -> Dict[str, Any]:
        """
        Compare two circuit states and identify differences.
        
        Args:
            python_circuit: Circuit state from Python/JSON
            kicad_circuit: Circuit state from KiCad schematic
            
        Returns:
            Dictionary describing the differences:
            {
                "components_to_add": [...],
                "components_to_remove": [...],
                "components_to_update": [...],
                "nets_to_add": [...],
                "nets_to_remove": [...],
                "identical": bool
            }
        """
        diff = {
            "components_to_add": [],
            "components_to_remove": [],
            "components_to_update": [],
            "nets_to_add": [],
            "nets_to_remove": [],
            "identical": False
        }
        
        python_refs = set(python_circuit.components.keys())
        kicad_refs = set(kicad_circuit.components.keys())
        
        # Components to add (in Python but not in KiCad)
        for ref in python_refs - kicad_refs:
            diff["components_to_add"].append(python_circuit.components[ref])
        
        # Components to remove (in KiCad but not in Python)
        for ref in kicad_refs - python_refs:
            diff["components_to_remove"].append(ref)
        
        # Components to potentially update (in both)
        for ref in python_refs & kicad_refs:
            python_comp = python_circuit.components[ref]
            kicad_comp = kicad_circuit.components[ref]
            
            # Check if symbol or connections changed
            if (python_comp.symbol != kicad_comp.symbol or 
                python_comp.nets != kicad_comp.nets):
                diff["components_to_update"].append({
                    "ref": ref,
                    "old": kicad_comp,
                    "new": python_comp
                })
        
        # Check if circuits are identical
        if (not diff["components_to_add"] and 
            not diff["components_to_remove"] and 
            not diff["components_to_update"]):
            diff["identical"] = True
        
        context_logger.info(
            f"Circuit comparison complete",
            component="DIFF",
            to_add=len(diff["components_to_add"]),
            to_remove=len(diff["components_to_remove"]),
            to_update=len(diff["components_to_update"]),
            identical=diff["identical"]
        )
        
        return diff
    
    @staticmethod
    def should_update_schematic(json_path: Path, sch_path: Path) -> bool:
        """
        Determine if the KiCad schematic needs updating based on circuit changes.
        
        Args:
            json_path: Path to circuit-synth JSON
            sch_path: Path to KiCad schematic
            
        Returns:
            True if schematic needs updating, False if circuits are identical
        """
        if not sch_path.exists():
            return True  # No schematic exists, must create
        
        python_circuit = SchematicDiffer.extract_circuit_from_json(json_path)
        kicad_circuit = SchematicDiffer.extract_circuit_from_kicad(sch_path)
        
        diff = SchematicDiffer.compare_circuits(python_circuit, kicad_circuit)
        
        return not diff["identical"]