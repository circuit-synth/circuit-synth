# Circuit-Synth Contributors Guide 🚀

**Welcome to the most contributor-friendly EE design tool ever built!** Whether you're fixing a bug, adding a feature, or just exploring - we've made it incredibly easy to get started.

## 🎯 Quick Start (5 minutes)

**1. Get the code:**
```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
```

**2. Install and run:**
```bash
# Install dependencies
uv sync

# Try it out
uv run python examples/example_kicad_project.py
```

**3. Use Claude Code (recommended):**
```bash
uv run register-agents
# Now Claude Code has specialized circuit-synth agents to help you!
```

That's it! You now have a working circuit-synth development environment.

## 🤖 Why We Love Claude Code

**This project is designed specifically for Claude Code + GitHub MCP.** You get:

- **Specialized agents** that understand circuit design, KiCad, manufacturing, and our codebase
- **Automated workflows** - from reading GitHub issues to creating PRs
- **Built-in guidance** - agents help with architecture, testing, and best practices
- **Instant expertise** - no need to learn everything upfront

**Quick Claude Code workflow:**
1. Use agents like `circuit-architect`, `power-expert`, `component-guru` 
2. Ask questions: *"How do I add Rust acceleration?"* or *"Find STM32 with 3 SPIs"*
3. Let agents guide you through implementation and testing

## 🎯 Choose Your Adventure

### 🔍 Option 1: Add a Component Example (Beginner-Friendly, 15 mins)

**Goal**: Add a new circuit example that other EEs can learn from.

**Steps:**
1. Look at existing examples in `examples/`
2. Pick a common circuit pattern (voltage divider, LED driver, sensor interface)
3. Create a new example file with clear comments
4. Test it generates valid KiCad files

**Example - LED Driver:**
```python
# examples/led_driver_example.py
from circuit_synth import *

@circuit(name="led_driver")
def led_driver_circuit():
    """Simple LED driver with current limiting resistor."""
    
    # Components
    led = Component("Device:LED", ref="D", value="Red LED")
    resistor = Component("Device:R", ref="R", value="220R", 
                        footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Nets
    VCC = Net('VCC_5V')
    GND = Net('GND')
    led_anode = Net('LED_ANODE')
    
    # Connections
    led["A"] += led_anode
    led["K"] += GND
    resistor[1] += VCC
    resistor[2] += led_anode
    
    return circuit

if __name__ == "__main__":
    circuit = led_driver_circuit()
    circuit.generate_kicad_project("led_driver")
    print("✅ LED driver example generated!")
```

### 🦀 Option 2: Add Rust Acceleration (High Impact, 1-4 hours)

**Goal**: Take a Python function and make it 100x faster with Rust.

**Pick from these high-impact issues:**
- **Issue #40**: Component processing (97% of total time!)
- **Issue #36**: Netlist processing 
- **Issue #37**: KiCad S-expression parsing

**Steps using Claude Code:**
1. Register agents: `uv run register-agents`
2. Ask the `contributor` agent: *"I want to work on Issue #40. What should I do first?"*
3. Follow the agent's guidance for Rust setup and implementation
4. The agent will help with PyO3 bindings and testing

### 🔧 Option 3: Improve Component Search (Manufacturing Focus, 30 mins - 2 hours)

**Goal**: Make it easier to find components that are actually available for purchase.

**Ideas:**
- Add support for Digi-Key search
- Improve JLCPCB search with better filtering
- Add component alternative suggestions
- Create component availability dashboard

**Steps:**
1. Look at `src/circuit_synth/manufacturing/jlcpcb/`
2. Study the existing JLCPCB integration patterns
3. Extend or improve the search capabilities

## 🛠️ Development Workflow

### 1. Set Up Your Environment

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/your-username/circuit-synth.git
cd circuit-synth

# Install dependencies
uv sync

# Test everything works
uv run python examples/example_kicad_project.py
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# Example: git checkout -b feature/led-driver-example
```

### 3. Make Your Changes

**For examples:** Add your file to `examples/`
**For Rust:** Work in `rust_modules/` with PyO3 bindings
**For features:** Follow existing patterns in `src/circuit_synth/`

### 4. Test Your Changes

```bash
# Test your specific change
uv run python examples/your_new_example.py

# Run the full test suite
./scripts/run_all_tests.sh

# Format your code
black src/ examples/
isort src/ examples/
```

### 5. Commit and Push

```bash
git add .
git commit -m "feat: Add LED driver circuit example

- Simple current-limiting LED driver circuit
- Includes component selection and footprints
- Generates valid KiCad project files"

git push origin feature/your-feature-name
```

### 6. Create Pull Request

Use GitHub to create a PR. Include:
- **Clear description** of what you added
- **Why it's useful** for other contributors/users
- **Testing done** to verify it works

## 🛠️ Essential Commands

**Development:**
```bash
# Run all tests
./scripts/run_all_tests.sh

# Run only Python tests (fast)
./scripts/run_all_tests.sh --python-only

