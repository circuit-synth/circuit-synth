# Circuit Design .claude Configuration

This .claude folder provides circuit design tools and AI assistance for circuit-synth projects.

## Purpose

This configuration is specifically for **circuit design work** - creating circuits, selecting components, and generating KiCad projects. It gets copied to new projects when you run `cs-new-project`.

**Note**: This is NOT the development .claude for circuit-synth library work. That's at the repository root.

## Available Tools

### Skills (Progressive Disclosure)
- **circuit-patterns**: Browse and use pre-made circuit patterns
- **component-search**: Fast JLCPCB component sourcing with caching
- **kicad-integration**: Multi-source symbol/footprint finder

### Slash Commands

**Circuit Design:**
- `/find-symbol` - Search KiCad symbols
- `/find-footprint` - Find KiCad footprints
- `/find-pins` - Get exact pin names for components
- `/generate-validated-circuit` - AI-powered circuit generation
- `/validate-existing-circuit` - Validate circuit code

**Manufacturing:**
- `/find-parts` - Search JLCPCB/DigiKey for components
- `/find_stm32` - STM32-specific peripheral search
- `/find-mcu` - General MCU search with requirements

**Setup:**
- `/setup-kicad-plugins` - Install KiCad plugins
- `/setup_circuit_synth` - Configure circuit-synth

**Development (for contributors):**
- `/dev:run-tests` - Run test suite
- `/dev:review-branch` - Review git branch
- `/dev:update-and-commit` - Update docs and commit

### AI Agents

**Circuit Design:**
- `circuit-architect` - Master circuit coordinator
- `circuit-generation-agent` - Code generation specialist
- `interactive-circuit-designer` - **PRIMARY** collaborative design interface
- `circuit-syntax-fixer` - Fixes code errors
- `circuit-validation-agent` - Tests generated code
- `component-symbol-validator` - Validates KiCad symbols
- `simulation-expert` - SPICE simulation

**Component Sourcing:**
- `stm32-mcu-finder` - STM32 selection with pin mapping
- `jlc-parts-finder` - JLCPCB component search
- `component-guru` - Manufacturing optimization
- `dfm-agent` - Design for Manufacturing analysis

**Orchestration:**
- `circuit-project-creator` - Master orchestrator for complete projects

**Development:**
- `contributor` - Contributor onboarding and help

## Using Claude Code

### Starting a Session

```bash
# Navigate to your project
cd my_circuit_project/

# Start Claude Code
claude code
```

### Example Interactions

**Using Skills:**
```
"What circuit patterns are available?"
"Find a 10k resistor on JLCPCB"
"What footprint should I use for LQFP-48?"
```

**Using Agents:**
```
# Let Claude choose the right agent
"Design a 5V power supply with USB-C input"
"Find an STM32 with 3 SPIs available on JLCPCB"
"Help me fix this circuit code error"
```

**Using Commands:**
```
/find-symbol STM32F411
/find-parts "AMS1117-3.3" --source jlcpcb
/generate-validated-circuit "LED blinker" simple
```

## Project Structure

Your project will have:
```
my_circuit_project/
├── circuit-synth/           # Your Python circuit files
│   ├── main.py
│   ├── buck_converter.py    # Circuit patterns available
│   └── ...
├── .claude/                 # This folder (Claude Code config)
└── Generated_Project/       # KiCad files output here
```

## Circuit Patterns Library

Import pre-made patterns directly:

```python
from buck_converter import buck_converter
from lipo_charger import lipo_charger
from thermistor import thermistor_sensor

# Use in your circuit
buck_converter(vin, vout, gnd, output_voltage="5V", max_current="3A")
```

Available patterns:
- **Power**: buck_converter, boost_converter, lipo_charger
- **Sensing**: resistor_divider, thermistor, opamp_follower
- **Communication**: rs485

See the pattern files in `circuit-synth/` for details and documentation.

## Getting Help

**Ask Claude directly:**
- "How do I use the buck converter pattern?"
- "What's the difference between the skills and agents?"
- "Show me an example of using multiple patterns together"

**Check documentation:**
- Main README: `../README.md`
- CLAUDE.md: `CLAUDE.md` (AI assistant instructions)
- Research docs in repo root: `CLAUDE_FOLDER_STRUCTURE_RESEARCH.md`

## For Contributors

If you're working on circuit-synth itself (not using it to design circuits):

1. Work from the repository root, not from example_project
2. Use the root .claude configuration (development tools)
3. See `CLAUDE_FOLDER_STRUCTURE_RESEARCH.md` for architecture details

This example_project .claude is specifically for **using** circuit-synth, not **developing** it.
