from circuit_synth import *

@circuit(name="top")
def top():
    resistor = Component(symbol="Device:R", ref="R", value="10k",footprint="Resistor_SMD:R_0805_2012Metric")



def main():
    circuit = top()
    circuit.generate_kicad_project(project_name="generated_project")

if __name__ == "__main__":
    main()
    print("KiCad project generated successfully!")