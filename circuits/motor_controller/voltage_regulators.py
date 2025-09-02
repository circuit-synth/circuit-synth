#!/usr/bin/env python3
"""
voltage_regulators subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='voltage_regulators')
def voltage_regulators(_3v3, _5v, _12v, enc_i, bemf1, bemf3, ghs1, oscp, gnd, netn_d12nk_, netn_j2npin_2_, netn_j6npad1_, netn_q3nground_1_, netn_u1npa2_, netn_u1npb10_, vdda):
    """
    voltage_regulators subcircuit
    Parameters: +3V3, +5V, +12V, Connectors/ENC_I, Motor Controller/BEMF1, Motor Controller/BEMF3, Motor Controller/GHS1, Motor Controller/OSC+, GND, Net-(D12-K), Net-(J2-Pin_2), Net-(J6-Pad1), Net-(Q3-GROUND_1), Net-(U1-PA2), Net-(U1-PB10), VDDA
    """
    # Create local nets
    phase_w = Net('Motor Controller/PHASE_W')
    netn_d17na_ = Net('Net-(D17-A)')

    # Create components
    c3 = Component(symbol="Device:C", ref="C3", value="18pF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c18 = Component(symbol="Device:C_Small", ref="C18", value="100nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c38 = Component(symbol="Device:C_Small", ref="C38", value="C2012X5R1V226M125AC", footprint="Capacitor_SMD:C_0805_2012Metric")
    c46 = Component(symbol="Device:C_Small", ref="C46", value="C2012X5R1V226M125AC", footprint="Capacitor_SMD:C_0805_2012Metric")
    fb1 = Component(symbol="Device:FerriteBead_Small", ref="FB1", value="GZ1608D601TF", footprint="Inductor_SMD:L_0603_1608Metric")
    l2 = Component(symbol="Device:L", ref="L2", value="FXL0530-4R7-M", footprint="_skip:FXL0530-4R7-M")
    tp4 = Component(symbol="Connector:TestPoint", ref="TP4", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp20 = Component(symbol="Connector:TestPoint", ref="TP20", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    d14 = Component(symbol="Device:D_Schottky_Small", ref="D14", value="RB520S-30", footprint="Diode_SMD:D_SOD-523")
    r27 = Component(symbol="Device:R_Small", ref="R27", value="HP02WAF1002TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r45 = Component(symbol="Device:R_Small", ref="R45", value="RC-02W2201FT", footprint="Resistor_SMD:R_0402_1005Metric")
    c47 = Component(symbol="Device:C_Small", ref="C47", value="0201CG101J500NT", footprint="Capacitor_SMD:C_0201_0603Metric")
    d15 = Component(symbol="Device:D_Schottky_Small", ref="D15", value="RB520S-30", footprint="Diode_SMD:D_SOD-523")
    tp14 = Component(symbol="Connector:TestPoint", ref="TP14", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.5x1.5mm")
    r44 = Component(symbol="Device:R_Small", ref="R44", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r43 = Component(symbol="Device:R_Small", ref="R43", value="C5375459", footprint="Resistor_SMD:R_2512_6332Metric")

    # Connections
    c18[1] += _3v3
    d14[1] += _3v3
    d15[1] += _3v3
    fb1[1] += _3v3
    c38[1] += _5v
    c47[1] += _12v
    r44[2] += enc_i
    d15[2] += bemf1
    d14[2] += bemf3
    r27[1] += bemf3
    r45[2] += bemf3
    tp14[1] += ghs1
    c3[1] += oscp
    r27[2] += phase_w
    c18[2] += gnd
    c3[2] += gnd
    c38[2] += gnd
    c46[2] += gnd
    c47[2] += gnd
    r43[2] += gnd
    l2[1] += netn_d12nk_
    r45[1] += netn_d17na_
    c46[1] += netn_j2npin_2_
    l2[2] += netn_j2npin_2_
    r44[1] += netn_j6npad1_
    r43[1] += netn_q3nground_1_
    tp4[1] += netn_u1npa2_
    tp20[1] += netn_u1npb10_
    fb1[2] += vdda