# PRD: Interactive CLI for cs-new-project

**Status**: Draft
**Author**: Claude Code
**Created**: 2025-10-22
**Last Updated**: 2025-10-22

---

## Executive Summary

Transform `cs-new-project` from a one-size-fits-all command into an interactive CLI that generates tailored circuit-synth projects. Users will select from simple starter circuits and optionally add complex examples, creating a learning path from beginner to advanced.

**Key Changes:**
- Default project: Simple, educational circuit (e.g., resistor divider)
- Interactive selection of base circuit and optional examples
- Quick-start mode for experienced users
- Clear separation between learning examples and production templates

---

## Problem Statement

### Current Issues

1. **Overwhelming for beginners**: `cs-new-project` currently generates a complex ESP32-C6 dev board with multiple subcircuits, which is intimidating for new users
2. **Memory-bank complexity**: Generated projects include memory-bank directories and config that aren't needed
3. **No customization**: Users get the same project regardless of their needs or skill level
4. **Unclear learning path**: No progression from simple to complex circuits

### User Pain Points

**Beginner User:**
> "I just ran `cs-new-project` and got a complex ESP32 board with USB, power supply, debug headers... I just wanted to understand the basics first."

**Intermediate User:**
> "I need a clean starting point for my STM32 project. I don't want to delete all the ESP32 example code first."

**Advanced User:**
> "I know what I'm doing. I wish there was a `--minimal` flag to skip all the prompts and examples."

---

## Goals and Objectives

### Primary Goals

1. **Lower barrier to entry**: New users get simple, educational circuits that teach circuit-synth fundamentals
2. **Support skill progression**: Clear path from beginner examples to complex hierarchical designs
3. **Enable customization**: Users choose what examples they want in their project
4. **Maintain power-user efficiency**: Quick-start mode for experienced users

### Success Metrics

- **Beginner engagement**: 80%+ of new users can run the default example within 5 minutes
- **Learning progression**: Users who start with simple circuits have 2x higher retention
- **Satisfaction**: 90%+ positive feedback on project setup experience
- **Time to first circuit**: Reduce from 15 minutes to <3 minutes for simple projects

---

## User Personas

### 1. **Alex - The Beginner**
- **Background**: Software engineer new to hardware design
- **Goal**: Learn circuit design basics without overwhelming complexity
- **Pain Point**: Current ESP32 example is too complex to understand
- **Needs**: Simple, well-commented examples with clear explanations

### 2. **Jordan - The Intermediate User**
- **Background**: Hobbyist with some PCB design experience
- **Goal**: Build specific circuits (e.g., STM32 dev board) with good examples
- **Pain Point**: Wants relevant examples, not one-size-fits-all
- **Needs**: Choice of base circuits and relevant additional examples

### 3. **Sam - The Power User**
- **Background**: Professional hardware engineer
- **Goal**: Quickly bootstrap new projects with minimal setup
- **Pain Point**: Interactive prompts slow them down
- **Needs**: `--quick` flag to skip all prompts

---

## User Stories

### Beginner Path

**Story 1: First-time user wants to learn**
```
As a new user
I want to generate a simple circuit example
So that I can understand circuit-synth basics without feeling overwhelmed

Acceptance Criteria:
- Default selection is a simple resistor divider or LED circuit
- Code is well-commented with explanations
- Example runs successfully with `uv run python circuit-synth/main.py`
- Generated KiCad project opens without errors
```

**Story 2: Progressive learning**
```
As a beginner who completed the basic example
I want to generate more complex examples incrementally
So that I can build my skills step-by-step

Acceptance Criteria:
- Can re-run `cs-new-project` to add examples to existing project
- Examples show increasing complexity (basic → intermediate → advanced)
- Each example includes comments explaining new concepts
```

### Intermediate Path

**Story 3: Project-specific setup**
```
As an intermediate user starting a USB project
I want to select USB-related examples
So that I have relevant reference code in my project

Acceptance Criteria:
- Can select USB-C circuit example during setup
- Can deselect irrelevant examples (ESP32, STM32, etc.)
- Generated project includes only selected examples
```

**Story 4: Multiple example selection**
```
As an intermediate user building an IoT device
I want to select multiple relevant examples
So that I have reference implementations for all subsystems

Acceptance Criteria:
- Can select ESP32 + Power Supply + USB-C examples
- Each example is in its own file in circuit-synth/ directory
- Examples can be imported and modified for actual project
```

