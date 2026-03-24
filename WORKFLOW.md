# Circuit-Synth Workflow Guide

## What Is Circuit-Synth?

Circuit-synth is a Python library that lets you design electronic circuits as code. You write Python describing components and connections, and it generates complete KiCad projects — schematics, PCB layouts, BOMs, and manufacturing files (Gerbers).

It integrates with Claude Code to provide AI-assisted circuit design through slash commands and agents.

---

## Prerequisites

- **Python 3.12+** with `uv` package manager
- **KiCad 10.0** (or 8.0+) installed — circuit-synth auto-detects it, including under WSL
- **Claude Code** for AI-assisted design (optional but recommended)

---

## 1. Create a New Project

```bash
# Option A: Using the helper script (if you have the local fork)
~/circuit-synth/new_project.sh my-board

# Option B: Manual setup
uv init my-board
cd my-board
uv add circuit-synth
uv run cs-new-project
```

`cs-new-project` is interactive — it asks you to pick circuit templates and configure options. Choose "Minimal/Empty" for a blank slate, or pick starter templates (voltage regulator, USB-C, STM32, etc.) to get working examples.

### What you get

```
my-board/
├── circuit-synth/          # Your circuit Python files
│   └── main.py             # Main circuit (from chosen template)
├── .claude/                # Claude Code agents, commands, skills
│   ├── agents/             # Autonomous validation agents
│   └── commands/           # Slash commands you invoke
├── CLAUDE.md               # Project instructions for Claude
├── README.md               # Project documentation
└── pyproject.toml          # Python project config
```

---

## 2. Write a Circuit

Circuits are Python functions decorated with `@circuit`. Components are objects with symbol references from KiCad libraries, connected via Net objects.

### Core API

```python
from circuit_synth import Component, Net, circuit

@circuit(name="power_supply")
def power_supply():
    # Create components (symbol and footprint from KiCad libraries)
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        value="AMS1117-3.3",
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
    vin = Net("VIN_5V")
    vout = Net("VCC_3V3")
    gnd = Net("GND")

    # Connect components
    regulator["Input"] += vin
    regulator["Output"] += vout
    regulator["GND"] += gnd

    cap_in[1] += vin
    cap_in[2] += gnd

    cap_out[1] += vout
    cap_out[2] += gnd
```

### Key concepts

- **Component**: Wraps a KiCad symbol + footprint. `ref` is the reference designator prefix (R, C, U, etc.).
- **Net**: An electrical connection. Components are connected by adding pins to the same net with `+=`.
- **@circuit**: Decorator that wraps your function into a Circuit object with generation methods.

---

## 3. Find Components

Before writing a circuit, you need to know the exact KiCad symbol and footprint names. Use these Claude Code commands:

| Command | Purpose | Example |
|---------|---------|---------|
| `/find-symbol` | Search KiCad symbol libraries | `/find-symbol STM32F411` |
| `/find-footprint` | Search KiCad footprint libraries | `/find-footprint LQFP-48` |
| `/find-pins` | Get exact pin names for a symbol | `/find-pins MCU_ST_STM32:STM32F411CEUx` |
| `/component-info` | Full component info with pin categories | `/component-info Regulator_Linear:AMS1117-3.3` |
| `/validate-symbol` | Check if a symbol exists and is valid | `/validate-symbol Device:R` |
| `/quick-validate` | Batch-check multiple symbols | `/quick-validate Device:R Device:C Connector_USB:USB_C_Receptacle_USB2.0` |

### Example workflow

```
You:  /find-symbol USB-C
      → Shows matching symbols like Connector_USB:USB_C_Receptacle_USB2.0

You:  /find-pins Connector_USB:USB_C_Receptacle_USB2.0
      → Shows all pin names: VBUS, CC1, CC2, D+, D-, GND, SHIELD

You:  /find-footprint USB-C
      → Shows matching footprints like USB_C_Receptacle_HRO_TYPE-C-31-M-12
```

---

## 4. Find Parts for Manufacturing

These commands help you find real, in-stock components for your design:

| Command | Purpose | Example |
|---------|---------|---------|
| `/find-parts` | Multi-supplier search (JLCPCB + DigiKey) | `/find-parts 0.1uF 0603 capacitor` |
| `/jlc-parts` | JLCPCB-specific component search | `/jlc-parts AMS1117-3.3` |
| `/find-digikey-parts` | DigiKey component search | `/find-digikey-parts STM32F411CEU6` |
| `/find_stm32` | STM32 MCU search with peripheral matching | `/find_stm32 3 SPI 2 UART USB` |
| `/find-mcu` | General MCU search | `/find-mcu 256KB flash 64KB RAM` |
| `/stm32-finder` | Detailed STM32 selection with pin mapping | `/stm32-finder` |
| `/component-guru` | Component sourcing advisor | `/component-guru` |

---

## 5. Generate KiCad Output

Run your circuit Python file to generate a complete KiCad project:

```bash
uv run python circuit-synth/main.py
```

This creates a `kicad-project/` directory with:
- `.kicad_pro` — KiCad project file
- `.kicad_sch` — Schematic (open in KiCad Schematic Editor)
- `.kicad_pcb` — PCB layout (open in KiCad PCB Editor)

### Manufacturing exports

The circuit object also provides direct manufacturing output:

