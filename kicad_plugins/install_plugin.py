#!/usr/bin/env python3
"""
KiCad Plugin Installer for Circuit-Synth AI

This script installs the Circuit-Synth AI plugin to the appropriate KiCad directory.
"""

import os
import sys
import shutil
import platform
from pathlib import Path


def get_kicad_plugins_directory():
    """Get the KiCad plugins directory for the current platform."""
    system = platform.system()
    home = Path.home()
    
    if system == "Darwin":  # macOS
        candidates = [
            home / "Documents" / "KiCad" / "9.0" / "plugins",
            home / "Documents" / "KiCad" / "8.0" / "plugins", # fallback
            home / "Library" / "Application Support" / "kicad" / "plugins"
        ]
    elif system == "Linux":
        candidates = [
            home / ".local" / "share" / "kicad" / "9.0" / "plugins",
            home / ".local" / "share" / "kicad" / "plugins",
            Path("/usr/share/kicad/plugins")
        ]
    elif system == "Windows":
        documents = Path(os.environ.get("USERPROFILE", str(home))) / "Documents"
        candidates = [
            documents / "KiCad" / "9.0" / "plugins",
            documents / "KiCad" / "8.0" / "plugins", # fallback
            Path(os.environ.get("APPDATA", "")) / "kicad" / "plugins"
        ]
    else:
        print(f"Unsupported platform: {system}")
        return None
    
    # Return the first existing directory, or the first candidate for creation
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    return candidates[0] if candidates else None


def install_plugin():
    """Install the Circuit-Synth AI plugin to KiCad."""
    plugin_source = Path(__file__).parent / "circuit_synth_ai"
    
    if not plugin_source.exists():
        print(f"Error: Plugin source directory not found: {plugin_source}")
        return False
    
    kicad_plugins_dir = get_kicad_plugins_directory()
    if not kicad_plugins_dir:
        print("Error: Could not determine KiCad plugins directory")
        return False
    
    print(f"KiCad plugins directory: {kicad_plugins_dir}")
    
    # Create the plugins directory if it doesn't exist
    try:
        kicad_plugins_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created plugins directory: {kicad_plugins_dir}")
    except Exception as e:
        print(f"Error creating plugins directory: {e}")
        return False
    
    # Install the plugin
    plugin_target = kicad_plugins_dir / "circuit_synth_ai"
    
    try:
        # Remove existing installation if it exists
        if plugin_target.exists():
            print(f"Removing existing installation: {plugin_target}")
            shutil.rmtree(plugin_target)
        
        # Copy the plugin
        print(f"Installing plugin from {plugin_source} to {plugin_target}")
        shutil.copytree(plugin_source, plugin_target)
        
        print("✅ Plugin installed successfully!")
        print(f"Plugin location: {plugin_target}")
        
        return True
        
    except Exception as e:
        print(f"Error installing plugin: {e}")
        return False


def test_plugin():
    """Test the plugin installation by running it directly."""
    plugin_dir = Path(__file__).parent / "circuit_synth_ai"
    main_script = plugin_dir / "main.py"
    
    if not main_script.exists():
        print(f"Error: Plugin main script not found: {main_script}")
        return False
    
    print("Testing plugin...")
    
    try:
        # Test the plugin by running it with the test action
        import subprocess
        result = subprocess.run([
            sys.executable, 
            str(main_script), 
            "test"
        ], capture_output=True, text=True, timeout=30)
        
        print(f"Plugin test result: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Plugin test timed out (this may be normal for GUI applications)")
        return True
    except Exception as e:
        print(f"Error testing plugin: {e}")
        return False


def main():
    """Main installer function."""
    print("Circuit-Synth AI KiCad Plugin Installer")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Running plugin test...")
        success = test_plugin()
    else:
        print("Installing plugin...")
        success = install_plugin()
        
        if success:
            print("\nNext steps:")
            print("1. Restart KiCad if it's currently running")
            print("2. Open KiCad PCB Editor")
            print("3. Look for 'Circuit-Synth AI' in the Tools menu or toolbar")
            
            # Optionally test the plugin in interactive mode
            try:
                if input("\nWould you like to test the plugin now? (y/n): ").lower().startswith('y'):
                    print("\nTesting plugin...")
                    test_success = test_plugin()
                    if not test_success:
                        print("⚠️  Plugin test failed, but installation may still work in KiCad")
            except (EOFError, KeyboardInterrupt):
                print("\nSkipping plugin test (non-interactive mode)")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()