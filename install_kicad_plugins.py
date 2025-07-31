#!/usr/bin/env python3
"""
Circuit-Synth KiCad Plugin Installer

This script installs Circuit-Synth plugins for both KiCad PCB Editor and Schematic Editor.
Can be run from anywhere after installing the circuit-synth package.
"""

import os
import sys
import shutil
from pathlib import Path
import platform

def get_kicad_directories():
    """Get KiCad plugin directories for the current platform."""
    system = platform.system().lower()
    home = Path.home()
    
    if system == "darwin":  # macOS
        base_dir = home / "Documents" / "KiCad" / "9.0"
        return {
            "pcb_plugins": base_dir / "scripting" / "plugins",
            "bom_plugins": base_dir / "scripting" / "plugins",  # BOM plugins also go in scripting/plugins
        }
    elif system == "linux":
        base_dir = home / ".config" / "kicad" / "9.0"
        return {
            "pcb_plugins": base_dir / "scripting" / "plugins", 
            "bom_plugins": base_dir / "scripting" / "plugins",  # BOM plugins also go in scripting/plugins
        }
    elif system == "windows":
        base_dir = home / "Documents" / "KiCad" / "9.0"
        return {
            "pcb_plugins": base_dir / "scripting" / "plugins",
            "bom_plugins": base_dir / "scripting" / "plugins",  # BOM plugins also go in scripting/plugins
        }
    else:
        raise ValueError(f"Unsupported platform: {system}")

def find_circuit_synth_plugins():
    """Find circuit-synth plugin files from multiple possible locations."""
    # Try multiple search strategies
    search_paths = []
    
    # 1. Check if running from repository
    script_dir = Path(__file__).parent
    if (script_dir / "kicad_plugins").exists():
        return script_dir
    
    # 2. Check if circuit_synth package is installed
    try:
        import circuit_synth
        pkg_path = Path(circuit_synth.__file__).parent
        if (pkg_path / ".." / "kicad_plugins").exists():
            return pkg_path / ".."
        if (pkg_path / "kicad_plugins").exists():
            return pkg_path
    except ImportError:
        pass
    
    # 3. Check common development locations
    common_locations = [
        Path.home() / "circuit-synth",
        Path.home() / "Desktop" / "circuit-synth", 
        Path.home() / "Documents" / "circuit-synth",
        Path.home() / "Projects" / "circuit-synth",
        Path.cwd() / "circuit-synth",
        Path.cwd(),
    ]
    
    for location in common_locations:
        if location.exists() and (location / "kicad_plugins").exists():
            return location
    
    return None

