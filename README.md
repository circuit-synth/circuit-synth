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

**Specialized AI Agents**: Domain experts for different aspects of circuit design:
- `circuit-architect`: Complete system design from requirements
- `circuit-synth`: Generate production-ready Python code
- `simulation-expert`: SPICE analysis and optimization
- `component-search`: Real-time component sourcing across suppliers
- Plus agents for debugging, testing, FMEA analysis, and more

**Slash Commands**: Quick access to common operations:
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

## 🚀 First Time User? Start Here!

**Complete working example in 3 minutes:**

```bash
# 1. Install circuit-synth
pip install circuit-synth

# 2. Create a new project with working example
uv run cs-new-project my_first_board

# 3. Generate KiCad files from the example
cd my_first_board/circuit-synth
uv run python example_project/circuit-synth/main.py

# 4. Open in KiCad (generated in ESP32_C6_Dev_Board/)
open ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro
```

**That's it!** You now have a complete ESP32-C6 development board schematic and PCB.

**What you just created:**
- ✅ ESP32-C6 microcontroller with proper power connections
- ✅ USB-C connector with CC resistors
- ✅ 3.3V voltage regulator
- ✅ LED with current-limiting resistor
- ✅ Complete KiCad project ready to edit/manufacture

**Next steps:**
- Modify `example_project/circuit-synth/main.py` to customize your circuit
- Re-run `uv run python example_project/circuit-synth/main.py` to regenerate KiCad files
- Open KiCad to view/edit your schematic and PCB layout

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

## 🔄 Automatic Source Reference Rewriting (Round-Trip Workflow)

Circuit-synth automatically updates your Python source code when KiCad auto-numbers component references, solving the back-annotation problem and enabling seamless round-trip workflow.

### The Problem (Without Source Rewriting)

```python
# Your Python code
cap1 = Component(ref="C", value="10uF", ...)   # ref="C"
cap2 = Component(ref="C", value="100nF", ...)  # ref="C"
cap3 = Component(ref="C", value="1uF", ...)    # ref="C"

# After KiCad generation: C1, C2, C3 in KiCad
# But Python still has ref="C" everywhere!
# Next generation fails with "duplicate reference C"
```

### The Solution (Automatic Source Update)

```python
# Your original code
cap1 = Component(ref="C", value="10uF", ...)   # ref="C"

# After generation, your source is automatically updated to:
cap1 = Component(ref="C1", value="10uF", ...)  # ref="C1"  ← Auto-updated!
cap2 = Component(ref="C2", value="100nF", ...) # ref="C2"  ← Auto-updated!
cap3 = Component(ref="C3", value="1uF", ...)   # ref="C3"  ← Auto-updated!

# Subsequent generations work perfectly - refs stay synchronized!
```

### How It Works

When you call `generate_kicad_project()`, circuit-synth:

1. **Auto-numbers** components: `ref="C"` → `C1`, `C2`, `C3`
2. **Updates your Python source file** with the final refs
3. **Preserves** comments, docstrings, and formatting
4. **Handles multiple components** with the same prefix correctly

### Usage

```python
circuit = main_circuit()

# Automatic source update (default when not force_regenerate)
circuit.generate_kicad_project("my_board")

# Explicitly control source updates
circuit.generate_kicad_project(
    "my_board",
    update_source_refs=True   # Force update
)

# Disable source updates
circuit.generate_kicad_project(
    "my_board",
    update_source_refs=False   # Never update
)
```

### What Gets Updated

✅ **Updated:**
- Component reference values: `ref="R"` → `ref="R1"`
- Both quote styles: `ref="C"` and `ref='C'`
- Multiple components with same prefix (ordered replacement)

❌ **NOT Updated (Preserved):**
- Comments: `# Component with ref="R"` stays unchanged
- Docstrings: Documentation examples remain intact
- String literals: Other occurrences of "R" in strings

### Safety Features

- **Atomic file operations**: Uses temp file + rename (no corruption risk)
- **Encoding preservation**: Maintains UTF-8, line endings (CRLF/LF)
- **Permission preservation**: Keeps original file permissions
- **Git-friendly**: Changes are visible in `git diff`
- **Error handling**: Graceful fallback if source file unavailable

### Benefits

🎯 **Solves Round-Trip Problem**: Refs stay synchronized between Python and KiCad forever
📝 **User-Visible Changes**: See exactly what changed in git diff
🔄 **Seamless Workflow**: Edit Python → Generate KiCad → Edit Python → Regenerate
⚡ **Zero Configuration**: Works automatically by default

### Example: See It In Action

