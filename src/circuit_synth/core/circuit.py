# FILE: src/circuit_synth/core/circuit.py

import json
import os
import re
import tempfile
from pathlib import Path  # Import Path
from typing import Any, Dict, List, Optional

from ._logger import context_logger
from .exception import CircuitSynthError, ValidationError
from .json_encoder import CircuitSynthJSONEncoder
from .net import Net

# Import the exporter function
from .netlist_exporter import NetlistExporter
from .reference_manager import ReferenceManager


class Circuit:
    from .component import Component  # for type-hinting

    def __init__(self, name=None, description=None, auto_comments=True):
        self.name = name or "UnnamedCircuit"
        self.description = description
        self.auto_comments = auto_comments
        self._components = {}
        self._nets = {}
        # self._unnamed_net_counter = 1 # Removed: Counter is now managed by ReferenceManager
        self._parent = None
        self._subcircuits = []
        self._component_list = []
        self._reference_manager = ReferenceManager()
        self._annotations = []  # Store TextProperty, TextBox, etc.

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

    @staticmethod
    def _from_json(json_data):
        circuit = Circuit(name=json_data.get("name", "unnamed"))

        # Add components
        if "components" in json_data:
            for comp_data in json_data["components"]:
                from .component import Component

                comp = Component(
                    symbol=comp_data.get("symbol", "Device:R"),
                    ref=comp_data.get("reference", comp_data.get("ref", "U")),
                    value=comp_data.get("value", ""),
                    footprint=comp_data.get("footprint", ""),
                )
                circuit._components[comp.ref] = comp
                circuit._component_list.append(comp)

        # Add nets
        if "nets" in json_data:
            from .net import Net

            for net_data in json_data["nets"]:
                net = Net(net_data.get("name", "unnamed"))
                circuit._nets[net.name] = net

        # Add subcircuits recursively
        if "subcircuits" in json_data:
            for sub_data in json_data["subcircuits"]:
                subcircuit = Circuit._from_json(sub_data)
                circuit.add_subcircuit(subcircuit)

        return circuit

    @property
    def components(self):
        """Get components dictionary for compatibility."""
        return self._components

    @property
    def nets(self):
        """Get nets dictionary for compatibility."""
        return self._nets

    @property
    def subcircuits(self):
        """Get subcircuits list."""
        return self._subcircuits

    def add_subcircuit_old(self, subcirc: "Circuit"):
        context_logger.debug(
            "Added subcircuit to parent",
            component="CIRCUIT",
            subcircuit_name=subcirc.name,
            parent_name=self.name,
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
                default_prefix = re.sub(r"[^A-Za-z0-9_]", "", default_prefix)
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
                circuit_name=self.name,
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
                circuit_name=self.name,
            )
            comp.ref = user_ref
            comp._is_prefix = True  # Mark as prefix reference
            self._components[placeholder_key] = comp
            self._component_list.append(comp)

    def finalize_references(self):
        """Auto-assign references for any components that only had a prefix."""
        context_logger.debug(
            "Starting reference finalization",
            component="CIRCUIT",
            circuit_name=self.name,
        )

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
                    circuit_name=self.name,
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
            total_components=len(self._components),
        )

        # Auto-generate docstring annotation if enabled
        if self.auto_comments and self.description and self.description.strip():
            self._add_docstring_annotation()

        # Recursively finalize subcircuits
        for sc in self._subcircuits:
            sc.finalize_references()

    def _add_docstring_annotation(self):
        """Add a TextBox annotation with the circuit's docstring."""
        # Check if docstring annotation already exists to prevent duplicates
        for annotation in self._annotations:
            if (
                hasattr(annotation, "text")
                and annotation.text.strip() == self.description.strip()
            ):
                return  # Already added
            elif (
                isinstance(annotation, dict)
                and annotation.get("text", "").strip() == self.description.strip()
            ):
                return  # Already added

        from .annotations import TextBox

        # Position the docstring in the top-left area of the schematic
        # Using a reasonable default position and size
        docstring_box = TextBox(
            text=self.description.strip(),
            position=(
                184.0,
                110.0,
            ),  # Double the coordinates to account for KiCad scaling
            size=(80.0, 30.0),  # 80mm wide, 30mm tall
            text_size=1.2,
            bold=True,
            background=True,
            background_color="lightyellow",
            border=True,
            justify="center center",
        )
        self.add_annotation(docstring_box)
        context_logger.debug(
            "Added auto-generated docstring annotation",
            component="CIRCUIT",
            circuit_name=self.name,
            text_length=len(self.description),
        )

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
                circuit_name=self.name,
            )
            self._nets[net.name] = net

    def add_annotation(self, annotation):
        """Add a text annotation (TextProperty, TextBox, etc.) to this circuit."""
        self._annotations.append(annotation)
        context_logger.debug(
            "Added annotation to circuit",
            component="CIRCUIT",
            annotation_type=type(annotation).__name__,
            circuit_name=self.name,
        )

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
        self, parent_name: str = None, flattened: List[Dict[str, Any]] = None
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

    def _generate_hierarchical_json_netlist(self, filename: str) -> None:
        """
        Generate JSON netlist with hierarchical components flattened into single component/net structure.
        This creates the format expected by the netlist service: {"components": {...}, "nets": {...}}
        """
        import json

        from .netlist_exporter import NetlistExporter

        # Collect all components and nets from this circuit and all subcircuits
        all_components = {}  # ref -> component_dict
        all_nets = {}  # net_name -> [connections]
        all_net_objects = {}  # net_name -> Net object (to collect connections from)

        context_logger.info(
            "Collecting hierarchical components and nets",
            component="CIRCUIT",
            circuit_name=self.name,
        )

        # Helper to recursively collect from circuit and subcircuits
        def collect_from_circuit(circuit, prefix=""):
            # Collect components
            for comp_ref, comp in circuit._components.items():
                if hasattr(comp, "ref") and comp.ref:
                    full_ref = f"{prefix}{comp.ref}" if prefix else comp.ref
                    # Convert component to dict format
                    all_components[full_ref] = comp.to_dict()

            # Collect nets (the Net objects themselves, not connections yet)
            for net_name, net in circuit._nets.items():
                if net_name not in all_net_objects:
                    all_net_objects[net_name] = net
                    all_nets[net_name] = []

            # Recursively collect from subcircuits
            for subcircuit in circuit._subcircuits:
                collect_from_circuit(subcircuit, f"{prefix}{subcircuit.name}_")

        # Start collection from root circuit
        collect_from_circuit(self)

        # Now collect connections from each net's _pins set
        for net_name, net in all_net_objects.items():
            if hasattr(net, "_pins"):
                for pin in net._pins:
                    if hasattr(pin, "_component") and pin._component:
                        component_ref = pin._component.ref

                        # Find the full reference (with prefix) for this component
                        full_ref = None
                        for ref, comp in all_components.items():
                            if comp.get("ref") == component_ref:
                                full_ref = ref
                                break

                        if full_ref:
                            connection = {
                                "component": full_ref,
                                "pin": {
                                    "number": str(pin.num),
                                    "name": getattr(pin, "name", "~"),
                                    "type": str(getattr(pin, "func", "passive")),
                                },
                            }
                            all_nets[net_name].append(connection)

        # Create the expected JSON structure
        json_data = {
            "name": self.name,
            "description": getattr(self, "description", ""),
            "tstamps": "",
            "source_file": f"{self.name}.kicad_sch",
            "components": all_components,
            "nets": all_nets,
            "subcircuits": [],  # Flattened, so no subcircuits
            "annotations": getattr(self, "_annotations", []),
        }

        context_logger.info(
            "Hierarchical collection complete",
            component="CIRCUIT",
            total_components=len(all_components),
            total_nets=len(all_nets),
            component_refs=list(all_components.keys()),
            net_names=list(all_nets.keys()),
        )

        # Write to file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, default=str)
            context_logger.info(
                f"Hierarchical JSON netlist written to {filename}", component="CIRCUIT"
            )
        except Exception as e:
            context_logger.error(f"Failed to write hierarchical JSON: {e}")
            raise

    def generate_kicad_netlist(self, filename: str) -> None:
        """
        Generate a KiCad netlist (.net) file for this circuit and its hierarchy.
        """
        exporter = NetlistExporter(self)
        return exporter.generate_kicad_netlist(filename)

    def generate_kicad_project(
        self,
        project_name: str,
        generate_pcb: bool = True,
        force_regenerate: bool = False,
        placement_algorithm: str = "connection_centric",
        draw_bounding_boxes: bool = False,
        generate_ratsnest: bool = True,
    ) -> None:
        """
        Generate a complete KiCad project (schematic + PCB) from this circuit.

        This method provides a simplified API that handles all the boilerplate setup
        required for KiCad project generation, creating the project directory and
        generating KiCad files directly without intermediate JSON files.

        Args:
            project_name: Name of the KiCad project and directory to create
            generate_pcb: Whether to generate PCB in addition to schematic (default: True)
            force_regenerate: Force regeneration of existing files, losing manual edits (default: False)
            placement_algorithm: Component placement algorithm to use (default: "connection_centric")
            draw_bounding_boxes: Whether to draw visual bounding boxes around components (default: False)
            generate_ratsnest: Whether to generate ratsnest connections in PCB (default: True)

        Example:
            >>> circuit = esp32s3_simple()
            >>> circuit.generate_kicad_project("esp32s3_simple")
        """
        try:
            from ..kicad.config import KiCadConfig, get_recommended_generator
            
            # Finalize references before generation
            self.finalize_references()

            # Create output directory with the project name
            output_path = Path(project_name).resolve()
            output_path.mkdir(parents=True, exist_ok=True)

            context_logger.info(
                "Starting KiCad project generation",
                component="CIRCUIT",
                project_name=project_name,
                output_dir=str(output_path),
                generate_pcb=generate_pcb,
                placement_algorithm=placement_algorithm,
                generator_type=get_recommended_generator(),
            )

            # Use legacy system for positioning/hierarchy, modern API for file writing
            from ..kicad.sch_gen.main_generator import SchematicGenerator

            context_logger.info("Using hybrid approach: legacy positioning + modern kicad-sch-api file writing", component="CIRCUIT")

            # Create a temporary JSON file for the circuit (will be cleaned up)
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_file:
                temp_json_path = temp_file.name
                self.generate_json_netlist(temp_json_path)

            try:
                # Create schematic generator that outputs directly to the project directory
                generator = SchematicGenerator(str(output_path.parent), project_name)

                # Generate the complete project using the temporary JSON file
                # Legacy system handles placement, modern API handles file writing via write_schematic_file
                result = generator.generate_project(
                    json_file=temp_json_path,
                    placement_algorithm=placement_algorithm,  # PCB placement algorithm  
                    schematic_placement="sequential",  # Use simple sequential for schematic
                    generate_pcb=generate_pcb,
                    force_regenerate=force_regenerate,
                    draw_bounding_boxes=draw_bounding_boxes,
                    generate_ratsnest=generate_ratsnest,
                )
            finally:
                # Clean up the temporary JSON file
                import os

                try:
                    os.unlink(temp_json_path)
                except OSError:
                    pass

            if result.get("success", True):  # Default to success if not specified
                context_logger.info(
                    "KiCad project generated successfully",
                    component="CIRCUIT",
                    project_name=project_name,
                    output_path=str(output_path),
                )
            else:
                error_msg = result.get(
                    "error", "Unknown error occurred during project generation"
                )
                context_logger.error(
                    "KiCad project generation failed",
                    component="CIRCUIT",
                    project_name=project_name,
                    error=error_msg,
                )
                raise CircuitSynthError(f"KiCad project generation failed: {error_msg}")

        except ImportError as e:
            error_msg = f"KiCad integration not available: {e}"
            context_logger.error(error_msg, component="CIRCUIT")
            raise CircuitSynthError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate KiCad project '{project_name}': {e}"
            context_logger.error(
                error_msg, component="CIRCUIT", project_name=project_name
            )
            raise CircuitSynthError(error_msg) from e

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

        Raises:
            ImportError: If simulation dependencies are not installed
            CircuitSynthError: If circuit cannot be converted for simulation
        """
        try:
            from ..simulation import CircuitSimulator
        except ImportError as e:
            context_logger.error(
                "Simulation module not available", component="CIRCUIT", error=str(e)
            )
            raise ImportError(
                "Circuit simulation requires PySpice and its dependencies. "
                "Install with: pip install circuit-synth[simulation]"
            ) from e

        context_logger.info(
            "Creating simulator for circuit",
            component="CIRCUIT",
            circuit_name=self.name,
        )
        return CircuitSimulator(self)

    def simulator(self):
        """
        Alias for simulate() method for backward compatibility.

        Returns:
            CircuitSimulator: Simulator object for running analyses
        """
        return self.simulate()

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
