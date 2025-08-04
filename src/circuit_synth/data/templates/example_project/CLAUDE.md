# CLAUDE.md

Project-specific guidance for Claude Code when working with this circuit-synth project.

## 🚀 Project Overview

This is a **circuit-synth project** for professional circuit design with AI-powered component intelligence.

## ⚡ Available Tools & Commands

### **Slash Commands**
- `/find-symbol STM32` - Search KiCad symbol libraries
- `/find-footprint LQFP` - Search KiCad footprint libraries  
- `/analyze-design` - Analyze circuit designs
- `/find_stm32` - STM32-specific component search
- `/generate_circuit` - Circuit generation workflows

### **Specialized Agents** 
- **orchestrator** - Master coordinator for complex projects
- **circuit-synth** - Circuit code generation and KiCad integration
- **simulation-expert** - SPICE simulation and validation
- **jlc-parts-finder** - JLCPCB component availability and sourcing
- **general-purpose** - Research and codebase analysis
- **code** - Software engineering and code quality

## 🏗️ Development Workflow

### **1. Component-First Design**
Always start with component availability checking:
```
👤 "Find STM32 with 3 SPIs available on JLCPCB"
👤 "Search for low-power op-amps suitable for battery applications"
```

### **2. Circuit Generation**
Use agents for code generation:
```
👤 @Task(subagent_type="circuit-synth", description="Create power supply", 
     prompt="Design 3.3V regulator circuit with USB-C input and overcurrent protection")
```

### **3. Validation & Simulation**
Validate designs before manufacturing:
```
👤 @Task(subagent_type="simulation-expert", description="Validate filter", 
     prompt="Simulate this low-pass filter and optimize component values")
```

## 🔧 Essential Commands

```bash
# Run the main example
uv run python circuit-synth/main.py

# Test the setup
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth ready!')"
```

## 🔌 KiCad Plugin Setup (Optional AI Integration)

Circuit-synth includes optional KiCad plugins for AI-powered circuit analysis:

```bash
# Install KiCad plugins (separate command)
uv run cs-setup-kicad-plugins
```

After installation and restarting KiCad:
- **PCB Editor**: Tools → External Plugins → "Circuit-Synth AI"  
- **Schematic Editor**: Tools → Generate Bill of Materials → "Circuit-Synth AI"

The plugins provide AI-powered BOM analysis and component optimization directly within KiCad!

## 🎯 Best Practices

### **Component Selection Priority**
1. **JLCPCB availability first** - Always check stock levels
2. **Standard packages** - Prefer common footprints (0603, 0805, LQFP)
3. **Proven components** - Use established parts with good track records

### **Circuit Organization**
- **Hierarchical design** - Use circuits for complex designs
- **Clear interfaces** - Define nets and connections explicitly  
- **Manufacturing focus** - Design for assembly and testing

### **AI Agent Usage**
- **Start with orchestrator** for complex multi-step projects
- **Use circuit-synth** for component selection and code generation
- **Use simulation-expert** for validation and optimization
- **Use jlc-parts-finder** for sourcing and alternatives

## 📚 Quick Reference

### **Component Creation**
```python
mcu = Component(
    symbol="RF_Module:ESP32-C6-MINI-1",
    ref="U",
    footprint="RF_Module:ESP32-C6-MINI-1"
)
```

### **Net Connections**
```python
vcc = Net("VCC_3V3")
mcu["VDD"] += vcc
```

### **Circuit Generation**
```python
@circuit(name="Power_Supply")
def power_supply():
    # Circuit implementation
    pass
```

## 🚀 Getting Help

- Use **natural language** to describe what you want to build
- **Be specific** about requirements (voltage, current, package, etc.)
- **Ask for alternatives** when components are out of stock
- **Request validation** for critical circuits before manufacturing

**Example project requests:**
```
👤 "Design ESP32 IoT sensor node with LoRaWAN, solar charging, and environmental sensors"
👤 "Create USB-C PD trigger circuit for 20V output with safety protection" 
👤 "Build ESP32-based IoT sensor node with WiFi, environmental sensors, and battery management"
```

---

**This project is optimized for AI-powered circuit design with Claude Code!** 🎛️
