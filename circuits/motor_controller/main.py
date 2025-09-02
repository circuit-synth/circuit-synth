#!/usr/bin/env python3
"""
Main circuit generated from KiCad
"""

from circuit_synth import *

# Import subcircuit functions
from bldc_driver import bldc_driver
from connectors import connectors

@circuit(name='main')
def main():
    """
    Main circuit with hierarchical subcircuits
    """
    # Main circuit nets
    _3v3 = Net('+3V3')
    _5v = Net('+5V')
    _12v = Net('+12V')
    enc_i = Net('Connectors/ENC_I')
    bemf1 = Net('Motor Controller/BEMF1')
    bemf3 = Net('Motor Controller/BEMF3')
    ghs1 = Net('Motor Controller/GHS1')
    oscp = Net('Motor Controller/OSC+')
    gnd = Net('GND')
    netn_d12nk_ = Net('Net-(D12-K)')
    netn_j2npin_2_ = Net('Net-(J2-Pin_2)')
    netn_j6npad1_ = Net('Net-(J6-Pad1)')
    netn_q3nground_1_ = Net('Net-(Q3-GROUND_1)')
    netn_u1npa2_ = Net('Net-(U1-PA2)')
    netn_u1npb10_ = Net('Net-(U1-PB10)')
    vdda = Net('VDDA')
    phase_v = Net('Motor Controller/PHASE_V')
    netn_d11nk_ = Net('Net-(D11-K)')
    enc_a = Net('Connectors/ENC_A')
    enc_b = Net('Connectors/ENC_B')
    enc_clk = Net('Connectors/ENC_CLK')
    enc_miso = Net('Connectors/ENC_MISO')
    enc_mosi = Net('Connectors/ENC_MOSI')
    joint_cs = Net('Connectors/JOINT_CS')
    rotor_cs = Net('Connectors/ROTOR_CS')
    rotor_cs_3v3 = Net('Motor Controller/ROTOR_CS_3v3')
    netn_u1npa15_ = Net('Net-(U1-PA15)')
    netn_u2na7_ = Net('Net-(U2-A7)')
    ghs3 = Net('Motor Controller/GHS3')


    # Instantiate top-level subcircuits
    bldc_driver_circuit = bldc_driver(_3v3, _5v, _12v, enc_i, bemf1, bemf3, ghs1, oscp, gnd, netn_d12nk_, netn_j2npin_2_, netn_u1npa2_, netn_u1npb10_, vdda, enc_a, enc_b, enc_clk, enc_miso, enc_mosi, joint_cs, rotor_cs, rotor_cs_3v3, netn_u1npa15_, netn_u2na7_, ghs3)
    connectors_circuit = connectors(_5v, enc_i, gnd, netn_j6npad1_, enc_a, enc_b, enc_clk, enc_miso, enc_mosi, joint_cs, rotor_cs)


# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="B-G431B-ESC1_clone_v_0_2_generated")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("B-G431B-ESC1_clone_v_0_2_generated/B-G431B-ESC1_clone_v_0_2_generated.net")