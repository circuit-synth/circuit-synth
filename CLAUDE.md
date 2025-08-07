# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Git & GitHub Operations
```bash
# Create PR (Claude excels at git operations)
git add . && git commit -m "your message" && git push && gh pr create

# View recent commits and changes
git log --oneline -10
git diff HEAD~1

# Check GitHub issues and PRs
gh issue list
gh pr list
```

### KiCad Integration
```bash
# Ensure KiCad is installed locally (required dependency)
kicad-cli version

# Verify KiCad libraries are accessible
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5
```

## Development Commands

### Installation and Setup

**Primary method (recommended) - using uv:**
```bash
# Install the project in development mode
uv pip install -e ".[dev]"

# Install dependencies
uv sync

# Register Claude Code agents for AI-assisted circuit design
uv run register-agents
```

**Alternative method - using pip:**
```bash
# If uv is not available
pip install -e ".[dev]"

# Register agents (after installation)
register-agents
```

### Code Quality and Testing
**IMPORTANT: Always run linting and tests after making changes**

**🚨 PRE-RELEASE TESTING (CRITICAL for PyPI):**
```bash
# Comprehensive regression test - MUST run before ANY release
./tools/testing/run_full_regression_tests.py

# This performs COMPLETE environment reconstruction:
# - Clears ALL caches (Python, Rust, system)
# - Reinstalls Python environment from scratch
# - Rebuilds all Rust modules with Python bindings
# - Runs comprehensive functionality tests
# - Takes ~2 minutes, prevents broken releases

# Quick test during development (skip reinstall)
./tools/testing/run_full_regression_tests.py --skip-install --quick
```

**🚀 AUTOMATED TESTING (Recommended):**
```bash
# Run all tests (Python + Rust + Integration + Core)
./tools/testing/run_all_tests.sh

# Run with verbose output for debugging
./tools/testing/run_all_tests.sh --verbose

# Run only Python tests (fast)
./tools/testing/run_all_tests.sh --python-only

# Run only Rust tests
./tools/testing/run_all_tests.sh --rust-only

# Stop on first failure (for debugging)
./tools/testing/run_all_tests.sh --fail-fast
```

**🦀 RUST TESTING:**
```bash
# Test all Rust modules automatically
./tools/testing/test_rust_modules.sh

# Test with verbose output and Python integration
./tools/testing/test_rust_modules.sh --verbose

# Test specific Rust module manually
cd rust_modules/rust_netlist_processor
cargo test --lib --no-default-features
```

**🐍 TRADITIONAL PYTHON TESTING:**
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/

# Run tests with coverage (preferred)
uv run pytest --cov=circuit_synth

# Run specific test file
uv run pytest tests/unit/test_core_circuit.py -v

# Run Rust integration tests
uv run pytest tests/rust_integration/ -v
```

### Building and Distribution

**Using uv (recommended):**
```bash
# Build package
uv build

# Install locally in development mode
uv pip install -e .
```

**Using traditional tools:**
```bash
# Build package
python -m build

# Install locally
pip install -e .
```

### Build Tools
```bash
# Build all Rust modules
./tools/build/build_rust_modules.sh

# Clean rebuild everything
./tools/build/rebuild_all_rust.sh

# Format all code (Python + Rust)
./tools/build/format_all.sh
```

### Component Search Commands
```bash
# Unified component search across suppliers (NEW!)
# /find-parts "0.1uF 0603" - Search all suppliers
# /find-parts "STM32F407" --source jlcpcb - JLCPCB only
# /find-parts "LM358" --source digikey - DigiKey only
# /find-parts "3.3V regulator" --compare - Compare across suppliers

# KiCad symbol and footprint search
# /find-symbol STM32 - Search for STM32 symbols
# /find-footprint LQFP - Search for LQFP footprints

# Circuit validation commands
# /generate-validated-circuit "ESP32 development board" - Generate circuit with quality assurance
# /validate-existing-circuit - Validate and improve existing circuit code

# Quality Assurance commands
# /analyze-fmea my_circuit.py - Run FMEA analysis on circuit
# /generate-fmea-report my_circuit.py --comprehensive - Generate 50+ page FMEA report

# Circuit Debugging commands (NEW!)
# /debug-start "Board not powering on" --board="my_board" - Start debug session
# /debug-symptom "No voltage on 3.3V rail" - Add symptom
# /debug-measure "VCC: 0V, VBUS: 5V" - Add measurements
# /debug-analyze - Get AI analysis of issues
# /debug-suggest - Get next troubleshooting steps
# /debug-tree power - Show power troubleshooting tree