def install_plugins():
    """Install Circuit-Synth KiCad plugins."""
    print("🚀 Circuit-Synth KiCad Plugin Installer")
    print("=" * 50)
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    
    # Find plugin files
    repo_root = find_circuit_synth_plugins()
    if not repo_root:
        print("❌ Error: Could not find circuit-synth plugin files!")
        print("\n🔍 Searched in:")
        print("   - Current directory and script location")
        print("   - Installed circuit_synth package location")
        print("   - Common development directories")
        print("\n💡 Solutions:")
        print("   1. Run this script from the circuit-synth repository root")
        print("   2. Install circuit-synth package: pip install circuit-synth")
        print("   3. Clone repository: git clone <circuit-synth-repo>")
        sys.exit(1)
    
    print(f"📁 Found circuit-synth plugins at: {repo_root}")
    
    # Check required directories exist
    kicad_plugins_dir = repo_root / "kicad_plugins"
    bom_plugins_dir = repo_root / "kicad_bom_plugins"
    
    if not kicad_plugins_dir.exists():
        print(f"❌ Error: {kicad_plugins_dir} not found!")
        sys.exit(1)
    
    if not bom_plugins_dir.exists():
        print(f"❌ Error: {bom_plugins_dir} not found!")
        sys.exit(1)
    
    # Get KiCad directories
    try:
        kicad_dirs = get_kicad_directories()
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print(f"📂 Installing to KiCad directories:")
    for name, path in kicad_dirs.items():
        print(f"   {name}: {path}")
    
    # Create directories if they don't exist
    for path in kicad_dirs.values():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {path}")
    
    # Install PCB plugins
    print(f"\n📐 Installing PCB Editor plugins...")
    pcb_plugins_src = kicad_plugins_dir
    pcb_plugins_dst = kicad_dirs["pcb_plugins"]
    
    # Install external PCB Claude chat plugin (most compatible)
    pcb_external_plugin = pcb_plugins_src / "circuit_synth_pcb_external_chat.py"
    if pcb_external_plugin.exists():
        shutil.copy2(pcb_external_plugin, pcb_plugins_dst / "circuit_synth_pcb_external_chat.py")
        print(f"✅ Installed: circuit_synth_pcb_external_chat.py")
    else:
        print(f"⚠️  Warning: circuit_synth_pcb_external_chat.py not found")
    
    # Install enhanced PCB Claude chat plugin (tkinter version)
    pcb_chat_plugin = pcb_plugins_src / "circuit_synth_pcb_claude_chat.py"
    if pcb_chat_plugin.exists():
        shutil.copy2(pcb_chat_plugin, pcb_plugins_dst / "circuit_synth_pcb_claude_chat.py")
        print(f"✅ Installed: circuit_synth_pcb_claude_chat.py (tkinter)")
    else:
        print(f"⚠️  Warning: circuit_synth_pcb_claude_chat.py not found")
    
    # Install simple PCB plugin as backup
    simple_plugin = pcb_plugins_src / "circuit_synth_simple_ai.py"
    if simple_plugin.exists():
        shutil.copy2(simple_plugin, pcb_plugins_dst / "circuit_synth_simple_ai.py")
        print(f"✅ Installed: circuit_synth_simple_ai.py (backup)")
    else:
        print(f"⚠️  Warning: circuit_synth_simple_ai.py not found")
    
    # Install Claude bridge dependency
    claude_bridge = pcb_plugins_src / "claude_bridge.py"
    if claude_bridge.exists():
        shutil.copy2(claude_bridge, pcb_plugins_dst / "claude_bridge.py")
        print(f"✅ Installed: claude_bridge.py")
    else:
        print(f"⚠️  Warning: claude_bridge.py not found in kicad_plugins")
    
    # Install BOM plugins (Schematic Editor)
    print(f"\n📋 Installing Schematic Editor (BOM) plugins...")
    bom_plugins_src = bom_plugins_dir
    bom_plugins_dst = kicad_dirs["bom_plugins"]
    
    # Install BOM plugin
    bom_plugin = bom_plugins_src / "circuit_synth_bom_plugin.py"
    if bom_plugin.exists():
        shutil.copy2(bom_plugin, bom_plugins_dst / "circuit_synth_bom_plugin.py")
        print(f"✅ Installed: circuit_synth_bom_plugin.py")
    else:
        print(f"⚠️  Warning: circuit_synth_bom_plugin.py not found")
    
    # Install Claude bridge for BOM plugin
    bom_claude_bridge = bom_plugins_src / "claude_bridge.py"
    if bom_claude_bridge.exists():
        shutil.copy2(bom_claude_bridge, bom_plugins_dst / "claude_bridge.py")
        print(f"✅ Installed: claude_bridge.py (for BOM plugin)")
    else:
        print(f"⚠️  Warning: claude_bridge.py not found in kicad_bom_plugins")
    
    print(f"\n🎉 Installation Complete!")
    print(f"\n📖 Usage Instructions:")
    print(f"")
    print(f"PCB Editor:")
    print(f"  1. Open KiCad PCB Editor")
    print(f"  2. Look for 'Circuit-Synth PCB Chat (External)' toolbar button")
    print(f"  3. Click to launch external Claude AI chat with PCB context")
    print(f"  Note: External version avoids tkinter compatibility issues")
    print(f"")
    print(f"Schematic Editor:")
    print(f"  1. Open KiCad Schematic Editor")
    print(f"  2. Go to Tools → Generate Bill of Materials")
    print(f"  3. Add Plugin: {bom_plugins_dst / 'circuit_synth_bom_plugin.py'}")
    print(f"  4. Click Generate for Claude AI chat interface")
    print(f"")
    print(f"🔧 Troubleshooting:")
    print(f"  - Restart KiCad after installation")
    print(f"  - Check KiCad → Preferences → Plugin paths")
    print(f"  - For Claude integration, install Claude CLI: https://claude.ai/code")

def main():
    """Main entry point for console script."""
    try:
        install_plugins()
    except KeyboardInterrupt:
        print(f"\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()