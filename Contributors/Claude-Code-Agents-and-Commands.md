# Claude Code Agents and Commands Reference

**Circuit-synth is specifically designed to work with Claude Code.** This document details all available agents and commands that make development incredibly productive.

## 🤖 Why Claude Code?

Circuit-synth is **built from the ground up** for Claude Code integration:

- **Specialized Domain Knowledge**: Our agents understand EE design patterns, KiCad workflows, and manufacturing constraints
- **Automated Development Workflows**: From issue analysis to PR creation, everything is automated
- **Performance Optimization Guidance**: Agents help optimize for our Python+Rust hybrid architecture
- **Test-Driven Development**: Built-in TDD workflow assistance and validation
- **Manufacturing Integration**: Deep integration with JLCPCB, component search, and availability checking

**While other AI tools can help**, Claude Code provides the **most comprehensive and productive** circuit-synth development experience.

## 🎯 Specialized Circuit-Synth Agents

### 1. **contributor** (Development Assistant)
**Purpose**: Onboarding and development assistance for contributors
**Use Cases**:
- Understanding codebase architecture
- Following coding conventions  
- Navigating Rust/Python integration
- Writing proper tests using TDD
- Code review preparation

**Example Usage**:
```
👤 "I want to contribute to the Rust integration. Where should I start?"

🤖 contributor agent:
   📚 Reading Contributors/Rust-Integration-Guide.md...
   🎯 Based on current performance analysis, Issue #40 (rust_component_acceleration) 
      has the highest impact - 97% of generation time is spent here!
   📋 Here's your step-by-step approach:
   1. Review the performance data (1796ms for 6 components)
   2. Study the existing rust_kicad_integration pattern
   3. Implement ComponentProcessor with PyO3 bindings
   🚀 Let's start with environment setup...
```

### 2. **circuit-architect** (Master Circuit Design Coordinator)
**Purpose**: Coordinates complex multi-step circuit design projects
**Use Cases**:
- Breaking down complex circuit requirements
- Managing hierarchical circuit design
- Coordinating between multiple specialized agents
- Ensuring design consistency and best practices

**Example Usage**:
```
👤 "Design a complete ESP32 IoT sensor board with LoRaWAN, solar charging, and environmental sensors"

🤖 circuit-architect agent:
   🎯 Breaking down requirements:
   - Power management (solar + battery + 3.3V regulation)
   - ESP32-S3 with WiFi/BLE capability
   - LoRaWAN transceiver (SX1276/SX1262)
   - Environmental sensors (BME280, light sensor)
   - Charging circuit with MPPT
   📋 Delegating to specialists:
   - power-expert: Solar charging and power management
   - component-guru: JLCPCB availability and sourcing
   - signal-integrity: RF layout considerations
   🚀 Starting with power supply architecture...
```

### 3. **power-expert** (Power Supply and Regulation Specialist) 
**Purpose**: Specialized in power supply design, regulation, and power management
**Use Cases**:
- Power supply topology selection
- Regulator selection and design
- Battery charging circuits
- Power consumption optimization
- Thermal management

**Example Usage**:
```
👤 "I need a 5V to 3.3V regulator that can handle 2A with good efficiency"

🤖 power-expert agent:
   🔍 Analyzing requirements: 5V→3.3V, 2A, efficiency priority
   📊 Recommending switching regulator (vs linear):
   - Linear: 66% efficiency, 6.8W heat dissipation
   - Switching: 90%+ efficiency, <1W heat dissipation
   🔧 Top recommendations:
   1. TPS54331 (3A, 95% efficiency, JLCPCB: ✅)
   2. LM2596S-3.3 (3A, 92% efficiency, JLCPCB: ✅)
   ⚡ Generating complete power supply circuit with:
   - Input/output capacitors for stability
   - Feedback network for precise regulation
   - Overcurrent and thermal protection
```

### 4. **signal-integrity** (High-Speed PCB Design Expert)
**Purpose**: High-speed design, signal integrity, and PCB layout optimization
**Use Cases**:
- High-speed signal routing guidelines
- Impedance control and matching
- EMI/EMC considerations
- Crystal oscillator placement
- USB, Ethernet, RF layout

**Example Usage**:
```
👤 "I have USB 2.0 signals on my ESP32 board. What are the layout considerations?"

🤖 signal-integrity agent:
   📡 USB 2.0 signal integrity requirements:
   - Differential impedance: 90Ω ± 10%
   - Trace length matching: ± 0.1mm (2.5 mils)
   - Minimum trace width: 0.1mm (4 mils) for 90Ω on standard 4-layer
   🛡️ EMI considerations:
   - Ground plane under USB traces
   - Keep away from switching regulators (>10mm)
   - Series termination resistors (22Ω typical)
   📏 Layout guidelines:
   - Route on internal layer with solid ground plane
   - Avoid vias in differential pair
   - 45° or curved bends only (no 90° angles)
```