# Development slash commands (for contributors)
# /dev-run-tests - Run comprehensive test suite
# /dev-update-and-commit "description" - Update docs and commit changes

# Manual search in KiCad libraries (if needed)
find /usr/share/kicad/symbols -name "*.kicad_sym" | xargs grep -l "STM32"
find /usr/share/kicad/footprints -name "*.kicad_mod" | grep -i lqfp
```

### Multi-Source Component Search (NEW!)
```python
from circuit_synth.manufacturing import find_parts

# Search all suppliers
results = find_parts("0.1uF 0603 X7R", sources="all")

# Search specific supplier
jlc_results = find_parts("STM32F407", sources="jlcpcb")
dk_results = find_parts("LM358", sources="digikey")

# Compare across suppliers
comparison = find_parts("3.3V regulator", sources="all", compare=True)
print(comparison)  # Shows comparison table

# Filter by requirements
high_stock = find_parts("10k resistor", min_stock=10000, max_price=0.10)
```

### DigiKey Integration Setup
```bash
# Configure DigiKey API (one-time setup)
python -m circuit_synth.manufacturing.digikey.config_manager

# Test connection
python -m circuit_synth.manufacturing.digikey.test_connection

# Environment variables (alternative to config file)
export DIGIKEY_CLIENT_ID="your_client_id"
export DIGIKEY_CLIENT_SECRET="your_client_secret"
```

## Circuit Validation System

**NEW FEATURE: Circuit Quality Assurance**

The validation system provides automatic quality checking and improvement for circuit code:

### Core Functions
```python
from circuit_synth.validation import validate_and_improve_circuit, get_circuit_design_context

# Validate and fix circuit code automatically
code, is_valid, status = validate_and_improve_circuit(circuit_code)

# Get comprehensive design context for better generation
context = get_circuit_design_context("esp32")  # or "power", "analog", etc.
```

### Available Commands
- `/generate-validated-circuit <description> [type]` - Generate circuit with quality assurance
- `/validate-existing-circuit` - Check and improve existing circuit code

### What It Validates
1. **Syntax errors** - Catches Python syntax issues
2. **Missing imports** - Automatically fixes circuit_synth imports
3. **Runtime execution** - Ensures code actually runs
4. **Circuit structure** - Validates @circuit decorator usage

### Example Usage
```bash
# Generate validated ESP32 circuit
/generate-validated-circuit "ESP32 with USB-C power" mcu

# Validate code you wrote manually
/validate-existing-circuit
```

## Circuit Debugging System

**NEW FEATURE: AI-Powered PCB Troubleshooting**

The debugging system helps diagnose and fix hardware issues with intelligent analysis:

### Core Functions
```python
from circuit_synth.debugging import CircuitDebugger, DebugSession

# Start debugging session
debugger = CircuitDebugger()
session = debugger.start_session("my_board", "v1.0")

# Add symptoms and measurements
session.add_symptom("Board not powering on")
session.add_measurement("VCC_3V3", 0, "V")

# Analyze issues
issues = debugger.analyze_symptoms(session)

# Get troubleshooting guidance
suggestions = debugger.suggest_next_test(session)
```

### CLI Tool
```bash
# Interactive debugging
uv run python -m circuit_synth.tools.debug_cli --interactive

