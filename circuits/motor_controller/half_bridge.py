#!/usr/bin/env python3
"""
half_bridge subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='half_bridge')
def half_bridge(_3v3, _12v, gnd, netn_q3nground_1_, pvdc, bemf2, ghs2, gls2, gpio_bemf, phase_v, vshunt2n, vshunt2p, netn_d11nk_):
    """
    half_bridge subcircuit
    Parameters: +3V3, +12V, GND, Net-(Q3-GROUND_1), +VDC, Motor Controller/BEMF2, Motor Controller/GHS2, Motor Controller/GLS2, Motor Controller/GPIO_BEMF, Motor Controller/PHASE_V, Motor Controller/VSHUNT2N, Motor Controller/VSHUNT2P, Net-(D11-K)
    """
    # Create local nets
    netn_d19na_ = Net('Net-(D19-A)')
    netn_ic3nhvg_ = Net('Net-(IC3-HVG)')
    netn_ic3nlvg_ = Net('Net-(IC3-LVG)')
    netn_q3ng_1_ = Net('Net-(Q3-G_1)')
    netn_q3ng_2_ = Net('Net-(Q3-G_2)')

    # Create components
    c29 = Component(symbol="Device:C_Small", ref="C29", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c48 = Component(symbol="Device:C_Small", ref="C48", value="0201CG101J500NT", footprint="Capacitor_SMD:C_0201_0603Metric")
    c51 = Component(symbol="Device:C_Small", ref="C51", value="0201CG101J500NT", footprint="Capacitor_SMD:C_0201_0603Metric")
    c54 = Component(symbol="Device:C_Small", ref="C54", value="0201CG101J500NT", footprint="Capacitor_SMD:C_0201_0603Metric")
    c58 = Component(symbol="Device:C_Small", ref="C58", value="CGA0805X5R226M350MT", footprint="Capacitor_SMD:C_0805_2012Metric")
    c59 = Component(symbol="Device:C_Small", ref="C59", value="CGA0805X5R226M350MT", footprint="Capacitor_SMD:C_0805_2012Metric")
    c60 = Component(symbol="Device:C_Small", ref="C60", value="CGA0805X5R226M350MT", footprint="Capacitor_SMD:C_0805_2012Metric")
    d11 = Component(symbol="Device:D_Schottky_Small", ref="D11", value="STPS0560Z", footprint="Diode_SMD:D_SOD-123F")
    d16 = Component(symbol="Device:D_Schottky_Small", ref="D16", value="RB520S-30", footprint="Diode_SMD:D_SOD-523")
    d19 = Component(symbol="Device:D_Schottky_Small", ref="D19", value="RB520S-30", footprint="Diode_SMD:D_SOD-523")
    h3 = Component(symbol="Mechanical:MountingHole_Pad", ref="H3", value="MountingHole_Pad", footprint="TestPoint:TestPoint_Pad_3.0x3.0mm")
    ic3 = Component(symbol="_skip:L6387ED013TR", ref="IC3", value="L6387ED013TR", footprint="_skip:SOIC127P600X175-8N")
    nt3 = Component(symbol="Device:NetTie_2", ref="NT3", value="NetTie_2", footprint="NetTie:NetTie-2_SMD_Pad0.5mm")
    q3 = Component(symbol="_skip:IAUC45N04S6N070HATMA1", ref="Q3", value="IAUC45N04S6N070HATMA1", footprint="_skip:IAUC60N04S6L045HATMA1")
    r29 = Component(symbol="Device:R_Small", ref="R29", value="HP02WAF1002TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r41 = Component(symbol="Device:R_Small", ref="R41", value="ERJ2RKF33R0X", footprint="Resistor_SMD:R_0402_1005Metric")
    r42 = Component(symbol="Device:R_Small", ref="R42", value="ERJ2RKF33R0X", footprint="Resistor_SMD:R_0402_1005Metric")
    r43 = Component(symbol="Device:R_Small", ref="R43", value="C5375459", footprint="Resistor_SMD:R_2512_6332Metric")
    r47 = Component(symbol="Device:R_Small", ref="R47", value="RC-02W2201FT", footprint="Resistor_SMD:R_0402_1005Metric")
    r50 = Component(symbol="Device:R_Small", ref="R50", value="RK73H1ETTP1501F", footprint="Resistor_SMD:R_0402_1005Metric")
    r53 = Component(symbol="Device:R_Small", ref="R53", value="0603WAF2202T5E", footprint="Resistor_SMD:R_0402_1005Metric")
    r56 = Component(symbol="Device:R_Small", ref="R56", value="0603WAF2201T5E", footprint="Resistor_SMD:R_0402_1005Metric")
    tp12 = Component(symbol="Connector:TestPoint", ref="TP12", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.5x1.5mm")
    tp15 = Component(symbol="Connector:TestPoint", ref="TP15", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.5x1.5mm")

    # Connections
    d16[1] += _3v3
    r53[2] += _3v3
    c48[1] += _12v
    d11[2] += _12v
    ic3[3] += _12v
    c58[1] += pvdc
    c59[1] += pvdc
    c60[1] += pvdc
    q3[11] += pvdc
    q3[15] += pvdc
    q3[7] += pvdc
    q3[8] += pvdc
    q3[9] += pvdc
    d16[2] += bemf2
    r29[1] += bemf2
    r47[2] += bemf2
    c54[1] += ghs2
    ic3[2] += ghs2
    tp15[1] += ghs2
    c51[1] += gls2
    ic3[1] += gls2
    tp12[1] += gls2
    d19[1] += gpio_bemf
    c29[2] += phase_v
    h3[1] += phase_v
    ic3[6] += phase_v
    q3[10] += phase_v
    q3[13] += phase_v
    q3[14] += phase_v
    q3[2] += phase_v
    q3[3] += phase_v
    r29[2] += phase_v
    nt3[2] += vshunt2n
    r50[2] += vshunt2p
    r53[1] += vshunt2p
    r56[2] += vshunt2p
    c48[2] += gnd
    c51[2] += gnd
    c54[2] += gnd
    c58[2] += gnd
    c59[2] += gnd
    c60[2] += gnd
    ic3[4] += gnd
    nt3[1] += gnd
    r43[2] += gnd
    r56[1] += gnd
    c29[1] += netn_d11nk_
    d11[1] += netn_d11nk_
    ic3[8] += netn_d11nk_
    d19[2] += netn_d19na_
    r47[1] += netn_d19na_
    ic3[7] += netn_ic3nhvg_
    r41[1] += netn_ic3nhvg_
    ic3[5] += netn_ic3nlvg_
    r42[1] += netn_ic3nlvg_
    q3[12] += netn_q3nground_1_
    q3[5] += netn_q3nground_1_
    q3[6] += netn_q3nground_1_
    r43[1] += netn_q3nground_1_
    r50[1] += netn_q3nground_1_
    q3[1] += netn_q3ng_1_
    r41[2] += netn_q3ng_1_
    q3[4] += netn_q3ng_2_
    r42[2] += netn_q3ng_2_