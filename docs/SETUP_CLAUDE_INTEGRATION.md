# Claude Code Integration Setup Guide

This guide shows how to set up Claude Code integration with circuit-synth for AI-powered circuit design.

## Quick Start

### For PyPI Users (Recommended)

After installing circuit-synth from PyPI:

```bash
# Install circuit-synth
pip install circuit-synth

# Set up Claude Code integration
setup-claude-integration
```

This command will:
- ✅ Copy agent training examples (10+ circuits)
- ✅ Copy design knowledge memory-bank (60+ documents)  
- ✅ Copy CLAUDE.md project instructions
- ✅ Create .claude configuration file
- ✅ Register specialized circuit design agents
- ✅ Enable real-time validation hooks

### For Development/CI-CD Environments

```bash
# Target specific directory
setup-claude-integration --target-dir /path/to/project

# Or use Python directly
python -m circuit_synth.tools.setup_claude
```

## What Gets Installed

### 1. Agent Training Examples (`examples/`)

**Progressive Learning Series:**
- `power/01_basic_ldo_3v3.py` - Basic 3.3V regulation
- `interfaces/01_basic_usb_c.py` - USB-C with protection
- `microcontrollers/01_esp32_minimal.py` - ESP32 basics
- `microcontrollers/02_stm32_with_crystal.py` - STM32 + crystal
- `03_complete_stm32_development_board.py` - Full system

**Component Categories:**
- **Power Management**: LDO regulators, decoupling, power distribution
- **Interface Design**: USB-C, connectors, protection circuits
- **Microcontroller Integration**: STM32, ESP32, crystal oscillators
- **Analog Circuits**: Op-amps, filters, sensors (coming soon)
- **Protection Circuits**: ESD, overcurrent, thermal (coming soon)

### 2. Design Knowledge Memory-Bank (`memory-bank/`)

**Organized Technical Knowledge:**
- `progress/` - Development milestones and technical breakthroughs
- `patterns/` - Reusable circuit design patterns
- `knowledge/` - Domain-specific expertise (STM32, JLCPCB, KiCad)
- `planning/` - Agent architecture and development strategies
- `issues/` - Known problems and workarounds

**Key Knowledge Documents:**
- STM32 peripheral search patterns
- JLCPCB component availability workflows
- KiCad symbol/footprint mapping strategies
- Agent coordination and specialization patterns

### 3. Project Instructions (`CLAUDE.md`)

**Complete Development Workflow:**
- Essential commands (git, docker, testing)
- Code quality guidelines and best practices
- Agent workflow and coordination strategies
- STM32 peripheral search optimization
- Memory bank usage patterns
- Circuit-synth specific knowledge

### 4. Configuration (`.claude`)

**Real-time Validation Hooks:**
- Component availability checking
- Design rule validation
- STM32 pin assignment verification
- Manufacturing readiness assessment

**Memory Management:**
- Context preservation across sessions
- Automatic example loading
- Memory bank integration

## Available Agents After Setup

### 🤖 Specialized Circuit Design Agents

**circuit-synth** - Circuit-synth code generation specialist
   - Expert circuit-synth Python code generation
   - KiCad symbol/footprint integration
   - JLCPCB component availability verification
   - Manufacturing-ready designs with verified components

### ⚡ Useful Shortcut

- `/check-manufacturing` - Real-time component availability check

## Usage Examples

### Basic Circuit Design

```bash
# Ask Claude to design a circuit
"Design an STM32 development board with USB-C power"

# The circuit-synth agent will:
# 1. Analyze requirements
# 2. Select appropriate STM32 (with stock checking)
# 3. Design power regulation circuit
# 4. Add programming interfaces
# 5. Generate production-ready Python code
```

### Component Selection

```bash
# Intelligent component queries
"Find STM32 with 3 SPI interfaces available on JLCPCB"

# The circuit-synth agent will:
# 1. Search modm-devices database
# 2. Check JLCPCB availability  
# 3. Verify KiCad symbol compatibility
# 4. Return optimized selections with working code
```

### Quick Component Check

