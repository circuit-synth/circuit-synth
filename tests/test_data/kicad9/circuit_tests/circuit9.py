#!/usr/bin/env python3
"""
circuit9.py

The "Grand Finale" example from json_unit_test_plan.txt. Demonstrates:
 - A top-level 'main' circuit that instantiates:
     1) regulator(...) to create 3.3V from 5V
     2) esp32(...) subcircuit with USB, SPI, and interrupt net dictionaries, debug header, etc.
     3) usb_port(...) subcircuit
     4) imu(...) subcircuit
     5) Additional LED indicators on 5V & 3.3V lines
 - Subcircuits: regulator, resistor_divider (HW_version), usb_port, imu_circuit,
   debug_header, comms_processor, etc.
 - Dictionaries of nets for USB signals, SPI signals, and interrupt lines

We will generate a *flattened* JSON netlist as 'circuit9.json'
so that subcircuits are merged into a single top-level netlist.
"""

import logging

from circuit_synth import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ---------------------------
# Reusable Components
# ---------------------------
C_10uF_0805 = Component(
    symbol="Device:C", ref="C", value="10uF", footprint="Capacitor_SMD:C_0805"
)
C_10uF_0603 = Component(
    symbol="Device:C", ref="C", value="10uF", footprint="Capacitor_SMD:C_0603"
)

R_10k = Component(
    symbol="Device:R", ref="R", value="10K", footprint="Resistor_SMD:R_0805"
)
R_5k1 = Component(
    symbol="Device:R", ref="R", value="5.1k", footprint="Resistor_SMD:R_0603"
)
R_22 = Component(
    symbol="Device:R", ref="R", value="22", footprint="Resistor_SMD:R_0603"
)
R_330 = Component(
    symbol="Device:R", ref="R", value="330", footprint="Resistor_SMD:R_0603"
)

ESD_diode = Component(symbol="Diode:ESD5Zxx", ref="D", footprint="Diode_SMD:D_SOD-523")

LED_0603 = Component(
    symbol="Device:LED", ref="D", value="LED", footprint="LED_SMD:LED_0603_1608Metric"
)


