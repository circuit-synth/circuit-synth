# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this circuit-synth project.

## 🚀 Project Overview

This is a **circuit-synth project** for professional circuit design with AI-powered component intelligence and manufacturing integration.

## ⚡ Quick Start Commands

```bash
# Run the main ESP32-C6 development board example
uv run python circuit-synth/main.py

# Test circuit-synth installation
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth ready!')"
```

## 🔧 Essential Commands

### KiCad Integration
```bash
# Ensure KiCad is installed locally (required dependency)
kicad-cli version

# Verify KiCad libraries are accessible
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5
```

### Component Search Commands
```bash
# Unified component search across suppliers (NEW!)
# /find-parts "0.1uF 0603" - Search all suppliers
# /find-parts "STM32F407" --source jlcpcb - JLCPCB only
# /find-parts "LM358" --source digikey - DigiKey only
# /find-parts "3.3V regulator" --compare - Compare across suppliers

# KiCad symbol and footprint search
# /find-symbol STM32 - Search for STM32 symbols
# /find-footprint LQFP - Search for LQFP footprints

# Circuit validation commands
# /generate-validated-circuit "ESP32 development board" - Generate circuit with quality assurance
# /validate-existing-circuit - Validate and improve existing circuit code

# Circuit Debugging commands (NEW!)
# /debug-start "Board not powering on" --board="my_board" - Start debug session
# /debug-symptom "No voltage on 3.3V rail" - Add symptom
# /debug-measure "VCC: 0V, VBUS: 5V" - Add measurements
# /debug-analyze - Get AI analysis of issues
# /debug-suggest - Get next troubleshooting steps
# /debug-tree power - Show power troubleshooting tree

# Manual search in KiCad libraries (if needed)
find /usr/share/kicad/symbols -name "*.kicad_sym" | xargs grep -l "STM32"
find /usr/share/kicad/footprints -name "*.kicad_mod" | grep -i lqfp
```

### Multi-Source Component Search (NEW!)
```python
from circuit_synth.manufacturing import find_parts

# Search all suppliers
results = find_parts("0.1uF 0603 X7R", sources="all")

# Search specific supplier
jlc_results = find_parts("STM32F407", sources="jlcpcb")
dk_results = find_parts("LM358", sources="digikey")

# Compare across suppliers
comparison = find_parts("3.3V regulator", sources="all", compare=True)
print(comparison)  # Shows comparison table

# Filter by requirements
high_stock = find_parts("10k resistor", min_stock=10000, max_price=0.10)
```

### DigiKey Integration Setup
```bash
# Configure DigiKey API (one-time setup)
python -m circuit_synth.manufacturing.digikey.config_manager

# Test connection
python -m circuit_synth.manufacturing.digikey.test_connection

# Environment variables (alternative to config file)
export DIGIKEY_CLIENT_ID="your_client_id"
export DIGIKEY_CLIENT_SECRET="your_client_secret"
```

## 🤖 Specialized AI Agents

This project includes specialized circuit design agents registered in `.claude/agents/`:

### **🎯 circuit-architect Agent**
- **Expertise**: Master circuit design coordinator and architecture expert
- **Usage**: `@Task(subagent_type="circuit-architect", description="Design ESP32 board", prompt="Create complete ESP32 development board with USB-C, power management, and programming interface")`
- **Capabilities**: 
  - Coordinates complex multi-domain circuit projects
  - Manages dependencies between power, digital, and analog domains
  - Professional PCB layout and component placement strategies

### **🔌 circuit-synth Agent**
- **Expertise**: Circuit-synth code generation and KiCad integration
- **Usage**: `@Task(subagent_type="circuit-synth", description="Design power supply", prompt="Create 3.3V regulator circuit with USB-C input")`
- **Capabilities**: 
  - Generate production-ready circuit-synth code
  - KiCad symbol/footprint verification with `/find-symbol` and `/find-footprint`
  - JLCPCB component availability checking
  - Manufacturing-ready designs with verified components

### **🔬 simulation-expert Agent**  
- **Expertise**: SPICE simulation and circuit validation
- **Usage**: `@Task(subagent_type="simulation-expert", description="Validate filter", prompt="Simulate and optimize this low-pass filter circuit")`
- **Capabilities**:
  - Professional SPICE analysis (DC, AC, transient)
  - Hierarchical circuit validation
  - Component value optimization
  - Performance analysis and reporting