### Power User Path

**Story 5: Quick minimal setup**
```
As an experienced user
I want to skip all prompts and get a minimal project
So that I can start coding immediately

Acceptance Criteria:
- `cs-new-project --quick` creates minimal project without prompts
- Only includes basic main.py with simple circuit
- No examples, just clean template structure
- Setup completes in <5 seconds
```

**Story 6: Command-line customization**
```
As a power user
I want to specify my project configuration via CLI flags
So that I can script project creation

Acceptance Criteria:
- `cs-new-project --base led --examples esp32,usb` works non-interactively
- All options available via flags
- CI/CD friendly (no interactive prompts if flags provided)
```

---

## Functional Requirements

### FR1: Interactive CLI Interface

**FR1.1 Base Circuit Selection**
- MUST present 3-5 base circuit options:
  1. **Resistor Divider** (5V → 3.3V logic level shifter) - Default, beginner-friendly
  2. **LED Blinker** (LED + current limiting resistor)
  3. **Voltage Regulator** (AMS1117-3.3 with decoupling)
  4. **Minimal/Empty** (blank template with @circuit decorator only)

- MUST use `rich` library for visual selection menu
- MUST highlight default option (Resistor Divider)
- MUST show brief description for each option
- MUST validate selection before proceeding

**FR1.2 Optional Examples Selection**
- SHOULD present complex examples as optional additions:
  1. **ESP32-C6 Dev Board** (current complex example)
  2. **STM32 Minimal Board** (basic STM32 + USB + debug)
  3. **USB-C Basic Circuit** (USB-C connector + CC resistors)
  4. **Power Supply Module** (5V/3.3V dual rail supply)

- MUST support multiple selection (checkboxes)
- MUST allow selecting zero examples (skip all)
- SHOULD show estimated complexity for each example

**FR1.3 Configuration Options**
- MUST ask: "Include Claude AI agents?" (default: Yes)
- MUST ask: "Include KiCad plugins setup?" (default: No)
- SHOULD ask: "Developer mode?" (default: No, shows dev commands/agents)

**FR1.4 Preview and Confirmation**
- MUST show summary of selections:
  ```
  📋 Project Summary:
     Base circuit: Resistor Divider
     Examples: ESP32-C6, USB-C
     Claude agents: Yes
     KiCad plugins: No
     Developer mode: No

  ✅ Create project? (y/n):
  ```

### FR2: Quick Start Mode

**FR2.1 Fast Setup**
- MUST support `--quick` flag for minimal setup
- MUST skip all interactive prompts
- MUST create resistor divider example only
- MUST include Claude agents by default
- MUST complete in <5 seconds

**FR2.2 Flag-based Configuration**
- MUST support `--base [resistor|led|regulator|minimal]`
- MUST support `--examples esp32,stm32,usb,power` (comma-separated)
- MUST support `--no-agents` to skip Claude setup
- MUST support `--developer` for dev mode
- MUST be CI/CD friendly (non-interactive when flags provided)

### FR3: Template System

**FR3.1 Base Circuit Templates**
Each base circuit MUST include:
- Single `main.py` file with complete working circuit
- Inline comments explaining every component and connection
- Reference to circuit-synth documentation for concepts used
- Working KiCad generation code in `if __name__ == "__main__"`
- Component values and footprints verified for JLCPCB availability

**FR3.2 Example Circuit Templates**
Each optional example MUST:
- Be in separate file (e.g., `circuit-synth/esp32_dev_board.py`)
- Include complete documentation comments
- Work independently when run
- Use real, available components (JLCPCB verified)
- Include BOM in comments with estimated costs

**FR3.3 Template Organization**
```
src/circuit_synth/data/templates/
├── base_circuits/
│   ├── resistor_divider.py
│   ├── led_blinker.py
│   ├── voltage_regulator.py
│   └── minimal.py
├── example_circuits/
│   ├── esp32_dev_board/
│   │   ├── main.py
│   │   ├── esp32_subcircuit.py
│   │   ├── power_subcircuit.py
│   │   └── usb_subcircuit.py
│   ├── stm32_minimal.py
│   ├── usb_c_basic.py
│   └── power_supply_module.py
├── project_template/
│   ├── README.md (templated based on selections)
│   ├── CLAUDE.md (simplified, no memory-bank)
│   └── .claude/ (agents and commands)
```

### FR4: Documentation Generation

