---
name: design
description: Generate working circuit-synth code and KiCad files (fast, no agents)
category: circuit-design
---

I'll generate a working circuit for you quickly using circuit-synth and KiCad.

What circuit do you want to design?

Examples:
- "STM32 development board like Black Pill"
- "3.3V linear power supply from 5V USB"
- "ESP32 board with WiFi and USB-C"
- "LED blinker with current limiting"
- "Motor driver H-bridge circuit"
- "Op-amp amplifier circuit"

Tell me:
1. **Circuit type** (power supply, MCU board, amplifier, etc.)
2. **Key specs** (voltage, current, frequency, etc.)
3. **Main component** (STM32F411, AMS1117, LM358, etc.)

I'll create circuit-synth Python code with working KiCad symbols, test it, generate the KiCad project files, and open them for you.

**Just describe what you want to build!**

---

*This command creates working circuits without agent complexity - fast and reliable.*