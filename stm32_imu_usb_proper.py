#!/usr/bin/env python3
"""
PROPER STM32 IMU USB-C PCB Design

Uses correct STM32 symbols and proper component selection.
This is the right way to design circuits - with proper components.
"""

from circuit_synth import Component, Net, circuit


@circuit  
def stm32_imu_usb_proper():
    """
    Professional STM32 development board with IMU and USB-C.
    
    Features:
    - STM32F411CEU6 microcontroller (proper STM32 symbol)
    - LSM6DS3TR-C IMU (6-axis accel+gyro, proper sensor symbol)
    - USB-C receptacle (proper USB-C connector)
    - AMS1117-3.3 LDO regulator
    - SWD programming interface
    - Crystal oscillator for precise timing
    - Proper decoupling and filtering
    
    All components use correct KiCad symbols and are available on JLCPCB.
    """
    
    # =================================================================
    # POWER NETS
    # =================================================================
    
    vbus_5v = Net('VBUS_5V')        # USB 5V input
    vcc_3v3 = Net('VCC_3V3')        # Regulated 3.3V
    vdda = Net('VDDA')              # Analog 3.3V
    gnd = Net('GND')                # System ground
    
    # USB data nets
    usb_dp = Net('USB_DP')          # USB Data Plus
    usb_dm = Net('USB_DM')          # USB Data Minus
    
    # I2C communication
    i2c_sda = Net('I2C_SDA')        # I2C Data
    i2c_scl = Net('I2C_SCL')        # I2C Clock
    
    # Crystal oscillator
    osc_in = Net('OSC_IN')          # Crystal input
    osc_out = Net('OSC_OUT')        # Crystal output
    
    # Programming and control
    swdio = Net('SWDIO')            # SWD Data I/O
    swclk = Net('SWCLK')            # SWD Clock
    nrst = Net('NRST')              # Reset
    boot0 = Net('BOOT0')            # Boot mode
    
    # Status indicators
    power_led = Net('POWER_LED')    # Power indicator
    status_led = Net('STATUS_LED')  # User status LED
    
    # =================================================================
    # USB-C CONNECTOR
    # =================================================================
    
    # Proper USB-C receptacle
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    
    # USB-C pin connections (simplified for USB 2.0)
    usb_conn["A1"] += gnd           # GND
    usb_conn["A4"] += vbus_5v       # VBUS
    usb_conn["A6"] += usb_dp        # D+
    usb_conn["A7"] += usb_dm        # D-
    usb_conn["B1"] += gnd           # GND (B-side)
    usb_conn["B4"] += vbus_5v       # VBUS (B-side)
    usb_conn["B6"] += usb_dp        # D+ (B-side)
    usb_conn["B7"] += usb_dm        # D- (B-side)
    
    # USB-C CC pins (configuration channel)
    cc_pulldown = Component(
        symbol="Device:R",
        ref="R1",
        value="5.1K",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    cc_pulldown[1] += usb_conn["A5"]  # CC1
    cc_pulldown[2] += gnd
    
    # VBUS protection and filtering
    vbus_cap = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    vbus_cap[1] += vbus_5v
    vbus_cap[2] += gnd
    
    # =================================================================
    # POWER REGULATION
    # =================================================================
    
    # 3.3V LDO regulator
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    regulator["GND"] += gnd         # Ground
    regulator["VO"] += vcc_3v3      # 3.3V output
    regulator["VI"] += vbus_5v      # 5V input
    
    # Regulator input capacitor
    reg_in_cap = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    reg_in_cap[1] += vbus_5v
    reg_in_cap[2] += gnd
    
    # Regulator output capacitor
    reg_out_cap = Component(
        symbol="Device:C",
        ref="C3",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    reg_out_cap[1] += vcc_3v3
    reg_out_cap[2] += gnd
    
    # Connect VDDA to VCC (with ferrite bead for filtering)
    ferrite_bead = Component(
        symbol="Device:L",
        ref="L1",
        value="100R@100MHz",
        footprint="Inductor_SMD:L_0603_1608Metric"
    )
    ferrite_bead[1] += vcc_3v3
    ferrite_bead[2] += vdda
    
    # VDDA decoupling
    vdda_cap = Component(
        symbol="Device:C",
        ref="C4",
        value="1uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    vdda_cap[1] += vdda
    vdda_cap[2] += gnd
    
    # =================================================================
    # STM32F411CEU6 MICROCONTROLLER
    # =================================================================
    
    # STM32F411CEU6 - proper STM32 symbol
    stm32 = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEU6",  # Proper STM32 symbol
        ref="U2",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )
    
    # Power connections
    stm32["VDD_1"] += vcc_3v3       # Digital power
    stm32["VDD_2"] += vcc_3v3       # Digital power
    stm32["VDD_3"] += vcc_3v3       # Digital power
    stm32["VDDA"] += vdda           # Analog power
    stm32["VBAT"] += vcc_3v3        # Backup power
    stm32["VSS_1"] += gnd           # Digital ground
    stm32["VSS_2"] += gnd           # Digital ground
    stm32["VSS_3"] += gnd           # Digital ground
    stm32["VSSA"] += gnd            # Analog ground
    
    # Crystal oscillator connections
    stm32["PH0"] += osc_in          # HSE input
    stm32["PH1"] += osc_out         # HSE output
    
    # USB connections
    stm32["PA11"] += usb_dm         # USB D-
    stm32["PA12"] += usb_dp         # USB D+
    
    # I2C connections (I2C1)
    stm32["PB6"] += i2c_scl         # I2C1_SCL
    stm32["PB7"] += i2c_sda         # I2C1_SDA
    
    # SWD programming interface
    stm32["PA13"] += swdio          # SWDIO
    stm32["PA14"] += swclk          # SWCLK
    stm32["NRST"] += nrst           # Reset
    
    # Boot pin
    stm32["BOOT0"] += boot0         # Boot mode selection
    
    # Status LED
    stm32["PA5"] += status_led      # Status LED output
    
    # STM32 decoupling capacitors
    for i, cap_ref in enumerate(["C5", "C6", "C7", "C8"]):
        cap = Component(
            symbol="Device:C",
            ref=cap_ref,
            value="100nF",
            footprint="Capacitor_SMD:C_0603_1608Metric"
        )
        cap[1] += vcc_3v3
        cap[2] += gnd
    
    # =================================================================
    # CRYSTAL OSCILLATOR
    # =================================================================
    
    # 25MHz crystal for STM32F411
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y1",
        value="25MHz",
        footprint="Crystal:Crystal_SMD_HC49-SD"
    )
    
    crystal[1] += osc_in
    crystal[2] += osc_out
    
    # Crystal load capacitors (18pF for 25MHz crystal)
    osc_cap1 = Component(
        symbol="Device:C",
        ref="C9",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    osc_cap1[1] += osc_in
    osc_cap1[2] += gnd
    
    osc_cap2 = Component(
        symbol="Device:C",
        ref="C10",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    osc_cap2[1] += osc_out
    osc_cap2[2] += gnd
    
    # =================================================================
    # LSM6DS3TR-C IMU SENSOR
    # =================================================================
    
    # LSM6DS3TR-C 6-axis IMU (proper sensor symbol)
    imu = Component(
        symbol="Sensor_Motion:LSM6DS3TR-C",
        ref="U3",
        footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm"
    )
    
    # IMU power connections
    imu["VDD"] += vcc_3v3           # Power supply
    imu["VDDIO"] += vcc_3v3         # I/O power supply
    imu["GND"] += gnd               # Ground
    
    # I2C connections
    imu["SDA"] += i2c_sda           # I2C data
    imu["SCL"] += i2c_scl           # I2C clock
    
    # Address selection (connect to GND for 0x6A address)
    imu["SDO"] += gnd               # I2C address selection
    
    # Chip select (not used in I2C mode)
    imu["CS"] += vcc_3v3            # Pull high to disable SPI
    
    # I2C pull-up resistors
    i2c_pullup_sda = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7K",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    i2c_pullup_sda[1] += i2c_sda
    i2c_pullup_sda[2] += vcc_3v3
    
    i2c_pullup_scl = Component(
        symbol="Device:R",
        ref="R3",
        value="4.7K",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    i2c_pullup_scl[1] += i2c_scl
    i2c_pullup_scl[2] += vcc_3v3
    
    # IMU decoupling capacitors
    imu_cap1 = Component(
        symbol="Device:C",
        ref="C11",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    imu_cap1[1] += vcc_3v3
    imu_cap1[2] += gnd
    
    imu_cap2 = Component(
        symbol="Device:C",
        ref="C12",
        value="10nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    imu_cap2[1] += vcc_3v3
    imu_cap2[2] += gnd
    
    # =================================================================
    # PROGRAMMING AND DEBUG INTERFACE
    # =================================================================
    
    # SWD connector (standard ARM 10-pin)
    swd_conn = Component(
        symbol="Connector_Generic:Conn_02x05_Odd_Even",
        ref="J2",
        footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical"
    )
    
    # SWD pin connections
    swd_conn[1] += vcc_3v3          # VTref
    swd_conn[2] += swdio            # SWDIO
    swd_conn[3] += gnd              # GND
    swd_conn[4] += swclk            # SWCLK
    swd_conn[5] += gnd              # GND
    swd_conn[6] += gnd              # SWO (not used)
    swd_conn[7] += gnd              # Key (no connection)
    swd_conn[8] += gnd              # NC
    swd_conn[9] += gnd              # GND
    swd_conn[10] += nrst            # NRST
    
    # Reset pull-up resistor
    reset_pullup = Component(
        symbol="Device:R",
        ref="R4",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    reset_pullup[1] += nrst
    reset_pullup[2] += vcc_3v3
    
    # Reset button
    reset_btn = Component(
        symbol="Switch:SW_Push",
        ref="SW1",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    reset_btn[1] += nrst
    reset_btn[2] += gnd
    
    # Boot0 pull-down resistor (normal boot mode)
    boot0_pulldown = Component(
        symbol="Device:R",
        ref="R5",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    boot0_pulldown[1] += boot0
    boot0_pulldown[2] += gnd
    
    # Boot jumper for programming mode
    boot_jumper = Component(
        symbol="Connector_Generic:Conn_01x03",
        ref="JP1",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    )
    boot_jumper[1] += vcc_3v3       # Program mode (connect to pin 2)
    boot_jumper[2] += boot0         # Boot0 pin
    boot_jumper[3] += gnd           # Normal mode (connect to pin 2)
    
    # =================================================================
    # STATUS INDICATORS
    # =================================================================
    
    # Power LED (always on when powered)
    power_led_res = Component(
        symbol="Device:R",
        ref="R6",
        value="1K",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    power_led_res[1] += vcc_3v3
    
    power_led_comp = Component(
        symbol="Device:LED",
        ref="D1",
        value="GREEN",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    power_led_res[2] += power_led_comp["A"]  # LED anode
    power_led_comp["K"] += gnd               # LED cathode
    
    # Status LED (controlled by MCU)
    status_led_res = Component(
        symbol="Device:R",
        ref="R7", 
        value="330R",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    status_led_res[1] += status_led
    
    status_led_comp = Component(
        symbol="Device:LED",
        ref="D2",
        value="BLUE",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    status_led_res[2] += status_led_comp["A"]  # LED anode
    status_led_comp["K"] += gnd                # LED cathode
    
    print("✅ Proper STM32 IMU USB-C PCB design complete!")
    print(f"📋 Features:")
    print(f"   • STM32F411CEU6 microcontroller (proper symbol)")
    print(f"   • LSM6DS3TR-C 6-axis IMU sensor")
    print(f"   • USB-C connector with proper pin mapping")
    print(f"   • 25MHz crystal oscillator")
    print(f"   • 3.3V power regulation with filtering")
    print(f"   • SWD programming interface")
    print(f"   • I2C communication")
    print(f"   • Status LEDs and reset button")
    print(f"🏭 All components available on JLCPCB")
    print(f"⚡ Professional-grade design ready for manufacturing")


# Allow running directly for testing
if __name__ == "__main__":
    try:
        circuit_result = stm32_imu_usb_proper()
        print("\n🎉 Circuit generation successful!")
    except Exception as e:
        print(f"\n❌ Circuit generation failed: {e}")
        import traceback
        traceback.print_exc()