# Incident Report: Spawn Loop Fix (2025-11-03)

## Summary

Fixed critical spawn loop bug in TAC-8 coordinator where completed workers with uncommitted changes were incorrectly treated as "stale" and destroyed, causing infinite respawning and loss of work.

## Timeline

- **2025-11-02**: Spawn loop discovered during multi-provider routing testing
- **2025-11-03 23:00**: Investigation began
- **2025-11-03 23:49**: Fix tested and verified

## Symptoms

1. Coordinator repeatedly spawned same task (gh-450) in tight loop
2. Multiple identical worktrees created and destroyed
3. Worker work was being destroyed before completion
4. Logs showed pattern:
   ```
   🤖 Spawning worker for gh-450
   👶 Reaped worker (exit 0)
   ⚠️  Worktree already exists
      Worktree has uncommitted changes
      Worker not running - removing stale worktree  ← BUG
   🌲 Creating worktree
   🤖 Spawning worker for gh-450  ← Loop continues
   ```

## Root Cause Analysis

### Primary Issue

When a worker completed successfully but left uncommitted changes, the coordinator's `create_worktree()` logic would:
1. See worktree exists
2. Check git status - find uncommitted changes
3. See worker is not running
4. **Incorrectly conclude** this is a "stale" worktree from a crash
5. Remove the worktree, destroying the worker's completed work
6. Create fresh worktree
7. Spawn same task again
8. GOTO 1 (infinite loop)

### Code Location

File: `adws/coordinator.py`
Function: `create_worktree()`
Lines: ~620-665

### Why the Bug Existed

The original logic assumed:
- Uncommitted changes + no running worker = crashed worker = safe to delete

But this failed to account for:
- Worker completing successfully but not committing yet
- Worker being interrupted mid-work (coordinator restart)
- Worker exiting before committing

## Fix Implemented

### Strategy

Instead of using runtime (which doesn't survive coordinator restarts), use **file modification times** to detect fresh work vs stale worktrees.

### Implementation

```python
# Check file modification times
most_recent_mtime = 0
for root, dirs, files in os.walk(worktree_path):
    if '.git' in root:
        continue
    for file in files:
        mtime = os.path.getmtime(file_path)
        most_recent_mtime = max(most_recent_mtime, mtime)

# Calculate age
age_minutes = (now - most_recent_mtime) / 60

# Preserve recent work
if age_minutes < 60:  # Changed within last hour
    print("✅ Recent changes detected - preserving completed work")
    return worktree_path  # DON'T remove
else:
    print("🗑️  Stale worktree detected - removing")
    remove_worktree(worktree_path)
```

### Why This Works

1. **Survives restarts** - File mtimes persist across coordinator restarts
2. **Accurate detection** - Recent files = fresh work, old files = stale crash
3. **Simple heuristic** - 60 minute threshold balances false positives/negatives
4. **No state required** - Doesn't depend on task.started being set

### Commits

- **f7cc12f**: Initial fix using runtime (didn't survive restarts)
- **a1567a2**: Improved fix using file modification times

## Verification

### Test Scenario

1. Worker w-86c1b7 was running on gh-450
2. Coordinator was shut down mid-work
3. Worker completed, leaving uncommitted changes
4. Coordinator restarted

### Expected Behavior (After Fix)

```
⚠️  Worktree already exists: gh-450
   🔍 Worktree status check:
      - Has changes: True
      - Worker running: False
      - Most recent file change: 0.2 minutes ago
   ✅ Recent changes detected - preserving completed work
   🤖 Spawning worker for gh-450  ← Continues work in SAME worktree
```

### Result

✅ **PASS** - Worktree preserved, work not lost, no spawn loop

## Impact

### Before Fix
- Workers' completed work was destroyed
- Infinite spawn loops consumed resources
- Same task attempted repeatedly with no progress
- Lost work required manual recovery

### After Fix
- Completed work is preserved
- Workers can continue in same worktree
- No spawn loops
- Graceful handling of interruptions

## Lessons Learned

1. **State persistence matters** - Runtime state doesn't survive restarts
2. **File mtimes are reliable** - Good proxy for "work freshness"
3. **Comprehensive logging essential** - Made debugging possible
4. **Test restart scenarios** - Don't assume state survives

## Related Issues

- GitHub Issue #450: Dashboard token budget monitoring (task that triggered discovery)
- PR #490: Live pricing feature
- PR #492: Multi-provider routing

## Follow-up Actions

- [ ] Monitor coordinator logs for 24 hours to ensure no regression
- [ ] Consider adding automatic commit on worker completion
- [ ] Add metric tracking for worktree preservation rate
- [ ] Document worker best practices (commit early, commit often)

## References

- Coordinator logs: `/home/shane/Desktop/circuit-synth/coordinator.log`
- Worker logs: `/home/shane/Desktop/circuit-synth/logs/gh-450.jsonl`
- Worktrees dir: `/home/shane/Desktop/circuit-synth/trees/`

---

**Status**: ✅ RESOLVED
**Severity**: CRITICAL
**Fix verified**: 2025-11-03 23:49 UTC