### **🏭 jlc-parts-finder Agent**
- **Expertise**: JLCPCB component sourcing and manufacturing optimization
- **Usage**: `@Task(subagent_type="jlc-parts-finder", description="Find STM32", prompt="Find STM32 with 3 SPIs available on JLCPCB")`
- **Capabilities**:
  - Real-time JLCPCB stock and pricing data
  - STM32 peripheral search with modm-devices integration
  - Component alternatives and substitutions
  - Manufacturing constraints and DFM guidance

### **⚙️ component-guru Agent**
- **Expertise**: Component sourcing and manufacturing optimization specialist
- **Usage**: `@Task(subagent_type="component-guru", description="Optimize BOM", prompt="Optimize component selection for cost and availability")`
- **Capabilities**:
  - Multi-supplier component sourcing (JLCPCB, DigiKey)
  - BOM optimization for cost and availability
  - Component lifecycle and obsolescence management
  - Supplier-specific manufacturing constraints

## 🚀 Agent-First Design Philosophy

**Circuit-synth is designed to be used with and by AI agents** for intelligent circuit design.

### **Natural Language → Working Code**
Describe what you want, get production-ready circuit-synth code:

```
👤 "Design a motor controller with STM32, 3 half-bridges, and CAN bus"

🤖 Claude (using circuit-architect agent):
   ✅ Coordinates power, digital, and CAN domains
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
3. **Multi-Agent Workflows**: Agents collaborate (circuit-architect → circuit-synth → simulation-expert)

**Examples:**
```
# Design and validate workflow
👤 "Create and simulate a buck converter for 5V→3.3V@2A"

# Component search workflow  
👤 "Find a low-noise op-amp for audio applications, check JLCPCB stock"

# Hierarchical design workflow
👤 "Design ESP32 IoT sensor node with power management and wireless"
```

## 🎛️ Circuit Validation System

**NEW FEATURE: Circuit Quality Assurance**

The validation system provides automatic quality checking and improvement for circuit code:

### Core Functions
```python
from circuit_synth.validation import validate_and_improve_circuit, get_circuit_design_context

# Validate and fix circuit code automatically
code, is_valid, status = validate_and_improve_circuit(circuit_code)

# Get comprehensive design context for better generation
context = get_circuit_design_context("esp32")  # or "power", "analog", etc.
```

### Available Commands
- `/generate-validated-circuit <description> [type]` - Generate circuit with quality assurance
- `/validate-existing-circuit` - Check and improve existing circuit code

### What It Validates
1. **Syntax errors** - Catches Python syntax issues
2. **Missing imports** - Automatically fixes circuit_synth imports
3. **Runtime execution** - Ensures code actually runs
4. **Circuit structure** - Validates @circuit decorator usage

### Example Usage
```bash
# Generate validated ESP32 circuit
/generate-validated-circuit "ESP32 with USB-C power" mcu

# Validate code you wrote manually
/validate-existing-circuit
```

## 🔧 Circuit Debugging System

**NEW FEATURE: AI-Powered PCB Troubleshooting**

The debugging system helps diagnose and fix hardware issues with intelligent analysis:

### Core Functions
```python
from circuit_synth.debugging import CircuitDebugger, DebugSession

# Start debugging session
debugger = CircuitDebugger()
session = debugger.start_session("my_board", "v1.0")

# Add symptoms and measurements
session.add_symptom("Board not powering on")
session.add_measurement("VCC_3V3", 0, "V")

# Analyze issues
issues = debugger.analyze_symptoms(session)

# Get troubleshooting guidance
suggestions = debugger.suggest_next_test(session)
```

### CLI Tool
```bash
# Interactive debugging
uv run python -m circuit_synth.tools.debug_cli --interactive

