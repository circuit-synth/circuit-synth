# circuit-synth

Python-based circuit design with KiCad integration and AI acceleration.

## What is Code-Based Circuit Design?

Circuit-synth brings software engineering practices to hardware design by letting you define circuits in Python code instead of clicking and dragging in a GUI. Your circuit becomes a program: testable, version-controlled, and composable.

### Traditional Visual CAD Workflow

In traditional EDA tools like KiCad, Altium, or Eagle, you:
- Click to place each component on a canvas
- Manually draw wires between pins
- Copy-paste repeated circuit patterns
- Track changes with screenshots or "before/after" project files
- Search through menus to find the right component symbol
- Manually verify that all connections are correct

This visual approach works for simple circuits, but becomes unwieldy as designs grow. Making systematic changes requires clicking through every instance. Reusing proven circuit blocks means copying between projects. Code review happens by comparing images or clicking through schematics.

### Code-Based Circuit Design

With circuit-synth, you write Python code:

```python
@circuit(name="Power_Supply")
def power_supply(vbus_in, vcc_3v3_out, gnd):
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    cap_in = Component(symbol="Device:C", ref="C", value="10uF")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF")

    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3_out
    regulator["GND"] += gnd

    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd
```

This circuit is now a **reusable function**. Need 5 power supplies? Call `power_supply()` five times. Need to change all decoupling caps? Update one line. Want to review what changed? `git diff` shows exactly which connections were modified.

### Key Benefits

**Version Control**: Every change is tracked with git. See exactly what changed, when, and why. Branch to try alternative designs. Merge proven improvements from other engineers.

**Modularity**: Build circuits from tested subcircuits. A USB-C power delivery circuit becomes a function you can reuse across projects. Change the implementation once, update everywhere.

**Code Review**: Team members review circuit changes like code. Diff shows "changed R1 from 10k to 4.7k" instead of visual schematic comparison. Catch mistakes before manufacturing.

**Automation**: Generate parametric designs. Write a function that creates a filter circuit for any cutoff frequency. Batch-generate variants for A/B testing.

**Testing**: Validate circuits with unit tests. Assert that power supply output is 3.3V ±5%. Run SPICE simulation in CI/CD. Catch regressions automatically.

**AI-Friendly**: LLMs can read and write circuit-synth code directly. Natural language → working circuit. This is one of the most powerful advantages of circuits-as-code: AI can understand, generate, and modify circuit designs through natural conversation.

**Refactoring**: Extract repeated patterns into functions. Rename nets across entire design. Reorganize hierarchy without manual rewiring.

### Claude Code Integration

Circuit-synth includes extensive Claude Code integration, making AI-assisted circuit design practical and powerful. When you create a circuit-synth project, you get:

**17 Specialized AI Agents**: Domain experts for different aspects of circuit design:
- `circuit-architect`: Complete system design from requirements
- `circuit-synth`: Generate production-ready Python code
- `simulation-expert`: SPICE analysis and optimization
- `component-search`: Real-time component sourcing across suppliers
- Plus agents for debugging, testing, FMEA analysis, and more

**18 Slash Commands**: Quick access to common operations:
- `/find-symbol STM32` - Search for KiCad symbols
- `/find-parts "0.1uF 0603"` - Component availability and pricing
- `/generate-validated-circuit "buck converter 5V to 3.3V"` - Natural language → working code
- `/analyze-fmea my_circuit.py` - Automated reliability analysis

**Natural Language Circuit Design**: Describe what you want in plain English, get working circuit-synth code:
```
You: "Design a USB-C power delivery circuit with 20V output and overcurrent protection"
Claude: [Generates complete power_supply.py with proper components, verified availability, and safety features]
```

This integration makes circuit-synth approachable for beginners while accelerating experts. The AI handles component selection, library lookups, and boilerplate code, letting you focus on design intent.

### When Code-Based Design Excels

