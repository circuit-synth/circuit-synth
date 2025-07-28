"""KiCad project notes folder management system."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Removed import: from ..llm_analysis.models.component_cache import ComponentCache, CachedComponent, ComponentSpecs


class ProjectNotesManager:
    """Manages the circuit_synth_notes folder structure for KiCad projects."""

    NOTES_FOLDER_NAME = "circuit_synth_notes"
    FOLDER_STRUCTURE = {
        "datasheets": "PDF datasheets",
        "component_cache": "JSON files with extracted component specs",
        "analysis_history": "Previous analysis results",
        "user_notes": "User annotations and notes",
    }
    CONFIG_FILE = "config.json"

    def __init__(self, project_path: Union[str, Path]):
        """
        Initialize the ProjectNotesManager for a KiCad project.

        Args:
            project_path: Path to the KiCad project directory or .kicad_pro/.pro file
        """
        self.project_path = Path(project_path)

        # If a file was provided, get its parent directory
        if self.project_path.is_file():
            self.project_path = self.project_path.parent

        # Verify this is a KiCad project
        if not self._is_kicad_project():
            raise ValueError(f"No KiCad project found at {self.project_path}")

        self.notes_path = self.project_path / self.NOTES_FOLDER_NAME
        self.project_name = self._get_project_name()

        # Removed: Initialize component cache
        # self._component_cache: Optional[ComponentCache] = None

    def _is_kicad_project(self) -> bool:
        """Check if the given path contains a KiCad project."""
        # Check for .kicad_pro (KiCad 6+) or .pro (KiCad 5) files
        kicad_extensions = [".kicad_pro", ".pro"]
        for ext in kicad_extensions:
            if list(self.project_path.glob(f"*{ext}")):
                return True
        return False

    def _get_project_name(self) -> str:
        """Get the KiCad project name from project files."""
        # Try .kicad_pro first (KiCad 6+)
        kicad_pro_files = list(self.project_path.glob("*.kicad_pro"))
        if kicad_pro_files:
            return kicad_pro_files[0].stem

        # Fall back to .pro (KiCad 5)
        pro_files = list(self.project_path.glob("*.pro"))
        if pro_files:
            return pro_files[0].stem

        # Default to directory name
        return self.project_path.name

    def ensure_notes_folder(self) -> Path:
        """
        Create the notes folder structure if it doesn't exist.

        Returns:
            Path to the notes folder
        """
        # Create main notes folder
        self.notes_path.mkdir(exist_ok=True)

        # Create subfolders
        for folder_name, description in self.FOLDER_STRUCTURE.items():
            folder_path = self.notes_path / folder_name
            folder_path.mkdir(exist_ok=True)

            # Create a README in each folder
            readme_path = folder_path / "README.md"
            if not readme_path.exists():
                readme_content = (
                    f"# {folder_name.replace('_', ' ').title()}\n\n{description}\n"
                )
                readme_path.write_text(readme_content)

        # Create or update config file
        self._update_config()

        return self.notes_path

    def _update_config(self) -> None:
        """Create or update the configuration file."""
        config_path = self.notes_path / self.CONFIG_FILE

        config = {
            "project_name": self.project_name,
            "project_path": str(self.project_path),
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "folders": self.FOLDER_STRUCTURE,
        }

        # Preserve existing config if it exists
        if config_path.exists():
            try:
                existing_config = json.loads(config_path.read_text())
                config["created_at"] = existing_config.get(
                    "created_at", config["created_at"]
                )
            except json.JSONDecodeError:
                pass

        config_path.write_text(json.dumps(config, indent=2))

    def save_datasheet(
        self,
        pdf_path: Union[str, Path],
        component_id: str,
        part_number: Optional[str] = None,
    ) -> Path:
        """
        Save a datasheet PDF with proper naming.

        Args:
            pdf_path: Path to the PDF file to save
            component_id: Component identifier (e.g., "U1", "R5")
            part_number: Optional part number for better naming

        Returns:
            Path to the saved datasheet
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists() or not pdf_path.suffix.lower() == ".pdf":
            raise ValueError(f"Invalid PDF file: {pdf_path}")

        # Ensure notes folder exists
        self.ensure_notes_folder()

        # Generate filename
        if part_number:
            filename = f"{component_id}_{part_number}.pdf"
        else:
            filename = f"{component_id}_datasheet.pdf"

        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")

        # Copy to datasheets folder
        dest_path = self.notes_path / "datasheets" / filename
        shutil.copy2(pdf_path, dest_path)

        return dest_path

    def get_datasheet_path(self, component_id: str) -> Optional[Path]:
        """
        Get path to a component's datasheet.

        Args:
            component_id: Component identifier

        Returns:
            Path to datasheet if found, None otherwise
        """
        datasheets_path = self.notes_path / "datasheets"
        if not datasheets_path.exists():
            return None

        # Look for files starting with component_id
        for pdf_file in datasheets_path.glob(f"{component_id}*.pdf"):
            return pdf_file

        return None

    # Removed: save_component_specs method
    # def save_component_specs(self, component: CachedComponent) -> Path:
    #     """
    #     Cache extracted component specifications.
    #
    #     Args:
    #         component: CachedComponent object with specifications
    #
    #     Returns:
    #         Path to the saved cache file
    #     """
    #     # Method removed due to dependency on llm_analysis module
    #     pass

    # Removed: get_component_specs method
    # def get_component_specs(self, component_id: str) -> Optional[CachedComponent]:
    #     """
    #     Retrieve cached specs for a component.
    #
    #     Args:
    #         component_id: Component identifier
    #
    #     Returns:
    #         CachedComponent if found, None otherwise
    #     """
    #     # Method removed due to dependency on llm_analysis module
    #     pass

    # Removed: _load_component_cache method
    # def _load_component_cache(self) -> None:
    #     """Load the component cache from disk."""
    #     # Method removed due to dependency on llm_analysis module
    #     pass

    def save_analysis_result(
        self, analysis_data: Dict[str, Any], analysis_type: str = "circuit_analysis"
    ) -> Path:
        """
        Store analysis results with timestamp.

        Args:
            analysis_data: Analysis results dictionary
            analysis_type: Type of analysis (e.g., "circuit_analysis", "thermal_analysis")

        Returns:
            Path to the saved analysis file
        """
        # Ensure notes folder exists
        self.ensure_notes_folder()

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{analysis_type}_{timestamp}.json"

        # Add metadata
        analysis_record = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type,
            "project_name": self.project_name,
            "data": analysis_data,
        }

        # Save to analysis history
        analysis_path = self.notes_path / "analysis_history" / filename
        analysis_path.write_text(json.dumps(analysis_record, indent=2))

        return analysis_path

    def get_analysis_history(
        self, analysis_type: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve previous analyses.

        Args:
            analysis_type: Filter by analysis type (None for all)
            limit: Maximum number of results to return (None for all)

        Returns:
            List of analysis records, newest first
        """
        history_path = self.notes_path / "analysis_history"
        if not history_path.exists():
            return []

        analyses = []

        # Load all analysis files
        for json_file in sorted(history_path.glob("*.json"), reverse=True):
            try:
                data = json.loads(json_file.read_text())

                # Filter by type if specified
                if analysis_type and data.get("analysis_type") != analysis_type:
                    continue

                analyses.append(data)

                # Apply limit if specified
                if limit and len(analyses) >= limit:
                    break

            except (json.JSONDecodeError, KeyError):
                # Skip corrupted files
                continue

        return analyses

    def add_user_note(
        self, note_title: str, note_content: str, component_id: Optional[str] = None
    ) -> Path:
        """
        Add a user note or annotation.

        Args:
            note_title: Title of the note
            note_content: Content of the note
            component_id: Optional component this note relates to

        Returns:
            Path to the saved note
        """
        # Ensure notes folder exists
        self.ensure_notes_folder()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in note_title if c.isalnum() or c in " -_")
        filename = f"{timestamp}_{safe_title}.md"

        # Create note content
        note_data = f"# {note_title}\n\n"
        note_data += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        note_data += f"**Project:** {self.project_name}\n"
        if component_id:
            note_data += f"**Component:** {component_id}\n"
        note_data += f"\n---\n\n{note_content}\n"

        # Save note
        note_path = self.notes_path / "user_notes" / filename
        note_path.write_text(note_data)

        return note_path

    # Removed: get_all_cached_components method
    # def get_all_cached_components(self) -> Dict[str, CachedComponent]:
    #     """
    #     Get all cached components for the project.
    #
    #     Returns:
    #         Dictionary of component_id -> CachedComponent
    #     """
    #     # Method removed due to dependency on llm_analysis module
    #     pass

    def export_cache_summary(self) -> Dict[str, Any]:
        """
        Export a summary of the cached data.

        Returns:
            Summary dictionary with statistics
        """
        # Removed component cache loading
        # if self._component_cache is None:
        #     self._load_component_cache()

        # Count datasheets
        datasheets_path = self.notes_path / "datasheets"
        datasheet_count = (
            len(list(datasheets_path.glob("*.pdf"))) if datasheets_path.exists() else 0
        )

        # Count analyses
        history_path = self.notes_path / "analysis_history"
        analysis_count = (
            len(list(history_path.glob("*.json"))) if history_path.exists() else 0
        )

        # Count user notes
        notes_path = self.notes_path / "user_notes"
        notes_count = len(list(notes_path.glob("*.md"))) if notes_path.exists() else 0

        return {
            "project_name": self.project_name,
            "project_path": str(self.project_path),
            "notes_folder": str(self.notes_path),
            "statistics": {
                # Removed cached_components count since we no longer have component cache
                # "cached_components": len(self._component_cache.components),
                "datasheets": datasheet_count,
                "analyses": analysis_count,
                "user_notes": notes_count,
            },
            # Removed component_summary section since it depends on component cache
            # "component_summary": {
            #     "total": len(self._component_cache.components),
            #     "by_confidence": {
            #         level: sum(1 for c in self._component_cache.components.values()
            #                  if c.confidence == level)
            #         for level in ["high", "medium", "low"]
            #     },
            #     "by_source": {
            #         source: sum(1 for c in self._component_cache.components.values()
            #                   if c.source == source)
            #         for source in ["manual", "llm", "api", "datasheet", "user"]
            #     }
            # }
        }
