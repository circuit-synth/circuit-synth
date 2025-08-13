# CLAUDE.md - circuit-synth

This file provides guidance to Claude Code when working on the circuit-synth project.

## Memory-Bank System

This project uses the Circuit Memory-Bank System for automatic engineering documentation and project knowledge preservation.

### Overview
The memory-bank system automatically tracks:
- **Design Decisions**: Component choices and rationale
- **Fabrication History**: PCB orders, delivery, and assembly
- **Testing Results**: Performance data and issue resolution
- **Timeline Events**: Project milestones and key dates
- **Cross-Board Insights**: Knowledge shared between PCB variants

### Multi-Level Agent System

This project uses a nested agent structure:

```
circuit-synth/
├── .claude/                    # Project-level agent
├── pcbs/
│   ├── circuit-synth-v1/
│   │   ├── .claude/           # PCB-level agent
│   │   └── memory-bank/       # PCB-specific documentation
```

### Context Switching

Use the `cs-switch-board` command to work on specific PCBs:

```bash
# Switch to specific board context
cs-switch-board circuit-synth-v1

# List available boards
cs-switch-board --list

# Check current context
cs-switch-board --status
```

**Important**: `cs-switch-board` will compress Claude's memory and reload the appropriate .claude configuration. This ensures you're working with the right context and memory-bank scope.

### Memory-Bank Files

Each PCB maintains standard memory-bank files:

- **decisions.md**: Component choices, design rationale, alternatives considered
- **fabrication.md**: PCB orders, delivery tracking, assembly notes
- **testing.md**: Test results, measurements, performance validation
- **timeline.md**: Project milestones, key events, deadlines
- **issues.md**: Problems encountered, root causes, solutions

### Automatic Documentation

The system automatically updates memory-bank files when you:
- Make git commits (primary trigger)
- Run circuit-synth commands
- Ask questions about the design
- Perform tests or measurements

**Best Practices for Commits**:
- Use descriptive commit messages explaining **why** changes were made
- Commit frequently to capture incremental design decisions
- Include context about alternatives considered
- Mention any testing or validation performed

Examples:
```bash
# Good commit messages for memory-bank
git commit -m "Switch to buck converter for better efficiency - tested 90% vs 60% with linear reg"
git commit -m "Add external crystal for USB stability - internal RC caused enumeration failures"
git commit -m "Increase decoupling cap to 22uF - scope showed 3.3V rail noise during WiFi tx"
```

### Memory-Bank Commands

```bash
# Initialize memory-bank in existing project
cs-memory-bank-init

# Remove memory-bank system
cs-memory-bank-remove

# Check memory-bank status
cs-memory-bank-status

# Search memory-bank content
cs-memory-bank-search "voltage regulator"
```

### Troubleshooting

**Context Issues**:
- If Claude seems confused about which board you're working on, use `cs-switch-board --status`
- Use `cs-switch-board {board_name}` to explicitly set context

**Memory-Bank Updates Not Working**:
- Ensure you're committing through git (primary trigger for updates)
- Check that memory-bank files exist in current board directory
- Verify .claude configuration includes memory-bank instructions

**File Corruption**:
- All memory-bank files are in git - use `git checkout` to recover
- Use `cs-memory-bank-init` to recreate missing template files

## Project-Specific Instructions

This is the circuit-synth project with memory-bank system enabled.

---

*This CLAUDE.md was generated automatically by circuit-synth memory-bank system*  
*Last updated: 2025-08-12T18:22:53.791299*
