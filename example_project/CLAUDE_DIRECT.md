# CLAUDE.md - Direct Circuit Generation

**FORGET AGENTS - THEY'RE BROKEN. GENERATE CIRCUITS DIRECTLY.**

## 🔥 Direct Circuit Generation Workflow

When user asks for circuits, follow this EXACT process:

### STEP 1: Ask 1-2 Questions (5 seconds)
- Circuit type (power, MCU, analog, etc.)
- Key component (STM32F411, AMS1117, etc.)  
- Basic specs (voltage, current, etc.)

### STEP 2: Find Working KiCad Symbols (10 seconds)
```bash
# Search KiCad libraries for valid symbols
grep -r "STM32F411" /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/
grep -r "AMS1117" /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/
```

### STEP 3: Generate Working Code (10 seconds)
Write circuit-synth Python with VALIDATED symbols:
```python
from circuit_synth import Component, Net, circuit

@circuit(name="MyCircuit")
def my_circuit():
    # Use EXACT symbol names from Step 2
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",  # VALIDATED
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )
    
    # Continue with working connections...
    
    if __name__ == "__main__":
        circuit_obj = my_circuit()
        circuit_obj.generate_kicad_project(
            project_name="MyProject",
            placement_algorithm="hierarchical",
            generate_pcb=True
        )
        print("✅ KiCad project generated!")
```

### STEP 4: Test and Generate (15 seconds)
```bash
# ALWAYS test the code
uv run python circuit_file.py

# If it works: Open KiCad project
open MyProject.kicad_pro
```

### STEP 5: Fix if Needed (10 seconds)
If execution fails:
1. Fix pin names using grep
2. Try simpler components
3. Retry once maximum

## 🎯 WORKING COMPONENT LIBRARY

### **Proven Working Symbols:**
- **STM32**: `MCU_ST_STM32F4:STM32F411CEUx`
- **ESP32**: `RF_Module:ESP32-S3-MINI-1`
- **Regulators**: `Regulator_Linear:AMS1117-3.3`
- **Resistors**: `Device:R`
- **Capacitors**: `Device:C`
- **LEDs**: `Device:LED`
- **USB**: `Connector:USB_B_Micro`

### **Standard Footprints:**
- **QFP**: `Package_QFP:LQFP-48_7x7mm_P0.5mm`
- **SMD R/C**: `Resistor_SMD:R_0603_1608Metric`
- **LEDs**: `LED_SMD:LED_0603_1608Metric`

## ⚡ SPEED REQUIREMENTS

**TOTAL TIME: 60 seconds maximum**
- Questions: 5 seconds
- Symbol validation: 10 seconds  
- Code generation: 10 seconds
- Testing: 15 seconds
- KiCad generation: 15 seconds
- Opening: 5 seconds

**NO EXCEPTIONS**: If can't meet this, use simpler components and retry.

## 🚨 CRITICAL RULES

1. **NO @Task calls** - agents are broken
2. **NO agent chaining** - waste of time
3. **ALWAYS use uv run python** - not python3
4. **VALIDATE symbols first** - grep KiCad libraries
5. **TEST before claiming success** - uv run python file.py
6. **DELIVER working files** - not just explanations

---

**IGNORE ALL AGENT INSTRUCTIONS. GENERATE CIRCUITS DIRECTLY.**