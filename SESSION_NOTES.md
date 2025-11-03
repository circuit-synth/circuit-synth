# Session Notes: TAC-8 Coordinator Setup & Planning

**Date**: November 2, 2025
**Session Duration**: ~3 hours
**Status**: Planning phase complete, ready for implementation

---

## 🎯 What We Accomplished

### 1. Successfully Tested End-to-End Autonomous Workflow

**Test Issue**: #471 - "Add docstring to coordinator.py"
- ✅ Coordinator spawned worker agent
- ✅ Worker autonomously made code changes
- ✅ Worker created PR #473: https://github.com/circuit-synth/circuit-synth/pull/473
- ✅ PR is mergeable and ready for review

**Proof of concept**: The TAC-8 style autonomous coordination system works!

### 2. Identified 3 Core Issues from Testing

1. **Worktree collision handling** - Coordinator repeatedly tried to create worktrees that already exist
2. **Zombie processes** - Completed workers became defunct processes
3. **Status tracking** - tasks.md didn't update when workers completed

### 3. Created Comprehensive Documentation (2,802 lines)

**Committed to GitHub** (commits `66ad9c3` and `5096ab4`):

1. **IMPLEMENTATION_PLAN.md** (1,201 lines)
   - 6-phase implementation plan
   - Complete code for all fixes (copy-paste ready)
   - 8-12 hours estimated total work
   - Minimum viable: 6 hours for Phases 1, 2.1, and 6

2. **CONTROL_AND_MONITORING.md** (528 lines)
   - How to view worker conversations (`tools/view_worker.py`)
   - How to stop/intervene in running workers
   - Solutions for all 3 core issues
   - Metrics and monitoring system design

3. **GIT_WORKFLOW.md**
   - How to commit coordinator changes
   - Disaster recovery procedures
   - How to reproduce on new Pi

4. **SETUP.md** (628 lines)
   - Complete step-by-step setup from scratch
   - Works on any computer (Ubuntu, macOS, Windows WSL2, Pi)
   - 30-60 minute setup time
   - Troubleshooting guide

5. **tools/view_worker.py** (122 lines)
   - Working tool to view worker conversation logs
   - Example: `python3 tools/view_worker.py 471`

### 4. Cleaned Up Repository Structure

**Before**:
- `circuit-synth-tac` (13GB) - Old research repo
- `circuit-synth-coordinator` (184KB) - Old coordinator draft
- `circuit-synth-dev-tools` (144KB) - Old PRD
- `circuit-synth` (1GB) - Main repo

**After** (pending your sudo command):
- `circuit-synth` (1.1GB) - **Everything we need**

**To complete cleanup**:
```bash
cd /home/shane/Desktop
sudo rm -rf circuit-synth-tac circuit-synth-coordinator circuit-synth-dev-tools
```

---

## 📊 Current State

### Git Status
```
Repository: circuit-synth
Branch: main
Status: Clean (all changes committed and pushed)
Latest commits:
  - 5096ab4: SETUP.md
  - 66ad9c3: Planning docs + view_worker.py
  - 0b06456: TAC-8 coordinator system
```

