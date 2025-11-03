# TAC-8 Simplified Logging System - Design Document v2

**Version**: 2.0 (Simplified)
**Date**: 2025-11-03
**Status**: Design Phase

---

## 1. Core Philosophy

**Keep It Simple**: Don't duplicate what JSONL already does well.

**Strategy**:
- **JSONL files**: Full conversations, detailed logs (source of truth)
- **SQLite**: Metadata, aggregations, fast queries (index/cache)

**Why This Works**:
- JSONL is great for: sequential writes, full content, grep-able
- SQLite is great for: queries, aggregations, relationships, dashboards
- Don't fight the tools - use each for what it's best at

---

## 2. Simplified Schema (5 Tables Instead of 9)

### 2.1 Schema Overview

```
sessions         (coordinator runs)
   ├── tasks     (task lifecycle)
   ├── workers   (worker lifecycle)
   └── events    (everything else: triggers, decisions, errors, worktree ops)

api_calls        (costs, tokens - for budget tracking)
```

**That's it.** 5 tables total.

### 2.2 Table Details

#### Table 1: sessions

One row per coordinator run.

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    git_commit TEXT,
    exit_reason TEXT,            -- 'normal', 'error', 'signal'
    config JSON                  -- Key settings snapshot
);
```

**Purpose**: Track coordinator runs, group everything else

#### Table 2: tasks

Task lifecycle from detection to completion.

```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,    -- 'gh-450'
    session_id TEXT NOT NULL,
    issue_number INTEGER,
    title TEXT,
    detected_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    status TEXT NOT NULL,        -- 'detected', 'active', 'completed', 'failed'
    pr_number INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Purpose**: Task tracking, completion rates, what's active

#### Table 3: workers

Worker lifecycle.

```sql
CREATE TABLE workers (
    worker_id TEXT PRIMARY KEY,   -- 'w-abc123'
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    spawned_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    pid INTEGER,
    status TEXT NOT NULL,         -- 'spawned', 'completed', 'failed'
    exit_code INTEGER,
    log_file TEXT,                -- Path to JSONL conversation log
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
```

**Purpose**: Worker tracking, link to conversation logs

**Key**: `log_file` points to JSONL - don't duplicate conversation in DB!

#### Table 4: events

Everything else: triggers, decisions, errors, worktree operations.

```sql
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,    -- 'trigger', 'decision', 'error', 'worktree', etc.
    context_type TEXT,           -- 'task', 'worker', 'coordinator'
    context_id TEXT,             -- ID of related object
    severity TEXT,               -- 'debug', 'info', 'warning', 'error'
    message TEXT NOT NULL,
    details JSON,                -- Structured data
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_events_session ON events(session_id, timestamp);
CREATE INDEX idx_events_type ON events(event_type, timestamp);
CREATE INDEX idx_events_severity ON events(severity, timestamp);
```

**Purpose**: Universal event log - flexible, queryable

**Examples**:
```json
// Trigger event
{
  "event_type": "trigger",
  "context_type": "coordinator",
  "severity": "info",
  "message": "GitHub issue detected: gh-450",
  "details": {"issue_number": 450, "labels": ["rpi-auto"]}
}

// Decision event
{
  "event_type": "decision",
  "context_type": "worktree",
  "context_id": "gh-450",
  "severity": "info",
  "message": "Preserved worktree - recent changes detected",
  "details": {"file_age_minutes": 0.2, "action": "preserve"}
}

// Worktree operation
{
  "event_type": "worktree_op",
  "context_id": "gh-450",
  "message": "Created worktree for task",
  "details": {"path": "/trees/gh-450", "branch": "auto/w-abc123"}
}
```

#### Table 5: api_calls

API usage for cost tracking.

```sql
CREATE TABLE api_calls (
    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    model TEXT NOT NULL,
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_total INTEGER,
    estimated_cost_usd REAL,
    duration_ms REAL,
    success BOOLEAN,
    FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
);

CREATE INDEX idx_api_calls_timestamp ON api_calls(timestamp);
CREATE INDEX idx_api_calls_worker ON api_calls(worker_id);
```

**Purpose**: Cost tracking, budget monitoring

---

## 3. What About Conversations?

**Keep them in JSONL!** Don't duplicate.

**Why**:
- JSONL files are already structured (`logs/gh-450.jsonl`)
- Can grep, tail, cat them easily
- SQLite would just duplicate 10x the data
- External HDD can store JSONL files directly

