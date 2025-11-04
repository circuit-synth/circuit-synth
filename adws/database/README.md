# TAC-X Database

PostgreSQL database for Hybrid TAC Architecture.

## Quick Start

```bash
# 1. Setup PostgreSQL in Docker
./tools/setup-postgres-docker.sh

# 2. Run migrations
docker exec -i tacx-postgres psql -U tacx -d tacx < adws/database/migrations/001_initial_schema.sql

# 3. Verify tables
docker exec tacx-postgres psql -U tacx -d tacx -c "\dt"
```

## Schema Overview

### Tables (7 total)

1. **tac_tasks** - Main task tracking
   - Links to GitHub issue
   - Tracks overall status and costs
   - Auto-calculates total costs via triggers

2. **tac_stages** - 4-stage pipeline execution
   - planning, building, reviewing, pr_creation
   - Per-stage provider/model/costs

3. **tac_helper_agents** - Dynamically spawned helpers
   - research-agent, test-agent, etc.
   - Linked to parent stage

4. **tac_events** - Complete event log
   - Every hook, tool use, response
   - Supports AI summarization

5. **tac_agent_templates** - Reusable agent configs
   - Loaded from `.claude/agents/*.md`
   - YAML frontmatter with tools/model/prompt

6. **tac_cost_summary** - Daily cost rollup
   - Fast queries for cost analysis
   - Breakdown by stage and helper type

7. **schema_version** - Migration tracking

### Automatic Features

- **Cost Rollup**: Tasks auto-update total costs when stages/helpers complete
- **Timestamp Updates**: `updated_at` columns auto-update
- **Test Functions**: `insert_test_task()` for quick testing

## Testing

```bash
# Test database functionality
docker exec tacx-postgres psql -U tacx -d tacx -c "
SELECT insert_test_task('TEST-001');
SELECT * FROM tac_tasks WHERE issue_number = 'TEST-001';
DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-%';
"
```

## Connection

```bash
# DATABASE_URL
postgresql://tacx:tacx@localhost:5433/tacx

# Direct psql access
docker exec -it tacx-postgres psql -U tacx -d tacx

# Stop/start container
docker stop tacx-postgres
docker start tacx-postgres
```

## Next Steps

Phase 2: Create `adw_modules/tac_database.py` with async CRUD operations.
