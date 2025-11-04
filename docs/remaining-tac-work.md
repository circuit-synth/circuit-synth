# Remaining TAC-X Work: Path to Fully Functional System

**Status:** Worker executes Claude successfully, but pipeline reports failure
**Date:** 2025-11-04
**Goal:** Achieve fully functional autonomous worker system with real-time dashboard

---

## Current State Analysis

### ✅ What's Working

1. **CLI Provider System**
   - `cli_providers.py` module functional
   - Command template system working
   - Claude CLI successfully invoked via subprocess
   - JSONL output logging captured

2. **Worker Execution**
   - `TACWorkerAdapter` wraps `MultiStageWorker`
   - Claude makes real LLM calls
   - Tools execute (Bash, Read, Grep, Glob, Write)
   - Output files created (plan.md: 12KB)
   - Token usage tracked (~50k input, ~2.8k output)

3. **Database Integration**
   - PostgreSQL connection working
   - Schema up to date (via migrations)
   - Task creation functional
   - Stage logging functional

4. **Repository Organization**
   - All "atopile" references replaced with "circuit-synth"
   - Correct GitHub URLs throughout codebase

### ❌ What's Broken

1. **Pipeline Success Detection**
   - Issue: Worker reports "Pipeline failed at stage 'planning'"
   - Reality: Claude successfully created plan.md
   - Root cause: Stage result not properly recorded in pipeline_state
   - Location: `multi_stage_worker.py:run_planner_stage()`

2. **Dashboard API**
   - Dashboard process not running (killed during restart)
   - API endpoint returning errors
   - workflow_config JSON parsing added but not tested
   - Location: `dashboard/tac_api.py`

3. **Stage Result Recording**
   - `MultiStageWorker.invoke_agent()` returns dict with returncode, tokens
   - `run_planner_stage()` expects result dict but doesn't store in pipeline_state.stage_results
   - TACWorkerAdapter looks for stage_results["planning"] but it's never added
   - Location: `multi_stage_worker.py` lines 230-287

4. **Coordinator Integration**
   - Coordinator spawning workers but they fail immediately
   - Workers exit with code 1
   - Worktree has uncommitted changes
   - Location: Coordinator seeing repeated failures for gh-504

---

## Root Cause Analysis

### Issue 1: Stage Results Not Stored

**Problem:** `run_planner_stage()` calls `invoke_agent()` and gets a result dict, but never stores it in `self.state.stage_results["planning"]`

**Evidence:**
```python
# multi_stage_worker.py line 263
result = self.invoke_agent(
    stage="planning",
    ...
)

# Line 268: Check if plan.md exists
plan_file = self.worktree_path / "plan.md"
if not plan_file.exists():
    return StageResult(success=False, ...)

# Line 279: Return success
return StageResult(
    stage_name="planning",
    success=True,
    ...
)

# PROBLEM: StageResult is returned but never stored!
# Should be: self.state.stage_results["planning"] = result
```

**Expected Flow:**
1. `run_planner_stage()` creates StageResult
2. **MISSING:** Store in `self.state.stage_results["planning"]`
3. `TACWorkerAdapter` reads from `pipeline_state.stage_results["planning"]`

**Why It Breaks:**
- TACWorkerAdapter line 316: `if stage_name in pipeline_state.stage_results:`
- This is always False because stage_results dict is never populated
- Falls through to error: "Stage result not found in pipeline state"

### Issue 2: Dashboard Not Running

**Problem:** Dashboard API killed during testing, never restarted properly

**Evidence:**
```bash
# Earlier: pkill -f "python3 tac_api.py"
# Started: nohup python3 tac_api.py > ../logs/dashboard_restart.log 2>&1 &
# Result: Process died immediately (no output in logs)
```

**Likely Causes:**
1. Import error (dashboard/tac_api.py imports might fail)
2. Port 8001 already in use
3. Database connection issue
4. Missing dependencies

**Need to Check:**
- Dashboard startup logs
- Import errors
- Port availability
- Database connectivity

---

## Implementation Plan

### Phase 1: Fix Stage Result Storage (CRITICAL)

**Goal:** Make pipeline record stage results properly

**Files to modify:**
1. `adws/adw_modules/multi_stage_worker.py`

**Changes needed:**

#### Change 1: Store StageResult in pipeline state

**Location:** `run_planner_stage()` method (lines 230-287)

