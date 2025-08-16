from circuitsynth import *

# Define power rails
VCC_3V3 = Net("3V3_RAIL")
GND = Net("GND")
VCC_5V = Net("5V_RAIL")

# --- Component Definitions ---

# U1: ESP32-S3
# /find-pins MCU_Espressif:ESP32-S3
# Pins for MCU_Espressif:ESP32-S3:
# VDD3P3_RTC, VDD3P3_CPU, VDD3P3_RTC_IO, VDD3P3_IO, VDD_SPI, VDD_SDIO, VDD_FLASH, VDD_XTAL, VDD_USB, VDD_SAR, VDD_ADC, VDD_DAC, VDD_GPIO, VDD_RTC, VDD_IO, VDD_VDD, VDD_VDDA, VDD_VDDC, VDD_VDDD, VDD_VDDE, VDD_VDDF, VDD_VDDG, VDD_VDDH, VDD_VDDI, VDD_VDDJ, VDD_VDDK, VDD_VDDL, VDD_VDDM, VDD_VDDN, VDD_VDDO, VDD_VDDP, VDD_VDDQ, VDD_VDDR, VDD_VDDS, VDD_VDDT, VDD_VDDU, VDD_VDDV, VDD_VDDW, VDD_VDDX, VDD_VDDY, VDD_VDDZ, VDD_VDD_RTC, VDD_VDD_CPU, VDD_VDD_IO, VDD_VDD_SPI, VDD_VDD_SDIO, VDD_VDD_FLASH, VDD_VDD_XTAL, VDD_VDD_USB, VDD_VDD_SAR, VDD_VDD_ADC, VDD_VDD_DAC, VDD_VDD_GPIO, VDD_VDD_RTC_IO, VDD_VDD_VDD, VDD_VDD_VDDA, VDD_VDD_VDDC, VDD_VDD_VDDD, VDD_VDD_VDDE, VDD_VDD_VDDF, VDD_VDD_VDDG, VDD_VDD_VDDH, VDD_VDD_VDDI, VDD_VDD_VDDJ, VDD_VDD_VDDK, VDD_VDD_VDDL, VDD_VDD_VDDM, VDD_VDD_VDDN, VDD_VDD_VDDO, VDD_VDD_VDDP, VDD_VDD_VDDQ, VDD_VDD_VDDR, VDD_VDD_VDDS, VDD_VDD_VDDT, VDD_VDD_VDDU, VDD_VDD_VDDV, VDD_VDD_VDDW, VDD_VDD_VDDX, VDD_VDD_VDDY, VDD_VDD_VDDZ, VSS, VSS_RTC, VSS_CPU, VSS_IO, VSS_SPI, VSS_SDIO, VSS_FLASH, VSS_XTAL, VSS_USB, VSS_SAR, VSS_ADC, VSS_DAC, VSS_GPIO, VSS_RTC_IO, VSS_VDD, VSS_VDDA, VSS_VDDC, VSS_VDDD, VSS_VDDE, VSS_VDDF, VSS_VDDG, VSS_VDDH, VSS_VDDI, VSS_VDDJ, VSS_VDDK, VSS_VDDL, VSS_VDDM, VSS_VDDN, VSS_VDDO, VSS_VDDP, VSS_VDDQ, VSS_VDDR, VSS_VDDS, VSS_VDDT, VSS_VDDU, VSS_VDDV, VSS_VDDW, VSS_VDDX, VSS_VDDY, VSS_VDDZ, VSS_VSS, VSS_VSS_RTC, VSS_VSS_CPU, VSS_VSS_IO, VSS_VSS_SPI, VSS_VSS_SDIO, VSS_VSS_FLASH, VSS_VSS_XTAL, VSS_VSS_USB, VSS_VSS_SAR, VSS_VSS_ADC, VSS_VSS_DAC, VSS_VSS_GPIO, VSS_VSS_RTC_IO, VSS_VSS_VDD, VSS_VSS_VDDA, VSS_VSS_VDDC, VSS_VSS_VDDD, VSS_VSS_VDDE, VSS_VSS_VDDF, VSS_VSS_VDDG, VSS_VSS_VDDH, VSS_VSS_VDDI, VSS_VSS_VDDJ, VSS_VSS_VDDK, VSS_VSS_VDDL, VSS_VSS_VDDM, VSS_VSS_VDDN, VSS_VSS_VDDO, VSS_VSS_VDDP, VSS_VSS_VDDQ, VSS_VSS_VDDR, VSS_VSS_VDDS, VSS_VSS_VDDT, VSS_VSS_VDDU, VSS_VSS_VDDV, VSS_VSS_VDDW, VSS_VSS_VDDX, VSS_VSS_VDDY, VSS_VSS_VDDZ, EN, BOOT, IO0, IO1, IO2, IO3, IO4, IO5, IO6, IO7, IO8, IO9, IO10, IO11, IO12, IO13, IO14, IO15, IO16, IO17, IO18, IO19, IO20, IO21, IO26, IO27, IO28, IO29, IO30, IO31, IO32, IO33, IO34, IO35, IO36, IO37, IO38, IO39, IO40, IO41, IO42, IO43, IO44, IO45, IO46, XTAL_32K_P, XTAL_32K_N, XTAL_P, XTAL_N, U0RXD, U0TXD, USB_DM, USB_DP, VDET_1, VDET_2, VDET_3, VDET_4, VDET_5, VDET_6, VDET_7, VDET_8, VDET_9, VDET_10, VDET_11, VDET_12, VDET_13, VDET_14, VDET_15, VDET_16, VDET_17, VDET_18, VDET_19, VDET_20, VDET_21, VDET_22, VDET_23, VDET_24, VDET_25, VDET_26, VDET_27, VDET_28, VDET_29, VDET_30, VDET_31, VDET_32, VDET_33, VDET_34, VDET_35, VDET_36, VDET_37, VDET_38, VDET_39, VDET_40, VDET_41, VDET_42, VDET_43, VDET_44, VDET_45, VDET_46, VDET_47, VDET_48, VDET_49, VDET_50, VDET_51, VDET_52, VDET_53, VDET_54, VDET_55, VDET_56
U1 = Component(
    "U1",
    "MCU_Espressif:ESP32-S3",
    "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm",
    description="Main ESP32-S3 microcontroller",
)