**FR4.1 README.md Customization**
- MUST generate README based on selected circuits
- MUST include explanation of selected base circuit
- MUST list and link to selected examples
- MUST include circuit-synth quick reference for features actually used
- MUST NOT include sections about unselected examples

**FR4.2 CLAUDE.md Simplification**
- MUST remove all memory-bank references
- MUST include only relevant agent guidance
- MUST provide examples matching selected circuits
- SHOULD include "Next Steps" based on selected complexity level

---

## Non-Functional Requirements

### NFR1: Performance
- Project creation MUST complete in <10 seconds (interactive mode)
- Project creation MUST complete in <5 seconds (quick mode)
- Template loading MUST not cause perceptible delay

### NFR2: Usability
- Interactive prompts MUST be clear and unambiguous
- Error messages MUST be helpful and actionable
- Default selections MUST work for 80% of beginner users
- CLI MUST be keyboard-navigable (arrow keys, space, enter)

### NFR3: Compatibility
- MUST work on macOS, Linux, and Windows
- MUST work with Python 3.10+
- MUST integrate with existing `uv` workflow
- MUST not break existing projects created with old `cs-new-project`

### NFR4: Maintainability
- Template files MUST be easy to update independently
- Adding new base circuits MUST require minimal code changes
- Adding new examples MUST be straightforward
- Code MUST follow existing circuit-synth patterns

---

## Technical Design

### Architecture

```
cs-new-project (CLI entry point)
├── Interactive CLI Layer (new)
│   ├── display_welcome()
│   ├── select_base_circuit() → BaseCircuit enum
│   ├── select_examples() → List[Example enum]
│   ├── select_configuration() → Config dict
│   └── show_confirmation() → bool
├── Template Manager (new)
│   ├── load_base_template(BaseCircuit) → str
│   ├── load_example_template(Example) → str
│   ├── generate_readme(selections) → str
│   └── generate_claude_md(selections) → str
├── Project Generator (existing, refactored)
│   ├── create_project_structure()
│   ├── copy_claude_setup()
│   └── finalize_project()
```

### Data Models

```python
from enum import Enum
from dataclasses import dataclass
from typing import List

class BaseCircuit(Enum):
    RESISTOR_DIVIDER = "resistor_divider"
    LED_BLINKER = "led_blinker"
    VOLTAGE_REGULATOR = "voltage_regulator"
    MINIMAL = "minimal"

class ExampleCircuit(Enum):
    ESP32_DEV_BOARD = "esp32_dev_board"
    STM32_MINIMAL = "stm32_minimal"
    USB_C_BASIC = "usb_c_basic"
    POWER_SUPPLY = "power_supply"

@dataclass
class ProjectConfig:
    base_circuit: BaseCircuit
    examples: List[ExampleCircuit]
    include_agents: bool = True
    include_kicad_plugins: bool = False
    developer_mode: bool = False

@dataclass
class CircuitTemplate:
    name: str
    description: str
    difficulty: str  # "beginner", "intermediate", "advanced"
    code: str
    estimated_bom_cost: str  # e.g., "$5-10"
```

### Interactive UI Components

Using `rich` library:

```python
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

def select_base_circuit() -> BaseCircuit:
    """Interactive base circuit selection with rich UI"""
    console = Console()

    # Display options table
    table = Table(title="Select Base Circuit")
    table.add_column("Option", style="cyan")
    table.add_column("Circuit", style="green")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Description")

    table.add_row(
        "1",
        "Resistor Divider",
        "Beginner ⭐",
        "5V → 3.3V logic level shifter (recommended)"
    )
    table.add_row(
        "2",
        "LED Blinker",
        "Beginner ⭐",
        "LED with current limiting resistor"
    )
    table.add_row(
        "3",
        "Voltage Regulator",
        "Intermediate ⭐⭐",
        "AMS1117-3.3 linear regulator with decoupling"
    )
    table.add_row(
        "4",
        "Minimal/Empty",
        "Advanced ⭐⭐⭐",
        "Blank template for experienced users"
    )

    console.print(table)

    choice = Prompt.ask(
        "Select base circuit",
        choices=["1", "2", "3", "4"],
        default="1"
    )

    mapping = {
        "1": BaseCircuit.RESISTOR_DIVIDER,
        "2": BaseCircuit.LED_BLINKER,
        "3": BaseCircuit.VOLTAGE_REGULATOR,
        "4": BaseCircuit.MINIMAL
    }

    return mapping[choice]
```

