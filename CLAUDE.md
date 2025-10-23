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

## Library Sourcing Commands

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

## Project-Specific Instructions

This is the circuit-synth project for generating KiCad PCB designs from Python code.

---

*This CLAUDE.md was updated to enable self-improving multi-agent architecture*
*Last updated: 2025-10-22*
