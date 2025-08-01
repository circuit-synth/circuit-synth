#!/usr/bin/env python3
"""
KiCad Plugin Setup Tool

Installs circuit-synth KiCad plugins for AI-powered circuit analysis.
Provides both automatic installation and manual setup instructions.
"""

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

console = Console()


def get_kicad_plugin_directories() -> Dict[str, Path]:
    """Get the KiCad plugin directories for different platforms."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return {
            "user": Path.home()
            / "Library"
            / "Application Support"
            / "kicad"
            / "scripting"
            / "plugins",
            "system": Path(
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/scripting/plugins"
            ),
        }
    elif system == "Windows":
        return {
            "user": Path.home()
            / "AppData"
            / "Roaming"
            / "kicad"
            / "scripting"
            / "plugins",
            "system": Path("C:/Program Files/KiCad/share/kicad/scripting/plugins"),
        }
    else:  # Linux
        return {
            "user": Path.home()
            / ".local"
            / "share"
            / "kicad"
            / "8.0"
            / "3rdparty"
            / "plugins",
            "system": Path("/usr/share/kicad/scripting/plugins"),
        }


def find_plugin_source_files() -> Optional[Path]:
    """Find the source KiCad plugin files in the circuit-synth installation."""
    # Look for plugins relative to this script
    script_dir = Path(__file__).parent
    possible_locations = [
        script_dir.parent.parent.parent / "kicad_plugins",  # From installed package
        script_dir.parent.parent.parent.parent / "kicad_plugins",  # From development
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


def check_kicad_installation() -> bool:
    """Check if KiCad is installed."""
    try:
        # Try to find KiCad in common locations
        if platform.system() == "Darwin":
            kicad_app = Path("/Applications/KiCad/KiCad.app")
            return kicad_app.exists()
        elif platform.system() == "Windows":
            # Check common Windows installation paths
            windows_paths = [
                Path("C:/Program Files/KiCad"),
                Path("C:/Program Files (x86)/KiCad"),
            ]
            return any(path.exists() for path in windows_paths)
        else:  # Linux
            # Check if kicad command is available
            import subprocess

            try:
                subprocess.run(["which", "kicad"], capture_output=True, check=True)
                return True
            except subprocess.CalledProcessError:
                return False
    except Exception:
        return False


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

    # Check if KiCad is installed
    if not check_kicad_installation():
        console.print("⚠️  KiCad not found on this system", style="yellow")
        if not Confirm.ask("Continue with plugin setup anyway?"):
            console.print("❌ Aborted", style="red")
            sys.exit(1)
    else:
        console.print("✅ KiCad installation detected", style="green")

    # Find plugin source files
    source_dir = find_plugin_source_files()
    if not source_dir:
        console.print("❌ Could not locate circuit-synth plugin files", style="red")
        console.print("   Make sure circuit-synth is properly installed", style="dim")
        sys.exit(1)

    console.print(f"📂 Found plugin files at: {source_dir}", style="green")

    # Get target directories
    plugin_dirs = get_kicad_plugin_directories()
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
