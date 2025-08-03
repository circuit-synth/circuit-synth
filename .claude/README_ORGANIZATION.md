# Claude Code Organization for Circuit-Synth

This directory contains organized agents and commands for Claude Code integration.

## 📁 Directory Structure

### Agents (`agents/`)
```
agents/
├── circuit-design/          # Circuit design and simulation
│   ├── circuit-architect.md
│   ├── circuit-synth.md
│   └── simulation-expert.md
├── development/             # Development and contribution
│   ├── contributor.md       ⭐ START HERE
│   ├── circuit_generation_agent.md
│   └── first_setup_agent.md
└── manufacturing/           # Component sourcing and manufacturing
    ├── component-guru.md
    ├── jlc-parts-finder.md
    └── stm32-mcu-finder.md
```

### Commands (`commands/`)
```
commands/
├── circuit-design/          # Design and analysis commands
│   ├── analyze-design.md
│   ├── find-footprint.md
│   ├── find-symbol.md
│   └── generate_circuit.md
├── development/             # Development workflow commands
│   ├── dev-release-pypi.md
│   ├── dev-review-branch.md
│   ├── dev-review-repo.md
│   ├── dev-run-tests.md
│   └── dev-update-and-commit.md
├── manufacturing/           # Component and MCU search
│   ├── find-mcu.md
│   └── find_stm32.md
└── setup/                   # Setup and configuration
    ├── setup-kicad-plugins.md
    └── setup_circuit_synth.md
```

## 🚀 Getting Started

1. **For Contributors**: Start with the `contributor` agent
2. **For Circuit Design**: Use `circuit-architect` or `circuit-synth` agents
3. **For Component Search**: Use agents in `manufacturing/`
4. **For Commands**: All commands are organized by purpose

## 📋 Usage

```bash
# Register all agents and commands
uv run register-agents

# Use in Claude Code
@Task(subagent_type="contributor", description="Help", prompt="How do I start contributing?")
```

The organized structure makes it easy to find the right agent or command for your specific needs!