# Or single commands
uv run python -m circuit_synth.tools.debug_cli start my_board --version 1.0
uv run python -m circuit_synth.tools.debug_cli symptom "No power LED"
uv run python -m circuit_synth.tools.debug_cli analyze
```

### Features
- **Symptom Analysis**: Categorizes issues by domain (power, digital, analog, RF)
- **Pattern Recognition**: Matches symptoms to historical debugging sessions
- **Test Guidance**: Systematic troubleshooting trees for common issues
- **Knowledge Base**: Learns from past debugging sessions
- **Equipment Guidance**: Recommends appropriate test equipment and procedures

## Code Style Guidelines

**IMPORTANT: Follow these conventions exactly**
- Use modern Python with type hints and dataclasses
- NO inheritance complexity or global state management
- Follow SOLID, KISS, YAGNI, and DRY principles
- Prefer composition over inheritance
- Use descriptive variable and function names
- Write comprehensive docstrings for public APIs

## Workflow Preferences

**Test-Driven Development (TDD) - MANDATORY APPROACH:**
1. **Write tests first** based on expected input/output behavior
2. **Run tests to confirm they fail** (red phase)
3. **Write minimal code** to make tests pass (green phase)
4. **Refactor and improve** while keeping tests passing
5. **Test thoroughly at each step** - don't assume code works
6. **YOU MUST run linting and type checking** before committing

**Incremental Development Philosophy:**
- **Make slow, steady progress** - small incremental changes are better than large jumps
- **Test every assumption** - don't assume your code does what you think it does
- **Validate behavior continuously** - run tests after every small change
- **Confirm expectations** - manually verify outputs match what you expect
- **One feature at a time** - complete and thoroughly test one feature before moving to the next
- **Example workflow**: Write test → Run test (fails) → Write minimal code → Run test (passes) → Manually verify output → Move to next small piece

**Planning Before Coding:**
- Always ask Claude to make a plan before implementing
- Use "think" keywords for extended thinking mode
- Break complex tasks into smaller, actionable steps

## STM32 Peripheral Search Pattern (HIGHEST PRIORITY)

**CRITICAL: Detect and handle STM32 peripheral queries directly - DO NOT use agents**

When user asks questions like:
- "find stm32 mcu that has 3 spi's and is available on jlcpcb"
- "stm32 with 2 uarts available on jlc" 
- "find stm32 with usb and 4 timers in stock"

**Use direct implementation immediately:**

```python
from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query

# Check if this is an STM32 peripheral query first
response = handle_stm32_peripheral_query(user_query)
if response:
    return response  # Direct answer - no agents, no web search, no complex workflow
```

**Detection Pattern:**
- Contains: stm32 + peripheral (spi/uart/i2c/usb/can/adc/timer/gpio) + availability (jlcpcb/jlc/stock)
- This workflow gives answers in 30 seconds vs 4+ minutes with agents

**Why this matters:**
- We have precise STM32 pin data via modm-devices
- JLCPCB caching prevents repeated API calls
- KiCad symbol verification ensures working results
- User gets exactly what they asked for quickly

**Debugging Strategy:**
- **Always use uv for running Python scripts**: Use `uv run python script.py` instead of just `python script.py`
- **Development flow pattern**: Add lots of debug logs → run script → observe output → change code → repeat
- **Add extensive logging during development**: Use Python's `logging` module liberally when troubleshooting or implementing new features
- **Log key data points**: Component creation, net connections, file operations, API calls
- **Redirect logs to files for analysis**: When logs grow too large for terminal, use `uv run python script.py > debug_output.log 2>&1` to capture all output
- **Remove non-essential logs when feature is complete**: Keep only critical error logs and high-level status messages
- **Example**: `logging.debug(f"Creating component {ref} with symbol {symbol}")` during development, remove when stable

**Multi-Attempt Problem Solving Protocol:**
When you have attempted to fix the same issue 3+ times without success, **STOP** and follow this systematic approach:

1. **Document the Problem State**:
   - Write a clear problem statement
   - List all attempted solutions with outcomes
   - Identify recurring patterns in failures
   - Note any error messages, symptoms, or clues

2. **Context Management**:
   - Use `/compact` to compress the conversation context
   - Save important findings to `memory-bank/issues/` if needed
   - Clear mental context to approach fresh

3. **Deep Analysis Phase**:
   - Break the problem into smaller, isolated components
   - Identify root causes vs. symptoms
   - Question initial assumptions about the problem
   - Consider alternative approaches or architectures

4. **Research Phase**:
   - Use WebSearch to research similar problems, error messages, or techniques
   - Look for official documentation, Stack Overflow solutions, GitHub issues
   - Research best practices for the specific technology or domain
   - Investigate whether the approach itself is fundamentally flawed

5. **Systematic Solution**:
   - Based on research, create a new approach plan
   - Test each component in isolation
   - Implement incrementally with verification at each step
   - Document the successful solution for future reference

**Example trigger scenarios:**
- Same CI test failing after 3+ different fix attempts
- Repeatedly encountering the same error with different "solutions"
- Multiple approaches to the same feature all hitting similar roadblocks
- Environment or dependency issues that persist across multiple fixes

## Memory Bank System

**CRITICAL: Use memory-bank/ effectively for context preservation**

The `memory-bank/` directory maintains project context and technical knowledge across sessions. Use it strategically:

### Memory Bank Structure
```
memory-bank/
├── progress/          # Development progress tracking
├── decisions/         # Technical decisions and rationale  
├── patterns/          # Reusable code patterns and solutions
├── issues/           # Known issues and workarounds
└── knowledge/        # Domain-specific insights and learnings
```

### How to Use Memory Bank

**1. Progress Tracking (`memory-bank/progress/`):**
- Create focused entries for significant technical milestones
- Document **what** was implemented and **why** it was needed
- Keep entries concise (2-3 sentences maximum)
- Use date-based filenames: `2025-07-28-feature-name.md`

**2. Technical Decisions (`memory-bank/decisions/`):**
- Record architectural choices and trade-offs
- Document **why** you chose one approach over alternatives
- Include context about constraints and requirements

**3. Reusable Patterns (`memory-bank/patterns/`):**
- Save common circuit-synth code patterns
- Document successful component configurations
- Record KiCad symbol/footprint mappings that work well

**4. Issue Tracking (`memory-bank/issues/`):**
- Document known bugs with workarounds
- Track compatibility issues between tools
- Record debugging strategies that worked

**Example Memory Bank Entry:**
```markdown
# KiCad Symbol Search Optimization

