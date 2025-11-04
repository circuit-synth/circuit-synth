# Hybrid TAC Architecture - Implementation Plan

**Branch:** `feat/hybrid-tac-architecture`
**Status:** 🔴 In Progress - Phase 1
**Est. Total Time:** 26 hours (3-4 weeks at 2h/day)

---

## What We're Building

A **hybrid TAC architecture** that combines:
1. ✅ Predictable 4-stage pipeline (keep existing)
2. ✨ NEW: Dynamic helper agents (spawned on demand)
3. ✨ NEW: PostgreSQL persistence (queryable history)
4. ✨ NEW: Web dashboard (real-time visibility)
5. ✨ NEW: Agent template system (reusable agents)

---

## Implementation Strategy

### Principle: **Test-Driven Incremental Rollout**

Each phase is:
- **Independently testable** - Can run `python3 test_phase_X.py`
- **Backward compatible** - Existing TAC continues working
- **Self-documenting** - Logs show what's happening
- **Rollback-safe** - Can disable new features with flags

---

## Phase 1: PostgreSQL Foundation (3 hours) 🔴 IN PROGRESS

### Goal
Set up database and prove it works end-to-end.

### Files Created
- ✅ `adws/database/migrations/001_initial_schema.sql` - Schema with all tables
- ✅ `adws/database/run_migrations.py` - Migration runner with self-tests
- ✅ `tools/setup-postgres-docker.sh` - Docker setup script

### Test Plan
```bash
# 1. Setup PostgreSQL in Docker
./tools/setup-postgres-docker.sh

# 2. Run migrations
export DATABASE_URL="postgresql://tacx:tacx@localhost:5433/tacx"
python3 adws/database/run_migrations.py

# Expected output:
# ✓ Migration applied successfully
# ✓ Test task created
# ✓ Test data cleaned up
# ✓ Database test completed successfully!
```

### Success Criteria
- [ ] PostgreSQL container running
- [ ] All 6 tables created
- [ ] Test data inserts/queries work
- [ ] Triggers update costs automatically

### Next Step
Create `adws/adw_modules/tac_database.py` module

---

## Phase 2: Database Module (4 hours)

### Goal
Create async database module with all CRUD operations.

### Files to Create
- `adws/adw_modules/tac_database.py` - Database class with connection pool
- `adws/adw_modules/tac_models.py` - Pydantic models for type safety
- `tests/test_tac_database.py` - Unit tests for database operations

### Test Plan
```python
# tests/test_tac_database.py
async def test_create_task():
    db = TACDatabase()
    task_id = await db.create_task(issue_number="TEST-001")
    task = await db.get_task(task_id)
    assert task.issue_number == "TEST-001"
    assert task.status == "running"

async def test_create_stage():
    db = TACDatabase()
    task_id = await db.create_task("TEST-002")
    stage_id = await db.create_stage(
        task_id=task_id,
        stage_name="planning",
        provider="openrouter",
        model="google/gemini-2.5-flash"
    )
    stage = await db.get_stage(stage_id)
    assert stage.status == "pending"

async def test_log_event():
    db = TACDatabase()
    task_id = await db.create_task("TEST-003")
    event_id = await db.log_event(
        task_id=task_id,
        event_category="system",
        event_type="Info",
        content="Test event"
    )
    events = await db.get_task_events(task_id)
    assert len(events) == 1
```

### Success Criteria
- [ ] All CRUD operations work
- [ ] Connection pool handles concurrent queries
- [ ] Pydantic models parse DB rows correctly
- [ ] All tests pass

---

## Phase 3: Agent Template System (2 hours)

### Goal
Load agent templates from `.claude/agents/*.md` files with YAML frontmatter.

### Files to Create
- `.claude/agents/research-agent.md` - Example template
- `.claude/agents/test-agent.md` - Example template
- `.claude/agents/security-scanner.md` - Example template
- `adws/adw_modules/agent_templates.py` - Template loader
- `tools/register-agent-templates.py` - Register templates in DB

### Example Template
```markdown
---
name: research-agent
description: Investigates codebase for context and documentation
tools: [Read, Grep, Glob, WebFetch]
model: haiku
temperature: 0.7
color: blue
---

# research-agent

You are a specialized research agent. Your job is to gather context about a codebase by:

1. Reading relevant files
2. Searching for patterns
3. Fetching external documentation if needed
4. Summarizing findings concisely

Always provide:
- List of files examined
- Key findings (bullet points)
- Recommendations for next steps
```

