#!/usr/bin/env python3
"""
Non-Determinism Investigation Script

This script investigates the source of non-deterministic behavior in the
current Python implementation to ensure we have a stable baseline before
any Rust integration.

Purpose: Understand why identical circuit generation produces different outputs.
"""

import sys
import time
import hashlib
import difflib
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def cleanup_outputs():
    """Clean up any existing outputs"""
    cleanup_patterns = [
        "example_kicad_project.net",
        "example_kicad_project.json",
        "example_kicad_project/",
        "investigate_run1/",
        "investigate_run2/",
    ]
    
    import shutil
    import os
    
    for pattern in cleanup_patterns:
        if os.path.exists(pattern):
            if os.path.isdir(pattern):
                shutil.rmtree(pattern)
            else:
                os.remove(pattern)
    print("🧹 Cleaned up previous outputs")

def run_circuit_generation(output_suffix: str):
    """Run circuit generation and save outputs with suffix"""
    print(f"🚀 Running circuit generation #{output_suffix}")
    
    # Import and run the example
    sys.path.append('examples')
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("example_module", "examples/example_kicad_project.py")
    example_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(example_module)
    
    # Create circuit
    circuit = example_module.root()
    
    # Generate outputs
    circuit.generate_kicad_netlist(f"netlist_{output_suffix}.net")
    circuit.generate_json_netlist(f"netlist_{output_suffix}.json")
    circuit.generate_kicad_project(f"project_{output_suffix}", force_regenerate=True, draw_bounding_boxes=True)
    
    print(f"✅ Generation #{output_suffix} completed")

def compare_files(file1: Path, file2: Path) -> bool:
    """Compare two files and show differences"""
    if not file1.exists() or not file2.exists():
        print(f"❌ Missing files: {file1.exists()=}, {file2.exists()=}")
        return False
    
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        content1 = f1.readlines()
        content2 = f2.readlines()
    
    if content1 == content2:
        print(f"✅ {file1.name} vs {file2.name}: IDENTICAL")
        return True
    else:
        print(f"❌ {file1.name} vs {file2.name}: DIFFERENT")
        
        # Show first few differences
        diff = list(difflib.unified_diff(
            content1[:10], content2[:10], 
            fromfile=str(file1), tofile=str(file2), lineterm=''
        ))
        
        if diff:
            print("   First 10 lines of diff:")
            for line in diff[:20]:  # Show first 20 diff lines
                print(f"   {line}")
        
        return False

def investigate_non_determinism():
    """Main investigation function"""
    print("🔍 INVESTIGATING NON-DETERMINISTIC BEHAVIOR")
    print("=" * 60)
    
    cleanup_outputs()
    
    # Run generation twice with identical parameters
    run_circuit_generation("1")
    time.sleep(1)  # Small delay
    run_circuit_generation("2")
    
    print("\n📊 COMPARING OUTPUTS")
    print("-" * 40)
    
    # Compare netlists
    netlist1 = Path("netlist_1.net")
    netlist2 = Path("netlist_2.net")
    netlist_identical = compare_files(netlist1, netlist2)
    
    # Compare JSON
    json1 = Path("netlist_1.json")
    json2 = Path("netlist_2.json")
    json_identical = compare_files(json1, json2)
    
    # Compare project files
    project1_dir = Path("project_1")
    project2_dir = Path("project_2")
    
    project_files_identical = True
    if project1_dir.exists() and project2_dir.exists():
        # Get all files in both projects
        files1 = {f.relative_to(project1_dir): f for f in project1_dir.rglob("*") if f.is_file()}
        files2 = {f.relative_to(project2_dir): f for f in project2_dir.rglob("*") if f.is_file()}
        
        # Check if same files exist
        if set(files1.keys()) != set(files2.keys()):
            print(f"❌ Project file lists differ:")
            print(f"   Project 1: {sorted(files1.keys())}")
            print(f"   Project 2: {sorted(files2.keys())}")
            project_files_identical = False
        else:
            # Compare each file
            for rel_path in files1.keys():
                file1 = files1[rel_path]
                file2 = files2[rel_path]
                if not compare_files(file1, file2):
                    project_files_identical = False
    
    print("\n📋 INVESTIGATION SUMMARY")
    print("-" * 40)
    print(f"Netlist identical:      {'✅' if netlist_identical else '❌'}")
    print(f"JSON identical:         {'✅' if json_identical else '❌'}")
    print(f"Project files identical: {'✅' if project_files_identical else '❌'}")
    
    if netlist_identical and json_identical and project_files_identical:
        print("\n✅ NO NON-DETERMINISM DETECTED")
        print("The outputs are consistent across runs.")
        print("Previous baseline inconsistency may have been due to:")
        print("- Import timing effects")
        print("- Environment differences between runs")
        print("- Test harness issues")
    else:
        print("\n❌ NON-DETERMINISM CONFIRMED")
        print("Sources of non-determinism to investigate:")
        print("- Timestamps or UUIDs in generated files")
        print("- Random number generation in placement algorithms")
        print("- Dictionary/set iteration order")
        print("- Floating point precision differences")
        
        # Try to identify common non-deterministic patterns
        if not netlist_identical:
            print("\n🔍 Netlist differences suggest:")
            print("- Component ordering issues")
            print("- Reference assignment non-determinism")
        
        if not project_files_identical:
            print("\n🔍 Project file differences suggest:")
            print("- UUID generation in schematic files")
            print("- Timestamp inclusion")
            print("- Component placement variation")
    
    print("\n🛡️ DEFENSIVE RECOMMENDATION:")
    if netlist_identical and json_identical and project_files_identical:
        print("✅ PROCEED with Rust integration - baseline is stable")
    else:
        print("⚠️ FIX non-determinism before Rust integration")
        print("   Rust integration should wait until outputs are consistent")

if __name__ == "__main__":
    investigate_non_determinism()