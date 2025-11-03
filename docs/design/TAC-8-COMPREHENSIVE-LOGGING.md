# TAC-8 Comprehensive Logging System - Design Document

**Version**: 1.0
**Date**: 2025-11-03
**Status**: Design Phase

---

## 1. Overview

### 1.1 Purpose

Design a comprehensive SQLite-based logging system for TAC-8 coordinator that captures every aspect of the autonomous workflow for:
- Full audit trail and debugging
- Performance analysis and optimization
- Cost tracking and budget management
- Conversation replay and analysis
- System health monitoring
- Incident investigation

### 1.2 Requirements

**Must Log**:
1. Action triggers received (GitHub issues, polling, signals)
2. Logic flow chain (every decision point with reasoning)
3. Token usage (input, output, cached, costs)
4. Dates and times for everything
5. Full LLM conversations (prompts and responses)
6. Worker lifecycle (spawn, progress, completion)
7. Worktree operations (create, remove, preserve decisions)
8. Task state transitions
9. System events (startup, shutdown, errors)

**Design Goals**:
- Easy querying and analysis
- Minimal performance overhead
- Support external storage (external HDD)
- Future-proof schema with migrations
- Queryable with standard SQL tools
- No loss of existing JSONL logs (migration strategy)

---

## 2. Database Schema Design

### 2.1 Schema Overview

Nine core tables capturing different aspects of TAC-8:

```
┌─────────────────────────┐
│ coordinator_sessions    │ ← Root entity (one per coordinator run)
└───────┬─────────────────┘
        │
        ├──→ action_triggers    (what triggered actions)
        ├──→ logic_flow         (decision points with reasoning)
        ├──→ system_events      (startup, shutdown, errors)
        │
        └──→ tasks ─┬──→ worker_sessions ─┬──→ conversations
                    │                     ├──→ api_calls
                    │                     └──→ (external refs)
                    │
                    └──→ worktree_operations
```

### 2.2 Table Schemas

#### 2.2.1 Coordinator Sessions

Tracks each coordinator run from start to finish.

```sql
CREATE TABLE coordinator_sessions (
    session_id TEXT PRIMARY KEY,          -- UUID, e.g., 'ses-2025-11-03-abc123'
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    config JSON,                          -- Full config at startup
    exit_reason TEXT,                     -- 'normal', 'signal', 'error', etc.
    pid INTEGER,
    hostname TEXT,
    git_branch TEXT,
    git_commit TEXT,
    python_version TEXT,
    tac_version TEXT
);
```

**Key Queries**:
- Active sessions: `WHERE ended_at IS NULL`
- Sessions by time range: `WHERE started_at BETWEEN ? AND ?`
- Failed sessions: `WHERE exit_reason = 'error'`

#### 2.2.2 Action Triggers

What caused the coordinator to take action.

```sql
CREATE TABLE action_triggers (
    trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    trigger_type TEXT NOT NULL,           -- 'poll', 'issue_detected', 'label_added'
    trigger_source TEXT,                  -- 'github', 'filesystem', 'signal'
    trigger_data JSON,                    -- Full event details
    task_id TEXT,                         -- If resulted in task
    FOREIGN KEY (session_id) REFERENCES coordinator_sessions(session_id)
);

CREATE INDEX idx_triggers_session ON action_triggers(session_id, timestamp);
CREATE INDEX idx_triggers_type ON action_triggers(trigger_type, timestamp);
```

**Key Queries**:
- Triggers per session: `WHERE session_id = ?`
- GitHub issue triggers: `WHERE trigger_type = 'issue_detected'`
- Trigger frequency: `GROUP BY trigger_type, date(timestamp)`

#### 2.2.3 Logic Flow

Decision points in coordinator logic with full reasoning.

```sql
CREATE TABLE logic_flow (
    flow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    context_type TEXT NOT NULL,           -- 'coordinator', 'worker', 'task', 'worktree'
    context_id TEXT,                      -- ID of the object (task_id, worker_id)
    function_name TEXT NOT NULL,          -- Method/function making decision
    decision_point TEXT NOT NULL,         -- Description of decision
    decision_input JSON,                  -- Input state/data
    decision_output JSON,                 -- Output/result
    decision_reason TEXT,                 -- Human-readable explanation
    duration_ms REAL,                     -- Time spent in this decision
    source_file TEXT,                     -- Python file:line for navigation
    FOREIGN KEY (session_id) REFERENCES coordinator_sessions(session_id)
);

CREATE INDEX idx_flow_session ON logic_flow(session_id, timestamp);
CREATE INDEX idx_flow_context ON logic_flow(context_type, context_id);
CREATE INDEX idx_flow_function ON logic_flow(function_name);
```

