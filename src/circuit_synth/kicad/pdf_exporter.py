"""PDF export functionality for KiCad schematics using KiCad CLI."""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PDFExporter:
    """Export PDF schematics from KiCad schematic files using kicad-cli."""

    @staticmethod
    def export_pdf(
        schematic_file: Path,
        output_file: Path,
        black_and_white: bool = False,
        theme: Optional[str] = None,
        exclude_drawing_sheet: bool = False,
        pages: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Export schematic to PDF format using kicad-cli.

        Args:
            schematic_file: Path to .kicad_sch schematic file
            output_file: Path where PDF should be written
            black_and_white: Export in black and white instead of color (default: False)
            theme: Color theme to use for export (optional)
            exclude_drawing_sheet: Exclude the drawing sheet/border from PDF (default: False)
            pages: Page range to export (e.g., "1,3-5" for pages 1, 3, 4, 5). Default: all pages

        Returns:
            dict: Result dictionary with keys:
                - success: bool - True if PDF was successfully exported
                - file: Path - Path to generated PDF file
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
            "pdf",
            "--output", str(output_file),
        ]

        # Add optional parameters
        if black_and_white:
            cmd.append("--black-and-white")
        if theme:
            cmd.extend(["--theme", theme])
        if exclude_drawing_sheet:
            cmd.append("--exclude-drawing-sheet")
        if pages:
            cmd.extend(["--pages", pages])

        # Add input file
        cmd.append(str(schematic_file))

        logger.debug(f"Running PDF export: {' '.join(cmd)}")

        try:
            # Execute kicad-cli
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"PDF exported successfully: {output_file}")

            return {
                "success": True,
                "file": output_file,
            }

        except FileNotFoundError:
            error_msg = (
                "kicad-cli not found. Ensure KiCad 7.0+ is installed and "
                "kicad-cli is available in PATH."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        except subprocess.CalledProcessError as e:
            error_msg = f"kicad-cli PDF export failed: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
