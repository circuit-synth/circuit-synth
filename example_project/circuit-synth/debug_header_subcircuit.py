#!/usr/bin/env python3
"""
Debug Header Subcircuit - Programming and debugging interface
Standard ESP32 debug header with UART, reset, and boot control
"""

from circuit_synth import *

@circuit(name="Debug_Header")
def debug_header_subcircuit(vcc_3v3=None, gnd=None, debug_tx=None, debug_rx=None, debug_en=None, debug_io0=None):
    """Debug header for programming and debugging"""
    
    # Interface nets - use provided nets or create defaults for standalone operation
    vcc_3v3 = vcc_3v3 or Net('VCC_3V3')
    gnd = gnd or Net('GND')
    debug_tx = debug_tx or Net('DEBUG_TX')
    debug_rx = debug_rx or Net('DEBUG_RX') 
    debug_en = debug_en or Net('DEBUG_EN')
    debug_io0 = debug_io0 or Net('DEBUG_IO0')
    
    # 2x3 debug header
    debug_header = Component(
        symbol="Connector_Generic:Conn_02x03_Odd_Even",
        ref="J",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical"
    )
    
    # Header connections (standard ESP32 debug layout)
    debug_header[1] += debug_en   # EN/RST
    debug_header[2] += vcc_3v3    # 3.3V
    debug_header[3] += debug_tx   # TX
    debug_header[4] += gnd        # GND
    debug_header[5] += debug_rx   # RX  
    debug_header[6] += debug_io0  # IO0/BOOT

if __name__ == "__main__":
    circuit = debug_header_subcircuit()
    circuit.generate_kicad_project("debug_header")
    print("✅ Debug header subcircuit generated!")
