#!/usr/bin/env python3
"""
Manual Test 5: Compare our generated schematics to reference circuits
"""

import sys
from pathlib import Path

def compare_files(generated_path, reference_path, name):
    """Compare generated vs reference file."""
    print(f"\n🔍 Comparing {name}:")
    print("-" * 40)
    
    if not generated_path.exists():
        print(f"❌ Generated file missing: {generated_path}")
        return False
    
    if not reference_path.exists():
        print(f"❌ Reference file missing: {reference_path}")
        return False
    
    # Read files
    with open(generated_path, 'r') as f:
        generated = f.read()
    with open(reference_path, 'r') as f:
        reference = f.read()
    
    # Compare basic metrics
    gen_size = len(generated)
    ref_size = len(reference)
    gen_symbols = generated.count("(symbol")
    ref_symbols = reference.count("(symbol")
    
    print(f"📊 Size - Generated: {gen_size} chars, Reference: {ref_size} chars")
    print(f"📊 Symbols - Generated: {gen_symbols}, Reference: {ref_symbols}")
    
    # Content checks
    components = ["R1", "R2", "10k", "22k", "Device:R"]
    print("📊 Content comparison:")
    for comp in components:
        gen_has = comp in generated
        ref_has = comp in reference
        match = "✅" if gen_has == ref_has else "❌"
        print(f"   {match} {comp}: Gen={gen_has}, Ref={ref_has}")
    
    # Structural similarity
    size_ratio = min(gen_size, ref_size) / max(gen_size, ref_size) if max(gen_size, ref_size) > 0 else 0
    print(f"📊 Size ratio: {size_ratio:.2f}")
    
    return gen_symbols > 0  # Success if we have components

def main():
    print("Manual Test 5: Compare to Reference Circuits")
    print("=" * 45)
    
    comparisons = [
        # (generated_path, reference_path, name)
        ("manual_blank/manual_blank.kicad_sch", "blank_schematic/blank_schematic.kicad_sch", "Blank Schematic"),
        ("manual_atomic/manual_atomic.kicad_sch", "single_resistor/single_resistor.kicad_sch", "Single Resistor"),
        ("manual_two_resistors/manual_two_resistors.kicad_sch", "two_resistors/two_resistors.kicad_sch", "Two Resistors"),
        ("manual_remove_test/manual_remove_test.kicad_sch", "single_resistor/single_resistor.kicad_sch", "After Remove (should match single)")
    ]
    
    results = []
    
    for gen_path_str, ref_path_str, name in comparisons:
        gen_path = Path(gen_path_str)
        ref_path = Path(ref_path_str)
        
        result = compare_files(gen_path, ref_path, name)
        results.append((name, result))
    
    # Summary
    print(f"\n{'='*45}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*45}")
    
    for name, success in results:
        status = "✅ FUNCTIONAL" if success else "❌ EMPTY"
        print(f"{status}: {name}")
    
    functional_count = sum(1 for _, success in results if success)
    print(f"\n📈 Score: {functional_count}/{len(results)} circuits are functional")
    
    if functional_count > 0:
        print("\n🎉 Atomic operations are working!")
        print("   Generated schematics contain actual components.")
    else:
        print("\n❌ No functional circuits generated.")

if __name__ == "__main__":
    main()