**Current code (line 279):**
```python
return StageResult(
    stage_name="planning",
    success=True,
    ...
)
```

**Fix:**
```python
result = StageResult(
    stage_name="planning",
    success=True,
    started_at=started_at,
    completed_at=completed_at,
    output_file="plan.md",
    tokens_input=result['tokens_input'],
    tokens_output=result['tokens_output']
)

# Store in pipeline state
self.state.stage_results["planning"] = result

return result
```

#### Change 2: Same fix for other stages

Apply same pattern to:
- `run_builder_stage()` (lines 289-334)
- `run_reviewer_stage()` (lines 336-397)
- `run_pr_creator_stage()` (lines 399-455)

**Pattern:**
```python
# At end of each stage method:
result = StageResult(...)
self.state.stage_results[stage_name] = result  # ADD THIS LINE
return result
```

**Verification:**
```python
# After fix, test with:
python3 test_worker.py

# Should see:
# ✓ Plan created: plan.md
# ✓ Pipeline completed successfully
```

### Phase 2: Fix Dashboard

**Goal:** Get dashboard API running and serving data

#### Step 1: Diagnose startup issue

```bash
# Try starting manually to see errors
cd dashboard
python3 tac_api.py
```

**Likely issues:**
- Import error in `tac_api.py`
- Port 8001 in use
- Missing `asyncpg` or other dependencies

#### Step 2: Fix identified issues

**If port in use:**
```bash
# Find process using port 8001
sudo lsof -i :8001
# Kill it or change dashboard port
```

**If import error:**
```bash
# Check imports work
python3 -c "from dashboard import tac_api"
```

**If missing dependencies:**
```bash
pip install asyncpg fastapi uvicorn
```

#### Step 3: Restart dashboard

```bash
cd dashboard
nohup python3 tac_api.py > ../logs/dashboard_api.log 2>&1 &
echo "Dashboard PID: $!"

# Verify it's running
curl http://localhost:8001/api/tasks
```

#### Step 4: Test dashboard UI

```bash
# Open in browser
xdg-open http://localhost:8001
```

**Expected:**
- Tasks list showing recent worker runs
- Real-time status updates
- No "Error loading tasks" message

### Phase 3: Test Full Pipeline

**Goal:** Run complete test proving system works end-to-end

#### Test 1: Direct worker test

```bash
# Clean test run
rm -rf trees/gh-504/.tac/stages/*
rm -f trees/gh-504/plan.md

# Run worker
python3 test_worker.py

# Expected output:
# ✓ Created TAC worker (task_id=...)
# 🚀 Starting TAC-X Multi-Stage Pipeline
# 📋 Stage 1: Planning
#    Running: claude-cli/claude-sonnet-4-5
#    ✓ Plan created: plan.md
# ✓ Pipeline completed successfully
```

#### Test 2: Coordinator integration

```bash
# Check coordinator is running
ps aux | grep coordinator

# Check coordinator picks up issue #504
tail -f logs/coordinator.log

# Expected:
# 📥 Found 1 new tasks from GitHub
# 🤖 Spawning TAC-X pipeline for gh-504
# ✓ TAC-X Pipeline w-XXXXXX started (PID: YYYYY)
```

#### Test 3: Dashboard reflects progress

```bash
# Query API
curl http://localhost:8001/api/tasks | jq .

# Should show:
# - task_id
# - status: "running" or "completed"
# - stages with token counts
# - workflow_config parsed correctly
```

### Phase 4: End-to-End Verification

**Goal:** Prove system works from issue creation to PR

#### Full workflow test:

1. **Issue exists**: gh-504 with label "rpi-auto"
2. **Coordinator detects**: Polls GitHub, finds issue
3. **Worktree created**: `trees/gh-504/`
4. **Worker spawned**: TACWorkerAdapter created
5. **Planning stage**: Claude analyzes issue, creates plan.md
6. **Building stage**: Claude implements solution
7. **Reviewing stage**: Claude reviews code
8. **PR creation**: Claude creates pull request
9. **Dashboard updates**: Real-time progress visible
10. **Database records**: All stages logged with tokens

**Success criteria:**
- All 4 stages complete without errors
- Dashboard shows complete pipeline
- Database has full stage history
- GitHub PR created automatically

---

## Testing Strategy

### Unit Tests