- **Parametric designs**: Circuits that come in many variants (different voltages, channel counts, etc.)
- **Repeated blocks**: Designs with multiple identical subcircuits (multi-channel systems, arrays)
- **Team collaboration**: Multiple engineers working on the same design simultaneously
- **Rapid iteration**: Frequent design changes that would require tedious manual updates
- **Complex systems**: Large hierarchical designs that benefit from modular organization
- **AI-assisted design**: Generating circuits from specifications or optimizing existing designs

### Integration with KiCad

Circuit-synth is designed to work **with** existing KiCad workflows, not replace them. You can adopt circuit-synth at any stage of your design process.

**Bi-Directional Workflow**: Circuit-synth isn't just code → KiCad. It's fully bi-directional:
- **Start in Python**: Generate initial design from circuit-synth code
- **Start in KiCad**: Import existing .kicad_sch files into Python for modification
- **Iterate**: Make changes in either Python or KiCad, re-import/re-export as needed
- **Hybrid approach**: Use Python for hierarchical structure and repeated blocks, KiCad for custom layout

You can import an existing KiCad project, modify it in Python (add a subcircuit, change component values, etc.), and export back to KiCad. This makes circuit-synth a powerful tool for:
- Automating changes to existing designs
- Extracting reusable subcircuits from legacy projects
- Adding parametric generation to hand-drawn schematics
- Batch-updating component values across multiple projects

**After code generation**, use KiCad normally:
- Visual schematic editing and verification
- PCB layout and routing with KiCad's tools
- DRC, ERC, and 3D visualization
- Manufacturing export (Gerbers, drill files, BOM, pick-and-place)

You get the best of both worlds: code-based definition with visual refinement.

## Installation

```bash
uv add circuit-synth
# or
pip install circuit-synth
```

## Quick Start

```bash
# Create new project with ESP32-C6 example
cs-new-project

# Generate KiCad files
cd circuit-synth && uv run python circuit-synth/main.py
```

## Example Circuit

```python
from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply(vbus_in, vcc_3v3_out, gnd):
    """5V to 3.3V power regulation"""

    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    cap_in = Component(symbol="Device:C", ref="C", value="10uF",
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")

    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3_out
    regulator["GND"] += gnd

    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd

@circuit(name="Main_Circuit")
def main_circuit():
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')

    power_circuit = power_supply(vbus, vcc_3v3, gnd)

if __name__ == "__main__":
    circuit = main_circuit()
    circuit.generate_kicad_project("my_board")
```

## Features

- **Professional KiCad Output**: Generate complete .kicad_pro, .kicad_sch, .kicad_pcb projects
- **Hierarchical Design**: Build modular circuits with reusable subcircuits like software functions
- **Component Intelligence**: Real-time JLCPCB & DigiKey availability, pricing, and alternatives
- **AI-Powered Design**: Specialized Claude Code agents for automated circuit generation and optimization
- **SPICE Simulation**: Built-in circuit validation with DC, AC, and transient analysis
- **Version Control Friendly**: Text-based Python definitions work seamlessly with git
- **Manufacturing Ready**: Automatic BOM generation with verified component availability

## Configuration

```bash
# Enable detailed logging
export CIRCUIT_SYNTH_LOG_LEVEL=INFO  # ERROR, WARNING, INFO, DEBUG
```

## Claude Code Integration

Circuit-synth projects include specialized AI agents for automated design workflows.

### Available Slash Commands

```bash
# Component search
/find-symbol STM32              # Search KiCad symbol libraries
/find-footprint LQFP64          # Find component footprints
/find-parts "0.1uF 0603"        # Search across all suppliers
/find-stm32 "3 SPIs, USB"       # STM32-specific search

# Circuit generation
/generate-validated-circuit "ESP32 IoT sensor" mcu
/validate-existing-circuit

# Analysis
/analyze-fmea my_circuit.py     # Reliability analysis
```

### AI Agents

- **circuit-architect**: Complete system-level design and architecture planning
- **circuit-synth**: Generate production-ready circuit-synth Python code
- **simulation-expert**: SPICE simulation setup and performance optimization
- **component-search**: Multi-source component search with price/availability comparison
- **jlc-parts-finder**: Real-time JLCPCB stock levels and pricing
- **test-plan-creator**: Automated test procedure generation

