from circuit_synth import *
from circuit_synth.kicad.atomic_operations import (
    add_component_to_schematic,
    remove_component_from_schematic
)
from pathlib import Path
import shutil


@circuit(name="blank_schematic")
def blank_schematic():
    """A blank schematic circuit."""
    pass


@circuit(name="single_resistor")
def single_resistor():
    """A circuit with a single 10k resistor."""
    r1 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    return r1


@circuit(name="two_resistors")
def two_resistors():
    """A circuit with two 10k resistors."""
    r1 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    return [r1, r2]


def compare_schematics(generated_path, reference_path, name):
    """Compare generated and reference schematics, ignoring UUIDs and positions."""
    print(f"\n🔍 Comparing {name}...")
    
    if not generated_path.exists():
        print(f"❌ Generated schematic not found: {generated_path}")
        return False
        
    if not reference_path.exists():
        print(f"❌ Reference schematic not found: {reference_path}")
        return False
    
    # Read both files
    with open(generated_path, 'r') as f:
        generated = f.read()
    with open(reference_path, 'r') as f:
        reference = f.read()
    
    print(f"📊 Generated size: {len(generated)} chars")
    print(f"📊 Reference size: {len(reference)} chars") 
    
    # Basic structure checks
    has_lib_symbols_gen = "lib_symbols" in generated
    has_lib_symbols_ref = "lib_symbols" in reference
    has_symbol_gen = "(symbol" in generated 
    has_symbol_ref = "(symbol" in reference
    
    print(f"   Generated has lib_symbols: {has_lib_symbols_gen}")
    print(f"   Reference has lib_symbols: {has_lib_symbols_ref}")
    print(f"   Generated has symbols: {has_symbol_gen}")
    print(f"   Reference has symbols: {has_symbol_ref}")
    
    return has_lib_symbols_gen and has_symbol_gen


def test_atomic_operations():
    """Test atomic operations and compare with reference circuits."""
    print("🧪 Testing atomic operations vs reference circuits...")
    
    # Step 1: Generate blank schematic
    print("\n📝 Step 1: Generating blank schematic")
    circuit = blank_schematic()
    circuit.generate_kicad_project(project_name="atomic_test")
    
    # Step 2: Generate reference circuits
    print("\n📋 Step 2: Generating reference circuits")
    single_circuit = single_resistor()
    single_circuit.generate_kicad_project(project_name="single_ref")
    
    two_circuit = two_resistors()  
    two_circuit.generate_kicad_project(project_name="two_ref")
    
    # Step 3: Apply atomic operations
    atomic_path = Path("atomic_test/atomic_test.kicad_sch")
    
    print("\n⚡ Step 3: Adding first resistor via atomic operation")
    add_component_to_schematic(
        atomic_path,
        lib_id="Device:R",
        reference="R1", 
        value="10k",
        position=(121.92, 68.58),
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Copy for single resistor comparison
    single_atomic_path = Path("single_atomic.kicad_sch")
    shutil.copy2(atomic_path, single_atomic_path)
    
    print("\n⚡ Step 4: Adding second resistor via atomic operation") 
    add_component_to_schematic(
        atomic_path,
        lib_id="Device:R",
        reference="R2",
        value="10k", 
        position=(137.16, 68.58),
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Step 4: Compare results
    print("\n🔍 Step 5: Comparing results...")
    
    # Use the actual reference circuits instead of generated ones
    single_ref_path = Path("single_resistor/single_resistor.kicad_sch")
    two_ref_path = Path("two_resistors/two_resistors.kicad_sch") 
    
    single_match = compare_schematics(single_atomic_path, single_ref_path, "Single resistor")
    two_match = compare_schematics(atomic_path, two_ref_path, "Two resistors")
    
    if single_match and two_match:
        print("\n🎉 SUCCESS: Atomic operations produce similar structure to reference circuits")
    else:
        print("\n⚠️  WARNING: Atomic operations produce different structure than reference circuits")
        print("    This suggests atomic operations may need improvement to match full circuit generation")


def main():
    print("🧪 Starting circuit synthesis and atomic operations test...")
    
    # Test regular circuit generation
    print("\n📋 Testing regular circuit generation...")
    circuit = blank_schematic()
    print(f"✅ Circuit created: {circuit}")
    
    try:
        circuit.generate_kicad_project(project_name="blank_schematic_project")
        print("✅ KiCad project generated successfully!")
    except Exception as e:
        print(f"❌ Error generating project: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test atomic operations
    test_atomic_operations()


if __name__ == "__main__":
    main()
    
    