"""
Project Template Generator for Hierarchical Circuit Projects

Creates professional project structures similar to example_project/circuit-synth/
with separate subcircuit files and a main orchestrator.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SubcircuitSpec:
    """Specification for a subcircuit module"""
    name: str
    filename: str  # e.g., "power_supply.py"
    function_name: str  # e.g., "power_supply"
    description: str
    nets_in: List[str]  # Input nets from main circuit
    nets_out: List[str]  # Output nets to main circuit
    components: List[str]  # Main components in this subcircuit
    code_template: str  # Circuit-synth code for this subcircuit


class ProjectTemplateGenerator:
    """Generate hierarchical project structures for fast generation"""
    
    def __init__(self):
        self.templates = self._define_templates()
    
    def _define_templates(self) -> Dict[str, Dict]:
        """Define project templates with hierarchical structure"""
        
        templates = {
            "esp32_complete_board": {
                "name": "ESP32_Complete_Development_Board",
                "description": "Professional ESP32-S3 development board with hierarchical design",
                "subcircuits": [
                    SubcircuitSpec(
                        name="USB Power",
                        filename="usb_power.py", 
                        function_name="usb_power",
                        description="USB-C power input with CC resistors and protection",
                        nets_in=[],
                        nets_out=["VBUS", "GND", "USB_DP", "USB_DM"],
                        components=["USB-C connector", "CC resistors", "Protection fuse"],
                        code_template=self._get_usb_power_template()
                    ),
                    SubcircuitSpec(
                        name="Power Supply",
                        filename="power_supply.py",
                        function_name="power_supply", 
                        description="5V to 3.3V power regulation",
                        nets_in=["VBUS", "GND"],
                        nets_out=["VCC_3V3", "GND"],
                        components=["AMS1117-3.3", "Input/Output capacitors"],
                        code_template=self._get_power_supply_template()
                    ),
                    SubcircuitSpec(
                        name="ESP32 MCU",
                        filename="esp32_mcu.py",
                        function_name="esp32_mcu",
                        description="ESP32-S3 microcontroller with support circuits",
                        nets_in=["VCC_3V3", "GND", "USB_DP", "USB_DM"],
                        nets_out=["VCC_3V3", "GND", "DEBUG_TX", "DEBUG_RX", "LED_CONTROL"],
                        components=["ESP32-S3-WROOM-1", "Decoupling caps", "EN pull-up"],
                        code_template=self._get_esp32_mcu_template()
                    ),
                    SubcircuitSpec(
                        name="Debug Header",
                        filename="debug_header.py",
                        function_name="debug_header",
                        description="Debug and programming interface",
                        nets_in=["VCC_3V3", "GND", "DEBUG_TX", "DEBUG_RX"],
                        nets_out=[],
                        components=["Debug connector"],
                        code_template=self._get_debug_header_template()
                    ),
                    SubcircuitSpec(
                        name="Status LED",
                        filename="led_status.py",
                        function_name="led_status", 
                        description="Status LED with current limiting",
                        nets_in=["VCC_3V3", "GND", "LED_CONTROL"],
                        nets_out=[],
                        components=["LED", "Current limiting resistor"],
                        code_template=self._get_led_status_template()
                    )
                ],
                "main_template": self._get_esp32_main_template()
            },
            
            "stm32_complete_board": {
                "name": "STM32_Complete_Development_Board", 
                "description": "Professional STM32F411 development board with hierarchical design",
                "subcircuits": [
                    SubcircuitSpec(
                        name="Power Supply",
                        filename="power_supply.py",
                        function_name="power_supply",
                        description="Power input and regulation", 
                        nets_in=[],
                        nets_out=["VCC_3V3", "GND"],
                        components=["Power connector", "Decoupling caps"],
                        code_template=self._get_stm32_power_template()
                    ),
                    SubcircuitSpec(
                        name="STM32 MCU",
                        filename="stm32_mcu.py", 
                        function_name="stm32_mcu",
                        description="STM32F411 microcontroller with crystal and support circuits",
                        nets_in=["VCC_3V3", "GND"],
                        nets_out=["VCC_3V3", "GND", "SWDIO", "SWCLK", "LED_CONTROL"],
                        components=["STM32F411", "HSE crystal", "Load caps", "Reset circuit"],
                        code_template=self._get_stm32_mcu_template()
                    ),
                    SubcircuitSpec(
                        name="Debug Header",
                        filename="debug_header.py",
                        function_name="debug_header", 
                        description="SWD debug and programming interface",
                        nets_in=["VCC_3V3", "GND", "SWDIO", "SWCLK"],
                        nets_out=[],
                        components=["SWD connector"],
                        code_template=self._get_swd_debug_template()
                    ),
                    SubcircuitSpec(
                        name="Status LED",
                        filename="led_status.py",
                        function_name="led_status",
                        description="Status LED with current limiting",
                        nets_in=["VCC_3V3", "GND", "LED_CONTROL"],
                        nets_out=[],
                        components=["LED", "Current limiting resistor"],
                        code_template=self._get_led_status_template()
                    )
                ],
                "main_template": self._get_stm32_main_template()
            }
        }
        
        return templates
    
    def generate_project(self, template_name: str, output_dir: Path, project_name: str = None) -> bool:
        """Generate a complete hierarchical project"""
        if template_name not in self.templates:
            return False
        
        template = self.templates[template_name]
        actual_project_name = project_name or template_name
        project_dir = output_dir / actual_project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate subcircuit files
        for subcircuit in template["subcircuits"]:
            subcircuit_file = project_dir / subcircuit.filename
            subcircuit_file.write_text(subcircuit.code_template)
        
        # Generate main.py
        main_file = project_dir / "main.py"
        main_file.write_text(template["main_template"])
        
        return True
    
    def _get_usb_power_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
USB Power Input Circuit
USB-C connector with CC resistors for power negotiation
"""