## Summary
Implemented cross-platform KiCad library search with fallback paths for macOS and Linux.

## Key Changes
- Added `/find-symbol` command with grep-based search across multiple library paths
- Handles both standard KiCad installations and Homebrew locations on macOS

## Impact
Users can now reliably find KiCad symbols regardless of installation method.
```

## Agent Workflow

**CRITICAL: Use specialized agents for optimal results**

This repository uses a structured agent workflow. Always start with **orchestrator** for complex multi-step tasks.

### Available Agents and Their Expertise

1. **orchestrator** - Master coordinator for complex projects
   - **When to use**: Multi-step tasks spanning different domains
   - **Capabilities**: Breaks down complex requests, delegates to specialists, manages dependencies
   - **Example**: "Build a complete ESP32 development board with power management"

2. **architect** - Planning and requirements analysis
   - **When to use**: Unclear requirements, need structured planning
   - **Capabilities**: Requirement gathering, task breakdown, technical planning
   - **Example**: "Plan the implementation of a new PCB routing algorithm"

3. **code** - Software engineering best practices
   - **When to use**: Code implementation, refactoring, code reviews
   - **Capabilities**: SOLID principles, design patterns, code quality
   - **Example**: "Refactor the component creation system for better maintainability"

4. **circuit-synth** - Circuit design and KiCad integration specialist
   - **When to use**: Circuit design, component selection, KiCad workflows
   - **Capabilities**: Uses `/find-symbol` and `/find-footprint`, circuit topology expertise
   - **Example**: "Design a USB-C power delivery circuit with proper protection"

5. **general-purpose** - Research and complex searches
   - **When to use**: Open-ended research, file searching across large codebases
   - **Capabilities**: Multi-round searching, code analysis, documentation research
   - **Example**: "Find all references to voltage regulator implementations in the codebase"

### Agent Usage Strategy

**Start Right:**
```bash
# Complex multi-domain task
Task(subagent_type="orchestrator", description="Build ESP32 board", prompt="Design complete ESP32 development board with USB-C, power management, and programming interface")

# Planning unclear requirements  
Task(subagent_type="architect", description="Plan PCB algorithm", prompt="Analyze requirements and create implementation plan for new PCB component placement algorithm")

# Circuit-specific design work
Task(subagent_type="circuit-synth", description="Design power circuit", prompt="Create 3.3V/5V dual rail power supply circuit with USB-C input and protection")
```

**Let Orchestrator Coordinate:**
- Don't manually chain agents - let orchestrator manage the workflow
- Orchestrator will delegate to architect → circuit-synth → code as needed
- Trust the orchestrator to choose the right specialist for each subtask

### Example Workflows

**Circuit Design Request:**
```
User: "Design an ESP32 development board with USB-C and LDO regulator"

orchestrator → architect (analyze requirements, plan circuit topology)  
architect → circuit-synth (find components, design circuit connections)
circuit-synth → code (implement Python circuit-synth code)
orchestrator → (coordinate testing, KiCad generation, validation)
```

**Code Enhancement Request:**
```
User: "Add a new placement algorithm for PCB components"

