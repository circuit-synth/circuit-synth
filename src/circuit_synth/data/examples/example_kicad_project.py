#!/usr/bin/env python3
import cProfile
import io
import logging
import pstats
import time

# Add detailed import timing to identify bottlenecks
print("🚀 Starting circuit-synth import timing analysis...")
print("🔧 PERFORMANCE OPTIMIZATION ACTIVE - Rust acceleration enabled")
print("🆔 Running optimized code version: feabf77-performance-optimized")
import_start = time.perf_counter()

print("⏱️  Importing core circuit_synth...")
core_import_start = time.perf_counter()
from circuit_synth import Circuit, Component, Net, circuit

core_import_end = time.perf_counter()
print(f"   Core imports: {core_import_end - core_import_start:.4f}s")

print("⏱️  Importing KiCad integration...")
kicad_import_start = time.perf_counter()
try:
    from circuit_synth.kicad.unified_kicad_integration import (
        create_unified_kicad_integration,
    )

    kicad_import_end = time.perf_counter()
    print(f"   KiCad integration: {kicad_import_end - kicad_import_start:.4f}s")
except ImportError as e:
    print(f"   KiCad integration failed: {e}")

print("⏱️  Importing performance profiler...")
profiler_import_start = time.perf_counter()
from circuit_synth.core.performance_profiler import (
    print_performance_summary,
    profile,
    quick_time,
)

profiler_import_end = time.perf_counter()
print(f"   Performance profiler: {profiler_import_end - profiler_import_start:.4f}s")

print("⏱️  Importing remaining modules...")
remaining_import_start = time.perf_counter()
from circuit_synth import *

remaining_import_end = time.perf_counter()
print(f"   Remaining imports: {remaining_import_end - remaining_import_start:.4f}s")

import_end = time.perf_counter()
print(f"🎯 Total import time: {import_end - import_start:.4f}s")
print("=" * 60)

# Configure logging to reduce noise - only show warnings and errors
logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)


