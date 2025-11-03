# BLOCKED: Issue #455 - Wrong Repository

## Issue Summary
GitHub Issue #455: "Dashboard: Add system performance metrics and resource monitoring"

**Requirements:**
- Implement system resource monitoring for Raspberry Pi hosting TAC system
- Real-time CPU, memory, disk, and network monitoring
- Historical resource usage trends
- Resource constraint alerts
- Process-level monitoring for PM Agent and workers
- Thermal monitoring for Raspberry Pi

## Problem: Wrong Repository/Worktree

This issue is filed in `circuit-synth/circuit-synth` repository, but the implementation belongs in the **TAC system**.

### Evidence:
1. **Current location**: `/home/shane/Desktop/circuit-synth/trees/gh-455`
   - This is the circuit-synth library (KiCad schematic generator)
   - No dashboard, web server, or TAC system here

2. **TAC system found**: `/home/shane/Desktop/circuit-synth-tac/`
   - Separate directory exists for TAC system
   - Cannot access from current worktree (permission/path issue)

3. **Issue references**:
   - "PM Agent" - not in circuit-synth
   - "workers" - not in circuit-synth
   - "TAC system dashboard" - not in circuit-synth
   - Label `rpi-auto` confirms this is for TAC system

4. **Related issues** (all about "Dashboard"):
   - gh-452: Dashboard agent error handling
   - gh-455: Dashboard system metrics (THIS ISSUE)
   - gh-450: Dashboard token budget monitoring
   - gh-454: Dashboard PM Agent chat
   - gh-453: Dashboard maintenance tasks
   - gh-451: Dashboard live agent logs
   - gh-456: Dashboard agent activity table (ACTIVE - references dashboard_data.py)

## Root Cause

The GitHub issue #455 is filed in the wrong repository. It should be:
- **Filed in**: circuit-synth-tac repository
- **Worked on in**: `/home/shane/Desktop/circuit-synth-tac/` directory

## Required Actions

### Option 1: Work in TAC Repository (RECOMMENDED)
1. Switch to TAC repository worktree
2. Create new branch for this issue there
3. Implement dashboard monitoring in TAC codebase

### Option 2: Transfer Issue
1. Transfer issue #455 from `circuit-synth/circuit-synth` to TAC repository
2. Create appropriate worktree in TAC repo
3. Proceed with implementation

### Option 3: Build in Circuit-Synth (NOT RECOMMENDED)
- Would require building entire dashboard/TAC system from scratch
- Duplicates existing TAC infrastructure
- Doesn't align with issue description

## Questions for Human

1. **How do I access the TAC repository?**
   - Is `/home/shane/Desktop/circuit-synth-tac/` the right location?
   - Do I need different permissions/setup?

2. **Should this issue be transferred?**
   - Move from circuit-synth repo to TAC repo?
   - Or keep issues centralized in circuit-synth?

3. **What's the correct workflow?**
   - How should I work on TAC-related issues?
   - Should there be separate worktrees per repository?

## What I Can Do

Once pointed to the correct TAC codebase, I can:
- ✅ Add psutil-based system monitoring
- ✅ Implement CPU, memory, disk, network metrics
- ✅ Add Raspberry Pi thermal monitoring
- ✅ Create historical trend storage
- ✅ Build alerts and notifications
- ✅ Add process-level monitoring
- ✅ Create Plotly visualizations

## Files Referenced in Other Issues

From issue #456 (active bug):
- `dashboard_data.py` line 340-342 - exists in TAC, not circuit-synth

This confirms dashboard code is in TAC repository, not circuit-synth.