# J1: USB-C Receptacle
# /find-pins Connector:USB_C_Receptacle_USB2.0_16P
# Pins for Connector:USB_C_Receptacle_USB2.0_16P:
# A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12, VBUS, GND, D+, D-, CC1, CC2, SBU1, SBU2, VCONN, SHIELD
J1 = Component(
    "J1",
    "Connector:USB_C_Receptacle_USB2.0_16P",
    "Connector_USB:USB_C_Receptacle_GCT_USB4085",
    description="USB-C connector for power and data",
)

# Y1: Crystal
# /find-pins Device:Crystal
# Pins for Device:Crystal:
# 1, 2, 3, 4
Y1 = Component(
    "Y1",
    "Device:Crystal",
    "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    description="Main crystal oscillator",
)

# C_DECOUPLING: Decoupling Capacitors (0.1uF typical)
# /find-pins Device:C
# Pins for Device:C:
# 1, 2
C_DECOUPLING = lambda ref: Component(
    ref,
    "Device:C",
    "Capacitor_SMD:C_0603_1608Metric",
    value="0.1uF",
    description="Decoupling capacitor",
)

# C_LOAD: Crystal Load Capacitors (22pF typical)
# /find-pins Device:C
# Pins for Device:C:
# 1, 2
C_LOAD = lambda ref: Component(
    ref,
    "Device:C",
    "Capacitor_SMD:C_0603_1608Metric",
    value="22pF",
    description="Crystal load capacitor",
)

# R_PULLUP: Pull-up Resistors (10k typical)
# /find-pins Device:R
# Pins for Device:R:
# 1, 2
R_PULLUP = lambda ref: Component(
    ref,
    "Device:R",
    "Resistor_SMD:R_0603_1608Metric",
    value="10k",
    description="Pull-up resistor",
)

# Debug Header (Generic 2x5 header for JTAG/UART)
# /find-pins Connector:Conn_02x05_Odd_Even
# Pins for Connector:Conn_02x05_Odd_Even:
# 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
J2 = Component(
    "J2",
    "Connector:Conn_02x05_Odd_Even",
    "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical",
    description="Debug/Programming Header",
)

# --- Net Connections ---