**How to query conversations**:
1. Query SQLite to find worker: `SELECT log_file FROM workers WHERE worker_id = 'w-abc123'`
2. Read JSONL file: `cat logs/gh-450.jsonl | jq ...`

**Best of both worlds**: Fast metadata queries (SQLite) + Full content (JSONL)

---

## 4. Simplified Integration

### 4.1 Coordinator Lifecycle

```python
# Startup
session_id = logger.start_session(config, git_info)

# Shutdown
logger.end_session(session_id, exit_reason='normal')
```

### 4.2 Task Events

```python
# Detected
logger.log_task(session_id, 'gh-450', 'detected',
                issue_number=450, title="...")

# Started
logger.log_task(session_id, 'gh-450', 'active')

# Completed
logger.log_task(session_id, 'gh-450', 'completed', pr_number=496)
```

### 4.3 Worker Events

```python
# Spawned
logger.log_worker(session_id, 'w-abc123', 'gh-450', 'spawned',
                 pid=12345, log_file='logs/gh-450.jsonl')

# Completed
logger.log_worker(session_id, 'w-abc123', 'gh-450', 'completed',
                 exit_code=0)
```

### 4.4 Generic Events

```python
# Trigger
logger.log_event(session_id, 'trigger', 'info',
                'GitHub issue detected: gh-450',
                details={'issue_number': 450})

# Decision
logger.log_event(session_id, 'decision', 'info',
                'Preserved worktree - recent changes',
                context_type='worktree', context_id='gh-450',
                details={'file_age_minutes': 0.2})

# Error
logger.log_event(session_id, 'error', 'error',
                'Worker spawn failed',
                context_type='worker', context_id='w-abc123',
                details={'error': 'OOM'})
```

### 4.5 API Calls

```python
logger.log_api_call(worker_id, model='claude-sonnet-4-5',
                   tokens_input=5000, tokens_output=2000,
                   estimated_cost_usd=0.045, duration_ms=3200)
```

---

## 5. External Storage - Keep It Simple

**Single Database**: `/mnt/external-hdd/tac8/logs.db`
**JSONL Files**: `/mnt/external-hdd/tac8/conversations/`

**Fallback Strategy**:
```python
# Try external first, fallback to local
db_paths = [
    '/mnt/external-hdd/tac8/logs.db',  # External
    '/var/lib/tac8/logs.db'            # Local fallback
]

for path in db_paths:
    if Path(path).parent.exists():
        db_path = path
        break
```

**Archive Strategy**: Simple
- Keep last 90 days in active DB
- Monthly archive script: `./tools/archive-logs.py --older-than 90`
- Archives to: `/mnt/external-hdd/tac8/archive/logs-2025-10.db`

---

## 6. Query Examples (Much Simpler!)

### Cost Tracking

```sql
-- Today's cost
SELECT SUM(estimated_cost_usd) FROM api_calls
WHERE date(timestamp) = date('now');

-- Cost by task
SELECT t.task_id, t.title, SUM(ac.estimated_cost_usd) as cost
FROM tasks t
JOIN workers w ON w.task_id = t.task_id
JOIN api_calls ac ON ac.worker_id = w.worker_id
GROUP BY t.task_id;
```

### Task Status

```sql
-- Active tasks
SELECT * FROM tasks WHERE status = 'active';

-- Completed today
SELECT * FROM tasks
WHERE status = 'completed' AND date(completed_at) = date('now');

-- Task duration
SELECT task_id,
       (julianday(completed_at) - julianday(started_at)) * 24 * 60 as minutes
FROM tasks WHERE completed_at IS NOT NULL;
```

### Debugging

```sql
-- All events for a task
SELECT * FROM events
WHERE context_id = 'gh-450'
ORDER BY timestamp;

-- Worker timeline
SELECT
  w.worker_id, w.spawned_at, w.completed_at, w.log_file,
  COUNT(ac.call_id) as api_calls,
  SUM(ac.tokens_total) as total_tokens
FROM workers w
LEFT JOIN api_calls ac ON ac.worker_id = w.worker_id
WHERE w.task_id = 'gh-450'
GROUP BY w.worker_id;
```

---

## 7. Implementation - Much Faster!

