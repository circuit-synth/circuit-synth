#!/usr/bin/env python3
"""
Simple one-command Rust acceleration enabler for circuit-synth.

This script compiles only the most impactful Rust modules:
- rust_kicad_schematic_writer: 6x faster KiCad generation
- rust_symbol_cache: 3-10x faster symbol lookups

Usage: python enable_rust_acceleration.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def check_prerequisites():
    """Check if Rust and maturin are available."""
    print("🔍 Checking prerequisites...")
    
    # Check Rust
    try:
        result = subprocess.run(['rustc', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("❌ Rust not found. Install with: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
            return False
        print(f"✅ Rust: {result.stdout.strip()}")
    except:
        print("❌ Rust not found. Install with: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
        return False
    
    # Check maturin
    try:
        result = subprocess.run(['maturin', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("❌ Maturin not found. Install with: pip install maturin")
            return False
        print(f"✅ Maturin: {result.stdout.strip()}")
    except:
        print("❌ Maturin not found. Install with: pip install maturin")
        return False
    
    return True


def compile_module(module_name, module_path):
    """Compile a single Rust module."""
    print(f"🔨 Compiling {module_name}...")
    
    try:
        os.chdir(module_path)
        start = time.time()
        
        result = subprocess.run(['maturin', 'develop', '--release'], 
                              capture_output=True, text=True, timeout=60)
        
        duration = time.time() - start
        
        if result.returncode == 0:
            print(f"✅ {module_name} compiled in {duration:.1f}s")
            return True
        else:
            print(f"❌ {module_name} failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ {module_name} error: {e}")
        return False


def test_modules():
    """Test that compiled modules work."""
    print("\n🧪 Testing compiled modules...")
    
    modules_to_test = [
        ("rust_kicad_schematic_writer", "KiCad S-expression generation"),
        ("rust_symbol_cache", "Symbol caching"),
        ("rust_force_directed_placement", "Component placement")
    ]
    
    working_count = 0
    for module, description in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {description} acceleration active")
            working_count += 1
        except ImportError:
            print(f"⚠️  {description} using Python fallback")
    
    return working_count


def main():
    """Main acceleration setup."""
    print("🚀 Circuit-Synth Rust Acceleration Setup")
    print("=" * 50)
    print("This will compile the most impactful performance modules:")
    print("  • KiCad generation: ~6x faster")
    print("  • Symbol caching: ~3-10x faster") 
    print("  • Component placement: ~10-50x faster")
    print()
    
    if not check_prerequisites():
        return False
    
    # Find modules to compile (only the most important ones)
    rust_dir = Path(__file__).parent / "rust_modules"
    priority_modules = [
        "rust_kicad_integration",
        "rust_symbol_cache", 
        "rust_force_directed_placement"
    ]
    
    print(f"\n🎯 Compiling {len(priority_modules)} high-impact modules...")
    
    original_cwd = os.getcwd()
    compiled_count = 0
    
    try:
        for module_name in priority_modules:
            module_path = rust_dir / module_name
            if module_path.exists():
                if compile_module(module_name, module_path):
                    compiled_count += 1
            else:
                print(f"⚠️  {module_name} not found, skipping")
    finally:
        os.chdir(original_cwd)
    
    # Test results
    working_count = test_modules()
    
    print(f"\n📊 Results:")
    print(f"   Compiled: {compiled_count}/{len(priority_modules)} modules")
    print(f"   Working: {working_count} modules")
    
    if working_count > 0:
        print(f"\n🎉 SUCCESS! Circuit-synth now has Rust acceleration!")
        print(f"🚀 Performance improvements active for {working_count} modules")
        print(f"\n💡 Test with: uv run python examples/example_kicad_project.py")
    else:
        print(f"\n⚠️  No acceleration enabled, using Python fallbacks")
        print(f"💡 Circuit-synth will still work perfectly!")
    
    return working_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)