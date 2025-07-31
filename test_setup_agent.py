#!/usr/bin/env python3
"""
Test script for circuit-synth first setup agent functionality.
This script validates the setup process that the agent would perform.
"""

import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path

def test_platform_detection():
    """Test platform detection logic."""
    print("🖥️  Testing Platform Detection...")
    system = platform.system().lower()
    print(f"   Platform: {system}")
    
    if system in ["darwin", "linux", "windows"]:
        print("   ✅ Platform detection: PASS")
        return True
    else:
        print("   ❌ Platform detection: FAIL")
        return False

def test_python_environment():
    """Test Python environment detection."""
    print("🐍 Testing Python Environment...")
    
    # Check Python version
    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("   ✅ Python version: PASS")
    else:
        print("   ❌ Python version: FAIL (requires 3.8+)")
        return False
    
    # Check uv availability
    try:
        result = subprocess.run(['which', 'uv'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ uv available: {result.stdout.strip()}")
        else:
            print("   ⚠️  uv not found (recommended for optimal experience)")
    except:
        print("   ⚠️  uv check failed")
    
    return True

def test_kicad_detection():
    """Test KiCad installation detection."""
    print("🔧 Testing KiCad Detection...")
    
    system = platform.system().lower()
    kicad_paths = []
    
    if system == "darwin":
        kicad_paths = [
            "/Applications/KiCad/KiCad.app",
            "/Applications/KiCad.app"
        ]
    elif system == "linux":
        kicad_paths = [
            "/usr/bin/kicad",
            "/usr/local/bin/kicad"
        ]
    elif system == "windows":
        kicad_paths = [
            "C:\\Program Files\\KiCad\\bin\\kicad.exe",
            "C:\\Program Files (x86)\\KiCad\\bin\\kicad.exe"
        ]
    
    found_kicad = False
    for path in kicad_paths:
        if Path(path).exists():
            print(f"   ✅ KiCad found: {path}")
            found_kicad = True
            break
    
    if not found_kicad:
        print("   ⚠️  KiCad not detected (install from https://kicad.org)")
    
    return found_kicad

def test_claude_cli_detection():
    """Test Claude CLI detection."""
    print("🤖 Testing Claude CLI Detection...")
    
    try:
        # Try direct claude command
        result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
        if result.returncode == 0:
            claude_path = result.stdout.strip()
            print(f"   ✅ Claude CLI found: {claude_path}")
            
            # Test version
            version_result = subprocess.run([claude_path, '--version'], 
                                          capture_output=True, text=True, timeout=10)
            if version_result.returncode == 0:
                print(f"   ✅ Claude version: {version_result.stdout.strip()}")
                return True
            else:
                print("   ⚠️  Claude CLI found but version check failed")
                return False
        else:
            print("   ❌ Claude CLI not found")
            print("   💡 Install: npm install -g @anthropic-ai/claude-cli")
            return False
    except Exception as e:
        print(f"   ❌ Claude CLI test error: {e}")
        return False

def test_circuit_synth_import():
    """Test circuit-synth package import."""
    print("📦 Testing Circuit-Synth Import...")
    
    try:
        import circuit_synth
        print(f"   ✅ circuit-synth imported successfully")
        print(f"   📍 Location: {circuit_synth.__file__}")
        return True
    except ImportError as e:
        print(f"   ❌ circuit-synth import failed: {e}")
        print("   💡 Install: pip install circuit-synth")
        return False

def test_kicad_plugin_installer():
    """Test KiCad plugin installer functionality."""
    print("🔌 Testing KiCad Plugin Installer...")
    
    installer_path = Path("install_kicad_plugins.py")
    if installer_path.exists():
        print(f"   ✅ Plugin installer found: {installer_path}")
        
        # Test installer import (dry run)  
        try:
            with open(installer_path, 'r') as f:
                content = f.read()
                if "get_kicad_directories" in content and "install_plugins" in content:
                    print("   ✅ Installer structure: PASS")
                    return True
                else:
                    print("   ❌ Installer structure: FAIL")
                    return False
        except Exception as e:
            print(f"   ❌ Installer test error: {e}")
            return False
    else:
        print("   ❌ Plugin installer not found")
        return False

def test_claude_agents_setup():
    """Test Claude agents and commands setup."""
    print("🎯 Testing Claude Agents Setup...")
    
    claude_dir = Path(".claude")
    if not claude_dir.exists():
        print("   ❌ .claude directory not found")
        return False
    
    agents_dir = claude_dir / "agents"
    commands_dir = claude_dir / "commands"
    
    # Check required agents
    required_agents = [
        "first_setup_agent.md",
        "circuit_generation_agent.md"
    ]
    
    agents_found = 0
    for agent in required_agents:
        agent_path = agents_dir / agent
        if agent_path.exists():
            print(f"   ✅ Agent found: {agent}")
            agents_found += 1
        else:
            print(f"   ❌ Agent missing: {agent}")
    
    # Check required commands
    required_commands = [
        "setup_circuit_synth.md",
        "find_stm32.md",
        "generate_circuit.md"
    ]
    
    commands_found = 0
    for command in required_commands:
        command_path = commands_dir / command
        if command_path.exists():
            print(f"   ✅ Command found: {command}")
            commands_found += 1
        else:
            print(f"   ❌ Command missing: {command}")
    
    success = (agents_found == len(required_agents) and 
              commands_found == len(required_commands))
    
    if success:
        print("   ✅ Claude agents setup: PASS")
    else:
        print("   ❌ Claude agents setup: FAIL")
    
    return success

def test_example_circuit():
    """Test example circuit generation."""
    print("⚡ Testing Example Circuit Generation...")
    
    example_path = Path("examples/example_kicad_project.py")
    if not example_path.exists():
        print("   ❌ Example circuit not found")
        return False
    
    print(f"   ✅ Example found: {example_path}")
    
    # Note: We don't actually run the example here to avoid creating files
    # In a real setup agent, this would be executed to verify functionality
    print("   ℹ️  Example execution would be tested in full setup")
    
    return True

def main():
    """Run all setup validation tests."""
    print("🚀 Circuit-Synth Setup Agent Validation Tests")
    print("=" * 60)
    
    tests = [
        ("Platform Detection", test_platform_detection),
        ("Python Environment", test_python_environment),
        ("KiCad Detection", test_kicad_detection),
        ("Claude CLI Detection", test_claude_cli_detection),
        ("Circuit-Synth Import", test_circuit_synth_import),
        ("KiCad Plugin Installer", test_kicad_plugin_installer),
        ("Claude Agents Setup", test_claude_agents_setup),
        ("Example Circuit", test_example_circuit),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup agent ready for deployment.")
        return 0
    elif passed >= total * 0.75:
        print("⚠️  Most tests passed. Minor issues to resolve.")
        return 1
    else:
        print("❌ Significant issues found. Setup requires attention.")
        return 2

if __name__ == "__main__":
    sys.exit(main())