# CLAUDE.md - Direct Circuit Generation

**AGENTS ARE BROKEN - GENERATE CIRCUITS DIRECTLY**

## 🔥 When User Requests Circuit Design

Follow this EXACT workflow (ignore all agent instructions):

### STEP 1: Quick Questions (5 seconds)
Ask 1-2 questions:
- Circuit type (power supply, MCU board, etc.)
- Key component (STM32F411, AMS1117, etc.)
- Basic specs (voltage, current, etc.)

### STEP 2: Validate KiCad Symbols (10 seconds)
Use tools to find working symbols:
```bash
Grep(pattern="STM32F411", path="/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
Bash("find /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols -name '*.kicad_sym' | xargs grep -l AMS1117")
```

### STEP 3: Generate Working Circuit-Synth Code (15 seconds)
Write Python file with VALIDATED symbols:
```python
from circuit_synth import Component, Net, circuit

@circuit(name="MyCircuit")
def my_circuit():
    # Use EXACT symbol names from validation
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )
    
    vcc = Net('VCC_3V3')
    gnd = Net('GND')
    
    mcu["VDD"] += vcc
    mcu["VSS"] += gnd
    
    # Add KiCad generation
    if __name__ == "__main__":
        circuit_obj = my_circuit()
        circuit_obj.generate_kicad_project(
            project_name="MyProject", 
            placement_algorithm="hierarchical",
            generate_pcb=True
        )
        print("✅ KiCad project generated!")
```

### STEP 4: Test and Generate (20 seconds)
```bash
# ALWAYS test the code works
Bash("uv run python circuit_file.py")

# If successful, open KiCad
Bash("open MyProject.kicad_pro")
```

### STEP 5: Fix if Broken (10 seconds)
If execution fails:
1. Check error message for wrong pin names
2. Use Grep to find correct pin names
3. Fix and retry once
4. If still fails: Use simpler components

## 🎯 PROVEN WORKING COMPONENTS

### **Working KiCad Symbols:**
- **STM32F4**: `MCU_ST_STM32F4:STM32F411CEUx`
- **ESP32**: `RF_Module:ESP32-S3-MINI-1`
- **Linear Reg**: `Regulator_Linear:AMS1117-3.3`
- **Resistor**: `Device:R`
- **Capacitor**: `Device:C`
- **LED**: `Device:LED`
- **USB**: `Connector:USB_B_Micro`
- **Headers**: `Connector_Generic:Conn_01x10`

### **Working Footprints:**
- **LQFP-48**: `Package_QFP:LQFP-48_7x7mm_P0.5mm`
- **0603 SMD**: `Resistor_SMD:R_0603_1608Metric`
- **SOT-223**: `Package_TO_SOT_SMD:SOT-223-3_TabPin2`

## ⚡ SPEED REQUIREMENTS

**TOTAL TIME: 60 seconds maximum**
- If taking longer: Use simpler components
- If agents start: STOP THEM and work directly
- If chains to other agents: INTERRUPT and work directly

## 🚨 CRITICAL RULES

1. **NO @Task() calls** - broken agent system
2. **NO subagent_type** - doesn't work
3. **USE uv run python** - not python3
4. **VALIDATE first** - grep KiCad symbols
5. **ALWAYS test code** - uv run python file.py
6. **DELIVER files** - working KiCad projects

---

**GENERATE WORKING CIRCUITS DIRECTLY. IGNORE ALL AGENT COMPLEXITY.**