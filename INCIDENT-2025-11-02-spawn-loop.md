# Incident Report: TAC Coordinator Spawn Loop (2025-11-02)

## Summary
The TAC-8 coordinator entered a worker spawn loop, creating 12+ simultaneous Claude worker processes, exhausting system resources (4.7GB/7.7GB RAM), and causing SSH connectivity issues on the Raspberry Pi.

## Timeline
- **21:23** - Coordinator started via systemd service
- **21:23-21:44** - Spawn loop active (12+ workers spawned repeatedly)
- **21:38** - User reports SSH connectivity problems
- **21:44** - Issue identified and mitigated (all workers killed, coordinator stopped)

## Root Cause Analysis

### Primary Bug: Missing FailureType Enum
**Location:** `adws/coordinator.py:808` references `FailureType.STARTUP_ERROR` which didn't exist in `adws/adw_modules/error_handling.py:17-26`

**Impact:**
1. Workers exit in <10s (instant failure)
2. Coordinator attempts to categorize as STARTUP_ERROR
3. AttributeError exception thrown (uncaught)
4. Task state not properly updated
5. Task remains in 'pending' status
6. Coordinator immediately respawns worker
7. Loop repeats exponentially

### Secondary Issue: Insufficient Backoff for Startup Errors
Even if STARTUP_ERROR existed, the default backoff (60s * 2^attempt) was too short to prevent spawn loops on resource-constrained hardware.

### Tertiary Issue: Config Mismatch
- Config file shows: `max_concurrent_workers = 1`
- Deploy log shows: `Max concurrent: 3`
- Likely old cached config or systemd service using stale config

## Evidence

### Deploy Log Analysis (`coordinator-deploy-test.log`)
```
Line 28: Max concurrent: 3  (should be 1)
Lines 37-175: 12 workers spawned for same 3 tasks (gh-456, gh-450, gh-455, gh-452)
Pattern: spawn → exit → respawn in <30s intervals
```

### Process List at Peak
```
13 Claude workers running simultaneously
Each consuming 2.7-3.9GB RAM
Total: ~40GB virtual memory allocated on 7.7GB system
Memory exhaustion: 4.7GB/7.7GB used (61%)
Load average: 1.60 (should be <0.5 on idle)
```

### Affected Tasks
- `gh-456` - Spawned 4+ times
- `gh-450` - Spawned 4+ times
- `gh-455` - Spawned 4+ times
- `gh-452` - Spawned 3+ times

## Impact

### System Impact
- **Memory:** 61% utilization (2.7GB excessive)
- **CPU:** Load avg 1.60 (320% normal)
- **SSH:** Connection timeouts/slowness
- **Disk I/O:** Excessive git worktree creation/deletion

### User Impact
- SSH connectivity severely degraded
- Manual intervention required to restore service
- Work interruption during autonomous operation

### Worker Impact
- No successful PR completions during incident
- 12+ failed worker attempts consuming API quota
- Stale git worktrees requiring cleanup

## Fixes Applied

### Fix 1: Add Missing STARTUP_ERROR Enum
**File:** `adws/adw_modules/error_handling.py`
```python
class FailureType(Enum):
    ...
    STARTUP_ERROR = "startup_error"  # Agent failed to start or exited in <10s
    ...
```

### Fix 2: Extended Backoff for Startup Errors
**File:** `adws/adw_modules/error_handling.py`
```python
def calculate_backoff(self) -> int:
    # Use longer backoff for startup errors to prevent spawn loops
    if self.last_failure_type == FailureType.STARTUP_ERROR:
        return 300 * (2 ** self.attempt_count)  # 5min, 10min, 20min

    return 60 * (2 ** self.attempt_count)  # Normal backoff
```

**Rationale:**
- Startup errors indicate config/environment issues
- Immediate retry won't help (same environment)
- Longer backoff prevents resource exhaustion
- Gives time for manual intervention

## Preventive Measures

### Immediate Actions Needed
1. ✅ Kill runaway workers
2. ✅ Stop coordinator systemd service
3. ✅ Add STARTUP_ERROR enum
4. ✅ Implement extended backoff
5. ⏳ Verify config.toml is correct (max_concurrent_workers = 1)
6. ⏳ Clean up stale git worktrees in `trees/` directory
7. ⏳ Verify systemd service uses correct config path

### Future Improvements
1. **Circuit Breaker:** Pause spawning if N failures in M seconds
2. **Resource Limits:** Use systemd resource controls (MemoryMax, CPUQuota)
3. **Health Checks:** Monitor memory/CPU before spawning
4. **Better Exception Handling:** Catch and log AttributeError on FailureType
5. **Spawn Rate Limiting:** Max 1 worker spawn per 10 seconds
6. **Alert System:** Send notification when spawn loop detected
7. **Config Validation:** Verify config on startup, fail fast if invalid

## Lessons Learned

1. **Test on target hardware:** Spawn loops are more severe on RPi than development machine
2. **Enum exhaustiveness:** Missing enum values cause silent failures
3. **Exponential backoff essential:** Prevents resource exhaustion cascades
4. **Monitor systemd services:** Config changes may not propagate without restart
5. **SSH degradation is early warning:** Resource exhaustion affects all services

## Verification Steps

After fix deployment:
- [ ] Verify config.toml has `max_concurrent_workers = 1`
- [ ] Restart systemd service: `sudo systemctl restart circuit-synth-coordinator`
- [ ] Monitor logs for 10 minutes: `journalctl -u circuit-synth-coordinator -f`
- [ ] Check no spawn loops occur
- [ ] Verify backoff times appear in logs for failures
- [ ] Clean up stale worktrees: `git worktree prune && rm -rf trees/gh-*`
- [ ] Monitor SSH responsiveness during operation

## References
- Config: `adws/config.toml`
- Coordinator: `adws/coordinator.py`
- Error handling: `adws/adw_modules/error_handling.py`
- Deploy log: `coordinator-deploy-test.log`
- Commit: (to be added after commit)
