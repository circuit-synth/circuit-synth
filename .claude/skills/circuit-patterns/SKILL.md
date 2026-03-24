---
name: circuit-patterns
description: Pre-made circuit patterns library for common circuit building blocks
allowed-tools: ["Read", "Bash", "Write"]
---

# Circuit Patterns Skill

## When to Use This Skill

Invoke this skill when the user:
- Mentions circuit patterns: "voltage regulator", "voltage divider", "USB-C circuit"
- Asks for pre-made circuits: "do you have a circuit for X", "example circuit"
- Needs design references: "how to design a power supply", "STM32 minimal board"
- Requests circuit templates: "template for USB-C", "LED blinker circuit"
- Wants to see available patterns: "what circuits are available", "list patterns"

## Available Circuit Templates

Templates are located in two directories within the circuit-synth package:

### Base Circuits (`src/circuit_synth/data/templates/base_circuits/`)

1. **resistor_divider.py** - Parametric voltage divider
   - Keywords: voltage divider, ADC, voltage sensing, scaling, level shifting
   - Example: 5V to 3.3V logic level shifter

2. **voltage_regulator.py** - Linear voltage regulator with decoupling
   - Keywords: LDO, linear regulator, AMS1117, voltage regulation
   - Example: AMS1117-3.3 linear regulator with decoupling

3. **led_blinker.py** - LED circuit with current limiting
   - Keywords: LED, blinker, indicator, current limiting resistor
   - Example: Basic LED blinker circuit

4. **minimal.py** - Minimal circuit template
   - Keywords: template, starter, minimal, skeleton
   - Example: Bare-minimum circuit-synth project structure

### Example Circuits (`src/circuit_synth/data/templates/example_circuits/`)

5. **stm32_minimal.py** - STM32 minimal development board
   - Keywords: STM32, microcontroller, MCU, development board, SWD, crystal
   - Example: STM32F411 with USB, crystal, and SWD debug

6. **usb_c_basic.py** - USB-C connector circuit
   - Keywords: USB-C, USB Type-C, CC resistors, USB connector
   - Example: USB-C connector with CC resistors for power delivery

7. **power_supply_module.py** - Dual-rail power supply
   - Keywords: power supply, dual rail, 5V, 3.3V, multi-rail
   - Example: Dual-rail 5V/3.3V power supply module

8. **esp32_dev_board.py** - ESP32 development board
   - Keywords: ESP32, WiFi, Bluetooth, IoT, development board
   - Example: ESP32 dev board with common peripherals

## Capabilities

### Pattern Retrieval
- Load complete circuit pattern code from template files
- Show design notes and calculations
- Provide component selection rationale
- Include PCB layout guidelines

### Design Assistance
- Explain pattern parameters and customization
- Suggest combinations of patterns
- Show usage examples
- Recommend alternatives

### Code Integration
- Patterns are importable Python modules
- All patterns follow circuit-synth `@circuit` decorator
- Composable - combine multiple patterns in one design

## Usage Examples

### Example 1: Get Voltage Regulator Pattern
**User:** "show me the voltage regulator circuit"

**Process:**
1. Read `src/circuit_synth/data/templates/base_circuits/voltage_regulator.py`
2. Extract main circuit function and design notes
3. Show component selection and parameters
4. Provide usage example

### Example 2: List Available Patterns
**User:** "what circuit patterns are available?"

**Process:**
1. List all template files in both directories
2. Categorize by complexity (base vs. example)
3. Provide brief description of each

**Output:**
```
Available Circuit Templates:

BASE CIRCUITS (Beginner):
- resistor_divider.py - Voltage divider for ADC scaling
- voltage_regulator.py - AMS1117-3.3 linear regulator
- led_blinker.py - LED with current limiting
- minimal.py - Bare-minimum project template

EXAMPLE CIRCUITS (Intermediate/Advanced):
- stm32_minimal.py - STM32F411 with USB, crystal, SWD
- usb_c_basic.py - USB-C connector with CC resistors
- power_supply_module.py - Dual-rail 5V/3.3V power supply
- esp32_dev_board.py - ESP32 development board

Use: "show me [template_name]" to see implementation details
```

### Example 3: Combine Multiple Templates
**User:** "create a USB-powered STM32 board"

**Process:**
1. Load relevant templates (stm32_minimal, usb_c_basic, power_supply_module)
2. Show how to import and combine
3. Provide complete integration example

## Template File Locations

```
src/circuit_synth/data/templates/
├── base_circuits/
│   ├── resistor_divider.py
│   ├── voltage_regulator.py
│   ├── led_blinker.py
│   └── minimal.py
└── example_circuits/
    ├── stm32_minimal.py
    ├── usb_c_basic.py
    ├── power_supply_module.py
    └── esp32_dev_board.py
```

## Integration Strategy

### Step 1: Identify Pattern Need
User describes requirement -> Match to available template

### Step 2: Load Template Code
```bash
Read(file_path="src/circuit_synth/data/templates/base_circuits/voltage_regulator.py")
# or
Read(file_path="src/circuit_synth/data/templates/example_circuits/stm32_minimal.py")
```

### Step 3: Extract Relevant Information
- Main circuit function
- Parameter options
- Component details
- Design notes

### Step 4: Provide to User
- Show template code
- Explain customization options
- Suggest usage examples
- Reference combination examples

## Template Structure

Each template follows this structure:

```python
#!/usr/bin/env python3
"""
Template Name - Brief Description
"""

from circuit_synth import *

@circuit(name="Template_Name")
def template_function(inputs, outputs, parameters):
    """Docstring with function description and examples"""
    # Component definitions with symbols and footprints
    # Net connections
    # Configuration
```

## Best Practices

### Pattern Selection
- Match template to exact requirement
- Consider combining templates for complex designs
- Review design notes before implementation

### Customization
- Use provided parameters
- Follow design equations for custom values
- Reference datasheet for advanced changes

### Integration
- Import templates as modules
- Share nets between templates
- Follow example circuits for guidance
