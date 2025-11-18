from circuit_synth import circuit, Component, Net

@circuit(name="ESP32_C6_Dev_Kit")
def esp32_dev_kit():
    """
    Complete ESP32-C6 Development Kit
    - USB-C power input with 5V
    - 3.3V linear regulator with proper decoupling
    - Auto-reset circuit for programming
    - Boot button for manual entry to programming mode
    - User LED on GPIO8
    - All GPIOs broken out to headers
    """

    # ======================
    # USB-C Interface
    # ======================
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4085"
    )

    # CC resistors for 5V power negotiation (5.1k to GND)
    cc1_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    cc2_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # ======================
    # Power Supply (5V to 3.3V)
    # ======================
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    # Input capacitor (before regulator)
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Output capacitor (after regulator)
    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # ======================
    # ESP32-C6 Module
    # ======================
    esp32 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )

    # ESP32 decoupling capacitors
    cap_esp1 = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    cap_esp2 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # ======================
    # Programming Interface (Auto-Reset)
    # ======================
    # DTR/RTS capacitors for auto-reset circuit
    cap_dtr = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_rts = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Reset pull-up resistor
    reset_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Boot pull-up resistor
    boot_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # ======================
    # User Buttons
    # ======================
    boot_btn = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )

    reset_btn = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )

    # ======================
    # User LED
    # ======================
    led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    led_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # ======================
    # GPIO Headers
    # ======================
    header_left = Component(
        symbol="Connector_Generic:Conn_01x15_Pin",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x15_P2.54mm_Vertical"
    )

    header_right = Component(
        symbol="Connector_Generic:Conn_01x15_Pin",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x15_P2.54mm_Vertical"
    )

    # ======================
    # Define Nets
    # ======================
    # Power nets
    vbus = Net('VBUS')          # 5V from USB
    vcc_3v3 = Net('VCC_3V3')    # 3.3V regulated
    gnd = Net('GND')            # Ground

    # USB data nets
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    cc1 = Net('CC1')
    cc2 = Net('CC2')

    # Programming nets
    dtr = Net('DTR')
    rts = Net('RTS')
    en = Net('EN')              # Reset pin
    gpio9 = Net('GPIO9')        # Boot pin

    # GPIO nets
    gpio8 = Net('GPIO8')        # User LED
    gpio0 = Net('GPIO0')
    gpio1 = Net('GPIO1')
    gpio2 = Net('GPIO2')
    gpio3 = Net('GPIO3')
    gpio4 = Net('GPIO4')
    gpio5 = Net('GPIO5')
    gpio6 = Net('GPIO6')
    gpio7 = Net('GPIO7')
    gpio10 = Net('GPIO10')
    gpio11 = Net('GPIO11')
    gpio18 = Net('GPIO18')
    gpio19 = Net('GPIO19')
    gpio20 = Net('GPIO20')
    gpio21 = Net('GPIO21')
    gpio22 = Net('GPIO22')
    gpio23 = Net('GPIO23')

    # ======================
    # USB-C Connections
    # ======================
    usb_conn["VBUS"] += vbus
    usb_conn["GND"] += gnd
    usb_conn["CC1"] += cc1
    usb_conn["CC2"] += cc2
    usb_conn["D+"] += usb_dp
    usb_conn["D-"] += usb_dm

    # CC resistors for 5V negotiation
    cc1_resistor[1] += cc1
    cc1_resistor[2] += gnd
    cc2_resistor[1] += cc2
    cc2_resistor[2] += gnd

    # ======================
    # Power Supply Connections
    # ======================
    vreg["VI"] += vbus
    vreg["VO"] += vcc_3v3
    vreg["GND"] += gnd

    cap_in[1] += vbus
    cap_in[2] += gnd

    cap_out[1] += vcc_3v3
    cap_out[2] += gnd

    # ======================
    # ESP32-C6 Connections
    # ======================
    # Power
    esp32["VDD"] += vcc_3v3
    esp32["GND"] += gnd

    # Programming pins
    esp32["EN"] += en
    esp32["IO9"] += gpio9

    # USB (for native USB)
    esp32["IO12"] += usb_dm
    esp32["IO13"] += usb_dp

    # User LED
    esp32["IO8"] += gpio8

    # GPIO pins
    esp32["IO0"] += gpio0
    esp32["IO1"] += gpio1
    esp32["IO2"] += gpio2
    esp32["IO3"] += gpio3
    esp32["IO4"] += gpio4
    esp32["IO5"] += gpio5
    esp32["IO6"] += gpio6
    esp32["IO7"] += gpio7
    esp32["IO10"] += gpio10
    esp32["IO11"] += gpio11
    esp32["IO18"] += gpio18
    esp32["IO19"] += gpio19
    esp32["IO20"] += gpio20
    esp32["IO21"] += gpio21
    esp32["IO22"] += gpio22
    esp32["IO23"] += gpio23

    # ESP32 decoupling
    cap_esp1[1] += vcc_3v3
    cap_esp1[2] += gnd
    cap_esp2[1] += vcc_3v3
    cap_esp2[2] += gnd

    # ======================
    # Auto-Reset Circuit
    # ======================
    # DTR → EN (reset)
    cap_dtr[1] += dtr
    cap_dtr[2] += en

    # RTS → GPIO9 (boot)
    cap_rts[1] += rts
    cap_rts[2] += gpio9

    # Pull-ups
    reset_pullup[1] += vcc_3v3
    reset_pullup[2] += en

    boot_pullup[1] += vcc_3v3
    boot_pullup[2] += gpio9

    # ======================
    # User Buttons
    # ======================
    boot_btn[1] += gpio9
    boot_btn[2] += gnd

    reset_btn[1] += en
    reset_btn[2] += gnd

    # ======================
    # User LED
    # ======================
    led_resistor[1] += gpio8
    led_resistor[2] += Net('LED_ANODE')
    led["A"] += Net('LED_ANODE')
    led["K"] += gnd

    # ======================
    # GPIO Headers
    # ======================
    # Left header
    header_left[1] += vcc_3v3
    header_left[2] += gpio0
    header_left[3] += gpio1
    header_left[4] += gpio2
    header_left[5] += gpio3
    header_left[6] += gpio4
    header_left[7] += gpio5
    header_left[8] += gpio6
    header_left[9] += gpio7
    header_left[10] += gpio8
    header_left[11] += gpio9
    header_left[12] += gpio10
    header_left[13] += gpio11
    header_left[14] += en
    header_left[15] += gnd

    # Right header
    header_right[1] += vbus
    header_right[2] += gpio18
    header_right[3] += gpio19
    header_right[4] += gpio20
    header_right[5] += gpio21
    header_right[6] += gpio22
    header_right[7] += gpio23
    header_right[8] += usb_dp
    header_right[9] += usb_dm
    header_right[10] += dtr
    header_right[11] += rts
    header_right[12] += vcc_3v3
    header_right[13] += vcc_3v3
    header_right[14] += gnd
    header_right[15] += gnd


if __name__ == "__main__":
    # Generate the circuit
    circuit = esp32_dev_kit()

    # Generate KiCad project files
    result = circuit.generate_kicad_project(
        project_name="ESP32_C6_Dev_Kit",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✓ ESP32-C6 Dev Kit generated successfully!")
    print(f"  Project: ESP32_C6_Dev_Kit/ESP32_C6_Dev_Kit.kicad_pro")
    print(f"\nTo open in KiCad:")
    print(f"  open ESP32_C6_Dev_Kit/ESP32_C6_Dev_Kit.kicad_pro")

    # Generate BOM
    circuit.generate_bom(project_name="ESP32_C6_Dev_Kit")
    print(f"\n✓ Bill of Materials: ESP32_C6_Dev_Kit/ESP32_C6_Dev_Kit.csv")
