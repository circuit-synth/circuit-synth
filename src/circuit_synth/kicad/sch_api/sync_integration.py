"""
Integration module for connecting the new KiCad Schematic API with existing synchronization system.

This module provides adapters and utilities to use the new ComponentManager and related
APIs with the existing SchematicSynchronizer and SchematicUpdater.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..sch_editor.schematic_editor import SchematicEditor
from ..sch_editor.schematic_reader import SchematicReader, SchematicSymbol
from ..sch_sync.schematic_updater import ComponentUpdate, PlacementInfo
from ..sch_sync.synchronizer import SchematicSynchronizer
from .bulk_operations import BulkOperations
from .component_manager import ComponentManager
from .component_search import ComponentSearch

logger = logging.getLogger(__name__)


class SyncIntegration:
    """
    Integrates the new Component API with the existing synchronization system.

    This class provides methods to:
    - Use ComponentManager for component operations during sync
    - Convert between sync report formats and API calls
    - Maintain compatibility with existing workflows
    """

    def __init__(self, project_path: str):
        """
        Initialize the sync integration.

        Args:
            project_path: Path to the KiCad project file (.kicad_pro)
        """
        self.project_path = Path(project_path)
        self.component_manager = None
        self.synchronizer = None
        self._schematic_path = None

        logger.info(f"SyncIntegration initialized for project: {project_path}")

    def setup_from_project(self) -> bool:
        """
        Set up the integration by loading the project and initializing managers.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Initialize synchronizer
            self.synchronizer = SchematicSynchronizer(
                str(self.project_path), preserve_user_components=True
            )

            # Find the schematic file
            self._schematic_path = self._find_schematic_file()
            if not self._schematic_path:
                logger.error("No schematic file found")
                return False

            # Initialize component manager
            self.component_manager = ComponentManager(str(self._schematic_path))

            logger.info("Setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    def sync_with_circuit_using_api(self, circuit) -> Dict[str, Any]:
        """
        Perform synchronization using the new Component API.

        This method:
        1. Uses the synchronizer to determine what changes are needed
        2. Applies changes using the ComponentManager API
        3. Returns a comprehensive sync report

        Args:
            circuit: Circuit Synth circuit object

        Returns:
            Sync report dictionary
        """
        if not self.synchronizer or not self.component_manager:
            raise RuntimeError(
                "Integration not properly set up. Call setup_from_project() first."
            )

        logger.info("Starting synchronization with Component API")

        # Step 1: Get sync report from synchronizer
        sync_report = self.synchronizer.sync_with_circuit(circuit)

        # Step 2: Apply changes using Component API
        changes_applied = self._apply_sync_changes(sync_report)

        # Step 3: Save the schematic
        if changes_applied > 0:
            self.component_manager.save()
            logger.info(f"Saved schematic with {changes_applied} changes")
        else:
            logger.info("No changes to save")

        # Add API usage info to report
        sync_report["api_integration"] = {
            "changes_applied": changes_applied,
            "component_manager_used": True,
            "schematic_path": str(self._schematic_path),
        }

        return sync_report

    def _apply_sync_changes(self, sync_report: Dict[str, Any]) -> int:
        """
        Apply synchronization changes using the Component API.

        Args:
            sync_report: Synchronization report from SchematicSynchronizer

        Returns:
            Number of changes applied
        """
        changes_applied = 0

        # Handle components to add
        for add_info in sync_report.get("components_to_add", []):
            if self._add_component_from_sync(add_info):
                changes_applied += 1

        # Handle components to modify
        for mod_info in sync_report.get("components_to_modify", []):
            if self._modify_component_from_sync(mod_info):
                changes_applied += 1

        # Handle components to remove (if not preserving)
        if not self.synchronizer.preserve_user_components:
            for remove_info in sync_report.get("components_to_remove", []):
                if self._remove_component_from_sync(remove_info):
                    changes_applied += 1

        return changes_applied

    def _add_component_from_sync(self, add_info: Dict[str, Any]) -> bool:
        """
        Add a component using the Component API based on sync info.

        Args:
            add_info: Dictionary with component information to add

        Returns:
            True if component was added successfully
        """
        try:
            component_data = add_info.get("component", {})
            circuit_id = add_info.get("circuit_id", "")

            # Extract component properties
            lib_id = component_data.get("symbol", "Device:R")
            reference = component_data.get("reference", circuit_id)
            value = component_data.get("value", "")
            footprint = component_data.get("footprint")

            # Use ComponentManager to add the component
            new_component = self.component_manager.add_component(
                library_id=lib_id,
                reference=reference,
                value=value,
                placement_strategy="edge_right",  # Place new components at right edge
                footprint=footprint,
            )

            if new_component:
                logger.info(f"Added component {reference} using Component API")
                return True
            else:
                logger.error(f"Failed to add component {reference}")
                return False

        except Exception as e:
            logger.error(f"Error adding component: {e}")
            return False

    def _modify_component_from_sync(self, mod_info: Dict[str, Any]) -> bool:
        """
        Modify a component using the Component API based on sync info.

        Args:
            mod_info: Dictionary with component modification information

        Returns:
            True if component was modified successfully
        """
        try:
            reference = mod_info.get("reference", "")
            updates = mod_info.get("updates", {})

            # Build properties dictionary for update
            properties = {}

            # Handle value update
            if "value" in updates:
                properties["value"] = updates["value"].get("new", "")

            # Handle footprint update
            if "footprint" in updates:
                properties["Footprint"] = updates["footprint"].get("new", "")

            # Handle connection changes (just log for now since we're not doing wires)
            if "connections" in updates:
                logger.info(
                    f"Component {reference} has connection changes (not handled yet)"
                )

            # Use ComponentManager to update properties
            if properties:
                success = self.component_manager.update_component_properties(
                    reference=reference, **properties
                )

                if success:
                    logger.info(f"Modified component {reference} using Component API")
                    return True
                else:
                    logger.error(f"Failed to modify component {reference}")
                    return False
            else:
                logger.debug(f"No property changes for component {reference}")
                return False

        except Exception as e:
            logger.error(f"Error modifying component: {e}")
            return False

    def _remove_component_from_sync(self, remove_info: Dict[str, Any]) -> bool:
        """
        Remove a component using the Component API based on sync info.

        Args:
            remove_info: Dictionary with component removal information

        Returns:
            True if component was removed successfully
        """
        try:
            reference = remove_info.get("reference", "")

            # Use ComponentManager to remove the component
            success = self.component_manager.remove_component(reference)

            if success:
                logger.info(f"Removed component {reference} using Component API")
                return True
            else:
                logger.error(f"Failed to remove component {reference}")
                return False

        except Exception as e:
            logger.error(f"Error removing component: {e}")
            return False

    def _find_schematic_file(self) -> Optional[Path]:
        """Find the main schematic file for the project."""
        # Look for .kicad_sch file with same name as project
        project_name = self.project_path.stem
        schematic_path = self.project_path.parent / f"{project_name}.kicad_sch"

        if schematic_path.exists():
            return schematic_path

        # Look for any .kicad_sch file
        sch_files = list(self.project_path.parent.glob("*.kicad_sch"))
        if sch_files:
            return sch_files[0]

        return None

    def demonstrate_api_features(self) -> None:
        """
        Demonstrate various Component API features.

        This method shows how to use the API for various operations
        beyond basic synchronization.
        """
        if not self.component_manager:
            logger.error("Component manager not initialized")
            return

        logger.info("=== Demonstrating Component API Features ===")

        # 1. Search for components
        search = ComponentSearch(
            self.component_manager.reader, self.component_manager.editor
        )

        # Find all resistors
        resistors = search.find_by_reference_pattern("R.*")
        logger.info(f"Found {len(resistors)} resistors")

        # Find components by value
        ten_k_components = search.find_by_value("10k")
        logger.info(f"Found {len(ten_k_components)} components with value '10k'")

        # 2. Bulk operations
        if resistors:
            bulk_ops = BulkOperations(
                self.component_manager.reader, self.component_manager.editor
            )

            # Example: Align resistors horizontally
            refs = [r.reference for r in resistors[:3]]  # First 3 resistors
            if len(refs) >= 2:
                success = bulk_ops.align_horizontal(refs, y_position=50.0)
                if success:
                    logger.info(f"Aligned {len(refs)} resistors horizontally")

        # 3. Clone a component
        if resistors:
            first_resistor = resistors[0]
            cloned = self.component_manager.clone_component(
                reference=first_resistor.reference,
                new_reference="R99",
                offset=(20, 0),  # 20mm to the right
            )
            if cloned:
                logger.info(f"Cloned {first_resistor.reference} as R99")

        # 4. Move components
        if len(resistors) > 1:
            second_resistor = resistors[1]
            moved = self.component_manager.move_component(
                reference=second_resistor.reference, new_position=(100, 100)
            )
            if moved:
                logger.info(f"Moved {second_resistor.reference} to (100, 100)")

        logger.info("=== API Demonstration Complete ===")


def create_sync_integration(project_path: str) -> SyncIntegration:
    """
    Factory function to create and set up a SyncIntegration instance.

    Args:
        project_path: Path to KiCad project file

    Returns:
        Configured SyncIntegration instance

    Raises:
        RuntimeError: If setup fails
    """
    integration = SyncIntegration(project_path)
    if not integration.setup_from_project():
        raise RuntimeError("Failed to set up sync integration")
    return integration
