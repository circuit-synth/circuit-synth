#!/usr/bin/env python3
"""
Circuit-synth Environment Validation Script
Checks for common environment issues that cause placement problems
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_path():
    """Check if circuit-synth is imported from the correct location."""
    print("🔍 Checking Python import path...")
    
    try:
        # Add local paths to search
        possible_paths = [
            "./submodules/circuit-synth/src",  # From parent directory
            "./src",                          # From circuit-synth directory
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                sys.path.insert(0, path)
                break
        
        import circuit_synth
        location = circuit_synth.__file__
        
        if "submodules/circuit-synth" in location:
            print(f"   ✅ Using local submodule: {location}")
            return True
        else:
            print(f"   ❌ Using pip package: {location}")
            print("   🔧 Run ./scripts/ensure-clean-environment.sh to fix")
            return False
            
    except ImportError as e:
        print(f"   ❌ Cannot import circuit_synth: {e}")
        return False

def check_submodule_status():
    """Check if submodules are properly initialized."""
    print("🔍 Checking submodule status...")
    
    # Check if we're inside circuit-synth directory
    if Path(".git").exists() and Path("src/circuit_synth").exists():
        print("   ✅ Running from within circuit-synth repository")
        return True
    
    submodule_path = Path("submodules/circuit-synth")
    if not submodule_path.exists():
        print("   ❌ circuit-synth submodule not found")
        return False
    
    if not (submodule_path / ".git").exists():
        print("   ❌ circuit-synth submodule not initialized")
        print("   🔧 Run: git submodule update --init --recursive")
        return False
    
    try:
        # Check submodule commit
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=submodule_path,
            capture_output=True,
            text=True,
            check=True
        )
        commit = result.stdout.strip()
        print(f"   ✅ Submodule at: {commit}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Cannot check submodule status: {e}")
        return False

def check_cache_files():
    """Check for Python cache files that might cause issues."""
    print("🔍 Checking for problematic cache files...")
    
    cache_dirs = list(Path(".").rglob("__pycache__"))
    pyc_files = list(Path(".").rglob("*.pyc"))
    
    if cache_dirs or pyc_files:
        print(f"   ⚠️  Found {len(cache_dirs)} cache dirs, {len(pyc_files)} .pyc files")
        print("   🔧 Consider running: find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null")
        return False
    else:
        print("   ✅ No problematic cache files found")
        return True

def check_virtual_environment():
    """Check virtual environment status."""
    print("🔍 Checking virtual environment...")
    
    if "VIRTUAL_ENV" in os.environ:
        venv_path = os.environ["VIRTUAL_ENV"]
        print(f"   ✅ Active virtual environment: {venv_path}")
        return True
    elif Path(".venv").exists():
        print("   ✅ Local .venv directory found")
        return True
    else:
        print("   ⚠️  No virtual environment detected")
        print("   💡 Consider using: uv venv or python -m venv .venv")
        return True  # Not critical, just a recommendation

def main():
    """Run all validation checks."""
    print("🔧 Circuit-synth Environment Validation")
    print("=====================================")
    
    checks = [
        ("Virtual Environment", check_virtual_environment),
        ("Submodule Status", check_submodule_status),
        ("Python Import Path", check_python_path),
        ("Cache Files", check_cache_files),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        results.append(check_func())
    
    print("\n" + "="*40)
    if all(results):
        print("🎉 All checks passed! Environment is ready.")
        return 0
    else:
        print("❌ Some checks failed. Review the output above.")
        print("🔧 Quick fix: ./scripts/ensure-clean-environment.sh")
        return 1

if __name__ == "__main__":
    exit(main())