**Example Entries**:
```json
{
  "context_type": "worktree",
  "context_id": "gh-450",
  "function_name": "create_worktree",
  "decision_point": "worktree_already_exists",
  "decision_input": {
    "worktree_path": "/trees/gh-450",
    "has_changes": true,
    "worker_running": false,
    "file_mtime_age_minutes": 0.2
  },
  "decision_output": {
    "action": "preserve",
    "reason": "Recent changes detected"
  },
  "decision_reason": "Files modified within last 60 minutes indicate fresh work, not stale crash",
  "duration_ms": 5.3
}
```

**Key Queries**:
- Decision chain for task: `WHERE context_id = 'gh-450' ORDER BY timestamp`
- Slow decisions: `WHERE duration_ms > 1000 ORDER BY duration_ms DESC`
- Decision distribution: `GROUP BY decision_point`

#### 2.2.4 Tasks

Full task lifecycle from detection to completion.

```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,             -- 'gh-450', 'manual-001', etc.
    session_id TEXT NOT NULL,
    detected_at TIMESTAMP NOT NULL,
    source TEXT NOT NULL,                 -- 'github', 'manual', 'retry'
    issue_number INTEGER,
    issue_url TEXT,
    title TEXT,
    description TEXT,
    priority INTEGER,
    labels JSON,                          -- ['rpi-auto', 'priority:P1']
    assigned_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    status TEXT NOT NULL,                 -- 'detected', 'assigned', 'active', 'completed', 'failed'
    failure_reason TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    commits JSON,                         -- List of commit SHAs
    FOREIGN KEY (session_id) REFERENCES coordinator_sessions(session_id)
);

CREATE INDEX idx_tasks_session ON tasks(session_id, detected_at);
CREATE INDEX idx_tasks_status ON tasks(status, detected_at);
CREATE INDEX idx_tasks_issue ON tasks(issue_number);
```

**Key Queries**:
- Active tasks: `WHERE status = 'active'`
- Completed tasks today: `WHERE status = 'completed' AND date(completed_at) = date('now')`
- Failed tasks: `WHERE status = 'failed' ORDER BY failed_at DESC`
- Task duration: `SELECT task_id, julianday(completed_at) - julianday(started_at) AS days`

#### 2.2.5 Worker Sessions

Worker lifecycle from spawn to completion/failure.

```sql
CREATE TABLE worker_sessions (
    worker_id TEXT PRIMARY KEY,           -- 'w-abc123'
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    spawned_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    pid INTEGER,
    status TEXT NOT NULL,                 -- 'spawned', 'running', 'completed', 'failed'
    exit_code INTEGER,
    failure_reason TEXT,
    worktree_path TEXT,
    branch_name TEXT,
    prompt_file TEXT,                     -- Path to prompt file
    log_file TEXT,                        -- Path to JSONL log file
    FOREIGN KEY (session_id) REFERENCES coordinator_sessions(session_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

CREATE INDEX idx_workers_task ON worker_sessions(task_id);
CREATE INDEX idx_workers_session ON worker_sessions(session_id, spawned_at);
CREATE INDEX idx_workers_status ON worker_sessions(status);
```

**Key Queries**:
- Active workers: `WHERE status IN ('spawned', 'running')`
- Worker history for task: `WHERE task_id = ?`
- Failed workers: `WHERE status = 'failed'`
- Worker duration: `SELECT worker_id, julianday(completed_at) - julianday(spawned_at) * 24 * 60 AS minutes`

#### 2.2.6 Conversations

Full LLM conversation logs (prompts and responses).

