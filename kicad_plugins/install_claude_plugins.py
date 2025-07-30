#!/usr/bin/env python3
"""
Enhanced KiCad Plugin Installer for Circuit-Synth AI with Claude Integration

This script installs all Circuit-Synth AI plugins including the new Claude Code integration.
"""

import os
import sys
import shutil
import platform
from pathlib import Path
import stat


def get_kicad_directories():
    """Get both KiCad plugins and scripting directories for the current platform."""
    system = platform.system()
    home = Path.home()
    
    if system == "Darwin":  # macOS
        base_candidates = [
            home / "Documents" / "KiCad" / "9.0",
            home / "Documents" / "KiCad" / "8.0",  # fallback
        ]
    elif system == "Linux":
        base_candidates = [
            home / ".local" / "share" / "kicad" / "9.0",
            home / ".local" / "share" / "kicad",
        ]
    elif system == "Windows":
        documents = Path(os.environ.get("USERPROFILE", str(home))) / "Documents"
        base_candidates = [
            documents / "KiCad" / "9.0",
            documents / "KiCad" / "8.0",  # fallback
        ]
    else:
        print(f"Unsupported platform: {system}")
        return None, None
    
    # Return the first existing base directory, or the first candidate for creation
    for base in base_candidates:
        if base.exists():
            return base / "scripting" / "plugins", base / "plugins"
    
    # If none exist, use the first candidate
    base = base_candidates[0]
    return base / "scripting" / "plugins", base / "plugins"


def install_claude_bridge():
    """Install the Claude bridge module."""
    source_file = Path(__file__).parent / "claude_bridge.py"
    
    if not source_file.exists():
        print(f"❌ Error: Claude bridge not found: {source_file}")
        return False
    
    scripting_dir, _ = get_kicad_directories()
    if not scripting_dir:
        print("❌ Error: Could not determine KiCad directories")
        return False
    
    try:
        # Create scripting directory if it doesn't exist
        scripting_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy Claude bridge
        target_file = scripting_dir / "claude_bridge.py"
        shutil.copy2(source_file, target_file)
        
        # Make it executable on Unix systems
        if platform.system() != "Windows":
            target_file.chmod(target_file.stat().st_mode | stat.S_IEXEC)
        
        print(f"✅ Claude bridge installed: {target_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error installing Claude bridge: {e}")
        return False


def install_pcb_plugin():
    """Install the enhanced PCB editor plugin with Claude integration."""
    plugin_source = Path(__file__).parent / "circuit_synth_ai"
    
    if not plugin_source.exists():
        print(f"❌ Error: PCB plugin source not found: {plugin_source}")
        return False
    
    scripting_dir, _ = get_kicad_directories()
    if not scripting_dir:
        print("❌ Error: Could not determine KiCad directories")
        return False
    
    try:
        # Create scripting directory if it doesn't exist
        scripting_dir.mkdir(parents=True, exist_ok=True)
        
        # Install the plugin
        plugin_target = scripting_dir / "circuit_synth_ai"
        
        # Remove existing installation if it exists
        if plugin_target.exists():
            print(f"🔄 Removing existing PCB plugin: {plugin_target}")
            shutil.rmtree(plugin_target)
        
        # Copy the plugin
        print(f"📦 Installing PCB plugin from {plugin_source} to {plugin_target}")
        shutil.copytree(plugin_source, plugin_target)
        
        print(f"✅ PCB plugin installed: {plugin_target}")
        return True
        
    except Exception as e:
        print(f"❌ Error installing PCB plugin: {e}")
        return False


def install_schematic_plugins():
    """Install the schematic editor plugins."""
    scripting_dir, _ = get_kicad_directories()
    if not scripting_dir:
        print("❌ Error: Could not determine KiCad directories")
        return False
    
    # List of schematic plugins to install
    schematic_plugins = [
        "circuit_synth_chat_plugin.py",  # Enhanced chat plugin
        "circuit_synth_claude_schematic_plugin.py",  # Claude-integrated plugin
        "circuit_synth_bom_plugin.py",  # Basic BOM plugin
    ]
    
    success_count = 0
    
    for plugin_name in schematic_plugins:
        source_file = Path(__file__).parent / plugin_name
        
        if not source_file.exists():
            print(f"⚠️  Warning: Schematic plugin not found: {source_file}")
            continue
        
        try:
            # Create scripting directory if it doesn't exist
            scripting_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy plugin
            target_file = scripting_dir / plugin_name
            shutil.copy2(source_file, target_file)
            
            # Make it executable on Unix systems
            if platform.system() != "Windows":
                target_file.chmod(target_file.stat().st_mode | stat.S_IEXEC)
            
            print(f"✅ Schematic plugin installed: {target_file}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error installing {plugin_name}: {e}")
    
    return success_count > 0