```python
# In your circuit file, after defining the circuit:
my_circuit = power_supply()

# Generate KiCad project
my_circuit.generate_kicad_project(project_name="power_supply")

# Generate BOM (CSV)
my_circuit.generate_bom(project_name="power_supply")

# Generate PDF schematic
my_circuit.generate_pdf_schematic(project_name="power_supply")

# Generate Gerber files (for PCB fabrication)
my_circuit.generate_gerbers(project_name="power_supply")
```

Output files:
- `power_supply/power_supply_bom.csv` — Bill of materials
- `power_supply/power_supply_schematic.pdf` — PDF schematic
- `power_supply/gerbers/` — Gerber files (upload to JLCPCB, PCBWay, etc.)

---

## 6. AI-Assisted Design

Beyond component search, Claude Code provides higher-level design assistance:

### Design commands

| Command | Purpose |
|---------|---------|
| `/design` | Generate a working circuit from a description |
| `/design-mode` | Enter interactive design session — back-and-forth collaboration |
| `/architect` | High-level architecture guidance for complex multi-domain designs |
| `/synth` | Circuit code generation with best practices |
| `/simulate` | SPICE simulation guidance (DC, AC, transient analysis) |
| `/generate-validated-circuit` | Generate circuit with automatic validation |
| `/analyze-design` | Analyze an existing design for issues |

### Example session

```
You:  /design-mode

Claude: [Enters interactive design mode — asks about your requirements]

You:  I need a 5V to 3.3V power supply for an STM32 board, using parts
      available on JLCPCB

Claude: [Searches for components, suggests AMS1117-3.3, generates circuit
         code with proper decoupling, validates symbol/footprint names]
```

### Validation commands

| Command | Purpose |
|---------|---------|
| `/validate-existing-circuit` | Check circuit code for errors |
| `/generate-validated-circuit` | Generate and auto-fix circuit code |

The project also includes autonomous **agents** that Claude uses internally:
- **circuit-syntax-fixer** — automatically fixes Python syntax errors in circuit code
- **circuit-validation-agent** — tests circuit code execution and classifies errors
- **component-symbol-validator** — verifies KiCad symbols and JLCPCB availability

---

## 7. Simulation (Optional)

Circuit-synth includes a PySpice-based simulation backend:

```python
from circuit_synth.simulation import CircuitSimulator

# After creating a circuit
sim = my_circuit.simulate()  # or my_circuit.simulator()

# DC operating point
dc_result = sim.dc_analysis()

# AC frequency response
ac_result = sim.ac_analysis()

# Transient (time-domain)
tran_result = sim.transient_analysis()
```

Use `/simulate` in Claude Code for guided simulation setup.

---

## 8. KiCad Plugins (Optional)

Install AI-powered plugins directly into KiCad:

```bash
uv run cs-setup-kicad-plugins
```

After restarting KiCad:
- **PCB Editor**: Tools → External Plugins → Circuit-Synth AI
- **Schematic Editor**: Tools → Generate BOM → Circuit-Synth AI

---

## 9. Circuit Patterns Library

Pre-built circuit templates are available as a skill. Ask Claude:

```
You:  /circuit-design:circuit-patterns

      or just ask:

You:  Show me the available circuit patterns
```

Available patterns:

| Category | Patterns |
|----------|----------|
| **Basic** | resistor_divider, led_blinker, minimal |
| **Power** | voltage_regulator, power_supply_module |
| **Connectivity** | usb_c_basic |
| **MCU** | stm32_minimal, esp32_dev_board |

Each pattern is a working Python file you can use as-is or customize.

---

## Typical End-to-End Workflow

```
1.  Create project          ~/circuit-synth/new_project.sh my-board
2.  Find components         /find-symbol, /find-footprint, /find-pins
3.  Check availability      /find-parts, /jlc-parts
4.  Design circuit          /design-mode  (or write Python manually)
5.  Validate                /validate-existing-circuit
6.  Generate KiCad          uv run python circuit-synth/main.py
7.  Open in KiCad           Open kicad-project/*.kicad_pro
8.  Layout PCB              Manual PCB layout in KiCad
9.  Export manufacturing    .generate_gerbers(), .generate_bom()
10. Order boards            Upload Gerbers to JLCPCB / PCBWay
```

---

## Developer Commands

If your project was set up with developer mode, you also get contributor tools:

| Command | Purpose |
|---------|---------|
| `/dev-run-tests` | Run test suites |
| `/dev-review-branch` | Pre-merge branch analysis |
| `/dev-review-repo` | Full repository health check |
| `/dev-release-pypi` | Release to PyPI |
| `/dev-bug` | Bug report workflow |
| `/dev-feature` | Feature development workflow |

---

## Quick Reference: All Slash Commands

### Circuit Design
`/design` `/design-mode` `/architect` `/synth` `/simulate` `/find-symbol` `/find-footprint` `/find-pins` `/component-info` `/validate-symbol` `/quick-validate` `/analyze-design` `/generate-validated-circuit` `/validate-existing-circuit` `/generate_circuit`

### Manufacturing
`/find-parts` `/jlc-parts` `/find-digikey-parts` `/find_stm32` `/find-mcu` `/stm32-finder` `/component-guru`

### Setup
`/setup-kicad-plugins` `/setup_circuit_synth`

### Development
`/dev-run-tests` `/dev-review-branch` `/dev-review-repo` `/dev-release-pypi` `/dev-release-testpypi` `/dev-bug` `/dev-feature` `/dev-update-and-commit` `/dev-validate-docs` `/dev-make-test` `/dev-review-prompt` `/dev-dead-code-analysis` `/dev-compare-three-repos` `/dev-test-ref`