# Format and lint
black src/ && isort src/ && flake8 src/

# Test your changes
uv run python examples/example_kicad_project.py
```

**Claude Code commands:**
```bash
/find-symbol STM32        # Find KiCad symbols
/jlc-search ESP32         # Search JLCPCB components  
/stm32-search "3 spi"     # Advanced STM32 search
```

## 🤖 Using Claude Code for Development

**Claude Code makes development much easier:**

```bash
# Register the agents first
uv run register-agents
```

**Then ask for help:**
- *"I want to add a new voltage regulator example. What components should I use?"*
- *"How do I test my Rust module integration?"*
- *"Review my branch before I create a PR"*
- *"Find STM32s with USB and 2 UARTs available on JLCPCB"*

**Available agents (organized by category):**

**Development:** (⭐ Start here)
- `contributor` - Development process and codebase navigation

**Circuit Design:**
- `circuit-architect` - Overall circuit design guidance
- `circuit-synth` - Circuit-synth code generation specialist
- `simulation-expert` - SPICE simulation and validation

**Manufacturing:**
- `component-guru` - Component selection and JLCPCB integration
- `jlc-parts-finder` - JLCPCB component search specialist
- `stm32-mcu-finder` - STM32 peripheral search

**The `contributor` agent is your best starting point** - it knows the codebase, current priorities, and can guide you through any contribution process.

## 🏗️ Architecture Overview

Circuit-synth is designed as a **Python-first EE design tool** with **Rust acceleration** for performance-critical operations:

```
┌─────────────────────────────────────────────────────────────────┐
│  Python API Layer (User Interface)                             │
│  ├─ Circuit Definition (@circuit decorator)                    │
│  ├─ Component Library (symbols, footprints, JLCPCB)          │
│  └─ Simple Python Syntax (nets, components, connections)      │
├─────────────────────────────────────────────────────────────────┤
│  Core Engine (Python + Rust Acceleration)                     │
│  ├─ Circuit Graph Management                                   │
│  ├─ Net Analysis & Validation                                  │
│  ├─ Reference Management                                       │
│  └─ Component Placement Algorithms                             │
├─────────────────────────────────────────────────────────────────┤
│  KiCad Integration Layer                                        │
│  ├─ Schematic Generation (hierarchical sheets)                │
│  ├─ PCB Generation (component placement)                      │
│  ├─ Netlist Export/Import (.net files)                       │
│  └─ Bi-directional Sync (canonical matching)                 │
├─────────────────────────────────────────────────────────────────┤
│  Manufacturing Integration                                      │
│  ├─ JLCPCB (availability, pricing, constraints)              │
│  ├─ Component Search (STM32, modm-devices)                   │
│  └─ Future: Digi-Key, PCBWay, OSH Park                       │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/circuit_synth/
├── core/                    # Core circuit logic
│   ├── circuit.py          # Circuit class, @circuit decorator
│   ├── component.py        # Component definitions
│   ├── net.py              # Net management
│   └── reference_manager.py # R1, C1, U1 assignment
├── component_info/          # Component-specific integrations
│   ├── microcontrollers/   # STM32, ESP32, etc.
│   ├── analog/             # Op-amps, ADCs, etc.
│   ├── power/              # Regulators, switching supplies
│   └── manufacturing/      # JLCPCB, sourcing integration
├── kicad_integration/       # KiCad file generation
│   ├── schematic_generator.py
│   ├── pcb_generator.py
│   └── netlist_processor.py
└── claude_integration/      # AI agent framework
    ├── agents/             # Specialized agents
    └── commands/           # Slash commands
```

## 🦀 Rust Integration Guide

**Why Rust?** Python is great for APIs but can be slow for intensive operations. Rust gives us 100x+ speedups where it matters.

### Current Rust Modules

```
rust_modules/
├── rust_netlist_processor/     # Issue #36 (missing!)
├── rust_kicad_integration/     # Issue #37 (missing!)
├── rust_core_circuit_engine/   # Issue #38
├── rust_force_directed_placement/  # Issue #39
└── rust_component_acceleration/    # Issue #40 (97% of time!)
```

### Adding a New Rust Module

**1. Create the Rust module:**
```bash
cd rust_modules
cargo new rust_your_module --lib
cd rust_your_module
```

**2. Set up PyO3 bindings in `Cargo.toml`:**
```toml
[lib]
name = "rust_your_module"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
```

**3. Write Rust code in `src/lib.rs`:**
```rust
use pyo3::prelude::*;

#[pyfunction]
fn fast_operation(data: Vec<String>) -> PyResult<Vec<String>> {
    // Your fast Rust implementation here
    Ok(data)
}

#[pymodule]
fn rust_your_module(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_operation, m)?)?;
    Ok(())
}
```

**4. Create Python wrapper in `src/circuit_synth/`:**
```python
try:
    from rust_your_module import fast_operation
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    
def fast_operation_fallback(data):
    # Pure Python fallback
    return data

