---
allowed-tools: ['*']
description: Clone successful circuit patterns into new designs\nargument-hint: [circuit_name or pattern_type]\n---\n\nClone proven circuit patterns from the memory-bank or existing designs.

🔄 **Circuit Pattern Cloning**: $ARGUMENTS

**Pattern Library Access:**
1. **Memory Bank Patterns**: Access documented successful designs
2. **Standard Circuit Blocks**: Power supplies, communication interfaces, etc.
3. **Application Specific**: Motor control, sensor interfaces, communication
4. **Custom Patterns**: User-defined reusable circuit blocks

**Cloning Process:**
- Search memory-bank for matching circuit patterns
- Extract and adapt circuit-synth code for current design
- Update component references and net names for integration
- Verify component availability and suggest alternatives if needed

**Available Pattern Categories:**
- **Power Management**: Linear/switching regulators, battery charging
- **Microcontroller Cores**: STM32, ESP32, Arduino-compatible designs
- **Communication**: UART, SPI, I2C, USB, Ethernet interfaces
- **Sensor Interfaces**: ADC, DAC, amplifiers, filters
- **Motor Control**: BLDC, stepper, servo motor drive circuits
- **Protection**: ESD, overvoltage, overcurrent protection

**Output:**
- Adapted circuit-synth code ready for integration
- Component list with current availability status
- Integration notes and connection requirements
- Performance specifications and design constraints