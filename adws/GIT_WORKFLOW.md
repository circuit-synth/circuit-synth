# Git Workflow for TAC-8 Coordinator Development

**CRITICAL**: All changes must be tracked in git for reproducibility and rollback.

---

## Repository Structure

This TAC-8 coordinator system lives in the **circuit-synth** repository:
- Repo: `https://github.com/circuit-synth/circuit-synth`
- Branch strategy: Main branch + feature branches for major changes
- Autonomous workers create PRs to main

---

## Committing Coordinator Changes

### After Each Phase of Implementation

**Phase 1: Core Fixes**
```bash
cd /home/shane/Desktop/circuit-synth

# Add modified coordinator
git add adws/coordinator.py

# Commit with clear message
git commit -m "fix: Add worktree cleanup and zombie reaping to coordinator

- Make worktree creation idempotent (handles existing worktrees)
- Add SIGCHLD handler to reap zombie processes
- Add PR detection for completion tracking
- Post comments to GitHub issues on completion

Fixes core reliability issues identified in testing.
Part of Phase 1 implementation plan."

# Push to GitHub
git push origin main
```

**Phase 2: Monitoring**
```bash
git add adws/metrics.py tools/status.py
git commit -m "feat: Add metrics tracking and status dashboard

- metrics.py tracks worker success/failure rates
- Auto-recovery when health degrades
- Real-time status dashboard (tools/status.py)

Part of Phase 2 implementation plan."
git push origin main
```

**Documentation Changes** (separate commits)
```bash
git add adws/IMPLEMENTATION_PLAN.md adws/CONTROL_AND_MONITORING.md
git commit -m "docs: Add implementation plan and control guide

- Comprehensive 1200-line implementation plan
- Control and monitoring documentation
- Troubleshooting runbook"
git push origin main
```

**Tools** (separate commits)
```bash
git add tools/view_worker.py tools/status.py tools/stop_worker.sh
git commit -m "feat: Add worker monitoring and control tools

- view_worker.py: Read worker conversation logs
- status.py: Real-time coordinator dashboard
- stop_worker.sh: Graceful worker shutdown"
git push origin main
```

---

## Commit Message Convention

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation only
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance

**Scopes** (optional):
- `coordinator` - Main coordinator logic
- `metrics` - Metrics and monitoring
- `worker` - Worker template or logic
- `tools` - Utility scripts

**Examples**:
```bash
feat(coordinator): Add worktree cleanup logic
fix(coordinator): Prevent zombie process accumulation
docs: Update implementation plan with git workflow
feat(tools): Add worker conversation viewer
test(coordinator): Add integration tests
```

---

## Creating Feature Branches (For Major Changes)

For implementing the full plan, use a feature branch:

```bash
# Create feature branch
git checkout -b feat/coordinator-improvements

# Make all Phase 1 changes
git add adws/coordinator.py
git commit -m "fix(coordinator): Add worktree cleanup"

git add adws/coordinator.py
git commit -m "fix(coordinator): Add zombie reaping"

git add adws/coordinator.py
git commit -m "fix(coordinator): Add completion tracking"

# Make Phase 2 changes
git add adws/metrics.py tools/status.py
git commit -m "feat(metrics): Add health tracking"

# When done with all phases
git push origin feat/coordinator-improvements

# Create PR
gh pr create --title "feat: Production-ready coordinator improvements" \
  --body "Implements Phases 1-3 of implementation plan:

  - ✅ Worktree cleanup and collision handling
  - ✅ Zombie process reaping
  - ✅ PR detection and status tracking
  - ✅ Metrics and health monitoring
  - ✅ Control mechanisms (stop/pause)

  See adws/IMPLEMENTATION_PLAN.md for details."
```

---

## Tagging Releases

After major milestones, tag the commit:

```bash
# After Phase 1 complete (minimum viable)
git tag -a v0.1.0 -m "Phase 1: Core fixes complete

- Worktree cleanup
- Zombie reaping
- Status tracking

Minimum viable for production."
git push origin v0.1.0

# After all phases complete
git tag -a v1.0.0 -m "TAC-8 Coordinator v1.0

Full production-ready autonomous coordination system.
All 6 phases complete."
git push origin v1.0.0
```

