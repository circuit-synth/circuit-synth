#!/usr/bin/env python3
"""
TAC-X Database Module

Async database operations for Hybrid TAC Architecture.
Provides CRUD operations, event logging, and aggregated queries.
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncpg
from decimal import Decimal
import logging

from .tac_models import (
    TaskModel,
    TaskCreate,
    TaskSummary,
    StageModel,
    StageCreate,
    StageWithEvents,
    HelperAgentModel,
    HelperAgentCreate,
    HelperWithEvents,
    EventModel,
    EventCreate,
    AgentTemplateModel,
    CostSummaryModel,
)

logger = logging.getLogger(__name__)


class TACDatabase:
    """
    Async database operations for TAC system.

    Manages connection pooling, CRUD operations, and complex queries
    for the hybrid TAC architecture.

    Example:
        db = TACDatabase()
        await db.connect()

        task_id = await db.create_task(TaskCreate(issue_number="gh-123"))
        await db.create_stage(StageCreate(task_id=task_id, stage_name="planning"))

        await db.close()
    """

    def __init__(self, database_url: str = None):
        """
        Initialize database connection manager.

        Args:
            database_url: PostgreSQL connection string. If None, uses DATABASE_URL env var.
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", "postgresql://tacx:tacx@localhost:5433/tacx"
        )
        self.pool: Optional[asyncpg.Pool] = None
        logger.debug(f"Initialized TACDatabase with URL: {self._mask_url(self.database_url)}")

    def _mask_url(self, url: str) -> str:
        """Mask password in URL for logging"""
        if "@" in url:
            parts = url.split("@")
            auth = parts[0].split("//")[1]
            if ":" in auth:
                user = auth.split(":")[0]
                return url.replace(auth, f"{user}:***")
        return url

    def _parse_jsonb_fields(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSONB fields that come back as JSON strings from asyncpg"""
        jsonb_fields = ['workflow_config', 'metadata', 'payload', 'result_data', 'stage_costs', 'helper_costs']
        for field in jsonb_fields:
            if field in row_dict and isinstance(row_dict[field], str):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except (json.JSONDecodeError, TypeError):
                    pass  # Keep as-is if not valid JSON
        return row_dict

    async def connect(self, min_size: int = 5, max_size: int = 20):
        """
        Create connection pool.

        Args:
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections to create
        """
        if self.pool:
            logger.warning("Connection pool already exists, skipping")
            return

        logger.info(f"Creating connection pool (min={min_size}, max={max_size})")
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
            )
            logger.info("✓ Connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    async def close(self):
        """Close connection pool"""
        if self.pool:
            logger.info("Closing connection pool")
            await self.pool.close()
            self.pool = None
            logger.info("✓ Connection pool closed")

    def _ensure_connected(self):
        """Verify connection pool exists"""
        if not self.pool:
            raise RuntimeError("Database not connected. Call await db.connect() first.")

    # ============================================================================
    # Task Operations
    # ============================================================================

    async def create_task(self, task: TaskCreate) -> UUID:
        """
        Create new task.

        Args:
            task: Task creation data

        Returns:
            UUID of created task
        """
        self._ensure_connected()

        logger.info(f"Creating task for issue {task.issue_number}")

        query = """
            INSERT INTO tac_tasks (
                issue_number, workflow_config, worktree_path,
                branch_name, metadata, status, started_at
            )
            VALUES ($1, $2, $3, $4, $5, 'running', NOW())
            RETURNING id;
        """

        task_id = await self.pool.fetchval(
            query,
            task.issue_number,
            json.dumps(task.workflow_config) if task.workflow_config else None,
            task.worktree_path,
            task.branch_name,
            json.dumps(task.metadata) if task.metadata else None,
        )

        logger.info(f"✓ Created task {task_id} for issue {task.issue_number}")
        return task_id

    async def get_task(self, task_id: UUID) -> Optional[TaskModel]:
        """
        Get task by ID.

        Args:
            task_id: Task UUID

        Returns:
            TaskModel if found, None otherwise
        """
        self._ensure_connected()

        query = "SELECT * FROM tac_tasks WHERE id = $1;"
        row = await self.pool.fetchrow(query, task_id)

        if row:
            row_dict = self._parse_jsonb_fields(dict(row))
            return TaskModel.model_validate(row_dict)
        return None

    async def update_task_status(
        self,
        task_id: UUID,
        status: str,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update task status and optionally current stage.

        Args:
            task_id: Task UUID
            status: New status (running, completed, errored, blocked, cancelled)
            current_stage: Optional current stage
            error_message: Optional error message

        Returns:
            True if updated, False if task not found
        """
        self._ensure_connected()

        logger.info(f"Updating task {task_id} status to {status}")

        query = """
            UPDATE tac_tasks
            SET status = $2::varchar,
                current_stage = COALESCE($3, current_stage),
                error_message = $4,
                completed_at = CASE WHEN $2::varchar IN ('completed', 'errored', 'cancelled') THEN NOW() ELSE completed_at END
            WHERE id = $1;
        """

        result = await self.pool.execute(query, task_id, status, current_stage, error_message)
        updated = result.split()[-1] == "1"

        if updated:
            logger.info(f"✓ Updated task {task_id} to {status}")
        else:
            logger.warning(f"Task {task_id} not found")

        return updated

    async def get_task_summary(self, task_id: UUID) -> Optional[TaskSummary]:
        """
        Get task with all stages, helpers, and recent events.

        Args:
            task_id: Task UUID

        Returns:
            TaskSummary with aggregated data, or None if not found
        """
        self._ensure_connected()

        # Get task
        task = await self.get_task(task_id)
        if not task:
            return None

        # Get stages
        stages_query = "SELECT * FROM tac_stages WHERE task_id = $1 ORDER BY started_at;"
        stages_rows = await self.pool.fetch(stages_query, task_id)
        stages = [StageModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in stages_rows]

        # Get helpers
        helpers_query = "SELECT * FROM tac_helper_agents WHERE task_id = $1 ORDER BY started_at;"
        helpers_rows = await self.pool.fetch(helpers_query, task_id)
        helpers = [HelperAgentModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in helpers_rows]

        # Get event count and latest events
        event_count_query = "SELECT COUNT(*) FROM tac_events WHERE task_id = $1;"
        event_count = await self.pool.fetchval(event_count_query, task_id)

        latest_events_query = """
            SELECT * FROM tac_events
            WHERE task_id = $1
            ORDER BY timestamp DESC
            LIMIT 10;
        """
        events_rows = await self.pool.fetch(latest_events_query, task_id)
        latest_events = [EventModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in events_rows]

        return TaskSummary(
            task=task,
            stages=stages,
            helpers=helpers,
            event_count=event_count,
            latest_events=latest_events,
        )

    # ============================================================================
    # Stage Operations
    # ============================================================================

    async def create_stage(self, stage: StageCreate) -> UUID:
        """
        Create new stage.

        Args:
            stage: Stage creation data

        Returns:
            UUID of created stage
        """
        self._ensure_connected()

        logger.info(f"Creating stage {stage.stage_name} for task {stage.task_id}")

        query = """
            INSERT INTO tac_stages (
                task_id, stage_name, provider, model,
                temperature, metadata, status, started_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, 'running', NOW())
            RETURNING id;
        """

        stage_id = await self.pool.fetchval(
            query,
            stage.task_id,
            stage.stage_name,
            stage.provider,
            stage.model,
            stage.temperature,
            json.dumps(stage.metadata) if stage.metadata else None,
        )

        # Update task's current_stage
        await self.pool.execute(
            "UPDATE tac_tasks SET current_stage = $1 WHERE id = $2;",
            stage.stage_name,
            stage.task_id,
        )

        logger.info(f"✓ Created stage {stage_id} ({stage.stage_name})")
        return stage_id

    async def update_stage_completion(
        self,
        stage_id: UUID,
        status: str,
        input_tokens: int,
        output_tokens: int,
        cost: Decimal,
        output_file: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update stage with completion data.

        Args:
            stage_id: Stage UUID
            status: New status (completed, errored)
            input_tokens: Total input tokens used
            output_tokens: Total output tokens used
            cost: Total cost in USD
            output_file: Optional output file path
            error_message: Optional error message

        Returns:
            True if updated, False if not found
        """
        self._ensure_connected()

        logger.info(f"Completing stage {stage_id} with status {status}")

        query = """
            UPDATE tac_stages
            SET status = $2,
                completed_at = NOW(),
                input_tokens = $3,
                output_tokens = $4,
                cost = $5,
                output_file = $6,
                error_message = $7
            WHERE id = $1;
        """

        result = await self.pool.execute(
            query, stage_id, status, input_tokens, output_tokens, cost, output_file, error_message
        )
        updated = result.split()[-1] == "1"

        if updated:
            logger.info(f"✓ Stage {stage_id} completed with cost ${cost}")

        return updated

    async def get_stage_with_events(self, stage_id: UUID) -> Optional[StageWithEvents]:
        """
        Get stage with all its events.

        Args:
            stage_id: Stage UUID

        Returns:
            StageWithEvents or None if not found
        """
        self._ensure_connected()

        # Get stage
        stage_query = "SELECT * FROM tac_stages WHERE id = $1;"
        stage_row = await self.pool.fetchrow(stage_query, stage_id)
        if not stage_row:
            return None

        stage = StageModel.model_validate(self._parse_jsonb_fields(dict(stage_row)))

        # Get events
        events_query = """
            SELECT * FROM tac_events
            WHERE stage_id = $1
            ORDER BY timestamp;
        """
        events_rows = await self.pool.fetch(events_query, stage_id)
        events = [EventModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in events_rows]

        return StageWithEvents(stage=stage, events=events)

    # ============================================================================
    # Helper Agent Operations
    # ============================================================================

    async def create_helper(self, helper: HelperAgentCreate) -> UUID:
        """
        Create new helper agent.

        Args:
            helper: Helper agent creation data

        Returns:
            UUID of created helper
        """
        self._ensure_connected()

        logger.info(f"Creating helper {helper.agent_name} for task {helper.task_id}")

        query = """
            INSERT INTO tac_helper_agents (
                task_id, stage_id, agent_name, agent_template,
                provider, model, metadata, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'running')
            RETURNING id;
        """

        helper_id = await self.pool.fetchval(
            query,
            helper.task_id,
            helper.stage_id,
            helper.agent_name,
            helper.agent_template,
            helper.provider,
            helper.model,
            json.dumps(helper.metadata) if helper.metadata else None,
        )

        logger.info(f"✓ Created helper {helper_id} ({helper.agent_name})")
        return helper_id

    async def update_helper_completion(
        self,
        helper_id: UUID,
        status: str,
        input_tokens: int,
        output_tokens: int,
        cost: Decimal,
        result_summary: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update helper agent with completion data.

        Args:
            helper_id: Helper UUID
            status: New status (completed, errored, interrupted)
            input_tokens: Total input tokens
            output_tokens: Total output tokens
            cost: Total cost in USD
            result_summary: Optional summary of work done
            result_data: Optional structured result data

        Returns:
            True if updated, False if not found
        """
        self._ensure_connected()

        logger.info(f"Completing helper {helper_id} with status {status}")

        query = """
            UPDATE tac_helper_agents
            SET status = $2,
                completed_at = NOW(),
                input_tokens = $3,
                output_tokens = $4,
                cost = $5,
                result_summary = $6,
                result_data = $7
            WHERE id = $1;
        """

        result = await self.pool.execute(
            query, helper_id, status, input_tokens, output_tokens, cost, result_summary,
            json.dumps(result_data) if result_data else None
        )
        updated = result.split()[-1] == "1"

        if updated:
            logger.info(f"✓ Helper {helper_id} completed with cost ${cost}")

        return updated

    async def get_helper_with_events(self, helper_id: UUID) -> Optional[HelperWithEvents]:
        """
        Get helper agent with all its events.

        Args:
            helper_id: Helper UUID

        Returns:
            HelperWithEvents or None if not found
        """
        self._ensure_connected()

        # Get helper
        helper_query = "SELECT * FROM tac_helper_agents WHERE id = $1;"
        helper_row = await self.pool.fetchrow(helper_query, helper_id)
        if not helper_row:
            return None

        helper = HelperAgentModel.model_validate(self._parse_jsonb_fields(dict(helper_row)))

        # Get events
        events_query = """
            SELECT * FROM tac_events
            WHERE helper_agent_id = $1
            ORDER BY timestamp;
        """
        events_rows = await self.pool.fetch(events_query, helper_id)
        events = [EventModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in events_rows]

        return HelperWithEvents(helper=helper, events=events)

    # ============================================================================
    # Event Operations
    # ============================================================================

    async def log_event(self, event: EventCreate) -> UUID:
        """
        Log event to database.

        Args:
            event: Event creation data

        Returns:
            UUID of created event
        """
        self._ensure_connected()

        query = """
            INSERT INTO tac_events (
                task_id, stage_id, helper_agent_id,
                event_category, event_type, content,
                summary, payload
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id;
        """

        event_id = await self.pool.fetchval(
            query,
            event.task_id,
            event.stage_id,
            event.helper_agent_id,
            event.event_category,
            event.event_type,
            event.content,
            event.summary,
            json.dumps(event.payload) if event.payload else None,
        )

        logger.debug(f"Logged event {event.event_type} for task {event.task_id}")
        return event_id

    async def get_task_events(
        self,
        task_id: UUID,
        limit: int = 100,
        event_category: Optional[str] = None,
    ) -> List[EventModel]:
        """
        Get events for task.

        Args:
            task_id: Task UUID
            limit: Maximum number of events to return
            event_category: Optional filter by category

        Returns:
            List of events, newest first
        """
        self._ensure_connected()

        if event_category:
            query = """
                SELECT * FROM tac_events
                WHERE task_id = $1 AND event_category = $2
                ORDER BY timestamp DESC
                LIMIT $3;
            """
            rows = await self.pool.fetch(query, task_id, event_category, limit)
        else:
            query = """
                SELECT * FROM tac_events
                WHERE task_id = $1
                ORDER BY timestamp DESC
                LIMIT $2;
            """
            rows = await self.pool.fetch(query, task_id, limit)

        return [EventModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in rows]

    # ============================================================================
    # Agent Template Operations
    # ============================================================================

    async def get_agent_template(self, name: str) -> Optional[AgentTemplateModel]:
        """
        Get agent template by name.

        Args:
            name: Template name (e.g., 'research-agent')

        Returns:
            AgentTemplateModel if found and active, None otherwise
        """
        self._ensure_connected()

        query = "SELECT * FROM tac_agent_templates WHERE name = $1 AND is_active = true;"
        row = await self.pool.fetchrow(query, name)

        if row:
            return AgentTemplateModel.model_validate(self._parse_jsonb_fields(dict(row)))
        return None

    async def list_agent_templates(self, active_only: bool = True) -> List[AgentTemplateModel]:
        """
        List all agent templates.

        Args:
            active_only: Only return active templates

        Returns:
            List of templates
        """
        self._ensure_connected()

        if active_only:
            query = "SELECT * FROM tac_agent_templates WHERE is_active = true ORDER BY name;"
        else:
            query = "SELECT * FROM tac_agent_templates ORDER BY name;"

        rows = await self.pool.fetch(query)
        return [AgentTemplateModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in rows]

    # ============================================================================
    # Query Operations
    # ============================================================================

    async def get_active_tasks(self) -> List[TaskModel]:
        """
        Get all active (running) tasks.

        Returns:
            List of running tasks
        """
        self._ensure_connected()

        query = "SELECT * FROM tac_tasks WHERE status = 'running' ORDER BY created_at DESC;"
        rows = await self.pool.fetch(query)
        return [TaskModel.model_validate(self._parse_jsonb_fields(dict(row))) for row in rows]

    async def get_task_by_issue(self, issue_number: str) -> Optional[TaskModel]:
        """
        Get task by GitHub issue number.

        Args:
            issue_number: GitHub issue number (e.g., 'gh-123')

        Returns:
            TaskModel if found, None otherwise
        """
        self._ensure_connected()

        query = "SELECT * FROM tac_tasks WHERE issue_number = $1 ORDER BY created_at DESC LIMIT 1;"
        row = await self.pool.fetchrow(query, issue_number)

        if row:
            return TaskModel.model_validate(self._parse_jsonb_fields(dict(row)))
        return None