orchestrator → architect (analyze requirements, plan implementation)
architect → code (implement algorithm following best practices)  
orchestrator → (coordinate testing, documentation, integration)
```

**Research/Analysis Request:**
```
User: "Find all voltage regulator patterns used in existing circuits"

orchestrator → general-purpose (search codebase, analyze patterns)
general-purpose → architect (organize findings, identify patterns)
orchestrator → (coordinate documentation, recommendations)
```

## Repository Structure

### CRITICAL: Two Circuit-Synth Repositories

There are **TWO** distinct circuit-synth repositories that you must be aware of:

1. **Private Repository**: `Circuit_Synth2/` (closed source)
   - This is the original project where most functionality was initially developed
   - Contains the complete, mature implementation
   - Located at `/Users/shanemattner/Desktop/Circuit_Synth2/`
   - This is the private, closed-source version

2. **Open Source Repository**: `Circuit_Synth2/submodules/circuit-synth/` (open source)
   - This is the open-source version created as a submodule
   - Some functionality from the private repo was **not copied over properly**
   - Located at `/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth/`
   - **This is where all new development should happen**

### Development Guidelines

- **ALWAYS work in the open source repo**: `/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth/`
- When referencing functionality, be explicit about which repo you're looking at
- If functionality exists in the private repo but is missing from the open source repo, it needs to be ported over
- **Never make changes to the private repo** - all development goes in the open source version
- Keep track of which repo contains which functionality to avoid confusion

### Repository References

When discussing code or functionality:
- **Private repo**: Reference as "private Circuit_Synth2 repo" or "closed source repo"
- **Open source repo**: Reference as "open source circuit-synth repo" or "submodule repo"
- **Default assumption**: Unless specified otherwise, all work should be done in the **open source repo**

## Annotation System

The circuit-synth repository includes a comprehensive annotation system that enables automatic and manual documentation of Python-generated circuit designs. This system provides seamless integration between Python code documentation and KiCad schematic annotations.

### Overview

The annotation system consists of three main components:

1. **Decorator-based automatic annotations** - Extracts docstrings from decorated functions
2. **Manual annotation classes** - Provides structured annotation objects for custom documentation
3. **JSON export pipeline** - Serializes annotations to JSON for KiCad integration

### Key Components

#### 1. Decorator Flags (`@enable_comments`)

The `@enable_comments` decorator automatically extracts function docstrings and converts them into schematic annotations:

```python
from circuit_synth.annotations import enable_comments

@enable_comments
def create_amplifier_stage():
    """
    Creates a common-emitter amplifier stage.
    
    This circuit provides voltage amplification with a gain of approximately 100.
    Input impedance: ~1kΩ, Output impedance: ~3kΩ
    """
    # Circuit implementation...
    pass
```

#### 2. Manual Annotation Classes

Three annotation classes provide structured documentation capabilities:

**TextBox Annotations:**
```python
from circuit_synth.annotations import TextBox

# Create a text box annotation
note = TextBox(
    text="High-frequency bypass capacitor for supply rail filtering",
    position=(50, 30),
    size=(40, 15),
    style="note"
)
```

**TextProperty Annotations:**
```python
from circuit_synth.annotations import TextProperty

# Add property annotation to a component
component_note = TextProperty(
    text="R1: Sets bias current to 2.5mA",
    position=(10, 5),
    style="property"
)
```

**Table Annotations:**
```python
from circuit_synth.annotations import Table

# Create a specifications table
specs_table = Table(
    headers=["Parameter", "Min", "Typical", "Max", "Unit"],
    rows=[
        ["Supply Voltage", "3.0", "3.3", "3.6", "V"],
        ["Gain", "95", "100", "105", "dB"],
        ["Bandwidth", "1", "10", "20", "MHz"]
    ],
    position=(100, 50),
    title="Amplifier Specifications"
)
```

#### 3. JSON Export Pipeline

The annotation system includes a complete serialization pipeline that converts annotations to JSON format compatible with KiCad:

```python
from circuit_synth.annotations import export_annotations_to_json

