from circuit_synth import *



@circuit
def child2(VIN, GND):
    c = Component(symbol="Device:C", ref="C", value="10uF", 
                    footprint="Capacitor_SMD:C_0603_1608Metric")
    r = Component(symbol="Device:R", ref="R", value="10k", 
                    footprint="Resistor_SMD:R_0603_1608Metric")
    
    c[1] += VIN  # Connect capacitor to VIN
    c[2] += GND  # Connect capacitor to GND

    r[1] += VIN  # Connect resistor to VIN
    r[2] += GND  # Connect resistor to GND

@circuit
def child1(VIN, GND):
    c = Component(symbol="Device:C", ref="C", value="10uF", 
                    footprint="Capacitor_SMD:C_0603_1608Metric")
    r = Component(symbol="Device:R", ref="R", value="10k", 
                    footprint="Resistor_SMD:R_0603_1608Metric")
    
    c[1] += VIN  # Connect capacitor to VIN
    c[2] += GND  # Connect capacitor to GND

    r[1] += VIN  # Connect resistor to VIN
    r[2] += GND  # Connect resistor to GND

    child2(VIN, GND)

@circuit
def root():

    c = Component(symbol="Device:C", ref="C", value="10uF", 
                    footprint="Capacitor_SMD:C_0603_1608Metric")
    r = Component(symbol="Device:R", ref="R", value="10k", 
                    footprint="Resistor_SMD:R_0603_1608Metric")
    
    VIN = Net("VIN")
    GND = Net("GND")

    c[1] += VIN  # Connect capacitor to VIN
    c[2] += GND  # Connect capacitor to GND

    r[1] += VIN  # Connect resistor to VIN
    r[2] += GND  # Connect resistor to GND

    child1(VIN, GND)
    
def main():
    circuit = root()

    circuit.generate_kicad_project("generated_circuit")

if __name__ == "__main__":
    main()