### Phase 1: Core (2-3 days)
- [ ] Create `tac_logger.py` with 5-table schema
- [ ] Basic logging methods
- [ ] Unit tests

### Phase 2: Integration (2-3 days)
- [ ] Integrate with coordinator
- [ ] Session, task, worker logging
- [ ] Event logging
- [ ] API call logging

### Phase 3: Tools (2-3 days)
- [ ] Query tool: `./tools/tac-query.py`
- [ ] Archive tool: `./tools/archive-logs.py`
- [ ] Simple dashboard (optional)

**Total**: 1-2 weeks instead of 3

---

## 8. Migration Strategy - Simpler

**Phase 1: Start Fresh**
- Just start logging new sessions to SQLite
- Keep all existing JSONL files as-is
- No complex migration needed

**Phase 2 (Optional): Import Historical**
- Parse existing JSONL files
- Extract metadata (task IDs, timestamps, tokens)
- Import to SQLite for historical queries
- Script: `./tools/import-historical-logs.py`

**Phase 3: Archive Old JSONL**
- After 30 days, archive old JSONL to external HDD
- Keep SQLite metadata forever (it's small)

---

## 9. Comparison: Before vs After

### Before (Complex Design)
- 9 tables
- Duplicate conversation content in DB
- Complex joins and queries
- 3-week implementation
- Large database (GB scale)

### After (Simple Design)
- 5 tables
- Conversations stay in JSONL
- Simple queries
- 1-2 week implementation
- Small database (MB scale)

### What We Keep
- ✅ Full audit trail (events table)
- ✅ Cost tracking (api_calls table)
- ✅ Task lifecycle (tasks table)
- ✅ Worker tracking (workers table)
- ✅ Decision logging (events table)
- ✅ External storage (JSONL files)
- ✅ Easy queries (SQL)
- ✅ Full conversations (JSONL)

### What We Simplify
- ❌ No separate logic_flow table (use events)
- ❌ No separate action_triggers table (use events)
- ❌ No separate worktree_operations table (use events)
- ❌ No duplicate conversations in DB (use JSONL)

---

## 10. Example Usage

### Start coordinator
```python
logger = TACLogger('/mnt/external-hdd/tac8/logs.db')
session_id = logger.start_session(config, git_info)
```

### Log workflow
```python
# Issue detected
logger.log_event(session_id, 'trigger', 'info',
                'GitHub issue detected: gh-450')
logger.log_task(session_id, 'gh-450', 'detected', issue_number=450)

# Worker spawned
logger.log_worker(session_id, 'w-abc123', 'gh-450', 'spawned',
                 log_file='logs/gh-450.jsonl')

# Worktree decision
logger.log_event(session_id, 'decision', 'info',
                'Preserved worktree - recent changes',
                context_id='gh-450',
                details={'file_age_minutes': 0.2, 'action': 'preserve'})

# API call
logger.log_api_call('w-abc123', 'claude-sonnet-4-5',
                   tokens_input=5000, tokens_output=2000,
                   estimated_cost_usd=0.045)

# Worker completed
logger.log_worker(session_id, 'w-abc123', 'gh-450', 'completed')
logger.log_task(session_id, 'gh-450', 'completed', pr_number=496)
```

### Query
```bash
# Cost today
./tools/tac-query.py cost --today

# Task status
./tools/tac-query.py task gh-450

# Worker logs
./tools/tac-query.py worker w-abc123 --show-conversation

# Events
./tools/tac-query.py events --type decision --last 24h
```

---

## 11. Open Questions (Simplified)

1. **Database Location**: External HDD path? Fallback to local?
   - Proposed: `/mnt/external-hdd/tac8/logs.db` with `/var/lib/tac8/logs.db` fallback

2. **Archive Threshold**: How many days to keep in active DB?
   - Proposed: 90 days

3. **Dashboard**: Want web dashboard? Or just CLI tools?
   - Proposed: Start with CLI, add dashboard later if needed

---

## 12. Summary

**Simplified from 9 tables to 5 tables**
**Implementation time: 1-2 weeks instead of 3**
**Database size: MB instead of GB**
**Complexity: Much lower**
**Functionality: Same!**

**Core principle**: Use JSONL for what it's good at (full content), use SQLite for what it's good at (queries/aggregations).

---

**Document Status**: Ready for Review (Simplified Version)
**Reviewers**: @shane
**Approval Required**: Yes