```sql
CREATE TABLE conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id TEXT NOT NULL,
    message_index INTEGER NOT NULL,       -- Order within conversation
    timestamp TIMESTAMP NOT NULL,
    role TEXT NOT NULL,                   -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,                -- Full message content (can be large)
    content_type TEXT,                    -- 'text', 'tool_use', 'tool_result'
    tool_name TEXT,                       -- If tool_use or tool_result
    tool_input JSON,                      -- If tool_use
    tool_output TEXT,                     -- If tool_result
    tool_success BOOLEAN,                 -- If tool_result
    FOREIGN KEY (worker_id) REFERENCES worker_sessions(worker_id),
    UNIQUE(worker_id, message_index)
);

CREATE INDEX idx_conversations_worker ON conversations(worker_id, message_index);
CREATE INDEX idx_conversations_tool ON conversations(tool_name, timestamp);
```

**Storage Consideration**: This table will be LARGE. Consider:
- Storing on external HDD (separate database file?)
- Compression (gzip content column?)
- Archival strategy (move old conversations to archive DB)

**Key Queries**:
- Full conversation: `WHERE worker_id = ? ORDER BY message_index`
- Tool usage stats: `SELECT tool_name, COUNT(*) FROM conversations WHERE content_type = 'tool_use' GROUP BY tool_name`
- Failed tool calls: `WHERE content_type = 'tool_result' AND tool_success = FALSE`

#### 2.2.7 API Calls

API usage, token counts, and costs.

```sql
CREATE TABLE api_calls (
    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    model TEXT NOT NULL,                  -- 'claude-sonnet-4-5', 'gpt-4', etc.
    provider TEXT,                        -- 'anthropic', 'openrouter', 'openai'
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_total INTEGER,
    tokens_cached_read INTEGER,           -- Cache hits
    tokens_cached_write INTEGER,          -- Cache writes
    estimated_cost_usd REAL,
    actual_cost_usd REAL,                 -- If available from provider
    time_to_first_token_ms REAL,
    duration_ms REAL,
    tokens_per_second REAL,
    success BOOLEAN,
    error_message TEXT,
    error_code TEXT,
    FOREIGN KEY (worker_id) REFERENCES worker_sessions(worker_id)
);

CREATE INDEX idx_api_calls_worker ON api_calls(worker_id, timestamp);
CREATE INDEX idx_api_calls_model ON api_calls(model, timestamp);
CREATE INDEX idx_api_calls_date ON api_calls(date(timestamp));
```

**Key Queries**:
- Total cost today: `SELECT SUM(estimated_cost_usd) FROM api_calls WHERE date(timestamp) = date('now')`
- Cost by model: `SELECT model, SUM(estimated_cost_usd) FROM api_calls GROUP BY model`
- Token usage: `SELECT SUM(tokens_total) FROM api_calls WHERE worker_id = ?`
- Performance: `SELECT AVG(tokens_per_second), AVG(time_to_first_token_ms) FROM api_calls WHERE model = ?`

#### 2.2.8 Worktree Operations

Worktree create, remove, preserve operations with full decision logic.

```sql
CREATE TABLE worktree_operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    operation TEXT NOT NULL,              -- 'create', 'remove', 'preserve', 'check'
    worktree_path TEXT NOT NULL,
    branch_name TEXT,
    decision_reason TEXT,                 -- Why was this action taken?
    had_changes BOOLEAN,                  -- git status showed changes
    was_clean BOOLEAN,                    -- git status clean
    worker_running BOOLEAN,               -- Worker process was running
    worker_pid INTEGER,
    file_mtime_age_minutes REAL,          -- Most recent file modification age
    decision_logic JSON,                  -- Full decision inputs/reasoning
    FOREIGN KEY (session_id) REFERENCES coordinator_sessions(session_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

CREATE INDEX idx_worktree_ops_task ON worktree_operations(task_id, timestamp);
CREATE INDEX idx_worktree_ops_operation ON worktree_operations(operation, timestamp);
```

**Example Entry**:
```json
{
  "operation": "preserve",
  "worktree_path": "/trees/gh-450",
  "decision_reason": "Recent changes detected - preserving completed work",
  "had_changes": true,
  "was_clean": false,
  "worker_running": false,
  "file_mtime_age_minutes": 0.2,
  "decision_logic": {
    "check_order": ["has_changes", "worker_running", "file_mtime"],
    "threshold_minutes": 60,
    "result": "preserve"
  }
}
```

**Key Queries**:
- Preserved worktrees: `WHERE operation = 'preserve'`
- Spawn loop detection: Count rapid create/remove cycles
- Decision effectiveness: Analyze preserve vs remove outcomes