### 5. **component-guru** (Manufacturing and Sourcing Specialist)
**Purpose**: Component selection, manufacturing constraints, and sourcing optimization
**Use Cases**:
- JLCPCB component availability checking
- Alternative component recommendations
- Cost optimization strategies
- Assembly constraints and recommendations
- Component lifecycle and availability

**Example Usage**:
```
👤 "Find me a low-cost op-amp for audio applications, available on JLCPCB"

🤖 component-guru agent:
   🔍 Searching JLCPCB for audio op-amps...
   💰 Cost-optimized recommendations:
   1. LM358 (Dual, $0.026, Stock: 15,420, THD: 0.1%)
   2. TL072 (JFET, $0.089, Stock: 8,340, Low noise: 18nV/√Hz)
   3. OPA2134 (High-end, $1.45, Stock: 234, THD: 0.00008%)
   
   🏭 Manufacturing considerations:
   - All available in SOIC-8 (easy assembly)
   - Lead time: <3 days for quantities <1000
   - Assembly: No special handling requirements
   
   🎵 Audio performance:
   - LM358: Good for basic audio, cost-sensitive
   - TL072: Best balance of cost/performance
   - OPA2134: Audiophile grade, high cost
   
   ✅ Recommendation: TL072 for best cost/performance balance
   📦 Generating component with verified JLCPCB part number...
```

## 🛠️ Circuit-Synth Commands

### Development Commands

#### `/dev-review-branch`
**Purpose**: Comprehensive branch review before creating PR
**Usage**: `/dev-review-branch [branch-name]`
**What it does**:
- Analyzes all changes in the branch
- Runs test suite and reports results
- Checks code quality and conventions
- Identifies potential issues or improvements
- Generates PR description template

**Example**:
```bash
/dev-review-branch feature/rust-component-acceleration

🔍 Analyzing branch: feature/rust-component-acceleration
📊 Changes detected:
  - New Rust module: rust_modules/rust_component_acceleration/
  - Python integration: src/circuit_synth/core/rust_integration.py
  - Tests: tests/rust_integration/test_component_acceleration.py

🧪 Test Results:
  ✅ All existing tests pass
  ✅ New Rust integration tests pass
  📈 Performance improvement: 149x speedup confirmed

📝 Code Quality:
  ✅ Rust code follows conventions (rustfmt, clippy)
  ✅ Python code follows PEP 8
  ✅ Comprehensive test coverage added

🚀 Ready for PR! Suggested title:
"feat: Rust Component Acceleration - 149x Performance Improvement"
```

#### `/dev-review-repo`
**Purpose**: Comprehensive repository analysis and health check
**Usage**: `/dev-review-repo`
**What it does**:
- Analyzes entire repository structure
- Identifies technical debt and improvement opportunities
- Checks test coverage and quality
- Reviews documentation completeness
- Suggests optimization opportunities

#### `/dev-update-and-commit "description"`
**Purpose**: Update documentation and commit changes atomically
**Usage**: `/dev-update-and-commit "Added rust component acceleration"`
**What it does**:
- Updates relevant documentation automatically
- Runs tests to ensure changes don't break anything
- Creates comprehensive commit with proper formatting
- Updates Contributors/ docs if needed

### Component Search Commands

#### `/find-symbol <search-term>`
**Purpose**: Search KiCad symbol libraries
**Usage**: `/find-symbol STM32`, `/find-symbol USB connector`
**What it does**:
- Searches across all available KiCad symbol libraries
- Returns exact symbol names for use in Component() definitions
- Shows library path and symbol details
- Verifies symbol exists and is accessible

**Example**:
```bash
/find-symbol STM32F407

🔍 Searching KiCad symbols for: STM32F407
📚 Found in MCU_ST_STM32F4 library:
  ✅ STM32F407VETx (LQFP-100)
  ✅ STM32F407VGTx (LQFP-100) 
  ✅ STM32F407ZETx (LQFP-144)
  ✅ STM32F407ZGTx (LQFP-144)

💡 Usage example:
mcu = Component(
    symbol="MCU_ST_STM32F4:STM32F407VETx",
    ref="U",
    footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm"
)
```

