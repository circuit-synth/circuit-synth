from circuit_synth import *

@circuit(name="Simple_LED")
def main():
    '''Simple LED test circuit.'''
    
    # Power nets
    vcc_3v3 = Net('3V3')
    gnd = Net('GND')
    
    # Components
    led = Component(
        symbol="Device:LED",
        ref="D1",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    resistor = Component(
        symbol="Device:R",
        ref="R1",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connections
    resistor[1] += vcc_3v3
    resistor[2] += led[1] 
    led[2] += gnd

if __name__ == '__main__':
    circuit = main()
    print("Circuit created successfully!")
    netlist = circuit.generate_text_netlist()
    print(netlist)