# Export all annotations from a design
annotations = [text_box, component_note, specs_table]
json_output = export_annotations_to_json(annotations, "amplifier_design")
```

### Usage Examples

#### Automatic Annotation Workflow

1. **Decorate functions** with `@enable_comments` to enable automatic docstring extraction
2. **Write descriptive docstrings** following standard Python conventions
3. **Run the design generation** - annotations are captured automatically
4. **Export to JSON** for KiCad integration

```python
@enable_comments
def design_filter_circuit():
    """
    Second-order Butterworth low-pass filter.
    
    Cutoff frequency: 1kHz
    Roll-off: -40dB/decade above cutoff
    Input/Output impedance: 50Ω
    """
    # Implementation creates filter components
    return circuit
```

#### Manual Annotation Workflow

1. **Create annotation objects** during circuit generation
2. **Position annotations** relative to components or absolute coordinates
3. **Collect annotations** in a list or annotation manager
4. **Export to JSON** alongside automatic annotations

```python
def create_power_supply():
    # Create circuit components
    
    # Add manual annotations
    annotations = [
        TextBox(
            text="Regulation: ±0.1% line/load",
            position=(75, 25),
            style="specification"
        ),
        Table(
            headers=["Rail", "Voltage", "Current"],
            rows=[
                ["+5V", "5.00V", "2.0A"],
                ["-5V", "-5.00V", "0.5A"],
                ["+12V", "12.00V", "1.0A"]
            ],
            position=(120, 60),
            title="Power Rail Specifications"
        )
    ]
    
    return circuit, annotations
```

### Technical Implementation Details

#### Data Flow Architecture

The annotation system implements a robust data flow from Python generation to KiCad integration:

1. **Collection Phase**: Annotations are gathered during circuit generation
2. **Validation Phase**: Annotation objects are validated for completeness
3. **Serialization Phase**: Objects are converted to JSON with proper formatting
4. **Export Phase**: JSON is written with KiCad-compatible structure

#### S-expression Formatting Fixes

The system includes comprehensive S-expression formatting with proper string escaping for KiCad compatibility:

- **String Escaping**: Handles special characters in annotation text
- **Coordinate Formatting**: Ensures proper numeric formatting for positions
- **Style Mapping**: Maps annotation styles to KiCad text properties
- **Hierarchical Structure**: Maintains proper S-expression nesting

```python
# Example of formatted S-expression output
(text "High-frequency bypass capacitor" (at 50.8 76.2 0)
  (effects (font (size 1.27 1.27)) (justify left))
  (uuid "annotation-uuid-here")
)
```

#### JSON Schema Structure

The export pipeline follows a consistent JSON schema:

```json
{
  "design_name": "amplifier_design",
  "timestamp": "2025-01-27T10:30:00Z",
  "annotations": [
    {
      "type": "textbox",
      "id": "unique-id",
      "text": "annotation content",
      "position": {"x": 50, "y": 30},
      "size": {"width": 40, "height": 15},
      "style": "note",
      "metadata": {
        "source": "automatic|manual",
        "function": "function_name"
      }
    }
  ]
}
```

### Integration with KiCad

The annotation system provides seamless integration with KiCad schematics:

1. **JSON Import**: KiCad can import the generated JSON files
2. **S-expression Compatibility**: All formatting follows KiCad standards
3. **Layer Management**: Annotations are placed on appropriate schematic layers
4. **UUID Tracking**: Each annotation receives a unique identifier for updates

This implementation provides a complete end-to-end solution for documenting Python-generated circuit designs with both automatic and manual annotation capabilities.

## Scalable Directory Structure

### IMPORTANT: Reorganized Source Structure

The repository has been reorganized with a scalable directory structure to support multiple chip families and manufacturers:

```
circuit-synth2/
├── src/circuit_synth/
│   ├── component_info/           # Component-specific integrations
│   │   ├── microcontrollers/    # MCU families (STM32, ESP32, PIC, AVR)
│   │   ├── analog/              # Analog components (op-amps, ADCs, etc.)
│   │   ├── power/               # Power management components
│   │   ├── rf/                  # RF/wireless components
│   │   ├── passives/            # Passive components (future)
│   │   └── sensors/             # Sensors and measurement (future)
│   ├── manufacturing/           # Manufacturing integrations  
│   │   ├── jlcpcb/             # JLCPCB integration
│   │   ├── pcbway/             # PCBWay (future)
│   │   ├── oshpark/            # OSH Park (future)
│   │   └── digikey/            # DigiKey sourcing (implemented)
│   ├── tools/                  # CLI tools and utilities
│   └── [core modules...]       # Core circuit-synth functionality
├── examples/                   # User examples organized by complexity
│   ├── basic/                 # Simple usage examples
│   ├── advanced/              # Complex feature demonstrations
│   ├── testing/               # Test and validation scripts
│   └── tools/                 # Utility scripts
├── tools/                      # Repository build/CI tools
└── [other repo files...]
```

### Import Guidelines

**Updated Import Patterns:**
```python
# STM32 MCU search (modm-devices integration)
from circuit_synth.ai_integration.component_info.microcontrollers.modm_device_search import search_stm32

