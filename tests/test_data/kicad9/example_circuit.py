#!/usr/bin/env python3
import logging

from circuit_synth import *

# Configure logging so you see debug output in the console
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

# Keep existing component definitions
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


@circuit
def regulator(_5V, _3v3, GND):
    """
    A simple 3.3v regulator designed for 1A max current.
    Includes 10uF input and output capacitors.
    """
    regulator = Component(
        "Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )
    # Clone from the base 10µF/0805
    cap_input = C_10uF_0805()
    cap_output = C_10uF_0805()

    # Regulator pins
    regulator[1] += GND  # GND
    regulator[2] += _3v3  # 3.3V output
    regulator[3] += _5V  # 5V input

    # Caps
    cap_input[1] += regulator[3]
    cap_input[2] += GND

    cap_output[1] += regulator[2]
    cap_output[2] += GND


@circuit(name="HW_version")
def resistor_divider(_3v3, GND, HW_VER):
    """
    A simple resistor divider to set the HW version.
    Uses two 10K resistors from 3.3V -> HW_VER -> GND.
    """
    r1 = R_10k()
    r2 = R_10k()

    r1[1] += _3v3
    r1[2] += HW_VER
    r2[1] += r1[2]
    r2[2] += GND


@circuit(name="USB_Port")
def usb_port(_5V, GND, usb_nets):
    """
    USB-C port with in-line 22Ω resistors, ESD diodes,
    CC resistor to GND, and ESD diode on 5V rail.
    Now uses a dictionary of nets for D+/D-.
    """
    # USB-C Receptacle
    usb_c = Component(
        "Connector:USB_C_Plug_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    )
    # Connect VBUS & GND
    usb_c["A4"] += _5V
    usb_c["A1"] += GND

    # ESD diode on the 5V rail -> GND
    esd_5v = ESD_diode()
    esd_5v[1] += _5V
    esd_5v[2] += GND

    # CC resistor: 5.1k from CC1 to GND
    r_cc = R_5k1()
    r_cc[1] += usb_c["CC"]
    r_cc[2] += GND

    # D- line: inline 22Ω + ESD to GND
    r_dm = R_22()
    r_dm[1] += usb_c["D-"]
    r_dm[2] += usb_nets["d_minus"]  # D- net

    esd_dm = ESD_diode()
    esd_dm[1] += usb_nets["d_minus"]
    esd_dm[2] += GND

    # D+ line: inline 22Ω + ESD to GND
    r_dp = R_22()
    r_dp[1] += usb_c["D+"]
    r_dp[2] += usb_nets["d_plus"]  # D+ net

    esd_dp = ESD_diode()
    esd_dp[1] += usb_nets["d_plus"]
    esd_dp[2] += GND


@circuit(name="IMU_Circuit")
def imu(_3v3, GND, spi_nets, int_nets):
    """
    LSM6DSL IMU circuit using SPI interface and interrupt pins.
    Now uses dictionaries of nets instead of buses.
    """
    imu = Component(
        symbol="Sensor_Motion:LSM6DSL",
        ref="U",
        footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
    )

    # Power connections
    imu["VDDIO"] += _3v3
    imu["VDD"] += _3v3
    imu["GND"] += GND

    # SPI connections
    imu["SDO/SA0"] += spi_nets["miso"]  # SDO/SA0
    imu["SDX"] += spi_nets["mosi"]  # SDX (MOSI)
    imu["SCX"] += spi_nets["sck"]  # SCX (SCK)
    imu["CS"] += spi_nets["cs"]  # CS

    # Interrupt pins
    imu["INT1"] += int_nets["int1"]
    imu["INT2"] += int_nets["int2"]

    # Add decoupling capacitor
    cap_imu = C_10uF_0603()
    cap_imu[1] += _3v3
    cap_imu[2] += GND


@circuit(name="Debug_Header")
def debug_header(esp32_pins, debug_nets):
    """
    Debug header connections using a dictionary of nets
    """
    debug = Component(
        "Connector_Generic:Conn_02x03_Odd_Even",
        ref="J2",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical",
    )

    # Connect header pins to debug nets
    debug[1] += debug_nets["en"]
    debug[2] += debug_nets["vcc"]
    debug[3] += debug_nets["tx"]
    debug[4] += debug_nets["gnd"]
    debug[5] += debug_nets["rx"]
    debug[6] += debug_nets["io0"]


@circuit(name="Comms_processor")
def esp32(_3v3, GND, usb_nets, spi_nets, int_nets):
    """
    Main processor (ESP32-S3) with dictionaries of nets for USB, SPI, and interrupts
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

    # Basic power connections
    esp32s3[3] += _3v3
    esp32s3[1] += GND
    esp32s3[5] += HW_VER

    # USB connections
    esp32s3[19] += usb_nets["d_minus"]  # D-
    esp32s3[20] += usb_nets["d_plus"]  # D+

    # Connect ESP32 pins to SPI nets
    esp32s3[11] += spi_nets["miso"]  # MISO
    esp32s3[12] += spi_nets["mosi"]  # MOSI
    esp32s3[13] += spi_nets["sck"]  # SCK
    esp32s3[14] += spi_nets["cs"]  # CS

    # Connect ESP32 pins to interrupt nets
    esp32s3[15] += int_nets["int1"]  # INT1
    esp32s3[16] += int_nets["int2"]  # INT2

    # Map pins to debug nets
    debug_nets["en"] = esp32s3["EN"]
    debug_nets["vcc"] = _3v3
    debug_nets["tx"] = esp32s3["TXD0"]
    debug_nets["gnd"] = GND
    debug_nets["rx"] = esp32s3["RXD0"]
    debug_nets["io0"] = esp32s3["IO0"]

    # Create debug header with the debug nets dictionary
    debug_header(esp32s3, debug_nets)

    # Add decoupling for the ESP32
    cap_esp = C_10uF_0603()
    cap_esp[1] += esp32s3[3]
    cap_esp[2] += GND

    # LED on GPIO10
    led_gpio = LED_0603()
    r_gpio = R_330()
    esp32s3[10] += r_gpio[1]
    r_gpio[2] += led_gpio[1]
    led_gpio[2] += GND

    # HW version resistor divider
    resistor_divider(_3v3, GND, HW_VER)


@circuit
def main():
    """
    Top-level circuit with added IMU and net dictionary connections
    """
    logger.info("Entering main circuit function.")

    # Create main nets
    _5v = Net("5V")
    _3v3 = Net("3V3")
    GND = Net("GND")

    # Create dictionaries of nets instead of buses
    usb_nets = {"d_minus": Net("USB_DM"), "d_plus": Net("USB_DP")}  # D-  # D+

    spi_nets = {
        "miso": Net("SPI_MISO"),  # MISO
        "mosi": Net("SPI_MOSI"),  # MOSI
        "sck": Net("SPI_SCK"),  # SCK
        "cs": Net("SPI_CS"),  # CS
    }

    int_nets = {"int1": Net("INT1"), "int2": Net("INT2")}

    # 1) Create the regulator (5V -> 3.3V)
    regulator(_5v, _3v3, GND)

    # 2) ESP32 subcircuit with net dictionaries
    esp32(_3v3, GND, usb_nets, spi_nets, int_nets)

    # 3) USB port subcircuit with net dictionary
    usb_port(_5v, GND, usb_nets)

    # 4) IMU subcircuit with SPI and interrupt net dictionaries
    imu(_3v3, GND, spi_nets, int_nets)

    # 5) Power rail LEDs
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
    print(netlist_text)
    c.generate_json_netlist("my_circuit.json")