### Test Plan
```python
# tools/register-agent-templates.py --test
async def test_load_templates():
    loader = AgentTemplateLoader()
    templates = await loader.load_all_templates()
    assert "research-agent" in templates
    assert "test-agent" in templates
    assert templates["research-agent"].model == "haiku"

async def test_register_in_db():
    db = TACDatabase()
    loader = AgentTemplateLoader()
    await loader.register_templates(db)

    template = await db.get_agent_template("research-agent")
    assert template.name == "research-agent"
    assert "Read" in template.tools
```

### Success Criteria
- [ ] Templates load from `.claude/agents/*.md`
- [ ] YAML frontmatter parsed correctly
- [ ] Templates registered in database
- [ ] Can query templates by name

---

## Phase 4: Helper Agent Spawn Mechanism (6 hours)

### Goal
Allow stages to spawn helper agents and await their results.

### Files to Modify
- `adws/adw_modules/multi_stage_worker.py` - Add helper spawn support
- `adws/adw_modules/llm_providers.py` - Add `create_helper_agent` tool

### New Tool: `create_helper_agent`

```python
# Available to all 4 stages during execution

def create_helper_agent(template_name: str, command: str) -> dict:
    """
    Spawn a helper agent from template.

    Args:
        template_name: Name of template (e.g., "research-agent")
        command: Task for helper to execute

    Returns:
        {
            "helper_id": "uuid",
            "status": "completed",
            "result": "Helper's response text",
            "cost": 0.023
        }
    """
    pass
```

### Example: Planner Spawns Research Agent

```
User creates issue #504: "Add potentiometer component support"

Coordinator starts TAC pipeline:
  → Stage 1: Planning

Planner agent (Claude Sonnet):
  "I need to understand the existing component structure first.
   Let me spawn a research agent to investigate."

  [Calls create_helper_agent("research-agent", "Find all existing component implementations and summarize the pattern")]

Research helper (Claude Haiku):
  Reads: src/components/resistor.py
  Reads: src/components/capacitor.py
  Greps for: "class.*Component"

  Returns: "Found 12 component classes following pattern:
  - Inherit from Component base class
  - __init__(self, reference, value)
  - _select_footprint() method
  - to_kicad() method for netlist generation"

Planner: "Perfect! I now have enough context to create a detailed plan."
  Writes: plan.md

  Stage 1 completes → Stage 2: Building
```

### Test Plan
```python
# tests/test_helper_spawn.py
async def test_spawn_helper():
    worker = MultiStageWorker(...)
    helper_id = await worker.spawn_helper_agent(
        stage_id=stage_id,
        template_name="research-agent",
        command="List all Python files in src/"
    )

    helper = await db.get_helper_agent(helper_id)
    assert helper.status == "completed"
    assert helper.result_data is not None

async def test_helper_events_logged():
    worker = MultiStageWorker(...)
    helper_id = await worker.spawn_helper_agent(...)

    events = await db.get_helper_events(helper_id)
    assert len(events) > 0  # Should have hook events
```

### Success Criteria
- [ ] Stages can spawn helpers
- [ ] Helpers execute and return results
- [ ] Helper events logged to database
- [ ] Costs tracked separately
- [ ] Parent stage waits for helper completion

---

## Phase 5: Update MultiStageWorker for PostgreSQL (4 hours)

### Goal
Migrate MultiStageWorker to use PostgreSQL instead of JSONL files.

### Implementation: Dual-Write Pattern

```python
# adws/adw_modules/multi_stage_worker.py

class MultiStageWorker:
    def __init__(self, ...):
        # ... existing code ...

        # NEW: Database connection
        self.db = TACDatabase() if config.get("use_postgres", True) else None

    async def run(self):
        """Execute 4-stage pipeline with PostgreSQL logging"""

        # Create task in database
        if self.db:
            self.task_id_db = await self.db.create_task(
                issue_number=self.issue_number,
                workflow_config=self.workflow.to_dict(),
                metadata={
                    "worktree_path": str(self.worktree_path),
                    "branch_name": self.branch_name
                }
            )

        # Run stages (existing logic)
        for stage in self.workflow.stages:
            await self.run_stage(stage)

    async def run_stage(self, stage_config):
        """Execute single stage with PostgreSQL logging"""

        # Create stage in database
        if self.db:
            stage_id_db = await self.db.create_stage(
                task_id=self.task_id_db,
                stage_name=stage_config.name,
                provider=stage_config.provider,
                model=stage_config.model,
                temperature=stage_config.temperature
            )

        # Existing stage execution logic...
        result = self.invoke_llm(stage_config)

        # Log to database
        if self.db:
            await self.db.update_stage(
                stage_id_db,
                status="completed",
                input_tokens=result.usage["input_tokens"],
                output_tokens=result.usage["output_tokens"],
                cost=result.cost
            )

        # ALSO log to JSONL (dual-write during transition)
        self._write_jsonl(result)
```

