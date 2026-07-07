# Circuit-Synth Project Structure

This document describes the organized directory structure of the circuit-synth repository.

## 📁 Root Level Organization

```
circuit-synth/
├── README.md                    # Main project documentation
├── LICENSE                      # MIT license
├── CLAUDE.md                   # Development guidelines and memory bank
├── pyproject.toml              # Python packaging and dependencies
├── uv.lock                     # Dependency lockfile
├── src/                        # Main source code
├── tests/                      # Test suite
├── examples/                   # Usage examples and demos
├── docs/                       # Documentation and guides
├── tools/                      # Development and CI tools
# (scripts/ directory removed - now consolidated in tools/)
├── docker/                     # Container definitions
├── submodules/                 # Git submodules (external projects)
├── memory-bank/                # Project knowledge and decisions
├── logs/                       # Development logs
├── test_outputs/               # Generated test files (gitignored)
└── .claude/                    # Claude Code integration
```

## 🎯 Directory Purposes

### Core Code
- **`src/circuit_synth/`** - Main Python package
  - `core/` - Core circuit design functionality
  - `kicad/` - KiCad integration and file handling
  - `component_info/` - Component intelligence and integration (organized by type)
    - `microcontrollers/` - MCU families (STM32, ESP32, PIC, AVR) 
    - `analog/` - Analog components (op-amps, ADCs, etc.)
    - `power/` - Power management components
    - `rf/` - RF/wireless components
  - `manufacturing/` - Manufacturing integrations
    - `jlcpcb/` - JLCPCB integration and availability
    - `pcbway/` - PCBWay integration (future)
    - `digikey/` - Digi-Key sourcing (future)
  - `tools/` - CLI tools and utilities (cs-new-project, cs-init-pcb)
  - `validation/` - Real-time design validation and quality assurance
  - `annotations/` - Automatic and manual circuit documentation system

### Development Tools
- **`tools/`** - Development and CI utilities
  - `ci-setup/` - Continuous integration setup scripts
  - Future: `development/`, `deployment/`, etc.

- ~~**`scripts/`**~~ - **REMOVED** (consolidated into organized `tools/` directory)
  - All functionality now in appropriate `tools/` subdirectories
  - Migration completed successfully

### Testing & Examples
- **`tests/`** - Comprehensive test suite
  - `unit/` - Unit tests
  - `integration/` - Integration tests
  - `functional_tests/` - End-to-end functionality tests

- **`examples/`** - Usage examples and demonstrations
  - Demo projects and tutorials
  - Reference designs

- **`test_outputs/`** - Generated files from testing (gitignored)

### Infrastructure
- **`docker/`** - Container infrastructure
  - Multiple Dockerfile variants
  - Docker Compose configurations
  - KiCad-integrated containers

  - Symbol processing acceleration
  - Placement algorithms
  - File I/O optimization

### Documentation & Knowledge
- **`docs/`** - Formal documentation
  - `integration/` - Integration guides (Claude Code, etc.)
  - API documentation
  - User guides

- **`memory-bank/`** - Project knowledge base
  - Technical decisions and rationale
  - Development progress tracking
  - Issue resolution patterns

### External Dependencies
- **`submodules/`** - Git submodules
  - `kicad-cli-docker/` - KiCad CLI tools
  - `pcb/` - PCB processing utilities
  - `skidl/`, `tscircuit/` - Competitive analysis
  - `modm-devices/` - STM32 pin mapping data

### AI Integration
- **`.claude/`** - Claude Code configuration (organized hierarchical structure)
  - `agents/circuit-design/` - Circuit design specialists (circuit-architect, circuit-synth, simulation-expert)
  - `agents/development/` - Development workflow agents (contributor, first_setup_agent, circuit_generation_agent)
  - `agents/manufacturing/` - Manufacturing specialists (component-guru, jlc-parts-finder, stm32-mcu-finder)
  - `commands/circuit-design/` - Circuit design commands (find-symbol, find-footprint, validate-existing-circuit)
  - `commands/development/` - Development commands (dev-update-and-commit)
  - `commands/manufacturing/` - Manufacturing commands (find-mcu, find_stm32)
  - `commands/setup/` - Setup and configuration commands (setup-kicad-plugins, setup_circuit_synth)
  - `settings.json` - Claude Code hooks and configuration
  - `AGENT_USAGE_GUIDE.md` - Complete guide for using specialized agents
  - `README_ORGANIZATION.md` - Documentation of the organized structure

## 🔧 Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python packaging, dependencies, build configuration |
| `uv.lock` | Locked dependency versions for reproducible builds |
| `CLAUDE.md` | Development guidelines, memory bank integration |
| `PROJECT_STRUCTURE.md` | This file - project organization guide |

## 🚀 Quick Access

### For Users
```bash
# Install and use
pip install circuit-synth
python examples/example_kicad_project.py
```

### For Contributors
```bash
# Development setup
git clone <repo>
cd circuit-synth
uv sync
uv run pytest
```

## 📊 Organization Benefits

### ✅ Clean Root Directory
- Essential files only at root level
- Clear project overview
- Professional appearance

### ✅ Logical Grouping
- Related functionality grouped together
- Clear separation of concerns
- Easy navigation and maintenance

### ✅ Scalable Structure
- Room for growth in each category
- Clear patterns for new additions
- Maintainable long-term organization

### ✅ Tool Integration
- CI scripts in dedicated location
- Docker tools organized separately
- Development tools separated from runtime

## 🏗️ Generated Project Structure

When you run `cs-new-project` or `cs-init-pcb`, the following organized structure is created:

```
my-sensor-board/
├── circuit-synth/               # Python circuit definitions
│   ├── main.py                 # Main hierarchical circuit
│   ├── usb.py                  # USB subcircuit
│   ├── power_supply.py         # Power subcircuit
│   └── esp32c6.py              # MCU subcircuit
├── kicad/                      # Generated KiCad files (organized)
│   ├── My_Sensor_Board.kicad_pro
│   ├── My_Sensor_Board.kicad_sch
│   ├── My_Sensor_Board.kicad_pcb
│   └── *.kicad_sch             # Hierarchical sheet files
├── memory-bank/                # AI documentation system
│   ├── decisions/              # Technical decisions
│   ├── progress/               # Development tracking
│   ├── issues/                 # Known issues and solutions
│   └── knowledge/              # Domain expertise
└── .claude/                    # Complete organized AI environment
    ├── agents/
    │   ├── circuit-design/     # Circuit specialists
    │   ├── development/        # Development workflow
    │   └── manufacturing/      # Component sourcing
    ├── commands/
    │   ├── circuit-design/     # Design commands
    │   ├── development/        # Dev commands
    │   ├── manufacturing/      # Sourcing commands
    │   └── setup/              # Configuration
    ├── AGENT_USAGE_GUIDE.md    # How to use agents effectively
    ├── README_ORGANIZATION.md  # Structure documentation
    └── settings.json           # Claude Code configuration
```

This structure supports both casual users who just want to install and use circuit-synth, and contributors who need to understand and modify the codebase effectively.