#### 2.2.9 System Events

General coordinator events (startup, shutdown, errors, warnings).

```sql
CREATE TABLE system_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,             -- 'startup', 'shutdown', 'error', 'warning'
    severity TEXT NOT NULL,               -- 'debug', 'info', 'warning', 'error', 'critical'
    component TEXT,                       -- Which component logged this
    message TEXT NOT NULL,
    details JSON,                         -- Additional structured data
    stack_trace TEXT,                     -- If exception
    FOREIGN KEY (session_id) REFERENCES coordinator_sessions(session_id)
);

CREATE INDEX idx_events_session ON system_events(session_id, timestamp, severity);
CREATE INDEX idx_events_type ON system_events(event_type, severity);
```

**Key Queries**:
- Errors today: `WHERE severity IN ('error', 'critical') AND date(timestamp) = date('now')`
- Events by component: `WHERE component = 'worktree_manager' ORDER BY timestamp DESC`
- Error frequency: `SELECT component, COUNT(*) FROM system_events WHERE severity = 'error' GROUP BY component`

---

## 3. Integration Points

### 3.1 Coordinator Lifecycle Logging

**When**: Coordinator start/stop

**Log**:
```python
# At startup
logger.start_session(session_id, config, git_info)
logger.log_event(session_id, 'startup', 'info', 'coordinator',
                'TAC-8 coordinator starting',
                details={'max_workers': 1, 'poll_interval': 30})

# At shutdown
logger.log_event(session_id, 'shutdown', 'info', 'coordinator',
                'Coordinator shutting down gracefully')
logger.end_session(session_id, exit_reason='normal')
```

### 3.2 Action Trigger Logging

**When**: GitHub issue detected, poll cycle, signal received

**Log**:
```python
# Poll cycle
logger.log_trigger(session_id, 'poll_cycle', 'github', {
    'issues_found': 2,
    'new_issues': 1,
    'poll_duration_ms': 453
})

# Issue detected
logger.log_trigger(session_id, 'issue_detected', 'github', {
    'issue_number': 450,
    'title': 'Dashboard: Add token budget monitoring',
    'labels': ['rpi-auto', 'priority:P1'],
    'created_at': '2025-11-03T06:14:45Z'
}, task_id='gh-450')
```

### 3.3 Logic Flow Logging

**When**: Every significant decision point

**Examples**:
```python
# Worktree preservation decision
logger.log_decision(
    session_id, 'worktree', 'gh-450',
    decision_point='create_worktree.worktree_exists_with_changes',
    decision_input={'has_changes': True, 'worker_running': False, 'file_age_min': 0.2},
    decision_output={'action': 'preserve'},
    decision_reason='Recent file changes indicate fresh work, not crash',
    duration_ms=5.3
)

# Task prioritization
logger.log_decision(
    session_id, 'coordinator', None,
    decision_point='select_next_task',
    decision_input={'available_tasks': ['gh-450', 'gh-451'], 'priorities': [1, 2]},
    decision_output={'selected': 'gh-450'},
    decision_reason='Priority P1 task selected over P2',
    duration_ms=1.2
)
```

### 3.4 Task Lifecycle Logging

**When**: Task detection, assignment, start, completion, failure

**Log**:
```python
# Task detected
logger.log_task_detected(session_id, 'gh-450', 'github', 450,
                        'Dashboard: Add token budget monitoring',
                        'Full description...',
                        priority=1, labels=['rpi-auto', 'priority:P1'])

# Task assigned to worker
logger.log_task_status_change('gh-450', 'assigned', worker_id='w-abc123')

# Task started
logger.log_task_status_change('gh-450', 'active')

# Task completed
logger.log_task_status_change('gh-450', 'completed',
                             pr_number=496, pr_url='https://...')
```

### 3.5 Worker Lifecycle Logging

**When**: Worker spawn, status changes, completion

**Log**:
```python
# Worker spawned
logger.log_worker_spawn(session_id, 'w-abc123', 'gh-450',
                       pid=12345, worktree_path='/trees/gh-450',
                       branch_name='auto/w-abc123')

# Worker completed
logger.log_worker_status_change('w-abc123', 'completed', exit_code=0)

# Worker failed
logger.log_worker_status_change('w-abc123', 'failed',
                               exit_code=1, failure_reason='OOM killed')
```

