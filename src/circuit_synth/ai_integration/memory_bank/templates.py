"""
Memory-Bank File Templates

Standard templates for memory-bank markdown files with consistent formatting.
"""

from datetime import datetime
from typing import Any, Dict

DECISIONS_TEMPLATE = """# Design Decisions

*This file automatically tracks design decisions and component choices*

## Template Entry
**Date**: YYYY-MM-DD  
**Change**: Brief description of what changed  
**Commit**: Git commit hash  
**Rationale**: Why this change was made  
**Alternatives Considered**: Other options evaluated  
**Impact**: Effects on design, cost, performance  
**Testing**: Any validation performed  

---

"""

FABRICATION_TEMPLATE = """# Fabrication History

*This file tracks PCB orders, delivery, and assembly notes*

## Template Order
**Order ID**: Vendor order number  
**Date**: YYYY-MM-DD  
**Specs**: Board specifications (size, layers, finish, etc.)  
**Quantity**: Number of boards ordered  
**Cost**: Total cost including shipping  
**Expected Delivery**: Estimated delivery date  
**Status**: Order status and tracking information  
**Received**: Actual delivery date and quality notes  
**Assembly Notes**: Assembly process and any issues  

---

"""

TESTING_TEMPLATE = """# Testing Results

*This file tracks test results, measurements, and performance validation*

## Template Test
**Date**: YYYY-MM-DD  
**Test Type**: Power consumption, functional, stress, etc.  
**Commit**: Git commit hash of version tested  
**Setup**: Test equipment and configuration  
**Expected**: Predicted results  
**Actual**: Measured results  
**Status**: Pass/Fail/Marginal  
**Notes**: Observations and follow-up actions  

---

"""

TIMELINE_TEMPLATE = """# Project Timeline

*This file tracks project milestones, key events, and deadlines*

## Template Event
**Date**: YYYY-MM-DD  
**Event**: Milestone or significant event  
**Commit**: Related git commit hash  
**Impact**: Effects on project timeline or scope  
**Next Actions**: Required follow-up tasks  

---

"""

ISSUES_TEMPLATE = """# Known Issues

*This file tracks problems encountered, root causes, and solutions*

## Template Issue
**Date**: YYYY-MM-DD  
**Issue**: Brief description of the problem  
**Commit**: Git commit hash where issue was introduced/discovered  
**Symptoms**: How the issue manifests  
**Root Cause**: Technical reason for the issue  
**Workaround**: Temporary solution if available  
**Status**: Open/In Progress/Resolved  
**Resolution**: Final solution and verification  

---

"""


