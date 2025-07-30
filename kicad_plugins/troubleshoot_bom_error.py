#!/usr/bin/env python3
"""
Troubleshoot KiCad BOM Plugin "Failed to create file" Error

This script helps diagnose and fix common issues with KiCad BOM plugin execution.
"""

import os
import sys
import stat
from pathlib import Path
import subprocess
import tempfile


def check_plugin_permissions():
    """Check if plugin files have correct permissions."""
    print("🔍 Checking Plugin File Permissions...")
    print("="*50)
    
    kicad_plugins_dir = Path.home() / "Documents" / "KiCad" / "9.0" / "scripting" / "plugins"
    
    plugins_to_check = [
        "circuit_synth_bom_plugin.py",
        "circuit_synth_claude_schematic_plugin.py", 
        "circuit_synth_chat_plugin.py",
        "claude_bridge.py"
    ]
    
    for plugin_name in plugins_to_check:
        plugin_path = kicad_plugins_dir / plugin_name
        
        if plugin_path.exists():
            file_stat = plugin_path.stat()
            permissions = stat.filemode(file_stat.st_mode)
            
            print(f"📄 {plugin_name}")
            print(f"   Path: {plugin_path}")
            print(f"   Permissions: {permissions}")
            print(f"   Owner: {file_stat.st_uid}")
            print(f"   Executable: {'✅ Yes' if os.access(plugin_path, os.X_OK) else '❌ No'}")
            print(f"   Readable: {'✅ Yes' if os.access(plugin_path, os.R_OK) else '❌ No'}")
            print()
            
            # Fix permissions if needed
            if not os.access(plugin_path, os.X_OK):
                print(f"🔧 Fixing permissions for {plugin_name}...")
                try:
                    plugin_path.chmod(plugin_path.stat().st_mode | stat.S_IEXEC)
                    print(f"✅ Fixed permissions for {plugin_name}")
                except Exception as e:
                    print(f"❌ Failed to fix permissions: {e}")
                print()
        else:
            print(f"❌ Missing: {plugin_name}")
            print(f"   Expected at: {plugin_path}")
            print()


