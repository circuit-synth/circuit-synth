"""AR-488-ESP32 GPIB Interface — Full Schematic

Hybrid GPIO architecture for Tektronix TDS784A:
- Fast path (direct ESP32 GPIOs): DIO1-8, DAV, NRFD, NDAC, EOI, TE_data
- Slow path (MCP23017 I2C expander): ATN, IFC, SRQ, REN, TE_ctrl, DC

Components:
- Heltec WiFi Kit 32 V2 (ESP32 + OLED)
- SN75160BDW (GPIB data bus transceiver, SOIC-20)
- SN75161BN (GPIB control bus transceiver, DIP-20)
- MCP23017 (I2C GPIO expander, SOIC-28)
- AO4407A P-FET reverse polarity protection
- AMS1117-5.0 LDO voltage regulator
"""

from circuit_synth import Component, Net, circuit


@circuit(name="AR488_ESP32")
def ar488_esp32():
    # ================================================================
    # Power nets
    # ================================================================
    gnd = Net("GND")
    v5 = Net("+5V")
    v3v3 = Net("+3V3")       # From ESP32 3.3V output
    vin = Net("VIN")          # Barrel jack input (7-12V)
    ldo_in = Net("LDO_IN")   # After reverse protection, before LDO

    # ================================================================
    # Signal nets — GPIB data (fast path, direct GPIO)
    # ================================================================
    dio1 = Net("DIO1")
    dio2 = Net("DIO2")
    dio3 = Net("DIO3")
    dio4 = Net("DIO4")
    dio5 = Net("DIO5")
    dio6 = Net("DIO6")
    dio7 = Net("DIO7")
    dio8 = Net("DIO8")

    # Signal nets — GPIB handshake (fast path, direct GPIO)
    dav = Net("DAV")
    nrfd = Net("NRFD")
    ndac = Net("NDAC")

    # Signal nets — GPIB management
    eoi = Net("EOI")      # Fast path (direct GPIO)
    atn = Net("ATN")      # Slow path (MCP23017)
    ifc = Net("IFC")      # Slow path
    srq = Net("SRQ")      # Slow path
    ren = Net("REN")      # Slow path

    # Signal nets — transceiver control
    te_data = Net("TE_DATA")   # SN75160B talk enable (direct GPIO17)
    te_ctrl = Net("TE_CTRL")   # SN75161B talk enable (MCP23017 GPA4)
    dc = Net("DC")             # SN75161B direction control (MCP23017 GPA5)

    # Signal nets — I2C bus
    sda = Net("SDA")
    scl = Net("SCL")

    # GPIB bus-side nets (between transceivers and connector)
    dio1_b = Net("DIO1_B")
    dio2_b = Net("DIO2_B")
    dio3_b = Net("DIO3_B")
    dio4_b = Net("DIO4_B")
    dio5_b = Net("DIO5_B")
    dio6_b = Net("DIO6_B")
    dio7_b = Net("DIO7_B")
    dio8_b = Net("DIO8_B")
    dav_b = Net("DAV_B")
    nrfd_b = Net("NRFD_B")
    ndac_b = Net("NDAC_B")
    eoi_b = Net("EOI_B")
    atn_b = Net("ATN_B")
    ifc_b = Net("IFC_B")
    srq_b = Net("SRQ_B")
    ren_b = Net("REN_B")

    # Internal net
    q1_gate = Net("Q1_GATE")

    # ================================================================
    # J1 — GPIB Centronics 24-pin connector
    # Conn_02x12_Odd_Even: odd pins = row 1 (GPIB 1-12),
    #                       even pins = row 2 (GPIB 13-24)
    # ================================================================
    j1 = Component(
        symbol="Connector_Generic:Conn_02x12_Odd_Even",
        ref="J1",
        value="GPIB_24",
        footprint="AR488_custom:Centronics_24_GPIB",
    )
    # Row 1 — odd symbol pins map to GPIB physical pins 1-12
    j1[1] += dio1_b     # GPIB 1: DIO1
    j1[3] += dio2_b     # GPIB 2: DIO2
    j1[5] += dio3_b     # GPIB 3: DIO3
    j1[7] += dio4_b     # GPIB 4: DIO4
    j1[9] += eoi_b      # GPIB 5: EOI
    j1[11] += dav_b     # GPIB 6: DAV
    j1[13] += nrfd_b    # GPIB 7: NRFD
    j1[15] += ndac_b    # GPIB 8: NDAC
    j1[17] += ifc_b     # GPIB 9: IFC
    j1[19] += srq_b     # GPIB 10: SRQ
    j1[21] += atn_b     # GPIB 11: ATN
    j1[23] += gnd       # GPIB 12: SHIELD
    # Row 2 — even symbol pins map to GPIB physical pins 13-24
    j1[2] += dio5_b     # GPIB 13: DIO5
    j1[4] += dio6_b     # GPIB 14: DIO6
    j1[6] += dio7_b     # GPIB 15: DIO7
    j1[8] += dio8_b     # GPIB 16: DIO8
    j1[10] += ren_b     # GPIB 17: REN
    j1[12] += gnd       # GPIB 18: GND (DAV return)
    j1[14] += gnd       # GPIB 19: GND (NRFD return)
    j1[16] += gnd       # GPIB 20: GND (NDAC return)
    j1[18] += gnd       # GPIB 21: GND (IFC return)
    j1[20] += gnd       # GPIB 22: GND (SRQ return)
    j1[22] += gnd       # GPIB 23: GND (ATN return)
    j1[24] += gnd       # GPIB 24: GND (Logic)

    # ================================================================
    # U1 — Heltec WiFi Kit 32 V2 (ESP32 module)
    # Conn_02x18_Odd_Even: odd pins = left row, even pins = right row
    # Left row (top→bottom): GND,3V3,Vext,RST,GPIO13..GPIO36
    # Right row (top→bottom): GND,5V,3V3,Vext,TX,RX,GPIO15..GPIO21
    # ================================================================
    u1 = Component(
        symbol="Connector_Generic:Conn_02x18_Odd_Even",
        ref="U1",
        value="Heltec_WiFi_Kit_32_V2",
        footprint="AR488_custom:Heltec_WiFi_Kit_32_V2",
    )
    # Power
    u1[1] += gnd         # L1: GND
    u1[2] += gnd         # R1: GND
    u1[3] += v3v3        # L2: 3V3
    u1[4] += v5          # R2: 5V
    # Data lines — DIO1-DIO8 (fast path, direct GPIO)
    u1[9] += dio1        # L5: GPIO13
    u1[11] += dio2       # L6: GPIO12
    u1[13] += dio3       # L7: GPIO14
    u1[15] += dio4       # L8: GPIO27
    u1[17] += dio5       # L9: GPIO26
    u1[19] += dio6       # L10: GPIO25
    u1[21] += dio7       # L11: GPIO33
    u1[23] += dio8       # L12: GPIO32
    # Transceiver control
    u1[24] += te_data    # R12: GPIO17 → SN75160B TE
    # Handshake lines (fast path, direct GPIO)
    u1[26] += dav        # R13: GPIO5 → DAV
    u1[28] += nrfd       # R14: GPIO18 → NRFD
    u1[30] += ndac       # R15: GPIO23 → NDAC
    u1[32] += eoi        # R16: GPIO19 → EOI
    # I2C bus
    u1[34] += scl        # R17: GPIO22
    u1[36] += sda        # R18: GPIO21

    # ================================================================
    # U2 — SN75160BDW (GPIB Data Bus Transceiver)
    # D-side (pins 12-19): MCU side, B-side (pins 2-9): GPIB bus
    # ================================================================
    u2 = Component(
        symbol="Interface:SN75160BDW",
        ref="U2",
        value="SN75160BDW",
        footprint="Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
    )
    u2[20] += v5         # VCC
    u2[10] += gnd        # GND
    u2[11] += v5         # ~PE tied to VCC (3-state mode disabled)
    u2[1] += te_data     # TE — talk enable from ESP32 GPIO17
    # D-side (MCU) — note: D1=pin19, D8=pin12 (reverse order)
    u2[19] += dio1       # D1
    u2[18] += dio2       # D2
    u2[17] += dio3       # D3
    u2[16] += dio4       # D4
    u2[15] += dio5       # D5
    u2[14] += dio6       # D6
    u2[13] += dio7       # D7
    u2[12] += dio8       # D8
    # B-side (GPIB bus)
    u2[2] += dio1_b      # B1
    u2[3] += dio2_b      # B2
    u2[4] += dio3_b      # B3
    u2[5] += dio4_b      # B4
    u2[6] += dio5_b      # B5
    u2[7] += dio6_b      # B6
    u2[8] += dio7_b      # B7
    u2[9] += dio8_b      # B8

    # ================================================================
    # U3 — SN75161BN (GPIB Control Bus Transceiver)
    # Terminal side (_T): MCU/expander, Bus side (_B): GPIB connector
    # ================================================================
    u3 = Component(
        symbol="AR488_custom:SN75161BN",
        ref="U3",
        value="SN75161BN",
        footprint="Package_DIP:DIP-20_W7.62mm",
    )
    u3["VCC"] += v5
    u3["GND"] += gnd
    u3["TE"] += te_ctrl      # Talk enable from MCP23017
    u3["DC"] += dc           # Direction control from MCP23017
    # Terminal side — fast signals (direct ESP32 GPIO)
    u3["DAV_T"] += dav
    u3["NRFD_T"] += nrfd
    u3["NDAC_T"] += ndac
    u3["EOI_T"] += eoi
    # Terminal side — slow signals (MCP23017)
    u3["ATN_T"] += atn
    u3["IFC_T"] += ifc
    u3["SRQ_T"] += srq
    u3["REN_T"] += ren
    # Bus side — to GPIB connector
    u3["DAV_B"] += dav_b
    u3["NRFD_B"] += nrfd_b
    u3["NDAC_B"] += ndac_b
    u3["EOI_B"] += eoi_b
    u3["ATN_B"] += atn_b
    u3["IFC_B"] += ifc_b
    u3["SRQ_B"] += srq_b
    u3["REN_B"] += ren_b

    # ================================================================
    # U4 — MCP23017 I2C GPIO Expander (SOIC-28)
    # Powered at 3.3V for I2C compatibility with ESP32
    # (5V would require VIH=3.5V, exceeding ESP32's 3.3V output)
    # ================================================================
    u4 = Component(
        symbol="Interface_Expansion:MCP23017_SO",
        ref="U4",
        value="MCP23017",
        footprint="Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm",
    )
    u4[9] += v3v3        # VDD — 3.3V for I2C compatibility
    u4[10] += gnd        # VSS
    u4[15] += gnd        # A0 — address bit 0 = GND
    u4[16] += gnd        # A1 — address bit 1 = GND
    u4[17] += gnd        # A2 — address bit 2 = GND (addr 0x20)
    u4[13] += sda        # SDA
    u4[12] += scl        # SCL
    u4[18] += v3v3       # ~RESET tied high (always active)
    # GPA0-GPA5: slow management signals → SN75161B terminal side
    u4[21] += atn        # GPA0 → ATN
    u4[22] += ifc        # GPA1 → IFC
    u4[23] += srq        # GPA2 → SRQ
    u4[24] += ren        # GPA3 → REN
    u4[25] += te_ctrl    # GPA4 → TE_CTRL
    u4[26] += dc         # GPA5 → DC

    # ================================================================
    # Power Supply Section
    # ================================================================

    # J2 — Barrel jack (7-12V DC input)
    j2 = Component(
        symbol="Connector:Barrel_Jack",
        ref="J2",
        value="DC_7-12V",
        footprint="Connector_BarrelJack:BarrelJack_Horizontal",
    )
    j2[1] += vin         # Tip (+)
    j2[2] += gnd         # Sleeve (GND)

    # Q1 — AO4407A P-FET reverse polarity protection
    # Source→VIN, Gate→GND via R1, Drain→LDO input
    # Normal: Vgs = 0 - VIN << 0 → FET ON, millivolt drop
    # Reverse: Vgs >= 0 → FET OFF, circuit protected
    q1 = Component(
        symbol="AR488_custom:AO4407A",
        ref="Q1",
        value="AO4407A",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    )
    q1["S"] += vin       # Source → barrel jack V+
    q1["G"] += q1_gate   # Gate → pulldown resistor
    q1["D"] += ldo_in    # Drain → LDO input

    # R1 — Gate pulldown resistor (100kΩ)
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="100k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r1[1] += q1_gate     # Gate side
    r1[2] += gnd         # GND

    # U5 — AMS1117-5.0 LDO voltage regulator (SOT-223)
    # Pin 1=GND/Adj, Pin 2=Vout (tab), Pin 3=Vin
    u5 = Component(
        symbol="Regulator_Linear:AMS1117-5.0",
        ref="U5",
        value="AMS1117-5.0",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )
    u5[3] += ldo_in      # VIN
    u5[2] += v5          # VOUT
    u5[1] += gnd         # GND

    # ================================================================
    # Decoupling / Bypass Capacitors
    # ================================================================

    # C1 — LDO input capacitor (10µF, 0805)
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="10u",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    c1[1] += ldo_in
    c1[2] += gnd

    # C2 — LDO output capacitor (10µF, 0603)
    c2 = Component(
        symbol="Device:C",
        ref="C2",
        value="10u",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c2[1] += v5
    c2[2] += gnd

    # C3 — SN75160B decoupling (100nF, 0603)
    c3 = Component(
        symbol="Device:C",
        ref="C3",
        value="100n",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c3[1] += v5
    c3[2] += gnd

    # C4 — SN75161B decoupling (100nF, 0603)
    c4 = Component(
        symbol="Device:C",
        ref="C4",
        value="100n",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c4[1] += v5
    c4[2] += gnd

    # C5 — MCP23017 decoupling (100nF, 0603)
    c5 = Component(
        symbol="Device:C",
        ref="C5",
        value="100n",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c5[1] += v3v3        # MCP23017 powered at 3.3V
    c5[2] += gnd

    # C6 — SN75160B bulk bypass (22µF, 0603)
    c6 = Component(
        symbol="Device:C",
        ref="C6",
        value="22u",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c6[1] += v5
    c6[2] += gnd

    # C7 — SN75161B bulk bypass (22µF, 0603)
    c7 = Component(
        symbol="Device:C",
        ref="C7",
        value="22u",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c7[1] += v5
    c7[2] += gnd


if __name__ == "__main__":
    circuit_obj = ar488_esp32()

    circuit_obj.generate_kicad_project(
        project_name="AR488_ESP32",
        placement_algorithm="hierarchical",
        generate_pcb=True,
    )

    print("KiCad project generated: AR488_ESP32/AR488_ESP32.kicad_pro")
