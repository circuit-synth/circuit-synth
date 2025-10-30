"""
PCB Synchronizer for Circuit Synth.

This module synchronizes KiCad PCB files with updated schematics, preserving
manual footprint placements while adding/removing/updating components.

Mirrors the schematic synchronizer architecture but for PCB operations.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import kicad_sch_api as ksa
from kicad_pcb_api import PCBBoard

logger = logging.getLogger(__name__)


@dataclass
class PCBSyncReport:
    """Report of PCB synchronization results."""

    matched: Dict[str, str] = field(default_factory=dict)  # schematic_ref -> pcb_ref
    added: List[str] = field(default_factory=list)  # New footprints added
    removed: List[str] = field(default_factory=list)  # Footprints removed
    updated: List[str] = field(default_factory=list)  # Footprints updated
    preserved: List[str] = field(default_factory=list)  # Positions preserved
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "matched": len(self.matched),
            "added": len(self.added),
            "removed": len(self.removed),
            "updated": len(self.updated),
            "preserved": len(self.preserved),
            "errors": len(self.errors),
        }


class PCBSynchronizer:
    """
    Synchronize KiCad PCB with updated schematic/netlist.

    This class mirrors the schematic synchronizer pattern but for PCB operations.
    It preserves manual footprint placements while adding/removing components.
    """

    def __init__(self, pcb_path: str, project_dir: Path, project_name: str):
        """
        Initialize the PCB synchronizer.

        Args:
            pcb_path: Path to the KiCad PCB file
            project_dir: Directory containing the KiCad project
            project_name: Name of the project
        """
        self.pcb_path = Path(pcb_path)
        self.project_dir = Path(project_dir)
        self.project_name = project_name

        logger.info(f"🔍 Initializing PCBSynchronizer")
        logger.debug(f"  PCB path: {self.pcb_path}")
        logger.debug(f"  Project dir: {self.project_dir}")
        logger.debug(f"  Project name: {self.project_name}")

        # Load existing PCB
        if not self.pcb_path.exists():
            raise FileNotFoundError(f"PCB file not found: {self.pcb_path}")

        logger.info(f"📄 Loading existing PCB: {self.pcb_path}")
        self.pcb = PCBBoard(str(self.pcb_path))
        logger.info(f"✅ PCB loaded with {len(self.pcb.footprints)} existing footprints")

    def sync_with_schematics(self) -> PCBSyncReport:
        """
        Update PCB based on schematic changes.

        Process:
        1. Extract components from all schematics
        2. Match with existing PCB footprints
        3. Add new footprints (default position)
        4. Remove deleted footprints
        5. Update footprint properties
        6. Update netlist connections
        7. PRESERVE existing positions/rotations

        Returns:
            PCBSyncReport with synchronization results
        """
        logger.info("="*70)
        logger.info("🔄 Starting PCB Synchronization")
        logger.info("="*70)

        report = PCBSyncReport()

        try:
            # Step 1: Extract components from schematics
            logger.info("📋 Step 1: Extracting components from schematics")
            schematic_components = self._extract_components_from_schematics()
            logger.info(f"  Found {len(schematic_components)} components in schematics")

            # Step 2: Get existing PCB footprints
            logger.info("📦 Step 2: Getting existing PCB footprints")
            pcb_footprints = self._get_existing_footprints()
            logger.info(f"  Found {len(pcb_footprints)} existing footprints in PCB")

            # Step 3: Match components
            logger.info("🔗 Step 3: Matching schematic components with PCB footprints")
            matches = self._match_components(schematic_components, pcb_footprints)
            logger.info(f"  Matched {len(matches)} components")

            # Step 4: Add new footprints
            logger.info("➕ Step 4: Adding new footprints")
            self._add_new_footprints(schematic_components, matches, report)
            logger.info(f"  Added {len(report.added)} new footprints")

            # Step 5: Remove deleted footprints
            logger.info("➖ Step 5: Removing deleted footprints")
            self._remove_deleted_footprints(pcb_footprints, matches, report)
            logger.info(f"  Removed {len(report.removed)} deleted footprints")

            # Step 6: Update existing footprints
            logger.info("🔧 Step 6: Updating existing footprints")
            self._update_existing_footprints(schematic_components, matches, report)
            logger.info(f"  Updated {len(report.updated)} footprints")

            # Step 7: Update netlist connections
            logger.info("🔌 Step 7: Updating netlist connections")
            self._update_netlist()
            logger.info(f"  Netlist updated")

            # Step 8: Save PCB
            logger.info("💾 Step 8: Saving PCB")
            self.pcb.save(str(self.pcb_path))
            logger.info(f"✅ PCB saved: {self.pcb_path}")

            logger.info("="*70)
            logger.info("📊 Synchronization Summary")
            logger.info("="*70)
            logger.info(f"  Matched:   {len(matches)}")
            logger.info(f"  Added:     {len(report.added)}")
            logger.info(f"  Removed:   {len(report.removed)}")
            logger.info(f"  Updated:   {len(report.updated)}")
            logger.info(f"  Preserved: {len(report.preserved)}")
            logger.info(f"  Errors:    {len(report.errors)}")
            logger.info("="*70)

            return report

        except Exception as e:
            logger.error(f"❌ PCB synchronization failed: {e}", exc_info=True)
            report.errors.append(str(e))
            raise

    def _extract_components_from_schematics(self) -> List[Dict[str, Any]]:
        """
        Extract component information from all schematic files.

        Returns:
            List of component dictionaries with reference, lib_id, value, footprint, etc.
        """
        components = []

        # Read all schematic files
        sch_files = list(self.project_dir.glob("*.kicad_sch"))
        logger.debug(f"🔍 Found {len(sch_files)} schematic files")

        for sch_file in sch_files:
            try:
                logger.debug(f"  Reading: {sch_file.name}")
                schematic = ksa.Schematic.load(str(sch_file))

                # Determine hierarchical path
                if sch_file.stem == self.project_name:
                    hierarchical_path = "/"
                else:
                    hierarchical_path = f"/{sch_file.stem}/"

                # Extract components
                for comp in schematic.components:
                    if comp.reference and not comp.reference.startswith("#"):
                        comp_info = {
                            "reference": comp.reference,
                            "lib_id": comp.lib_id,
                            "value": comp.value,
                            "footprint": comp.footprint,
                            "hierarchical_path": hierarchical_path,
                            "schematic": sch_file.stem,
                        }
                        components.append(comp_info)
                        logger.debug(f"    • {comp.reference}: {comp.footprint}")

            except Exception as e:
                logger.error(f"❌ Error reading schematic {sch_file}: {e}")
                continue

        return components

    def _get_existing_footprints(self) -> Dict[str, Any]:
        """
        Get existing footprints from PCB.

        Returns:
            Dictionary mapping reference to footprint object
        """
        footprints = {}

        for fp in self.pcb.footprints:
            footprints[fp.reference] = {
                "footprint": fp,
                "reference": fp.reference,
                "library": fp.library,
                "name": fp.name,
                "position": (fp.position.x, fp.position.y),
                "rotation": fp.rotation,
                "layer": fp.layer,
            }
            logger.debug(f"  • {fp.reference}: {fp.library}:{fp.name} at ({fp.position.x:.2f}, {fp.position.y:.2f})")

        return footprints

    def _match_components(
        self,
        schematic_components: List[Dict[str, Any]],
        pcb_footprints: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Match schematic components with PCB footprints by reference.

        Args:
            schematic_components: List of components from schematics
            pcb_footprints: Dictionary of existing PCB footprints

        Returns:
            Dictionary mapping schematic reference to PCB reference (should be identical)
        """
        matches = {}

        for comp in schematic_components:
            ref = comp["reference"]
            if ref in pcb_footprints:
                matches[ref] = ref
                logger.debug(f"  ✓ Matched: {ref}")
            else:
                logger.debug(f"  ✗ Not in PCB: {ref}")

        return matches

    def _add_new_footprints(
        self,
        schematic_components: List[Dict[str, Any]],
        matches: Dict[str, str],
        report: PCBSyncReport
    ):
        """
        Add new footprints for components that don't exist in PCB.

        Args:
            schematic_components: List of components from schematics
            matches: Dictionary of matched components
            report: Sync report to update
        """
        for comp in schematic_components:
            ref = comp["reference"]
            footprint = comp.get("footprint")

            # Skip if already in PCB or no footprint specified
            if ref in matches:
                continue

            if not footprint:
                logger.warning(f"⚠️  {ref} has no footprint, skipping")
                report.errors.append(f"{ref}: No footprint specified")
                continue

            try:
                logger.info(f"  ➕ Adding {ref}: {footprint}")

                # Add footprint at default position (50mm, 50mm)
                fp = self.pcb.add_footprint_from_library(
                    footprint_id=footprint,
                    reference=ref,
                    x=50.0,
                    y=50.0,
                    rotation=0.0,
                    value=comp.get("value", ""),
                )

                if fp:
                    # Store hierarchical path if available
                    if comp.get("hierarchical_path"):
                        fp.path = comp["hierarchical_path"]

                    report.added.append(ref)
                    logger.debug(f"    ✅ Added at (50.0, 50.0)")
                else:
                    logger.error(f"    ❌ Failed to add {ref}")
                    report.errors.append(f"{ref}: Failed to add footprint")

            except Exception as e:
                logger.error(f"    ❌ Error adding {ref}: {e}")
                report.errors.append(f"{ref}: {str(e)}")

    def _remove_deleted_footprints(
        self,
        pcb_footprints: Dict[str, Any],
        matches: Dict[str, str],
        report: PCBSyncReport
    ):
        """
        Remove footprints that no longer exist in schematic.

        Args:
            pcb_footprints: Dictionary of existing PCB footprints
            matches: Dictionary of matched components
            report: Sync report to update
        """
        for ref, fp_info in pcb_footprints.items():
            # Skip if matched (exists in schematic)
            if ref in matches:
                continue

            # Skip power symbols and special components
            if ref.startswith("#PWR") or ref.startswith("#FL"):
                logger.debug(f"  Skipping special component: {ref}")
                continue

            try:
                logger.info(f"  ➖ Removing {ref}: no longer in schematic")

                # Remove footprint from PCB
                self.pcb.footprints.remove(fp_info["footprint"])
                report.removed.append(ref)
                logger.debug(f"    ✅ Removed")

            except Exception as e:
                logger.error(f"    ❌ Error removing {ref}: {e}")
                report.errors.append(f"{ref}: {str(e)}")

    def _update_existing_footprints(
        self,
        schematic_components: List[Dict[str, Any]],
        matches: Dict[str, str],
        report: PCBSyncReport
    ):
        """
        Update properties of existing footprints (preserve positions).

        Args:
            schematic_components: List of components from schematics
            matches: Dictionary of matched components
            report: Sync report to update
        """
        # Create lookup dictionary for schematic components
        sch_lookup = {comp["reference"]: comp for comp in schematic_components}

        for ref in matches.keys():
            sch_comp = sch_lookup.get(ref)
            if not sch_comp:
                continue

            # Get footprint from PCB
            pcb_fp = None
            for fp in self.pcb.footprints:
                if fp.reference == ref:
                    pcb_fp = fp
                    break

            if not pcb_fp:
                logger.warning(f"⚠️  Matched component {ref} not found in PCB")
                continue

            # Check if value changed
            sch_value = sch_comp.get("value", "")
            if pcb_fp.value != sch_value:
                logger.debug(f"  🔧 Updating {ref} value: {pcb_fp.value} → {sch_value}")
                pcb_fp.value = sch_value

                # Also update the Value property in properties list
                for prop in pcb_fp.properties:
                    if prop.name == "Value":
                        prop.value = sch_value
                        break

                report.updated.append(ref)
            else:
                # Position preserved, no changes needed
                report.preserved.append(ref)
                logger.debug(f"  ✓ Preserved: {ref} at ({pcb_fp.position.x:.2f}, {pcb_fp.position.y:.2f})")

    def _update_netlist(self):
        """
        Update netlist connections from schematic netlist file.

        This applies the netlist to update pad-to-net assignments.
        Ported from pcb_generator.py _apply_netlist_to_pcb()
        """
        # Import at method level to avoid circular imports
        import re
        from collections import defaultdict
        from kicad_pcb_api.core.types import Net

        # Find netlist file - check multiple locations
        netlist_path = self.project_dir / f"{self.project_name}.net"
        if not netlist_path.exists():
            netlist_path = self.project_dir.parent / f"{self.project_name}.net"
        if not netlist_path.exists():
            netlist_path = self.project_dir.parent / f"circuit_synth_{self.project_name}.net"
        if not netlist_path.exists():
            netlist_path = self.project_dir.parent.parent / f"{self.project_name}.net"

        if not netlist_path.exists():
            logger.warning(f"⚠️  No netlist file found for {self.project_name}")
            logger.info("  Skipping netlist update")
            return

        logger.debug(f"  Reading netlist: {netlist_path}")

        try:
            # Parse netlist file
            with open(netlist_path, "r") as f:
                content = f.read()

            # Pattern to match net definitions with multi-line support
            net_pattern = r'\(net\s+\(code\s+"?\d+"?\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|$)'
            net_matches = re.findall(net_pattern, content, re.DOTALL)

            # Track assigned pads and net mapping
            assigned_pads = set()
            nets_created = 0
            net_groups = defaultdict(list)
            net_mapping = {}

            # First pass: group nets by base name
            for net_name, net_content in net_matches:
                if "/" in net_name:
                    base_name = net_name.split("/")[-1]
                    net_groups[base_name].append((net_name, net_content))
                else:
                    net_groups[net_name].append((net_name, net_content))

            # Second pass: determine which nets should be merged
            for base_name, net_list in net_groups.items():
                if len(net_list) > 1:
                    logger.debug(f"  Merging {len(net_list)} nets with base name '{base_name}'")
                    target_net = min([net[0] for net in net_list], key=len)
                    if all("/" in net[0] for net in net_list):
                        target_net = base_name
                    for net_name, _ in net_list:
                        net_mapping[net_name] = target_net
                else:
                    net_name = net_list[0][0]
                    net_mapping[net_name] = net_name

            # Third pass: create nets and assign pads
            for net_name, net_content in net_matches:
                flattened_net_name = net_mapping.get(net_name, net_name)

                # Extract component references and pad numbers
                node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
                nodes = re.findall(node_pattern, net_content)

                if not nodes:
                    continue

                # Clean up hierarchical references
                clean_nodes = []
                for ref, pin in nodes:
                    clean_ref = ref.split("/")[-1] if "/" in ref else ref
                    clean_nodes.append((clean_ref, pin))

                # Check if net already exists
                existing_net = self.pcb.get_net_by_name(flattened_net_name)
                if existing_net:
                    net_num = existing_net.number
                else:
                    net_num = self.pcb.add_net(flattened_net_name)
                    nets_created += 1
                    logger.debug(f"    Created net {net_num}: '{flattened_net_name}'")

                # Assign all pads in this net
                for ref, pad_num in clean_nodes:
                    footprint = self.pcb.get_footprint(ref)
                    if not footprint:
                        logger.debug(f"    Footprint {ref} not found, skipping")
                        continue

                    # Find ALL pads with this number
                    pads_found = 0
                    for pad in footprint.pads:
                        if pad.number == pad_num:
                            pad.net = net_num
                            pad.net_name = flattened_net_name
                            pads_found += 1

                    if pads_found > 0:
                        assigned_pads.add((ref, pad_num))

            logger.debug(f"  Created {nets_created} nets, assigned {len(assigned_pads)} pads")

            # Fourth pass: create unique nets for unconnected pads
            unconnected_count = 0
            for footprint in self.pcb.pcb_data["footprints"]:
                for pad in footprint.pads:
                    if (footprint.reference, pad.number) not in assigned_pads:
                        if pad.net is None:
                            pin_name = getattr(pad, "pin_name", f"Pad{pad.number}")
                            unconnected_net_name = f"unconnected-({footprint.reference}-{pin_name}-Pad{pad.number})"
                            net_num = len(self.pcb.pcb_data["nets"])
                            new_net = Net(number=net_num, name=unconnected_net_name)
                            self.pcb.pcb_data["nets"].append(new_net)
                            pad.net = net_num
                            pad.net_name = unconnected_net_name
                            unconnected_count += 1

            if unconnected_count > 0:
                logger.debug(f"  Created {unconnected_count} nets for unconnected pads")

            logger.info(f"  ✅ Netlist applied: {nets_created} nets created, {len(assigned_pads)} pads assigned")

        except Exception as e:
            logger.error(f"❌ Error updating netlist: {e}", exc_info=True)
