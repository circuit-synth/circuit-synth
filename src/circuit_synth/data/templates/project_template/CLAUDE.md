# CLAUDE.md - Circuit-Synth Direct Generation

**Generate working circuits directly using commands - NO AGENTS**

## 🔥 Circuit Design Workflow

When user requests circuit design, follow this EXACT workflow:

### STEP 1: Quick Requirements (5 seconds)
Ask 1-2 focused questions:
- Circuit type (power supply, MCU board, analog, etc.)
- Key specifications (voltage, current, frequency, etc.)
- Main component requirements (STM32 with USB, 3.3V regulator, etc.)

### STEP 2: Find Suitable Components (15 seconds)

#### For STM32 Circuits:
```bash
# Find STM32 with specific peripherals
/find_stm32 "STM32 with USB and 3 SPIs available on JLCPCB"
```

#### For Other Components:
```bash
# Check JLCPCB availability
/find-parts --source jlcpcb AMS1117-3.3

# Check DigiKey for alternatives
/find-parts --source digikey "3.3V linear regulator SOT-223"
```

### STEP 3: Get KiCad Integration Data (15 seconds)
```bash
# Find exact KiCad symbol
/find-symbol STM32F411CEU

# Find matching footprint
/find-footprint LQFP-48

# Get exact pin names (CRITICAL)
/find-pins MCU_ST_STM32F4:STM32F411CEUx
```

### STEP 4: Generate Circuit-Synth Code (15 seconds)
Write Python file using EXACT data from commands:
```python
from circuit_synth import Component, Net, circuit

@circuit(name="MyCircuit")
def my_circuit():
    # Use EXACT symbol and footprint from commands
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",  # From /find-symbol
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"  # From /find-footprint
    )
    
    # Use EXACT pin names from /find-pins
    vcc = Net('VCC_3V3')
    gnd = Net('GND')
    
    mcu["VDD"] += vcc      # Exact pin name from /find-pins
    mcu["VSS"] += gnd      # Exact pin name from /find-pins
    
    # Continue circuit design...
    
    if __name__ == "__main__":
        circuit_obj = my_circuit()
        circuit_obj.generate_kicad_project(
            project_name="MyProject",
            placement_algorithm="hierarchical",
            generate_pcb=True
        )
        print("✅ KiCad project generated!")
        
# ALWAYS include main execution block
```

### STEP 5: Test and Generate KiCad (10 seconds)
```bash
# MANDATORY: Test the code
uv run python circuit_file.py

# If successful: Open KiCad project
open MyProject.kicad_pro
```

## ⚡ Available Commands

### Component Sourcing:
- `/find-parts --source jlcpcb <component>` - Search JLCPCB
- `/find-parts --source digikey <component>` - Search DigiKey  
- `/find_stm32 "<requirements>"` - STM32 peripheral search

### KiCad Integration:
- `/find-symbol <component_name>` - Find KiCad symbols
- `/find-footprint <package_type>` - Find KiCad footprints
- `/find-pins <symbol_name>` - Get exact pin names

## 🎯 Example Workflows

### STM32 Development Board:
```
User: "STM32 development board with USB"
1. /find_stm32 "STM32 with USB available on JLCPCB"
2. /find-symbol STM32F411CEU
3. /find-footprint LQFP-48
4. /find-pins MCU_ST_STM32F4:STM32F411CEUx
5. Generate circuit with exact pin names
6. uv run python stm32_board.py
```

### Power Supply Circuit:
```
User: "3.3V power supply from USB"
1. /find-parts --source jlcpcb AMS1117-3.3
2. /find-symbol AMS1117-3.3
3. /find-footprint SOT-223
4. /find-pins Regulator_Linear:AMS1117-3.3
5. Generate power circuit
6. uv run python power_supply.py
```

### LED Circuit:
```
User: "LED blinker circuit"
1. /find-parts --source jlcpcb "LED 0603"
2. /find-symbol LED
3. /find-footprint 0603
4. Generate simple LED circuit (Device:LED, Device:R)
5. uv run python led_blinker.py
```

## 🚨 Critical Rules

1. **ALWAYS use commands** - don't guess component specs
2. **VALIDATE before generating** - use /find-pins for exact pin names
3. **TEST the code** - uv run python before claiming success
4. **Use uv run python** - not python3 or python
5. **Include KiCad generation** - in the if __name__ == "__main__" block
6. **60-second time limit** - work fast and direct

## 🔧 Error Handling

### Component Not Found:
- Try /find-parts with different search terms
- Use basic Device: components as fallback

### Pin Name Errors:
- Use /find-pins to get exact pin names
- Don't guess pin names - always validate

### Execution Failures:
- Check error message for specific issues
- Fix pin names or component symbols
- Retry once maximum

## 📦 Working Component Library

### STM32 Microcontrollers:
- **STM32F4**: `MCU_ST_STM32F4:STM32F411CEUx` / LQFP-48
- **STM32G4**: `MCU_ST_STM32G4:STM32G431CBTx` / LQFP-48

### Power Components:
- **Linear Reg**: `Regulator_Linear:AMS1117-3.3` / SOT-223
- **Buck IC**: `Regulator_Switching:LM2596S-3.3` / TO-263

### Basic Components:
- **Resistor**: `Device:R` / R_0603_1608Metric
- **Capacitor**: `Device:C` / C_0603_1608Metric  
- **LED**: `Device:LED` / LED_0603_1608Metric

### Connectors:
- **USB Micro**: `Connector:USB_B_Micro`
- **Headers**: `Connector_Generic:Conn_01x10`

---

**WORK DIRECTLY. USE COMMANDS. GENERATE WORKING CIRCUITS FAST.**