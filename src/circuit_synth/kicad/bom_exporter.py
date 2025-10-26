"""BOM (Bill of Materials) export functionality using KiCad CLI."""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BOMExporter:
    """Export Bill of Materials from KiCad schematic files using kicad-cli."""

    @staticmethod
    def export_csv(
        schematic_file: Path,
        output_file: Path,
        fields: Optional[str] = None,
        labels: Optional[str] = None,
        group_by: Optional[str] = None,
        exclude_dnp: bool = False,
    ) -> Dict[str, Any]:
        """
        Export BOM from a KiCad schematic to CSV format using kicad-cli.

        Args:
            schematic_file: Path to .kicad_sch schematic file
            output_file: Path where CSV BOM should be written
            fields: Comma-separated fields to export. Default: all fields from schematic
            labels: Comma-separated column headers. Must match number of fields.
            group_by: Field to group references by (e.g., "Value" to group by component value)
            exclude_dnp: Whether to exclude "Do not populate" components

        Returns:
            dict: Result dictionary with keys:
                - success: bool - True if BOM was successfully exported
                - file: Path - Path to generated BOM file
                - component_count: int - Number of components in BOM
                - error: str (optional) - Error message if export failed

        Raises:
            FileNotFoundError: If kicad-cli is not available or schematic file not found
            subprocess.CalledProcessError: If kicad-cli returns non-zero exit code
        """
        schematic_file = Path(schematic_file)
        output_file = Path(output_file)

        # Verify schematic file exists
        if not schematic_file.exists():
            raise FileNotFoundError(f"Schematic file not found: {schematic_file}")

        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Build kicad-cli command
        cmd = [
            "kicad-cli",
            "sch",
            "export",
            "bom",
            "--output", str(output_file),
        ]

        # Add optional parameters
        if fields:
            cmd.extend(["--fields", fields])
        if labels:
            cmd.extend(["--labels", labels])
        if group_by:
            cmd.extend(["--group-by", group_by])
        if exclude_dnp:
            cmd.append("--exclude-dnp")

        # Add input file
        cmd.append(str(schematic_file))

        logger.debug(f"Running BOM export: {' '.join(cmd)}")

        try:
            # Execute kicad-cli
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            # Count components in BOM by reading CSV
            component_count = 0
            try:
                with open(output_file, 'r') as f:
                    # Skip header row
                    next(f)
                    # Count remaining lines
                    component_count = sum(1 for _ in f)
            except Exception as e:
                logger.warning(f"Could not count components in BOM: {e}")

            logger.info(f"BOM exported successfully: {output_file} ({component_count} components)")

            return {
                "success": True,
                "file": output_file,
                "component_count": component_count,
            }

        except FileNotFoundError:
            error_msg = (
                "kicad-cli not found. Ensure KiCad 8.0+ is installed and "
                "kicad-cli is available in PATH."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        except subprocess.CalledProcessError as e:
            error_msg = f"kicad-cli BOM export failed: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