def setup_bom_plugin_instructions():
    """Provide instructions for setting up the BOM plugins."""
    print("\n" + "="*60)
    print("📋 BOM PLUGIN SETUP INSTRUCTIONS")
    print("="*60)
    
    print("""
To use the schematic plugins, you need to add them to KiCad's BOM tools:

🔧 SETUP STEPS:

1. Open KiCad Schematic Editor
2. Go to: Tools → Generate Bill of Materials
3. Click the "+" button to add a plugin
4. Browse to your KiCad scripting directory and select:

   📄 For Enhanced Chat Plugin:
   • File: circuit_synth_chat_plugin.py
   • Nickname: "Circuit-Synth AI Chat"
   • Command: python3 "%I" "%O"

   🤖 For Claude Integration Plugin:
   • File: circuit_synth_claude_schematic_plugin.py  
   • Nickname: "Circuit-Synth AI Claude Chat"
   • Command: python3 "%I" "%O"

   📊 For Basic Analysis Plugin:
   • File: circuit_synth_bom_plugin.py
   • Nickname: "Circuit-Synth AI Analysis"
   • Command: python3 "%I" "%O"

5. Save the configuration

⌨️  HOTKEY SETUP:

1. Go to: Preferences → Hotkeys
2. Search for: "Generate Legacy Bill of Materials"
3. Assign hotkey: Ctrl+Shift+A
4. Apply and close

🚀 USAGE:

• Press Ctrl+Shift+A in schematic editor
• Select your preferred Circuit-Synth AI plugin
• Click "Generate" to launch the AI assistant!
""")


def test_claude_availability():
    """Test if Claude CLI is available for integration."""
    print("\n🧪 Testing Claude Code Integration...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["claude", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Claude CLI is available!")
            print(f"   📋 Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Claude CLI found but not responding correctly")
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Claude CLI not found")
    
    print("""
💡 To enable Claude integration:

1. Install Claude CLI:
   macOS: brew install claude-cli
   Linux: Download from GitHub releases
   Windows: Use Chocolatey or download directly

2. Set up API key:
   claude configure set api_key YOUR_API_KEY

3. Test: claude "Hello Claude!"

4. Re-run the plugins to get real AI assistance!
""")
    
    return False


def main():
    """Main installer function."""
    print("🚀 Circuit-Synth AI Enhanced Plugin Installer with Claude Integration")
    print("="*80)
    
    # Show what will be installed
    print("\n📦 Installing the following components:")
    print("   • Enhanced PCB Editor Plugin (with Claude chat)")
    print("   • Claude Bridge Communication Module")
    print("   • Enhanced Schematic Chat Plugin")
    print("   • Claude-Integrated Schematic Plugin")
    print("   • Basic BOM Analysis Plugin")
    
    # Check directories
    scripting_dir, plugins_dir = get_kicad_directories()
    print(f"\n📁 Target directories:")
    print(f"   • Scripting: {scripting_dir}")
    print(f"   • Plugins: {plugins_dir}")
    
    success_count = 0
    total_components = 3
    
    # Install Claude bridge
    print(f"\n🔗 Installing Claude Bridge...")
    if install_claude_bridge():
        success_count += 1
    
    # Install PCB plugin
    print(f"\n🖥️  Installing PCB Editor Plugin...")
    if install_pcb_plugin():
        success_count += 1
    
    # Install schematic plugins
    print(f"\n📐 Installing Schematic Plugins...")
    if install_schematic_plugins():
        success_count += 1
    
    # Test Claude availability
    claude_available = test_claude_availability()
    
    # Summary
    print(f"\n" + "="*80)
    print(f"🎯 INSTALLATION SUMMARY")
    print(f"="*80)
    print(f"✅ Successfully installed: {success_count}/{total_components} components")
    print(f"🤖 Claude integration: {'✅ Ready' if claude_available else '❌ Needs setup'}")
    
    if success_count == total_components:
        print("\n🎉 All plugins installed successfully!")
        
        # Provide setup instructions
        setup_bom_plugin_instructions()
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Restart KiCad if it's currently running")
        print(f"2. Set up BOM plugins using instructions above")
        print(f"3. Configure hotkey (Ctrl+Shift+A) for quick access")
        if not claude_available:
            print(f"4. Install and configure Claude CLI for real AI assistance")
        print(f"5. Test the plugins in both PCB and schematic editors")
        
        print(f"\n🎯 USAGE:")
        print(f"• PCB Editor: Tools → External Plugins → Circuit-Synth AI")
        print(f"• Schematic Editor: Ctrl+Shift+A → Select AI plugin → Generate")
        
        return True
    else:
        print(f"\n❌ Some components failed to install")
        print(f"Please check the error messages above and try again")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)