# CLAUDE.md - circuit-synth

This file provides guidance to Claude Code when working on the circuit-synth project.

## 🚀 Multi-Agent Execution Strategy

**Default: Aggressive parallelization with Haiku 4.5**

When working on tasks, prioritize **speed and efficiency** through parallel task decomposition:

### Model Selection
- **Haiku 4.5** (Default for sub-agents):
  - Fast (3x faster than Sonnet)
  - Cost-effective (3x cheaper)
  - Use for: File searches, component lookups, validation, data extraction, tool execution

- **Sonnet 4.5** (Main agent & complex reasoning):
  - Use when Haiku encounters complexity beyond its capability
  - Complex design decisions, multi-constraint optimization, ambiguous requirements
  - **Escalation trigger**: If task requires deep reasoning, ask user then switch to Sonnet

### Parallel Execution Pattern
**Always decompose tasks into parallel sub-agents when possible:**

Example: "Design ESP32-C6 Dev Board"
1. (Sonnet) Understand requirements & create architecture
2. Launch parallel Haiku sub-agents:
   - Search ESP32-C6 symbol
   - Find USB-C footprint
   - Lookup voltage regulator
   - Search crystal oscillator
   - Validate power design

**Launch all independent sub-agents in ONE message** - not sequentially. This maximizes parallelism and speed.

### Sub-Agent Configuration
- Default model for sub-agents: `claude-haiku-4-5` (configured in `.claude/settings.json`)
- Max parallel agents: 10
- Strategy: Parallel-first (decompose aggressively)

---

## 🔄 Self-Improvement Protocol

**All agents, commands, and skills should actively improve themselves**

As you execute tasks, identify opportunities for improvement:

### When to Self-Improve
- You encounter an error or limitation in your instructions
- You discover a more efficient approach than documented
- User feedback reveals unclear or missing guidance
- You develop a valuable workaround or pattern

### How to Self-Improve
1. **Identify**: Note the specific improvement needed
2. **Ask user**: Explain the improvement and ask for approval
3. **Document**: Clearly explain what changed and why
4. **Update**: Use the Edit tool to modify the relevant file
5. **Commit**: Create a git commit describing the improvement

### Safety Guardrails
- **Ask first**: Always get user approval before applying improvements
- Only modify relevant prompt/documentation files
- Preserve core purpose and structure
- Add, don't remove (unless fixing errors)
- Use clear, professional language
- Include reasoning in commit messages

### Example Improvements
- Adding common error solutions
- Documenting edge cases discovered
- Clarifying ambiguous instructions
- Adding helpful examples
- Optimizing inefficient steps

---

## 🎛️ CIRCUIT DESIGN AGENT (PRIMARY INTERFACE)

**🚨 FOR ALL CIRCUIT-RELATED TASKS: Use the interactive-circuit-designer agent**

This agent provides professional engineering partnership throughout the complete design lifecycle with:
- Expert consultation and probing questions for optimal design decisions
- Comprehensive project memory and design decision tracking
- Component intelligence with real-time sourcing integration
- Professional documentation generation and test procedures
- Seamless support from concept through manufacturing and testing

---

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

### Library Sourcing Commands

```bash
# Setup library API credentials
cs-library-setup                     # Show setup instructions
cs-setup-snapeda-api YOUR_API_KEY    # Configure SnapEDA API
cs-setup-digikey-api API_KEY CLIENT_ID  # Configure DigiKey API

# Enhanced symbol/footprint search with fallback
/find-symbol STM32                   # Local → DigiKey GitHub → APIs
/find-footprint LQFP                 # Multi-source component search
```

### Troubleshooting

**Environment Issues - Package Conflicts**:
- **Problem**: Components placed incorrectly due to old pip-installed circuit-synth
- **Solution**: Run `./tools/maintenance/ensure-clean-environment.sh` to remove conflicting packages
- **Prevention**: Always use the cleanup script before starting work
- **Symptoms**: Layout doesn't match expected placement, import errors, outdated behavior

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

*This CLAUDE.md was updated to enable self-improving multi-agent architecture*
*Last updated: 2025-10-22*
