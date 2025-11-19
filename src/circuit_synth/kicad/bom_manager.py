"""BOM Property Management for Circuit-Synth.

High-level interface for managing Bill of Materials properties in KiCad schematics.
Wraps kicad-sch-api BOM functionality with circuit-synth conventions.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from kicad_sch_api.bom import BOMPropertyAuditor, ComponentIssue, PropertyMatcher

logger = logging.getLogger(__name__)


class BOMPropertyManager:
    """
    Manage BOM properties for KiCad schematics.

    High-level interface for auditing, updating, and transforming component
    properties across schematics. Useful for BOM cleanup and standardization.

    Example:
        >>> manager = BOMPropertyManager()
        >>>
        >>> # Audit for missing properties
        >>> issues = manager.audit_directory(
        ...     Path("~/my_designs"),
        ...     required_properties=["PartNumber", "Manufacturer"]
        ... )
        >>>
        >>> # Generate report
        >>> manager.generate_report(issues, Path("audit.csv"))
        >>>
        >>> # Bulk update properties
        >>> manager.update_properties(
        ...     Path("~/my_designs"),
        ...     match={"value": "10k", "lib_id": "Device:R"},
        ...     set_properties={"PartNumber": "RC0805FR-0710KL"}
        ... )
    """

    def __init__(self):
        """Initialize BOM property manager."""
        self.auditor = BOMPropertyAuditor()
        logger.debug("BOMPropertyManager initialized")

    def audit_directory(
        self,
        directory: Path,
        required_properties: List[str],
        recursive: bool = True,
        exclude_dnp: bool = False,
    ) -> List[ComponentIssue]:
        """
        Audit directory for components missing required properties.

        Args:
            directory: Path to directory containing .kicad_sch files
            required_properties: List of property names that must be present
            recursive: Scan subdirectories (default: True)
            exclude_dnp: Skip Do-Not-Populate components (default: False)

        Returns:
            List of ComponentIssue objects describing missing properties

        Example:
            >>> manager = BOMPropertyManager()
            >>> issues = manager.audit_directory(
            ...     Path("~/designs"),
            ...     required_properties=["PartNumber", "Manufacturer"],
            ...     exclude_dnp=True
            ... )
            >>> print(f"Found {len(issues)} components with missing properties")
        """
        logger.info(
            f"Auditing directory: {directory} for properties: {required_properties}"
        )

        issues = self.auditor.audit_directory(
            directory=directory,
            required_properties=required_properties,
            recursive=recursive,
            exclude_dnp=exclude_dnp,
        )

        logger.info(f"Audit complete: found {len(issues)} components with missing properties")
        return issues

    def audit_schematic(
        self,
        schematic_path: Path,
        required_properties: List[str],
        exclude_dnp: bool = False,
    ) -> List[ComponentIssue]:
        """
        Audit single schematic for missing properties.

        Args:
            schematic_path: Path to .kicad_sch file
            required_properties: List of property names that must be present
            exclude_dnp: Skip Do-Not-Populate components (default: False)

        Returns:
            List of ComponentIssue objects

        Example:
            >>> manager = BOMPropertyManager()
            >>> issues = manager.audit_schematic(
            ...     Path("circuit.kicad_sch"),
            ...     required_properties=["PartNumber"]
            ... )
        """
        logger.debug(f"Auditing schematic: {schematic_path}")

        issues = self.auditor.audit_schematic(
            schematic_path=schematic_path,
            required_properties=required_properties,
            exclude_dnp=exclude_dnp,
        )

        logger.debug(f"Found {len(issues)} components with missing properties")
        return issues

    def generate_report(
        self, issues: List[ComponentIssue], output_path: Path
    ) -> None:
        """
        Generate CSV report from audit results.

        Args:
            issues: List of ComponentIssue objects from audit
            output_path: Path where CSV report should be saved

        Example:
            >>> manager = BOMPropertyManager()
            >>> issues = manager.audit_directory(Path("~/designs"), ["PartNumber"])
            >>> manager.generate_report(issues, Path("audit_report.csv"))
        """
        logger.info(f"Generating audit report: {output_path}")
        self.auditor.generate_csv_report(issues, output_path)
        logger.info(f"Report saved: {output_path}")

    def update_properties(
        self,
        directory: Path,
        match: Dict[str, str],
        set_properties: Dict[str, str],
        dry_run: bool = False,
        recursive: bool = True,
        exclude_dnp: bool = False,
    ) -> int:
        """
        Bulk update properties on matching components.

        Args:
            directory: Path to directory containing .kicad_sch files
            match: Dict of field=pattern criteria (all must match)
            set_properties: Dict of property=value updates to apply
            dry_run: Preview only, don't modify files (default: False)
            recursive: Scan subdirectories (default: True)
            exclude_dnp: Skip Do-Not-Populate components (default: False)

        Returns:
            Number of components updated

        Example:
            >>> manager = BOMPropertyManager()
            >>>
            >>> # Preview update
            >>> count = manager.update_properties(
            ...     Path("~/designs"),
            ...     match={"value": "10k", "lib_id": "Device:R"},
            ...     set_properties={"PartNumber": "RC0805FR-0710KL"},
            ...     dry_run=True
            ... )
            >>> print(f"Would update {count} components")
            >>>
            >>> # Apply update
            >>> count = manager.update_properties(
            ...     Path("~/designs"),
            ...     match={"value": "10k", "lib_id": "Device:R"},
            ...     set_properties={
            ...         "PartNumber": "RC0805FR-0710KL",
            ...         "Manufacturer": "Yageo",
            ...         "Tolerance": "1%"
            ...     }
            ... )
        """
        action = "Would update" if dry_run else "Updating"
        logger.info(
            f"{action} components matching {match} with properties {set_properties}"
        )

        count = self.auditor.update_properties(
            directory=directory,
            match_criteria=match,
            property_updates=set_properties,
            dry_run=dry_run,
            recursive=recursive,
            exclude_dnp=exclude_dnp,
        )

        logger.info(f"{action} {count} components")
        return count

    def transform_properties(
        self,
        directory: Path,
        transformations: List[Tuple[str, str]],
        only_if_empty: bool = False,
        dry_run: bool = False,
        recursive: bool = True,
        exclude_dnp: bool = False,
    ) -> int:
        """
        Copy or rename properties across components.

        Args:
            directory: Path to directory containing .kicad_sch files
            transformations: List of (source_property, dest_property) tuples
            only_if_empty: Only copy to empty destination properties (default: False)
            dry_run: Preview only, don't modify files (default: False)
            recursive: Scan subdirectories (default: True)
            exclude_dnp: Skip Do-Not-Populate components (default: False)

        Returns:
            Number of components transformed

        Example:
            >>> manager = BOMPropertyManager()
            >>>
            >>> # Copy MPN to PartNumber (only where PartNumber is empty)
            >>> count = manager.transform_properties(
            ...     Path("~/designs"),
            ...     transformations=[("MPN", "PartNumber")],
            ...     only_if_empty=True
            ... )
            >>>
            >>> # Rename property (overwrite existing)
            >>> count = manager.transform_properties(
            ...     Path("~/designs"),
            ...     transformations=[("OldField", "NewField")]
            ... )
        """
        action = "Would transform" if dry_run else "Transforming"
        logger.info(
            f"{action} properties: {transformations} (only_if_empty={only_if_empty})"
        )

        count = self.auditor.transform_properties(
            directory=directory,
            transformations=transformations,
            only_if_empty=only_if_empty,
            dry_run=dry_run,
            recursive=recursive,
            exclude_dnp=exclude_dnp,
        )

        logger.info(f"{action} {count} components")
        return count

    @staticmethod
    def parse_match_criteria(criteria_str: str) -> Dict[str, str]:
        """
        Parse criteria string into dict for matching.

        Args:
            criteria_str: Comma-separated criteria (e.g., "value=10k,lib_id=Device:R")

        Returns:
            Dict of field=pattern criteria

        Example:
            >>> criteria = BOMPropertyManager.parse_match_criteria("value=10k,footprint=*0805*")
            >>> # Returns: {"value": "10k", "footprint": "*0805*"}
        """
        return PropertyMatcher.parse_criteria(criteria_str)

    @staticmethod
    def parse_properties(props_str: str) -> Dict[str, str]:
        """
        Parse property string into dict for setting.

        Args:
            props_str: Comma-separated properties (e.g., "PartNumber=XXX,Manufacturer=YYY")

        Returns:
            Dict of property=value pairs

        Example:
            >>> props = BOMPropertyManager.parse_properties("PartNumber=XXX,Manufacturer=YYY")
            >>> # Returns: {"PartNumber": "XXX", "Manufacturer": "YYY"}
        """
        return PropertyMatcher.parse_criteria(props_str)
