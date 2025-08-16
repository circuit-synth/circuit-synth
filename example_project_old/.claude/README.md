# Circuit-Synth Claude Code Integration

This directory contains specialized agents and commands for circuit-synth development with Claude Code.

## 🚀 Quick Start

### First Time Setup
```bash
# In Claude Code, run:
/setup_circuit_synth
```

This command will:
- ✅ Install circuit-synth package and dependencies
- ✅ Set up KiCad plugins for AI integration
- ✅ Configure Claude Code agents and commands
- ✅ Run validation tests to ensure everything works
- ✅ Provide personalized quick start guide

## 🤖 Available Agents

### 🛠️ first_setup_agent
**Purpose**: Comprehensive environment setup from scratch
- Detects platform and adapts installation steps
- Installs circuit-synth, KiCad plugins, and Claude integration
- Runs validation tests and provides troubleshooting
- Gets users productive immediately

### ⚡ circuit_generation_agent  
**Purpose**: Expert circuit design and code generation
- Specializes in manufacturing-ready circuit designs
- Uses proven component templates and pin mappings
- Integrates JLCPCB availability and KiCad compatibility
- Generates production-quality circuit-synth code

## 📋 Available Commands

### 🔧 /setup_circuit_synth
Complete environment setup with validation testing

### 🔍 /find_stm32 `<requirements>`
Search STM32 microcontrollers by peripheral requirements
```bash
/find_stm32 3 spi 2 uart usb available on jlcpcb
```

### ⚙️ /generate_circuit `<description>`
Generate complete circuit-synth code from description
```bash
/generate_circuit esp32 development board with usb-c power
```

## 🎯 Workflow Examples

### New User Setup
```bash
# Start here - complete setup
/setup_circuit_synth

# Find components for your project
/find_stm32 stm32g4 with 2 spi usb available jlc

# Generate circuit code
/generate_circuit stm32g4 development board with usb debugger
```

### Experienced User Workflow
```bash
# Quick component search
/find_stm32 low power 3 spi 2 uart for battery project

# Generate and iterate
/generate_circuit iot sensor node with esp32 lora and battery management
```

## 🔗 Integration Points

### KiCad Plugins
- **PCB Editor**: "Circuit-Synth AI (Simple)" toolbar button
- **Schematic Editor**: BOM plugin with full Claude chat interface
- **Auto-installation**: `/setup_circuit_synth` handles everything

### Manufacturing Integration
- **JLCPCB**: Real-time stock and pricing data
- **Component Selection**: Prioritizes available, cost-effective parts
- **Assembly Ready**: Considers manufacturing constraints

### Development Tools
- **Memory Bank**: Project context preservation across sessions
- **Testing Infrastructure**: Automated validation of generated circuits
- **Error Recovery**: Comprehensive troubleshooting and fallback options

## 📖 Success Metrics

After setup, you should be able to:

1. ✅ **Generate Circuits**: Create working circuit-synth Python code
2. ✅ **KiCad Integration**: Open generated projects without errors  
3. ✅ **AI Assistance**: Chat with Claude through KiCad plugins
4. ✅ **Component Search**: Find STM32s with specific peripherals
5. ✅ **Manufacturing Ready**: All components in stock at JLCPCB

## 🚨 Troubleshooting

### Common Issues

**KiCad Plugins Not Appearing**
```bash
# Restart KiCad after installation
# Check: KiCad → Preferences → Plugin paths
```

**Claude CLI Connection Failed**
```bash
# Verify Claude CLI installation
claude --version

# Re-authenticate if needed
claude auth login
```

**Circuit Generation Fails**
```bash
# Ensure circuit-synth is properly installed
uv run python -c "import circuit_synth; print('OK')"

# Run example to verify core functionality  
uv run python examples/example_kicad_project.py
```

## 🔄 Updates

To update the circuit-synth environment:
```bash
# Re-run setup to get latest agents and commands
/setup_circuit_synth

# Or manually update the package
pip install --upgrade circuit-synth
```

## 💡 Pro Tips

- **Use `/setup_circuit_synth` first** - it handles all the complex setup
- **Start with examples** - run the working examples before creating custom circuits
- **Test in KiCad** - always verify generated projects open correctly
- **Leverage AI chat** - use the KiCad plugins for design guidance and optimization

This integration makes circuit design as simple as describing what you want to build!