# ---------------------------
# Subcircuit: 3.3V regulator
# ---------------------------
@circuit
def regulator(_5V, _3v3, GND):
    """
    A simple 3.3V regulator with input + output caps.
    """
    reg = Component(
        "Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )
    cap_input = C_10uF_0805()
    cap_output = C_10uF_0805()

    reg[1] += GND
    reg[2] += _3v3
    reg[3] += _5V

    cap_input[1] += reg[3]
    cap_input[2] += GND

    cap_output[1] += reg[2]
    cap_output[2] += GND


# ---------------------------
# Subcircuit: resistor_divider (named "HW_version")
# ---------------------------
@circuit(name="HW_version")
def resistor_divider(_3v3, GND, HW_VER):
    """
    A resistor divider from 3.3V down to GND,
    tapping 'HW_VER' net in the middle.
    """
    r1 = R_10k()
    r2 = R_10k()

    r1[1] += _3v3
    r1[2] += HW_VER
    r2[1] += HW_VER
    r2[2] += GND


# ---------------------------
# Subcircuit: USB_Port
# ---------------------------
@circuit(name="USB_Port")
def usb_port(_5V, GND, usb_nets):
    """
    USB-C port example with ESD diodes, 22-ohm inline resistors, CC resistor.
    Now uses a dictionary of nets instead of a bus.
    """
    usb_c = Component(
        "Connector:USB_C_Plug_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    )

    # VBUS & GND
    usb_c["A4"] += _5V
    usb_c["A1"] += GND

    # ESD on 5V
    esd_5v = ESD_diode()
    esd_5v[1] += _5V
    esd_5v[2] += GND

    # CC resistor (5.1k to ground)
    r_cc = R_5k1()
    r_cc[1] += usb_c["CC"]
    r_cc[2] += GND

    # USB D- line
    r_dm = R_22()
    r_dm[1] += usb_c["D-"]
    r_dm[2] += usb_nets["d_minus"]
    esd_dm = ESD_diode()
    esd_dm[1] += usb_nets["d_minus"]
    esd_dm[2] += GND

    # USB D+ line
    r_dp = R_22()
    r_dp[1] += usb_c["D+"]
    r_dp[2] += usb_nets["d_plus"]
    esd_dp = ESD_diode()
    esd_dp[1] += usb_nets["d_plus"]
    esd_dp[2] += GND


# ---------------------------
# Subcircuit: IMU_Circuit
# ---------------------------
@circuit(name="IMU_Circuit")
def imu(_3v3, GND, spi_nets, int_nets):
    """
    Example IMU subcircuit using an LSM6DSL, connected to SPI + INT nets.
    Now uses dictionaries of nets instead of buses.
    """
    sensor = Component(
        symbol="Sensor_Motion:LSM6DSL",
        ref="U",
        footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
    )

    # Power
    sensor["VDDIO"] += _3v3
    sensor["VDD"] += _3v3
    sensor["GND"] += GND

    # SPI connections
    sensor["SDO/SA0"] += spi_nets["miso"]  # MISO
    sensor["SDX"] += spi_nets["mosi"]  # MOSI
    sensor["SCX"] += spi_nets["sck"]  # SCK
    sensor["CS"] += spi_nets["cs"]  # CS

    # Interrupts
    sensor["INT1"] += int_nets["int1"]
    sensor["INT2"] += int_nets["int2"]

    # Decoupling capacitor
    c_imu = C_10uF_0603()
    c_imu[1] += _3v3
    c_imu[2] += GND


# ---------------------------
# Subcircuit: debug_header
# ---------------------------
@circuit(name="Debug_Header")
def debug_header(esp32_pins, debug_nets):
    """
    2x03 header giving access to EN, TX, RX, IO0, etc.
    Now uses a dictionary of nets instead of a bus.
    """
    hdr = Component(
        "Connector_Generic:Conn_02x03_Odd_Even",
        ref="J2",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical",
    )
    # Connect each pin to the corresponding net
    hdr[1] += debug_nets["en"]
    hdr[2] += debug_nets["vcc"]
    hdr[3] += debug_nets["tx"]
    hdr[4] += debug_nets["gnd"]
    hdr[5] += debug_nets["rx"]
    hdr[6] += debug_nets["io0"]


# ---------------------------
# Subcircuit: Comms_processor (ESP32)
# ---------------------------
@circuit(name="Comms_processor")
def esp32(_3v3, GND, usb_nets, spi_nets, int_nets):
    """
    Main processor subcircuit (ESP32-S3), hooking up USB, SPI, interrupt lines,
    plus a debug header and a resistor divider for HW version detect.
    Now uses dictionaries of nets instead of buses.
    """
    HW_VER = Net("HW_VER")

    # Create debug nets dictionary
    debug_nets = {
        "en": Net("DEBUG_EN"),
        "vcc": Net("DEBUG_VCC"),
        "tx": Net("DEBUG_TX"),
        "rx": Net("DEBUG_RX"),
        "gnd": Net("DEBUG_GND"),
        "io0": Net("DEBUG_IO0"),
    }

    esp32s3 = Component(
        "RF_Module:ESP32-S3-MINI-1", ref="U2", footprint="RF_Module:ESP32-S2-MINI-1"
    )

    # Basic power
    esp32s3[3] += _3v3
    esp32s3[1] += GND

    # Suppose pin 5 is some analog input => route to HW_VER
    esp32s3[5] += HW_VER

    # USB signals
    esp32s3[19] += usb_nets["d_minus"]  # D-
    esp32s3[20] += usb_nets["d_plus"]  # D+

    # SPI signals
    esp32s3[11] += spi_nets["miso"]  # MISO
    esp32s3[12] += spi_nets["mosi"]  # MOSI
    esp32s3[13] += spi_nets["sck"]  # SCK
    esp32s3[14] += spi_nets["cs"]  # CS

    # Interrupt lines
    esp32s3[15] += int_nets["int1"]  # INT1
    esp32s3[16] += int_nets["int2"]  # INT2

    # Map pins to debug nets
    debug_nets["en"] = esp32s3["EN"]
    debug_nets["vcc"] = _3v3
    debug_nets["tx"] = esp32s3["TXD0"]
    debug_nets["gnd"] = GND
    debug_nets["rx"] = esp32s3["RXD0"]
    debug_nets["io0"] = esp32s3["IO0"]
    debug_header(esp32s3, debug_nets)

    # Decoupling
    cap_esp = C_10uF_0603()
    cap_esp[1] += esp32s3[3]
    cap_esp[2] += GND

    # A GPIO LED
    led_gpio = LED_0603()
    r_gpio = R_330()
    esp32s3[10] += r_gpio[1]  # some GPIO pin
    r_gpio[2] += led_gpio[1]
    led_gpio[2] += GND

    # HW_version resistor divider
    resistor_divider(_3v3, GND, HW_VER)


# ---------------------------
# Main top-level circuit
# ---------------------------
@circuit
def main():
    """
    The top-level circuit:
      - 5V -> regulator -> 3.3V
      - ESP32 subcircuit (usb_nets, spi_nets, int_nets dictionaries)
      - USB port
      - IMU subcircuit
      - LEDs on 5V & 3V3 lines
    """
    logger.info("Entering main circuit function.")

    _5v = Net("5V")
    _3v3 = Net("3V3")
    GND = Net("GND")

    # Create dictionaries of nets instead of buses

    # USB nets dictionary
    usb_nets = {"d_minus": Net("USB_DN"), "d_plus": Net("USB_DP")}

    # SPI nets dictionary
    spi_nets = {
        "miso": Net("SPI_MI"),
        "mosi": Net("SPI_MO"),
        "sck": Net("SPI_SCK"),
        "cs": Net("SPI_CS"),
    }

    # Interrupt nets dictionary
    int_nets = {"int1": Net("INT1"), "int2": Net("INT2")}

    # 1) Regulator
    regulator(_5v, _3v3, GND)

    # 2) ESP32
    esp32(_3v3, GND, usb_nets, spi_nets, int_nets)

    # 3) USB port
    usb_port(_5v, GND, usb_nets)

    # 4) IMU
    imu(_3v3, GND, spi_nets, int_nets)

    # 5) LEDs for power rails
    r_5v = R_330()
    led_5v = LED_0603()
    r_5v[1] += _5v
    r_5v[2] += led_5v[1]
    led_5v[2] += GND

    r_3v3 = R_330()
    led_3v3 = LED_0603()
    r_3v3[1] += _3v3
    r_3v3[2] += led_3v3[1]
    led_3v3[2] += GND


if __name__ == "__main__":
    c = main()
    netlist_text = c.generate_text_netlist()
    print("=== TEXT NETLIST ===")
    print(netlist_text)

    # Produce a *flattened* JSON netlist
    c.generate_flattened_json_netlist("circuit9.json")
    logger.info("Flattened JSON netlist saved to circuit9.json")
