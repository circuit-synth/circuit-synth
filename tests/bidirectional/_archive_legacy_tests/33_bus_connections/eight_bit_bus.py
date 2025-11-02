#!/usr/bin/env python3
"""
Fixture: 8-bit data bus connecting MCU to memory device.

Simulates a real microcontroller circuit with bidirectional data bus:
- MCU (microcontroller) with 8 data pins (D0-D7)
- MEM (memory device) with 8 data pins (D0-D7)
- BUF (buffer/driver optional, for single-line modification test)

All 8 data lines connect between MCU and MEM via hierarchical labels.
This creates 8 separate nets: D0, D1, D2, D3, D4, D5, D6, D7

Test workflow:
1. Generate with all 8 lines connected (MCU ↔ MEM)
2. Modify in Python (e.g., disconnect D0 from MEM)
3. Regenerate and validate only D0 changed
"""

from circuit_synth import *


@circuit(name="eight_bit_bus")
def eight_bit_bus():
    """Circuit with 8-bit data bus connecting MCU to memory device."""

    # Microcontroller (simplified as a Component with 8 data pins)
    # In reality, this would be an STM32, AVR, etc.
    # Using a 8-pin connector to represent 8 data pins
    mcu = Component(
        symbol="Connector:Conn_01x08_Pin",  # 8-pin connector - all pins usable
        ref="MCU1",
        value="ARM_MCU",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    )

    # Memory device (SRAM, Flash, etc.)
    # Using 8-pin connector with pins 1-8
    mem = Component(
        symbol="Connector:Conn_01x08_Pin",  # 8-pin connector - all pins usable
        ref="MEM1",
        value="32K_SRAM",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    )

    # Optional: Buffer/driver for single-line test modification
    # This allows us to modify which component connects to a bus line
    # Using a simpler component (2-pin resistor) for buffer testing
    buf = Component(
        symbol="Device:R",  # Simple 2-pin component for buffer
        ref="BUF1",
        value="BUFFER",
        footprint="Package_DIP:DIP-2_W7.62mm",
    )

    # Create 8-bit data bus connecting MCU to MEM
    # Each net represents one data line
    # Format: D0, D1, D2, D3, D4, D5, D6, D7
    # Using Conn_01x08_Pin which has pins 1-8, all usable for data

    # D0 - Data bit 0
    d0_net = Net(name="D0")
    d0_net += mcu[1]  # MCU pin 1 → D0
    d0_net += mem[1]  # MEM pin 1 → D0

    # D1 - Data bit 1
    d1_net = Net(name="D1")
    d1_net += mcu[2]  # MCU pin 2 → D1
    d1_net += mem[2]  # MEM pin 2 → D1

    # D2 - Data bit 2
    d2_net = Net(name="D2")
    d2_net += mcu[3]  # MCU pin 3 → D2
    d2_net += mem[3]  # MEM pin 3 → D2

    # D3 - Data bit 3
    d3_net = Net(name="D3")
    d3_net += mcu[4]  # MCU pin 4 → D3
    d3_net += mem[4]  # MEM pin 4 → D3

    # D4 - Data bit 4
    d4_net = Net(name="D4")
    d4_net += mcu[5]  # MCU pin 5 → D4
    d4_net += mem[5]  # MEM pin 5 → D4

    # D5 - Data bit 5
    d5_net = Net(name="D5")
    d5_net += mcu[6]  # MCU pin 6 → D5
    d5_net += mem[6]  # MEM pin 6 → D5

    # D6 - Data bit 6
    d6_net = Net(name="D6")
    d6_net += mcu[7]  # MCU pin 7 → D6
    d6_net += mem[7]  # MEM pin 7 → D6

    # D7 - Data bit 7 (MSB)
    d7_net = Net(name="D7")
    d7_net += mcu[8]  # MCU pin 8 → D7
    d7_net += mem[8]  # MEM pin 8 → D7

    # Note: Buffer device is included for potential modification tests
    # Example modification: Connect buffer to D0 instead of MEM
    # buf[1] += d0_net  # Uncomment to test single-line modification


if __name__ == "__main__":
    circuit_obj = eight_bit_bus()
    circuit_obj.generate_kicad_project(
        project_name="eight_bit_bus",
        placement_algorithm="simple",
        generate_pcb=True,
        force_regenerate=True  # Always regenerate to support modification testing
    )
    print("✅ 8-bit data bus circuit generated!")
    print("📁 Open in KiCad: eight_bit_bus/eight_bit_bus.kicad_pro")
    print("\n📊 Data Bus Connections:")
    print("   MCU1 (microcontroller)")
    print("   MEM1 (memory device)")
    print("\n   Bus Lines (D0-D7):")
    print("   ├─ D0: MCU1[1] ↔ MEM1[1]")
    print("   ├─ D1: MCU1[2] ↔ MEM1[2]")
    print("   ├─ D2: MCU1[3] ↔ MEM1[3]")
    print("   ├─ D3: MCU1[4] ↔ MEM1[4]")
    print("   ├─ D4: MCU1[5] ↔ MEM1[5]")
    print("   ├─ D5: MCU1[6] ↔ MEM1[6]")
    print("   ├─ D6: MCU1[7] ↔ MEM1[7]")
    print("   └─ D7: MCU1[8] ↔ MEM1[8]")
    print("\n🔧 Test modifications:")
    print("   - Edit D0_net to connect buffer instead of MEM")
    print("   - Regenerate and verify only D0 changes")
    print("   - D1-D7 should remain unchanged")
