#!/usr/bin/env python3
"""
bldc_driver subcircuit generated from KiCad
"""

from circuit_synth import *

# Import child circuits
from half_bridge import half_bridge
from half_bridge import half_bridge
from half_bridge import half_bridge

@circuit(name='bldc_driver')
def bldc_driver(_3v3, _5v, _12v, enc_i, bemf1, bemf3, ghs1, oscp, gnd, netn_d12nk_, netn_j2npin_2_, netn_u1npa2_, netn_u1npb10_, vdda, enc_a, enc_b, enc_clk, enc_miso, enc_mosi, joint_cs, rotor_cs, rotor_cs_3v3, netn_u1npa15_, netn_u2na7_, ghs3):
    """
    bldc_driver subcircuit
    Parameters: +3V3, +5V, +12V, Connectors/ENC_I, Motor Controller/BEMF1, Motor Controller/BEMF3, Motor Controller/GHS1, Motor Controller/OSC+, GND, Net-(D12-K), Net-(J2-Pin_2), Net-(U1-PA2), Net-(U1-PB10), VDDA, Connectors/ENC_A, Connectors/ENC_B, Connectors/ENC_CLK, Connectors/ENC_MISO, Connectors/ENC_MOSI, Connectors/JOINT_CS, Connectors/ROTOR_CS, Motor Controller/ROTOR_CS_3v3, Net-(U1-PA15), Net-(U2-A7), Motor Controller/GHS3
    """
    # Create local nets
    pvdc = Net('+VDC')
    bemf2 = Net('Motor Controller/BEMF2')
    ghs2 = Net('Motor Controller/GHS2')
    gls2 = Net('Motor Controller/GLS2')
    gpio_bemf = Net('Motor Controller/GPIO_BEMF')
    vshunt2n = Net('Motor Controller/VSHUNT2N')
    vshunt2p = Net('Motor Controller/VSHUNT2P')
    encoder_cs = Net('Motor Controller/ENCODER_CS')
    eqep_a = Net('Motor Controller/EQEP_A')
    eqep_b = Net('Motor Controller/EQEP_B')
    eqep_i = Net('Motor Controller/EQEP_I')
    fet_temp = Net('Motor Controller/FET_TEMP')
    gls1 = Net('Motor Controller/GLS1')
    gls3 = Net('Motor Controller/GLS3')
    nrst = Net('Motor Controller/NRST')
    oscn = Net('Motor Controller/OSC-')
    spi2_clk = Net('Motor Controller/SPI2_CLK')
    spi2_miso = Net('Motor Controller/SPI2_MISO')
    spi2_mosi = Net('Motor Controller/SPI2_MOSI')
    swclk = Net('Motor Controller/SWCLK')
    swdio = Net('Motor Controller/SWDIO')
    uart2_rx = Net('Motor Controller/UART2_RX')
    uart2_tx = Net('Motor Controller/UART2_TX')
    vshunt1n = Net('Motor Controller/VSHUNT1N')
    vshunt1p = Net('Motor Controller/VSHUNT1P')
    vshunt3n = Net('Motor Controller/VSHUNT3N')
    vshunt3p = Net('Motor Controller/VSHUNT3P')
    vbus_sense = Net('Motor Controller/Vbus_sense')
    netn_c27npad1_ = Net('Net-(C27-Pad1)')
    netn_c39npad1_ = Net('Net-(C39-Pad1)')
    netn_d1nk_ = Net('Net-(D1-K)')
    netn_d2na_ = Net('Net-(D2-A)')
    netn_d3na_ = Net('Net-(D3-A)')
    netn_d13na_ = Net('Net-(D13-A)')
    netn_j3npin_2_ = Net('Net-(J3-Pin_2)')
    netn_ps1nboot_ = Net('Net-(PS1-BOOT)')
    netn_ps1ncomp_ = Net('Net-(PS1-COMP)')
    netn_ps1nss_ = Net('Net-(PS1-SS)')
    netn_ps1nvsense_ = Net('Net-(PS1-VSENSE)')
    netn_ps2nboot_ = Net('Net-(PS2-BOOT)')
    netn_ps2ncomp_ = Net('Net-(PS2-COMP)')
    netn_ps2nss_ = Net('Net-(PS2-SS)')
    netn_ps2nvsense_ = Net('Net-(PS2-VSENSE)')
    netn_u1npa6_ = Net('Net-(U1-PA6)')
    netn_u1npb1_ = Net('Net-(U1-PB1)')
    netn_u1npb9_ = Net('Net-(U1-PB9)')
    netn_u1npc6_ = Net('Net-(U1-PC6)')
    netn_u1npc10_ = Net('Net-(U1-PC10)')
    netn_u1npc11_ = Net('Net-(U1-PC11)')
    netn_u1npc14_ = Net('Net-(U1-PC14)')
    netn_u1npc15_ = Net('Net-(U1-PC15)')
    netn_u2na1_ = Net('Net-(U2-A1)')
    netn_u2na2_ = Net('Net-(U2-A2)')
    netn_u2na3_ = Net('Net-(U2-A3)')
    netn_u2na4_ = Net('Net-(U2-A4)')
    netn_u2na5_ = Net('Net-(U2-A5)')
    netn_u2na6_ = Net('Net-(U2-A6)')
    netn_u2na8_ = Net('Net-(U2-A8)')
    netn_u2noe_ = Net('Net-(U2-OE)')
    unconnectedn_j7npad1_ = Net('unconnected-(J7-Pad1)')
    unconnectedn_j7npad2_ = Net('unconnected-(J7-Pad2)')
    unconnectedn_j7npad8_ = Net('unconnected-(J7-Pad8)')
    unconnectedn_j7npad9_ = Net('unconnected-(J7-Pad9)')
    unconnectedn_j7npad10_ = Net('unconnected-(J7-Pad10)')
    unconnectedn_ps1nennpad3_ = Net('unconnected-(PS1-EN-Pad3)')
    unconnectedn_ps2nennpad3_ = Net('unconnected-(PS2-EN-Pad3)')

    # Create components
    c1 = Component(symbol="Device:C_Small", ref="C1", value="CGA0805X5R226M350MT", footprint="Capacitor_SMD:C_0805_2012Metric")
    c2 = Component(symbol="Device:C_Small", ref="C2", value="100nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c3 = Component(symbol="Device:C", ref="C3", value="18pF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c4 = Component(symbol="Device:C_Small", ref="C4", value="CGA0805X5R226M350MT", footprint="Capacitor_SMD:C_0805_2012Metric")
    c5 = Component(symbol="Device:C_Small", ref="C5", value="CGA0805X5R226M350MT", footprint="Capacitor_SMD:C_0805_2012Metric")
    c6 = Component(symbol="Device:C_Small", ref="C6", value="2.2uF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c7 = Component(symbol="Device:C_Small", ref="C7", value="CGA0805X5R226M350MT", footprint="Capacitor_SMD:C_0805_2012Metric")
    c9 = Component(symbol="Device:C_Small", ref="C9", value="2.2uF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c12 = Component(symbol="Device:C", ref="C12", value="18pF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c14 = Component(symbol="Device:C_Small", ref="C14", value="CL05A106MP5NUNC", footprint="Capacitor_SMD:C_0201_0603Metric")
    c18 = Component(symbol="Device:C_Small", ref="C18", value="100nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c19 = Component(symbol="Device:C_Small", ref="C19", value="100nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c20 = Component(symbol="Device:C_Small", ref="C20", value="100nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c21 = Component(symbol="Device:C_Small", ref="C21", value="100nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c22 = Component(symbol="Device:C_Small", ref="C22", value="100nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c23 = Component(symbol="Device:C_Small", ref="C23", value="GRM033R61E104KE14D", footprint="Capacitor_SMD:C_0201_0603Metric")
    c25 = Component(symbol="Device:C_Small", ref="C25", value="CC0603JRNPO9BN220", footprint="Capacitor_SMD:C_0603_1608Metric")
    c27 = Component(symbol="Device:C_Small", ref="C27", value="0603B222K500NT", footprint="Capacitor_SMD:C_0603_1608Metric")
    c30 = Component(symbol="Device:C_Small", ref="C30", value="GRM033R61E104KE14D", footprint="Capacitor_SMD:C_0201_0603Metric")
    c32 = Component(symbol="Device:C_Small", ref="C32", value="CC0603JRNPO9BN220", footprint="Capacitor_SMD:C_0603_1608Metric")
    c33 = Component(symbol="Device:C_Small", ref="C33", value="0402B333K500NT", footprint="Capacitor_SMD:C_0402_1005Metric")
    c34 = Component(symbol="Device:C_Small", ref="C34", value="C2012X5R1V226M125AC", footprint="Capacitor_SMD:C_0805_2012Metric")
    c35 = Component(symbol="Device:C_Small", ref="C35", value="0402B333K500NT", footprint="Capacitor_SMD:C_0402_1005Metric")
    c36 = Component(symbol="Device:C_Small", ref="C36", value="C2012X5R1V226M125AC", footprint="Capacitor_SMD:C_0805_2012Metric")
    c38 = Component(symbol="Device:C_Small", ref="C38", value="C2012X5R1V226M125AC", footprint="Capacitor_SMD:C_0805_2012Metric")
    c39 = Component(symbol="Device:C_Small", ref="C39", value="0603B222K500NT", footprint="Capacitor_SMD:C_0603_1608Metric")
    c40 = Component(symbol="Device:C_Small", ref="C40", value="10nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c41 = Component(symbol="Device:C_Small", ref="C41", value="CL03A104KA3NNNC", footprint="Capacitor_SMD:C_0201_0603Metric")
    c42 = Component(symbol="Device:C_Small", ref="C42", value="2.2uF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c44 = Component(symbol="Device:C_Small", ref="C44", value="10nF", footprint="Capacitor_SMD:C_0201_0603Metric")
    c45 = Component(symbol="Device:C_Small", ref="C45", value="C2012X5R1V226M125AC", footprint="Capacitor_SMD:C_0805_2012Metric")
    c46 = Component(symbol="Device:C_Small", ref="C46", value="C2012X5R1V226M125AC", footprint="Capacitor_SMD:C_0805_2012Metric")
    d1 = Component(symbol="Device:D_Schottky_Small", ref="D1", value="C22452", footprint="Diode_SMD:D_SMA")
    d2 = Component(symbol="Device:LED_Small", ref="D2", value="LED_Small", footprint="LED_SMD:LED_0201_0603Metric")
    d3 = Component(symbol="Device:LED_Small", ref="D3", value="LED_Small", footprint="LED_SMD:LED_0201_0603Metric")
    d12 = Component(symbol="Device:D_Schottky_Small", ref="D12", value="C22452", footprint="Diode_SMD:D_SMA")
    d13 = Component(symbol="Device:LED_Small", ref="D13", value="LED_Small", footprint="LED_SMD:LED_0201_0603Metric")
    fb1 = Component(symbol="Device:FerriteBead_Small", ref="FB1", value="GZ1608D601TF", footprint="Inductor_SMD:L_0603_1608Metric")
    j1 = Component(symbol="skip_kicad_symbols:XT30PW-M", ref="J1", value="XT30PW-M", footprint="_skip:XT30PWM")
    j2 = Component(symbol="Connector:Conn_01x02_Pin", ref="J2", value="B-2100S02P-A110", footprint="Connector_PinHeader_2.54mm:PinHeader_2x01_P2.54mm_Vertical")
    j3 = Component(symbol="Connector:Conn_01x02_Pin", ref="J3", value="B-2100S02P-A110", footprint="Connector_PinHeader_2.54mm:PinHeader_2x01_P2.54mm_Vertical")
    j7 = Component(symbol="skip_kicad_symbols:3220-14-0100-00", ref="J7", value="3220-14-0100-00", footprint="_skip:322014010000")
    j8 = Component(symbol="Connector_Generic:Conn_01x05", ref="J8", value="HB-PH3-25415PB2GOP", footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical")
    j9 = Component(symbol="Connector_Generic:Conn_01x05", ref="J9", value="HB-PH3-25415PB2GOP", footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical")
    j10 = Component(symbol="Connector_Generic:Conn_01x05", ref="J10", value="HB-PH3-25415PB2GOP", footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical")
    l1 = Component(symbol="Device:L", ref="L1", value="FXL0530-4R7-M", footprint="_skip:FXL0530-4R7-M")
    l2 = Component(symbol="Device:L", ref="L2", value="FXL0530-4R7-M", footprint="_skip:FXL0530-4R7-M")
    ps1 = Component(symbol="skip_kicad_symbols:TPS54531DDAR", ref="PS1", value="TPS54531DDAR", footprint="_skip:SOIC127P600X170-9N")
    ps2 = Component(symbol="skip_kicad_symbols:TPS54531DDAR", ref="PS2", value="TPS54531DDAR", footprint="_skip:SOIC127P600X170-9N")
    r2 = Component(symbol="Device:R_Small", ref="R2", value="0603WAF3742T5E", footprint="Capacitor_SMD:C_0603_1608Metric")
    r3 = Component(symbol="Device:R_Small", ref="R3", value="0603WAF3742T5E", footprint="Capacitor_SMD:C_0603_1608Metric")
    r4 = Component(symbol="Device:R_Small", ref="R4", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r5 = Component(symbol="Device:R_Small", ref="R5", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r6 = Component(symbol="Device:R_Small", ref="R6", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r7 = Component(symbol="Device:R_Small", ref="R7", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r8 = Component(symbol="Device:R_Small", ref="R8", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r9 = Component(symbol="Device:R_Small", ref="R9", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r11 = Component(symbol="Device:R_Small", ref="R11", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r12 = Component(symbol="Device:R_Small", ref="R12", value="RC0201FR-0710KL", footprint="Resistor_SMD:R_0201_0603Metric")
    r14 = Component(symbol="Device:R_Small", ref="R14", value="HQ02WAJ0103TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r15 = Component(symbol="Device:R_Small", ref="R15", value="AR03BTDX1202", footprint="Resistor_SMD:R_0603_1608Metric")
    r16 = Component(symbol="Device:R_Small", ref="R16", value="RT0603BRD072K2L", footprint="Capacitor_SMD:C_0603_1608Metric")
    r17 = Component(symbol="Device:R_Small", ref="R17", value="0402WGF1402TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r18 = Component(symbol="Device:R_Small", ref="R18", value="0603WAF1001T5E", footprint="Capacitor_SMD:C_0603_1608Metric")
    r19 = Component(symbol="Device:R_Small", ref="R19", value="RC0201FR-0710KL", footprint="Resistor_SMD:R_0201_0603Metric")
    r20 = Component(symbol="Device:R_Small", ref="R20", value="RC0201FR-0710KL", footprint="Resistor_SMD:R_0201_0603Metric")
    r21 = Component(symbol="Device:R_Small", ref="R21", value="ERA2AEB4991X", footprint="Resistor_SMD:R_0402_1005Metric")
    r22 = Component(symbol="Device:R_Small", ref="R22", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    r64 = Component(symbol="Device:R_Small", ref="R64", value="0402WGF1693TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r66 = Component(symbol="Device:R_Small", ref="R66", value="0402WGF1802TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    s1 = Component(symbol="skip_kicad_symbols:TS-1187A-B-A-B", ref="S1", value="TS-1187A-B-A-B", footprint="_skip:TS1187ABAB")
    th1 = Component(symbol="Device:Thermistor", ref="TH1", value="SDNT1005X103F3950FTF", footprint="Resistor_SMD:R_0402_1005Metric")
    tp1 = Component(symbol="Connector:TestPoint", ref="TP1", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp2 = Component(symbol="Connector:TestPoint", ref="TP2", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp3 = Component(symbol="Connector:TestPoint", ref="TP3", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp4 = Component(symbol="Connector:TestPoint", ref="TP4", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp5 = Component(symbol="Connector:TestPoint", ref="TP5", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp6 = Component(symbol="Connector:TestPoint", ref="TP6", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp7 = Component(symbol="Connector:TestPoint", ref="TP7", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp8 = Component(symbol="Connector:TestPoint", ref="TP8", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp9 = Component(symbol="Connector:TestPoint", ref="TP9", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp16 = Component(symbol="Connector:TestPoint", ref="TP16", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp17 = Component(symbol="Connector:TestPoint", ref="TP17", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp18 = Component(symbol="Connector:TestPoint", ref="TP18", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp19 = Component(symbol="Connector:TestPoint", ref="TP19", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    tp20 = Component(symbol="Connector:TestPoint", ref="TP20", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    u1 = Component(symbol="MCU_ST_STM32G4:STM32G431CBUx", ref="U1", value="STM32G431CBUx", footprint="Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm")
    u2 = Component(symbol="Logic_LevelTranslator:TXS0108EPW", ref="U2", value="TXS0108EPW", footprint="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm")
    u3 = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U3", value="AMS1117-3.3", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    y1 = Component(symbol="_skip:X322512MOB4SI", ref="Y1", value="X322524MOB4SI", footprint="_skip:X322512MOB4SI")

    # Instantiate child circuits
    half_bridge_circuit = half_bridge(_3v3, _12v, gnd, netn_q3nground_1_, pvdc, bemf2, ghs2, gls2, gpio_bemf, phase_v, vshunt2n, vshunt2p, netn_d11nk_)
    half_bridge_circuit = half_bridge(_3v3, _12v, gnd, netn_q3nground_1_, pvdc, bemf2, ghs2, gls2, gpio_bemf, phase_v, vshunt2n, vshunt2p, netn_d11nk_)
    half_bridge_circuit = half_bridge(_3v3, _12v, gnd, netn_q3nground_1_, pvdc, bemf2, ghs2, gls2, gpio_bemf, phase_v, vshunt2n, vshunt2p, netn_d11nk_)

    # Connections
    c14[1] += _3v3
    c18[1] += _3v3
    c19[1] += _3v3
    c2[1] += _3v3
    c20[1] += _3v3
    c21[1] += _3v3
    c36[1] += _3v3
    c6[1] += _3v3
    fb1[1] += _3v3
    j10[4] += _3v3
    j7[3] += _3v3
    r12[2] += _3v3
    th1[1] += _3v3
    u1[1] += _3v3
    u1[23] += _3v3
    u1[35] += _3v3
    u1[48] += _3v3
    u2[2] += _3v3
    u3[2] += _3v3
    c22[1] += _5v
    c38[1] += _5v
    j10[3] += _5v
    j3[1] += _5v
    r19[2] += _5v
    tp1[1] += _5v
    u2[19] += _5v
    u3[3] += _5v
    j10[2] += _12v
    j2[1] += _12v
    r20[2] += _12v
    tp2[1] += _12v
    c1[1] += pvdc
    c4[1] += pvdc
    c5[1] += pvdc
    c7[1] += pvdc
    j1[1] += pvdc
    j10[1] += pvdc
    ps1[2] += pvdc
    ps2[2] += pvdc
    r14[1] += pvdc
    r64[1] += pvdc
    u2[15] += enc_a
    u2[14] += enc_b
    u2[18] += enc_clk
    u2[12] += enc_i
    u2[16] += enc_miso
    u2[17] += enc_mosi
    u2[20] += joint_cs
    u2[13] += rotor_cs
    u1[12] += bemf1
    u1[16] += bemf2
    u1[24] += bemf3
    j8[1] += encoder_cs
    r4[1] += encoder_cs
    u1[25] += encoder_cs
    j8[5] += eqep_a
    r8[1] += eqep_a
    u1[44] += eqep_a
    j9[1] += eqep_b
    r9[1] += eqep_b
    u1[45] += eqep_b
    j9[3] += eqep_i
    r11[1] += eqep_i
    u1[46] += eqep_i
    c35[1] += fet_temp
    r21[1] += fet_temp
    th1[2] += fet_temp
    tp3[1] += fet_temp
    u1[30] += ghs1
    u1[31] += ghs2
    u1[32] += ghs3
    u1[2] += gls1
    u1[34] += gls2
    u1[28] += gls3
    u1[43] += gpio_bemf
    c41[1] += nrst
    j7[12] += nrst
    s1['A1'] += nrst
    s1['B1'] += nrst
    u1[7] += nrst
    c3[1] += oscp
    u1[6] += oscp
    y1[1] += oscp
    c12[1] += oscn
    u1[5] += oscn
    y1[3] += oscn
    j9[2] += rotor_cs_3v3
    r22[1] += rotor_cs_3v3
    j8[2] += spi2_clk
    r5[1] += spi2_clk
    u1[26] += spi2_clk
    j8[4] += spi2_miso
    r7[1] += spi2_miso
    u1[27] += spi2_miso
    j8[3] += spi2_mosi
    r6[1] += spi2_mosi
    u1[33] += spi2_mosi
    j7[6] += swclk
    u1[37] += swclk
    j7[4] += swdio
    u1[36] += swdio
    j7[13] += uart2_rx
    u1[42] += uart2_rx
    j7[14] += uart2_tx
    u1[41] += uart2_tx
    u1[11] += vshunt1n
    u1[9] += vshunt1p
    u1[13] += vshunt2n
    u1[15] += vshunt2p
    u1[19] += vshunt3n
    u1[17] += vshunt3p
    c33[1] += vbus_sense
    r64[2] += vbus_sense
    r66[1] += vbus_sense
    u1[8] += vbus_sense
    c1[2] += gnd
    c12[2] += gnd
    c14[2] += gnd
    c18[2] += gnd
    c19[2] += gnd
    c2[2] += gnd
    c20[2] += gnd
    c21[2] += gnd
    c22[2] += gnd
    c23[1] += gnd
    c25[1] += gnd
    c3[2] += gnd
    c30[1] += gnd
    c32[1] += gnd
    c33[2] += gnd
    c34[2] += gnd
    c35[2] += gnd
    c36[2] += gnd
    c38[2] += gnd
    c4[2] += gnd
    c41[2] += gnd
    c42[2] += gnd
    c45[2] += gnd
    c46[2] += gnd
    c5[2] += gnd
    c6[2] += gnd
    c7[2] += gnd
    c9[2] += gnd
    d1[2] += gnd
    d12[2] += gnd
    d13[1] += gnd
    d2[1] += gnd
    d3[1] += gnd
    j1[2] += gnd
    j1[3] += gnd
    j1[4] += gnd
    j10[5] += gnd
    j7[11] += gnd
    j7[5] += gnd
    j7[7] += gnd
    j9[4] += gnd
    j9[5] += gnd
    ps1[7] += gnd
    ps1[9] += gnd
    ps2[7] += gnd
    ps2[9] += gnd
    r16[2] += gnd
    r18[2] += gnd
    r2[2] += gnd
    r21[2] += gnd
    r3[2] += gnd
    r66[2] += gnd
    s1['C1'] += gnd
    s1['D1'] += gnd
    u1[49] += gnd
    u2[11] += gnd
    u3[1] += gnd
    y1[2] += gnd
    y1[4] += gnd
    c27[1] += netn_c27npad1_
    r3[1] += netn_c27npad1_
    c39[1] += netn_c39npad1_
    r2[1] += netn_c39npad1_
    c40[1] += netn_d1nk_
    d1[1] += netn_d1nk_
    l1[1] += netn_d1nk_
    ps1[8] += netn_d1nk_
    d2[2] += netn_d2na_
    r14[2] += netn_d2na_
    d3[2] += netn_d3na_
    r19[1] += netn_d3na_
    c44[1] += netn_d12nk_
    d12[1] += netn_d12nk_
    l2[1] += netn_d12nk_
    ps2[8] += netn_d12nk_
    d13[2] += netn_d13na_
    r20[1] += netn_d13na_
    c45[1] += netn_j2npin_2_
    c46[1] += netn_j2npin_2_
    j2[2] += netn_j2npin_2_
    l2[2] += netn_j2npin_2_
    r17[1] += netn_j2npin_2_
    c34[1] += netn_j3npin_2_
    j3[2] += netn_j3npin_2_
    l1[2] += netn_j3npin_2_
    r15[1] += netn_j3npin_2_
    c40[2] += netn_ps1nboot_
    ps1[1] += netn_ps1nboot_
    c25[2] += netn_ps1ncomp_
    c27[2] += netn_ps1ncomp_
    ps1[6] += netn_ps1ncomp_
    c23[2] += netn_ps1nss_
    ps1[4] += netn_ps1nss_
    ps1[5] += netn_ps1nvsense_
    r15[2] += netn_ps1nvsense_
    r16[1] += netn_ps1nvsense_
    c44[2] += netn_ps2nboot_
    ps2[1] += netn_ps2nboot_
    c32[2] += netn_ps2ncomp_
    c39[2] += netn_ps2ncomp_
    ps2[6] += netn_ps2ncomp_
    c30[2] += netn_ps2nss_
    ps2[4] += netn_ps2nss_
    ps2[5] += netn_ps2nvsense_
    r17[2] += netn_ps2nvsense_
    r18[1] += netn_ps2nvsense_
    tp4[1] += netn_u1npa2_
    u1[10] += netn_u1npa2_
    tp5[1] += netn_u1npa6_
    u1[14] += netn_u1npa6_
    tp6[1] += netn_u1npa15_
    u1[38] += netn_u1npa15_
    tp18[1] += netn_u1npb1_
    u1[18] += netn_u1npb1_
    tp19[1] += netn_u1npb9_
    u1[47] += netn_u1npb9_
    tp20[1] += netn_u1npb10_
    u1[22] += netn_u1npb10_
    tp7[1] += netn_u1npc6_
    u1[29] += netn_u1npc6_
    tp8[1] += netn_u1npc10_
    u1[39] += netn_u1npc10_
    tp9[1] += netn_u1npc11_
    u1[40] += netn_u1npc11_
    tp16[1] += netn_u1npc14_
    u1[3] += netn_u1npc14_
    tp17[1] += netn_u1npc15_
    u1[4] += netn_u1npc15_
    r4[2] += netn_u2na1_
    u2[1] += netn_u2na1_
    r5[2] += netn_u2na2_
    u2[3] += netn_u2na2_
    r6[2] += netn_u2na3_
    u2[4] += netn_u2na3_
    r7[2] += netn_u2na4_
    u2[5] += netn_u2na4_
    r8[2] += netn_u2na5_
    u2[6] += netn_u2na5_
    r9[2] += netn_u2na6_
    u2[7] += netn_u2na6_
    r22[2] += netn_u2na7_
    u2[8] += netn_u2na7_
    r11[2] += netn_u2na8_
    u2[9] += netn_u2na8_
    r12[1] += netn_u2noe_
    u2[10] += netn_u2noe_
    c42[1] += vdda
    c9[1] += vdda
    fb1[2] += vdda
    u1[20] += vdda
    u1[21] += vdda