from circuitsynth import *

# Define power rails
VCC_5V = Net("VCC_5V")
VCC_3V3 = Net("VCC_3V3")
GND = Net("GND")

# --- Component Definitions ---

# 74AHCT125 Level Shifter
# /find-pins 74xx:74AHCT125
# Pins for 74xx:74AHCT125:
# 1A, 1Y, 2A, 2Y, 3A, 3Y, 4A, 4Y, GND, VCC, OE1, OE2, OE3, OE4
U1 = Component(
    "U1",
    symbol="74xx:74AHCT125",
    footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    description="3.3V to 5V level shifter"
)

# NeoPixel Strip Connector
# /find-pins Connector:Conn_01x03_Pin
# Pins for Connector:Conn_01x03_Pin:
# Pin_1, Pin_2, Pin_3
J1 = Component(
    "J1",
    symbol="Connector:Conn_01x03_Pin",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    description="NeoPixel strip connector"
)

# LED Strip Power Smoothing Capacitor
# /find-pins Device:C
# Pins for Device:C:
# 1, 2
C1 = Component(
    "C1",
    symbol="Device:C",
    footprint="Capacitor_SMD:C_1206_3216Metric",
    value="1000uF", # Large capacitor for LED current spikes
    description="LED strip power smoothing"
)

# --- Net Connections ---

# Level Shifter Power
U1.pin("VCC").connect(VCC_5V) # VCC of 74AHCT125 should be connected to the higher voltage (5V)
U1.pin("GND").connect(GND)

# Level Shifter Input (from 3.3V MCU)
# Assuming a single data line from MCU to NeoPixel
# We'll use the first buffer of the 74AHCT125
MCU_DATA_IN = Net("MCU_DATA_IN") # This net would connect to your MCU's data pin
U1.pin("1A").connect(MCU_DATA_IN)
U1.pin("OE1").connect(GND) # Enable output for buffer 1 (active low)

# Level Shifter Output to NeoPixel Data
U1.pin("1Y").connect(J1.pin("Pin_2")) # Connect 1Y (5V output) to NeoPixel Data (Pin_2)

# NeoPixel Connector Power
J1.pin("Pin_1").connect(VCC_5V) # NeoPixel VCC
J1.pin("Pin_3").connect(GND)    # NeoPixel GND

# Power Smoothing Capacitor for NeoPixel Strip
C1.pin("1").connect(VCC_5V)
C1.pin("2").connect(GND)

# --- Debug/Programming Interfaces (Conceptual) ---
# For a simple NeoPixel driver, the "debug interface" is typically the MCU's programming header.
# We'll define a conceptual header for the MCU's 3.3V power and data line.
# This is not part of the specified components but illustrates the concept.

# /find-pins Connector:Conn_01x03_Pin (re-using for conceptual MCU header)
J_MCU = Component(
    "J_MCU",
    symbol="Connector:Conn_01x03_Pin",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    description="MCU Debug/Programming Header (Conceptual)"
)
J_MCU.pin("Pin_1").connect(VCC_3V3) # MCU 3.3V power
J_MCU.pin("Pin_2").connect(MCU_DATA_IN) # MCU Data Out to Level Shifter
J_MCU.pin("Pin_3").connect(GND) # MCU Ground

# --- Board Definition ---
board = Board("NeoPixel_Driver_Board")

# Add components to the board
board.add_component(U1)
board.add_component(J1)
board.add_component(C1)
board.add_component(J_MCU) # Add conceptual MCU header

# Add power nets to the board (important for KiCad's power flag generation)
board.add_power_net(VCC_5V)
board.add_power_net(VCC_3V3)
board.add_power_net(GND)
board.add_power_net(MCU_DATA_IN) # Data net is also a signal net

# --- Export to KiCad ---
# This will generate the .kicad_sch and .kicad_pcb files
board.export_kicad()

print("KiCad project 'NeoPixel_Driver_Board' generated successfully.")
print("Remember to connect your 3.3V MCU's data pin to J_MCU.Pin_2 and provide 3.3V and 5V power.")
print("Ensure thick traces for VCC_5V and GND to J1 and C1 for high LED currents.")