from circuit_synth import *

@circuit(name="USB_Power_Input")
def usb_power(vbus_out, gnd, usb_dp, usb_dm):
    """USB-C power input subcircuit"""
    
    # USB-C connector
    usb_c = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
    )
    
    # CC pull-down resistors (5.1k for default USB power)
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
    
    # ESD protection for USB data lines
    esd_protection = Component(
        symbol="Power_Protection:USBLC6-2P6",
        ref="D",
        footprint="Package_TO_SOT_SMD:SOT-23-6"
    )
    
    # VBUS protection fuse
    vbus_fuse = Component(
        symbol="Device:Fuse",
        ref="F",
        value="2A",
        footprint="Fuse:Fuse_1206_3216Metric"
    )
    
    # USB-C power connections
    usb_c["A4"] += vbus_fuse[1]  # VBUS (A-side)
    usb_c["A9"] += vbus_fuse[1]  # VBUS (A-side)
    usb_c["B4"] += vbus_fuse[1]  # VBUS (B-side)  
    usb_c["B9"] += vbus_fuse[1]  # VBUS (B-side)
    vbus_fuse[2] += vbus_out
    usb_c["A1"] += gnd   # GND (A-side)
    usb_c["A12"] += gnd  # GND (A-side)
    usb_c["B1"] += gnd   # GND (B-side)
    usb_c["B12"] += gnd  # GND (B-side)
    
    # USB-C data connections through ESD protection
    usb_c["A6"] += esd_protection[1]  # D+ (A-side) to ESD pin 1
    usb_c["A7"] += esd_protection[3]  # D- (A-side) to ESD pin 3
    usb_c["B6"] += esd_protection[1]  # D+ (B-side) to ESD pin 1  
    usb_c["B7"] += esd_protection[3]  # D- (B-side) to ESD pin 3
    esd_protection[6] += usb_dp  # Protected D+ output (pin 6)
    esd_protection[4] += usb_dm  # Protected D- output (pin 4)
    esd_protection[5] += vbus_out    # ESD protection power (pin 5 = VBUS)
    esd_protection[2] += gnd         # ESD protection ground (pin 2 = GND)
    
    # CC pull-down resistors for power negotiation
    usb_c["A5"] += cc1_resistor[1]  # CC1
    cc1_resistor[2] += gnd
    usb_c["B5"] += cc2_resistor[1]  # CC2
    cc2_resistor[2] += gnd
'''

    def _get_power_supply_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
Power Supply Circuit - 5V to 3.3V regulation
Clean power regulation from USB-C VBUS to regulated 3.3V
"""

from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply(vbus_in, vcc_3v3_out, gnd):
    """5V to 3.3V power regulation subcircuit"""
    
    # 3.3V regulator
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input/output capacitors
    cap_in = Component(
        symbol="Device:C", 
        ref="C", 
        value="10uF", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_out = Component(
        symbol="Device:C", 
        ref="C", 
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connections
    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3_out 
    regulator["GND"] += gnd
    
    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd
'''

    def _get_esp32_mcu_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
