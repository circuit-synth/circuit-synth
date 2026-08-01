"""Three-phase BLDC motor driver - hierarchical block example.

Demonstrates hierarchical blocks with declared inputs and outputs. Each
subcircuit annotates its parameters with a port direction, so the generated
KiCad project gets real hierarchical sheet pins and matching hierarchical
labels instead of net-name-matched labels.

Structure:

    bldc_motor_driver (root)
    +-- Power             VBUS in -> 30V and 3.3V out
    +-- MCU               3.3V in -> six gate drive signals out
    +-- PhaseDriver       HI/LI in -> PHASE out   (three instances, A/B/C)
    +-- PhaseDriver2
    +-- PhaseDriver3

The three phase drivers are three instances of the same block. Because the
interface is declared by port name rather than by net name, each instance
connects to a different set of nets while keeping the same block definition.

KiCad ERC reports the STM32's unused GPIO pins as unconnected. That is expected
for an example that only wires up the six timer outputs it needs.
"""

from circuit_synth import (
    Bidirectional,
    Component,
    Input,
    Net,
    Output,
    PowerIn,
    PowerOut,
    circuit,
)


@circuit(name="Power")
def power(V30: PowerOut, V3V3: PowerOut, GND: Bidirectional):
    """Board supply: a 30V motor rail and a 3.3V logic rail.

    The DC input arrives on J1, is fused to become the 30V motor rail, and an
    LM2596 buck converter derives 3.3V from it for the logic. Only the two
    output rails and ground are exported, so the input wiring stays inside
    this block.
    """
    vbus = Net("VBUS")

    input_conn = Component(
        symbol="Connector_Generic:Conn_01x02",
        ref="J",
        value="VBUS_30V",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    )
    bulk_cap = Component(
        symbol="Device:C_Polarized",
        ref="C",
        value="470uF/50V",
        footprint="Capacitor_SMD:CP_Elec_10x10.5",
    )
    rail_cap = Component(
        symbol="Device:C",
        ref="C",
        value="1uF/50V",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )

    buck = Component(
        symbol="Regulator_Switching:LM2596S-3.3",
        ref="U",
        value="LM2596S-3.3",
        footprint="Package_TO_SOT_SMD:TO-263-5_TabPin3",
    )
    buck_in_cap = Component(
        symbol="Device:C",
        ref="C",
        value="100nF/50V",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    catch_diode = Component(
        symbol="Device:D_Schottky",
        ref="D",
        value="SS54",
        footprint="Diode_SMD:D_SMA",
    )
    inductor = Component(
        symbol="Device:L",
        ref="L",
        value="33uH",
        footprint="Inductor_SMD:L_12x12mm_H8mm",
    )
    out_cap = Component(
        symbol="Device:C",
        ref="C",
        value="220uF/10V",
        footprint="Capacitor_SMD:C_1210_3225Metric",
    )

    fuse = Component(
        symbol="Device:Fuse",
        ref="F",
        value="5A",
        footprint="Fuse:Fuse_1206_3216Metric",
    )
    # PWR_FLAG tells KiCad's ERC that these rails are driven, which it cannot
    # infer when a rail arrives through a connector or a hierarchical port.
    flags = [
        Component(symbol="power:PWR_FLAG", ref="#FLG", footprint="") for _ in range(4)
    ]

    switch_node = Net("SW_NODE")

    # Fused input becomes the 30V motor rail.
    input_conn[1] += vbus
    input_conn[2] += GND
    bulk_cap[1] += vbus
    bulk_cap[2] += GND
    fuse[1] += vbus
    fuse[2] += V30
    rail_cap[1] += V30
    rail_cap[2] += GND

    # LM2596 buck: 30V -> 3.3V, fixed output so FB ties to the output.
    buck[1] += V30  # VIN
    buck[3] += GND  # GND
    buck[5] += GND  # ~ON/OFF, low to enable
    buck[2] += switch_node  # OUT
    buck[4] += V3V3  # FB

    buck_in_cap[1] += V30
    buck_in_cap[2] += GND

    flags[0][1] += V30
    flags[1][1] += V3V3
    flags[2][1] += GND
    flags[3][1] += vbus

    catch_diode[2] += switch_node  # cathode
    catch_diode[1] += GND  # anode

    inductor[1] += switch_node
    inductor[2] += V3V3

    out_cap[1] += V3V3
    out_cap[2] += GND


@circuit(name="MCU")
def mcu(
    V3V3: PowerIn,
    GND: Bidirectional,
    AH: Output,
    AL: Output,
    BH: Output,
    BL: Output,
    CH: Output,
    CL: Output,
):
    """STM32F103 generating the six half-bridge gate drive signals.

    TIM1 provides three complementary channel pairs on PA8/PB13, PA9/PB14 and
    PA10/PB15, which is the usual mapping for three-phase drive.
    """
    stm32 = Component(
        symbol="MCU_ST_STM32F1:STM32F103C8Tx",
        ref="U",
        value="STM32F103C8T6",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
    )
    boot_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    reset_cap = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    decoupling = [
        Component(
            symbol="Device:C",
            ref="C",
            value="100nF",
            footprint="Capacitor_SMD:C_0603_1608Metric",
        )
        for _ in range(3)
    ]

    reset = Net("NRST")

    # Power pins are addressed by number because the symbol repeats the VDD
    # and VSS names across several pins.
    for vdd_pin in (24, 36, 48):
        stm32[vdd_pin] += V3V3
    for vss_pin in (23, 35, 47):
        stm32[vss_pin] += GND
    stm32[1] += V3V3  # VBAT
    stm32[9] += V3V3  # VDDA
    stm32[8] += GND  # VSSA

    stm32[7] += reset  # NRST
    reset_cap[1] += reset
    reset_cap[2] += GND

    stm32[44] += boot_resistor[1]  # BOOT0
    boot_resistor[2] += GND

    for cap in decoupling:
        cap[1] += V3V3
        cap[2] += GND

    # TIM1 complementary outputs.
    stm32[29] += AH  # PA8  - TIM1_CH1
    stm32[26] += AL  # PB13 - TIM1_CH1N
    stm32[30] += BH  # PA9  - TIM1_CH2
    stm32[27] += BL  # PB14 - TIM1_CH2N
    stm32[31] += CH  # PA10 - TIM1_CH3
    stm32[28] += CL  # PB15 - TIM1_CH3N


@circuit(name="PhaseDriver")
def phase_driver(
    HI: Input,
    LI: Input,
    PHASE: Output,
    VM: PowerIn,
    VDRV: PowerIn,
    GND: Bidirectional,
):
    """One half-bridge: high and low side drive in, motor phase out.

    An IR2101 high/low side driver with a bootstrap supply drives a pair of
    N-channel MOSFETs. Three instances of this block make a three-phase
    inverter.
    """
    driver = Component(
        symbol="Driver_FET:IR2101",
        ref="U",
        value="IR2101",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    )
    high_fet = Component(
        symbol="Transistor_FET:Q_NMOS_GDS",
        ref="Q",
        value="IRF3205",
        footprint="Package_TO_SOT_SMD:TO-263-3_TabPin2",
    )
    low_fet = Component(
        symbol="Transistor_FET:Q_NMOS_GDS",
        ref="Q",
        value="IRF3205",
        footprint="Package_TO_SOT_SMD:TO-263-3_TabPin2",
    )
    high_gate_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="10R",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )
    low_gate_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="10R",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )
    bootstrap_cap = Component(
        symbol="Device:C",
        ref="C",
        value="1uF/25V",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    bootstrap_diode = Component(
        symbol="Device:D_Schottky",
        ref="D",
        value="BAT54",
        footprint="Diode_SMD:D_SOD-123",
    )
    vcc_cap = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    boot = Net("BOOT")
    high_gate = Net("HGATE")
    low_gate = Net("LGATE")

    # Driver supply and logic inputs.
    driver[1] += VDRV  # VCC
    driver[4] += GND  # COM
    driver[2] += HI  # HIN
    driver[3] += LI  # LIN
    vcc_cap[1] += VDRV
    vcc_cap[2] += GND

    # Bootstrap supply referenced to the switching node.
    bootstrap_diode[1] += VDRV  # anode
    bootstrap_diode[2] += boot  # cathode
    driver[8] += boot  # VB
    driver[6] += PHASE  # VS
    bootstrap_cap[1] += boot
    bootstrap_cap[2] += PHASE

    # Gate drive.
    driver[7] += high_gate_resistor[1]  # HO
    high_gate_resistor[2] += high_gate
    driver[5] += low_gate_resistor[1]  # LO
    low_gate_resistor[2] += low_gate

    # Half bridge.
    high_fet[1] += high_gate
    high_fet[2] += VM
    high_fet[3] += PHASE

    low_fet[1] += low_gate
    low_fet[2] += PHASE
    low_fet[3] += GND


@circuit(name="BLDC_Motor_Driver")
def bldc_motor_driver():
    """Three-phase BLDC motor driver built from nested hierarchical blocks."""
    v30 = Net("V30")
    v3v3 = Net("V3V3")
    gnd = Net("GND")

    ah, al = Net("AH"), Net("AL")
    bh, bl = Net("BH"), Net("BL")
    ch, cl = Net("CH"), Net("CL")

    phase_a = Net("PHASE_A")
    phase_b = Net("PHASE_B")
    phase_c = Net("PHASE_C")

    power(v30, v3v3, gnd)
    mcu(v3v3, gnd, ah, al, bh, bl, ch, cl)

    # Three instances of one block, each on its own phase.
    phase_driver(ah, al, phase_a, v30, v3v3, gnd)
    phase_driver(bh, bl, phase_b, v30, v3v3, gnd)
    phase_driver(ch, cl, phase_c, v30, v3v3, gnd)

    motor = Component(
        symbol="Connector_Generic:Conn_01x03",
        ref="J",
        value="BLDC_MOTOR",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    )
    motor[1] += phase_a
    motor[2] += phase_b
    motor[3] += phase_c


if __name__ == "__main__":
    circuit_obj = bldc_motor_driver()
    circuit_obj.generate_kicad_project(
        project_name="bldc_motor_driver",
        force_regenerate=True,
        generate_pcb=False,
    )
    print("Generated bldc_motor_driver/bldc_motor_driver.kicad_pro")
