#!/usr/bin/env python3
"""
USB-C Subcircuit - Professional USB Interface
============================================

USB-C connector with proper ESD protection and configuration resistors.
Provides robust USB interface for power and programming.
"""

from circuit_synth import Component, Net, circuit


@circuit(name="USB_C_Interface")
def usb_subcircuit(vbus_net, vcc_5v_net, gnd_net, usb_dp_net, usb_dm_net):
    """
    USB-C connector subcircuit with ESD protection
    
    Features:
    - USB-C receptacle with proper pinout
    - CC resistors for USB 2.0 device configuration  
    - ESD protection on data lines
    - VBUS sensing and power distribution
    
    Args:
        vbus_net: USB VBUS detection net
        vcc_5v_net: Filtered 5V power output net
        gnd_net: System ground net
        usb_dp_net: USB D+ data net
        usb_dm_net: USB D- data net
    """
    
    # USB-C receptacle connector
    # Standard 24-pin USB-C connector
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P_TopMount_DrillsUnspecified",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_JAE_DX07S024WJ1R350"
    )
    
    # CC configuration resistors (5.1k for device/sink)
    # These resistors on CC1/CC2 pins identify this as a USB device
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
    
    # VBUS filter capacitor
    # Filters noise on the 5V USB power line
    vbus_cap = Component(
        symbol="Device:C",
        ref="C",
        value="10uF", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # ESD protection diodes (optional but recommended)
    # Protects USB data lines from electrostatic discharge
    esd_diode = Component(
        symbol="Device:D_TVS_Dual_AAC",
        ref="D",
        footprint="Diode_SMD:D_SOD-323"
    )
    
    # Connect USB-C pins
    # VBUS pins (multiple for current carrying capacity)
    usb_conn["A4"] += vbus_net    # VBUS
    usb_conn["A9"] += vbus_net    # VBUS  
    usb_conn["B4"] += vbus_net    # VBUS
    usb_conn["B9"] += vbus_net    # VBUS
    
    # Ground pins
    usb_conn["A1"] += gnd_net     # GND
    usb_conn["A12"] += gnd_net    # GND
    usb_conn["B1"] += gnd_net     # GND
    usb_conn["B12"] += gnd_net    # GND
    usb_conn["S1"] += gnd_net     # Shield
    
    # USB 2.0 data pins
    usb_conn["A6"] += usb_dp_net  # D+
    usb_conn["A7"] += usb_dm_net  # D-
    usb_conn["B6"] += usb_dp_net  # D+
    usb_conn["B7"] += usb_dm_net  # D-
    
    # Configuration Channel (CC) pins
    # CC resistors identify this as a USB device
    usb_conn["A5"] += cc1_resistor[1]  # CC1
    usb_conn["B5"] += cc2_resistor[1]  # CC2
    cc1_resistor[2] += gnd_net
    cc2_resistor[2] += gnd_net
    
    # VBUS filtering and power distribution
    vbus_net += vbus_cap[1]
    vbus_cap[2] += gnd_net
    
    # Connect filtered 5V output (could add ferrite bead here)
    vbus_net += vcc_5v_net
    
    # ESD protection on data lines
    esd_diode["A1"] += usb_dp_net
    esd_diode["A2"] += gnd_net
    esd_diode["C1"] += usb_dm_net
    esd_diode["C2"] += gnd_net
    
    return locals()


if __name__ == "__main__":
    print("🔌 Testing USB-C subcircuit...")
    
    # Create test nets
    vbus = Net('USB_VBUS')
    vcc_5v = Net('VCC_5V')
    gnd = Net('GND')
    usb_dp = Net('USB_DP') 
    usb_dm = Net('USB_DM')
    
    # Test the subcircuit
    circuit_obj = usb_subcircuit(vbus, vcc_5v, gnd, usb_dp, usb_dm)
    
    print("✅ USB-C subcircuit created successfully")
    print(f"📊 Components: {len(circuit_obj.to_dict()['components'])}")