# JLCPCB integration (moved from circuit_synth.jlc_integration)  
from circuit_synth.manufacturing.jlcpcb import find_component, search_jlc_components_web

# Future component families
from circuit_synth.ai_integration.component_info.microcontrollers.esp32 import ESP32DeviceSearch  # (future)
from circuit_synth.ai_integration.component_info.analog.opamps import OpAmpSelector  # (future)
from circuit_synth.ai_integration.component_info.power.regulators import RegulatorDesigner  # (future)
from circuit_synth.ai_integration.component_info.passives.resistors import ResistorSelector  # (future)
from circuit_synth.ai_integration.component_info.sensors.temperature import TempSensorSelector  # (future)

# Future manufacturing integrations
from circuit_synth.manufacturing.pcbway import get_pcbway_pricing  # (future)
from circuit_synth.manufacturing.digikey import search_digikey_components  # (implemented)
```

**Backward Compatibility:**
- Old import paths are updated but may need adjustment in legacy code
- New structure enables easy addition of chip families and manufacturers
- Each category provides clear separation of concerns and expertise domains

### Adding New Integrations

**To add a new component family:**
1. Create directory: `src/circuit_synth/component_info/[category]/[family]/`
2. Implement component-specific functionality (device search, configuration, etc.)  
3. Add proper `__init__.py` with clear API exports
4. Update relevant Claude agents and commands

**To add a new manufacturer:**
1. Create directory: `src/circuit_synth/manufacturing/[manufacturer]/`
2. Implement manufacturer-specific APIs (availability, pricing, constraints)
3. Follow JLCPCB integration patterns for consistency
4. Add manufacturing-specific validation and optimization

## Circuit-Synth Specific Knowledge

### Core Components and Patterns

**Component Creation:**
```python
# Standard component pattern
component = Component(
    symbol="Library:SymbolName",        # Use /find-symbol to locate
    ref="U",                           # Reference prefix (U, R, C, etc.)
    footprint="Library:FootprintName", # Use /find-footprint to locate
    value="optional_value"             # For passives (resistors, caps)
)
```

**Net Management:**
```python
# Create nets for connections
VCC_3V3 = Net('VCC_3V3')  # Descriptive names
GND = Net('GND')

# Connect components to nets
component["pin_name"] += net_name
component[1] += VCC_3V3  # Pin numbers for simple components
```

**Circuit Decorators:**
```python
@circuit(name="circuit_name")
def my_circuit():
    """Docstring becomes schematic annotation"""
    # Circuit implementation
    return circuit  # Optional explicit return
