# BLOCKED: Issue #455 - Incorrect Repository Context

## Issue Summary
GitHub Issue #455: "Dashboard: Add system performance metrics and resource monitoring"

**Issue Description:**
- Implement system resource monitoring for Raspberry Pi hosting TAC system
- Real-time CPU, memory, disk, and network monitoring
- Historical resource usage trends
- Resource constraint alerts
- Process-level monitoring for PM Agent and workers
- Thermal monitoring for Raspberry Pi

## Problem
This issue appears to be filed in the **wrong repository** or requires clarification about where the implementation should go.

### Evidence:
1. **Current repository**: `circuit-synth/circuit-synth` - A Python library for generating KiCad schematics from code
2. **Issue context**: References "TAC system dashboard", "PM Agent", and "workers" which don't exist in circuit-synth
3. **Issue label**: `rpi-auto` - "Issue can be automated by Raspberry Pi TAC system"
4. **No existing dashboard**: circuit-synth has no web dashboard, FastAPI/Flask server, or monitoring UI

### What I Found in circuit-synth:
- Static website (`website/`) with documentation
- Performance debugging tools (`src/circuit_synth/kicad/sch_gen/debug_performance.py`)
- Cache monitoring (`tests/cache/cache_monitor.py`)
- No TAC system, PM Agent, or worker processes
- No dashboard application

## Questions Needed

1. **Where should this be implemented?**
   - Is there a separate TAC system repository?
   - Should this be a new dashboard application within circuit-synth?
   - Is the TAC system external infrastructure that manages circuit-synth workers?

2. **What is the TAC system?**
   - TAC = Task Automation and Control?
   - Is it a separate project that orchestrates circuit-synth tasks?
   - Where is the TAC system code located?

3. **Architecture clarification:**
   - Should I create a new dashboard application from scratch?
   - Should this integrate with existing circuit-synth tooling?
   - What technology stack is preferred? (FastAPI, Flask, streamlit, TUI, etc.)

4. **PM Agent and workers:**
   - What is the PM Agent?
   - What are the workers that need monitoring?
   - Are these part of circuit-synth or external?

## What I Attempted

1. ✅ Read GitHub issue #455
2. ✅ Explored circuit-synth codebase thoroughly
3. ✅ Searched for TAC, dashboard, monitoring references
4. ✅ Checked existing performance/monitoring code
5. ❌ Could not find any TAC system, dashboard, or related infrastructure

## Recommendation

**Option A**: If TAC system exists elsewhere:
- Please provide the correct repository path
- I can work on that repository instead

**Option B**: If this should be built into circuit-synth:
- Clarify the architecture and requirements
- Should this be a new web dashboard application?
- How should it integrate with existing circuit-synth code?

**Option C**: If this is a misrouted issue:
- The issue may have been filed in the wrong repository
- Should be moved to the correct repository

## Next Steps
Waiting for human guidance on:
1. Correct repository/codebase location
2. Architecture decisions if building from scratch
3. Clarification on TAC system and its relationship to circuit-synth