#### `/find-footprint <search-term>`
**Purpose**: Search KiCad footprint libraries  
**Usage**: `/find-footprint LQFP-100`, `/find-footprint USB-C`
**What it does**:
- Searches KiCad footprint libraries
- Returns exact footprint names for Component() definitions
- Shows package dimensions and specifications
- Verifies footprint exists and provides usage examples

#### `/jlc-search <search-term>`
**Purpose**: Search JLCPCB component database
**Usage**: `/jlc-search ESP32`, `/jlc-search "1uF capacitor"`
**What it does**:
- Searches JLCPCB's component database
- Shows real-time stock levels and pricing
- Provides JLCPCB part numbers
- Includes basic vs extended part information
- Suggests alternatives if out of stock

**Example**:
```bash
/jlc-search ESP32-S3

🏭 JLCPCB Search Results for: ESP32-S3
💰 Basic Parts (cheaper assembly):
  ✅ ESP32-S3-WROOM-1-N16R8 (C2913206)
     Stock: 2,847 | Price: $3.45 | Package: SMD
     WiFi + Bluetooth, 16MB Flash, 8MB RAM

📦 Extended Parts (higher assembly cost):
  ✅ ESP32-S3-MINI-1-N8 (C2838571)  
     Stock: 1,234 | Price: $2.89 | Package: SMD
     WiFi + Bluetooth, 8MB Flash, No external RAM

🔧 Recommended for new designs:
ESP32-S3-WROOM-1-N16R8 (best balance of features/availability)

💡 Usage:
esp32 = Component(
    symbol="RF_Module:ESP32-S3-WROOM-1",
    ref="U",
    footprint="RF_Module:ESP32-S3-WROOM-1", 
    jlc_part="C2913206"
)
```

#### `/stm32-search <requirements>`
**Purpose**: Advanced STM32 search with peripheral requirements
**Usage**: `/stm32-search "3 spi 2 uart jlcpcb"`, `/stm32-search "usb adc 12bit available"`
**What it does**:
- Searches modm-devices database for STM32s matching requirements
- Cross-references with JLCPCB availability
- Verifies KiCad symbols exist
- Provides complete component specifications

**Example**:
```bash
/stm32-search "3 spi 2 uart jlcpcb available"

🔍 STM32 Search: 3x SPI, 2x UART, JLCPCB available
📊 Found 12 matching STM32s:

🥇 Top Recommendations:
1. STM32F407VETx (LQFP-100)
   - SPI: 3x, UART: 4x (exceeds requirement)
   - JLCPCB: ✅ C13749 ($8.45, Stock: 1,847)
   - KiCad: ✅ MCU_ST_STM32F4:STM32F407VETx
   - Features: 168MHz, 512KB Flash, 192KB RAM, USB, CAN

2. STM32G474RETx (LQFP-64)  
   - SPI: 4x, UART: 5x (exceeds requirement)
   - JLCPCB: ✅ C2843621 ($4.23, Stock: 892)
   - KiCad: ✅ MCU_ST_STM32G4:STM32G474RETx
   - Features: 170MHz, 512KB Flash, 128KB RAM, USB

💡 Complete component example:
stm32 = Component(
    symbol="MCU_ST_STM32F4:STM32F407VETx",
    ref="U", 
    footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm",
    jlc_part="C13749"
)
```

### Circuit Design Commands

#### `/generate-power-supply <specs>`
**Purpose**: Generate power supply circuits with specifications
**Usage**: `/generate-power-supply "5V to 3.3V 2A switching"`
**What it does**:
- Analyzes requirements and selects optimal topology
- Chooses appropriate components with JLCPCB availability
- Generates complete Python circuit code
- Includes protection circuits and stability components

#### `/generate-usb-interface <type>`
**Purpose**: Generate USB interface circuits
**Usage**: `/generate-usb-interface "USB-C PD"`, `/generate-usb-interface "USB 2.0"`
**What it does**:
- Creates complete USB interface with proper termination
- Includes ESD protection and filtering
- Adds appropriate connectors and supporting components
- Follows USB specification requirements

#### `/validate-circuit <circuit-name>`
**Purpose**: Comprehensive circuit validation and analysis
**Usage**: `/validate-circuit my_power_supply`
**What it does**:
- Checks electrical connectivity and design rules
- Validates component selections and ratings
- Identifies potential issues or improvements
- Suggests optimization opportunities

## 🎯 Agent and Command Best Practices

### When to Use Which Agent

**circuit-architect**: Complex multi-domain projects requiring coordination
```
👤 "Design a complete IoT sensor board with multiple subsystems"
🤖 Use circuit-architect → delegates to specialists
```

