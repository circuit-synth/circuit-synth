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
├── scripts/                    # Runtime utility scripts
├── docker/                     # Container definitions
├── rust_modules/               # Rust accelerated modules
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
  - `jlc_integration/` - Manufacturing integration
  - `stm32_pinout/` - STM32 microcontroller support
  - `claude_integration/` - AI-powered design features
  - `validation/` - Real-time design validation

### Development Tools
- **`tools/`** - Development and CI utilities
  - `ci-setup/` - Continuous integration setup scripts
  - Future: `development/`, `deployment/`, etc.

- **`scripts/`** - Runtime scripts (part of installed package)
  - Docker integration scripts
  - Production deployment tools
  - KiCad environment setup

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

- **`rust_modules/`** - Performance-critical Rust modules
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

- **`external_repos/`** - External repositories
  - `modm-devices/` - STM32 pin mapping data

### AI Integration
- **`.claude/`** - Claude Code configuration
  - `agents/` - Specialized AI agents
  - `commands/` - Custom slash commands
  - `settings.json` - Claude Code hooks and configuration

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
./tools/ci-setup/setup-ci-symbols.sh
```

### For CI/CD
```bash
# CI environment setup
./tools/ci-setup/setup-ci-symbols.sh
pytest tests/ -v
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

This structure supports both casual users who just want to install and use circuit-synth, and contributors who need to understand and modify the codebase effectively.