```bash
# Check manufacturing readiness
"/check-manufacturing"

# The circuit-synth agent will:
# 1. Extract all components from current design
# 2. Check real-time JLCPCB availability
# 3. Suggest alternatives for out-of-stock parts
# 4. Validate DFM compliance
```

## Advanced Configuration

### Custom Target Directory

```bash
# Set up in specific project directory
setup-claude-integration --target-dir ./my-circuit-project

# Verify setup
ls ./my-circuit-project
# Should show: examples/, memory-bank/, CLAUDE.md, .claude
```

### CI/CD Integration

```bash
# In CI/CD pipelines
export CI=true
setup-claude-integration --target-dir $BUILD_DIR

# This enables:
# - Batch processing mode
# - Detailed logging
# - Strict component validation
# - Automated failure handling
```

### Updating Installation

```bash
# Update to latest examples and knowledge
setup-claude-integration  # Will update existing installation

# Or force clean reinstall
rm -rf examples memory-bank CLAUDE.md .claude
setup-claude-integration
```

## Troubleshooting

### Common Issues

**1. "Package data directory not found"**
```bash
# Reinstall circuit-synth with data files
pip uninstall circuit-synth
pip install circuit-synth

# Or use development mode
pip install -e .
```

**2. "Claude Code not found in PATH"**
```bash
# Install Claude Code CLI
# See: https://claude.ai/code

# Or continue without CLI (reduced functionality)
# Basic circuit-synth will still work
```

**3. "Permission denied" errors**
```bash
# Ensure write permissions to target directory
chmod +w .
setup-claude-integration
```

### Verification

**Check Installation:**
```bash
# Verify all components installed
ls -la
# Should show: examples/, memory-bank/, CLAUDE.md, .claude

# Check example count
find examples -name "*.py" | wc -l
# Should show: 10+ example circuits

# Check knowledge count  
find memory-bank -name "*.md" | wc -l
# Should show: 60+ knowledge documents
```

**Test Agent Integration:**
```bash
# Test if agents are registered (requires Claude Code CLI)
claude list-agents
# Should show circuit design agents

# Test intelligent commands
claude help
# Should show /analyze-power, /optimize-routing, etc.
```

## Next Steps

After setup completion:

1. **Try a Simple Design:**
   ```
   Ask Claude: "Create a basic LED blink circuit with STM32"
   ```

2. **Explore Examples:**
   ```bash
   cd examples/agent-training
   # Review progressive examples from basic to advanced
   ```

3. **Learn the Workflow:**
   ```bash
   cd memory-bank/planning
   cat agent-architecture-design.md
   # Understand how agents coordinate
   ```

4. **Design Real Circuits:**
   ```
   Ask Claude: "Design a USB-C powered sensor node with STM32 and I2C sensors"
   ```

## Advanced Features

### Dynamic Component Updates

The setup includes tools for keeping component availability current:

```bash
# Update component stock levels (weekly recommended)
python tools/update_examples_with_stock.py

# This updates all examples with:
# - Current JLCPCB stock levels
# - Optimized component selections
# - Updated pricing information
```

### Custom Agent Training

Add your own circuit patterns to `examples/agent-training/`:

```python
# examples/agent-training/custom/my_circuit.py
from circuit_synth import Circuit, Component, Net, circuit

@circuit
def my_custom_circuit():
    """
    Custom circuit description for agent training.
    
    Include detailed comments explaining design decisions,
    component selections, and implementation strategies.
    """
    # Your implementation here
```

### Memory Bank Contributions

Document your circuit design insights in `memory-bank/`:

```markdown
# memory-bank/patterns/my-design-pattern.md

## Custom Design Pattern

### Summary
Description of your reusable circuit pattern

### Implementation
Circuit-synth code examples and usage

### Applications
When and why to use this pattern
```

## Support

- **Issues**: https://github.com/circuit-synth/circuit-synth/issues
- **Documentation**: https://circuit-synth.readthedocs.io
- **Examples**: Browse `examples/` directory after setup
- **Community**: Join discussions in GitHub issues

---
*Generated by circuit-synth v0.1.1 setup-claude-integration*