def your_operation(data):
    if RUST_AVAILABLE:
        return fast_operation(data)
    else:
        return fast_operation_fallback(data)
```

**5. Test it:**
```bash
# Build the Rust module
cd rust_modules/rust_your_module
cargo build --release

# Test Python integration
cd ../..
uv run python -c "from circuit_synth import your_operation; print('✅ Rust module works!')"
```

## 🧪 Testing Guidelines

**We use Test-Driven Development (TDD):**
1. Write tests first based on expected behavior
2. Run tests to confirm they fail (red phase)
3. Write minimal code to make tests pass (green phase)
4. Refactor and improve while keeping tests passing

### Test Structure

```
tests/
├── unit/                   # Unit tests for individual modules
├── integration/            # Integration tests across modules
├── rust_integration/       # Rust module integration tests
└── fixtures/              # Test data and helper files
```

### Running Tests

```bash
# Run all tests (Python + Rust + Integration)
./scripts/run_all_tests.sh

# Run only Python tests (fast)
./scripts/run_all_tests.sh --python-only

# Run only Rust tests
./scripts/run_all_tests.sh --rust-only

# Run specific test file
uv run pytest tests/unit/test_core_circuit.py -v

# Run with coverage
uv run pytest --cov=circuit_synth
```

### Writing Good Tests

```python
import pytest
from circuit_synth import Circuit, Component, Net

def test_led_driver_circuit():
    """Test LED driver circuit creation and validation."""
    
    # Setup
    circuit = Circuit("led_driver")
    led = Component("Device:LED", ref="D")
    resistor = Component("Device:R", ref="R", value="220R")
    
    # Test component creation
    assert led.symbol == "Device:LED"
    assert resistor.value == "220R"
    
    # Test connections
    vcc = Net("VCC_5V")
    led["A"] += vcc
    assert "VCC_5V" in [net.name for net in led.get_connected_nets()]
    
    # Test circuit generation
    kicad_files = circuit.generate_kicad_project("test_output")
    assert kicad_files["schematic"].exists()
    assert kicad_files["pcb"].exists()
```

## 🎨 What Makes Contributing Fun

**Easy Entry Points:**
- 🔍 **Component Search**: Add support for new manufacturers or component types
- 📚 **Examples**: Create circuit examples for different use cases  
- 🦀 **Rust Integration**: Add performance acceleration (100x+ speedups possible!)
- 🧪 **Testing**: Improve test coverage or add new test scenarios

**High-Impact Opportunities:**
- **Issue #40**: Component processing acceleration (97% of generation time!)
- **Issue #36**: Netlist processing with Rust
- **Issue #37**: KiCad integration compilation

**We Handle the Boring Stuff:**
- ✅ Automated testing and CI
- ✅ Documentation updates
- ✅ Code formatting and linting
- ✅ GitHub integration and workflows

## 🤝 Getting Help

**Using Claude Code:**
- Ask the `contributor` agent for onboarding help and development guidance
- Use `circuit-architect` for design questions
- Try `component-guru` for sourcing and manufacturing

**Quick start with the contributor agent:**
```bash
uv run register-agents  # Register all agents including contributor
# Then in Claude Code:
# "I want to add a new component example. Where should I start?"
```

**Traditional Support:**
- 📋 [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues) - bug reports, feature requests
- 💬 [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions) - questions, ideas

## 🎯 Tips for Success

### Make It Simple
- **Start small** - A working simple example is better than a complex broken one
- **Follow patterns** - Look at existing code and copy the style
- **Test early** - Run your code frequently to catch issues

### Ask for Help
- **GitHub Discussions** - Great for "how do I..." questions
- **GitHub Issues** - Report bugs or propose features
- **Claude Code agents** - Built-in expertise and guidance

### Focus on Real Value
- **Components that exist** - Use parts available on JLCPCB/Digi-Key
- **Circuits people build** - Common patterns, not theoretical examples
- **Performance that matters** - Rust acceleration where it helps most

## 🎯 Our Philosophy

**Circuit-synth is for electrical engineers who want to:**
- Write Python instead of clicking through GUIs
- Generate professional KiCad projects programmatically  
- Integrate with manufacturing (JLCPCB, component search, etc.)
- Use modern development practices (Git, testing, CI/CD)
- Work with AI assistance for faster development

**We believe contributing should be:**
- **Easy to start** - working environment in 5 minutes
- **Well-guided** - agents and docs help you succeed
- **Immediately useful** - see your changes work right away
- **Professionally rewarding** - learn modern EE design practices

## 🚀 Next Steps

After your first contribution:

1. **Browse the issues** - Find more ways to help
2. **Explore Rust integration** - High impact performance improvements
3. **Join discussions** - Help other contributors
4. **Suggest improvements** - You'll have ideas after using the codebase

**Most importantly**: Have fun! Circuit-synth is designed to make EE design enjoyable and productive.

---

**Ready to contribute?** Just start exploring with Claude Code or jump into an example! Questions? Ask in GitHub Discussions or use Claude Code agents - we're here to help you succeed! 🎉