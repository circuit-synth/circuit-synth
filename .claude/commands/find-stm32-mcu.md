---
allowed-tools: Task
description: Find optimal STM32 MCU with pin assignments for your project requirements
argument-hint: [project requirements]
---

Find the perfect STM32 MCU with complete pin assignments for: **$ARGUMENTS**

**🎯 What This Command Does:**

This command connects you with an STM32 specialist that combines:
1. **Comprehensive STM32 Knowledge** - All families (F0, F1, F4, G0, G4, H7, etc.)
2. **Real Pin Mapping Data** - Uses modm-devices repository for accurate pin assignments
3. **JLCPCB Integration** - Verifies component availability and pricing
4. **Ready Circuit Code** - Generates circuit-synth code with proper pin connections

**📋 Usage Examples:**

- `/find-stm32-mcu IoT project with WiFi, 2 UARTs, SPI, I2C, low power`
- `/find-stm32-mcu Motor controller for 3-phase BLDC with encoder feedback`
- `/find-stm32-mcu Audio processor with I2S, USB, and DSP capabilities`
- `/find-stm32-mcu Battery-powered sensor node with LoRa and multiple ADCs`
- `/find-stm32-mcu High-speed data logger with SD card and Ethernet`

**🔍 What You'll Get:**

```
🎯 STM32G431CBT6 - Recommended for IoT Project
💡 ARM Cortex-M4 @ 170MHz, 128KB Flash, 32KB RAM
📦 LQFP-48 Package | 💰 $2.50@100pcs | ✅ 83K units in stock

📋 Complete Pin Assignment:
- USART1_TX: PA9 (AF7) | USART1_RX: PA10 (AF7)
- USART2_TX: PA2 (AF7) | USART2_RX: PA3 (AF7)  
- SPI1_SCK: PA5 (AF5) | SPI1_MISO: PA6 (AF5)
- I2C1_SCL: PB8 (AF4) | I2C1_SDA: PB9 (AF4)

🔌 Ready Circuit-Synth Code:
mcu = Component(
    symbol="MCU_ST_STM32G4:STM32G431CBTx",
    ref="U1",
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
)
# Pin connections included...
```

**🚀 Advanced Features:**

- **Conflict Resolution**: Ensures no pin assignment conflicts
- **Alternative Options**: Shows 2-3 MCU choices with trade-offs
- **Power Analysis**: Considers current consumption for battery projects
- **Package Options**: Recommends optimal package for your constraints
- **Future Expansion**: Suggests pins for potential future features

**⚡ Perfect For:**

- **Embedded Developers** - Get precise pin assignments instantly
- **Hardware Designers** - Verify manufacturability and availability
- **Prototyping** - Skip hours of datasheet reading and pin planning
- **Production** - Ensure chosen MCU is available and cost-effective

**🧠 Intelligent Recommendations:**

The agent considers:
- Peripheral count and capabilities vs your requirements
- Power consumption patterns for battery applications
- Manufacturing availability and lead times
- Cost optimization across quantity breaks
- Pin availability for future expansion
- KiCad library compatibility

**Example Output:**
Instead of spending hours reading datasheets and checking pin assignments, get comprehensive MCU recommendations with verified pin mappings in seconds. The agent uses real modm-devices data to ensure accuracy and provides ready-to-use circuit-synth code.

Transform vague requirements like "I need an MCU for motor control" into specific, manufacturable solutions with complete pin assignments and component availability verification.