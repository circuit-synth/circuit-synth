#!/usr/bin/env python3
"""
connectors subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='connectors')
def connectors(_5v, enc_i, gnd, netn_j6npad1_, enc_a, enc_b, enc_clk, enc_miso, enc_mosi, joint_cs, rotor_cs):
    """
    connectors subcircuit
    Parameters: +5V, Connectors/ENC_I, GND, Net-(J6-Pad1), Connectors/ENC_A, Connectors/ENC_B, Connectors/ENC_CLK, Connectors/ENC_MISO, Connectors/ENC_MOSI, Connectors/JOINT_CS, Connectors/ROTOR_CS
    """
    # Create local nets
    netn_j6npad2_ = Net('Net-(J6-Pad2)')
    netn_j6npad3_ = Net('Net-(J6-Pad3)')
    netn_j6npad5_ = Net('Net-(J6-Pad5)')
    netn_j6npad7_ = Net('Net-(J6-Pad7)')
    netn_j6npad9_ = Net('Net-(J6-Pad9)')
    netn_j6npad11_ = Net('Net-(J6-Pad11)')
    netn_j6npad12_ = Net('Net-(J6-Pad12)')

    # Create components
    j6 = Component(symbol="_skip:20542-012E-01", ref="J6", value="20542-012E-01", footprint="_skip:IPEX_20542-012E-01")
    r10 = Component(symbol="Device:R_Small", ref="R10", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r13 = Component(symbol="Device:R_Small", ref="R13", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r30 = Component(symbol="Device:R_Small", ref="R30", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r31 = Component(symbol="Device:R_Small", ref="R31", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r34 = Component(symbol="Device:R_Small", ref="R34", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r36 = Component(symbol="Device:R_Small", ref="R36", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r39 = Component(symbol="Device:R_Small", ref="R39", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r44 = Component(symbol="Device:R_Small", ref="R44", value="33", footprint="Resistor_SMD:R_0201_0603Metric")

    # Connections
    j6[6] += _5v
    r34[2] += enc_a
    r36[2] += enc_b
    r13[2] += enc_clk
    r44[2] += enc_i
    r31[2] += enc_miso
    r30[2] += enc_mosi
    r10[2] += joint_cs
    r39[2] += rotor_cs
    j6[10] += gnd
    j6[4] += gnd
    j6[8] += gnd
    j6['S1'] += gnd
    j6['S2'] += gnd
    j6[1] += netn_j6npad1_
    r44[1] += netn_j6npad1_
    j6[2] += netn_j6npad2_
    r39[1] += netn_j6npad2_
    j6[3] += netn_j6npad3_
    r36[1] += netn_j6npad3_
    j6[5] += netn_j6npad5_
    r34[1] += netn_j6npad5_
    j6[7] += netn_j6npad7_
    r31[1] += netn_j6npad7_
    j6[9] += netn_j6npad9_
    r30[1] += netn_j6npad9_
    j6[11] += netn_j6npad11_
    r13[1] += netn_j6npad11_
    j6[12] += netn_j6npad12_
    r10[1] += netn_j6npad12_