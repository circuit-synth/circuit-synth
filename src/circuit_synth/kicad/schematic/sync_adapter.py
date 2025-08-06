"""
Adapter to make APISynchronizer compatible with existing interfaces.
"""

from pathlib import Path
from typing import Any, Dict, List

from .synchronizer import APISynchronizer


class SyncAdapter:
    """
    Adapts APISynchronizer to work with existing SchematicSynchronizer interface.
    """

    def __init__(
        self,
        project_path: str,
        match_criteria: List[str] = None,
        preserve_user_components: bool = True,
    ):
        """Initialize adapter with compatibility interface."""
        self.project_path = Path(project_path)
        self.preserve_user_components = preserve_user_components

        # Find schematic file
        schematic_path = self._find_schematic()

        # Create API synchronizer
        self.api_sync = APISynchronizer(
            str(schematic_path), preserve_user_components=preserve_user_components
        )

    def _find_schematic(self) -> Path:
        """Find the schematic file with actual components (not just cover sheet)."""
        project_name = self.project_path.stem
        main_schematic_path = self.project_path.parent / f"{project_name}.kicad_sch"

        # Check if the main schematic has components
        if main_schematic_path.exists():
            if self._schematic_has_components(main_schematic_path):
                return main_schematic_path
            else:
                # Main schematic appears to be a cover sheet, look for circuit schematics
                pass

        # Look for schematic files that contain actual components
        sch_files = list(self.project_path.parent.glob("*.kicad_sch"))
        for sch_file in sch_files:
            if sch_file != main_schematic_path and self._schematic_has_components(
                sch_file
            ):
                return sch_file

        # Fallback: use the main schematic even if it's a cover sheet
        if main_schematic_path.exists():
            print(
                f"[WARNING] No circuit schematics found with components, using main schematic: {main_schematic_path}"
            )
            return main_schematic_path

        # Last resort: use any schematic file
        if sch_files:
            print(f"[WARNING] Main schematic not found, using: {sch_files[0]}")
            return sch_files[0]

        raise FileNotFoundError("No schematic file found")

    def _schematic_has_components(self, schematic_path: Path) -> bool:
        """Check if a schematic file contains actual components (not just a cover sheet)."""
        try:
            # Use the parser to check for components
            from ..core.s_expression import SExpressionParser

            parser = SExpressionParser()
            schematic = parser.parse_file(str(schematic_path))

            # Check if schematic has non-power components
            component_count = 0
            for comp in schematic.components:
                # Skip power symbols
                if comp.lib_id and not any(
                    pwr in comp.lib_id for pwr in ["power:", "Power:", "#PWR", "#FLG"]
                ):
                    component_count += 1

            return component_count > 0

        except Exception as e:
            print(f"[ERROR] Failed to check schematic {schematic_path}: {e}")
            return False

    def sync_with_circuit(self, circuit) -> Dict[str, Any]:
        """
        Synchronize using the same interface as SchematicSynchronizer.
        """
        # Use API synchronizer
        report = self.api_sync.sync_with_circuit(circuit)

        # Convert to expected format
        result = report.to_dict()

        return result

    def synchronize(self, circuit) -> Dict[str, Any]:
        """Legacy method name compatibility."""
        return self.sync_with_circuit(circuit)
