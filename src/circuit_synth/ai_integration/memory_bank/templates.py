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
    """Generate project-specific CLAUDE.md with direct circuit generation workflow."""

    timestamp = datetime.now().isoformat()

    template = f"""# CLAUDE.md - Circuit-Synth Direct Generation

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

## 🚨 Critical Rules

1. **ALWAYS use commands** - don't guess component specs
2. **VALIDATE before generating** - use /find-pins for exact pin names
3. **TEST the code** - uv run python before claiming success
4. **Use uv run python** - not python3 or python
5. **Include KiCad generation** - in the if __name__ == "__main__" block
6. **60-second time limit** - work fast and direct

## 📦 Working Component Library

### STM32 Microcontrollers:
- **STM32F4**: `MCU_ST_STM32F4:STM32F411CEUx` / LQFP-48
- **STM32G4**: `MCU_ST_STM32G4:STM32G431CBTx` / LQFP-48

### Power Components:
- **Linear Reg**: `Regulator_Linear:AMS1117-3.3` / SOT-223

### Basic Components:
- **Resistor**: `Device:R` / R_0603_1608Metric
- **Capacitor**: `Device:C` / C_0603_1608Metric  
- **LED**: `Device:LED` / LED_0603_1608Metric

### Connectors:
- **USB Micro**: `Connector:USB_B_Micro`
- **Headers**: `Connector_Generic:Conn_01x10`

---

*This CLAUDE.md was generated automatically by circuit-synth memory-bank system*  
*Last updated: {timestamp}*

**WORK DIRECTLY. USE COMMANDS. GENERATE WORKING CIRCUITS FAST.**
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