```bash
# 1. Create circuit with unnumbered refs
echo 'cap = Component(ref="C", ...)' > circuit.py

# 2. Generate KiCad project
python circuit.py  # Calls generate_kicad_project()

# 3. Check your source file
cat circuit.py
# Output: cap = Component(ref="C1", ...)  ← Updated!

# 4. See what changed
git diff circuit.py
# Shows: -ref="C"
#        +ref="C1"
```

### When Source Updates Are Skipped

Source rewriting is automatically disabled when:
- `force_regenerate=True` (full regeneration mode)
- Running in REPL/interactive mode (no source file)
- File is read-only (permission error)
- Source file cannot be determined (frozen apps)

In these cases, KiCad generation still works normally - only the Python source update is skipped.

---

## Core Features

- **Automatic Source Reference Rewriting**: Keep Python and KiCad refs synchronized (see above)
- **Professional KiCad Output**: Generate .kicad_pro, .kicad_sch, .kicad_pcb files with modern kicad-sch-api integration
- **Circuit Patterns Library**: 7 pre-made, manufacturing-ready circuits (buck/boost converters, battery chargers, sensors, communication)
- **Hierarchical Design**: Modular subcircuits like software modules
- **Component Intelligence**: JLCPCB & DigiKey integration, symbol/footprint verification
- **AI Integration**: Claude Code agents and skills for automated design assistance
- **FMEA Analysis**: Comprehensive reliability analysis with physics-based failure models
- **Version Control**: Git-friendly text-based circuit definitions

## Configuration

```bash
# Enable detailed logging
export CIRCUIT_SYNTH_LOG_LEVEL=INFO  # ERROR, WARNING, INFO, DEBUG
```

## Circuit Patterns Library

Circuit-synth includes a curated library of 7 pre-made, manufacturing-ready circuit patterns for common design building blocks. Each pattern is a proven design with complete component selection, calculations, and PCB layout guidelines.

### Available Patterns

**Power Management:**
- `buck_converter` - 12V→5V/3.3V step-down switching regulator (TPS54331, 3A)
- `boost_converter` - 3.7V→5V step-up switching regulator (TPS61070, 1A)
- `lipo_charger` - Li-ion/LiPo USB-C charging circuit (MCP73831, CC/CV)

**Sensing & Measurement:**
- `resistor_divider` - Parametric voltage divider for ADC scaling
- `thermistor` - NTC thermistor temperature sensing circuit
- `opamp_follower` - Unity-gain voltage buffer (MCP6001)

**Communication:**
- `rs485` - Industrial differential serial interface (MAX485, Modbus/BACnet)

### Using Circuit Patterns

```python
from circuit_synth import *
from buck_converter import buck_converter
from thermistor import thermistor_sensor

@circuit(name="Battery_Monitor")
def battery_monitor():
    # Power nets
    vin_12v = Net('VIN_12V')
    vout_5v = Net('VOUT_5V')
    system_3v3 = Net('VCC_3V3')
    gnd = Net('GND')

    # Use pre-made patterns
    buck_converter(vin_12v, vout_5v, gnd, output_voltage="5V", max_current="3A")
    buck_converter(vout_5v, system_3v3, gnd, output_voltage="3.3V", max_current="2A")
    thermistor_sensor(system_3v3, adc_temp, gnd, thermistor_type="NTC_10k")
```

### Pattern Features

Each pattern includes:
- ✅ Verified KiCad symbols and footprints
- ✅ Complete component selection with datasheets
- ✅ Design calculations and theory of operation
- ✅ PCB layout guidelines and thermal management
- ✅ Manufacturing-ready specifications
- ✅ Common failure modes and troubleshooting

### Claude Code Integration

When using Claude Code, the circuit-patterns skill provides intelligent access:

```
"What circuit patterns are available?"
"Show me the buck converter circuit"
"How do I customize the boost converter for 12V output?"
```

The skill uses progressive disclosure - loading only requested patterns to save context.

See `example_project/circuit-synth/battery_monitor_example.py` and `power_systems_example.py` for complete usage examples.

## AI-Powered Design

### Claude Code Skills

Circuit-synth provides intelligent Claude Code skills for progressive disclosure:

**circuit-patterns** - Circuit pattern library browser
- Lists available pre-made circuits
- Loads pattern details on demand
- Shows customization options
- Token efficient (only loads requested patterns)

**component-search** - Fast JLCPCB component sourcing
- Real-time stock and pricing from JLCPCB
- Automatic caching for speed
- Ranks by availability and price
- Prefers Basic parts (no setup fee)