### What's Working
- ✅ GitHub issue fetching via `gh` CLI
- ✅ Worker spawning with `claude -p`
- ✅ Git worktree creation
- ✅ Autonomous code changes
- ✅ PR creation
- ✅ Basic task queue management (tasks.md)
- ✅ Worker conversation logging (logs/*.jsonl)
- ✅ Worker viewer tool (tools/view_worker.py)

### What Needs Fixing (Phase 1)
- ❌ Worktree collision handling
- ❌ Zombie process reaping
- ❌ Status tracking with PR detection

### What Needs Adding (Phases 2-6)
- ⚠️ Monitoring and metrics
- ⚠️ Control mechanisms (stop/pause)
- ⚠️ Automated testing
- ⚠️ Production deployment

---

## 📋 Implementation Roadmap

### Phase 1: Fix Core Issues (CRITICAL - 3-4 hours)

**Priority**: P0 - Must fix before production

1. **Worktree collision handling** (~1 hour)
   - Add `ensure_worktree()` method (idempotent)
   - Check if worktree exists before creating
   - Clean up stale worktrees automatically
   - Code in IMPLEMENTATION_PLAN.md lines 80-150

2. **Zombie process reaping** (~30 min)
   - Add SIGCHLD signal handler
   - Automatically reap completed workers
   - Code in IMPLEMENTATION_PLAN.md lines 152-220

3. **Status tracking** (~2 hours)
   - Add `check_completions()` method
   - Detect PR creation via `gh pr list`
   - Update tasks.md automatically
   - Post comments to GitHub issues
   - Code in IMPLEMENTATION_PLAN.md lines 222-360

**Files to modify**:
- `adws/coordinator.py` - Add ~150 lines

**Testing**:
- Create test issue, verify completion tracking
- Check no zombie processes
- Verify worktree cleanup

### Phase 2: Monitoring (HIGH - 2-3 hours)

1. **Metrics tracking** (~2 hours)
   - Create `adws/metrics.py`
   - Track success rate, errors, health
   - Auto-recovery when health degrades
   - Code in IMPLEMENTATION_PLAN.md lines 362-520

2. **Status dashboard** (~1 hour)
   - Create `tools/status.py`
   - Real-time coordinator health view
   - Code in IMPLEMENTATION_PLAN.md lines 522-620

### Phase 3: Control Mechanisms (MEDIUM - 2 hours)

1. **Graceful stop** (~1 hour)
   - Add STOP file check to worker template
   - Create `tools/stop_worker.sh`
   - Code in IMPLEMENTATION_PLAN.md lines 622-680

2. **Pause/resume** (~1 hour)
   - Add USR1 signal handler
   - Pause new worker launches
   - Code in IMPLEMENTATION_PLAN.md lines 682-720

### Phase 4: Testing (HIGH - 2-3 hours)

- Integration tests
- End-to-end test
- Smoke tests

### Phase 5: Documentation (LOW - 1-2 hours)

- Update README.md
- Create RUNBOOK.md

### Phase 6: Raspberry Pi Deployment (FINAL - 1-2 hours)

- Create deployment script
- Create systemd service
- Deploy and monitor

---

## 🚀 Next Steps (In Order)

### Immediate (Manual Cleanup)

```bash
# 1. Delete obsolete repos
cd /home/shane/Desktop
sudo rm -rf circuit-synth-tac circuit-synth-coordinator circuit-synth-dev-tools

# 2. Verify only circuit-synth remains
ls -la | grep circuit
# Should show only: circuit-synth

# 3. Stop background coordinators (if still running)
pkill -f "python3 adws/coordinator.py"
```

### Next Session: Implement Phase 1

**Option A: Create feature branch + PR**
```bash
cd /home/shane/Desktop/circuit-synth
git checkout -b feat/production-ready-coordinator

# Implement Phase 1.1 (worktree fix)
# Implement Phase 1.2 (zombie reaping)
# Implement Phase 1.3 (status tracking)

git add adws/coordinator.py
git commit -m "fix: Add production-ready improvements to coordinator

- Idempotent worktree creation
- Zombie process reaping
- PR detection and status tracking

See IMPLEMENTATION_PLAN.md Phase 1 for details."

git push origin feat/production-ready-coordinator
gh pr create --title "feat: Production-ready coordinator improvements"
```

**Option B: Direct to main** (if you prefer)
```bash
# Make changes directly on main
# Commit as you complete each phase
```

### After Phase 1: Test

```bash
# Create test issue
gh issue create --repo circuit-synth/circuit-synth \
  --title "Test: Verify coordinator improvements" \
  --body "Test completion tracking and status updates" \
  --label "rpi-auto,priority:P0"

# Start coordinator
python3 adws/coordinator.py

# Monitor
python3 tools/view_worker.py <issue_number>

# Verify:
# - No zombie processes (ps aux | grep defunct)
# - No worktree errors
# - tasks.md updates when PR created
```

---

## 📚 Reference Documentation

All documentation is in the `circuit-synth` repo:

1. **IMPLEMENTATION_PLAN.md** - Read this to implement Phase 1
   - Lines 1-100: Executive summary
   - Lines 101-360: Phase 1 code (copy-paste ready)
   - Lines 361-720: Phases 2-3 code
   - Lines 721-1201: Phases 4-6

2. **CONTROL_AND_MONITORING.md** - Control and monitoring guide
   - How to view worker conversations
   - How to stop workers
   - Metrics system design

3. **SETUP.md** - Reproduce system on new computer
   - Complete prerequisites
   - Step-by-step setup
   - Troubleshooting

4. **GIT_WORKFLOW.md** - Git tracking
   - Commit conventions
   - Disaster recovery

---

## 🔍 How to View Worker Conversations

```bash
# View conversation for issue #471
python3 tools/view_worker.py 471

# Detailed view with all parameters
python3 tools/view_worker.py 471 --detailed

# Check raw logs
tail -f logs/gh-471.jsonl | jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="text")? | .text'
```

---

## ⚠️ Known Issues

1. **Worktree cleanup needed**: Old worktrees from testing need manual cleanup
   ```bash
   cd /home/shane/Desktop/circuit-synth
   for tree in trees/gh-*; do git worktree remove "$tree" --force 2>/dev/null; done
   ```

2. **Background coordinators**: May still be running from testing
   ```bash
   ps aux | grep "python3 adws/coordinator.py"
   kill <PID>  # If found
   ```

3. **Test issue #471**: PR #473 ready to review/merge
   - https://github.com/circuit-synth/circuit-synth/pull/473

---

## 🎯 Success Criteria

You'll know the system is production-ready when:

1. ✅ No zombie processes accumulate
2. ✅ No repeated worktree errors
3. ✅ tasks.md accurately reflects status
4. ✅ Metrics track health
5. ✅ Can stop workers gracefully
6. ✅ Smoke tests pass
7. ✅ Runs 24/7 on Raspberry Pi without crashes
8. ✅ Success rate > 80%
9. ✅ Auto-recovery from errors
10. ✅ GitHub issues get status comments

---

## 💡 Key Insights from This Session

1. **TAC-8 simplicity works** - One 456-line script, markdown state, zero deps
2. **End-to-end test validates design** - PR #473 proved the concept
3. **Three fixes unlock production** - Worktree, zombies, status tracking
4. **Documentation enables reproducibility** - Can set up on any computer now
5. **Git tracking is essential** - Everything committed and versioned

---

## 🤔 Questions to Consider Next Session

1. **Branch strategy**: Feature branch vs direct to main for Phase 1?
2. **Testing approach**: Manual testing or write automated tests first?
3. **Deployment timing**: Deploy after Phase 1, or wait for Phase 2?
4. **Metrics urgency**: Is Phase 2 (metrics) needed before Pi deployment?

---

## 📞 Quick Commands Reference

```bash
# Start coordinator
cd /home/shane/Desktop/circuit-synth
python3 adws/coordinator.py

# View worker conversation
python3 tools/view_worker.py <issue_number>

# Check git status
git status
git log --oneline -5

# Clean up worktrees
for tree in trees/gh-*; do git worktree remove "$tree" --force 2>/dev/null; done

# Create test issue
gh issue create --repo circuit-synth/circuit-synth --title "Test: <description>" --label "rpi-auto,priority:P0"

# Stop coordinator
pkill -f "python3 adws/coordinator.py"
```

---

## 🔗 Important Links

- **Main repo**: https://github.com/circuit-synth/circuit-synth
- **Test PR #473**: https://github.com/circuit-synth/circuit-synth/pull/473
- **Test issue #471**: https://github.com/circuit-synth/circuit-synth/issues/471

---

**Ready to continue? Pick up where we left off:**
1. Clean up old repos (sudo rm -rf ...)
2. Read IMPLEMENTATION_PLAN.md Phase 1
3. Implement the three fixes
4. Test with a new issue
5. Deploy to Pi!

**Estimated time to production**: 6-12 hours of focused implementation work.
