# circuit-synth

A circuit-synth project for professional circuit design with hierarchical architecture.

## 🚀 Quick Start

```bash
# Run the ESP32-C6 development board example
uv run python circuit-synth/main.py
```

## 📁 Project Structure

```
my_kicad_project/
├── circuit-synth/        # Circuit-synth Python files
│   ├── main.py           # Main ESP32-C6 development board (nets only)
│   ├── usb_subcircuit.py # USB-C with CC resistors and ESD protection
│   ├── power_supply_subcircuit.py # 5V to 3.3V power regulation
│   ├── debug_header_subcircuit.py # Programming and debug interface
│   ├── led_blinker_subcircuit.py  # Status LED with current limiting
│   └── esp32_subcircuit.py        # ESP32-C6 microcontroller subcircuit
├── kicad_plugins/        # KiCad plugin files for AI integration
│   ├── circuit_synth_bom_plugin.py        # Schematic BOM plugin
│   ├── circuit_synth_pcb_bom_bridge.py   # PCB editor plugin
│   ├── install_plugin.py                 # Plugin installer script
│   └── README_SIMPLIFIED.md              # Plugin setup instructions
├── kicad-project/        # KiCad files (generated when circuits run)
│   ├── ESP32_C6_Dev_Board.kicad_pro        # Main project file
│   ├── ESP32_C6_Dev_Board.kicad_sch        # Top-level schematic  
│   ├── ESP32_C6_Dev_Board.kicad_pcb        # PCB layout
│   ├── USB_Port.kicad_sch                  # USB-C circuit sheet
│   ├── Power_Supply.kicad_sch              # Power regulation circuit sheet
│   ├── Debug_Header.kicad_sch              # Debug interface circuit sheet
│   └── LED_Blinker.kicad_sch               # Status LED circuit sheet
├── .claude/              # AI agents for Claude Code
│   ├── agents/           # Specialized circuit design agents
│   └── commands/         # Slash commands
├── README.md            # This file
└── CLAUDE.md            # Project-specific Claude guidance
```

## 🏗️ Circuit-Synth Basics

### **Hierarchical Design Philosophy**

Circuit-synth uses **hierarchical subcircuits** - each subcircuit is like a software function with single responsibility and clear interfaces. **The main circuit only defines nets and passes them to subcircuits:**

```python
@circuit(name="ESP32_C6_Dev_Board_Main")
def main_circuit():
    """Main circuit - ONLY nets and subcircuit connections"""
    # Define shared nets (no components here!)
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    
    # Pass nets to subcircuits
    esp32 = esp32_subcircuit(vcc_3v3, gnd, usb_dp, ...)
    power_supply = power_supply_subcircuit()
```

### **Basic Component Creation**

```python
# Create components with symbol, reference, and footprint
mcu = Component(
    symbol="RF_Module:ESP32-C6-MINI-1",       # KiCad symbol
    ref="U",                                   # Reference prefix  
    footprint="RF_Module:ESP32-C6-MINI-1"
)

# Passive components with values
resistor = Component(symbol="Device:R", ref="R", value="330", 
                    footprint="Resistor_SMD:R_0805_2012Metric")
```

### **Net Connections**

```python
# Create nets for electrical connections
vcc = Net("VCC_3V3")
gnd = Net("GND")

# Connect components to nets
mcu["VDD"] += vcc      # Named pins
mcu["VSS"] += gnd
resistor[1] += vcc     # Numbered pins
```

### **Generate KiCad Projects**

```python
# Generate complete KiCad project
circuit = my_circuit()
circuit.generate_kicad_project(
    project_name="my_design",
    placement_algorithm="hierarchical",  # Professional layout
    generate_pcb=True                   # Include PCB file
)
```

## 🤖 AI-Powered Design with Claude Code

**Circuit-synth is an agent-first library** - designed to be used with and by AI agents for intelligent circuit design.

### **Available AI Agents**

This project includes specialized circuit design agents registered in `.claude/agents/`:

#### **🎯 circuit-synth Agent**
- **Expertise**: Circuit-synth code generation and KiCad integration
- **Usage**: `@Task(subagent_type="circuit-synth", description="Design power supply", prompt="Create 3.3V regulator circuit with USB-C input")`
- **Capabilities**: 
  - Generate production-ready circuit-synth code
  - KiCad symbol/footprint verification
  - JLCPCB component availability checking
  - Manufacturing-ready designs with verified components

#### **🔬 simulation-expert Agent**  
- **Expertise**: SPICE simulation and circuit validation
- **Usage**: `@Task(subagent_type="simulation-expert", description="Validate filter", prompt="Simulate and optimize this low-pass filter circuit")`
- **Capabilities**:
  - Professional SPICE analysis (DC, AC, transient)
  - Hierarchical circuit validation
  - Component value optimization
  - Performance analysis and reporting

### **Agent-First Design Philosophy**

**Natural Language → Working Code:** Describe what you want, get production-ready circuit-synth code.

```
👤 "Design a motor controller with STM32, 3 half-bridges, and CAN bus"

🤖 Claude (using circuit-synth agent):
   ✅ Searches components with real JLCPCB availability
   ✅ Generates hierarchical circuit-synth code
   ✅ Creates professional KiCad project
   ✅ Includes manufacturing data and alternatives
```

### **Component Intelligence Example**

```
👤 "Find STM32 with 3 SPIs available on JLCPCB"

🤖 **STM32G431CBT6** - Found matching component  
   📊 Stock: 83,737 units | Price: $2.50@100pcs
   ✅ 3 SPIs: SPI1, SPI2, SPI3
   
   # Ready-to-use circuit-synth code:
   mcu = Component(
       symbol="MCU_ST_STM32G4:STM32G431CBTx",
       ref="U", 
       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
   )
```

### **Using Agents in Claude Code**

1. **Direct Agent Tasks**: Use `@Task()` with specific agents
2. **Natural Conversation**: Agents automatically activated based on context
3. **Multi-Agent Workflows**: Agents collaborate (circuit-synth → simulation-expert)

**Examples:**
```
# Design and validate workflow
👤 "Create and simulate a buck converter for 5V→3.3V@2A"

# Component search workflow  
👤 "Find a low-noise op-amp for audio applications, check JLCPCB stock"

# Hierarchical design workflow
👤 "Design ESP32 IoT sensor node with power management and wireless"
```

## 🔬 SPICE Simulation

Validate your designs with professional simulation:

```python
# Add to any circuit for simulation
circuit = my_circuit()
sim = circuit.simulator()

# DC analysis
result = sim.operating_point()
print(f"Output voltage: {result.get_voltage('VOUT'):.3f}V")

# AC frequency response  
ac_result = sim.ac_analysis(1, 100000)  # 1Hz to 100kHz
```

## 📚 KiCad Libraries

This project uses these KiCad symbol libraries:

**Standard Libraries:**
- Device (resistors, capacitors, LEDs)
- Connector_Generic (headers, connectors)
- MCU_ST_STM32F4 (STM32 microcontrollers)
- Regulator_Linear (voltage regulators)
- RF_Module (ESP32, wireless modules)



## 🛠️ Development Workflow

1. **Design**: Create hierarchical circuits in Python
2. **Validate**: Use SPICE simulation for critical circuits  
3. **Generate**: Export to KiCad with proper hierarchical structure
4. **Manufacture**: Components verified for JLCPCB availability

## 📖 Documentation

- Circuit-Synth: https://circuit-synth.readthedocs.io
- KiCad: https://docs.kicad.org
- Component Search: Use Claude Code agents for intelligent component selection

## 🚀 Next Steps

1. Run the example circuits to familiarize yourself
2. Use Claude Code for AI-assisted circuit design
3. Create your own hierarchical circuits
4. Validate designs with SPICE simulation
5. Generate production-ready KiCad projects

**Happy circuit designing!** 🎛️