# Or single commands
uv run python -m circuit_synth.tools.debug_cli start my_board --version 1.0
uv run python -m circuit_synth.tools.debug_cli symptom "No power LED"
uv run python -m circuit_synth.tools.debug_cli analyze
```

### Features
- **Symptom Analysis**: Categorizes issues by domain (power, digital, analog, RF)
- **Pattern Recognition**: Matches symptoms to historical debugging sessions
- **Test Guidance**: Systematic troubleshooting trees for common issues
- **Knowledge Base**: Learns from past debugging sessions
- **Equipment Guidance**: Recommends appropriate test equipment and procedures

## 🏗️ Circuit Generation from Single Prompt Workflow

**NEW: Fast circuit generation workflow for complete projects**

### Quick Circuit Generation
For creating complete circuit projects from natural language prompts, use:
```
@Task(subagent_type="circuit-project-creator", description="Generate circuit project", prompt="make a circuit board with stm32 with 3 spi peripherals with 1 imu on each spi, add a usb-c")
```

The workflow automatically:
- Analyzes requirements and selects appropriate components
- Generates hierarchical circuit-synth Python code  
- Validates code execution with `uv run main.py`
- Fixes syntax errors automatically (max 3 attempts)
- Creates complete project directory with documentation

**Performance**: Under 3 minutes total (3x faster with Haiku models)
**Success Rate**: 95% for common circuit types

### New Agents Available
- **circuit-project-creator**: Master orchestrator for complete workflows
- **circuit-validation-agent**: Tests generated code execution  
- **circuit-syntax-fixer**: Fixes errors while preserving design intent

## 💡 STM32 Peripheral Search Pattern (HIGHEST PRIORITY)

**CRITICAL: Fast STM32 component search for immediate results**

When you ask questions like:
- "find stm32 mcu that has 3 spi's and is available on jlcpcb"
- "stm32 with 2 uarts available on jlc" 
- "find stm32 with usb and 4 timers in stock"

**Use the jlc-parts-finder agent for instant results:**

```python
from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query

# Check if this is an STM32 peripheral query first
response = handle_stm32_peripheral_query(user_query)
if response:
    return response  # Direct answer - no complex workflow needed
```

**Detection Pattern:**
- Contains: stm32 + peripheral (spi/uart/i2c/usb/can/adc/timer/gpio) + availability (jlcpcb/jlc/stock)
- This workflow gives answers in 30 seconds vs 4+ minutes with other approaches

**Why this matters:**
- We have precise STM32 pin data via modm-devices integration
- JLCPCB caching prevents repeated API calls
- KiCad symbol verification ensures working results
- User gets exactly what they asked for quickly

## 📖 Circuit-Synth Specific Knowledge

### Core Components and Patterns

**Component Creation:**
```python
# Standard component pattern
component = Component(
    symbol="Library:SymbolName",        # Use /find-symbol to locate
    ref="U",                           # Reference prefix (U, R, C, etc.)
    footprint="Library:FootprintName", # Use /find-footprint to locate
    value="optional_value"             # For passives (resistors, caps)
)
```

**Net Management:**
```python
# Create nets for connections
VCC_3V3 = Net('VCC_3V3')  # Descriptive names
GND = Net('GND')

# Connect components to nets
component["pin_name"] += net_name
component[1] += VCC_3V3  # Pin numbers for simple components
```

**Circuit Decorators:**
```python
@circuit(name="circuit_name")
def my_circuit():
    """Docstring becomes schematic annotation"""
    # Circuit implementation
    return circuit  # Optional explicit return