### Template Loading System

```python
from pathlib import Path
from typing import Dict
import importlib.resources

class TemplateManager:
    """Manages loading and rendering of circuit templates"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "data" / "templates"

    def load_base_circuit(self, circuit: BaseCircuit) -> str:
        """Load base circuit template code"""
        template_file = self.templates_dir / "base_circuits" / f"{circuit.value}.py"
        return template_file.read_text()

    def load_example(self, example: ExampleCircuit) -> Dict[str, str]:
        """Load example circuit (may be multiple files)"""
        example_dir = self.templates_dir / "example_circuits" / example.value

        if example_dir.is_dir():
            # Multi-file example
            return {
                f.name: f.read_text()
                for f in example_dir.glob("*.py")
            }
        else:
            # Single-file example
            example_file = example_dir.with_suffix(".py")
            return {example_file.name: example_file.read_text()}

    def render_readme(self, config: ProjectConfig) -> str:
        """Generate README.md based on selections"""
        # Load template and substitute variables
        template = self._load_template("README.md.jinja2")
        return template.render(
            base_circuit=config.base_circuit,
            examples=config.examples,
            has_examples=len(config.examples) > 0
        )

    def render_claude_md(self, config: ProjectConfig) -> str:
        """Generate CLAUDE.md based on selections"""
        template = self._load_template("CLAUDE.md.jinja2")
        return template.render(
            base_circuit=config.base_circuit,
            examples=config.examples
        )
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Tasks:**
1. Create data models (`BaseCircuit`, `ExampleCircuit`, `ProjectConfig`)
2. Implement `TemplateManager` class
3. Create template directory structure
4. Write resistor divider base template (well-commented, tested)
5. Write LED blinker base template
6. Update tests for new structure

**Deliverables:**
- Working template loading system
- 2 base circuit templates
- Unit tests for template manager

### Phase 2: Interactive CLI (Week 2)

**Tasks:**
1. Implement `select_base_circuit()` with rich UI
2. Implement `select_examples()` with multi-select
3. Implement `select_configuration()` for agents/plugins
4. Implement `show_confirmation()` preview
5. Add `--quick` flag support
6. Add CLI flag parsing for non-interactive mode

**Deliverables:**
- Complete interactive CLI
- Quick-start mode working
- Flag-based configuration working

### Phase 3: Project Generation (Week 2)

**Tasks:**
1. Refactor existing project generator to use `ProjectConfig`
2. Implement conditional file generation based on selections
3. Create README.md.jinja2 template
4. Create CLAUDE.md.jinja2 template
5. Update .claude setup to be config-driven
6. Test all combinations of selections

**Deliverables:**
- Projects generated based on user selections
- Custom README/CLAUDE.md per project
- All selection combinations tested

### Phase 4: Example Templates (Week 3)

**Tasks:**
1. Port ESP32-C6 example to new template system
2. Create STM32 minimal board template
3. Create USB-C basic template
4. Create power supply module template
5. Verify all examples work independently
6. Add BOM comments with pricing

**Deliverables:**
- 4 working example templates
- Documentation for each example
- JLCPCB component verification

### Phase 5: Testing & Documentation (Week 4)

**Tasks:**
1. Write integration tests for all user flows
2. Test on macOS, Linux, Windows
3. Update main documentation
4. Create tutorial video/guide
5. Add error handling and validation
6. Performance testing and optimization

**Deliverables:**
- Comprehensive test coverage
- Cross-platform verification
- User documentation
- Performance benchmarks

### Phase 6: Migration & Release (Week 5)

**Tasks:**
1. Add migration guide for existing users
2. Update release notes
3. Create deprecation notices if needed
4. Soft launch to beta testers
5. Collect feedback and iterate
6. Final release

**Deliverables:**
- Migration documentation
- Release announcement
- User feedback incorporated
- v2.0 release

---

## Base Circuit Templates Specification

### 1. Resistor Divider (Default)

**Purpose:** Teach net connections and basic component creation
**Complexity:** Beginner ⭐
**Components:** 2 resistors
**Concepts:** Nets, component creation, pin connections, voltage division

**Code Structure:**
```python
"""Resistor Divider - 5V to 3.3V Logic Level Shifter

This example demonstrates:
- Creating components with Device library
- Defining nets for electrical connections
- Connecting components to nets
- Calculating resistor values for voltage division

Voltage divider formula: Vout = Vin * (R2 / (R1 + R2))
For 5V → 3.3V: R1=1kΩ, R2=2kΩ
"""
from circuit_synth import Component, Net, circuit

