# FILE: src/circuit_synth/core/netlist_exporter.py

import logging
import json
import tempfile
import os
from typing import List, Dict, Optional, Any
from pathlib import Path

from .exception import CircuitSynthError
from .json_encoder import CircuitSynthJSONEncoder

logger = logging.getLogger(__name__)

# Use Rust implementation for netlist processing (Phase 4 migration)
# Temporarily disabled due to PyO3 linking issues - using Python fallback
RUST_NETLIST_AVAILABLE = False
try:
    # Temporarily commented out to force Python fallback
    # from rust_netlist_processor import RustNetlistProcessor, convert_json_to_netlist
    # RUST_NETLIST_AVAILABLE = True
    raise ImportError("Rust netlist processor temporarily disabled")
except ImportError:
    # Use the proper KiCad netlist exporter instead of simple fallback
    try:
        from ..kicad.netlist_exporter import convert_json_to_netlist
        RUST_NETLIST_AVAILABLE = False
        logger.debug("Using KiCad netlist exporter for netlist generation")
    except ImportError:
        # Final fallback to simple implementation
        def convert_json_to_netlist(json_data, output_path):
            """Simple netlist conversion for open source version."""
            # Basic implementation that writes a simple netlist format
            with open(output_path, 'w') as f:
                f.write("# Simple netlist format\n")
                if 'components' in json_data:
                    for comp in json_data['components']:
                        f.write(f"# Component: {comp.get('ref', 'Unknown')}\n")
                if 'nets' in json_data:
                    for net in json_data['nets']:
                        f.write(f"# Net: {net.get('name', 'Unknown')}\n")
            return True
        
        RUST_NETLIST_AVAILABLE = False