```

### Common Libraries and Footprints

**Microcontrollers:**
- ESP32: `RF_Module:ESP32-S3-MINI-1`
- STM32: `MCU_ST_STM32F4:STM32F407VETx` (use /find-symbol STM32)
- Arduino: `MCU_Module:Arduino_UNO_R3`

**Passives:**
- Resistors: `Device:R` with footprints like `Resistor_SMD:R_0603_1608Metric`
- Capacitors: `Device:C` with footprints like `Capacitor_SMD:C_0603_1608Metric`
- Inductors: `Device:L` with appropriate footprints

**Connectors:**
- USB-C: `Connector:USB_C_Receptacle_*` (search with /find-symbol)
- Headers: `Connector_Generic:Conn_01x*` or `Conn_02x*`
- Power jacks: `Connector:Barrel_Jack_*`

### KiCad Integration Best Practices

**Symbol and Footprint Naming:**
- Always use full library:name format
- Verify symbols exist before using (run /find-symbol first)
- Match footprint to component package exactly

**Net Naming Conventions:**
- Power nets: `VCC_5V`, `VCC_3V3`, `GND`
- Signal nets: `USB_DP`, `USB_DM`, descriptive names
- Avoid generic names like `Net1`, `Net2`

**Reference Designators:**
- Follow standard conventions: U (ICs), R (resistors), C (capacitors), L (inductors), J (connectors)
- Let circuit-synth auto-assign numbers: `ref="U"` becomes `U1`, `U2`, etc.

### Common Patterns

**Power Supply Design:**
```python
# Voltage regulator with decoupling
vreg = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
cap_in = Component(symbol="Device:C", ref="C", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
cap_out = Component(symbol="Device:C", ref="C", value="22uF", footprint="Capacitor_SMD:C_0805_2012Metric")
```

**USB Interface:**
```python
usb_conn = Component(symbol="Connector:USB_C_Receptacle_USB2.0", ref="J", footprint="Connector_USB:USB_C_Receptacle_*")
# Connect VBUS, GND, D+, D- appropriately
```

### Troubleshooting Common Issues

**Symbol/Footprint Not Found:**
- Use /find-symbol and /find-footprint commands
- Check exact spelling and capitalization
- Verify library names match KiCad standard libraries

**Net Connection Problems:**
- Ensure pin names match exactly (case sensitive)
- Use integers for simple component pins: `component[1]`, `component[2]`
- Use strings for named pins: `component["VCC"]`, `component["GND"]`

**KiCad Generation Issues:**
- Check that all components have valid symbols and footprints
- Verify net connections are complete (no unconnected pins)
- Ensure reference designators are unique and follow conventions

## 🔗 JSON-Centric Architecture

Circuit-synth uses **JSON as the canonical intermediate representation** for all circuit data. This is critical to understand:

### Data Flow
```
Python Circuit Code ←→ JSON (Central Format) ←→ KiCad Files
```

- **Python → JSON**: `circuit.to_dict()` or `circuit.generate_json_netlist()`
- **JSON → KiCad**: Internal JSON processing generates .kicad_* files
- **KiCad → JSON**: Parser extracts circuit structure to JSON format
- **JSON → Python**: `json_to_python_project` generates Python code

### Key Points
1. **Hierarchical circuits are stored as nested JSON** with subcircuits preserved
2. **Round-trip conversion is lossless** - no information lost in any direction
3. **JSON is the single source of truth** - all conversions go through JSON
4. **One JSON format** - consistent structure for all operations

### Working with JSON
```python
# Export circuit to JSON
circuit.generate_json_netlist("my_circuit.json")

# Load circuit from JSON
from circuit_synth.io import load_circuit_from_json_file
circuit = load_circuit_from_json_file("my_circuit.json")

# KiCad generation uses JSON internally
circuit.generate_kicad_project("my_project")  # Creates temp JSON, then KiCad files
```

## 🎯 Best Practices

### **Component Selection Priority**
1. **JLCPCB availability first** - Always check stock levels with agents
2. **Standard packages** - Prefer common footprints (0603, 0805, LQFP)
3. **Proven components** - Use established parts with good track records

### **Circuit Organization**
- **Hierarchical design** - Use subcircuits for complex designs
- **Clear interfaces** - Define nets and connections explicitly  
- **Manufacturing focus** - Design for assembly and testing

### **AI Agent Usage**
- **Start with circuit-architect** for complex multi-step projects
- **Use circuit-synth** for component selection and code generation
- **Use simulation-expert** for validation and optimization
- **Use jlc-parts-finder** for sourcing and alternatives

## 🚀 Getting Help

- Use **natural language** to describe what you want to build
- **Be specific** about requirements (voltage, current, package, etc.)
- **Ask for alternatives** when components are out of stock
- **Request validation** for critical circuits before manufacturing

**Example project requests:**
```
👤 "Design ESP32 IoT sensor node with LoRaWAN, solar charging, and environmental sensors"
👤 "Create USB-C PD trigger circuit for 20V output with safety protection" 
👤 "Build motor controller with STM32, 3 half-bridges, CAN bus, and current sensing"
```

---

**This project is optimized for AI-powered circuit design with Claude Code!** 🎛️