### 3.6 Conversation Logging

**When**: Each message in LLM conversation (parse from JSONL)

**Options**:
1. **Parse existing JSONL files** - Import to database post-facto
2. **Log during worker execution** - Slower but real-time
3. **Hybrid** - Basic logging real-time, full parsing async

**Recommended**: Hybrid approach
- Log API call metadata immediately
- Parse and store full conversation async after worker completion

### 3.7 Worktree Operations Logging

**When**: Create, remove, preserve decisions

**Log**:
```python
logger.log_worktree_operation(
    session_id, 'gh-450',
    operation='preserve',
    worktree_path='/trees/gh-450',
    decision_reason='Recent changes detected - preserving completed work',
    decision_logic={...},
    had_changes=True,
    worker_running=False,
    file_mtime_age_minutes=0.2
)
```

---

## 4. External Storage Configuration

### 4.1 Database Locations

**Option A: Single Database**
- Path: `/mnt/external-hdd/tac8/logs.db`
- Pro: Simple, all data in one place
- Con: Large file, slow over USB

**Option B: Split Databases**
- Main: `/var/lib/tac8/logs.db` (metadata, small)
- Conversations: `/mnt/external-hdd/tac8/conversations.db` (large content)
- Pro: Fast metadata queries, bulk storage external
- Con: Slightly more complex

**Recommendation**: Option B with ATTACH DATABASE

```python
# Configuration
config.toml:
[logging]
main_db = "/var/lib/tac8/logs.db"
conversations_db = "/mnt/external-hdd/tac8/conversations.db"
auto_attach = true

# Usage
conn = sqlite3.connect(main_db)
conn.execute(f"ATTACH DATABASE '{conversations_db}' AS conversations")
# Now can query both: SELECT * FROM main.tasks JOIN conversations.conversations
```

### 4.2 Archival Strategy

**Monthly Archives**:
- Keep last 30 days in active DB
- Archive older data to: `/mnt/external-hdd/tac8/archive/logs-2025-10.db`
- Script: `./tools/archive-logs.py --month 2025-10`

**Benefits**:
- Active DB stays fast
- Historical data preserved
- Easy to query specific months

---

## 5. Query Patterns and Tools

### 5.1 Common Queries

**Cost Tracking**:
```sql
-- Today's cost
SELECT SUM(estimated_cost_usd) as cost_today
FROM api_calls
WHERE date(timestamp) = date('now');

-- Cost by task
SELECT t.task_id, t.title, SUM(ac.estimated_cost_usd) as cost
FROM tasks t
JOIN worker_sessions ws ON ws.task_id = t.task_id
JOIN api_calls ac ON ac.worker_id = ws.worker_id
GROUP BY t.task_id
ORDER BY cost DESC;
```

**Performance Analysis**:
```sql
-- Average worker duration by status
SELECT status, AVG(julianday(completed_at) - julianday(spawned_at)) * 24 * 60 as avg_minutes
FROM worker_sessions
WHERE completed_at IS NOT NULL
GROUP BY status;

-- Slowest decisions
SELECT function_name, decision_point, AVG(duration_ms) as avg_ms
FROM logic_flow
GROUP BY function_name, decision_point
ORDER BY avg_ms DESC
LIMIT 20;
```

**Debugging**:
```sql
-- Full task timeline
SELECT
  'task_detected' as event, detected_at as timestamp
FROM tasks WHERE task_id = 'gh-450'
UNION ALL
SELECT
  'worker_spawned', spawned_at
FROM worker_sessions WHERE task_id = 'gh-450'
UNION ALL
SELECT
  'api_call', timestamp
FROM api_calls ac
JOIN worker_sessions ws ON ac.worker_id = ws.worker_id
WHERE ws.task_id = 'gh-450'
ORDER BY timestamp;
```

### 5.2 Query Tools

Create convenience scripts:

**`./tools/tac-query.py`** - Interactive query tool
```bash
./tools/tac-query.py cost --today
./tools/tac-query.py task gh-450 --full
./tools/tac-query.py sessions --active
./tools/tac-query.py export --task gh-450 --format json
```

**`./tools/tac-dashboard.py`** - Web dashboard (Flask/Streamlit)
- Real-time coordinator status
- Cost tracking graphs
- Task timeline visualization
- Conversation viewer
- Performance metrics

---