```

### Common Libraries and Footprints

**Microcontrollers:**
- ESP32: `RF_Module:ESP32-S3-MINI-1`
- STM32: `MCU_ST_STM32F4:STM32F407VETx` (use /find-symbol STM32)
- Arduino: `MCU_Module:Arduino_UNO_R3`

**Passives:**
- Resistors: `Device:R` with footprints like `Resistor_SMD:R_0603_1608Metric`
- Capacitors: `Device:C` with footprints like `Capacitor_SMD:C_0603_1608Metric`
- Inductors: `Device:L` with appropriate footprints

**Connectors:**
- USB-C: `Connector:USB_C_Receptacle_*` (search with /find-symbol)
- Headers: `Connector_Generic:Conn_01x*` or `Conn_02x*`
- Power jacks: `Connector:Barrel_Jack_*`

### KiCad Integration Best Practices

**Symbol and Footprint Naming:**
- Always use full library:name format
- Verify symbols exist before using (run /find-symbol first)
- Match footprint to component package exactly

**Net Naming Conventions:**
- Power nets: `VCC_5V`, `VCC_3V3`, `GND`
- Signal nets: `USB_DP`, `USB_DM`, descriptive names
- Avoid generic names like `Net1`, `Net2`

**Reference Designators:**
- Follow standard conventions: U (ICs), R (resistors), C (capacitors), L (inductors), J (connectors)
- Let circuit-synth auto-assign numbers: `ref="U"` becomes `U1`, `U2`, etc.

### Common Patterns

**Power Supply Design:**
```python
# Voltage regulator with decoupling
vreg = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
cap_in = Component(symbol="Device:C", ref="C", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
cap_out = Component(symbol="Device:C", ref="C", value="22uF", footprint="Capacitor_SMD:C_0805_2012Metric")
```

**USB Interface:**
```python
usb_conn = Component(symbol="Connector:USB_C_Receptacle_USB2.0", ref="J", footprint="Connector_USB:USB_C_Receptacle_*")
# Connect VBUS, GND, D+, D- appropriately
```

### Troubleshooting Common Issues

**Symbol/Footprint Not Found:**
- Use /find-symbol and /find-footprint commands
- Check exact spelling and capitalization
- Verify library names match KiCad standard libraries

**Net Connection Problems:**
- Ensure pin names match exactly (case sensitive)
- Use integers for simple component pins: `component[1]`, `component[2]`
- Use strings for named pins: `component["VCC"]`, `component["GND"]`

**KiCad Generation Issues:**
- Check that all components have valid symbols and footprints
- Verify net connections are complete (no unconnected pins)
- Ensure reference designators are unique and follow conventions

## JSON-Centric Architecture

Circuit-synth uses **JSON as the canonical intermediate representation** for all circuit data. This is critical to understand:

### Data Flow
```
Python Circuit Code ←→ JSON (Central Format) ←→ KiCad Files
```

- **Python → JSON**: `circuit.to_dict()` or `circuit.generate_json_netlist()`
- **JSON → KiCad**: Internal JSON processing generates .kicad_* files
- **KiCad → JSON**: Parser extracts circuit structure to JSON format
- **JSON → Python**: `json_to_python_project` generates Python code

### Key Points
1. **Hierarchical circuits are stored as nested JSON** with subcircuits preserved
2. **Round-trip conversion is lossless** - no information lost in any direction
3. **JSON is the single source of truth** - all conversions go through JSON
4. **One JSON format** - consistent structure for all operations

### Working with JSON
```python
# Export circuit to JSON
circuit.generate_json_netlist("my_circuit.json")

# Load circuit from JSON
from circuit_synth.io import load_circuit_from_json_file
circuit = load_circuit_from_json_file("my_circuit.json")

# KiCad generation uses JSON internally
circuit.generate_kicad_project("my_project")  # Creates temp JSON, then KiCad files
```

For detailed architecture information, see `docs/ARCHITECTURE.md`.

## PyPI Release Process

**IMPORTANT: Clean repository before releasing to PyPI**

The repository includes an automated release script that handles the complete PyPI release pipeline:

```bash
# Release to PyPI (from develop or main branch)
./tools/release/release_to_pypi.sh 0.5.1
```

### Pre-Release Checklist

**1. Clean up test/temporary files:**
The release script will check for and warn about files that shouldn't be in the main branch:
- Top-level Python scripts (test_*.py, *_test.py, debug scripts)
- Generated directories (*_generated/, *_reference/, *_Dev_Board/)
- Temporary files (*.log, *.tmp, *.txt)
- Debug/analysis files (*.md except README.md, CLAUDE.md, Contributors.md)

**2. Ensure clean working directory:**
```bash
git status  # Should show no uncommitted changes
```

**3. Update from develop branch:**
```bash
git checkout develop
git pull origin develop
```

### What the Release Script Does

1. **Validates** version format and clean working directory
2. **Checks** for test/temporary files that shouldn't be released
3. **Updates** version in pyproject.toml and __init__.py
4. **Runs** test suite to ensure everything works
5. **Merges** develop → main (if releasing from develop)
6. **Tags** the release with semantic version
7. **Builds** source and wheel distributions
8. **Cleans** build artifacts and caches
9. **Uploads** to PyPI
10. **Creates** GitHub release with changelog

### Manual Cleanup (if needed)

If you have test files in the top-level directory:
```bash
# Move test files to appropriate directories
mv test_*.py tests/
mv *_generated/ *_reference/ examples/testing/

# Or remove if no longer needed
rm -rf *_Dev_Board/ *.log *.tmp
```

### Post-Release

After successful release:
- Package available at: https://pypi.org/project/circuit-synth/
- GitHub release created with changelog
- Users can install with: `pip install circuit-synth==VERSION`
