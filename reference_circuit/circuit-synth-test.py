from circuit_synth import *


@circuit(name="blank_schematic")
def blank_schematic():
    """A blank schematic circuit."""
    pass

def main():
    # Run the circuit synthesis test
    circuit = blank_schematic()

    circuit.generate_kicad_project(
        project_name="blank_schematic_project")
    
    