"""
DigiKey library converter - converts legacy .lib to modern .kicad_sym format
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from loguru import logger


class DigiKeyLibraryConverter:
    """Converts DigiKey legacy .lib files to modern .kicad_sym format"""

    def __init__(self, digikey_path: Optional[Path] = None):
        self.digikey_path = digikey_path or Path.cwd() / "libraries" / "digikey-kicad"
        self.converted_path = Path.cwd() / "libraries" / "digikey-kicad-converted"
        self.symbols_input = self.digikey_path / "digikey-symbols"
        self.symbols_output = self.converted_path / "symbols"

        # Check if kicad-cli is available
        self.kicad_cli = self._find_kicad_cli()

    def _find_kicad_cli(self) -> Optional[str]:
        """Find kicad-cli executable"""

        # Common locations
        cli_paths = [
            "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
            "/usr/bin/kicad-cli",
            "/usr/local/bin/kicad-cli",
            shutil.which("kicad-cli"),
        ]

        for cli_path in cli_paths:
            if cli_path and Path(cli_path).exists():
                return str(cli_path)

        return None

    def is_conversion_needed(self) -> bool:
        """Check if conversion is needed"""

        if not self.digikey_path.exists():
            return False

        if not self.symbols_input.exists():
            return False

        # Check if already converted
        if self.symbols_output.exists() and list(
            self.symbols_output.glob("*.kicad_sym")
        ):
            logger.info("DigiKey library already converted")
            return False

        return True

    def convert_all_libraries(self) -> bool:
        """Convert all DigiKey legacy libraries to modern format"""

        if not self.is_conversion_needed():
            return True

        if not self.kicad_cli:
            logger.warning("kicad-cli not found - cannot convert DigiKey libraries")
            return False

        # Create output directory
        self.symbols_output.mkdir(parents=True, exist_ok=True)

        # Find all .lib files
        lib_files = list(self.symbols_input.glob("*.lib"))

        if not lib_files:
            logger.warning("No .lib files found in DigiKey library")
            return False

        logger.info(f"Converting {len(lib_files)} DigiKey library files...")

        converted_count = 0
        failed_count = 0

        for lib_file in lib_files:
            output_file = self.symbols_output / f"{lib_file.stem}.kicad_sym"

            if self._convert_library(lib_file, output_file):
                converted_count += 1
            else:
                failed_count += 1

        logger.info(
            f"Conversion complete: {converted_count} succeeded, {failed_count} failed"
        )

        return failed_count == 0

    def _convert_library(self, input_file: Path, output_file: Path) -> bool:
        """Convert single library file"""

        try:
            cmd = [
                self.kicad_cli,
                "sym",
                "upgrade",
                str(input_file),
                "--output",
                str(output_file),
                "--force",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                logger.debug(f"Converted {input_file.name} -> {output_file.name}")
                return True
            else:
                logger.warning(f"Failed to convert {input_file.name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error converting {input_file.name}: {e}")
            return False

    def get_converted_symbols_path(self) -> Optional[Path]:
        """Get path to converted symbols directory"""

        if self.symbols_output.exists() and list(
            self.symbols_output.glob("*.kicad_sym")
        ):
            return self.symbols_output

        return None

    def cleanup_converted_libraries(self):
        """Remove converted libraries (useful for testing)"""

        if self.converted_path.exists():
            shutil.rmtree(self.converted_path)
            logger.info("Cleaned up converted DigiKey libraries")


def convert_digikey_library_if_needed() -> Optional[Path]:
    """
    Utility function to convert DigiKey library if needed
    Returns path to converted symbols or None
    """

    converter = DigiKeyLibraryConverter()

    if converter.convert_all_libraries():
        return converter.get_converted_symbols_path()

    return None
