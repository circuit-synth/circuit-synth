#!/usr/bin/env python3
"""
Verify Circuit-Synth AI Plugin Installation

Quick verification script to ensure all components are properly installed.
"""

import sys
from pathlib import Path
import platform


def get_kicad_scripting_dir():
    """Get the KiCad scripting directory."""
    home = Path.home()
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return home / "Documents" / "KiCad" / "9.0" / "scripting" / "plugins"
    elif system == "Linux":
        return home / ".local" / "share" / "kicad" / "9.0" / "scripting" / "plugins"
    elif system == "Windows":
        documents = Path.home() / "Documents"
        return documents / "KiCad" / "9.0" / "scripting" / "plugins"
    
    return None


def verify_installation():
    """Verify all plugin components are installed."""
    print("🔍 Circuit-Synth AI Plugin Installation Verification")
    print("="*60)
    
    scripting_dir = get_kicad_scripting_dir()
    if not scripting_dir or not scripting_dir.exists():
        print(f"❌ KiCad scripting directory not found: {scripting_dir}")
        return False
    
    print(f"📁 Checking directory: {scripting_dir}")
    
    # Files to check
    required_files = {
        "claude_bridge.py": "Claude Code integration bridge",
        "circuit_synth_ai/": "Enhanced PCB editor plugin (directory)",
        "circuit_synth_ai/__init__.py": "PCB plugin initialization",
        "circuit_synth_ai/plugin_action.py": "PCB plugin main action",
        "circuit_synth_ai/ui/claude_chat_dialog.py": "PCB Claude chat interface",
        "circuit_synth_chat_plugin.py": "Enhanced schematic chat plugin",
        "circuit_synth_claude_schematic_plugin.py": "Claude-integrated schematic plugin",
        "circuit_synth_bom_plugin.py": "Basic BOM analysis plugin"
    }
    
    found_count = 0
    total_count = len(required_files)
    
    for file_path, description in required_files.items():
        full_path = scripting_dir / file_path
        
        if full_path.exists():
            print(f"✅ {description}")
            print(f"   → {full_path}")
            found_count += 1
        else:
            print(f"❌ MISSING: {description}")
            print(f"   → Expected: {full_path}")
    
    print(f"\n📊 Installation Status: {found_count}/{total_count} components found")
    
    # Test Claude bridge import
    print(f"\n🧪 Testing Claude Bridge Import...")
    try:
        sys.path.insert(0, str(scripting_dir))
        import claude_bridge
        print("✅ Claude bridge imports successfully")
        
        # Test basic functionality
        circuit_data = claude_bridge.CircuitData()
        circuit_data.project_name = "test_verification"
        context = circuit_data.to_claude_context()
        
        if "test_verification" in context:
            print("✅ Claude bridge basic functionality works")
        else:
            print("⚠️  Claude bridge context generation issue")
        
    except ImportError as e:
        print(f"❌ Claude bridge import failed: {e}")
    except Exception as e:
        print(f"⚠️  Claude bridge test error: {e}")
    
    # Test Claude CLI availability
    print(f"\n🤖 Testing Claude CLI...")
    try:
        import subprocess
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✅ Claude CLI available: {result.stdout.strip()}")
        else:
            print(f"⚠️  Claude CLI issue: {result.stderr}")
    except Exception as e:
        print(f"❌ Claude CLI not available: {e}")
    
    # Summary
    success = found_count == total_count
    
    print(f"\n" + "="*60)
    if success:
        print("🎉 VERIFICATION SUCCESSFUL!")
        print("\n🚀 Your Circuit-Synth AI plugins are ready to use:")
        print("   • PCB Editor: Tools → External Plugins → Circuit-Synth AI")
        print("   • Schematic Editor: Tools → Generate Bill of Materials → Add plugins")
        print("\n💡 Next Steps:")
        print("   1. Restart KiCad if it's running")
        print("   2. Add schematic plugins to BOM tools")
        print("   3. Set up Ctrl+Shift+A hotkey")
        print("   4. Test with real circuit files!")
        
    else:
        print("❌ VERIFICATION FAILED!")
        print("\n🔧 Troubleshooting:")
        print("   1. Re-run the installer: python install_claude_plugins.py")
        print("   2. Check file permissions")
        print("   3. Verify KiCad directory structure")
    
    return success


if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)