**power-expert**: Any power-related design questions
```
👤 "What's the best way to convert 12V to 5V efficiently?"
🤖 Use power-expert → topology analysis and component selection
```

**component-guru**: Component selection, availability, alternatives
```
👤 "Find a low-cost MCU available on JLCPCB with USB"
🤖 Use component-guru → JLCPCB search with requirements analysis
```

**signal-integrity**: High-speed signals, layout, EMI/EMC
```
👤 "How should I route Ethernet signals on my PCB?"
🤖 Use signal-integrity → layout guidelines and best practices
```

**contributor**: Development, contribution, codebase questions
```
👤 "How do I add a new Rust module to circuit-synth?"
🤖 Use contributor → development guidance and architecture explanation
```

### Command Chaining and Workflows

**Typical Design Workflow:**
```bash
# 1. Find components
/jlc-search "ESP32-S3"
/find-symbol ESP32-S3
/find-footprint ESP32-S3

# 2. Design power supply
/generate-power-supply "USB 5V to 3.3V 1A linear"

# 3. Validate design
/validate-circuit esp32_board

# 4. Development workflow (for contributors)
/dev-review-branch feature/esp32-board
/dev-update-and-commit "Added ESP32-S3 development board example"
```

## 🔄 Keeping Agents and Commands Updated

### Auto-Update Mechanism

**Location**: `.github/workflows/update-docs.yml`
```yaml
# Automatically update Contributors/ docs when agents/commands change
name: Update Contributor Documentation

on:
  push:
    paths:
      - 'src/circuit_synth/claude_integration/agents/*.py'
      - 'src/circuit_synth/claude_integration/commands/*.py'
      - '.claude/agent_config.json'

jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
    - name: Update Contributors documentation
      run: |
        python scripts/update_contributor_docs.py
        # Auto-commit if changes detected
```

### Manual Review Trigger

**Location**: `scripts/review_agents_and_commands.py`
```python
"""
Review script for agents and commands - run periodically to ensure:
- All agents and commands have a clear use case
- Naming conventions are consistent and intuitive  
- No redundant or unused agents/commands
- Missing agents/commands for common activities are identified
"""

def review_agents():
    """Review all registered agents for utility and naming."""
    agents = load_all_agents()
    
    for agent in agents:
        print(f"Agent: {agent.name}")
        print(f"  Description: {agent.description}")
        print(f"  Capabilities: {agent.get_capabilities()}")
        print(f"  Usage examples: {len(agent.usage_examples)}")
        print(f"  Last used: {agent.get_usage_stats()}")
        print()
    
    # Suggest improvements, identify unused agents, etc.

def review_commands():
    """Review all commands for utility and naming."""
    # Similar analysis for commands
    pass

if __name__ == "__main__":
    review_agents()
    review_commands()
```

### Update Reminder System

**Location**: `CLAUDE.md` (Development commands section)
```markdown
## Contributors Documentation Update Protocol

**IMPORTANT**: When making changes to agents or commands, always update Contributors/ documentation:

### Automatic Updates
- Agent/command changes trigger automatic doc updates via GitHub Actions
- Contributors/Claude-Code-Agents-and-Commands.md is automatically regenerated

### Manual Review Required
Run this command after significant agent/command changes:
```bash
python scripts/review_agents_and_commands.py
```

### Update Checklist
- [ ] New agents have clear use cases and examples
- [ ] Command naming follows conventions (/dev-*, /find-*, /generate-*)
- [ ] No duplicate functionality between agents
- [ ] Contributors/ docs reflect current capabilities
- [ ] All agents include usage examples and best practices
```

## 📊 Current Agent/Command Audit (as of Latest Update)

### ✅ Well-Utilized Agents
- **contributor**: High usage, clear value for onboarding
- **circuit-architect**: Essential for complex designs
- **component-guru**: Critical for JLCPCB integration

### ⚠️ Agents Needing Review
- **power-expert**: Good concept, needs more specialized knowledge
- **signal-integrity**: Valuable but may need more specific expertise

### 🔄 Commands Needing Updates
- `/dev-review-branch`: Implementation needed
- `/dev-review-repo`: Implementation needed  
- `/stm32-search`: Working well, may need expanded peripheral database

### 💡 Suggested New Agents/Commands
- **simulation-expert**: SPICE simulation and analysis
- **manufacturing-optimizer**: DFM analysis and cost optimization
- `/generate-test-circuit`: Generate test and validation circuits
- `/optimize-bom`: Analyze and optimize bill of materials

---

**This comprehensive agent and command system makes circuit-synth the most productive EE design environment available. The tight integration with Claude Code provides unmatched development velocity and design quality.** 🚀