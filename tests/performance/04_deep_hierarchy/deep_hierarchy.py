#!/usr/bin/env python3
"""Deep hierarchy circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="level_10")
def level_10(sig_in, sig_out):
    r = Component(symbol="Device:R", ref="R10", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_out

@circuit(name="level_9")
def level_9(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_9")
    r = Component(symbol="Device:R", ref="R9", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_10(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_8")
def level_8(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_8")
    r = Component(symbol="Device:R", ref="R8", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_9(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_7")
def level_7(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_7")
    r = Component(symbol="Device:R", ref="R7", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_8(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_6")
def level_6(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_6")
    r = Component(symbol="Device:R", ref="R6", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_7(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_5")
def level_5(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_5")
    r = Component(symbol="Device:R", ref="R5", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_6(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_4")
def level_4(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_4")
    r = Component(symbol="Device:R", ref="R4", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_5(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_3")
def level_3(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_3")
    r = Component(symbol="Device:R", ref="R3", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_4(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_2")
def level_2(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_2")
    r = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_3(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="deep_hierarchy")
def deep_hierarchy():
    """Deep hierarchy with 10 levels."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig_in = Net(name="SIG_IN")

    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r1[1] += vcc
    r1[2] += sig_in

    level_2(sig_in=sig_in, sig_out=gnd)

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = deep_hierarchy()
    circuit_obj.generate_kicad_project(project_name="deep_hierarchy", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Deep hierarchy circuit generated in {elapsed:.2f}s")
