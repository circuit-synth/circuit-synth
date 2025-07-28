"""
KiCad CLI integration module for the PCB API.

This module provides a generic interface to run any kicad-cli command with:
- Automatic detection of kicad-cli path on different platforms
- Both low-level (run any command) and high-level methods (specific commands)
- JSON output parsing when available
- Proper error handling with custom exceptions
"""

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class KiCadCLIError(Exception):
    """Base exception for KiCad CLI errors."""

    pass


class KiCadCLINotFoundError(KiCadCLIError):
    """Raised when kicad-cli executable cannot be found."""

    pass


class KiCadCLICommandError(KiCadCLIError):
    """Raised when a kicad-cli command fails."""

    def __init__(self, message: str, return_code: int, stdout: str, stderr: str):
        super().__init__(message)
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr


@dataclass
class DRCResult:
    """Result of a DRC (Design Rule Check) operation."""

    success: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    unconnected_items: List[Dict[str, Any]]
    output_file: Optional[Path] = None

    @property
    def total_issues(self) -> int:
        """Total number of issues found."""
        return len(self.violations) + len(self.warnings) + len(self.unconnected_items)


class KiCadCLI:
    """
    Generic interface to run KiCad CLI commands.

    Provides both low-level command execution and high-level convenience methods
    for common operations like DRC, export, etc.
    """

    def __init__(self, kicad_cli_path: Optional[str] = None):
        """
        Initialize KiCad CLI interface.

        Args:
            kicad_cli_path: Optional explicit path to kicad-cli executable.
                           If not provided, will attempt auto-detection.
        """
        self.kicad_cli_path = kicad_cli_path or self._find_kicad_cli()
        if not self.kicad_cli_path:
            raise KiCadCLINotFoundError(
                "Could not find kicad-cli executable. Please install KiCad or provide explicit path."
            )
        logger.info(f"Using kicad-cli at: {self.kicad_cli_path}")

    def _find_kicad_cli(self) -> Optional[str]:
        """
        Automatically detect kicad-cli path on different platforms.

        Returns:
            Path to kicad-cli executable or None if not found.
        """
        # First check if it's in PATH
        cli_path = shutil.which("kicad-cli")
        if cli_path:
            return cli_path

        # Platform-specific search paths
        system = platform.system()
        search_paths = []

        if system == "Darwin":  # macOS
            search_paths = [
                "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
                "/Applications/KiCad.app/Contents/MacOS/kicad-cli",
                os.path.expanduser(
                    "~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
                ),
                os.path.expanduser("~/Applications/KiCad.app/Contents/MacOS/kicad-cli"),
            ]
        elif system == "Windows":
            # Common Windows installation paths
            program_files = [
                os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
            ]
            for pf in program_files:
                search_paths.extend(
                    [
                        os.path.join(pf, "KiCad", "9.0", "bin", "kicad-cli.exe"),
                        os.path.join(pf, "KiCad", "8.0", "bin", "kicad-cli.exe"),
                        os.path.join(pf, "KiCad", "7.0", "bin", "kicad-cli.exe"),
                        os.path.join(pf, "KiCad", "bin", "kicad-cli.exe"),
                    ]
                )
        elif system == "Linux":
            search_paths = [
                "/usr/bin/kicad-cli",
                "/usr/local/bin/kicad-cli",
                "/opt/kicad/bin/kicad-cli",
                os.path.expanduser("~/.local/bin/kicad-cli"),
            ]

        # Search for the executable
        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def run_command(
        self,
        args: List[str],
        cwd: Optional[Union[str, Path]] = None,
        capture_output: bool = True,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run a kicad-cli command with the given arguments.

        This is the low-level interface that all high-level methods use.

        Args:
            args: Command arguments (without 'kicad-cli' prefix)
            cwd: Working directory for the command
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception on non-zero return code

        Returns:
            CompletedProcess instance with command results

        Raises:
            KiCadCLICommandError: If command fails and check=True
        """
        cmd = [self.kicad_cli_path] + args
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=False,  # We'll handle errors ourselves
            )

            if check and result.returncode != 0:
                raise KiCadCLICommandError(
                    f"Command failed with return code {result.returncode}",
                    return_code=result.returncode,
                    stdout=result.stdout if capture_output else "",
                    stderr=result.stderr if capture_output else "",
                )

            return result

        except FileNotFoundError:
            raise KiCadCLINotFoundError(
                f"kicad-cli not found at: {self.kicad_cli_path}"
            )

    def get_version(self) -> str:
        """
        Get KiCad CLI version information.

        Returns:
            Version string
        """
        result = self.run_command(["version"])
        return result.stdout.strip()

    def run_drc(
        self,
        pcb_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        units: str = "mm",
        severity: str = "error",
        format: str = "json",
        custom_rules_file: Optional[Union[str, Path]] = None,
    ) -> DRCResult:
        """
        Run Design Rule Check on a PCB file.

        Args:
            pcb_file: Path to the PCB file
            output_file: Optional output file for the report. If not provided,
                        will use pcb_file with .drc extension
            units: Units for the report (mm, in, mils)
            severity: Minimum severity to report (error, warning, info)
            format: Output format (json, report)
            custom_rules_file: Optional path to custom DRC rules file

        Returns:
            DRCResult object with violations, warnings, and unconnected items

        Note:
            Custom DRC rules via command line are not directly supported in current
            KiCad versions. Rules are typically embedded in the PCB file or project.
            The custom_rules_file parameter is included for future compatibility.
        """
        pcb_path = Path(pcb_file)
        if not pcb_path.exists():
            raise FileNotFoundError(f"PCB file not found: {pcb_path}")

        # Determine output file
        if output_file is None:
            output_file = pcb_path.with_suffix(".drc")
        else:
            output_file = Path(output_file)

        # Build command arguments
        args = [
            "pcb",
            "drc",
            "--output",
            str(output_file),
            "--units",
            units,
            "--severity",
            severity,
            "--format",
            format,
        ]

        # Note: Current KiCad CLI doesn't support custom rules file parameter
        # Rules must be embedded in the PCB file or project settings
        if custom_rules_file:
            logger.warning(
                "Custom DRC rules file specified, but KiCad CLI currently uses rules "
                "embedded in the PCB file. The custom_rules_file parameter is ignored."
            )

        args.append(str(pcb_path))

        # Run DRC
        try:
            result = self.run_command(args, cwd=pcb_path.parent)

            # Parse results based on format
            if format == "json" and output_file.exists():
                with open(output_file, "r") as f:
                    drc_data = json.load(f)

                return DRCResult(
                    success=len(drc_data.get("violations", [])) == 0,
                    violations=drc_data.get("violations", []),
                    warnings=drc_data.get("warnings", []),
                    unconnected_items=drc_data.get("unconnected_items", []),
                    output_file=output_file,
                )
            else:
                # For non-JSON formats, just check if file was created
                return DRCResult(
                    success=True,  # Command succeeded
                    violations=[],
                    warnings=[],
                    unconnected_items=[],
                    output_file=output_file if output_file.exists() else None,
                )

        except KiCadCLICommandError as e:
            # DRC command may return non-zero if violations found
            # Try to parse the output file anyway
            if format == "json" and output_file.exists():
                with open(output_file, "r") as f:
                    drc_data = json.load(f)

                return DRCResult(
                    success=False,
                    violations=drc_data.get("violations", []),
                    warnings=drc_data.get("warnings", []),
                    unconnected_items=drc_data.get("unconnected_items", []),
                    output_file=output_file,
                )
            else:
                raise

    def export_gerbers(
        self,
        pcb_file: Union[str, Path],
        output_dir: Union[str, Path],
        layers: Optional[List[str]] = None,
        protel_extensions: bool = False,
    ) -> List[Path]:
        """
        Export Gerber files from a PCB.

        Args:
            pcb_file: Path to the PCB file
            output_dir: Directory to save Gerber files
            layers: Optional list of layer names to export. If None, exports all copper and technical layers
            protel_extensions: Use Protel filename extensions

        Returns:
            List of generated Gerber file paths
        """
        pcb_path = Path(pcb_file)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        args = [
            "pcb",
            "export",
            "gerbers",
            "--output",
            str(output_path),
        ]

        if layers:
            for layer in layers:
                args.extend(["--layers", layer])

        if protel_extensions:
            args.append("--use-protel-extensions")

        args.append(str(pcb_path))

        self.run_command(args, cwd=pcb_path.parent)

        # Find generated files
        gerber_files = list(output_path.glob("*.gbr")) + list(output_path.glob("*.g*"))
        return sorted(gerber_files)

    def export_drill(
        self,
        pcb_file: Union[str, Path],
        output_dir: Union[str, Path],
        format: str = "excellon",
        units: str = "mm",
        mirror_y: bool = False,
        minimal_header: bool = False,
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Export drill files from a PCB.

        Args:
            pcb_file: Path to the PCB file
            output_dir: Directory to save drill files
            format: Drill file format (excellon, gerber)
            units: Units for coordinates (mm, in)
            mirror_y: Mirror Y coordinates
            minimal_header: Use minimal header

        Returns:
            Tuple of (plated_holes_file, non_plated_holes_file)
        """
        pcb_path = Path(pcb_file)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        args = [
            "pcb",
            "export",
            "drill",
            "--output",
            str(output_path),
            "--format",
            format,
            "--units",
            units,
        ]

        if mirror_y:
            args.append("--mirror-y")

        if minimal_header:
            args.append("--minimal-header")

        args.append(str(pcb_path))

        self.run_command(args, cwd=pcb_path.parent)

        # Find generated files
        base_name = pcb_path.stem
        plated_file = output_path / f"{base_name}-PTH.drl"
        non_plated_file = output_path / f"{base_name}-NPTH.drl"

        return (
            plated_file if plated_file.exists() else None,
            non_plated_file if non_plated_file.exists() else None,
        )

    def export_pos(
        self,
        pcb_file: Union[str, Path],
        output_file: Union[str, Path],
        side: str = "both",
        format: str = "csv",
        units: str = "mm",
        use_drill_origin: bool = False,
        smd_only: bool = False,
    ) -> Path:
        """
        Export pick and place (position) file from a PCB.

        Args:
            pcb_file: Path to the PCB file
            output_file: Output file path
            side: Which side to export (front, back, both)
            format: Output format (csv, ascii, gerber)
            units: Units for coordinates (mm, in)
            use_drill_origin: Use drill/place origin instead of page origin
            smd_only: Only include SMD components

        Returns:
            Path to generated position file
        """
        pcb_path = Path(pcb_file)
        output_path = Path(output_file)

        args = [
            "pcb",
            "export",
            "pos",
            "--output",
            str(output_path),
            "--side",
            side,
            "--format",
            format,
            "--units",
            units,
        ]

        if use_drill_origin:
            args.append("--use-drill-origin")

        if smd_only:
            args.append("--smd-only")

        args.append(str(pcb_path))

        self.run_command(args, cwd=pcb_path.parent)

        return output_path

    def export_svg(
        self,
        pcb_file: Union[str, Path],
        output_file: Union[str, Path],
        layers: Optional[List[str]] = None,
        theme: Optional[str] = None,
        black_and_white: bool = False,
        page_size: Optional[str] = None,
    ) -> Path:
        """
        Export PCB as SVG image.

        Args:
            pcb_file: Path to the PCB file
            output_file: Output SVG file path
            layers: List of layers to include
            theme: Color theme to use
            black_and_white: Export in black and white
            page_size: Page size (A4, A3, etc.)

        Returns:
            Path to generated SVG file
        """
        pcb_path = Path(pcb_file)
        output_path = Path(output_file)

        args = [
            "pcb",
            "export",
            "svg",
            "--output",
            str(output_path),
        ]

        if layers:
            for layer in layers:
                args.extend(["--layers", layer])

        if theme:
            args.extend(["--theme", theme])

        if black_and_white:
            args.append("--black-and-white")

        if page_size:
            args.extend(["--page-size", page_size])

        args.append(str(pcb_path))

        self.run_command(args, cwd=pcb_path.parent)

        return output_path


# Convenience function for creating CLI instance
def get_kicad_cli(kicad_cli_path: Optional[str] = None) -> KiCadCLI:
    """
    Get a KiCad CLI instance with auto-detection.

    Args:
        kicad_cli_path: Optional explicit path to kicad-cli

    Returns:
        KiCadCLI instance
    """
    return KiCadCLI(kicad_cli_path)