ESP32 MCU Circuit
ESP32-S3 microcontroller with support circuitry
"""

from circuit_synth import *

@circuit(name="ESP32_MCU")
def esp32_mcu(vcc_3v3, gnd, usb_dp, usb_dm, debug_tx, debug_rx, led_control):
    """ESP32-S3 microcontroller subcircuit"""
    
    # ESP32-S3 microcontroller
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-WROOM-1",
        ref="U",
        footprint="RF_Module:ESP32-S3-WROOM-1"
    )
    
    # Decoupling capacitors
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_bypass1 = Component(
        symbol="Device:C",
        ref="C", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # EN pull-up resistor
    en_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Power connections
    esp32["3V3"] += vcc_3v3
    esp32["GND"] += gnd
    
    # USB connections
    esp32["USB_D+"] += usb_dp
    esp32["USB_D-"] += usb_dm
    
    # Debug UART
    esp32["TXD0"] += debug_tx
    esp32["RXD0"] += debug_rx
    
    # LED control
    esp32["IO8"] += led_control
    
    # Power supply decoupling
    cap_bulk[1] += vcc_3v3
    cap_bulk[2] += gnd
    cap_bypass1[1] += vcc_3v3
    cap_bypass1[2] += gnd
    
    # EN pull-up
    en_pullup[1] += vcc_3v3
    en_pullup[2] += esp32["EN"]
'''

    def _get_debug_header_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
Debug Header Circuit
UART debug and programming interface
"""

from circuit_synth import *

@circuit(name="Debug_Header")
def debug_header(vcc_3v3_in, gnd_in, debug_tx_in, debug_rx_in):
    """Debug header subcircuit"""
    
    # Use input nets
    vcc_3v3 = vcc_3v3_in
    gnd = gnd_in
    debug_tx = debug_tx_in
    debug_rx = debug_rx_in
    
    # Debug header connector
    debug_conn = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Connections
    debug_conn[1] += vcc_3v3  # Power
    debug_conn[2] += gnd      # Ground
    debug_conn[3] += debug_tx # UART TX
    debug_conn[4] += debug_rx # UART RX
'''

    def _get_led_status_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
Status LED Circuit
Status LED with current limiting resistor
"""

from circuit_synth import *

@circuit(name="Status_LED")
def led_status(vcc_3v3_in, gnd_in, led_control_in):
    """Status LED subcircuit"""
    
    # Use input nets
    vcc_3v3 = vcc_3v3_in
    gnd = gnd_in
    led_control = led_control_in
    
    # Status LED
    led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistor
    led_resistor = Component(
        symbol="Device:R", 
        ref="R",
        value="220",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connections
    led_control += led_resistor[1]
    led_resistor[2] += led["A"]
    led["K"] += gnd
'''

    def _get_esp32_main_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
Main Circuit - ESP32-S3 Complete Development Board
Professional hierarchical circuit design with modular subcircuits

This is the main entry point that orchestrates all subcircuits:
- USB-C power input with proper CC resistors and protection
- 5V to 3.3V power regulation
- ESP32-S3 microcontroller with USB and debug interfaces  
- Debug header for programming and development
- Status LED with current limiting
"""

from circuit_synth import *

# Import all subcircuits
from usb_power import usb_power
from power_supply import power_supply  
from esp32_mcu import esp32_mcu
from debug_header import debug_header
from led_status import led_status

@circuit(name="ESP32_Complete_Board")
def main_circuit():
    """Main hierarchical circuit - ESP32-S3 complete development board"""
    
    # Create shared nets between subcircuits (ONLY nets - no components here)
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    debug_tx = Net('DEBUG_TX')
    debug_rx = Net('DEBUG_RX')
    led_control = Net('LED_CONTROL')
    
    # Create all circuits with shared nets
    usb_power_circuit = usb_power(vbus, gnd, usb_dp, usb_dm)
    power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
    esp32_circuit = esp32_mcu(vcc_3v3, gnd, usb_dp, usb_dm, debug_tx, debug_rx, led_control)
    debug_header_circuit = debug_header(vcc_3v3, gnd, debug_tx, debug_rx)
    led_status_circuit = led_status(vcc_3v3, gnd, led_control)


if __name__ == "__main__":
    print("🚀 Starting ESP32 Complete Board generation...")
    
    circuit = main_circuit()
    
    print("🔌 Generating KiCad netlist...")
    circuit.generate_kicad_netlist("ESP32_Complete_Board.net")
    
    print("📄 Generating JSON netlist...")  
    circuit.generate_json_netlist("ESP32_Complete_Board.json")
    
    print("🏗️  Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="ESP32_Complete_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ ESP32 Complete Board project generated!")
    print("📁 Check the ESP32_Complete_Board/ directory for KiCad files")
'''

    def _get_stm32_power_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
STM32 Power Supply Circuit
3.3V power input with filtering and protection
"""

from circuit_synth import *

@circuit(name="STM32_Power_Supply")
def power_supply(vcc_3v3_out, gnd):
    """STM32 power supply subcircuit with filtering"""
    
    # Power input connector (assuming external 3.3V supply)
    power_input = Component(
        symbol="Connector_Generic:Conn_01x02",
        ref="J",
        footprint="Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
    )
    
    # Power filtering capacitors
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_bypass = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Power connections
    power_input[1] += vcc_3v3_out  # 3.3V input
    power_input[2] += gnd          # Ground
    
    # Power filtering
    cap_bulk[1] += vcc_3v3_out
    cap_bulk[2] += gnd
    cap_bypass[1] += vcc_3v3_out
    cap_bypass[2] += gnd