**kicad-integration** - KiCad symbol/footprint finder
- Multi-source search (local, DigiKey GitHub, SnapEDA, DigiKey API)
- Symbol and footprint verification
- Pin name extraction for accurate connections

### Claude Code Commands

```bash
# Component search
/find-symbol STM32                    # Search KiCad symbols
/find-footprint LQFP64                # Find footprints
/find-parts "STM32F407" --source jlcpcb   # Check JLCPCB availability
/find-stm32 "3 SPIs, USB"             # STM32-specific search

# Circuit generation
/generate-validated-circuit "ESP32 IoT sensor" mcu

# Fast JLCPCB CLI (no agents, 80% faster)
jlc-fast search STM32G4               # Direct search
jlc-fast cheapest "10uF 0805"         # Find cheapest option
```

### 🤖 AI Assistance

When using Claude Code, you can ask for help with:

- **Circuit Patterns**: "What circuit patterns are available?" → circuit-patterns skill
- **Component Selection**: "Find me a 3.3V regulator available on JLCPCB" → component-search skill
- **KiCad Integration**: "What footprint should I use for LQFP-48?" → kicad-integration skill
- **Circuit Design**: "Design a USB-C power supply with protection"
- **Troubleshooting**: "My board isn't powering on - help debug"
- **SPICE Simulation**: "Simulate this amplifier circuit"
- **Test Planning**: "Generate test procedures for my power supply"

The AI agents and skills will automatically select the right tools and expertise for your request.

## 🚀 Commands

### Project Creation
```bash
cs-new-project              # Complete project setup with ESP32-C6 example
```

### Circuit Generation
```bash
cd circuit-synth && uv run python example_project/circuit-synth/main.py    # Generate KiCad files from Python code
```

### Available Commands

```bash
# Component Search
/find-symbol STM32              # Search KiCad symbols
/find-footprint LQFP64          # Find footprints
/find-parts "STM32F407" --source jlcpcb   # Check availability
/find-stm32 "3 SPIs, USB"       # STM32-specific search

# Circuit Generation
/generate-validated-circuit "ESP32 IoT sensor" mcu
/validate-existing-circuit      # Validate circuit code

# Fast JLCPCB CLI
jlc-fast search STM32G4         # Direct search
jlc-fast cheapest "10uF 0805"   # Find cheapest option

# FMEA Analysis
/analyze-fmea my_circuit.py     # Run reliability analysis
```

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

### What Gets Analyzed

