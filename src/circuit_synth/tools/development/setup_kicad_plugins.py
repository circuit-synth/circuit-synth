#!/usr/bin/env python3
"""
KiCad Plugin Setup Tool

Installs circuit-synth KiCad plugins for AI-powered circuit analysis.
Provides both automatic installation and manual setup instructions.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from circuit_synth.core.kicad_validator import (
    _is_wsl,
    _looks_like_version,
    validate_kicad_installation,
)

console = Console()


def _get_windows_home() -> Optional[Path]:
    """Get the Windows home directory when running under WSL."""
    try:
        result = subprocess.run(
            ["wslpath", "-u", subprocess.run(
                ["cmd.exe", "/C", "echo", "%USERPROFILE%"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()],
            capture_output=True, text=True, timeout=5,
        )
        p = Path(result.stdout.strip())
        if p.exists():
            return p
    except Exception:
        pass
    # Fallback: try common pattern
    try:
        for user_dir in Path("/mnt/c/Users").iterdir():
            if user_dir.is_dir() and user_dir.name not in ("Public", "Default", "Default User", "All Users"):
                if (user_dir / "AppData" / "Roaming" / "kicad").exists():
                    return user_dir
    except OSError:
        pass
    return None


def _extract_version_from_path(path_str: str) -> Optional[str]:
    """Extract version string from a KiCad path like '/mnt/c/Program Files/KiCad/10.0/...'."""
    if not path_str:
        return None
    for part in Path(path_str).parts:
        if _looks_like_version(part):
            return part
    return None


def get_kicad_plugin_directories(version: Optional[str] = None) -> Dict[str, Path]:
    """Get the KiCad plugin directories for the current platform.

    Args:
        version: KiCad version string (e.g. "10.0"). Auto-detected if None.
    """
    system = platform.system()
    wsl = _is_wsl()

    if system == "Darwin":
        return {
            "user": Path.home()
            / "Library"
            / "Application Support"
            / "kicad"
            / (version or "")
            / "scripting"
            / "plugins",
            "system": Path(
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/scripting/plugins"
            ),
        }
    elif system == "Windows" or wsl:
        if wsl:
            win_home = _get_windows_home()
            if win_home and version:
                user_dir = win_home / "AppData" / "Roaming" / "kicad" / version / "scripting" / "plugins"
            elif win_home:
                user_dir = win_home / "AppData" / "Roaming" / "kicad" / "scripting" / "plugins"
            else:
                user_dir = Path.home() / ".local" / "share" / "kicad" / (version or "") / "3rdparty" / "plugins"
            return {
                "user": user_dir,
                "system": Path("/mnt/c/Program Files/KiCad")
                / (version or "")
                / "share"
                / "kicad"
                / "scripting"
                / "plugins",
            }
        else:
            base = Path.home() / "AppData" / "Roaming" / "kicad"
            if version:
                base = base / version
            return {
                "user": base / "scripting" / "plugins",
                "system": Path("C:/Program Files/KiCad")
                / (version or "")
                / "share"
                / "kicad"
                / "scripting"
                / "plugins",
            }
    else:  # Native Linux
        base = Path.home() / ".local" / "share" / "kicad"
        if version:
            base = base / version
        return {
            "user": base / "3rdparty" / "plugins",
            "system": Path("/usr/share/kicad/scripting/plugins"),
        }


def find_plugin_source_files() -> Optional[Path]:
    """Find the source KiCad plugin files in the circuit-synth installation."""
    # Look for plugins relative to this script
    script_dir = Path(__file__).parent
    possible_locations = [
        script_dir.parent.parent.parent / "kicad_plugins",  # From installed package
        script_dir.parent.parent.parent.parent / "kicad_plugins",  # From development
        script_dir.parent.parent / "kicad_plugins",  # Inside circuit_synth package
        Path.cwd() / "kicad_plugins",  # In current directory
    ]

    for location in possible_locations:
        if location.exists() and (location / "circuit_synth_bom_plugin.py").exists():
            return location

    return None


def get_plugin_files() -> List[str]:
    """Get the list of plugin files to install."""
    return [
        "circuit_synth_bom_plugin.py",
        "circuit_synth_pcb_bom_bridge.py",
    ]


def install_plugins_to_directory(source_dir: Path, target_dir: Path) -> bool:
    """Install plugin files to the specified directory."""
    try:
        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        plugin_files = get_plugin_files()
        installed_files = []

        for plugin_file in plugin_files:
            source_file = source_dir / plugin_file
            target_file = target_dir / plugin_file

            if source_file.exists():
                shutil.copy2(source_file, target_file)
                installed_files.append(plugin_file)
                console.print(f"✅ Installed: {plugin_file}", style="green")
            else:
                console.print(f"⚠️  Missing source file: {plugin_file}", style="yellow")

        if installed_files:
            console.print(f"📁 Installed to: {target_dir}", style="cyan")
            return True
        else:
            console.print("❌ No plugin files were installed", style="red")
            return False

    except Exception as e:
        console.print(f"❌ Installation failed: {e}", style="red")
        return False


def show_manual_instructions(plugin_dirs: Dict[str, Path], source_dir: Path):
    """Show manual installation instructions."""
    console.print("\n📋 Manual Installation Instructions", style="bold yellow")

    system = platform.system()
    plugin_files = get_plugin_files()
    files_list = " ".join(plugin_files)

    console.print(f"\n📂 Source files located at: {source_dir}", style="cyan")
    console.print(f"📄 Files to copy: {files_list}", style="dim")

    if system == "Darwin":  # macOS
        console.print("\n🍎 macOS Installation:", style="bold")
        console.print(f"cp {source_dir}/*.py \"{plugin_dirs['user']}\"", style="dim")

    elif system == "Windows":
        console.print("\n🪟 Windows Installation:", style="bold")
        console.print(
            f"copy \"{source_dir}\\*.py\" \"{plugin_dirs['user']}\"", style="dim"
        )

    else:  # Linux
        console.print("\n🐧 Linux Installation:", style="bold")
        console.print(f"cp {source_dir}/*.py \"{plugin_dirs['user']}\"", style="dim")

    console.print(f"\n🎯 Target directory: {plugin_dirs['user']}", style="cyan")


@click.command()
@click.option(
    "--manual", is_flag=True, help="Show manual installation instructions only"
)
@click.option(
    "--system", is_flag=True, help="Install to system-wide directory (requires admin)"
)
def main(manual: bool, system: bool):
    """Setup KiCad plugins for circuit-synth AI integration"""

    console.print(
        Panel.fit(
            Text("🔌 Circuit-Synth KiCad Plugin Setup", style="bold blue"), style="blue"
        )
    )

    # Detect environment
    wsl = _is_wsl()
    if wsl:
        console.print("🐧 WSL detected — looking for Windows-side KiCad", style="cyan")

    # Check if KiCad is installed (reuses shared kicad_validator)
    results = validate_kicad_installation()
    found = results.get("cli_available", False) or results.get("libraries_available", False)
    kicad_version = None
    # Extract version from CLI version string or from discovered paths
    if results.get("cli_version"):
        # cli_version is like "10.0.1" — take major.minor
        parts = results["cli_version"].split(".")
        if len(parts) >= 2:
            kicad_version = f"{parts[0]}.{parts[1]}"
    if not kicad_version:
        # Try to extract from discovered paths
        for key in ("cli_path", "symbol_path", "footprint_path"):
            kicad_version = _extract_version_from_path(results.get(key, ""))
            if kicad_version:
                break

    if not found:
        console.print("⚠️  KiCad not found on this system", style="yellow")
        if not Confirm.ask("Continue with plugin setup anyway?"):
            console.print("❌ Aborted", style="red")
            sys.exit(1)
    else:
        ver_str = f" (version {kicad_version})" if kicad_version else ""
        console.print(f"✅ KiCad installation detected{ver_str}", style="green")

    # Find plugin source files
    source_dir = find_plugin_source_files()
    if not source_dir:
        console.print("❌ Could not locate circuit-synth plugin files", style="red")
        console.print("   Make sure circuit-synth is properly installed", style="dim")
        sys.exit(1)

    console.print(f"📂 Found plugin files at: {source_dir}", style="green")

    # Get target directories
    plugin_dirs = get_kicad_plugin_directories(version=kicad_version)
    target_dir = plugin_dirs["system"] if system else plugin_dirs["user"]

    # Show manual instructions if requested
    if manual:
        show_manual_instructions(plugin_dirs, source_dir)
        return

    # Automatic installation
    console.print(f"\n🎯 Installing to: {target_dir}", style="cyan")

    if system:
        console.print(
            "⚠️  System installation requires administrator privileges", style="yellow"
        )
        if not Confirm.ask("Continue with system installation?"):
            console.print("❌ Aborted", style="red")
            sys.exit(1)

    # Install plugins
    success = install_plugins_to_directory(source_dir, target_dir)

    if success:
        console.print(
            Panel.fit(
                Text("✅ KiCad plugins installed successfully!", style="bold green")
                + Text(f"\n\n📁 Location: {target_dir}")
                + Text("\n🔄 Restart KiCad to activate the plugins")
                + Text("\n\n🔧 Usage in KiCad:")
                + Text(
                    "\n   • PCB Editor: Tools → External Plugins → 'Circuit-Synth AI'"
                )
                + Text(
                    "\n   • Schematic Editor: Tools → Generate BOM → 'Circuit-Synth AI'"
                ),
                title="🎉 Success!",
                style="green",
            )
        )
    else:
        console.print("\n❌ Plugin installation failed", style="red")
        console.print("💡 Try manual installation:", style="yellow")
        show_manual_instructions(plugin_dirs, source_dir)
        sys.exit(1)


if __name__ == "__main__":
    main()
