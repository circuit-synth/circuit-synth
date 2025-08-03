#!/usr/bin/env python3

from src.circuit_synth import circuit
from src.circuit_synth.core.circuit import Circuit

# Create a simple USB-C circuit to test logging
@circuit(name="USB_Port")
def usb_port():
    """Simple USB-C port subcircuit for testing logging cleanup."""
    
    # Import Component and Net classes
    from src.circuit_synth.core.component import Component
    from src.circuit_synth.core.net import Net
    
    # Create USB-C connector
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    
    # Create nets
    usb_dm = Net('USB_DM') 
    usb_dp = Net('USB_DP')
    vbus_out = Net('VBUS_OUT')
    gnd = Net('GND')
    
    # Connect USB differential pairs
    usb_connector["A6"] += usb_dp  # D+
    usb_connector["B6"] += usb_dp  # D+ (duplicate)
    usb_connector["A7"] += usb_dm  # D-
    usb_connector["B7"] += usb_dm  # D- (duplicate)
    
    # Connect power
    usb_connector["A4"] += vbus_out
    usb_connector["A9"] += vbus_out
    usb_connector["B4"] += vbus_out
    usb_connector["B9"] += vbus_out
    
    # Connect ground pins
    usb_connector["A1"] += gnd
    usb_connector["A12"] += gnd
    usb_connector["B1"] += gnd
    usb_connector["B12"] += gnd
    usb_connector["S1"] += gnd  # Shield

if __name__ == "__main__":
    print("✅ USB-C circuit created for logging test!")
    
    # Generate the circuit
    subcircuit = usb_port()
    
    # Try to generate KiCad files to see logging output
    try:
        subcircuit.generate_kicad_project(
            project_name="test_logging"
        )
        print("🎉 KiCad generation completed!")
    except Exception as e:
        print(f"❌ KiCad generation failed: {e}")