## 6. Migration Strategy

### 6.1 Existing JSONL Logs

Don't lose existing data! Migration plan:

**Phase 1: Parallel Logging**
- Keep existing JSONL logs
- Start logging to SQLite in parallel
- Validate SQLite logs match JSONL

**Phase 2: Import Historical Data**
- Script: `./tools/import-jsonl-to-sqlite.py`
- Parse all existing JSONL files
- Import to SQLite with retroactive session IDs
- Preserve original timestamps

**Phase 3: Deprecate JSONL**
- After 30 days of parallel logging
- Archive JSONL files to `/mnt/external-hdd/tac8/archive/jsonl/`
- Switch to SQLite-only

### 6.2 Schema Migrations

Use Alembic or simple version tracking:

```python
# In tac_logger.py
SCHEMA_VERSION = 2

def migrate_v1_to_v2(conn):
    """Add new columns for version 2"""
    conn.execute("ALTER TABLE tasks ADD COLUMN estimated_cost_usd REAL")
    conn.execute("UPDATE schema_version SET version = 2")
```

---

## 7. Performance Considerations

### 7.1 Write Performance

**Batch Inserts**: Group related logs
```python
# Instead of 100 separate INSERT calls:
conn.executemany("INSERT INTO conversations VALUES (?,?,?...)", messages)
```

**Async Logging**: Don't block coordinator
```python
from queue import Queue
from threading import Thread

log_queue = Queue()

def log_worker():
    while True:
        log_entry = log_queue.get()
        logger.log_to_db(log_entry)

Thread(target=log_worker, daemon=True).start()
```

**WAL Mode**: Better concurrency
```python
conn.execute("PRAGMA journal_mode=WAL")
```

### 7.2 Query Performance

**Indexes**: Already defined in schema

**ANALYZE**: Keep statistics up to date
```python
conn.execute("ANALYZE")  # Run weekly
```

**Connection Pooling**: Reuse connections
```python
from contextlib import contextmanager

@contextmanager
def get_connection():
    # Reuse connection from pool
    conn = connection_pool.get()
    try:
        yield conn
    finally:
        connection_pool.return(conn)
```

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create `tac_logger.py` with schema
- [ ] Database initialization
- [ ] Basic logging methods
- [ ] Unit tests for schema

### Phase 2: Coordinator Integration (Week 1)
- [ ] Session lifecycle logging
- [ ] Action trigger logging
- [ ] System events logging
- [ ] Test with coordinator

### Phase 3: Worker Integration (Week 2)
- [ ] Task lifecycle logging
- [ ] Worker lifecycle logging
- [ ] Worktree operations logging
- [ ] Logic flow logging

### Phase 4: Conversation & API (Week 2)
- [ ] API call logging
- [ ] JSONL parser for conversations
- [ ] Async conversation import
- [ ] Historical data import

### Phase 5: Tools & Dashboard (Week 3)
- [ ] Query convenience tools
- [ ] Web dashboard
- [ ] Cost tracking reports
- [ ] Performance analysis tools

### Phase 6: Production Deployment (Week 3)
- [ ] External storage configuration
- [ ] Archival scripts
- [ ] Monitoring and alerts
- [ ] Documentation

---

## 9. Success Criteria

System is successful when:

1. ✅ **Complete Audit Trail**: Every action is logged with reasoning
2. ✅ **Easy Debugging**: Can reconstruct any coordinator decision
3. ✅ **Cost Visibility**: Know exactly what tokens/costs were used
4. ✅ **Performance**: <10ms logging overhead per decision
5. ✅ **Queryable**: Can answer "what happened?" in seconds
6. ✅ **Reliable**: No data loss, handles coordinator crashes
7. ✅ **Scalable**: Supports months of operation without slowdown

---

## 10. Open Questions

1. **Conversation Storage**: Compress content? Separate DB? Archive threshold?
2. **External HDD Mount**: Auto-mount strategy? Fallback if unavailable?
3. **Log Rotation**: When to archive? How much to keep active?
4. **Real-time Dashboard**: WebSocket updates? Polling interval?
5. **Alert System**: Slack/email notifications for errors? Budget exceeded?

**Next Steps**: Review this design → Make decisions on open questions → Start implementation

---

**Document Status**: Ready for Review
**Reviewers**: @shane
**Approval Required**: Yes