@circuit(name="Resistor_Divider")
def resistor_divider():
    """5V to 3.3V voltage divider for logic level shifting"""

    # Create resistors from KiCad Device library
    # R1 = 1kΩ (upper resistor)
    r1 = Component(
        symbol="Device:R",
        ref="R",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # R2 = 2kΩ (lower resistor)
    r2 = Component(
        symbol="Device:R",
        ref="R",
        value="2k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Define electrical nets (connections)
    vin_5v = Net('VIN_5V')      # Input: 5V
    vout_3v3 = Net('VOUT_3V3')  # Output: 3.3V
    gnd = Net('GND')            # Ground reference

    # Connect resistors to form voltage divider
    r1[1] += vin_5v    # R1 pin 1 to 5V input
    r1[2] += vout_3v3  # R1 pin 2 to 3.3V output (junction)
    r2[1] += vout_3v3  # R2 pin 1 to 3.3V output (junction)
    r2[2] += gnd       # R2 pin 2 to ground

if __name__ == '__main__':
    # Generate KiCad project
    circuit = resistor_divider()
    circuit.generate_kicad_project(
        project_name="resistor_divider",
        placement_algorithm="simple",
        generate_pcb=True
    )

    print("✅ Resistor divider circuit generated!")
    print("📁 Open in KiCad: resistor_divider/resistor_divider.kicad_pro")
    print("📊 Expected output: 3.3V at VOUT_3V3 when VIN_5V = 5V")
```

**Learning Outcomes:**
- Understand `Component()` creation
- Learn net definition with `Net()`
- Master pin connections with `+=` operator
- See KiCad project generation workflow

**BOM:**
- 2x Resistors (0603): $0.02 @ JLCPCB
- **Total:** ~$0.02

---

### 2. LED Blinker

**Purpose:** Introduce component values and current limiting
**Complexity:** Beginner ⭐
**Components:** LED, resistor
**Concepts:** Component values, footprints, current limiting

**Code Structure:**
```python
"""LED Blinker - Basic LED Circuit with Current Limiting

This example demonstrates:
- Using LED components from Device library
- Calculating current limiting resistor values
- Working with different footprints
- Component value specification

LED specifications:
- Forward voltage (Vf): 2.0V (red LED)
- Forward current (If): 20mA
- Supply voltage (Vcc): 3.3V

Resistor calculation: R = (Vcc - Vf) / If = (3.3V - 2.0V) / 20mA = 65Ω
Standard value: 68Ω (allows ~19mA, safe for LED)
"""
from circuit_synth import Component, Net, circuit

@circuit(name="LED_Blinker")
def led_blinker():
    """Simple LED circuit with current limiting resistor"""

    # Create LED (red, common 0603 package)
    led = Component(
        symbol="Device:LED",
        ref="D",
        value="Red",
        footprint="LED_SMD:LED_0603_1608Metric"
    )

    # Create current limiting resistor
    # 68Ω limits current to ~19mA (safe for most LEDs)
    resistor = Component(
        symbol="Device:R",
        ref="R",
        value="68",  # 68 Ohms
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Define nets
    vcc_3v3 = Net('VCC_3V3')  # Power supply: 3.3V
    led_anode = Net('LED_ANODE')  # Connection between R and LED
    gnd = Net('GND')  # Ground

    # Connect components
    # Current flow: VCC → R → LED → GND
    resistor[1] += vcc_3v3     # R pin 1 to 3.3V supply
    resistor[2] += led_anode   # R pin 2 to LED anode
    led["A"] += led_anode      # LED anode (positive)
    led["K"] += gnd            # LED cathode (negative) to ground

if __name__ == '__main__':
    # Generate KiCad project
    circuit = led_blinker()
    circuit.generate_kicad_project(
        project_name="led_blinker",
        placement_algorithm="simple",
        generate_pcb=True
    )

    print("✅ LED blinker circuit generated!")
    print("📁 Open in KiCad: led_blinker/led_blinker.kicad_pro")
    print("💡 LED will light when VCC_3V3 is powered")
    print("⚡ Current draw: ~19mA at 3.3V")
```

**Learning Outcomes:**
- Work with specific component values
- Use named pins ("A", "K") vs numbered pins
- Understand current calculations
- Choose appropriate footprints

**BOM:**
- 1x LED (0603 red): $0.01 @ JLCPCB
- 1x 68Ω resistor (0603): $0.01 @ JLCPCB
- **Total:** ~$0.02

---

### 3. Voltage Regulator

**Purpose:** Introduce ICs and decoupling capacitors
**Complexity:** Intermediate ⭐⭐
**Components:** AMS1117-3.3, 2 capacitors
**Concepts:** IC components, decoupling, power supply design

**Code Structure:**
```python
"""Voltage Regulator - 5V to 3.3V Linear Regulator

This example demonstrates:
- Using IC components (3-pin voltage regulator)
- Decoupling capacitor placement
- Power supply circuit design
- Multiple components working together

Circuit: AMS1117-3.3 linear regulator
- Input: 5V (from USB or other source)
- Output: 3.3V regulated
- Max current: 1A
- Dropout voltage: ~1.2V

Decoupling capacitors:
- Input cap (C1): 10µF - stabilizes input voltage
- Output cap (C2): 22µF - reduces output ripple and improves transient response
"""
from circuit_synth import Component, Net, circuit

@circuit(name="Voltage_Regulator")
def voltage_regulator():
    """5V to 3.3V linear voltage regulator circuit"""

    # Voltage regulator IC - AMS1117-3.3
    # Common 3.3V LDO regulator, SOT-223 package
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    # Input decoupling capacitor - 10µF
    # Placed close to regulator input for stability
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Output decoupling capacitor - 22µF
    # Provides clean 3.3V output with low ripple
    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Define power nets
    vin_5v = Net('VIN_5V')      # Input: 5V unregulated
    vout_3v3 = Net('VOUT_3V3')  # Output: 3.3V regulated
    gnd = Net('GND')            # Ground plane

    # Connect voltage regulator
    # AMS1117 pinout: 1=GND(tab), 2=VOUT, 3=VIN
    vreg["GND"] += gnd      # Ground (also connected to tab)
    vreg["VOUT"] += vout_3v3  # 3.3V output
    vreg["VIN"] += vin_5v   # 5V input

    # Connect input capacitor
    # Placed between VIN and GND
    cap_in[1] += vin_5v
    cap_in[2] += gnd

    # Connect output capacitor
    # Placed between VOUT and GND
    cap_out[1] += vout_3v3
    cap_out[2] += gnd

if __name__ == '__main__':
    # Generate KiCad project
    circuit = voltage_regulator()
    circuit.generate_kicad_project(
        project_name="voltage_regulator",
        placement_algorithm="simple",
        generate_pcb=True
    )

    print("✅ Voltage regulator circuit generated!")
    print("📁 Open in KiCad: voltage_regulator/voltage_regulator.kicad_pro")
    print("⚡ Input: 5V → Output: 3.3V @ 1A max")
    print("📊 Efficiency: ~66% (linear regulator)")
    print("🌡️  Heat dissipation: 1.7W @ 1A load")
```

**Learning Outcomes:**
- Work with IC components (not just passives)
- Understand named pins on complex components
- Learn importance of decoupling capacitors
- Design complete power supply circuit

**BOM:**
- 1x AMS1117-3.3 (SOT-223): $0.10 @ JLCPCB
- 1x 10µF capacitor (0805): $0.02 @ JLCPCB
- 1x 22µF capacitor (0805): $0.03 @ JLCPCB
- **Total:** ~$0.15

---

### 4. Minimal/Empty Template

**Purpose:** Clean starting point for experienced users
**Complexity:** Advanced ⭐⭐⭐
**Components:** None
**Concepts:** Template structure only

**Code Structure:**
```python
"""Minimal Circuit Template

Empty template for experienced circuit-synth users.
This provides the basic structure without any example components.

Documentation: https://circuit-synth.readthedocs.io
"""
from circuit_synth import Component, Net, circuit

@circuit(name="My_Circuit")
def my_circuit():
    """
    Your circuit implementation goes here.

    Example workflow:
    1. Create components with Component(symbol=..., ref=..., footprint=...)
    2. Define nets with Net('NET_NAME')
    3. Connect components to nets with component[pin] += net
    4. Return locals() or specific dict of components/nets
    """

    # TODO: Add your components here
    # example_component = Component('Device:R', 'R', value='10k')

    # TODO: Define your nets
    # vcc = Net('VCC')
    # gnd = Net('GND')

    # TODO: Make connections
    # example_component[1] += vcc
    # example_component[2] += gnd

    pass

if __name__ == '__main__':
    # Generate KiCad project
    circuit = my_circuit()
    circuit.generate_kicad_project(
        project_name="my_circuit",
        placement_algorithm="hierarchical",  # or "simple"
        generate_pcb=True
    )

    print("✅ Circuit generated successfully!")
    print("📁 Open in KiCad: my_circuit/my_circuit.kicad_pro")
```

---

## Example Circuits Specification

### 1. ESP32-C6 Dev Board

**Purpose:** Production-quality hierarchical design example
**Complexity:** Advanced ⭐⭐⭐
**Files:** 6 files (main + 5 subcircuits)
**Concepts:** Hierarchical design, subcircuits, professional workflow

**Structure:**
- `main.py` - Top-level nets only
- `esp32_subcircuit.py` - Microcontroller with decoupling
- `power_subcircuit.py` - 5V→3.3V regulation
- `usb_subcircuit.py` - USB-C with CC resistors
- `debug_subcircuit.py` - SWD programming header
- `led_subcircuit.py` - Status LED

**BOM Cost:** ~$5-8 @ JLCPCB (100 units)

### 2. STM32 Minimal Board

**Purpose:** Alternative MCU platform example
**Complexity:** Advanced ⭐⭐⭐
**Files:** Single file
**Concepts:** STM32 peripherals, USB, debug interface

**Components:**
- STM32F411CEU6 (LQFP-48)
- AMS1117-3.3 regulator
- USB Micro connector
- 8MHz crystal + load caps
- Debug header (SWD)
- Boot select resistors

**BOM Cost:** ~$3-5 @ JLCPCB (100 units)

### 3. USB-C Basic Circuit

**Purpose:** Learn USB-C connector implementation
**Complexity:** Intermediate ⭐⭐
**Files:** Single file
**Concepts:** USB connectors, CC resistors, VBUS detection

**Components:**
- USB-C receptacle
- 2x 5.1kΩ CC resistors
- Optional ESD protection

**BOM Cost:** ~$0.50 @ JLCPCB (100 units)

### 4. Power Supply Module

**Purpose:** Dual-rail power supply design
**Complexity:** Intermediate ⭐⭐
**Files:** Single file
**Concepts:** Multiple regulators, power distribution

**Components:**
- 2x AMS1117 regulators (3.3V, 5V)
- Decoupling capacitors
- Power indicator LEDs
- Input protection

**BOM Cost:** ~$0.50 @ JLCPCB (100 units)

---

## CLI Flags Reference

```bash
# Interactive mode (default)
cs-new-project

# Quick start (minimal, no prompts)
cs-new-project --quick

# Specify base circuit non-interactively
cs-new-project --base resistor
cs-new-project --base led
cs-new-project --base regulator
cs-new-project --base minimal

# Add examples non-interactively
cs-new-project --base led --examples esp32,usb

# Skip Claude agents
cs-new-project --no-agents

# Developer mode (includes dev commands/agents)
cs-new-project --developer

# Combine flags
cs-new-project --quick --developer --no-agents

# Skip KiCad check
cs-new-project --skip-kicad-check
```

---

## Migration Plan

### For Existing Users

**Option 1: Keep Current Behavior (Recommended)**
- Existing projects work unchanged
- Old `cs-new-project` command still works via compatibility mode
- Warning message: "Using legacy project template. Try new interactive mode!"

**Option 2: Explicit Legacy Flag**
- `cs-new-project --legacy` creates old ESP32 complex project
- Default switches to new interactive mode
- Migration guide in documentation

**Option 3: Hard Break (Not Recommended)**
- Remove old template entirely
- All users must use new system
- Provide clear migration documentation

**Recommendation:** Option 1 with automatic detection:
```python
if Path('.claude').exists():
    console.print("⚠️  Existing project detected - adding examples only")
    # Add examples to existing project
else:
    # New project - show interactive CLI
    run_interactive_setup()
```

---

## Testing Strategy

### Unit Tests

1. **Template Loading**
   - All base templates load successfully
   - All example templates load successfully
   - Invalid template names raise errors

2. **CLI Parsing**
   - Flags parsed correctly
   - Invalid flags show help
   - Flag combinations work as expected

3. **Project Generation**
   - Correct files created for each selection
   - README matches selections
   - CLAUDE.md matches selections

### Integration Tests

1. **User Flows**
   - Beginner flow: resistor divider only
   - Intermediate flow: LED + ESP32 example
   - Power user flow: minimal + all examples
   - Quick start flow

2. **Cross-Platform**
   - macOS (Homebrew KiCad + standard)
   - Linux (apt/dnf KiCad)
   - Windows (standard KiCad install)

3. **Generated Projects**
   - All generated main.py files run without errors
   - KiCad projects open successfully
   - All BOMs accurate

### Manual Testing Checklist

- [ ] Interactive UI looks good in terminal
- [ ] Arrow key navigation works
- [ ] Space/Enter selection works
- [ ] Color highlighting clear
- [ ] Help text understandable
- [ ] Error messages helpful
- [ ] Preview confirmation accurate
- [ ] Quick mode completes in <5s
- [ ] All base circuits generate working KiCad projects
- [ ] All examples generate working KiCad projects

---

## Success Criteria

### Launch Criteria

- [ ] All base circuit templates complete and tested
- [ ] All example templates complete and tested
- [ ] Interactive CLI works on macOS/Linux/Windows
- [ ] Quick mode works
- [ ] Flag-based mode works
- [ ] Documentation complete
- [ ] Migration guide written
- [ ] 90%+ test coverage
- [ ] Beta testing feedback incorporated

### Post-Launch Metrics

**Week 1:**
- 100+ new projects created
- <5% error rate
- User feedback survey: 80%+ satisfaction

**Month 1:**
- 500+ new projects created
- Beginner retention: 70%+ complete first circuit
- Support tickets: <10 related to setup

**Quarter 1:**
- 2000+ new projects created
- 50%+ choose non-default base circuits
- 30%+ add example circuits
- Feature request: <20% want old complex default back

---

## Future Enhancements

### Phase 2 Features

1. **Template Marketplace**
   - Community-contributed templates
   - `cs-add-template` command to install from GitHub
   - Rating/review system

2. **Smart Recommendations**
   - AI suggests examples based on base circuit
   - "Users who built X also added Y"

3. **Project Upgrading**
   - `cs-upgrade-project` to add examples to existing project
   - `cs-list-examples` to see available additions

4. **Custom Templates**
   - `cs-create-template` to save current project as template
   - Share templates with team

5. **Web UI**
   - Browser-based project configurator
   - Visual preview of circuits before generation
   - Download generated project as ZIP

---

## Open Questions

1. **Template Versioning**: How do we handle template updates? Should old templates remain available?
2. **Component Availability**: Should we validate JLCPCB availability during generation and warn if out of stock?
3. **KiCad Version**: Should templates target specific KiCad versions (7.0 vs 8.0)?
4. **Tutorial Mode**: Should there be a `--tutorial` flag that adds extra comments and explanations?
5. **Project Naming**: Should users be prompted for project name, or always use current directory?

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Templates become outdated | Medium | High | Automated testing against latest KiCad version |
| Users confused by too many options | Medium | Medium | Good defaults, clear descriptions, progressive disclosure |
| Breaking changes for existing users | High | Low | Compatibility mode, clear migration guide |
| Template code has bugs | High | Medium | Comprehensive testing, JLCPCB verification |
| Performance issues with large templates | Low | Low | Lazy loading, caching |
| Cross-platform UI issues | Medium | Medium | Test on all platforms, fallback to simple prompts |

---

## Appendix: User Research

### Survey Results (Hypothetical)

**Question: "What was your first experience with cs-new-project?"**
- 45%: "Too complex, overwhelming"
- 30%: "Just right, good examples"
- 15%: "Too simple, wanted more features"
- 10%: "Didn't understand the example code"

**Question: "What would improve your experience?"**
- 60%: "Simpler starting examples"
- 40%: "More choice in what's included"
- 30%: "Better documentation"
- 20%: "Video tutorials"

**Question: "Would you use an interactive setup wizard?"**
- 70%: "Yes, would be helpful"
- 20%: "Maybe, if it's fast"
- 10%: "No, prefer flags/config file"

---

## Conclusion

This PRD outlines a comprehensive redesign of `cs-new-project` to better serve users at all skill levels. By providing simple defaults with optional complexity, we create a clear learning path while maintaining power-user efficiency.

**Next Steps:**
1. Review and approve PRD
2. Begin Phase 1 implementation
3. Create first two base templates
4. Iterate based on internal testing

---

**Document Version:** 1.0
**Last Updated:** 2025-10-22
**Status:** Ready for Review
