from circuit_synth import *


@circuit
def voltage_divider():
    """Voltage Divider Circuit - Correct topology with proper connections"""
    
    # Components: Resistors
    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0805_2012Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k",
                   footprint="Resistor_SMD:R_0805_2012Metric")
    vcc = Net(name="Vcc")
    vout = Net(name="Vout")
    gnd = Net(name="GND")

    # Connections: R1 to Vcc, R2 to ground
    r1[1] += vcc
    r1[2] += vout  # R1 output to Vout
    r2[1] += vout  # R2 input from Vout
    r2[2] += gnd

def main():
    """Main function to run the voltage divider circuit"""
    c = voltage_divider()
    c.generate_kicad_project("01_voltage_divider")


if __name__ == "__main__":
    main()