class NetlistExporter:
    """
    Handles all export functionality for Circuit objects.
    
    This class is responsible for:
    - Text netlist generation
    - JSON export (hierarchical and flattened)
    - KiCad netlist export
    - KiCad project generation
    - Data transformation (to_dict, to_flattened_list)
    """
    
    def __init__(self, circuit):
        """
        Initialize the exporter with a circuit reference.
        
        Args:
            circuit: The Circuit object to export
        """
        self.circuit = circuit
    
    def generate_text_netlist(self) -> str:
        """
        Generate a textual netlist for display or debugging.
        """
        logger.info("NetlistExporter.generate_text_netlist: generating netlist for '%s'", self.circuit.name)
        return self.generate_full_netlist()

    def generate_full_netlist(self) -> str:
        """
        Print a hierarchical netlist showing:
          1) Each circuit + subcircuit (name, components, and optional description)
          2) A single combined net listing from all circuits
        """
        lines = []
        logger.debug("NetlistExporter.generate_full_netlist: building full netlist for '%s'", self.circuit.name)

        all_nets = {}

        def collect_nets(circ):
            for net in circ._nets.values():
                if net.name not in all_nets:
                    all_nets[net.name] = set()
                for pin in net._pins:
                    pin_str = f"{pin._component.ref}.{pin._component_pin_id}"
                    all_nets[net.name].add(pin_str)
            for sc in circ._subcircuits:
                collect_nets(sc)

        def print_circuit(circ, indent_level=0):
            indent = "  " * indent_level
            lines.append(f"{indent}CIRCUIT: {circ.name}")
            if circ.description:
                # Print docstring/description if present
                desc = circ.description.strip()
                lines.append(f"{indent}  Description: {desc}")
            lines.append(f"{indent}Components:")

            if circ._components:
                for comp in circ._components.values():
                    lines.append(f"{indent}  {comp.symbol} {comp.ref}")
            else:
                lines.append(f"{indent}  (none)")

            for sc in circ._subcircuits:
                lines.append("")
                print_circuit(sc, indent_level + 1)

        print_circuit(self.circuit)
        collect_nets(self.circuit)

        lines.append("")
        lines.append("Combined Nets:")
        if all_nets:
            for net_name, pin_set in sorted(all_nets.items()):
                pin_list = sorted(pin_set)
                lines.append(f"  Net {net_name} => pins={pin_list}")
        else:
            lines.append("  (none)")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a hierarchical dictionary representation of this circuit,
        including subcircuits, components (as a dictionary keyed by reference),
        and net connections.

        Key point:
        We do NOT distinguish local vs. external nets.
        We simply list ALL net names that this circuit's own components use.

        NOTE: The 'components' field is intentionally structured as a dictionary
        keyed by the component reference designator (e.g., "R1", "U1"). This
        provides efficient O(1) lookup for consumers needing access by reference
        (like netlist exporters) and aligns semantically with how components
        are uniquely identified in a schematic. This is the standardized format
        for the library's intermediate JSON representation.
        """
        # TODO: Implement UUID generation and source file tracking later
        # For now, use placeholders similar to the initial exporter output
        sheet_tstamps = f"/{self.circuit.name.lower().replace(' ', '-')}-{id(self.circuit)}/" # Simple placeholder tstamp
        source_file = f"{self.circuit.name}.kicad_sch" # Placeholder source file name

        data = {
            "name": self.circuit.name,
            "description": self.circuit.description or "",
            "tstamps": sheet_tstamps, # Add sheet timestamp placeholder
            "source_file": source_file, # Add source file placeholder
            "components": {},  # Standardized: Dictionary keyed by component reference
            "nets": {},
            "subcircuits": [],
        }

        # 1) Collect all components
        for comp in self.circuit._components.values():
            data["components"][comp.ref] = comp.to_dict() # Add using ref as key

        # 2) Gather net usage only from our local components
        #    (including any net that actually comes from a parent)
        net_to_pins = {}

        for comp in self.circuit._components.values():
            for pin_obj in comp._pins.values():
                net_obj = pin_obj.net
                if net_obj is None:
                    continue
                net_name = net_obj.name
                if net_name not in net_to_pins:
                    net_to_pins[net_name] = []
                # Store full pin details needed by the exporter
                net_to_pins[net_name].append({
                    "component": comp.ref,
                    "pin": {
                        "number": pin_obj.num, # Standardize on "number" key
                        "name": pin_obj.name,
                        "func": pin_obj.func # Assuming 'func' maps to 'type' later? Check exporter.
                    }
                })

        # Store them in data["nets"]
        for net_name, pin_list in net_to_pins.items():
            data["nets"][net_name] = pin_list

        # 3) Recursively gather subcircuits
        for sc in self.circuit._subcircuits:
            exporter = NetlistExporter(sc)
            data["subcircuits"].append(exporter.to_dict())

        return data

    def generate_json_netlist(self, filename: str) -> None:
        """
        Generate a JSON representation of this circuit and its hierarchy,
        then write it out to 'filename'.
        """
        logger.info("NetlistExporter.generate_json_netlist: generating JSON netlist for '%s'", self.circuit.name)
        circuit_data = self.to_dict()
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(circuit_data, f, indent=2, cls=CircuitSynthJSONEncoder)
            logger.debug(
                "NetlistExporter.generate_json_netlist: JSON netlist written successfully to '%s'",
                filename
            )
        except Exception as e:
            logger.error("Error writing JSON netlist to '%s': %s", filename, e)
            raise CircuitSynthError(f"Could not write JSON netlist to {filename}: {e}")

    def to_flattened_list(
        self,
        parent_name: str = None,
        flattened: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build or update a shared `flattened` list of circuit data dicts. Each entry is:
          {
            "name": <circuit name>,
            "parent": <parent circuit name or None>,
            "description": <string>,
            "components": { ref: {...}, ... },
            "nets": { net_name: [ {component, pin_id}, ... ] }
          }

        This approach iterates over every local component's Pin objects to see which
        nets they are actually connected to. That way, we display all nets used by
        local components, including parent-owned nets.
        """
        if flattened is None:
            flattened = []

        circuit_data = {
            "name": self.circuit.name,
            "parent": parent_name,
            "description": self.circuit.description or "",
            "components": {},
            "nets": {}
        }

        # Collect components into a dict keyed by final reference
        for comp in self.circuit._components.values():
            circuit_data["components"][comp.ref] = {
                "symbol": comp.symbol,
                "value": comp.value,
                "footprint": comp.footprint
            }

        # Build usage-based net info
        used_nets: Dict[str, List[Dict[str, Any]]] = {}

        for comp in self.circuit._components.values():
            # IMPORTANT FIX: iterate over pin objects, not pin IDs
            # if comp._pins is dict-like {pin_id: Pin(...), ...}
            if hasattr(comp._pins, "values"):
                # assume it's a dict: pin_id -> Pin
                for pin_obj in comp._pins.values():
                    net_obj = pin_obj.net
                    if net_obj is not None:
                        net_name = net_obj.name
                        if net_name not in used_nets:
                            used_nets[net_name] = [] # Initialize if first time seeing this net
                        # Construct the full node dictionary (Structure A)
                        used_nets[net_name].append({
                            "component": comp.ref,
                            "pin": { # Corrected attributes based on Pin class
                                "number": str(pin_obj.num), # Use pin_obj.num
                                "name": pin_obj.name or "",
                                "type": pin_obj.func or "unspecified" # Use pin_obj.func
                            }
                        })
            else:
                # if comp._pins is a list or something else, handle accordingly
                for pin_obj in comp._pins:
                    net_obj = pin_obj.net
                    if net_obj is not None:
                        net_name = net_obj.name
                        # Construct the full node dictionary (Structure A)
                        used_nets.setdefault(net_name, []).append({
                            "component": comp.ref,
                            "pin": { # Corrected attributes based on Pin class
                                "number": str(pin_obj.num), # Use pin_obj.num
                                "name": pin_obj.name or "",
                                "type": pin_obj.func or "unspecified" # Use pin_obj.func
                            }
                        })

        circuit_data["nets"] = used_nets

        # Add this circuit's data to flattened
        flattened.append(circuit_data)

        # Recursively flatten subcircuits
        for sc in self.circuit._subcircuits:
            exporter = NetlistExporter(sc)
            exporter.to_flattened_list(parent_name=self.circuit.name, flattened=flattened)

        return flattened

    def generate_flattened_json_netlist(self, filename: str) -> None:
        """
        Produce a flattened JSON representation for this circuit + subcircuits.
        - "name", "parent", "description"
        - a dict of all local "components"
        - a dict of "nets" => each net_name -> [ {component, pin_id}, ... ]
        Then write it to 'filename'.
        """
        logger.info("NetlistExporter.generate_flattened_json_netlist: generating JSON netlist for '%s'", self.circuit.name)
        flattened_list = self.to_flattened_list(parent_name=None, flattened=None)

        final_json = {
            "circuits": flattened_list
        }

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(final_json, f, indent=2, cls=CircuitSynthJSONEncoder)
            logger.debug(
                "NetlistExporter.generate_flattened_json_netlist: JSON netlist written successfully to '%s'",
                filename
            )
        except Exception as e:
            logger.error("Error writing JSON netlist to '%s': %s", filename, e)
            raise CircuitSynthError(f"Could not write JSON netlist to {filename}: {e}")

    def generate_kicad_netlist(self, filename: str) -> None:
        """
        Generate a KiCad netlist (.net) file for this circuit and its hierarchy.

        This method first generates the intermediate Circuit Synth JSON representation
        to a temporary file, then calls the KiCad netlist exporter to convert
        that temporary JSON file into the final KiCad netlist format at the
        specified 'filename'.

        Args:
            filename: The path (as a string) where the output KiCad netlist
                      file should be saved.
        """
        logger.info("NetlistExporter.generate_kicad_netlist: generating KiCad netlist for '%s' to '%s'", self.circuit.name, filename)
        circuit_data = self.to_dict()
        temp_json_file = None
        try:
            # Create a temporary file to hold the intermediate JSON
            # Use delete=False and manual removal in finally block for robustness
            with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding="utf-8") as tf:
                temp_json_file = tf.name
                json.dump(circuit_data, tf, indent=2, cls=CircuitSynthJSONEncoder)
                logger.debug("Intermediate JSON written to temporary file: %s", temp_json_file)

            # Ensure the temporary file is closed before passing its path
            # The 'with' block handles closing.

            # Convert the temporary JSON to the KiCad netlist
            output_path = Path(filename)
            convert_json_to_netlist(Path(temp_json_file), output_path)
            logger.info("KiCad netlist successfully generated at '%s'", filename)

        except Exception as e:
            logger.error("Error generating KiCad netlist for '%s': %s", self.circuit.name, e, exc_info=True)
            # Re-raise to indicate failure
            raise CircuitSynthError(f"Could not generate KiCad netlist for {self.circuit.name}: {e}")
        finally:
            # Ensure the temporary file is always deleted
            if temp_json_file and os.path.exists(temp_json_file):
                try:
                    os.remove(temp_json_file)
                    logger.debug("Temporary JSON file deleted: %s", temp_json_file)
                except OSError as e:
                    logger.error("Error deleting temporary JSON file '%s': %s", temp_json_file, e)

    def generate_kicad_project(self, path: str, project_name: Optional[str] = None,
                             force_create: bool = False, preserve_user_components: bool = True) -> None:
        """
        Generate or update a KiCad project (schematic files) from this circuit.
        
        This method automatically detects if a KiCad project already exists at the
        target location and switches to update mode using the canonical matching system.
        If no project exists, it creates a new one.
        
        Args:
            path: Path where the KiCad project will be created/updated. Can be:
                  - Just a project name (e.g., "my_project") - creates in current directory
                  - A relative path (e.g., "output/my_project") - creates in specified directory
                  - An absolute path (e.g., "/home/user/projects/my_project")
            project_name: (Optional) Explicit project name. If not provided, extracted from path.
                         Kept for backward compatibility.
            force_create: (Optional) If True, always create a new project even if one exists.
                         Default is False (auto-detect and update if exists).
            preserve_user_components: (Optional) If True, components in KiCad that don't exist
                                    in the Python circuit will be preserved. If False, they
                                    will be removed. Default is True (safe mode).
        
        Examples:
            circuit = voltage_divider()
            
            # Simple usage - creates new or updates existing
            circuit.generate_kicad_project("my_project")
            
            # Creates/updates in output directory
            circuit.generate_kicad_project("output/my_project")
            
            # Force creation of new project (overwrite if exists)
            circuit.generate_kicad_project("my_project", force_create=True)
            
            # Remove components that don't exist in Python circuit
            circuit.generate_kicad_project("my_project", preserve_user_components=False)
            
            # Backward compatible usage
            circuit.generate_kicad_project("output", "my_project")
        """
        # Handle backward compatibility - if project_name is provided, use old behavior
        if project_name is not None:
            output_dir = path
            logger.info("NetlistExporter.generate_kicad_project: processing KiCad project '%s' in '%s' (legacy mode)",
                       project_name, output_dir)
        else:
            # New behavior - parse the path
            path_obj = Path(path)
            
            # Extract project name and output directory
            if path_obj.is_absolute():
                # Absolute path
                output_dir = str(path_obj.parent)
                project_name = path_obj.name
            else:
                # Relative path
                if "/" in path or "\\" in path:
                    # Path contains directory separators
                    output_dir = str(path_obj.parent)
                    project_name = path_obj.name
                else:
                    # Just a project name, use current directory
                    output_dir = "."
                    project_name = path
            
            logger.info("NetlistExporter.generate_kicad_project: processing KiCad project '%s' in '%s'",
                       project_name, output_dir)
        
        # Check if KiCad project already exists
        project_dir = Path(output_dir) / project_name
        kicad_pro_file = project_dir / f"{project_name}.kicad_pro"
        kicad_sch_file = project_dir / f"{project_name}.kicad_sch"
        
        # For update mode, we need BOTH project and schematic files to exist
        project_file_exists = kicad_pro_file.exists()
        schematic_file_exists = kicad_sch_file.exists()
        project_complete = project_file_exists and schematic_file_exists
        
        # Check for incomplete project state
        if project_file_exists and not schematic_file_exists:
            logger.warning("Incomplete KiCad project detected: .kicad_pro exists but .kicad_sch is missing")
            logger.info("Treating as new project creation")
        elif not project_file_exists and schematic_file_exists:
            logger.warning("Incomplete KiCad project detected: .kicad_sch exists but .kicad_pro is missing")
            logger.info("Treating as new project creation")
        
        if project_complete and not force_create:
            # Complete project exists - switch to update mode
            logger.info("Complete KiCad project detected at '%s' - switching to update mode", project_dir)
            
            # Import new API synchronizer
            from ..kicad_api.schematic.sync_adapter import SyncAdapter
            
            try:
                # Initialize synchronizer using new API
                synchronizer = SyncAdapter(
                    project_path=str(kicad_pro_file),
                    preserve_user_components=preserve_user_components
                )
                
                # Run synchronization with new API
                print("\n🔄 Synchronizing KiCad project with Circuit Synth...")
                logger.info("Running synchronization with new KiCad API...")
                sync_report = synchronizer.sync_with_circuit(self.circuit)
                
                # Print analysis summary
                circuit_comp_count = len(self.circuit._components)
                # Get the actual KiCad component count from the synchronizer
                # First check if we have kicad_components in the report
                kicad_comp_count = len(sync_report.get('kicad_components', {}))
                
                # If not available, calculate from other fields
                if kicad_comp_count == 0:
                    # Count matched components
                    matched_count = len(sync_report.get('matched_components', {}))
                    # Count components to preserve (these are unmatched KiCad components)
                    preserve_count = len(sync_report.get('components_to_preserve', []))
                    # Total KiCad components = matched + to preserve
                    kicad_comp_count = matched_count + preserve_count
                
                print(f"📊 Analysis:")
                print(f"   - Python circuit: {circuit_comp_count} component(s)")
                print(f"   - KiCad project: {kicad_comp_count} component(s)")
                
                # Check for discrepancies and report them
                components_to_add = sync_report.get('components_to_add', [])
                components_to_modify = sync_report.get('components_to_modify', [])
                components_to_preserve = sync_report.get('components_to_preserve', [])
                
                # Report discrepancies
                if components_to_preserve or components_to_add or components_to_modify:
                    print("\n⚠️  Discrepancies detected:")
                    
                    # Components in KiCad but not in Python
                    for comp in components_to_preserve:
                        action = "PRESERVED" if preserve_user_components else "WILL BE REMOVED"
                        print(f"   - {comp['reference']}: Exists in KiCad but not in Python circuit")
                        print(f"     → Action: {action} (preserve_user_components={preserve_user_components})")
                    
                    # Components to add
                    for comp in components_to_add:
                        print(f"   - {comp['circuit_id']}: Exists in Python but not in KiCad")
                        print(f"     → Action: WILL BE ADDED")
                    
                    # Components to modify
                    for comp in components_to_modify:
                        print(f"   - {comp['reference']}: Properties or connections differ")
                        if 'updates' in comp:
                            for prop, changes in comp['updates'].items():
                                print(f"     → {prop}: {changes.get('old', 'N/A')} → {changes.get('new', 'N/A')}")
                
                # The sync_with_circuit method only returns the report, it doesn't apply changes
                # We need to use the traditional synchronize method which includes update application
                # Or we can check if there are changes and apply them manually
                
                # Check if there are any changes to apply
                if components_to_add or components_to_modify or (components_to_preserve and not preserve_user_components):
                    print("\n📝 Applying changes to schematic...")
                    logger.info("Changes detected, applying updates to schematic...")
                    
                    # Use the traditional synchronize method which handles the complete workflow
                    # including applying updates and saving the schematic
                    full_sync_report = synchronizer.synchronize(self.circuit)
                    
                    print("✅ Schematic updated successfully")
                    logger.info("Schematic updated successfully")
                    
                    # Use the full sync report for logging
                    sync_report = full_sync_report
                else:
                    print("\n✅ No changes needed - schematic is already up to date")
                    logger.info("No changes needed - schematic is already up to date")
                
                # Print final summary
                summary = sync_report.get('summary', {})
                matched = summary.get('matched', 0)
                modified = summary.get('modified', 0)
                added = summary.get('added', 0)
                preserved = summary.get('preserved', 0)
                # Get removed count from the sync report if available
                removed = summary.get('removed', 0)
                if removed == 0 and not preserve_user_components and components_to_preserve:
                    removed = len(components_to_preserve)
                
                print("\n📋 Summary:")
                print(f"   - Matched: {matched}")
                if modified > 0:
                    print(f"   - Modified: {modified}")
                if added > 0:
                    print(f"   - Added: {added}")
                if preserved > 0:
                    print(f"   - Preserved: {preserved}")
                if removed > 0:
                    print(f"   - Removed: {removed} ({', '.join([c['reference'] for c in components_to_preserve])})")
                
                # Log summary for debugging
                logger.info("Update summary - Matched: %d, Modified: %d, Added: %d, Preserved: %d",
                           matched, modified, added, preserved)
                
            except Exception as e:
                logger.error("Error updating KiCad project: %s", e, exc_info=True)
                raise CircuitSynthError(f"Could not update KiCad project '{project_name}': {e}")
        
        else:
            # Project doesn't exist completely or force_create is True - create new project
            if force_create and project_complete:
                logger.info("Force creating new KiCad project (overwriting existing)")
            elif force_create and (project_file_exists or schematic_file_exists):
                logger.info("Force creating new KiCad project (overwriting incomplete project)")
            else:
                logger.info("Creating new KiCad project")
            
            # Create a temporary JSON file
            temp_json_file = None
            try:
                # Generate circuit data
                circuit_data = self.to_dict()
                
                # Create temporary JSON file
                with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding="utf-8") as tf:
                    temp_json_file = tf.name
                    json.dump(circuit_data, tf, indent=2, cls=CircuitSynthJSONEncoder)
                    logger.debug("Intermediate JSON written to temporary file: %s", temp_json_file)
                
                # Use the new API project generator
                from ..kicad_api.schematic.project_generator import ProjectGenerator
                gen = ProjectGenerator(output_dir, project_name)
                gen.generate_from_circuit(self.circuit)
                
                logger.info("KiCad project '%s' successfully generated in '%s'", project_name, output_dir)
                
            except Exception as e:
                logger.error("Error generating KiCad project '%s': %s", project_name, e, exc_info=True)
                raise CircuitSynthError(f"Could not generate KiCad project '{project_name}': {e}")
            finally:
                # Clean up temporary file
                if temp_json_file and os.path.exists(temp_json_file):
                    try:
                        os.remove(temp_json_file)
                        logger.debug("Temporary JSON file deleted: %s", temp_json_file)
                    except OSError as e:
                        logger.error("Error deleting temporary JSON file '%s': %s", temp_json_file, e)