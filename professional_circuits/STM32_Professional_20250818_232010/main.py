#!/usr/bin/env python3
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
