#!/usr/bin/env python3
"""
Rust KiCad Schematic Adapter

This module provides an adapter layer to use the Rust schematic generation
backend from Python. It converts Python circuit data structures to the format
expected by the Rust module and handles the generation process.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure detailed logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the Rust module
try:
    import rust_kicad_schematic_writer
    RUST_AVAILABLE = True
    logger.info("✅ Rust KiCad schematic writer module loaded successfully")
except ImportError as e:
    RUST_AVAILABLE = False
    logger.error(f"❌ Failed to import Rust module: {e}")
    raise


class RustSchematicAdapter:
    """Adapter to use Rust schematic generation from Python circuits."""
    
    def __init__(self, circuit):
        """
        Initialize the adapter with a Python circuit object.
        
        Args:
            circuit: A Circuit object from circuit_synth
        """
        self.circuit = circuit
        self.rust_writer = None
        logger.info(f"🚀 Initializing RustSchematicAdapter for circuit: {circuit.name}")
        
    def _convert_component_to_rust(self, component) -> Dict[str, Any]:
        """
        Convert a Python Component to Rust-compatible format.
        
        Args:
            component: Python Component object
            
        Returns:
            Dictionary with component data in Rust format
        """
        logger.debug(f"Converting component: {component.ref}")
        
        # Get symbol from component
        symbol = getattr(component, 'symbol', '')
        if hasattr(component, 'get_symbol'):
            symbol = component.get_symbol()
            
        # Get position
        position = {"x": 0.0, "y": 0.0}
        if hasattr(component, 'position'):
            if isinstance(component.position, dict):
                position = component.position
            elif hasattr(component.position, 'x') and hasattr(component.position, 'y'):
                position = {"x": component.position.x, "y": component.position.y}
                
        # Get rotation
        rotation = 0.0
        if hasattr(component, 'rotation'):
            rotation = float(component.rotation)
            
        # Convert pins if available
        pins = []
        if hasattr(component, 'pins'):
            for pin_name, pin_obj in component.pins.items():
                pin_data = {
                    "number": str(pin_name),
                    "name": str(pin_name),
                    "x": 0.0,
                    "y": 0.0,
                    "orientation": 0.0
                }
                # Try to get pin position if available
                if hasattr(pin_obj, 'position'):
                    if hasattr(pin_obj.position, 'x'):
                        pin_data["x"] = float(pin_obj.position.x)
                    if hasattr(pin_obj.position, 'y'):
                        pin_data["y"] = float(pin_obj.position.y)
                pins.append(pin_data)
        
        component_data = {
            "reference": component.ref,
            "lib_id": symbol,
            "symbol": symbol,  # Include both for compatibility
            "value": getattr(component, 'value', component.ref),
            "position": position,
            "rotation": rotation,
            "pins": pins
        }
        
        logger.debug(f"  Converted: ref={component.ref}, symbol={symbol}, position={position}")
        return component_data
        
    def _convert_net_to_rust(self, net) -> Dict[str, Any]:
        """
        Convert a Python Net to Rust-compatible format.
        
        Args:
            net: Python Net object
            
        Returns:
            Dictionary with net data in Rust format
        """
        logger.debug(f"Converting net: {net.name}")
        
        connections = []
        
        # Handle circuit_synth Net objects with pins attribute (frozenset of Pin objects)
        if hasattr(net, 'pins'):
            for pin in net.pins:
                # Pin object has num attribute for pin number
                # Parse component ref from string representation "Pin(~ of R1, net=VCC)"
                pin_str = str(pin)
                import re
                match = re.search(r'of ([A-Z]+\d*)', pin_str)
                if match:
                    comp_ref = match.group(1)
                    # Use pin.num for pin number
                    pin_id = str(pin.num) if hasattr(pin, 'num') else '1'
                    
                    connections.append({
                        "component_ref": comp_ref,
                        "pin_id": pin_id
                    })
                else:
                    logger.warning(f"Could not parse pin: {pin_str}")
        # Fallback for other net formats
        elif hasattr(net, 'get_connections'):
            for comp_ref, pin_id in net.get_connections():
                connections.append({
                    "component_ref": str(comp_ref),
                    "pin_id": str(pin_id)
                })
        elif hasattr(net, 'connections'):
            # Handle different net formats
            for conn in net.connections:
                if isinstance(conn, tuple) and len(conn) >= 2:
                    connections.append({
                        "component_ref": str(conn[0]),
                        "pin_id": str(conn[1])
                    })
                elif isinstance(conn, dict):
                    connections.append({
                        "component_ref": str(conn.get('component_ref', '')),
                        "pin_id": str(conn.get('pin_id', ''))
                    })
        
        net_data = {
            "name": net.name,
            "connected_pins": connections
        }
        
        logger.debug(f"  Converted net {net.name} with {len(connections)} connections")
        return net_data
        
    def _convert_subcircuit_to_rust(self, subcircuit) -> Dict[str, Any]:
        """
        Convert a subcircuit to Rust-compatible format.
        
        Args:
            subcircuit: Python subcircuit object
            
        Returns:
            Dictionary with subcircuit data in Rust format
        """
        logger.debug(f"Converting subcircuit: {getattr(subcircuit, 'name', 'unnamed')}")
        
        # Recursively convert subcircuit components and nets
        subcircuit_data = {
            "name": getattr(subcircuit, 'name', 'subcircuit'),
            "components": [],
            "nets": [],
            "subcircuits": []
        }
        
        # Convert components in subcircuit
        if hasattr(subcircuit, 'components'):
            for comp in subcircuit.components.values():
                subcircuit_data["components"].append(self._convert_component_to_rust(comp))
                
        # Convert nets in subcircuit
        if hasattr(subcircuit, 'nets'):
            for net in subcircuit.nets.values():
                subcircuit_data["nets"].append(self._convert_net_to_rust(net))
                
        # Convert nested subcircuits if any
        if hasattr(subcircuit, 'subcircuits'):
            for nested_sub in subcircuit.subcircuits:
                subcircuit_data["subcircuits"].append(self._convert_subcircuit_to_rust(nested_sub))
                
        logger.debug(f"  Converted subcircuit with {len(subcircuit_data['components'])} components, {len(subcircuit_data['nets'])} nets")
        return subcircuit_data
        
    def convert_to_rust_format(self) -> Dict[str, Any]:
        """
        Convert the entire Python circuit to Rust-compatible format.
        
        Returns:
            Dictionary with circuit data in Rust format
        """
        logger.info("🔄 Converting Python circuit to Rust format...")
        
        circuit_data = {
            "name": self.circuit.name,
            "components": [],
            "nets": [],
            "subcircuits": []
        }
        
        # Convert all components
        logger.info(f"  Converting {len(self.circuit.components)} components...")
        
        # Handle both list and dict formats
        if isinstance(self.circuit.components, dict):
            for comp_ref, component in self.circuit.components.items():
                try:
                    component_data = self._convert_component_to_rust(component)
                    circuit_data["components"].append(component_data)
                except Exception as e:
                    logger.error(f"  ❌ Failed to convert component {comp_ref}: {e}")
                    raise
        elif isinstance(self.circuit.components, list):
            for component in self.circuit.components:
                try:
                    component_data = self._convert_component_to_rust(component)
                    circuit_data["components"].append(component_data)
                except Exception as e:
                    logger.error(f"  ❌ Failed to convert component {component.ref}: {e}")
                    raise
        else:
            logger.error(f"  ❌ Unexpected components type: {type(self.circuit.components)}")
            raise TypeError(f"Expected dict or list for components, got {type(self.circuit.components)}")
                
        # Convert all nets
        logger.info(f"  Converting {len(self.circuit.nets)} nets...")
        for net_name, net in self.circuit.nets.items():
            try:
                net_data = self._convert_net_to_rust(net)
                circuit_data["nets"].append(net_data)
            except Exception as e:
                logger.error(f"  ❌ Failed to convert net {net_name}: {e}")
                raise
                
        # Convert subcircuits if present
        if hasattr(self.circuit, 'subcircuits') and self.circuit.subcircuits:
            logger.info(f"  Converting {len(self.circuit.subcircuits)} subcircuits...")
            for subcircuit in self.circuit.subcircuits:
                try:
                    subcircuit_data = self._convert_subcircuit_to_rust(subcircuit)
                    circuit_data["subcircuits"].append(subcircuit_data)
                except Exception as e:
                    logger.error(f"  ❌ Failed to convert subcircuit: {e}")
                    raise
                    
        logger.info(f"✅ Conversion complete: {len(circuit_data['components'])} components, {len(circuit_data['nets'])} nets, {len(circuit_data['subcircuits'])} subcircuits")
        
        # Log the structure for debugging
        logger.debug("Circuit data structure:")
        logger.debug(f"  Components: {[c['reference'] for c in circuit_data['components']]}")
        logger.debug(f"  Nets: {[n['name'] for n in circuit_data['nets']]}")
        if circuit_data['subcircuits']:
            logger.debug(f"  Subcircuits: {[s['name'] for s in circuit_data['subcircuits']]}")
            
        return circuit_data
        
    def generate_schematic(self, output_path: str, config: Optional[Dict] = None) -> None:
        """
        Generate a KiCad schematic using the Rust backend.
        
        Args:
            output_path: Path where the .kicad_sch file should be written
            config: Optional configuration dictionary
        """
        logger.info(f"🚀 Generating schematic using Rust backend to: {output_path}")
        
        # Convert circuit to Rust format
        circuit_data = self.convert_to_rust_format()
        
        # Default configuration
        if config is None:
            config = {
                "paper_size": "A4",
                "generator": "rust_kicad_schematic_writer",
                "title": self.circuit.name,
                "version": "1.0"
            }
            
        logger.info(f"  Using config: {config}")
        
        try:
            # Log the data being sent to Rust
            logger.debug("Sending to Rust module:")
            logger.debug(f"  Circuit name: {circuit_data['name']}")
            logger.debug(f"  Component count: {len(circuit_data['components'])}")
            logger.debug(f"  Net count: {len(circuit_data['nets'])}")
            logger.debug(f"  Subcircuit count: {len(circuit_data['subcircuits'])}")
            
            # Call Rust to generate schematic
            logger.info("  🦀 RUST CALL: Calling rust_kicad_schematic_writer.generate_schematic_from_python()")
            logger.info(f"  🦀 RUST CALL: Circuit name: '{circuit_data['name']}'")
            logger.info(f"  🦀 RUST CALL: Components: {len(circuit_data['components'])} items")
            logger.info(f"  🦀 RUST CALL: Nets: {len(circuit_data['nets'])} items")
            logger.info(f"  🦀 RUST CALL: Subcircuits: {len(circuit_data['subcircuits'])} items")
            
            schematic_content = rust_kicad_schematic_writer.generate_schematic_from_python(
                circuit_data, config
            )
            
            logger.info(f"  🦀 RUST RETURN: Generated {len(schematic_content)} bytes")
            
            logger.info(f"  ✅ Rust generated {len(schematic_content)} bytes of schematic data")
            
            # Write to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(schematic_content)
                
            logger.info(f"✅ Schematic written successfully to: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate schematic: {e}")
            logger.error(f"  Error type: {type(e).__name__}")
            import traceback
            logger.error(f"  Traceback:\n{traceback.format_exc()}")
            raise
            
    def generate_hierarchical_labels(self) -> List[Dict[str, Any]]:
        """
        Generate hierarchical labels for the circuit using Rust.
        
        Returns:
            List of hierarchical label dictionaries
        """
        logger.info("🏷️ Generating hierarchical labels using Rust...")
        
        circuit_data = self.convert_to_rust_format()
        config = {"paper_size": "A4"}
        
        try:
            # Create Rust writer and generate labels
            labels = rust_kicad_schematic_writer.generate_hierarchical_labels_from_python(
                circuit_data, config
            )
            
            logger.info(f"✅ Generated {len(labels)} hierarchical labels")
            return labels
            
        except Exception as e:
            logger.error(f"❌ Failed to generate hierarchical labels: {e}")
            raise


def test_rust_adapter():
    """Test function to verify the Rust adapter works."""
    logger.info("🧪 Testing Rust adapter...")
    
    # Create a simple test circuit
    from circuit_synth import Circuit, Component, Net
    
    circuit = Circuit("test_circuit")
    
    # Add a resistor
    r1 = Component(symbol="Device:R", ref="R", value="1k")
    circuit.add_component(r1)
    
    # Add a capacitor
    c1 = Component(symbol="Device:C", ref="C", value="100nF")
    circuit.add_component(c1)
    
    # Create a net
    vcc = Net("VCC")
    vcc.connect(r1.ref, "1")
    vcc.connect(c1.ref, "1")
    circuit.add_net(vcc)
    
    # Test the adapter
    adapter = RustSchematicAdapter(circuit)
    
    # Test conversion
    rust_data = adapter.convert_to_rust_format()
    logger.info(f"✅ Conversion successful: {rust_data['name']}")
    
    # Test schematic generation
    output_path = "test_rust_schematic.kicad_sch"
    adapter.generate_schematic(output_path)
    
    if Path(output_path).exists():
        logger.info(f"✅ Test schematic generated: {output_path}")
        return True
    else:
        logger.error("❌ Test schematic generation failed")
        return False


if __name__ == "__main__":
    # Run test when module is executed directly
    success = test_rust_adapter()
    sys.exit(0 if success else 1)