#!/usr/bin/env python3
"""
Circuit Generated from KiCad
"""

from circuit_synth import *

@circuit
def main():
    """Generated circuit from KiCad"""
    # Create nets
    avdd = Net('AVDD')
    c1 = Net('C1')
    c2 = Net('C2')
    c3 = Net('C3')
    cbo = Net('CBO')
    cd = Net('CD')
    chg = Net('CHG')
    dsg = Net('DSG')
    ld = Net('LD')
    lpwr = Net('LPWR')
    ocdp = Net('OCDP')
    packn = Net('PACK-')
    pres = Net('PRES')
    srp = Net('SR+')
    srn = Net('SR-')
    ts = Net('TS')
    vc0 = Net('VC0')
    vc1 = Net('VC1')
    vc2 = Net('VC2')
    vc3 = Net('VC3')
    vdd = Net('VDD')
    vtb = Net('VTB')
    gnd = Net('GND')
    netn_c10npad1_ = Net('Net-(C10-Pad1)')
    netn_c12npad1_ = Net('Net-(C12-Pad1)')
    netn_nt1npad2_ = Net('Net-(NT1-Pad2)')
    netn_nt2npad2_ = Net('Net-(NT2-Pad2)')
    netn_nt3npad2_ = Net('Net-(NT3-Pad2)')
    netn_q1ng_ = Net('Net-(Q1-G)')
    netn_q1ns_1_ = Net('Net-(Q1-S_1)')
    netn_q2ng_ = Net('Net-(Q2-G)')

    # Create components
    c1 = Component(symbol="Device:C_Small", ref="C1", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c2 = Component(symbol="Device:C_Small", ref="C2", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c3 = Component(symbol="Device:C_Small", ref="C3", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c4 = Component(symbol="Device:C_Small", ref="C4", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c5 = Component(symbol="Device:C_Small", ref="C5", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c6 = Component(symbol="Device:C_Small", ref="C6", value="CL05B104KB54PNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c7 = Component(symbol="Device:C_Small", ref="C7", value="CL05B104KB54PNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c8 = Component(symbol="Device:C_Small", ref="C8", value="CL05B104KB54PNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c9 = Component(symbol="Device:C_Small", ref="C9", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c10 = Component(symbol="Device:C_Small", ref="C10", value="CL05B104KB54PNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c11 = Component(symbol="Device:C_Small", ref="C11", value="CL05B104KB54PNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c12 = Component(symbol="Device:C_Small", ref="C12", value="CL05B104KB54PNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    c13 = Component(symbol="Device:C_Small", ref="C13", value="CL05B104KB54PNC", footprint="Capacitor_SMD:C_0402_1005Metric")
    ic1 = Component(symbol="_skip:BQ7791502PWR", ref="IC1", value="BQ7791501PWR", footprint="skip_kicad:SOP65P640X120-24N")
    nt1 = Component(symbol="Device:NetTie_2", ref="NT1", value="NetTie_2", footprint="NetTie:NetTie-2_SMD_Pad2.0mm")
    nt2 = Component(symbol="Device:NetTie_2", ref="NT2", value="NetTie_2", footprint="NetTie:NetTie-2_SMD_Pad0.5mm")
    nt3 = Component(symbol="Device:NetTie_2", ref="NT3", value="NetTie_2", footprint="NetTie:NetTie-2_SMD_Pad0.5mm")
    q1 = Component(symbol="_skip:STL220N6F7", ref="Q1", value="STL220N6F7", footprint="skip_kicad:FERD20U50DJFTR")
    q2 = Component(symbol="_skip:STL220N6F7", ref="Q2", value="STL220N6F7", footprint="skip_kicad:FERD20U50DJFTR")
    r1 = Component(symbol="Device:R_Small", ref="R1", value="RC-02W2943FT", footprint="Resistor_SMD:R_0402_1005Metric")
    r2 = Component(symbol="Device:R_Small", ref="R2", value="0402WGF1002TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r3 = Component(symbol="Device:R_Small", ref="R3", value="0805W8F330JT5E", footprint="Resistor_SMD:R_0805_2012Metric")
    r4 = Component(symbol="Device:R_Small", ref="R4", value="0805W8F1001T5E", footprint="Resistor_SMD:R_0805_2012Metric")
    r5 = Component(symbol="Device:R_Small", ref="R5", value="0805W8F330JT5E", footprint="Resistor_SMD:R_0805_2012Metric")
    r6 = Component(symbol="Device:R_Small", ref="R6", value="0805W8F330JT5E", footprint="Resistor_SMD:R_0805_2012Metric")
    r7 = Component(symbol="Device:R_Small", ref="R7", value="0805W8F330JT5E", footprint="Resistor_SMD:R_0805_2012Metric")
    r8 = Component(symbol="Device:R_Small", ref="R8", value="0402WGF1002TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r10 = Component(symbol="Device:R_Small", ref="R10", value="0402WGF1000TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r11 = Component(symbol="Device:R", ref="R11", value="CSM2512FT1L00", footprint="Resistor_SMD:R_2512_6332Metric")
    r12 = Component(symbol="Device:R_Small", ref="R12", value="0402WGF1000TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r13 = Component(symbol="Device:R_Small", ref="R13", value="ERJ2RKF4531X", footprint="Resistor_SMD:R_0402_1005Metric")
    r14 = Component(symbol="Device:R_Small", ref="R14", value="0402WGF1004TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r15 = Component(symbol="Device:R_Small", ref="R15", value="0402WGF1001TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r18 = Component(symbol="Device:R_Small", ref="R18", value="0402WGF1004TCE", footprint="Resistor_SMD:R_0402_1005Metric")
    r19 = Component(symbol="Device:R_Small", ref="R19", value="CR0402FF4703G", footprint="Resistor_SMD:R_0402_1005Metric")
    th1 = Component(symbol="Device:Thermistor_NTC", ref="TH1", value="NCP18XH103F03RB", footprint="Resistor_SMD:R_0603_1608Metric")
    tp1 = Component(symbol="Connector:TestPoint_Alt", ref="TP1", value="TestPoint_Alt", footprint="skip_kicad:TP_9mmx6mm")
    tp2 = Component(symbol="Connector:TestPoint_Alt", ref="TP2", value="TestPoint_Alt", footprint="skip_kicad:TP_9mmx6mm")
    tp3 = Component(symbol="Connector:TestPoint_Alt", ref="TP3", value="TestPoint_Alt", footprint="TestPoint:TestPoint_Pad_4.0x4.0mm")
    tp4 = Component(symbol="Connector:TestPoint_Alt", ref="TP4", value="TestPoint_Alt", footprint="TestPoint:TestPoint_Pad_4.0x4.0mm")
    tp5 = Component(symbol="Connector:TestPoint", ref="TP5", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp6 = Component(symbol="Connector:TestPoint", ref="TP6", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp7 = Component(symbol="Connector:TestPoint", ref="TP7", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp8 = Component(symbol="Connector:TestPoint", ref="TP8", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp9 = Component(symbol="Connector:TestPoint", ref="TP9", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp10 = Component(symbol="Connector:TestPoint", ref="TP10", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp11 = Component(symbol="Connector:TestPoint", ref="TP11", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp12 = Component(symbol="Connector:TestPoint_Alt", ref="TP12", value="TestPoint_Alt", footprint="TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm")
    tp13 = Component(symbol="Connector:TestPoint_Alt", ref="TP13", value="TestPoint_Alt", footprint="TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm")
    tp14 = Component(symbol="Connector:TestPoint", ref="TP14", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp15 = Component(symbol="Connector:TestPoint", ref="TP15", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp16 = Component(symbol="Connector:TestPoint", ref="TP16", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.5x1.5mm")
    tp17 = Component(symbol="Connector:TestPoint", ref="TP17", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.5x1.5mm")
    tp18 = Component(symbol="Connector:TestPoint", ref="TP18", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp19 = Component(symbol="Connector:TestPoint", ref="TP19", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp20 = Component(symbol="Connector:TestPoint", ref="TP20", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp21 = Component(symbol="Connector:TestPoint", ref="TP21", value="TestPoint", footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp22 = Component(symbol="Connector:TestPoint_Alt", ref="TP22", value="TestPoint_Alt", footprint="TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm")
    tp23 = Component(symbol="Connector:TestPoint_Alt", ref="TP23", value="TestPoint_Alt", footprint="TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm")
    tp24 = Component(symbol="Connector:TestPoint_Alt", ref="TP24", value="TestPoint_Alt", footprint="TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm")
    tp25 = Component(symbol="Connector:TestPoint_Alt", ref="TP25", value="TestPoint_Alt", footprint="TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm")

    # Connections
    c9[2] += avdd
    ic1[2] += avdd
    r5[1] += c1
    tp19[1] += c1
    tp3[1] += c1
    r3[1] += c2
    tp18[1] += c2
    tp4[1] += c2
    c13[2] += c3
    nt3[1] += c3
    r4[1] += c3
    tp1[1] += c3
    tp13[1] += c3
    tp15[1] += c3
    tp23[1] += c3
    ic1[21] += cbo
    q1[5] += cd
    q1[6] += cd
    q1[7] += cd
    q1[8] += cd
    q1[9] += cd
    q2[5] += cd
    q2[6] += cd
    q2[7] += cd
    q2[8] += cd
    q2[9] += cd
    tp9[1] += cd
    ic1[13] += chg
    r15[1] += chg
    ic1[12] += dsg
    r13[1] += dsg
    ic1[14] += ld
    r19[1] += ld
    tp11[1] += ld
    ic1[15] += lpwr
    tp20[1] += lpwr
    ic1[17] += ocdp
    r1[2] += ocdp
    c11[1] += packn
    c12[2] += packn
    q2[1] += packn
    q2[2] += packn
    q2[3] += packn
    r18[2] += packn
    r19[2] += packn
    tp12[1] += packn
    tp14[1] += packn
    tp22[1] += packn
    ic1[22] += pres
    r2[1] += pres
    tp21[1] += pres
    c6[2] += srp
    c7[2] += srp
    ic1[10] += srp
    r10[1] += srp
    tp5[1] += srp
    c7[1] += srn
    c8[2] += srn
    ic1[11] += srn
    r12[1] += srn
    tp6[1] += srn
    ic1[18] += ts
    r8[1] += ts
    th1[2] += ts
    tp17[1] += ts
    c1[2] += vc0
    ic1[8] += vc0
    r6[2] += vc0
    c3[2] += vc1
    c4[1] += vc1
    ic1[7] += vc1
    r5[2] += vc1
    c4[2] += vc2
    c5[1] += vc2
    ic1[6] += vc2
    r3[2] += vc2
    c5[2] += vc3
    ic1[3] += vc3
    ic1[4] += vc3
    ic1[5] += vc3
    r7[2] += vc3
    c2[2] += vdd
    ic1[1] += vdd
    r2[2] += vdd
    r4[2] += vdd
    tp8[1] += vdd
    ic1[19] += vtb
    r8[2] += vtb
    c1[1] += gnd
    c2[1] += gnd
    c3[1] += gnd
    c6[1] += gnd
    c8[1] += gnd
    c9[1] += gnd
    ic1[16] += gnd
    ic1[20] += gnd
    ic1[23] += gnd
    ic1[24] += gnd
    ic1[9] += gnd
    nt1[1] += gnd
    nt2[1] += gnd
    r1[1] += gnd
    th1[1] += gnd
    tp16[1] += gnd
    tp2[1] += gnd
    c10[1] += netn_c10npad1_
    c11[2] += netn_c10npad1_
    c12[1] += netn_c12npad1_
    c13[1] += netn_c12npad1_
    nt1[2] += netn_nt1npad2_
    r10[2] += netn_nt1npad2_
    r11[1] += netn_nt1npad2_
    nt2[2] += netn_nt2npad2_
    r6[1] += netn_nt2npad2_
    nt3[2] += netn_nt3npad2_
    r7[1] += netn_nt3npad2_
    q1[4] += netn_q1ng_
    r13[2] += netn_q1ng_
    r14[1] += netn_q1ng_
    tp7[1] += netn_q1ng_
    c10[2] += netn_q1ns_1_
    q1[1] += netn_q1ns_1_
    q1[2] += netn_q1ns_1_
    q1[3] += netn_q1ns_1_
    r11[2] += netn_q1ns_1_
    r12[2] += netn_q1ns_1_
    r14[2] += netn_q1ns_1_
    q2[4] += netn_q2ng_
    r15[2] += netn_q2ng_
    r18[1] += netn_q2ng_
    tp10[1] += netn_q2ng_

# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="bms_v_0_9_generated")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("bms_v_0_9_generated/bms_v_0_9_generated.net")