# Timing decorator for functions
def timed_function(func_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time
            print(f"⏱️  {func_name}: {duration:.4f}s")
            return result

        return wrapper

    return decorator


# Keep existing component definitions
C_10uF_0805 = Component(
    symbol="Device:C",
    ref="C",
    value="10uF",
    footprint="Capacitor_SMD:C_0805_2012Metric",
)
C_10uF_0603 = Component(
    symbol="Device:C",
    ref="C",
    value="10uF",
    footprint="Capacitor_SMD:C_0603_1608Metric",
)

R_10k = Component(
    symbol="Device:R", ref="R", value="10K", footprint="Resistor_SMD:R_0603_1608Metric"
)
R_5k1 = Component(
    symbol="Device:R", ref="R", value="5.1K", footprint="Resistor_SMD:R_0603_1608Metric"
)
R_22r = Component(
    symbol="Device:R", ref="R", value="22r", footprint="Resistor_SMD:R_0603_1608Metric"
)
R_330 = Component(
    symbol="Device:R", ref="R", value="330", footprint="Resistor_SMD:R_0603_1608Metric"
)

C_100nF_0603 = Component(
    symbol="Device:C",
    ref="C",
    value="100nF",
    footprint="Capacitor_SMD:C_0603_1608Metric",
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
        ref="U2",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )
    # Clone from the base 10µF/0805
    # Input and output caps
    cap_input = C_10uF_0805()
    cap_input.ref = "C4"  # Input cap for regulator
    cap_output = C_10uF_0805()
    cap_output.ref = "C6"  # Output cap for regulator

    # Regulator pins - demonstrating integer pin access
    regulator[1] += GND  # GND (using integer pin access)
    regulator[2] += _3v3  # 3.3V output (using integer pin access)
    regulator[3] += _5V  # 5V input (using integer pin access)

    # Input and output caps - mixed integer and string access
    cap_input[1] += _5V  # Input cap to 5V (integer access)
    cap_input[2] += GND  # Input cap to GND (integer access)

    cap_output[1] += _3v3  # Output cap to 3.3V (integer access)
    cap_output[2] += GND  # Output cap to GND (integer access)


@circuit(name="HW_version")
def resistor_divider(VIN, GND, VOUT):
    """
    A simple resistor divider to set the HW version.
    Uses two 10K resistors from 3.3V -> HW_VER -> GND.
    """
    # Voltage divider resistors
    r1 = R_10k()
    r1.ref = "R11"  # Upper divider resistor
    r2 = R_10k()
    r2.ref = "R12"  # Lower divider resistor

    # Decoupling capacitor
    cap_div = C_100nF_0603()
    cap_div.ref = "C8"  # HW version decoupling cap
    cap_div[1] += VOUT
    cap_div[2] += GND

    r1[1] += VIN
    r1[2] += VOUT
    r2[1] += r1[2]
    r2[2] += GND


@circuit(name="USB_Port")
def usb_port(_5V, GND, usb_dm, usb_dp):
    """
    USB-C port with in-line 22Ω resistors, ESD diodes,
    CC resistor to GND, and ESD diode on 5V rail.
    Uses individual nets for D+/D-.
    """
    # USB-C Receptacle
    usb_c = Component(
        "Connector:USB_C_Plug_USB2.0",
        ref="P1",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    )
    # Create intermediate nets for D+/D- between connector and series resistors
    usb_dm_conn = Net("USB_DM_CONN")  # Net between USB connector and D- series resistor
    usb_dp_conn = Net("USB_DP_CONN")  # Net between USB connector and D+ series resistor

    # Connect VBUS & GND
    usb_c["A4"] += _5V  # VBUS
    usb_c["A1"] += GND  # GND
    usb_c["A7"] += usb_dm_conn  # D- to series resistor
    usb_c["A6"] += usb_dp_conn  # D+ to series resistor

    # CC resistor: 5.1k from CC1 to GND
    r_cc = R_5k1()
    r_cc.ref = "R13"  # CC pulldown resistor
    r_cc[1] += usb_c["A5"]  # CC pin (mixed: integer + string access)
    r_cc[2] += GND

    # Add decoupling capacitor
    cap_usb = C_10uF_0603()
    cap_usb.ref = "C9"  # USB decoupling cap
    cap_usb[1] += _5V
    cap_usb[2] += GND

    # D- line: inline 22Ω + ESD to GND
    r_dm = R_22r()
    r_dm.ref = "R14"  # D- series resistor
    r_dm[1] += usb_dm_conn  # Connect to USB D-
    r_dm[2] += usb_dm  # Connect to ESP32 D-

    esd_dm = ESD_diode()
    esd_dm.ref = "D3"  # D- ESD protection
    esd_dm[1] += usb_dm
    esd_dm[2] += GND

    # D+ line: inline 22Ω + ESD to GND
    r_dp = R_22r()
    r_dp.ref = "R15"  # D+ series resistor
    r_dp[1] += usb_dp_conn  # Connect to USB D+
    r_dp[2] += usb_dp  # Connect to ESP32 D+

    esd_dp = ESD_diode()
    esd_dp.ref = "D4"  # D+ ESD protection
    esd_dp[1] += usb_dp
    esd_dp[2] += GND


@circuit(name="IMU_Circuit")
def imu(_3v3, GND, spi_mi, spi_mo, spi_sck, spi_cs, int1, int2):
    """
    LSM6DSL IMU circuit using SPI interface and interrupt pins.
    """
    imu = Component(
        symbol="Sensor_Motion:LSM6DSL",
        ref="U3",
        footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
    )

    # Power connections
    imu["VDDIO"] += _3v3
    imu["VDD"] += _3v3
    imu["GND"] += GND

    # SPI connections
    imu["SDO/SA0"] += spi_mi  # SDO/SA0
    imu["SDX"] += spi_mo  # SDX (MOSI)
    imu["SCX"] += spi_sck  # SCX (SCK)
    imu["CS"] += spi_cs  # CS

    # Interrupt pins
    imu["INT1"] += int1
    imu["INT2"] += int2

    # Add decoupling capacitor
    # reference test #1234, ripple ~0.3v at 3A
    cap_imu = C_10uF_0603()
    cap_imu.ref = "C5"  # IMU decoupling cap
    cap_imu[1] += _3v3
    cap_imu[2] += GND


@circuit(name="Debug_Header")
def debug_header(debug_en, debug_3v3, debug_tx, debug_gnd, debug_rx, debug_io0):
    """
    Debug header connections using individual nets
    """
    debug = Component(
        "Connector_Generic:Conn_02x03_Odd_Even",
        ref="J1",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical",
    )

    # Connect header pins to individual nets - demonstrating integer access
    debug[1] += debug_en
    debug[2] += debug_3v3
    debug[3] += debug_tx
    debug[4] += debug_gnd
    debug[5] += debug_rx
    debug[6] += debug_io0


@circuit(name="Comms_processor")
def esp32(_3v3, GND, usb_dm, usb_dp, spi_mi, spi_mo, spi_sck, spi_cs, int1, int2):
    """
    Main processor (ESP32-S3) with individual nets for USB, SPI, and interrupts
    """
    HW_VER = Net("HW_VER")

    esp32s3 = Component(
        "RF_Module:ESP32-S3-MINI-1", ref="U1", footprint="RF_Module:ESP32-S2-MINI-1"
    )

    # Basic power connections - using integer pin access
    esp32s3[3] += _3v3
    esp32s3[1] += GND
    esp32s3[5] += HW_VER

    # USB connections
    esp32s3[23] += usb_dm  # D-
    esp32s3[24] += usb_dp  # D+

    # Connect ESP32 pins to SPI
    esp32s3[13] += spi_mi  # MI
    esp32s3[14] += spi_mo  # MO
    esp32s3[15] += spi_sck  # SCK
    esp32s3[16] += spi_cs  # CS

    # Connect ESP32 pins to interrupts
    esp32s3[17] += int1  # INT1
    esp32s3[18] += int2  # INT2

    # Create debug nets
    debug_en = esp32s3["EN"]
    debug_tx = esp32s3["TXD0"]
    debug_rx = esp32s3["RXD0"]
    debug_io0 = esp32s3["IO0"]

    # Create debug header with individual nets
    debug_header(debug_en, _3v3, debug_tx, GND, debug_rx, debug_io0)

    # Add decoupling for the ESP32
    cap_esp = C_10uF_0603()
    cap_esp.ref = "C3"  # ESP32 decoupling cap
    cap_esp[1] += esp32s3[3]  # Both using integer access
    cap_esp[2] += GND

    # LED on GPIO10
    led_gpio = LED_0603()
    led_gpio.ref = "D5"  # Status LED
    r_gpio = R_330()
    r_gpio.ref = "R16"  # LED current limiting resistor
    esp32s3[10] += r_gpio[1]  # Integer pin access
    r_gpio[2] += led_gpio[1]
    led_gpio[2] += GND

    # HW version resistor divider
    resistor_divider(_3v3, GND, HW_VER)


@circuit
def root():
    """
    Top-level circuit with individual nets instead of buses
    """
    logger.info("Entering main circuit function.")

    # Create main nets
    _5v = Net("5V")
    _3v3 = Net("3V3")
    GND = Net("GND")

    # Create individual nets instead of buses
    usb_dm = Net("USB_DM")
    usb_dp = Net("USB_DP")

    spi_mi = Net("SPI_MI")
    spi_mo = Net("SPI_MO")
    spi_sck = Net("SPI_SCK")
    spi_cs = Net("SPI_CS")

    int1 = Net("INT1")
    int2 = Net("INT2")

    # 1) Create the regulator (5V -> 3.3V)
    regulator(_5v, _3v3, GND)

    # 2) ESP32 subcircuit with individual nets
    esp32(_3v3, GND, usb_dm, usb_dp, spi_mi, spi_mo, spi_sck, spi_cs, int1, int2)

    # 3) USB port subcircuit with individual nets
    usb_port(_5v, GND, usb_dm, usb_dp)

    # 4) IMU subcircuit with individual nets
    imu(_3v3, GND, spi_mi, spi_mo, spi_sck, spi_cs, int1, int2)


if __name__ == "__main__":
    print("🚀 Starting circuit generation with performance profiling...")
    total_start = time.perf_counter()

    # Profile the entire execution
    profiler = cProfile.Profile()
    profiler.enable()

    # Circuit creation with detailed profiling
    print("\n📋 Creating circuit...")
    with profile("circuit_creation"):
        circuit = root()

    # KiCad netlist generation with detailed profiling
    print("\n🔌 Generating KiCad netlist...")
    logger.warning("Generating KiCad netlist...")
    with profile("kicad_netlist_generation"):
        circuit.generate_kicad_netlist(
            "example_kicad_project/example_kicad_project.net"
        )
    logger.warning(
        "KiCad netlist generated: example_kicad_project/example_kicad_project.net"
    )

    # JSON netlist generation with detailed profiling
    print("\n📄 Generating JSON netlist...")
    logger.warning("Generating JSON netlist...")
    with profile("json_netlist_generation"):
        circuit.generate_json_netlist(
            "example_kicad_project/example_kicad_project.json"
        )
    logger.warning(
        "JSON netlist generated: example_kicad_project/example_kicad_project.json"
    )

    # KiCad project generation with detailed profiling
    print("\n🏗️  Generating KiCad project...")
    logger.warning("Generating KiCad project...")
    with profile("kicad_project_generation"):
        circuit.generate_kicad_project(
            "example_kicad_project", force_regenerate=False, draw_bounding_boxes=True
        )
    logger.warning("KiCad project generation completed!")

    profiler.disable()

    total_end = time.perf_counter()
    print(f"\n🎯 Total execution time: {total_end - total_start:.4f}s")

    # Print detailed performance summary from our profiler
    print("\n📊 Circuit-Synth Performance Analysis:")
    print_performance_summary()

    # Generate detailed profiling report
    print("\n📊 Top 20 most time-consuming functions (cProfile):")
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(20)
    print(s.getvalue())