## Component Search

### Multi-Source Search

Search across JLCPCB, DigiKey, and other suppliers with unified interface:

```python
from circuit_synth.manufacturing import find_parts

# Search all suppliers
results = find_parts("0.1uF 0603 X7R", sources="all")

# Specific supplier only
jlc_results = find_parts("STM32F407", sources="jlcpcb")
dk_results = find_parts("LM358", sources="digikey")

# Compare pricing and availability
comparison = find_parts("3.3V regulator", sources="all", compare=True)
```

### Fast JLCPCB Search

Optimized direct search (80% faster, zero LLM tokens):

```python
from circuit_synth.manufacturing.jlcpcb import fast_jlc_search, find_cheapest_jlc

# Search with filtering
results = fast_jlc_search("STM32G4", min_stock=100, max_results=5)

# Find cheapest option
cheapest = find_cheapest_jlc("0.1uF 0603", min_stock=1000)
```

CLI usage:
```bash
jlc-fast search "USB-C connector" --min-stock 500
jlc-fast cheapest "10k resistor" --min-stock 10000
```

### DigiKey Setup

Configure DigiKey API for access to 8M+ components:

```bash
python -m circuit_synth.manufacturing.digikey.config_manager
python -m circuit_synth.manufacturing.digikey.test_connection
```

## Library Sourcing

Multi-source component library search with automatic fallback:

```bash
cs-library-setup                     # Show configuration status
cs-setup-snapeda-api YOUR_KEY        # Optional: Enable SnapEDA API
cs-setup-digikey-api KEY CLIENT_ID   # Optional: Enable DigiKey API
```

The `/find-symbol` and `/find-footprint` commands automatically search in order:
1. Local KiCad installation
2. DigiKey GitHub libraries (150+ curated libraries)
3. SnapEDA API (millions of components)
4. DigiKey API (supplier validation)

Results show source: `[Local]`, `[DigiKey GitHub]`, `[SnapEDA]`, `[DigiKey API]`

## SPICE Simulation

```python
circuit = my_circuit()
sim = circuit.simulator()

# DC analysis
result = sim.operating_point()
print(f"Output: {result.get_voltage('VOUT'):.3f}V")

# AC analysis
ac_result = sim.ac_analysis(1, 100000)
```

## FMEA Analysis

Automated reliability analysis with comprehensive failure mode detection:

```bash
# Generate FMEA report
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py

# Specify output file and risk threshold
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py -o report.pdf --threshold 150
```

Python API:
```python
from circuit_synth.quality_assurance import EnhancedFMEAAnalyzer
from circuit_synth.quality_assurance import ComprehensiveFMEAReportGenerator

analyzer = EnhancedFMEAAnalyzer()
circuit_context = {
    'environment': 'industrial',       # Operating environment
    'safety_critical': True,           # Affects severity ratings
    'production_volume': 'high'        # Influences detection ratings
}

# Generate 50+ page PDF report
generator = ComprehensiveFMEAReportGenerator("My Project")
report_path = generator.generate_comprehensive_report(
    analysis_results,
    output_path="FMEA_Report.pdf"
)
```

Features:
- 300+ failure modes (component failures, solder joints, environmental stress)
- Physics-based reliability models (Arrhenius, Coffin-Manson, Black's equation)
- IPC Class 3 compliance checking
- Risk Priority Number (RPN) calculations
- Specific mitigation strategies for each failure mode

## Development Setup

```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync

# Run tests
uv run pytest

# Code quality
black src/ && isort src/ && flake8 src/ && mypy src/
```

## Requirements

- Python 3.9+
- KiCad 8.0+

```bash
# macOS
brew install kicad

# Linux
sudo apt install kicad
```

## Resources

- [Documentation](https://docs.circuit-synth.com)
- [Examples](https://github.com/circuit-synth/examples)
- [Contributing](CONTRIBUTING.md)