**Test 1: Stage result storage**
```python
def test_stage_result_stored_in_pipeline_state():
    """Verify run_planner_stage stores result in pipeline state"""
    worker = MultiStageWorker(...)
    worker.run_planner_stage()

    assert "planning" in worker.state.stage_results
    assert worker.state.stage_results["planning"].success == True
```

**Test 2: Dashboard workflow_config parsing**
```python
def test_workflow_config_json_parsing():
    """Verify API parses workflow_config JSON string"""
    # Mock database row with JSON string
    row = {
        'workflow_config': '{"stages": [...]}'
    }

    # Parse it
    parsed = json.loads(row['workflow_config'])

    # Verify it's a dict
    assert isinstance(parsed, dict)
    assert 'stages' in parsed
```

### Integration Tests

**Test 1: Full pipeline execution**
```bash
# Run test worker with fresh worktree
pytest tests/integration/test_full_pipeline.py -v
```

**Test 2: Dashboard API endpoints**
```bash
# Test all endpoints
pytest dashboard/tests/test_api_endpoints.py -v
```

### Manual Testing

**Test 1: Coordinator watching GitHub**
```bash
# Monitor coordinator logs
tail -f logs/coordinator.log

# Create new issue with rpi-auto label
gh issue create --label rpi-auto --title "Test issue"

# Verify coordinator picks it up
```

**Test 2: Dashboard live updates**
```bash
# Open dashboard
xdg-open http://localhost:8001

# Start worker in another terminal
python3 test_worker.py

# Verify dashboard shows progress in real-time
```

---

## Rollout Plan

### Step 1: Fix stage result storage (30 min)

- Modify `multi_stage_worker.py`
- Add `self.state.stage_results[stage_name] = result` to all 4 stage methods
- Test with `python3 test_worker.py`
- Verify: "Pipeline completed successfully"
- Commit: "fix: Store stage results in pipeline state"

### Step 2: Restart and test dashboard (15 min)

- Diagnose why dashboard died
- Fix startup issues
- Restart dashboard
- Test API endpoints
- Verify: `curl http://localhost:8001/api/tasks` returns valid JSON
- Commit: "fix: Dashboard API startup and JSON parsing"

### Step 3: Clean test run (10 min)

- Kill all old test_worker processes
- Clear old logs and worktree artifacts
- Run fresh `python3 test_worker.py`
- Verify all 4 stages complete
- Check database has correct records
- Commit: "test: Verify full pipeline execution"

### Step 4: Coordinator integration (20 min)

- Verify coordinator is running
- Check it picks up gh-504
- Monitor worker spawn and execution
- Verify dashboard shows progress
- Document any issues
- Commit: "docs: Coordinator integration test results"

### Step 5: Documentation update (15 min)

- Update README with current state
- Document known issues
- Add troubleshooting guide
- Update temperature settings in workflow.yaml
- Commit: "docs: Update system status and troubleshooting"

**Total estimated time:** ~90 minutes

---

## Success Metrics

### Metric 1: Pipeline Success Rate
- **Target:** 100% for test worker
- **Current:** 0% (reports failure despite success)
- **Measure:** `python3 test_worker.py` exit code

### Metric 2: Dashboard Availability
- **Target:** 99% uptime
- **Current:** 0% (not running)
- **Measure:** `curl http://localhost:8001/health`

### Metric 3: Stage Completion Rate
- **Target:** All 4 stages complete
- **Current:** Stage 1 completes but reports failure
- **Measure:** Database query for completed stages

### Metric 4: Token Usage Tracking
- **Target:** All stages report token counts
- **Current:** Unknown (stage results not recorded)
- **Measure:** Dashboard token usage graphs

### Metric 5: Coordinator Reliability
- **Target:** Picks up issues within 30 seconds
- **Current:** Spawns workers but they fail
- **Measure:** Time from issue creation to worker spawn

---

## Risk Assessment

### High Risk

**Risk:** Stage result storage fix breaks other parts of pipeline
- **Mitigation:** Test each stage individually
- **Fallback:** Revert commit if tests fail

**Risk:** Dashboard has deeper issues than startup
- **Mitigation:** Start with minimal test (import check)
- **Fallback:** Use database queries directly to verify data

### Medium Risk

**Risk:** Coordinator spawns multiple workers for same issue
- **Mitigation:** Check coordinator logic for duplicate prevention
- **Fallback:** Add task locking mechanism

**Risk:** Workers leave worktree in dirty state
- **Mitigation:** Add cleanup step in TACWorkerAdapter
- **Fallback:** Manual cleanup script