### Test Plan
```python
# tests/test_multi_stage_postgres.py
async def test_full_pipeline_postgres():
    """Test that full pipeline logs to PostgreSQL"""
    worker = MultiStageWorker(
        task_id="test-task",
        issue_number="TEST-004",
        ...
    )

    state = await worker.run()

    # Check database
    task = await db.get_task_by_issue("TEST-004")
    assert task.status == "completed"
    assert task.total_cost > 0

    stages = await db.get_task_stages(task.id)
    assert len(stages) == 4  # planning, building, reviewing, pr_creation

    events = await db.get_task_events(task.id)
    assert len(events) > 0  # Should have many events
```

### Success Criteria
- [ ] Tasks created in PostgreSQL
- [ ] Stages tracked in PostgreSQL
- [ ] Events logged to PostgreSQL
- [ ] Costs calculated automatically
- [ ] JSONL still works (dual-write)
- [ ] Can disable PostgreSQL with flag

---

## Phase 6: Web Dashboard Backend (2 hours)

### Goal
FastAPI backend serving real-time data from PostgreSQL.

### Files to Create
- `adws/web_dashboard/backend/main.py` - FastAPI app
- `adws/web_dashboard/backend/routes.py` - API endpoints
- `adws/web_dashboard/backend/websocket.py` - WebSocket manager

### API Endpoints

```python
# GET /tasks - List all tasks
# GET /tasks/{task_id} - Get task details
# GET /tasks/{task_id}/stages - Get task stages
# GET /tasks/{task_id}/events - Get task events (with streaming)
# GET /tasks/{task_id}/helpers - Get helper agents for task
# GET /templates - List agent templates
# WS /ws - WebSocket for real-time updates
```

### Test Plan
```bash
# Start backend
cd adws/web_dashboard/backend
uvicorn main:app --reload --port 9500

# Test endpoints
curl http://localhost:9500/tasks
curl http://localhost:9500/tasks/{task_id}
curl http://localhost:9500/tasks/{task_id}/events

# Test WebSocket
wscat -c ws://localhost:9500/ws
```

### Success Criteria
- [ ] All endpoints return data
- [ ] WebSocket broadcasts events
- [ ] CORS configured for frontend
- [ ] Real-time updates work

---

## Phase 7: Web Dashboard Frontend (2 hours)

### Goal
Vue 3 dashboard showing tasks, events, and costs in real-time.

### Files to Create
- `adws/web_dashboard/frontend/src/App.vue` - Main app
- `adws/web_dashboard/frontend/src/components/TaskList.vue`
- `adws/web_dashboard/frontend/src/components/EventStream.vue`
- `adws/web_dashboard/frontend/src/stores/tacStore.ts` - Pinia store

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ TAC-X Dashboard                          Cost: $2.45    │
├─────────────┬───────────────────────────────────────────┤
│ Tasks       │ Event Stream                              │
│             │                                           │
│ #504 ✓      │ [12:34:56] Planning started              │
│ #505 →      │ [12:35:01] Helper: research-agent spawn  │
│ #506 ⏸      │ [12:35:15] Helper: completed ($0.03)     │
│             │ [12:35:20] Planning completed            │
│             │ [12:35:25] Building started              │
│             │ [12:35:40] Tool: Write → component.py    │
│             │ [12:36:00] Building completed            │
│             │                                           │
└─────────────┴───────────────────────────────────────────┘
```

### Success Criteria
- [ ] Shows all tasks from database
- [ ] Real-time event stream via WebSocket
- [ ] Cost tracking visible
- [ ] Helper agents shown inline
- [ ] Responsive design

---

## Phase 8: Integration Testing (3 hours)

### Goal
End-to-end tests proving everything works together.

### Test Scenarios

```python
# tests/integration/test_hybrid_tac_e2e.py