def test_python_path():
    """Test the KiCad Python interpreter."""
    print("🐍 Testing KiCad Python Interpreter...")
    print("="*50)
    
    kicad_python = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
    
    if not Path(kicad_python).exists():
        print(f"❌ KiCad Python not found at: {kicad_python}")
        print("\n🔍 Looking for alternative Python paths...")
        
        # Check common KiCad Python locations
        alternative_paths = [
            "/Applications/KiCad/KiCad.app/Contents/MacOS/Python",
            "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3",
            "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.11/bin/python3",
        ]
        
        for alt_path in alternative_paths:
            if Path(alt_path).exists():
                print(f"✅ Found alternative: {alt_path}")
                kicad_python = alt_path
                break
        else:
            print("❌ No suitable Python interpreter found")
            return False
    
    print(f"📍 Using Python: {kicad_python}")
    
    # Test basic execution
    try:
        result = subprocess.run([kicad_python, "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Python version: {result.stdout.strip()}")
        else:
            print(f"❌ Python test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Python execution failed: {e}")
        return False
    
    # Test tkinter availability (needed for GUI)
    try:
        result = subprocess.run([kicad_python, "-c", "import tkinter; print('tkinter available')"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ tkinter is available")
        else:
            print("⚠️  tkinter may not be available - GUI plugins might not work")
            print(f"   Error: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not test tkinter: {e}")
    
    return True


def test_plugin_execution():
    """Test direct plugin execution."""
    print("\n🧪 Testing Plugin Execution...")
    print("="*50)
    
    kicad_plugins_dir = Path.home() / "Documents" / "KiCad" / "9.0" / "scripting" / "plugins"
    kicad_python = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
    
    # Create a test netlist file
    test_netlist_content = '''<?xml version="1.0" encoding="utf-8"?>
<export version="E">
  <design>
    <source>/tmp/test_circuit.kicad_sch</source>
    <date>Mon 29 Jul 2025 12:00:00 PM PST</date>
    <tool>Eeschema 9.0.0</tool>
  </design>
  <components>
    <comp ref="U1">
      <value>ESP32-S3</value>
      <libsource lib="RF_Module" part="ESP32-S3-WROOM-1" description=""/>
    </comp>
    <comp ref="C1">
      <value>100nF</value>
      <libsource lib="Device" part="C" description=""/>
    </comp>
  </components>
  <nets>
    <net code="1" name="VCC_3V3">
      <node ref="U1" pin="1"/>
      <node ref="C1" pin="1"/>
    </net>
  </nets>
</export>'''
    
    # Write test netlist to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_netlist:
        temp_netlist.write(test_netlist_content)
        temp_netlist_path = temp_netlist.name
    
    # Test each plugin
    plugins_to_test = [
        ("Basic BOM Plugin", "circuit_synth_bom_plugin.py"),
        ("Claude Plugin", "circuit_synth_claude_schematic_plugin.py"),
        ("Enhanced Chat Plugin", "circuit_synth_chat_plugin.py")
    ]
    
    for plugin_name, plugin_file in plugins_to_test:
        plugin_path = kicad_plugins_dir / plugin_file
        
        if not plugin_path.exists():
            print(f"⚠️  {plugin_name}: Plugin file not found")
            continue
        
        print(f"\n🔧 Testing {plugin_name}...")
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # Test plugin execution
            result = subprocess.run([
                kicad_python,
                str(plugin_path),
                temp_netlist_path,
                temp_output_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ {plugin_name}: Executed successfully")
                print(f"   Output: {result.stdout[:200]}..." if result.stdout else "   No stdout output")
                
                # Check if output file was created
                if Path(temp_output_path).exists() and Path(temp_output_path).stat().st_size > 0:
                    print(f"✅ Output file created successfully")
                else:
                    print(f"⚠️  Output file empty or not created")
                    
            else:
                print(f"❌ {plugin_name}: Execution failed")
                print(f"   Return code: {result.returncode}")
                print(f"   Stderr: {result.stderr}")
                print(f"   Stdout: {result.stdout}")
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {plugin_name}: Execution timed out (may be waiting for GUI)")
        except Exception as e:
            print(f"❌ {plugin_name}: Exception during execution: {e}")
        
        # Cleanup
        try:
            os.unlink(temp_output_path)
        except:
            pass
    
    # Cleanup test netlist
    try:
        os.unlink(temp_netlist_path)
    except:
        pass


def check_output_directory_permissions():
    """Check if KiCad can write to common output directories."""
    print("\n📁 Checking Output Directory Permissions...")
    print("="*50)
    
    directories_to_check = [
        Path.home() / "Documents",
        Path.home() / "Desktop", 
        Path("/tmp"),
        Path.home() / "Documents" / "KiCad" / "9.0",
    ]
    
    for directory in directories_to_check:
        if directory.exists():
            writable = os.access(directory, os.W_OK)
            print(f"📂 {directory}")
            print(f"   Writable: {'✅ Yes' if writable else '❌ No'}")
            
            if writable:
                # Test actual file creation
                test_file = directory / "kicad_test_write.tmp"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    print(f"   File creation: ✅ Success")
                except Exception as e:
                    print(f"   File creation: ❌ Failed - {e}")
            print()
        else:
            print(f"📂 {directory}: ❌ Does not exist")


def provide_solutions():
    """Provide solutions for common issues."""
    print("\n💡 Common Solutions for 'Failed to create file' Error:")
    print("="*60)
    
    print("""
🔧 SOLUTION 1: Fix File Permissions
   sudo chmod +x ~/Documents/KiCad/9.0/scripting/plugins/*.py
   
🔧 SOLUTION 2: Use Absolute Output Path
   In KiCad BOM dialog, try setting output to:
   /Users/$(whoami)/Desktop/circuit_analysis.txt
   
🔧 SOLUTION 3: Create Output Directory First
   mkdir -p ~/Documents/KiCad/9.0/output
   
🔧 SOLUTION 4: Test with Simple Plugin First
   Use the basic BOM plugin to test if the issue is plugin-specific
   
🔧 SOLUTION 5: Check KiCad Console
   In KiCad: Tools → Scripting Console
   Look for detailed error messages
   
🔧 SOLUTION 6: Run KiCad with Debug
   /Applications/KiCad/KiCad.app/Contents/MacOS/kicad --debug
   
🔧 SOLUTION 7: Use Alternative Python Command
   Try using 'python3' instead of the full KiCad Python path:
   python3 "%P" "%I" "%O"
""")


def main():
    """Main troubleshooting function."""
    print("🚨 KiCad BOM Plugin 'Failed to create file' Error Troubleshooter")
    print("="*70)
    
    # Run all checks
    check_plugin_permissions()
    
    if test_python_path():
        test_plugin_execution()
    
    check_output_directory_permissions()
    provide_solutions()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Fix any permission issues found above")
    print("2. Try the suggested solutions")
    print("3. Test with a simple schematic file")
    print("4. Check KiCad's scripting console for detailed errors")
    print("5. If still failing, try the basic plugin first before Claude integration")


if __name__ == "__main__":
    main()