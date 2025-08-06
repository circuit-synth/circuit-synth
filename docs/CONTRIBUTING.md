# Contributing to Circuit-Synth 🚀

Thank you for your interest in contributing to circuit-synth.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
```

2. Install dependencies:
```bash
uv sync
```

3. Run tests:
```bash
./scripts/run_all_tests.sh
```

4. (Optional) Register Claude Code agents:
```bash
uv run register-agents
```

## Development Workflow

1. Create a feature branch from `develop`
2. Make your changes with tests
3. Run the test suite: `./scripts/run_all_tests.sh`
4. Submit a pull request to `develop`

## Code Style

- Python: Use `black`, `isort`, `mypy`, `flake8`
- Rust: Use `cargo fmt`, `cargo clippy`
- Write tests for new functionality
- Update documentation as needed


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

## 🤖 Alternative AI Tools

While optimized for Claude Code, other tools work too:
- **ChatGPT/GPT-4**: Provide this CONTRIBUTING.md for context
- **Cursor/GitHub Copilot**: Good code completion with our patterns  
- **Any LLM**: Extensive documentation designed for AI agent consumption

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

---

## Traditional Contributing Guide

### Development Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shanemattner/circuit-synth.git
   cd circuit-synth
   ```

2. **Install dependencies with uv** (recommended):
   ```bash
   # Install UV if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install project in development mode
   uv sync
   ```

3. **Optional: Enable Rust acceleration** (6x performance boost):
   ```bash
   # Install Rust toolchain if not already installed
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env
   
   # Install maturin for Python-Rust bindings
   pip install maturin
   
   # Compile Rust modules for performance acceleration
   cd rust_modules/rust_kicad_integration
   maturin develop --release
   cd ../..
   ```

4. **Verify installation** (with optional Rust acceleration):
   ```bash
   uv run python examples/example_kicad_project.py
   # If Rust is compiled, you'll see performance improvements in the logs
   ```

### Development Workflow

#### 1. Set Up Your Environment

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/your-username/circuit-synth.git
cd circuit-synth

# Install dependencies
uv sync

# Test everything works
uv run python examples/example_kicad_project.py
```

#### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# Example: git checkout -b feature/led-driver-example
```

#### 3. Make Your Changes

**For examples:** Add your file to `examples/`
**For Rust:** Work in `rust_modules/` with PyO3 bindings
**For features:** Follow existing patterns in `src/circuit_synth/`

#### 4. Test Your Changes

```bash
# Test your specific change
uv run python examples/your_new_example.py

# Run the full test suite
./scripts/run_all_tests.sh

# Format your code
black src/ examples/
isort src/ examples/
```

#### 5. Commit and Push

```bash
git add .
git commit -m "feat: Add LED driver circuit example

- Simple current-limiting LED driver circuit
- Includes component selection and footprints
- Generates valid KiCad project files"

git push origin feature/your-feature-name
```

#### 6. Create Pull Request

Use GitHub to create a PR. Include:
- **Clear description** of what you added
- **Why it's useful** for other contributors/users
- **Testing done** to verify it works

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

## Types of Contributions

### 🐛 Bug Reports

**Before submitting**:
- Search existing issues to avoid duplicates
- Test with the latest version
- Include reproduction steps

**Include in your report**:
- Circuit-synth version (`import circuit_synth; print(circuit_synth.__version__)`)
- Python version and operating system
- KiCad version (if relevant)
- Minimal code example that reproduces the issue
- Expected vs. actual behavior
- Error messages and stack traces

### 💡 Feature Requests

**Good feature requests**:
- Clearly describe the problem you're trying to solve
- Explain how it fits with Circuit-Synth's goals
- Consider implementation complexity
- Provide use cases and examples

### 🔧 Code Contributions

**Development Process**:

1. **Create an issue** discussing your planned changes
2. **Fork the repository** and create a feature branch
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Submit a pull request**

**Code Standards**:

```bash
# Format code
uv run black src/
uv run isort src/

# Lint code
uv run flake8 src/
uv run mypy src/

# Run tests
uv run pytest
```

## Development Guidelines

### Code Style

- **Follow PEP 8** with line length of 88 characters
- **Use type hints** for all public functions
- **Write docstrings** for classes and public methods
- **No bare `except` clauses** - always specify exception types


### Documentation

**Documentation Requirements**:
- Update README.md for user-facing changes
- Add docstrings for new public APIs
- Include code examples for new features
- Update relevant documentation files