async def test_e2e_with_helper_agent():
    """Full pipeline with helper agent spawn"""

    # 1. Create test issue
    issue = create_test_github_issue("Add LED component")

    # 2. Start coordinator
    coordinator = TACCoordinator()

    # 3. Coordinator creates task
    task = await coordinator.process_issue(issue)

    # 4. Planning stage runs
    # 5. Planner spawns research-agent
    # 6. Research agent completes
    # 7. Planner completes with plan.md
    # 8. Building stage runs
    # 9. Builder spawns test-agent
    # 10. Test agent writes tests
    # 11. Builder completes with code
    # 12. Reviewing stage runs
    # 13. Reviewer approves
    # 14. PR creation stage runs
    # 15. PR created

    # Verify database
    task = await db.get_task(task.id)
    assert task.status == "completed"

    stages = await db.get_task_stages(task.id)
    assert all(s.status == "completed" for s in stages)

    helpers = await db.get_task_helpers(task.id)
    assert len(helpers) >= 2  # research-agent + test-agent

    events = await db.get_task_events(task.id)
    assert len(events) > 50  # Many events logged

    # Verify costs
    assert task.total_cost > 0
    assert task.total_input_tokens > 0
    assert task.total_output_tokens > 0
```

### Success Criteria
- [ ] Full pipeline completes
- [ ] Helper agents spawn and complete
- [ ] All data in PostgreSQL
- [ ] Web dashboard shows real-time updates
- [ ] Costs tracked correctly
- [ ] JSONL files still generated (dual-write)

---

## Testing Strategy

### Unit Tests
Each module has its own test file:
- `tests/test_tac_database.py`
- `tests/test_agent_templates.py`
- `tests/test_helper_spawn.py`
- `tests/test_multi_stage_postgres.py`

### Integration Tests
Full end-to-end scenarios:
- `tests/integration/test_hybrid_tac_e2e.py`
- `tests/integration/test_web_dashboard.py`

### Manual Testing
Self-testing scripts:
- `python3 adws/database/run_migrations.py --test-data`
- `python3 tools/register-agent-templates.py --test`
- `python3 tools/test-helper-spawn.py`

---

## Rollout Strategy

### Week 1: Foundation
- Setup PostgreSQL
- Create database module
- Register agent templates
- **Deliverable:** Can query database, templates loaded

### Week 2: Core Features
- Helper spawn mechanism
- Update MultiStageWorker
- **Deliverable:** Pipeline logs to PostgreSQL, helpers work

### Week 3: Dashboard
- Build backend API
- Build frontend UI
- **Deliverable:** Web dashboard shows real-time data

### Week 4: Testing & Polish
- Integration tests
- Documentation
- **Deliverable:** Production-ready system

---

## Configuration Flags

Enable/disable features with environment variables:

```bash
# Enable PostgreSQL (default: true)
export TAC_USE_POSTGRES=true

# Enable helper agents (default: true)
export TAC_ENABLE_HELPERS=true

# Enable dual-write to JSONL (default: true during transition)
export TAC_WRITE_JSONL=true

# Enable web dashboard (default: true)
export TAC_WEB_DASHBOARD=true

# Database URL
export DATABASE_URL="postgresql://tacx:tacx@localhost:5433/tacx"
```

---

## Success Metrics

### Performance
- [ ] Pipeline execution time < 10 min for typical issue
- [ ] Helper agents add < 2 min overhead
- [ ] Database queries < 100ms
- [ ] WebSocket latency < 500ms

### Cost
- [ ] Helper agents cost < 20% of total
- [ ] Total cost tracked accurately to $0.001
- [ ] Budget limits enforced

### Reliability
- [ ] 95% pipeline success rate
- [ ] Helper agents don't block main pipeline
- [ ] Database connection pool stable
- [ ] Web dashboard 99% uptime

---

## Current Status

**Phase 1: PostgreSQL Foundation** 🔴 IN PROGRESS

Files created:
- ✅ `adws/database/migrations/001_initial_schema.sql`
- ✅ `adws/database/run_migrations.py`
- ✅ `tools/setup-postgres-docker.sh`

Next steps:
1. Run `./tools/setup-postgres-docker.sh`
2. Test migrations
3. Create database module (Phase 2)

---

**Last Updated:** 2025-11-03
**Branch:** feat/hybrid-tac-architecture
