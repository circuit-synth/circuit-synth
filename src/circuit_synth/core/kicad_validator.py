"""
KiCad Installation Validator

Validates that KiCad is properly installed and accessible for circuit-synth.
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KiCadValidationError(Exception):
    """Raised when KiCad validation fails."""

    pass


class KiCadValidator:
    """Validates KiCad installation and provides setup guidance."""

    def __init__(self):
        self.kicad_paths = self._get_kicad_paths()
        self.validation_results = {}

    def _get_kicad_paths(self) -> Dict[str, List[str]]:
        """Get platform-specific KiCad installation paths."""
        if sys.platform == "darwin":  # macOS
            return {
                "cli": [
                    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
                    "/Applications/KiCad.app/Contents/MacOS/kicad-cli",
                    "/usr/local/bin/kicad-cli",
                    "/opt/homebrew/bin/kicad-cli",
                    "/usr/bin/kicad-cli",
                ],
                "symbols": [
                    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
                    "/Applications/KiCad.app/Contents/SharedSupport/symbols",
                    "/Applications/KiCad/KiCad.app/Contents/Resources/share/kicad/symbols",
                    "/Applications/KiCad.app/Contents/Resources/share/kicad/symbols",
                    "/usr/local/share/kicad/symbols",
                    "/opt/homebrew/share/kicad/symbols",
                    "/usr/share/kicad/symbols",
                ],
                "footprints": [
                    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
                    "/Applications/KiCad.app/Contents/SharedSupport/footprints",
                    "/Applications/KiCad/KiCad.app/Contents/Resources/share/kicad/footprints",
                    "/Applications/KiCad.app/Contents/Resources/share/kicad/footprints",
                    "/usr/local/share/kicad/footprints",
                    "/opt/homebrew/share/kicad/footprints",
                    "/usr/share/kicad/footprints",
                ],
            }
        elif sys.platform.startswith("linux"):  # Linux
            return {
                "cli": [
                    "/usr/bin/kicad-cli",
                    "/usr/local/bin/kicad-cli",
                    "~/.local/bin/kicad-cli",
                    "/usr/lib/kicad/bin/kicad-cli",
                    "/var/lib/flatpak/app/org.kicad.KiCad/current/active/files/bin/kicad-cli",
                ],
                "symbols": [
                    "/usr/share/kicad/symbols",
                    "/usr/local/share/kicad/symbols",
                    "~/.local/share/kicad/symbols",
                    "/usr/share/kicad/library/symbols",
                    "/usr/local/share/kicad/library/symbols",
                    "/var/lib/flatpak/runtime/org.kicad.KiCad.Library/current/active/files/share/kicad/symbols",
                ],
                "footprints": [
                    "/usr/share/kicad/footprints",
                    "/usr/local/share/kicad/footprints",
                    "~/.local/share/kicad/footprints",
                    "/usr/share/kicad/library/footprints",
                    "/usr/local/share/kicad/library/footprints",
                    "/var/lib/flatpak/runtime/org.kicad.KiCad.Library/current/active/files/share/kicad/footprints",
                ],
            }
        elif sys.platform == "win32":  # Windows
            return {
                "cli": [
                    "C:\\Program Files\\KiCad\\8.0\\bin\\kicad-cli.exe",
                    "C:\\Program Files\\KiCad\\bin\\kicad-cli.exe",
                    "C:\\Program Files\\KiCad\\7.0\\bin\\kicad-cli.exe",
                    "C:\\Program Files (x86)\\KiCad\\8.0\\bin\\kicad-cli.exe",
                    "C:\\Program Files (x86)\\KiCad\\bin\\kicad-cli.exe",
                ],
                "symbols": [
                    "C:\\Program Files\\KiCad\\8.0\\share\\kicad\\symbols",
                    "C:\\Program Files\\KiCad\\share\\kicad\\symbols",
                    "C:\\Program Files\\KiCad\\7.0\\share\\kicad\\symbols",
                    "C:\\Program Files (x86)\\KiCad\\8.0\\share\\kicad\\symbols",
                    "C:\\Program Files (x86)\\KiCad\\share\\kicad\\symbols",
                ],
                "footprints": [
                    "C:\\Program Files\\KiCad\\8.0\\share\\kicad\\footprints",
                    "C:\\Program Files\\KiCad\\share\\kicad\\footprints",
                    "C:\\Program Files\\KiCad\\7.0\\share\\kicad\\footprints",
                    "C:\\Program Files (x86)\\KiCad\\8.0\\share\\kicad\\footprints",
                    "C:\\Program Files (x86)\\KiCad\\share\\kicad\\footprints",
                ],
            }
        else:
            return {"cli": [], "symbols": [], "footprints": []}

    def validate_kicad_cli(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate KiCad CLI is available and get version."""
        # First check if kicad-cli is in PATH
        cli_path = shutil.which("kicad-cli")
        if cli_path:
            try:
                result = subprocess.run(
                    [cli_path, "version"], capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    return True, cli_path, version
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

        # Check platform-specific paths
        for path in self.kicad_paths["cli"]:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                try:
                    result = subprocess.run(
                        [str(expanded_path), "version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        return True, str(expanded_path), version
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue

        return False, None, None

    def validate_kicad_libraries(self) -> Tuple[bool, Dict[str, Optional[str]]]:
        """Validate KiCad symbol and footprint libraries."""
        found_paths = {"symbols": None, "footprints": None}

        for lib_type in ["symbols", "footprints"]:
            for path in self.kicad_paths[lib_type]:
                expanded_path = Path(path).expanduser()
                if expanded_path.exists() and expanded_path.is_dir():
                    # Check if library contains expected files
                    if lib_type == "symbols":
                        lib_files = list(expanded_path.glob("*.kicad_sym"))
                    else:  # footprints
                        lib_files = list(expanded_path.glob("*.pretty"))

                    if lib_files:
                        found_paths[lib_type] = str(expanded_path)
                        break

        all_found = all(path is not None for path in found_paths.values())
        return all_found, found_paths

    def validate_full_installation(self) -> Dict[str, any]:
        """Perform complete KiCad installation validation."""
        results = {
            "cli_available": False,
            "cli_path": None,
            "cli_version": None,
            "libraries_available": False,
            "symbol_path": None,
            "footprint_path": None,
            "errors": [],
            "warnings": [],
            "installation_guide": None,
        }

        # Validate CLI
        cli_ok, cli_path, cli_version = self.validate_kicad_cli()
        results["cli_available"] = cli_ok
        results["cli_path"] = cli_path
        results["cli_version"] = cli_version

        if not cli_ok:
            results["errors"].append("KiCad CLI not found")

        # Validate libraries
        libs_ok, lib_paths = self.validate_kicad_libraries()
        results["libraries_available"] = libs_ok
        results["symbol_path"] = lib_paths["symbols"]
        results["footprint_path"] = lib_paths["footprints"]

        if not lib_paths["symbols"]:
            results["errors"].append("KiCad symbol libraries not found")
        if not lib_paths["footprints"]:
            results["errors"].append("KiCad footprint libraries not found")

        # Generate installation guide if needed
        if results["errors"]:
            results["installation_guide"] = self._generate_installation_guide()

        self.validation_results = results
        return results

    def _generate_installation_guide(self) -> str:
        """Generate platform-specific installation guide."""
        if sys.platform == "darwin":  # macOS
            return """
🍎 KiCad Installation for macOS:

1. **Official Installer (Recommended):**
   Download from: https://www.kicad.org/download/macos/
   
2. **Homebrew:**
   brew install kicad
   
3. **MacPorts:**
   sudo port install kicad

After installation, KiCad should be available at:
- CLI: /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
- Libraries: /Applications/KiCad/KiCad.app/Contents/SharedSupport/
"""
        elif sys.platform.startswith("linux"):  # Linux
            return """
🐧 KiCad Installation for Linux:

1. **Ubuntu/Debian:**
   sudo apt update
   sudo apt install kicad
   
2. **Fedora:**
   sudo dnf install kicad
   
3. **Arch Linux:**
   sudo pacman -S kicad
   
4. **Flatpak (Universal):**
   flatpak install org.kicad.KiCad

After installation, verify with: kicad-cli version
"""
        elif sys.platform == "win32":  # Windows
            return """
🪟 KiCad Installation for Windows:

1. **Official Installer (Recommended):**
   Download from: https://www.kicad.org/download/windows/
   
2. **Microsoft Store:**
   Search for "KiCad" in Microsoft Store
   
3. **Chocolatey:**
   choco install kicad

After installation, add KiCad to your PATH or use full path:
C:\\Program Files\\KiCad\\8.0\\bin\\kicad-cli.exe
"""
        else:
            return "Please install KiCad from: https://www.kicad.org/download/"

    def require_kicad(self) -> None:
        """Require KiCad installation, raise exception if not available."""
        results = self.validate_full_installation()

        if not results["cli_available"]:
            error_msg = "KiCad CLI is required but not found.\n\n"
            error_msg += results["installation_guide"]
            raise KiCadValidationError(error_msg)

        if not results["libraries_available"]:
            error_msg = "KiCad libraries are required but not found.\n\n"
            error_msg += "Missing libraries:\n"
            if not results["symbol_path"]:
                error_msg += "- Symbol libraries\n"
            if not results["footprint_path"]:
                error_msg += "- Footprint libraries\n"
            error_msg += "\n" + results["installation_guide"]
            raise KiCadValidationError(error_msg)

        logger.info(f"KiCad validation successful: {results['cli_version']}")
        logger.info(f"Symbol libraries: {results['symbol_path']}")
        logger.info(f"Footprint libraries: {results['footprint_path']}")


# Convenience functions
def validate_kicad_installation() -> Dict[str, any]:
    """Validate KiCad installation and return results."""
    validator = KiCadValidator()
    return validator.validate_full_installation()


def require_kicad() -> None:
    """Require KiCad installation, raise exception if not available."""
    validator = KiCadValidator()
    validator.require_kicad()


def get_kicad_paths() -> Dict[str, Optional[str]]:
    """Get paths to KiCad CLI and libraries."""
    validator = KiCadValidator()
    results = validator.validate_full_installation()
    return {
        "cli": results["cli_path"],
        "symbols": results["symbol_path"],
        "footprints": results["footprint_path"],
    }


def main():
    """CLI entry point for KiCad validation."""
    import sys

    print("🔍 Circuit-Synth KiCad Validation")
    print("=" * 50)

    try:
        results = validate_kicad_installation()

        # Print results
        if results["cli_available"]:
            print(f"✅ KiCad CLI: {results['cli_path']}")
            print(f"   Version: {results['cli_version']}")
        else:
            print("❌ KiCad CLI: Not found")

        if results["symbol_path"]:
            print(f"✅ Symbol Libraries: {results['symbol_path']}")
        else:
            print("❌ Symbol Libraries: Not found")

        if results["footprint_path"]:
            print(f"✅ Footprint Libraries: {results['footprint_path']}")
        else:
            print("❌ Footprint Libraries: Not found")

        # Print warnings and errors
        if results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in results["warnings"]:
                print(f"   - {warning}")

        if results["errors"]:
            print("\n❌ Errors:")
            for error in results["errors"]:
                print(f"   - {error}")

            if results["installation_guide"]:
                print("\n📖 Installation Guide:")
                print(results["installation_guide"])

            sys.exit(1)
        else:
            print("\n🎉 KiCad installation is valid and ready to use!")
            sys.exit(0)

    except Exception as e:
        print(f"\n💥 Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
