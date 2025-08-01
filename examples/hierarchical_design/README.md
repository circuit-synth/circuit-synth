# Hierarchical Circuit Design Example

This example demonstrates professional circuit design organization using Circuit-Synth, following software engineering best practices.

## 🏗️ Architecture Overview

```
hierarchical_design/
├── components.py      # 📦 Reusable component library
├── power_supply.py    # ⚡ 3.3V regulator circuit  
├── led_indicator.py   # 💡 Status LED circuits
├── main_board.py      # 🖥️  Complete system assembly
└── README.md          # 📚 This documentation
```

## 🎯 Key Principles Demonstrated

### 1. **Single Circuit Per File**
Each `.py` file contains one primary circuit function, making code easier to:
- Understand and maintain
- Test independently  
- Reuse across projects
- Debug when issues arise

### 2. **Component Library Pattern**
`components.py` defines standard parts that can be reused:

```python
# Standard 0603 resistors
R_1K = Component(symbol="Device:R", ref="R", value="1K", 
                footprint="Resistor_SMD:R_0603_1608Metric")

R_10K = Component(symbol="Device:R", ref="R", value="10K",
                 footprint="Resistor_SMD:R_0603_1608Metric")
```

### 3. **Hierarchical Composition**
Complex circuits are built from simpler building blocks:

```python
# main_board.py composes multiple subsystems
def esp32_development_board():
    # Power supply subsystem
    ldo_3v3_regulator(VIN_5V, VCC_3V3, GND)
    
    # Status LED subsystem  
    dual_status_leds(VCC_3V3, GND, POWER_LED, USER_LED)
    
    # Microcontroller subsystem
    # ... ESP32 connections
```

### 4. **Clear Interfaces**
Each circuit function has a well-defined interface:

```python
@circuit(name="ldo_3v3_regulator")
def ldo_3v3_regulator(vin, vout, gnd):
    """
    Args:
        vin: Input voltage net (5V typical)
        vout: Regulated 3.3V output net  
        gnd: Ground net
    """
```

## 🚀 Running the Examples

### Test Individual Circuits
```bash
# Test power supply independently
python -m examples.hierarchical_design.power_supply

# Test LED indicators independently  
python -m examples.hierarchical_design.led_indicator
```

### Generate Complete Board
```bash
# Generate the full ESP32 development board
python -m examples.hierarchical_design.main_board
```

## 📋 Generated Files

Running `main_board.py` creates:
- `esp32_dev_board.kicad_pro` - KiCad project file
- `esp32_dev_board.kicad_sch` - Schematic file
- `esp32_dev_board.kicad_pcb` - PCB layout file  
- `esp32_dev_board.json` - JSON netlist
- `esp32_dev_board.net` - KiCad netlist

## 💡 Benefits of This Approach

### **Maintainability**
- Easy to locate and fix issues
- Clear separation of concerns
- Modular testing capabilities

### **Reusability** 
- Components defined once, used everywhere
- Circuits can be shared between projects
- Standard patterns emerge naturally

### **Scalability**
- Add new circuits without affecting existing ones
- Complex systems remain manageable
- Team collaboration becomes easier

### **Professional Workflow**
- Matches software engineering practices
- Version control friendly
- Supports code review processes

## 🔧 Customization

### Adding New Components
Add to `components.py`:
```python
# Custom component definition
CUSTOM_IC = Component(
    symbol="Custom:MyIC", 
    ref="U",
    footprint="Package_QFP:TQFP-44_10x10mm_P0.8mm"
)
```

### Creating New Circuits  
Follow the pattern in existing files:
```python
@circuit(name="my_new_circuit")
def my_new_circuit(input_nets...):
    """Clear docstring explaining the circuit"""
    # Circuit implementation
    pass
```

### Integration with Main Board
Import and use in `main_board.py`:
```python
from .my_new_module import my_new_circuit

def esp32_development_board():
    # ... existing code ...
    my_new_circuit(net1, net2, net3)
```

This architecture scales from simple projects to complex multi-board systems while maintaining code quality and developer productivity.