---

## Disaster Recovery

If something breaks, you can roll back:

```bash
# See what changed
git log --oneline -10

# Roll back coordinator to previous version
git checkout <commit-hash> -- adws/coordinator.py

# Or reset entire repo to known-good state
git reset --hard v0.1.0
```

---

## State Files (NOT in Git)

These should be in `.gitignore`:

```gitignore
# Autonomous coordinator runtime state
trees/           # Git worktrees
logs/            # Worker logs
adws/metrics.json  # Runtime metrics
tasks.md.tmp     # Temp files
coordinator.pid  # Process ID
coordinator.log  # Log output
```

**Why**: These are runtime artifacts, recreated on each run. Git should track:
- ✅ Source code (coordinator.py)
- ✅ Configuration (config.toml)
- ✅ Templates (worker_template.md)
- ✅ Documentation (*.md guides)
- ✅ Tools (tools/*.py)
- ❌ Runtime state (trees/, logs/, metrics.json)

---

## Reproducing the System on New Pi

With proper git tracking, you can reproduce on a new Raspberry Pi:

```bash
# On new Pi
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Checkout specific version
git checkout v1.0.0  # Or main for latest

# Install dependencies
pip3 install -r requirements.txt

# Configure
cp adws/config.toml.example adws/config.toml
# Edit config.toml for your environment

# Start coordinator
python3 adws/coordinator.py
```

All tools, documentation, and code will be there because they're in git!

---

## Recovering from Failed Worker

If a worker corrupts something, it's isolated:

```bash
# Worker changes are in trees/gh-XXX worktree
# Main repo is untouched

# If worker made bad changes:
git worktree remove trees/gh-456 --force  # Deletes the worktree
# Main repo still clean!

# Worker's branch is on GitHub (auto/w-XXXXX)
# Can inspect it: gh pr view <number>
# Or delete it: git push origin --delete auto/w-XXXXX
```

---

## Current Status (Need to Commit)

**Untracked files**:
- `adws/CONTROL_AND_MONITORING.md` - Control guide (528 lines)
- `adws/IMPLEMENTATION_PLAN.md` - Implementation plan (1201 lines)
- `tools/view_worker.py` - Worker viewer (122 lines)

**Action needed**:
```bash
cd /home/shane/Desktop/circuit-synth

git add adws/CONTROL_AND_MONITORING.md adws/IMPLEMENTATION_PLAN.md tools/view_worker.py adws/GIT_WORKFLOW.md

git commit -m "docs: Add comprehensive planning and control documentation

- IMPLEMENTATION_PLAN.md: 6-phase plan for production readiness (1201 lines)
- CONTROL_AND_MONITORING.md: How to control and monitor workers (528 lines)
- GIT_WORKFLOW.md: Git tracking and reproducibility guide
- view_worker.py: Tool to view worker conversation logs

Created during Phase 0 (planning and tooling).
Implements lessons learned from PR #473 test."

git push origin main
```

---

## Testing Reproducibility

To verify the system can be reproduced:

```bash
# On second Pi or clean environment
git clone https://github.com/circuit-synth/circuit-synth.git test-reproduce
cd test-reproduce

# Should have everything
ls adws/coordinator.py          # ✓
ls adws/IMPLEMENTATION_PLAN.md  # ✓
ls tools/view_worker.py         # ✓
python3 adws/coordinator.py --help  # ✓ Works

# Proves reproducibility!
```

---

**Summary**: Git tracking is CRITICAL for:
1. **Reproducibility** - Recreate system on new hardware
2. **Rollback** - Recover from mistakes
3. **Audit trail** - Know what changed when
4. **Collaboration** - Others can contribute
5. **Disaster recovery** - Lose Pi? Clone repo on new one

Let's commit those 3 files NOW before proceeding with implementation!