### Low Risk

**Risk:** Temperature settings need tuning
- **Mitigation:** Already documented in llm-temperature-research.md
- **Fallback:** Revert to 1.0 if 0.2-0.4 causes issues

---

## Dependencies

### Code Dependencies
- ✅ `cli_providers.py` (working)
- ✅ `workflow_config.py` (working)
- ❌ `multi_stage_worker.py` (needs stage result storage fix)
- ❌ `tac_worker_adapter.py` (works but receives wrong data)
- ❌ `dashboard/tac_api.py` (not running)

### External Dependencies
- ✅ PostgreSQL (running, port 5433)
- ✅ Claude CLI (working, successfully making calls)
- ❌ Dashboard UI (not accessible)
- ✅ GitHub API (coordinator polling working)

### Infrastructure Dependencies
- ✅ Git worktrees (working)
- ✅ JSONL logging (working)
- ✅ Database migrations (working)
- ✅ Coordinator process (running but workers fail)

---

## Next Actions (Prioritized)

1. **IMMEDIATE:** Fix stage result storage in `multi_stage_worker.py`
   - Impact: HIGH - Unlocks full pipeline
   - Effort: LOW - 4 one-line additions
   - Risk: LOW - Simple data storage

2. **IMMEDIATE:** Diagnose and fix dashboard startup
   - Impact: HIGH - Required for observability
   - Effort: MEDIUM - Depends on root cause
   - Risk: MEDIUM - May require debugging

3. **HIGH:** Test full pipeline with fixed worker
   - Impact: HIGH - Proves system works
   - Effort: LOW - Run existing tests
   - Risk: LOW - Just verification

4. **HIGH:** Verify coordinator picks up work
   - Impact: HIGH - End-to-end validation
   - Effort: MEDIUM - May need debugging
   - Risk: MEDIUM - Complex interaction

5. **MEDIUM:** Update temperature settings per research
   - Impact: MEDIUM - Better quality output
   - Effort: LOW - Edit workflow.yaml
   - Risk: LOW - Easily reversible

6. **MEDIUM:** Add monitoring/alerting
   - Impact: MEDIUM - Catch future issues
   - Effort: HIGH - Build new infrastructure
   - Risk: LOW - Additive change

7. **LOW:** Performance optimization
   - Impact: LOW - System works, just slower
   - Effort: HIGH - Profiling and tuning
   - Risk: MEDIUM - May introduce bugs

---

## Open Questions

1. **Why did dashboard process die?**
   - Need to check logs
   - May be import error or port conflict

2. **Does coordinator have rate limiting?**
   - Important to avoid spawning too many workers
   - Need to check coordinator.py logic

3. **How are failed workers cleaned up?**
   - Coordinator logs show "Reaped worker" messages
   - Need to verify cleanup is complete

4. **Should we implement worker health checks?**
   - Could help catch failures faster
   - Need to design health check protocol

5. **What's the token cost per run?**
   - Planning stage: ~50k input, ~2.8k output
   - Need to multiply by 4 stages for full run
   - Need budget/cost tracking

---

## Appendix: Key File Locations

### Core Worker Files
- `adws/adw_modules/multi_stage_worker.py` - Main pipeline orchestrator
- `adws/adw_modules/tac_worker_adapter.py` - Database integration wrapper
- `adws/adw_modules/cli_providers.py` - CLI provider system
- `adws/adw_modules/workflow_config.py` - YAML workflow configuration

### Configuration
- `adws/config.toml` - Main configuration file
- `trees/gh-504/.tac/workflow.yaml` - Per-worktree workflow config

### Database
- `adws/database/migrations/001_initial_schema.sql` - Schema definition
- `adws/database/reset_database.py` - Reset utility

### Dashboard
- `dashboard/tac_api.py` - FastAPI backend
- `dashboard/app.js` - Frontend JavaScript

### Testing
- `test_worker.py` - Direct worker test script
- `logs/test_full_execution.log` - Latest test results

### Logs
- `logs/coordinator.log` - Coordinator activity
- `logs/dashboard.log` - Dashboard activity (if running)
- `trees/gh-504/.tac/stages/planning.jsonl` - Claude execution trace

---

**Last Updated:** 2025-11-04T01:00:00Z
**Author:** TAC-X System Analysis
**Status:** Ready for implementation