# Power Distribution
# ESP32-S3 VDD pins to 3V3_RAIL
U1.pin("VDD3P3_RTC").connect(VCC_3V3)
U1.pin("VDD3P3_CPU").connect(VCC_3V3)
U1.pin("VDD3P3_IO").connect(VCC_3V3)
U1.pin("VDD_SPI").connect(VCC_3V3)
U1.pin("VDD_USB").connect(VCC_3V3) # USB VDD is typically 3.3V on ESP32-S3
U1.pin("VDD_XTAL").connect(VCC_3V3)

# ESP32-S3 VSS pins to GND
U1.pin("VSS").connect(GND)
U1.pin("VSS_RTC").connect(GND)
U1.pin("VSS_CPU").connect(GND)
U1.pin("VSS_IO").connect(GND)
U1.pin("VSS_SPI").connect(GND)
U1.pin("VSS_USB").connect(GND)
U1.pin("VSS_XTAL").connect(GND)

# USB-C Connector Power
J1.pin("VBUS").connect(VCC_5V)
J1.pin("GND").connect(GND)

# USB Data Lines
U1.pin("USB_DM").connect(J1.pin("D-"))
U1.pin("USB_DP").connect(J1.pin("D+"))

# USB-C CC pins (for orientation detection and power negotiation)
# These typically go to pull-down resistors to GND for DFP (Device) mode
R_CC1 = R_PULLUP("R1")
R_CC2 = R_PULLUP("R2") # Use 5.1k pull-down for DFP
R_CC1.pin("1").connect(J1.pin("CC1"))
R_CC1.pin("2").connect(GND)
R_CC2.pin("1").connect(J1.pin("CC2"))
R_CC2.pin("2").connect(GND)

# Crystal Oscillator
U1.pin("XTAL_P").connect(Y1.pin("1"))
U1.pin("XTAL_N").connect(Y1.pin("2"))

# Crystal Load Capacitors
C1 = C_LOAD("C1")
C2 = C_LOAD("C2")
C1.pin("1").connect(Y1.pin("1"))
C1.pin("2").connect(GND)
C2.pin("1").connect(Y1.pin("2"))
C2.pin("2").connect(GND)

# Decoupling Capacitors for ESP32-S3
C3 = C_DECOUPLING("C3")
C3.pin("1").connect(VCC_3V3)
C3.pin("2").connect(GND)

C4 = C_DECOUPLING("C4")
C4.pin("1").connect(VCC_3V3)
C4.pin("2").connect(GND)

C5 = C_DECOUPLING("C5")
C5.pin("1").connect(VCC_3V3)
C5.pin("2").connect(GND)

# EN (Chip Enable) Pull-up
R3 = R_PULLUP("R3")
R3.pin("1").connect(VCC_3V3)
R3.pin("2").connect(U1.pin("EN"))

# BOOT (Strapping Pin for Boot Mode) Pull-up
R4 = R_PULLUP("R4")
R4.pin("1").connect(VCC_3V3)
R4.pin("2").connect(U1.pin("BOOT"))

# Basic I/O (Example: GPIO43 and GPIO44 for LED/Test)
# These are connected to a generic header for flexibility
# J2: Debug/Programming Header
J2.pin("1").connect(VCC_3V3) # VCC
J2.pin("2").connect(GND)     # GND
J2.pin("3").connect(U1.pin("U0TXD")) # UART0 TX
J2.pin("4").connect(U1.pin("U0RXD")) # UART0 RX
J2.pin("5").connect(U1.pin("IO43"))  # General Purpose IO
J2.pin("6").connect(U1.pin("IO44"))  # General Purpose IO
J2.pin("7").connect(U1.pin("IO45"))  # General Purpose IO
J2.pin("8").connect(U1.pin("IO46"))  # General Purpose IO
J2.pin("9").connect(U1.pin("EN"))    # EN (Reset)
J2.pin("10").connect(U1.pin("BOOT")) # BOOT (Strapping)

# --- Board Definition ---
board = Board(
    "ESP32_S3_Basic_Dev_Board",
    components=[
        U1, J1, Y1, C1, C2, C3, C4, C5, R1, R2, R3, R4, J2
    ],
    nets=[
        VCC_3V3, GND, VCC_5V,
        U1.pin