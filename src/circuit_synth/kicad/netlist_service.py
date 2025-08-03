"""
KiCad Netlist Generation Service

This module provides a clean, testable service for generating KiCad netlist files
from circuit JSON data. Follows SOLID principles with dependency injection
and clear separation of concerns.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NetlistGenerationResult:
    """Result of netlist generation operation."""

    success: bool
    netlist_path: Optional[Path] = None
    error_message: Optional[str] = None
    component_count: int = 0
    net_count: int = 0


class CircuitDataLoader:
    """Responsible for loading and validating circuit JSON data."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def load_circuit_data(self, json_file_path: str) -> Dict[str, Any]:
        """Load and validate circuit data from JSON file."""
        self.logger.info(f"Loading circuit data from: {json_file_path}")

        try:
            with open(json_file_path, "r") as f:
                circuit_data = json.load(f)

            # Validate required structure
            if not isinstance(circuit_data, dict):
                raise ValueError("Circuit data must be a dictionary")

            # Flatten hierarchical circuit data for netlist generation
            flattened_data = self._flatten_hierarchical_data(circuit_data)

            components = flattened_data.get("components", {})
            nets = flattened_data.get("nets", {})

            self.logger.info(
                f"Loaded {len(components)} components and {len(nets)} nets from hierarchical circuit"
            )
            # self.logger.debug(f"Components: {list(components.keys())}")
            # self.logger.debug(f"Nets: {list(nets.keys())}")

            return flattened_data

        except FileNotFoundError:
            raise FileNotFoundError(f"Circuit JSON file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in circuit file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load circuit data: {e}")

    def _flatten_hierarchical_data(
        self, circuit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Flatten hierarchical circuit data into a single-level structure for netlist generation."""
        flattened_components = {}
        flattened_nets = {}

        # Helper function to recursively collect components and nets
        def collect_from_circuit(circuit, prefix=""):
            # Collect components from this circuit level
            components = circuit.get("components", {})
            for comp_ref, comp_data in components.items():
                full_ref = f"{prefix}{comp_ref}" if prefix else comp_ref
                flattened_components[full_ref] = comp_data.copy()
                # Update the component's ref to include prefix
                flattened_components[full_ref]["ref"] = full_ref

            # Collect nets from this circuit level
            nets = circuit.get("nets", {})
            for net_name, net_connections in nets.items():
                if net_name not in flattened_nets:
                    flattened_nets[net_name] = []

                # Update component references in net connections to include prefix
                for connection in net_connections:
                    if isinstance(connection, dict) and "component" in connection:
                        original_ref = connection["component"]
                        full_ref = f"{prefix}{original_ref}" if prefix else original_ref
                        updated_connection = connection.copy()
                        updated_connection["component"] = full_ref
                        flattened_nets[net_name].append(updated_connection)
                    else:
                        flattened_nets[net_name].append(connection)

            # Recursively process subcircuits
            subcircuits = circuit.get("subcircuits", [])
            for subcircuit in subcircuits:
                # Remove subcircuit prefixing to get clean references (R1, R2 instead of subcircuit_R1, subcircuit_R2)
                collect_from_circuit(subcircuit, prefix)

        # Start flattening from root circuit
        collect_from_circuit(circuit_data)

        # Create flattened circuit data structure
        flattened_data = circuit_data.copy()
        flattened_data["components"] = flattened_components
        flattened_data["nets"] = flattened_nets
        flattened_data["subcircuits"] = (
            []
        )  # Clear subcircuits since we've flattened them

        return flattened_data


class CircuitReconstructor:
    """Responsible for reconstructing Circuit objects from JSON data."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def reconstruct_circuit(self, circuit_data: Dict[str, Any], circuit_name: str):
        """Reconstruct a Circuit object from JSON data, preserving hierarchical structure."""
        from ..core.circuit import Circuit
        from ..core.component import Component
        from ..core.net import Net

        # CRITICAL FIX: Preserve the original circuit name and structure instead of flattening
        main_circuit = Circuit(name=circuit_name)

        # Preserve hierarchical structure by reconstructing subcircuits first
        for subcircuit_data in circuit_data.get("subcircuits", []):
            subcircuit_name = subcircuit_data.get("name", "UnknownSubcircuit")

            # Recursively reconstruct subcircuit
            subcircuit = self.reconstruct_circuit(subcircuit_data, subcircuit_name)
            main_circuit.add_subcircuit(subcircuit)

        # Now create the circuit with proper hierarchical structure preserved
        temp_circuit = main_circuit

        # Set active circuit context for Net creation using the correct module
        from ..core.decorators import get_current_circuit, set_current_circuit

        original_active_circuit = get_current_circuit()
        # self.logger.debug(f"Original active circuit: {original_active_circuit}")
        set_current_circuit(temp_circuit)
        # self.logger.debug(f"Set active circuit to: {temp_circuit}")

        try:
            # Reconstruct components - ONLY for this circuit level (not subcircuits)
            components_data = circuit_data.get("components", {})

            for comp_ref, comp_data in components_data.items():
                # self.logger.info(f"🔧 Creating component {comp_ref}:")
                # self.logger.info(f"   - symbol: {comp_data.get('symbol', 'NOT SET')}")
                # self.logger.info(f"   - ref_prefix: {comp_data.get('ref_prefix', 'NOT SET')}")
                # self.logger.info(f"   - value: {comp_data.get('value', 'NOT SET')}")
                # self.logger.info(f"   - footprint: {comp_data.get('footprint', 'NOT SET')}")

                # Temporarily disable circuit context to prevent automatic addition
                original_active_circuit = get_current_circuit()
                set_current_circuit(None)

                try:
                    # Create component without adding to circuit to avoid reference collisions
                    comp = Component(
                        symbol=comp_data.get("symbol", ""),
                        ref=comp_data.get("ref_prefix", "U"),
                        value=comp_data.get("value", ""),
                        footprint=comp_data.get("footprint", ""),
                    )
                    # Set the specific reference from JSON
                    comp.ref = comp_ref
                    # self.logger.info(f"✅ Created component with final ref: {comp.ref}")
                    # Store component directly in internal storage without calling add_component
                    temp_circuit._components[comp_ref] = comp
                    # self.logger.info(f"📋 Stored component in circuit._components['{comp_ref}']")
                finally:
                    # Restore the original circuit context
                    set_current_circuit(original_active_circuit)

            # self.logger.info(f"📋 Final components in circuit: {list(temp_circuit._components.keys())}")

            # Reconstruct nets - ONLY for this circuit level (not subcircuits)
            nets_data = circuit_data.get("nets", {})

            for net_name, connections in nets_data.items():
                # Creating net with connections (verbose logging available if needed)

                net = Net(net_name)
                # Store net directly in internal storage since add_net may not exist
                temp_circuit._nets[net_name] = net
                # Net created successfully

                # Connect components to this net based on connections list
                for connection_idx, connection in enumerate(connections):
                    comp_ref = connection.get("component")
                    pin_data = connection.get("pin", {})
                    pin_number = pin_data.get("number", "1")

                    # Processing connection (verbose logging available if needed)

                    if comp_ref and pin_number:
                        # Access component directly from internal storage
                        if comp_ref in temp_circuit._components:
                            component = temp_circuit._components[comp_ref]
                            # Connect component pin to net
                            component[pin_number] += net
                        else:
                            available_comps = list(temp_circuit._components.keys())
                            self.logger.error(
                                f"❌ Component '{comp_ref}' not found in circuit!"
                            )
                            self.logger.error(
                                f"📋 Available components: {available_comps}"
                            )
                    else:
                        self.logger.warning(
                            f"⚠️ Skipping connection - missing comp_ref ({comp_ref}) or pin_number ({pin_number})"
                        )

            # Log any connection issues for debugging
            for net_name, net_obj in temp_circuit._nets.items():
                if len(net_obj._pins) < 2:
                    self.logger.warning(
                        f"Net '{net_name}' has only {len(net_obj._pins)} connection(s) - may indicate connection issue"
                    )
                # elif len(net_obj._pins) > 10:
                #     self.logger.info(f"Net '{net_name}' has {len(net_obj._pins)} connections (large net)")

            return temp_circuit

        finally:
            # Restore original active circuit
            # self.logger.debug(f"Restoring original active circuit: {original_active_circuit}")
            set_current_circuit(original_active_circuit)


class NetlistFileWriter:
    """Responsible for writing netlist files to disk."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def write_netlist(self, circuit, output_path: Path) -> bool:
        """Write circuit netlist to KiCad .net file."""
        from ..core.netlist_exporter import NetlistExporter

        try:
            self.logger.info(f"Writing netlist to: {output_path}")
            # self.logger.info(f"🔍 DEBUG: Circuit components: {list(circuit._components.keys()) if hasattr(circuit, '_components') else 'NO _components'}")
            # self.logger.info(f"🔍 DEBUG: Circuit nets: {list(circuit._nets.keys()) if hasattr(circuit, '_nets') else 'NO _nets'}")
            #
            ## Detailed inspection of circuit net connections
            # if hasattr(circuit, '_nets'):
            #     for net_name, net_obj in circuit._nets.items():
            #         self.logger.info(f"🌐 DEBUG: Net '{net_name}' has {len(net_obj._pins)} pins connected:")
            #         for pin in net_obj._pins:
            #             component_ref = pin._component.ref if pin._component else "NO_COMPONENT"
            #             pin_num = pin._component_pin_id if hasattr(pin, '_component_pin_id') else pin.num
            #             self.logger.info(f"   - {component_ref}[{pin_num}]")
            #
            ## ADDITIONAL DEBUG: Inspect the circuit data being passed to netlist exporter
            # self.logger.info("🔍 DEBUG: Inspecting circuit data passed to netlist exporter...")
            # circuit_data = circuit.to_dict()
            # self.logger.info(f"🔍 DEBUG: Circuit data components: {list(circuit_data.get('components', {}).keys())}")
            # self.logger.info(f"🔍 DEBUG: Circuit data nets: {list(circuit_data.get('nets', {}).keys())}")
            #
            ## Check net connections in detail
            # for net_name, connections in circuit_data.get('nets', {}).items():
            #     self.logger.info(f"🔗 DEBUG: Net '{net_name}' connections:")
            #     for i, conn in enumerate(connections):
            #         self.logger.info(f"   Connection {i}: {conn}")
            #         component = conn.get('component')
            #         pin_info = conn.get('pin', {})
            #         self.logger.info(f"     Component: {component} (type: {type(component)})")
            #         self.logger.info(f"     Pin info: {pin_info}")

            exporter = NetlistExporter(circuit)
            exporter.generate_kicad_netlist(str(output_path))

            # Verify file was created
            if output_path.exists() and output_path.stat().st_size > 0:
                self.logger.info(f"Netlist file created successfully: {output_path}")
                return True
            else:
                self.logger.error(
                    f"❌ Netlist file was not created or is empty: {output_path}"
                )
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to write netlist file: {e}")
            return False


class KiCadNetlistService:
    """
    Main service for generating KiCad netlist files.

    This service orchestrates the netlist generation process using
    dependency injection and clear separation of concerns.
    """

    def __init__(
        self,
        data_loader: Optional[CircuitDataLoader] = None,
        circuit_reconstructor: Optional[CircuitReconstructor] = None,
        file_writer: Optional[NetlistFileWriter] = None,
    ):
        """Initialize service with optional dependency injection."""
        self.data_loader = data_loader or CircuitDataLoader()
        self.circuit_reconstructor = circuit_reconstructor or CircuitReconstructor()
        self.file_writer = file_writer or NetlistFileWriter()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate_netlist(
        self, json_file_path: str, output_path: str, circuit_name: str
    ) -> NetlistGenerationResult:
        """
        Generate KiCad netlist file from circuit JSON data.

        Args:
            json_file_path: Path to circuit JSON file
            output_path: Path for output .net file
            circuit_name: Name of the circuit

        Returns:
            NetlistGenerationResult with success status and details
        """
        self.logger.info(f"Starting netlist generation for '{circuit_name}'")
        # self.logger.info(f"📖 Source: {json_file_path}")
        # self.logger.info(f"📝 Output: {output_path}")

        try:
            # Step 1: Load circuit data
            circuit_data = self.data_loader.load_circuit_data(json_file_path)

            # Step 2: Reconstruct circuit object
            circuit = self.circuit_reconstructor.reconstruct_circuit(
                circuit_data, circuit_name
            )

            # Step 3: Write netlist file
            output_file = Path(output_path)
            success = self.file_writer.write_netlist(circuit, output_file)

            # Step 4: Return result
            if success:
                component_count = (
                    len(circuit._components) if hasattr(circuit, "_components") else 0
                )
                net_count = len(circuit._nets) if hasattr(circuit, "_nets") else 0

                self.logger.info(
                    f"Netlist generation successful: {component_count} components, {net_count} nets"
                )

                return NetlistGenerationResult(
                    success=True,
                    netlist_path=output_file,
                    component_count=component_count,
                    net_count=net_count,
                )
            else:
                return NetlistGenerationResult(
                    success=False, error_message="Failed to write netlist file"
                )

        except Exception as e:
            import traceback

            error_msg = f"Netlist generation failed: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.logger.error(f"❌ Full traceback: {traceback.format_exc()}")

            return NetlistGenerationResult(success=False, error_message=error_msg)


def create_netlist_service() -> KiCadNetlistService:
    """Factory function to create a configured netlist service."""
    return KiCadNetlistService()