**Example Documentation**:
```python
def generate_kicad_project(self, project_name: str, 
                          generate_pcb: bool = True,
                          force_regenerate: bool = True) -> None:
    """
    Generate a complete KiCad project from this circuit.
    
    Args:
        project_name: Name for the generated KiCad project
        generate_pcb: Whether to generate PCB file (default: True)
        force_regenerate: Force regeneration of existing files (default: True)
        
    Example:
        >>> circuit = esp32s3_simple()
        >>> circuit.generate_kicad_project("my_project")
        
    Raises:
        CircuitError: If circuit validation fails
        FileNotFoundError: If required libraries are missing
    """
```

## Project Architecture

### Core Components

- **`src/circuit_synth/core/`**: Core circuit design functionality
- **`src/circuit_synth/kicad/`**: KiCad integration (schematics, symbols, S-expressions)
- **`src/circuit_synth/pcb/`**: PCB generation and layout
- **`src/circuit_synth/ai_integration/`**: AI-assisted circuit design tools

### Architecture Overview

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

Circuit-synth uses a **JSON-centric architecture** where JSON serves as the canonical intermediate representation between Python circuit definitions and KiCad files. This enables:

- **Round-trip conversion**: Python ↔ JSON ↔ KiCad without data loss
- **Hierarchical design**: Full circuit hierarchy preserved in JSON
- **Version control**: Human-readable JSON format ideal for Git

For detailed architecture documentation, see **[docs/ARCHITECTURE.md](ARCHITECTURE.md)**.

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

### Key Design Principles

1. **Simple Python Code**: No special DSL - just Python classes
2. **Transparent Output**: Generated KiCad files are human-readable
3. **Bidirectional**: Support import from existing KiCad projects
4. **Professional Workflow**: Integrate with existing EE processes

### 🦀 Rust Integration Guide

**Why Rust?** Python is great for APIs but can be slow for intensive operations. Rust gives us 100x+ speedups where it matters.

#### Current Rust Modules

```
rust_modules/
├── rust_netlist_processor/     # Issue #36 (missing!)
├── rust_kicad_integration/     # Issue #37 (missing!)
├── rust_core_circuit_engine/   # Issue #38
├── rust_force_directed_placement/  # Issue #39
└── rust_component_acceleration/    # Issue #40 (97% of time!)
```

#### Adding a New Rust Module

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

### Adding New Features

**Feature Development Process**:

1. **Design Phase**:
   - Create design document explaining the feature
   - Consider impact on existing APIs
   - Plan backward compatibility

2. **Implementation Phase**:
   - Start with failing tests (TDD approach)
   - Implement minimal functionality
   - Iterate with feedback

3. **Integration Phase**:
   - Ensure all regression tests pass
   - Update examples if needed
   - Document new functionality

## Submitting Changes

### Pull Request Guidelines

**PR Requirements**:
- **Descriptive title** and detailed description
- **Reference related issues** (e.g., "Fixes #123")
- **Include tests** for new functionality
- **Update documentation** if needed
- **All CI checks pass**

**PR Template**:
```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that breaks existing functionality)
- [ ] Documentation update

## Testing
- [ ] All regression tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Changes are backward compatible (or breaking changes documented)
```

### Review Process

**What to Expect**:
- Initial feedback within 48 hours
- Constructive code review focusing on:
  - Code quality and maintainability
  - Test coverage and reliability
  - Documentation completeness
  - Performance implications

**Addressing Feedback**:
- Respond to all review comments
- Make requested changes in additional commits
- Ask questions if feedback is unclear
- Mark conversations as resolved when addressed

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

## Community Guidelines

### Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, nationality, or other similar characteristics.

**Expected Behavior**:
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

**Unacceptable Behavior**:
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Communication

**Preferred Channels**:
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Pull Requests**: Code review and discussion

**Communication Guidelines**:
- Be respectful and constructive
- Stay on topic
- Help others learn and grow
- Assume good intentions

## Recognition

Contributors who make significant contributions will be:
- Added to the CONTRIBUTORS.md file
- Mentioned in release notes
- Credited in documentation where appropriate

## 🚀 Next Steps

After your first contribution:

1. **Browse the issues** - Find more ways to help
2. **Explore Rust integration** - High impact performance improvements
3. **Join discussions** - Help other contributors
4. **Suggest improvements** - You'll have ideas after using the codebase

**Most importantly**: Have fun! Circuit-synth is designed to make EE design enjoyable and productive.

Thank you for helping make Circuit-Synth better! 🚀

---

**Ready to contribute?** Just start exploring with Claude Code or jump into an example! Questions? Ask in [GitHub Discussions](https://github.com/shanemattner/circuit-synth/discussions) or use Claude Code agents - we're here to help you succeed! 🎉