'''
    
    def _get_stm32_mcu_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
STM32 MCU Circuit
STM32F411 microcontroller with crystal and support circuits
"""

from circuit_synth import *

@circuit(name="STM32_MCU")
def stm32_mcu(vcc_3v3, gnd, swdio, swclk, led_control):
    """STM32F411 microcontroller subcircuit"""
    
    # STM32F411 microcontroller
    stm32 = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )
    
    # 8MHz HSE crystal
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y",
        value="8MHz",
        footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"
    )
    
    # Crystal load capacitors
    cap_c1 = Component(
        symbol="Device:C",
        ref="C",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap_c2 = Component(
        symbol="Device:C",
        ref="C",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Power decoupling
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_bypass = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Reset components
    reset_button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    reset_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Internal reset net
    reset = Net('nRESET')
    
    # STM32 power connections
    stm32["VDD"] += vcc_3v3
    stm32["VSS"] += gnd
    stm32["VDDA"] += vcc_3v3
    stm32["VSSA"] += gnd
    
    # HSE crystal connections
    crystal[1] += stm32["PH0"]  # HSE_IN
    crystal[2] += stm32["PH1"]  # HSE_OUT
    
    # Crystal load capacitors
    cap_c1[1] += stm32["PH0"]
    cap_c1[2] += gnd
    cap_c2[1] += stm32["PH1"]
    cap_c2[2] += gnd
    
    # SWD debug connections
    stm32["PA13"] += swdio
    stm32["PA14"] += swclk
    
    # LED control
    stm32["PA5"] += led_control  # GPIO for LED
    
    # Reset circuit
    reset_pullup[1] += vcc_3v3
    reset_pullup[2] += reset
    reset_button[1] += reset
    reset_button[2] += gnd
    stm32["NRST"] += reset
    
    # Power decoupling
    cap_bulk[1] += vcc_3v3
    cap_bulk[2] += gnd
    cap_bypass[1] += vcc_3v3
    cap_bypass[2] += gnd
'''
    
    def _get_swd_debug_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
SWD Debug Header Circuit
SWD debug and programming interface for STM32
"""

from circuit_synth import *

@circuit(name="SWD_Debug_Header")
def debug_header(vcc_3v3, gnd, swdio, swclk):
    """SWD debug header subcircuit"""
    
    # SWD debug connector (4-pin: VCC, GND, SWDIO, SWCLK)
    swd_conn = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Connections
    swd_conn[1] += vcc_3v3  # Power
    swd_conn[2] += gnd      # Ground
    swd_conn[3] += swdio    # SWDIO
    swd_conn[4] += swclk    # SWCLK
'''
    
    def _get_stm32_main_template(self) -> str:
        return '''#!/usr/bin/env python3
"""
Main Circuit - STM32 Complete Development Board
Professional hierarchical circuit design with modular subcircuits

This is the main entry point that orchestrates all subcircuits:
- 3.3V power input with filtering
- STM32F411 microcontroller with crystal and support circuits
- SWD debug header for programming
- Status LED with current limiting
"""

from circuit_synth import *

# Import all subcircuits
from power_supply import power_supply
from stm32_mcu import stm32_mcu
from debug_header import debug_header
from led_status import led_status

@circuit(name="STM32_Complete_Board")
def main_circuit():
    """Main hierarchical circuit - STM32 complete development board"""
    
    # Create shared nets between subcircuits (ONLY nets - no components here)
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    swdio = Net('SWDIO')
    swclk = Net('SWCLK')
    led_control = Net('LED_CONTROL')
    
    # Create all circuits with shared nets
    power_supply_circuit = power_supply(vcc_3v3, gnd)
    stm32_circuit = stm32_mcu(vcc_3v3, gnd, swdio, swclk, led_control)
    debug_header_circuit = debug_header(vcc_3v3, gnd, swdio, swclk)
    led_status_circuit = led_status(vcc_3v3, gnd, led_control)


if __name__ == "__main__":
    print("🚀 Starting STM32 Complete Board generation...")
    
    circuit = main_circuit()
    
    print("🔌 Generating KiCad netlist...")
    circuit.generate_kicad_netlist("STM32_Complete_Board.net")
    
    print("📄 Generating JSON netlist...")
    circuit.generate_json_netlist("STM32_Complete_Board.json")
    
    print("🏗️  Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="STM32_Complete_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ STM32 Complete Board project generated!")
    print("📁 Check the STM32_Complete_Board/ directory for KiCad files")
'''


# For testing
if __name__ == "__main__":
    generator = ProjectTemplateGenerator()
    output_dir = Path("generated_projects")
    success = generator.generate_project("esp32_complete_board", output_dir)
    print(f"Project generation: {'✅ Success' if success else '❌ Failed'}")