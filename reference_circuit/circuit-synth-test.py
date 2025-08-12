from circuit_synth import *


@circuit(name="blank_schematic")
def blank_schematic():
    """A blank schematic circuit."""
    pass

def main():
    print("🧪 Starting blank schematic test...")
    
    # Run the circuit synthesis test
    print("📋 Creating blank circuit...")
    circuit = blank_schematic()
    print(f"✅ Circuit created: {circuit}")
    
    # Debug circuit state
    print(f"🔍 Circuit nets type: {type(circuit.nets)}")
    print(f"🔍 Circuit nets content: {circuit.nets}")
    print(f"🔍 Circuit _nets type: {type(circuit._nets)}")
    print(f"🔍 Circuit _nets content: {circuit._nets}")
    print(f"🔍 Circuit components: {len(circuit._component_list)}")
    
    print("🏗️  Generating KiCad project...")
    try:
        circuit.generate_kicad_project(
            project_name="blank_schematic_project")
        print("✅ KiCad project generated successfully!")
    except Exception as e:
        print(f"❌ Error generating project: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    
    