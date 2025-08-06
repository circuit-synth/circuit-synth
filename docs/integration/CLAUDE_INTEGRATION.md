# Claude Code Integration

Circuit-synth includes optional integration with Claude Code for enhanced development workflows.

## Setup

```bash
pip install circuit-synth
uv run register-agents  # Register Claude Code agents
```

## Available Commands

When working in a circuit-synth project with Claude Code:

### Component Search
- `/find-symbol <name>` - Search KiCad symbol libraries
- `/find-footprint <name>` - Search KiCad footprint libraries  
- `/find_stm32 <requirements>` - Search STM32 microcontrollers

### Circuit Generation
- `/generate-validated-circuit <description>` - Generate circuit with validation
- `/validate-existing-circuit` - Check current circuit code

### Development
- `/dev-run-tests` - Run test suite
- `/dev-update-and-commit <message>` - Update docs and commit

## Agents

Circuit-synth registers several specialized agents with Claude Code:

- **circuit-synth** - Circuit code generation and KiCad integration
- **component-guru** - Component sourcing and manufacturing optimization  
- **simulation-expert** - SPICE simulation and validation
- **test-plan-creator** - Test procedure generation

## Usage

```bash
# Example workflow
/find_stm32 "3 SPIs, USB, available JLCPCB"
/generate-validated-circuit "ESP32 sensor board with I2C"
/validate-existing-circuit
```

The integration provides development assistance but is completely optional - all core functionality works without Claude Code.