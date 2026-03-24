"""
KiCad Installation Validator

Validates that KiCad is properly installed and accessible for circuit-synth.
Supports native Linux, macOS, Windows, and WSL (Windows Subsystem for Linux)
where KiCad is installed on the Windows side.
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _is_wsl() -> bool:
    """Detect if running inside Windows Subsystem for Linux."""
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except (OSError, FileNotFoundError):
        return False


def _looks_like_version(name: str) -> bool:
    """Check if a directory name looks like a version (e.g. '8.0', '10.0')."""
    parts = name.split(".")
    return len(parts) >= 1 and all(p.isdigit() for p in parts)


def _discover_versioned_paths(
    base_dir: Path, sub_path: str
) -> List[str]:
    """Discover versioned KiCad paths under a base directory.

    Scans for versioned subdirectories (e.g. 10.0, 8.0) and returns paths
    with the sub_path appended, sorted highest version first.
    Falls back to the un-versioned path if no versioned dirs exist.
    """
    paths = []
    if base_dir.exists():
        versioned = sorted(
            [d for d in base_dir.iterdir() if d.is_dir() and _looks_like_version(d.name)],
            key=lambda d: d.name,
            reverse=True,
        )
        for v in versioned:
            paths.append(str(v / sub_path))
    # Also include the un-versioned fallback
    paths.append(str(base_dir / sub_path))
    return paths


class KiCadValidationError(Exception):
    """Raised when KiCad validation fails."""

    pass


class KiCadValidator:
    """Validates KiCad installation and provides setup guidance."""

    def __init__(self):
        self.wsl = _is_wsl()
        self.kicad_paths = self._get_kicad_paths()
        self.validation_results = {}

    def _get_kicad_paths(self) -> Dict[str, List[str]]:
        """Get platform-specific KiCad installation paths.

        Auto-discovers versioned install directories so new KiCad releases
        (10.0, 11.0, etc.) are found without code changes.
        """
        paths: Dict[str, List[str]] = {"cli": [], "symbols": [], "footprints": []}

        if sys.platform == "darwin":  # macOS
            paths["cli"] = [
                "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
                "/Applications/KiCad.app/Contents/MacOS/kicad-cli",
                "/usr/local/bin/kicad-cli",
                "/opt/homebrew/bin/kicad-cli",
                "/usr/bin/kicad-cli",
            ]
            paths["symbols"] = [
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
                "/Applications/KiCad.app/Contents/SharedSupport/symbols",
                "/Applications/KiCad/KiCad.app/Contents/Resources/share/kicad/symbols",
                "/Applications/KiCad.app/Contents/Resources/share/kicad/symbols",
                "/usr/local/share/kicad/symbols",
                "/opt/homebrew/share/kicad/symbols",
                "/usr/share/kicad/symbols",
            ]
            paths["footprints"] = [
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
                "/Applications/KiCad.app/Contents/SharedSupport/footprints",
                "/Applications/KiCad/KiCad.app/Contents/Resources/share/kicad/footprints",
                "/Applications/KiCad.app/Contents/Resources/share/kicad/footprints",
                "/usr/local/share/kicad/footprints",
                "/opt/homebrew/share/kicad/footprints",
                "/usr/share/kicad/footprints",
            ]

        if sys.platform.startswith("linux"):
            if self.wsl:
                # WSL: look for KiCad on the Windows side
                for base in [
                    Path("/mnt/c/Program Files/KiCad"),
                    Path("/mnt/c/Program Files (x86)/KiCad"),
                ]:
                    paths["cli"] += _discover_versioned_paths(base, "bin/kicad-cli.exe")
                    paths["symbols"] += _discover_versioned_paths(base, "share/kicad/symbols")
                    paths["footprints"] += _discover_versioned_paths(base, "share/kicad/footprints")

            # Native Linux paths (also checked under WSL as fallback)
            paths["cli"] += [
                "/usr/bin/kicad-cli",
                "/usr/local/bin/kicad-cli",
                "~/.local/bin/kicad-cli",
                "/usr/lib/kicad/bin/kicad-cli",
                "/var/lib/flatpak/app/org.kicad.KiCad/current/active/files/bin/kicad-cli",
            ]
            paths["symbols"] += [
                "/usr/share/kicad/symbols",
                "/usr/local/share/kicad/symbols",
                "~/.local/share/kicad/symbols",
                "/usr/share/kicad/library/symbols",
                "/usr/local/share/kicad/library/symbols",
                "/var/lib/flatpak/runtime/org.kicad.KiCad.Library/current/active/files/share/kicad/symbols",
            ]
            paths["footprints"] += [
                "/usr/share/kicad/footprints",
                "/usr/local/share/kicad/footprints",
                "~/.local/share/kicad/footprints",
                "/usr/share/kicad/library/footprints",
                "/usr/local/share/kicad/library/footprints",
                "/var/lib/flatpak/runtime/org.kicad.KiCad.Library/current/active/files/share/kicad/footprints",
            ]

        elif sys.platform == "win32":  # Native Windows
            for base in [
                Path("C:/Program Files/KiCad"),
                Path("C:/Program Files (x86)/KiCad"),
            ]:
                paths["cli"] += _discover_versioned_paths(base, "bin/kicad-cli.exe")
                paths["symbols"] += _discover_versioned_paths(base, "share/kicad/symbols")
                paths["footprints"] += _discover_versioned_paths(base, "share/kicad/footprints")

        return paths

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
                        # KiCad <= 9: .kicad_sym files; KiCad >= 10: .kicad_symdir directories
                        lib_files = list(expanded_path.glob("*.kicad_sym")) + list(
                            expanded_path.glob("*.kicad_symdir")
                        )
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
        elif sys.platform.startswith("linux") and self.wsl:
            return """
🐧 KiCad on WSL (Windows Subsystem for Linux):

Install KiCad on the **Windows side** — circuit-synth will detect it automatically.

1. **Official Installer (Recommended):**
   Download from: https://www.kicad.org/download/windows/

2. **Chocolatey:**
   choco install kicad

3. **Winget:**
   winget install KiCad.KiCad

After installation, circuit-synth finds KiCad via /mnt/c/Program Files/KiCad/.
"""
        elif sys.platform.startswith("linux"):  # Native Linux
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

After installation, add KiCad to your PATH or use full path.
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
