#!/usr/bin/env python3
"""
Fixture: Level shifter circuit with multiple voltage domains in subcircuit.

This tests multi-voltage power distribution through hierarchical circuits:
- Root sheet: VCC_5V and VCC_3V3 power rails (two voltage domains)
- Child sheet (Level_Shifter): Contains level shifter circuit requiring BOTH voltages

This is a CRITICAL real-world pattern: subcircuits that need multiple voltage
domains (like level shifters interfacing between 5V and 3.3V systems).

Circuit topology:
- VCC_5V: Powers 5V side pull-up resistor (R1)
- VCC_3V3: Powers 3.3V side pull-up resistor (R2)
- Q1: N-channel MOSFET (BSS138) for level shifting
- GND: Common ground reference

Starting point:
- One level shifter (Q1, R1, R2) with dual voltage power symbols in child sheet
- Test will add second level shifter (Q2, R3, R4) to verify power symbol reuse
"""

from circuit_synth import *


@circuit(name="level_shifter")
def level_shifter():
    """Hierarchical level shifter circuit with dual voltage domains.

    Root sheet:
    - Establishes VCC_5V power net (5V supply)
    - Establishes VCC_3V3 power net (3.3V supply)
    - Establishes GND net (common ground)

    Child sheet (Level_Shifter):
    - Level shifter circuit (Q1, R1, R2) requiring both voltages
    - Power symbols (VCC_5V, VCC_3V3, GND) placed IN child sheet
    - Hierarchical labels connecting to parent for both voltages

    Circuit operation:
    - 5V side: Input signal pulls Q1 gate through R1
    - 3.3V side: Output signal on Q1 drain through R2
    - Q1 source: Connected to GND
    - Bidirectional level shifting between 5V and 3.3V domains
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet: Establish two voltage domains
    # In real designs, these would connect to voltage regulators
    vcc_5v = Net(name="VCC_5V")     # 5V supply rail
    vcc_3v3 = Net(name="VCC_3V3")   # 3.3V supply rail
    gnd = Net(name="GND")            # Common ground

    # START_MARKER: Test will modify between these markers to add second shifter

    # Child sheet: Level shifter circuit with dual voltage domains
    shifter_circuit = Circuit("Level_Shifter")

    # Components on child sheet
    # Q1: N-channel MOSFET for level shifting (BSS138 or similar)
    q1 = Component(
        symbol="Device:Q_NMOS",
        ref="Q1",
        value="BSS138",
        footprint="Package_TO_SOT_SMD:SOT-23",
    )

    # R1: Pull-up resistor on 5V side (input side)
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R2: Pull-up resistor on 3.3V side (output side)
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    shifter_circuit.add_component(q1)
    shifter_circuit.add_component(r1)
    shifter_circuit.add_component(r2)

    # Power symbols IN child sheet for BOTH voltage domains
    # This is the key pattern: multiple voltage domains distributed to subcircuit
    vcc_5v_child = Net(name="VCC_5V")
    vcc_3v3_child = Net(name="VCC_3V3")
    gnd_child = Net(name="GND")

    # Connect level shifter circuit
    # 5V side: VCC_5V -> R1 -> Q1 gate (5V input signal)
    vcc_5v_child += r1[1]  # R1 pull-up to 5V

    # 3.3V side: VCC_3V3 -> R2 -> Q1 drain (3.3V output signal)
    vcc_3v3_child += r2[1]  # R2 pull-up to 3.3V

    # Level shifter connections
    # Q_NMOS: pins are G (gate), S (source), D (drain)
    r1[2] += q1["G"]      # R1 other end to gate (5V side input node)
    r2[2] += q1["D"]      # R2 other end to drain (3.3V side output node)
    q1["S"] += gnd_child  # Source to ground

    # Note: In real circuit, additional connections would be:
    # - 5V_IN signal connects to node between R1 and Q1 gate
    # - 3V3_OUT signal connects to node between R2 and Q1 drain
    # These are omitted for clarity in this test

    root.add_subcircuit(shifter_circuit)

    # END_MARKER


if __name__ == "__main__":
    circuit_obj = level_shifter()
    circuit_obj.generate_kicad_project(
        project_name="level_shifter", placement_algorithm="simple", generate_pcb=True
    )
    print("✅ Level shifter with dual voltage domains generated!")
    print("📁 Open in KiCad: level_shifter/level_shifter.kicad_pro")
    print("\n⚡ Power domains:")
    print("   - VCC_5V: 5V supply (R1 pull-up)")
    print("   - VCC_3V3: 3.3V supply (R2 pull-up)")
    print("   - GND: Common ground (Q1 source)")
