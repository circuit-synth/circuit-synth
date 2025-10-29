# FILE: src/circuit_synth/core/circuit.py

import inspect
import re
from pathlib import Path  # Import Path
from typing import Any, Dict, List, Optional

from ._logger import context_logger
from .exception import ValidationError
from .net import Net
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
        self._ref_mapping = (
            {}
        )  # Track prefix -> final ref mappings for source rewriting
        self._circuit_func = None  # Store reference to the @circuit decorated function

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
                # Use from_dict to preserve all Net attributes
                net = Net.from_dict(net_data)
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

                # Capture ref mapping for source rewriting
                # Use list to track multiple components with same prefix
                if prefix not in self._ref_mapping:
                    self._ref_mapping[prefix] = []
                self._ref_mapping[prefix].append(final_ref)

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

    def _get_source_file(self) -> Optional[Path]:
        """Get the source file path for this circuit's function.

        Uses Python's inspect module to find where the @circuit decorated
        function was defined.

        Returns:
            Path to source file, or None if not available (REPL, exec, frozen app)
        """
        if not self._circuit_func:
            context_logger.debug(
                "No circuit function reference available",
                component="CIRCUIT",
                circuit_name=self.name,
            )
            return None

        try:
            source_file = inspect.getfile(self._circuit_func)

            # Check for special cases where source isn't available
            if source_file == "<stdin>" or source_file == "<string>":
                context_logger.warning(
                    "Circuit defined in REPL/exec environment, source file not available",
                    component="CIRCUIT",
                    circuit_name=self.name,
                )
                return None

            # Check for frozen applications (PyInstaller, etc)
            if getattr(inspect.sys, "frozen", False):
                context_logger.warning(
                    "Running in frozen application, source file not available",
                    component="CIRCUIT",
                    circuit_name=self.name,
                )
                return None

            path = Path(source_file).resolve()

            if not path.exists():
                context_logger.warning(
                    "Source file no longer exists",
                    component="CIRCUIT",
                    circuit_name=self.name,
                    source_file=str(path),
                )
                return None

            return path

        except (TypeError, OSError) as e:
            context_logger.warning(
                "Could not determine source file",
                component="CIRCUIT",
                circuit_name=self.name,
                error=str(e),
            )
            return None

    def _update_source_refs(self, source_file: Path) -> bool:
        """Update component refs in the source file.

        Uses SourceRefRewriter to atomically update ref values in the
        Python source file, preserving formatting and encoding.

        Args:
            source_file: Path to the Python source file to update

        Returns:
            True if update succeeded, False if skipped or failed
        """
        if not self._ref_mapping:
            context_logger.debug(
                "No ref mapping to apply", component="CIRCUIT", circuit_name=self.name
            )
            return False

        try:
            from .source_ref_rewriter import SourceRefRewriter

            context_logger.info(
                "Updating source file with finalized refs",
                component="CIRCUIT",
                circuit_name=self.name,
                source_file=str(source_file),
                ref_mapping=self._ref_mapping,
            )

            rewriter = SourceRefRewriter(source_file, self._ref_mapping)
            success = rewriter.update()

            if success:
                context_logger.info(
                    "Source file updated successfully",
                    component="CIRCUIT",
                    circuit_name=self.name,
                    refs_updated=len(self._ref_mapping),
                )
            else:
                context_logger.debug(
                    "Source file unchanged (no modifications needed)",
                    component="CIRCUIT",
                    circuit_name=self.name,
                )

            return success

        except Exception as e:
            context_logger.error(
                "Failed to update source file",
                component="CIRCUIT",
                circuit_name=self.name,
                source_file=str(source_file),
                error=str(e),
            )
            # Don't raise - source rewriting failure shouldn't break project generation
            return False

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

    def add_image(self, image_path: str, position: tuple, scale: float = 1.0):
        """
        Add an embedded image to the schematic.

        Images are embedded as base64-encoded data in the KiCad schematic file.
        The image file is read when the schematic is generated, so it only needs
        to exist at generation time.

        Args:
            image_path: Path to image file (PNG, JPG, etc.)
            position: Tuple of (x, y) position in mm
            scale: Scale factor (1.0 = original size, 2.0 = 2x larger, etc.)

        Returns:
            Image: The created Image annotation object

        Example:
            >>> circuit.add_image("logo.png", position=(100, 50), scale=2.0)
        """
        from .annotations import Image

        img = Image(image_path=image_path, position=position, scale=scale)
        self.add_annotation(img)

        context_logger.debug(
            "Added image to circuit",
            component="CIRCUIT",
            image_path=image_path,
            position=position,
            scale=scale,
            circuit_name=self.name,
        )

        return img

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
        placement_algorithm: str = "hierarchical",
        draw_bounding_boxes: bool = False,
        generate_ratsnest: bool = True,
        update_source_refs: Optional[bool] = None,
        preserve_user_components: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a complete KiCad project (schematic + PCB) from this circuit.

        This method provides a simplified API that handles all the boilerplate setup
        required for KiCad project generation, creating the project directory and
        generating KiCad files with an automatic JSON netlist in the project directory.

        Args:
            project_name: Name of the KiCad project and directory to create
            generate_pcb: Whether to generate PCB in addition to schematic (default: True)
            force_regenerate: Force regeneration of existing files, losing manual edits (default: False)
            placement_algorithm: Component placement algorithm to use (default: "hierarchical")
            draw_bounding_boxes: Whether to draw visual bounding boxes around components (default: False)
            generate_ratsnest: Whether to generate ratsnest connections in PCB (default: True)
            update_source_refs: Whether to update source file with finalized refs.
                               None (default): Auto-update unless force_regenerate=True
                               True: Always update source file
                               False: Never update source file
            preserve_user_components: Keep components in KiCad that don't exist in Python (default: False)
                                     False: Python is source of truth - delete components not in Python
                                     True: Preserve all components in KiCad, even if not in Python

        Returns:
            dict: Result dictionary containing:
                - success (bool): Whether generation succeeded
                - json_path (Path): Path to the canonical JSON netlist
                - project_path (Path): Path to the KiCad project directory
                - error (str, optional): Error message if generation failed

        Example:
            >>> circuit = esp32s3_simple()
            >>> result = circuit.generate_kicad_project("esp32s3_simple")
            >>> print(f"JSON netlist: {result['json_path']}")
            >>> print(f"KiCad project: {result['project_path']}")
        """
        try:
            from .. import print_version_info
            from ..kicad.config import get_recommended_generator

            # Print version information for debugging
            print_version_info()
            print()  # Blank line after version info

            # Finalize references before generation
            self.finalize_references()

            # Determine if we should update source file
            should_update_source = update_source_refs
            if should_update_source is None:
                # Auto mode: update unless force_regenerate
                should_update_source = not force_regenerate

            # Update source file with finalized refs if enabled
            if should_update_source:
                source_file = self._get_source_file()
                if source_file:
                    self._update_source_refs(source_file)
                else:
                    context_logger.debug(
                        "Source file not available, skipping ref update",
                        component="CIRCUIT",
                        circuit_name=self.name,
                    )

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

            context_logger.info(
                "Using hybrid approach: legacy positioning + modern kicad-sch-api file writing",
                component="CIRCUIT",
            )

            # Determine project base name for file generation
            # Check for existing .kicad_pro files in output directory
            existing_projects = list(output_path.glob("*.kicad_pro"))

            if len(existing_projects) > 1:
                # Multiple projects - error out
                project_names = [p.stem for p in existing_projects]
                raise ValueError(
                    f"Multiple KiCad projects found in '{output_path}': {project_names}. "
                    f"Please specify which project to update or clean the directory."
                )
            elif len(existing_projects) == 1:
                # Exactly one project - use its base name for regeneration
                project_base_name = existing_projects[0].stem
                context_logger.info(
                    f"Detected existing KiCad project: {project_base_name}",
                    component="CIRCUIT",
                )
                # Validate folder name matches project base name
                if output_path.name != project_base_name:
                    context_logger.warning(
                        f"Folder name '{output_path.name}' doesn't match project '{project_base_name}'. "
                        f"Using circuit name for file generation.",
                        component="CIRCUIT",
                    )
                    # Use circuit name for file generation, not folder name
                    project_base_name = self.name
            else:
                # No existing project - use circuit name for KiCad files
                project_base_name = self.name
                context_logger.info(
                    f"No existing project found, using circuit name: {project_base_name}",
                    component="CIRCUIT",
                )

            # Create JSON netlist in project directory (canonical format)
            json_path = output_path / f"{project_base_name}.json"
            self.generate_json_netlist(str(json_path))

            context_logger.info(
                "Generated canonical JSON netlist",
                component="CIRCUIT",
                json_path=str(json_path),
            )

            # Create schematic generator
            # Pass output_path.parent as output_dir and project_base_name as project_name
            # But we need to change how SchematicGenerator uses project_dir
            # For now, pass the full path and update how project_dir is computed
            generator = SchematicGenerator(str(output_path), project_base_name)
            # Override project_dir since output_path is already the full project directory
            generator.project_dir = Path(str(output_path)).resolve()

            # Generate the complete project using the JSON file
            # Legacy system handles placement, modern API handles file writing via write_schematic_file
            result = generator.generate_project(
                json_file=str(json_path),
                placement_algorithm=placement_algorithm,  # PCB placement algorithm
                schematic_placement="sequential",  # Use simple sequential for schematic
                generate_pcb=generate_pcb,
                force_regenerate=force_regenerate,
                draw_bounding_boxes=draw_bounding_boxes,
                generate_ratsnest=generate_ratsnest,
                preserve_user_components=preserve_user_components,
            )

            if result.get("success", True):  # Default to success if not specified
                context_logger.info(
                    "KiCad project generated successfully",
                    component="CIRCUIT",
                    project_name=project_name,
                    output_path=str(output_path),
                )
                # Return success result with JSON path
                return {
                    "success": True,
                    "json_path": json_path,
                    "project_path": output_path,
                }
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
                return {
                    "success": False,
                    "error": error_msg,
                    "json_path": json_path,
                    "project_path": output_path,
                }

        except ImportError as e:
            error_msg = f"KiCad integration not available: {e}"
            context_logger.error(error_msg, component="CIRCUIT")
            return {
                "success": False,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Failed to generate KiCad project '{project_name}': {e}"
            context_logger.error(
                error_msg, component="CIRCUIT", project_name=project_name
            )
            return {
                "success": False,
                "error": error_msg,
            }

    def generate_bom(
        self,
        output_file: Optional[str] = None,
        project_name: Optional[str] = None,
        fields: Optional[str] = None,
        labels: Optional[str] = None,
        group_by: Optional[str] = None,
        exclude_dnp: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a Bill of Materials (BOM) from this circuit as a CSV file.

        This method creates a KiCad project if one doesn't already exist, then
        exports the schematic to a CSV BOM file using kicad-cli.

        Args:
            output_file: Path where CSV BOM should be written. If not provided,
                        defaults to {project_name}/{project_name}.csv
            project_name: Name of the KiCad project directory. If not provided,
                         defaults to the circuit name. Required if output_file is provided
                         but needs a project.
            fields: Comma-separated fields to export from schematic. If not specified,
                   KiCad will export default fields (Refs, Value, Footprint, etc.)
            labels: Comma-separated column headers for the BOM. Must match the number
                   of fields if fields are specified.
            group_by: Field to group references by when exporting. Common values:
                     "Value" (group by component value), "Footprint", etc.
            exclude_dnp: If True, exclude "Do not populate" components from BOM

        Returns:
            dict: Result dictionary containing:
                - success (bool): True if BOM was successfully generated
                - file (Path): Path to the generated CSV file
                - component_count (int): Number of components in the BOM
                - project_path (Path): Path to the KiCad project directory
                - error (str, optional): Error message if generation failed

        Example:
            >>> circuit = led_blinker()
            >>> result = circuit.generate_bom(project_name="led_blinker")
            >>> print(f"BOM exported to: {result['file']}")
            >>> print(f"Component count: {result['component_count']}")

        Raises:
            FileNotFoundError: If kicad-cli is not available
            RuntimeError: If BOM export fails
        """
        from ..kicad.bom_exporter import BOMExporter

        # Determine project name
        if project_name is None:
            project_name = self.name

        # Determine output file
        if output_file is None:
            output_path = Path(project_name)
            output_file = output_path / f"{project_name}.csv"
        else:
            output_file = Path(output_file)

        try:
            # Generate KiCad project if needed
            project_path = Path(project_name).resolve()
            project_base_name = self.name
            sch_file = project_path / f"{project_base_name}.kicad_sch"

            if not sch_file.exists():
                context_logger.info(
                    "Generating KiCad project for BOM export",
                    component="CIRCUIT",
                    circuit_name=self.name,
                    project_name=project_name,
                )

                project_result = self.generate_kicad_project(
                    project_name=project_name,
                    generate_pcb=False,  # Only need schematic for BOM
                )

                if not project_result.get("success"):
                    error_msg = f"Failed to generate KiCad project: {project_result.get('error')}"
                    context_logger.error(
                        error_msg, component="CIRCUIT", project_name=project_name
                    )
                    return {"success": False, "error": error_msg}

            else:
                context_logger.debug(
                    "Using existing KiCad project for BOM export",
                    component="CIRCUIT",
                    project_path=str(project_path),
                )

            # Export BOM using kicad-cli
            context_logger.info(
                "Exporting BOM",
                component="CIRCUIT",
                schematic_file=str(sch_file),
                output_file=str(output_file),
            )

            bom_result = BOMExporter.export_csv(
                schematic_file=sch_file,
                output_file=output_file,
                fields=fields,
                labels=labels,
                group_by=group_by,
                exclude_dnp=exclude_dnp,
            )

            # Add project path to result
            bom_result["project_path"] = project_path

            return bom_result

        except FileNotFoundError as e:
            error_msg = f"Cannot export BOM: {e}"
            context_logger.error(error_msg, component="CIRCUIT")
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Failed to generate BOM: {e}"
            context_logger.error(
                error_msg, component="CIRCUIT", exception=str(e)
            )
            return {"success": False, "error": error_msg}

    def generate_pdf_schematic(
        self,
        output_file: Optional[str] = None,
        project_name: Optional[str] = None,
        black_and_white: bool = False,
        theme: Optional[str] = None,
        exclude_drawing_sheet: bool = False,
        pages: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a PDF schematic from this circuit.

        This method creates a KiCad project if one doesn't already exist, then
        exports the schematic to a PDF file using kicad-cli.

        Args:
            output_file: Path where PDF should be written. If not provided,
                        defaults to {project_name}/{project_name}.pdf
            project_name: Name of the KiCad project directory. If not provided,
                         defaults to the circuit name.
            black_and_white: Export in black and white instead of color (default: False)
            theme: Color theme to use for export (optional). Theme name depends on KiCad installation.
            exclude_drawing_sheet: Exclude the drawing sheet/border from PDF (default: False)
            pages: Page range to export (e.g., "1,3-5" for pages 1, 3, 4, 5).
                  If not specified, all pages are exported.

        Returns:
            dict: Result dictionary containing:
                - success (bool): True if PDF was successfully generated
                - file (Path): Path to the generated PDF file
                - project_path (Path): Path to the KiCad project directory
                - error (str, optional): Error message if generation failed

        Example:
            >>> circuit = led_blinker()
            >>> result = circuit.generate_pdf_schematic(project_name="led_blinker")
            >>> print(f"PDF exported to: {result['file']}")

        Raises:
            FileNotFoundError: If kicad-cli is not available
            RuntimeError: If PDF export fails
        """
        from ..kicad.pdf_exporter import PDFExporter

        # Determine project name
        if project_name is None:
            project_name = self.name

        # Determine output file
        if output_file is None:
            output_path = Path(project_name)
            output_file = output_path / f"{project_name}.pdf"
        else:
            output_file = Path(output_file)

        try:
            # Generate KiCad project if needed
            project_path = Path(project_name).resolve()
            project_base_name = self.name
            sch_file = project_path / f"{project_base_name}.kicad_sch"

            if not sch_file.exists():
                context_logger.info(
                    "Generating KiCad project for PDF export",
                    component="CIRCUIT",
                    circuit_name=self.name,
                    project_name=project_name,
                )

                project_result = self.generate_kicad_project(
                    project_name=project_name,
                    generate_pcb=False,  # Only need schematic for PDF
                )

                if not project_result.get("success"):
                    error_msg = f"Failed to generate KiCad project: {project_result.get('error')}"
                    context_logger.error(
                        error_msg, component="CIRCUIT", project_name=project_name
                    )
                    return {"success": False, "error": error_msg}

            else:
                context_logger.debug(
                    "Using existing KiCad project for PDF export",
                    component="CIRCUIT",
                    project_path=str(project_path),
                )

            # Export PDF using kicad-cli
            context_logger.info(
                "Exporting PDF schematic",
                component="CIRCUIT",
                schematic_file=str(sch_file),
                output_file=str(output_file),
            )

            pdf_result = PDFExporter.export_pdf(
                schematic_file=sch_file,
                output_file=output_file,
                black_and_white=black_and_white,
                theme=theme,
                exclude_drawing_sheet=exclude_drawing_sheet,
                pages=pages,
            )

            # Add project path to result
            pdf_result["project_path"] = project_path

            return pdf_result

        except FileNotFoundError as e:
            error_msg = f"Cannot export PDF: {e}"
            context_logger.error(error_msg, component="CIRCUIT")
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Failed to generate PDF schematic: {e}"
            context_logger.error(
                error_msg, component="CIRCUIT", exception=str(e)
            )
            return {"success": False, "error": error_msg}

    def generate_gerbers(
        self,
        output_dir: Optional[str] = None,
        project_name: Optional[str] = None,
        include_drill: bool = True,
        drill_format: str = "excellon",
    ) -> Dict[str, Any]:
        """
        Generate Gerber files for PCB manufacturing from this circuit.

        This method creates a complete KiCad project (including PCB) if one doesn't
        already exist, then exports Gerber files for manufacturing using kicad-cli.
        Gerbers can be submitted directly to manufacturers like JLCPCB, PCBWay, etc.

        Args:
            output_dir: Directory where Gerber files should be written. If not provided,
                       defaults to {project_name}/gerbers
            project_name: Name of the KiCad project directory. If not provided,
                         defaults to the circuit name.
            include_drill: Also export drill files along with Gerbers (default: True)
            drill_format: Format for drill files: "excellon" (default) or "gerber"

        Returns:
            dict: Result dictionary containing:
                - success (bool): True if Gerbers were successfully generated
                - gerber_files (list): List of Path objects to generated .gbr files
                - drill_files (tuple): Tuple of (plated_holes_file, non_plated_holes_file) or None
                - project_path (Path): Path to the KiCad project directory
                - output_dir (Path): Directory where Gerbers were exported
                - error (str, optional): Error message if generation failed

        Example:
            >>> circuit = esp32_board()
            >>> result = circuit.generate_gerbers(project_name="esp32_board")
            >>> print(f"Gerbers exported to: {result['output_dir']}")
            >>> print(f"Files: {len(result['gerber_files'])} Gerber files")

        Requirements:
            - KiCad 8.0 or later
            - kicad-cli must be available in PATH
            - Circuit must be complete with all components and connections

        Notes:
            - First run generates full KiCad project including PCB (slower)
            - Subsequent runs reuse existing project (faster)
            - Default layers: F.Cu, B.Cu, F.Mask, B.Mask, F.SilkS, B.SilkS, F.Paste, B.Paste, Edge.Cuts
            - Gerbers use standard Protel file extension format (.gbr, .gbl, etc.)
            - Compatible with JLCPCB, PCBWay, OSH Park, and most PCB manufacturers
        """
        # Determine project name
        if project_name is None:
            project_name = self.name

        # Determine output directory
        if output_dir is None:
            output_path = Path(project_name) / "gerbers"
        else:
            output_path = Path(output_dir)

        try:
            # Generate full KiCad project (including PCB) if needed
            project_path = Path(project_name).resolve()
            project_base_name = self.name
            pcb_file = project_path / f"{project_base_name}.kicad_pcb"

            if not pcb_file.exists():
                context_logger.info(
                    "Generating complete KiCad project for Gerber export",
                    component="CIRCUIT",
                    circuit_name=self.name,
                    project_name=project_name,
                )

                project_result = self.generate_kicad_project(
                    project_name=project_name,
                    generate_pcb=True,  # Need PCB for Gerber export
                )

                if not project_result.get("success"):
                    error_msg = f"Failed to generate KiCad project: {project_result.get('error')}"
                    context_logger.error(
                        error_msg, component="CIRCUIT", project_name=project_name
                    )
                    return {"success": False, "error": error_msg}

            else:
                context_logger.debug(
                    "Using existing KiCad project for Gerber export",
                    component="CIRCUIT",
                    project_path=str(project_path),
                )

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            context_logger.info(
                "Exporting Gerber files",
                component="CIRCUIT",
                pcb_file=str(pcb_file),
                output_dir=str(output_path),
            )

            # Import PCB utilities for Gerber export
            from ..pcb.kicad_cli import get_kicad_cli

            cli = get_kicad_cli()

            # Export Gerbers with standard layer set
            standard_layers = [
                "F.Cu",          # Front copper
                "B.Cu",          # Back copper
                "F.Mask",        # Front solder mask
                "B.Mask",        # Back solder mask
                "F.SilkS",       # Front silkscreen
                "B.SilkS",       # Back silkscreen
                "F.Paste",       # Front solder paste
                "B.Paste",       # Back solder paste
                "Edge.Cuts",     # Board outline
            ]

            gerber_files = cli.export_gerbers(
                pcb_file=pcb_file,
                output_dir=output_path,
                layers=standard_layers,
                protel_extensions=True,  # Use .gbr, .gbl format for compatibility
            )

            context_logger.info(
                "Gerber export successful",
                component="CIRCUIT",
                gerber_count=len(gerber_files),
                output_dir=str(output_path),
            )

            # Export drill files if requested
            drill_files = None
            if include_drill:
                context_logger.debug(
                    "Exporting drill files",
                    component="CIRCUIT",
                    format=drill_format,
                )

                drill_files = cli.export_drill(
                    pcb_file=pcb_file,
                    output_dir=output_path,
                    format=drill_format,
                    units="mm",
                )

            return {
                "success": True,
                "gerber_files": gerber_files,
                "drill_files": drill_files,
                "project_path": project_path,
                "output_dir": output_path,
            }

        except Exception as e:
            error_msg = f"Failed to generate Gerbers: {e}"
            context_logger.error(
                error_msg, component="CIRCUIT", exception=str(e)
            )
            return {"success": False, "error": error_msg}

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
    def nets(self):
        """
        Return a dictionary of all nets in this circuit.

        Returns:
            Dict[str, Net]: Dictionary of nets keyed by net name
        """
        return self._nets