def generate_claude_md(project_name: str, boards: list = None, **kwargs) -> str:
    """Generate project-specific CLAUDE.md with comprehensive circuit-synth usage guidance."""

    timestamp = datetime.now().isoformat()

    template = f"""# CLAUDE.md - {project_name}

Circuit-synth project guidance for Claude Code AI assistant.

## 🎯 Project Structure

This is a **circuit-synth project** - Python code that generates professional KiCad PCB designs.

### Recommended File Organization

```
{project_name}/
├── main.py                    # Main circuit (nets only, coordinates subcircuits)
├── power_supply.py           # Power regulation subcircuit
├── mcu_subcircuit.py         # Microcontroller subcircuit
├── usb_interface.py          # USB connectivity subcircuit
├── led_indicators.py         # Status LEDs subcircuit
└── kicad-project/            # Generated KiCad files (auto-created)
    ├── {project_name}.kicad_pro
    ├── {project_name}.kicad_sch
    └── *.kicad_sch           # Hierarchical sheets
```

**Key Principle**: **One circuit per file** - keep circuits small and modular, just like you would functions.

## 🔧 Circuit-Synth Basics

### 1. Creating Components

```python
from circuit_synth import Component, Net, circuit

# Basic component with symbol, reference, and footprint
mcu = Component(
    symbol="MCU_ST_STM32F4:STM32F411CEUx",      # KiCad symbol
    ref="U",                                     # Reference prefix (U1, U2, etc.)
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm" # KiCad footprint
)

# Passive components include value
resistor = Component(
    symbol="Device:R",
    ref="R",
    value="10k",
    footprint="Resistor_SMD:R_0603_1608Metric"
)

capacitor = Component(
    symbol="Device:C",
    ref="C",
    value="100nF",
    footprint="Capacitor_SMD:C_0603_1608Metric"
)
```

### 2. Connecting Components with Nets

```python
# Create nets for electrical connections
vcc_3v3 = Net('VCC_3V3')
gnd = Net('GND')
usb_dp = Net('USB_DP')
usb_dm = Net('USB_DM')

# Connect components to nets using pin names
mcu["VDD"] += vcc_3v3       # Named pins (for complex ICs)
mcu["VSS"] += gnd
mcu["PA11"] += usb_dp
mcu["PA12"] += usb_dm

# Or use pin numbers (for simple components)
resistor[1] += vcc_3v3      # Pin 1 to VCC
resistor[2] += gnd          # Pin 2 to GND
```

### 3. Circuit Decorator Pattern

```python
@circuit(name="PowerSupply")
def power_supply_circuit():
    \"\"\"3.3V voltage regulator with decoupling capacitors\"\"\"

    # Create components
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Create nets
    vin = Net('VIN_5V')
    vout = Net('VCC_3V3')
    gnd = Net('GND')

    # Connect components
    vreg["VIN"] += vin
    vreg["VOUT"] += vout
    vreg["GND"] += gnd

    cap_in[1] += vin
    cap_in[2] += gnd

    cap_out[1] += vout
    cap_out[2] += gnd

    # Circuit decorator automatically returns the circuit object
```

### 4. Hierarchical Main Circuit

**IMPORTANT**: The main circuit should **only define nets and call subcircuits** - no components!

```python
from power_supply import power_supply_circuit
from mcu_subcircuit import mcu_subcircuit
from usb_interface import usb_interface_circuit

@circuit(name="{project_name}_Main")
def main_circuit():
    \"\"\"Main circuit - coordinates subcircuits with shared nets\"\"\"

    # Define shared nets (NO COMPONENTS HERE!)
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')

    # Instantiate subcircuits and pass nets
    power = power_supply_circuit()
    mcu = mcu_subcircuit(vcc_3v3, gnd, usb_dp, usb_dm)
    usb = usb_interface_circuit(usb_dp, usb_dm, gnd)

    # That's it! No components in main circuit.

if __name__ == "__main__":
    circuit = main_circuit()
    circuit.generate_kicad_project(
        project_name="{project_name}",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ KiCad project generated successfully!")
```

## 🔍 Finding KiCad Components

### Search for Symbols

```bash
# Use slash commands to find KiCad symbols
/find-symbol STM32F411
/find-symbol AMS1117
/find-symbol USB_C
```

### Search for Footprints

```bash
# Find footprints by package type
/find-footprint LQFP-48
/find-footprint SOT-223
/find-footprint 0603
```

### Get Exact Pin Names

```bash
# CRITICAL: Get exact pin names before connecting components
/find-pins MCU_ST_STM32F4:STM32F411CEUx
```

**Why this matters**: Pin names must match exactly (case-sensitive) or connections will fail.

## 🏭 Component Sourcing

### Check JLCPCB Availability

```bash
# Search for components available on JLCPCB
/find-parts --source jlcpcb AMS1117-3.3
/find-parts --source jlcpcb "STM32F411"
```

### STM32 Peripheral Search

```bash
# Find STM32 with specific peripherals
/find_stm32 "STM32 with USB and 3 SPIs available on JLCPCB"
/find_stm32 "STM32G4 with CAN and 2 UARTs in stock"
```

## ⚡ Running Your Circuit

```bash
# Execute the main circuit file
uv run python main.py

# Generated files appear in kicad-project/
# Open with: open kicad-project/{project_name}.kicad_pro
```

## 🎨 Best Practices

### Circuit Organization
1. **One circuit per file** - like functions, keep them focused and modular
2. **Main circuit coordinates** - only nets and subcircuit calls, no components
3. **Descriptive net names** - `VCC_3V3`, `USB_DP`, not `Net1`, `Net2`
4. **Standard reference prefixes** - U (ICs), R (resistors), C (capacitors), L (inductors), J (connectors)

### Component Selection
1. **Verify symbols exist** - use `/find-symbol` before creating components
2. **Check JLCPCB stock** - use `/find-parts` to ensure manufacturability
3. **Standard packages** - prefer common footprints (0603, 0805, LQFP, QFN)
4. **Get exact pins** - use `/find-pins` to get correct pin names

### Development Workflow
1. **Search for components** - verify symbols/footprints exist
2. **Write circuit code** - one subcircuit at a time
3. **Test generation** - run `uv run python main.py` frequently
4. **Open in KiCad** - verify layout and connections
5. **Iterate** - refine placement and routing

## 🚨 Common Issues

### "Symbol not found"
- Use `/find-symbol` to find exact symbol name
- Check spelling and library prefix (e.g., `Device:R` not just `R`)

### "Pin not found" or "Invalid pin name"
- Use `/find-pins` to get exact pin names (case-sensitive!)
- Named pins: `component["VDD"]` for ICs
- Numbered pins: `component[1]` for simple components

### Components overlap in KiCad
- Use `placement_algorithm="hierarchical"` for better automatic layout
- Adjust positions manually in KiCad after generation

### Import errors
- Always use `uv run python` (not `python` or `python3`)
- Ensure circuit-synth is installed: `uv add circuit-synth`

## 📚 Example Patterns

### Voltage Regulator Circuit
```python
@circuit(name="VoltageRegulator")
def voltage_regulator(vin_net, vout_net, gnd_net):
    vreg = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U",
                    footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    cap_in = Component(symbol="Device:C", ref="C", value="10uF",
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")

    vreg["VIN"] += vin_net
    vreg["VOUT"] += vout_net
    vreg["GND"] += gnd_net
    cap_in[1] += vin_net
    cap_in[2] += gnd_net
    cap_out[1] += vout_net
    cap_out[2] += gnd_net
```

### LED with Current Limiting Resistor
```python
@circuit(name="StatusLED")
def status_led(vcc_net, gnd_net):
    led = Component(symbol="Device:LED", ref="D",
                   footprint="LED_SMD:LED_0603_1608Metric")
    resistor = Component(symbol="Device:R", ref="R", value="330",
                        footprint="Resistor_SMD:R_0603_1608Metric")

    resistor[1] += vcc_net
    resistor[2] += led[1]  # LED anode
    led[2] += gnd_net      # LED cathode
```

### USB Connector
```python
@circuit(name="USB_Interface")
def usb_interface(dp_net, dm_net, gnd_net):
    usb = Component(symbol="Connector:USB_C_Receptacle_USB2.0", ref="J",
                   footprint="Connector_USB:USB_C_Receptacle_GCT_USB4085")

    usb["DP"] += dp_net
    usb["DM"] += dm_net
    usb["GND"] += gnd_net
    usb["VBUS"] += Net('VBUS_5V')
```

## 🤖 Getting Help from Claude

When asking for circuit design help:

1. **Be specific about requirements**:
   - "Design a 3.3V regulator with USB-C input"
   - "Create ESP32 board with WiFi and battery charging"

2. **Mention constraints**:
   - "Use components available on JLCPCB"
   - "Prefer 0603 passives"
   - "STM32 with at least 2 UARTs and SPI"

3. **Request verification**:
   - "Check if these symbols exist in KiCad"
   - "Verify JLCPCB stock for these components"

---

*Generated: {timestamp}*
*Circuit-synth: Professional PCB design with Python*
"""

    return template


# Template file mapping for easy access
TEMPLATE_FILES = {
    "decisions.md": DECISIONS_TEMPLATE,
    "fabrication.md": FABRICATION_TEMPLATE,
    "testing.md": TESTING_TEMPLATE,
    "timeline.md": TIMELINE_TEMPLATE,
    "issues.md": ISSUES_TEMPLATE,
}


def get_template(filename: str) -> str:
    """Get template content for a specific memory-bank file."""
    return TEMPLATE_FILES.get(filename, "")


def get_all_templates() -> Dict[str, str]:
    """Get all template files as a dictionary."""
    return TEMPLATE_FILES.copy()