- **Comprehensive failure mode database** covering all standard component types
- **Context-aware analysis** adjusts risk ratings based on circuit environment and stress factors
- **Physics-based reliability models** (Arrhenius, Coffin-Manson, Black's equation) referenced in reports
- **IPC Class 3 Compliance**: High-reliability assembly standards
- **Risk Priority Number (RPN)** calculations (Severity × Occurrence × Detection)
- **Mitigation Strategies**: Specific recommendations for each failure mode

### Command Line FMEA

```bash
# Quick FMEA analysis
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py

# Specify output file
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py -o FMEA_Report.pdf

# Analyze with custom threshold
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py --threshold 150
```

See [FMEA Guide](docs/FMEA_GUIDE.md) for detailed documentation.

## Library Sourcing System

Hybrid component discovery across multiple sources with automatic fallback:

### Setup
```bash
cs-library-setup                    # Show configuration status
cs-setup-snapeda-api YOUR_KEY       # Optional: SnapEDA API access  
cs-setup-digikey-api KEY CLIENT_ID  # Optional: DigiKey API access
```

### Usage
Enhanced `/find-symbol` and `/find-footprint` commands automatically search:
1. **Local KiCad** (user installation)
2. **DigiKey GitHub** (150 curated libraries, auto-converted)
3. **SnapEDA API** (millions of components)
4. **DigiKey API** (supplier validation)

Results show source tags: `[Local]`, `[DigiKey GitHub]`, `[SnapEDA]`, `[DigiKey API]`

## Fast JLCPCB Component Search

The optimized search API provides direct JLCPCB component lookup without agent overhead:

### Python API

```python
from circuit_synth.manufacturing.jlcpcb import fast_jlc_search, find_cheapest_jlc

# Fast search with filtering
results = fast_jlc_search("STM32G4", min_stock=100, max_results=5)
for r in results:
    print(f"{r.part_number}: {r.description} (${r.price}, stock: {r.stock})")

# Find cheapest option
cheapest = find_cheapest_jlc("0.1uF 0603", min_stock=1000)
print(f"Cheapest: {cheapest.part_number} at ${cheapest.price}")
```

### CLI Usage

```bash
# Search components
jlc-fast search "USB-C connector" --min-stock 500

# Find cheapest with stock
jlc-fast cheapest "10k resistor" --min-stock 10000

# Performance benchmark
jlc-fast benchmark
```

### Performance Improvements

- **80% faster**: ~0.5s vs ~30s with agent-based search
- **90% less tokens**: 0 LLM tokens vs ~500 per search
- **Intelligent caching**: Avoid repeated API calls
- **Batch operations**: Search multiple components efficiently

## Project Structure

```
my_circuit_project/
├── example_project/
│   ├── circuit-synth/
│   │   ├── main.py                      # ESP32-C6 dev board (hierarchical)
│   │   ├── power_supply.py              # 5V→3.3V regulation
│   │   ├── usb.py                       # USB-C with CC resistors
│   │   ├── esp32c6.py                   # ESP32-C6 microcontroller
│   │   ├── led_blinker.py               # Status LED control
│   │   # Circuit Patterns Library
│   │   ├── buck_converter.py            # Step-down switching regulator
│   │   ├── boost_converter.py           # Step-up switching regulator
│   │   ├── lipo_charger.py              # Li-ion/LiPo battery charger
│   │   ├── resistor_divider.py          # Voltage divider for ADC
│   │   ├── thermistor.py                # Temperature sensing
│   │   ├── opamp_follower.py            # Unity-gain buffer
│   │   ├── rs485.py                     # Industrial communication
│   │   # Usage Examples
│   │   ├── battery_monitor_example.py   # Multi-pattern integration
│   │   └── power_systems_example.py     # Power conversion examples
│   └── ESP32_C6_Dev_Board/              # Generated KiCad files
│       ├── ESP32_C6_Dev_Board.kicad_pro
│       ├── ESP32_C6_Dev_Board.kicad_sch
│       ├── ESP32_C6_Dev_Board.kicad_pcb
│       └── ESP32_C6_Dev_Board.net
├── .claude/                             # Claude Code integration
│   ├── agents/                          # AI agents
│   ├── commands/                        # Slash commands
│   └── skills/                          # Progressive disclosure skills
│       ├── circuit-patterns/            # Circuit pattern library skill
│       ├── component-search/            # JLCPCB sourcing skill
│       └── kicad-integration/           # Symbol/footprint finder skill
├── README.md                            # Project guide
├── CLAUDE.md                            # AI assistant instructions
└── pyproject.toml                       # Project dependencies
```


## Why Circuit-Synth?

| Traditional EE Workflow | With Circuit-Synth |
|-------------------------|-------------------|
| Manual component placement | `python example_project/circuit-synth/main.py` → Complete project |
| Hunt through symbol libraries | Verified components with JLCPCB & DigiKey availability |
| Visual net verification | Explicit Python connections |
| GUI-based editing | Version-controlled Python files |
| Copy-paste patterns | Reusable circuit functions + 7 pre-made patterns |
| Research reference designs | Import proven patterns: `from buck_converter import buck_converter` |
| Manual FMEA documentation | Automated 50+ page reliability analysis |

## Resources

- [Documentation](https://docs.circuit-synth.com)
- [Examples](https://github.com/circuit-synth/examples)
- [Contributing](CONTRIBUTING.md)

## Development Setup

```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync

# Run tests
uv run pytest

# Optional: Register Claude Code agents
uv run register-agents

# Build template for distribution (copies example_project to package data)
python build.py
```

### Claude Code Working Directory

**Important for Contributors**: Circuit-synth has separate .claude configurations:

- **Repository root** (`/.claude`): Reserved for circuit-synth development, testing, and repo maintenance
- **Example project** (`/example_project/.claude`): For circuit design (this gets copied to user projects via `cs-new-project`)

**Claude Code activates based on your current working directory:**

```bash
# ❌ DON'T work from repo root for circuit design
cd circuit-synth/
claude code              # Uses dev .claude (wrong context for design)

# ✅ DO work from example_project for circuit design
cd circuit-synth/example_project/
claude code              # Uses design .claude (correct context)

# ✅ DO work from repo root for library development
cd circuit-synth/
claude code              # Uses dev .claude (correct for development)
```

The repo root .claude is for contributors working on circuit-synth itself, not for using circuit-synth to design circuits.

See `CLAUDE_FOLDER_STRUCTURE_RESEARCH.md` for detailed explanation of this architecture.

## Testing

```bash
# Run comprehensive tests
./tools/testing/run_full_regression_tests.py

# Python tests only
uv run pytest --cov=circuit_synth

# Pre-release regression test
./tools/testing/run_full_regression_tests.py

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
