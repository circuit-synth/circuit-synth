#!/usr/bin/env python3
"""
TAC Worker Adapter

Wraps the existing MultiStageWorker to add PostgreSQL tracking and helper agent
spawning capabilities from the Hybrid TAC Architecture.

This adapter provides:
- Database tracking of tasks, stages, and events
- Helper agent spawning during stage execution
- Cost and token aggregation to PostgreSQL
- Full observability without modifying core MultiStageWorker

Usage:
------
```python
from adw_modules.tac_worker_adapter import TACWorkerAdapter
from adw_modules.tac_database import TACDatabase

# Connect to database
db = TACDatabase()
await db.connect()

# Create adapted worker
worker = await TACWorkerAdapter.create(
    issue_number="gh-123",
    worktree_path="/path/to/worktree",
    branch_name="fix/issue-123",
    llm_config={...},
    api_logger=logger,
    database=db,
)

# Execute pipeline with full tracking
await worker.run()

# Database now contains complete execution history
task_summary = await db.get_task_summary(worker.task_id)
```
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from uuid import UUID
from decimal import Decimal

from .multi_stage_worker import MultiStageWorker, StageResult
from .tac_database import TACDatabase
from .tac_models import TaskCreate, StageCreate, EventCreate
from .tac_helper_manager import HelperAgentManager
from .workflow_config import WorkflowConfig

logger = logging.getLogger(__name__)


class TACWorkerAdapter:
    """
    Adapter that wraps MultiStageWorker with PostgreSQL tracking.

    Provides hybrid TAC architecture capabilities:
    - Fixed 4-stage pipeline (via MultiStageWorker)
    - Dynamic helper agent spawning
    - Full database observability
    - Cost and token aggregation
    """

    def __init__(
        self,
        worker: MultiStageWorker,
        database: TACDatabase,
        task_id: UUID,
        workflow_config: Optional[WorkflowConfig] = None,
    ):
        """
        Initialize TAC worker adapter.

        Args:
            worker: Underlying MultiStageWorker instance
            database: Connected TACDatabase instance
            task_id: UUID of task in database
            workflow_config: Optional workflow configuration
        """
        self.worker = worker
        self.db = database
        self.task_id = task_id
        self.workflow_config = workflow_config

        # Helper agent manager
        self.helper_manager = HelperAgentManager(database)

        # Stage tracking
        self.current_stage_id: Optional[UUID] = None

        logger.info(
            f"TACWorkerAdapter initialized for task {task_id} "
            f"(issue: {worker.issue_number})"
        )

    @classmethod
    async def create(
        cls,
        issue_number: str,
        worktree_path: Path,
        branch_name: str,
        llm_config: Dict[str, Any],
        api_logger,
        database: TACDatabase,
        workflow_config: Optional[WorkflowConfig] = None,
        task_metadata: Optional[Dict[str, Any]] = None,
        full_config: Optional[Dict] = None,
    ) -> "TACWorkerAdapter":
        """
        Create a new TAC worker adapter with database tracking.

        This factory method:
        1. Creates task record in database
        2. Initializes MultiStageWorker
        3. Returns wrapped adapter

        Args:
            issue_number: GitHub issue number (e.g., "gh-123")
            worktree_path: Path to git worktree
            branch_name: Git branch name
            llm_config: LLM configuration dict
            api_logger: API logger instance
            database: Connected TACDatabase
            workflow_config: Optional workflow configuration
            task_metadata: Optional metadata dict

        Returns:
            TACWorkerAdapter instance ready to run
        """
        # Create task in database
        task_create = TaskCreate(
            issue_number=issue_number,
            worktree_path=str(worktree_path),
            branch_name=branch_name,
            workflow_config={"stages": [s.__dict__ for s in workflow_config.stages]} if workflow_config else None,
            metadata=task_metadata or {},
        )

        task_id = await database.create_task(task_create)

        logger.info(
            f"Created task {task_id} for issue {issue_number}"
        )

        # Log task creation event
        await database.log_event(
            EventCreate(
                task_id=task_id,
                event_category="system",
                event_type="TaskCreated",
                summary=f"Task created for {issue_number}",
                content=f"Branch: {branch_name}, Worktree: {worktree_path}",
            )
        )

        # Create underlying MultiStageWorker
        # Use a placeholder task_id string for the worker
        worker = MultiStageWorker(
            task_id=str(task_id),
            issue_number=issue_number,
            worktree_path=worktree_path,
            branch_name=branch_name,
            llm_config=llm_config,
            api_logger=api_logger,
            workflow_config=workflow_config,
            full_config=full_config or {},
        )

        # Return adapter
        return cls(
            worker=worker,
            database=database,
            task_id=task_id,
            workflow_config=workflow_config,
        )

    async def log_stage_start(self, stage_name: str) -> UUID:
        """
        Log the start of a pipeline stage.

        Args:
            stage_name: Name of stage (planning, building, reviewing, pr_creation)

        Returns:
            UUID of created stage record
        """
        # Get stage configuration from workflow
        stage_config = None
        if self.workflow_config:
            for stage in self.workflow_config.stages:
                if stage.name == stage_name:
                    stage_config = stage
                    break

        # Create stage in database
        stage_create = StageCreate(
            task_id=self.task_id,
            stage_name=stage_name,
            provider=stage_config.provider if stage_config else None,
            model=stage_config.model if stage_config else None,
            temperature=Decimal(str(stage_config.temperature)) if stage_config else None,
        )

        stage_id = await self.db.create_stage(stage_create)
        self.current_stage_id = stage_id

        logger.info(f"Started stage {stage_name} (stage_id: {stage_id})")

        # Log event
        await self.db.log_event(
            EventCreate(
                task_id=self.task_id,
                stage_id=stage_id,
                event_category="stage",
                event_type="StageStarted",
                summary=f"Stage '{stage_name}' started",
            )
        )

        return stage_id

    async def log_stage_completion(
        self,
        stage_id: UUID,
        result: StageResult,
    ):
        """
        Log the completion of a pipeline stage.

        Args:
            stage_id: UUID of stage
            result: StageResult from MultiStageWorker
        """
        status = "completed" if result.success else "errored"

        await self.db.update_stage_completion(
            stage_id=stage_id,
            status=status,
            input_tokens=result.tokens_input,
            output_tokens=result.tokens_output,
            cost=Decimal("0"),  # TODO: Calculate cost from tokens
            output_file=result.output_file,
            error_message=result.error,
        )

        logger.info(
            f"Completed stage {result.stage_name}: {status} "
            f"(tokens: {result.tokens_input}→{result.tokens_output})"
        )

        # Log event
        await self.db.log_event(
            EventCreate(
                task_id=self.task_id,
                stage_id=stage_id,
                event_category="stage",
                event_type="StageCompleted" if result.success else "StageErrored",
                summary=f"Stage '{result.stage_name}' {status}",
                content=result.error if not result.success else None,
                payload={
                    "tokens_input": result.tokens_input,
                    "tokens_output": result.tokens_output,
                    "output_file": result.output_file,
                },
            )
        )

    async def run(self) -> bool:
        """
        Execute the multi-stage pipeline with full database tracking.

        This wraps MultiStageWorker.run() and adds:
        - Stage tracking in database
        - Event logging
        - Task status updates

        Returns:
            True if pipeline completed successfully, False otherwise
        """
        try:
            # Update task status
            await self.db.update_task_status(
                self.task_id,
                status="running",
            )

            logger.info(
                f"Starting pipeline for task {self.task_id} "
                f"(issue: {self.worker.issue_number})"
            )

            # Get stages from workflow
            stages = ["planning", "building", "reviewing", "pr_creation"]

            # Execute the full pipeline via MultiStageWorker
            logger.info("Executing MultiStageWorker pipeline...")

            # Run the multi-stage worker (this is synchronous)
            import asyncio
            loop = asyncio.get_event_loop()
            pipeline_state = await loop.run_in_executor(None, self.worker.run)

            logger.info(f"Pipeline completed with status: {pipeline_state.status}")

            # Log each stage result to database
            for stage_name in stages:
                # Log stage start
                stage_id = await self.log_stage_start(stage_name)

                # Get the stage result from pipeline_state.stage_results dict
                if stage_name in pipeline_state.stage_results:
                    result = pipeline_state.stage_results[stage_name]
                else:
                    # Fallback for missing results
                    result = StageResult(
                        stage_name=stage_name,
                        success=False,
                        started_at="",
                        completed_at="",
                        output_file="",
                        tokens_input=0,
                        tokens_output=0,
                        error="Stage result not found in pipeline state",
                    )

                # Log stage completion
                await self.log_stage_completion(stage_id, result)

                # Break if stage failed
                if not result.success:
                    logger.error(f"Stage {stage_name} failed: {result.error}")
                    await self.db.update_task_status(
                        self.task_id,
                        status="errored",
                    )
                    return False

            # All stages completed successfully
            await self.db.update_task_status(
                self.task_id,
                status="completed",
            )

            logger.info(f"Pipeline completed successfully for task {self.task_id}")

            return True

        except Exception as e:
            logger.error(f"Pipeline failed for task {self.task_id}: {e}", exc_info=True)

            # Update task as errored
            await self.db.update_task_status(
                self.task_id,
                status="errored",
            )

            # Log error event
            await self.db.log_event(
                EventCreate(
                    task_id=self.task_id,
                    event_category="system",
                    event_type="PipelineErrored",
                    summary="Pipeline execution failed",
                    content=str(e),
                )
            )

            raise

    async def get_task_summary(self):
        """Get full task summary from database"""
        return await self.db.get_task_summary(self.task_id)

    def spawn_helper(
        self,
        template_name: str,
        purpose: str,
        **kwargs
    ):
        """
        Spawn a helper agent during stage execution.

        This is a convenience method that delegates to HelperAgentManager.

        Args:
            template_name: Name of agent template
            purpose: Human-readable purpose
            **kwargs: Additional arguments for spawn_helper

        Returns:
            Async context manager from helper_manager.spawn_helper()
        """
        return self.helper_manager.spawn_helper(
            task_id=self.task_id,
            stage_id=self.current_stage_id,
            template_name=template_name,
            purpose=purpose,
            **kwargs
        )
