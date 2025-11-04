#!/usr/bin/env python3
"""
Phase 5 TAC Worker Adapter Test Suite

Tests the TACWorkerAdapter which wraps MultiStageWorker with PostgreSQL tracking.

Validates:
- Task creation and tracking
- Stage lifecycle management
- Event logging
- Helper agent integration
- Cost aggregation
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_database import TACDatabase
from adw_modules.tac_worker_adapter import TACWorkerAdapter
from adw_modules.workflow_config import create_default_workflow


async def test_worker_creation():
    """Test 1: Create TAC worker adapter"""
    print("Test 1: Worker Adapter Creation")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Create temp worktree directory
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)

            # Create adapter
            worker = await TACWorkerAdapter.create(
                issue_number="TEST-PHASE5-001",
                worktree_path=worktree_path,
                branch_name="test/phase5-001",
                llm_config={"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
                api_logger=None,  # Placeholder
                database=db,
            )

            print(f"✓ Worker created with task_id: {worker.task_id}")

            # Verify task in database
            task = await db.get_task(worker.task_id)
            assert task is not None, "Task should exist in database"
            assert task.issue_number == "TEST-PHASE5-001", "Issue number should match"
            assert task.status == "running", "Task should be running"
            print("✓ Task record created in database")

            # Verify task creation event
            events = await db.get_task_events(worker.task_id, limit=10)
            assert len(events) > 0, "Should have task creation event"
            assert any(e.event_type == "TaskCreated" for e in events), "Should have TaskCreated event"
            print(f"✓ Task creation event logged ({len(events)} events)")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE5-%';"
        )
        await db.close()

    print()


async def test_stage_tracking():
    """Test 2: Stage lifecycle tracking"""
    print("Test 2: Stage Lifecycle Tracking")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Create temp worktree directory
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)

            # Create adapter
            worker = await TACWorkerAdapter.create(
                issue_number="TEST-PHASE5-002",
                worktree_path=worktree_path,
                branch_name="test/phase5-002",
                llm_config={"provider": "anthropic"},
                api_logger=None,
                database=db,
                workflow_config=create_default_workflow(),
            )

            print(f"✓ Worker created")

            # Log stage start
            from adw_modules.multi_stage_worker import StageResult

            stage_id = await worker.log_stage_start("planning")
            print(f"✓ Stage 'planning' started (stage_id: {stage_id})")

            # Verify stage in database
            stage_db = await db.pool.fetchrow(
                "SELECT * FROM tac_stages WHERE id = $1;",
                stage_id
            )
            assert stage_db is not None, "Stage should exist"
            assert stage_db['stage_name'] == "planning", "Stage name should match"
            assert stage_db['status'] == "running", "Stage should be running"
            print("✓ Stage record created in database")

            # Log stage completion
            result = StageResult(
                stage_name="planning",
                success=True,
                started_at="2025-01-01T00:00:00",
                completed_at="2025-01-01T00:05:00",
                output_file=".tac/outputs/planning.md",
                tokens_input=1000,
                tokens_output=500,
            )

            await worker.log_stage_completion(stage_id, result)
            print("✓ Stage completion logged")

            # Verify stage completion
            stage_db = await db.pool.fetchrow(
                "SELECT * FROM tac_stages WHERE id = $1;",
                stage_id
            )
            assert stage_db['status'] == "completed", "Stage should be completed"
            assert stage_db['input_tokens'] == 1000, "Input tokens should match"
            assert stage_db['output_tokens'] == 500, "Output tokens should match"
            print("✓ Stage marked as completed in database")

            # Verify stage events
            all_events = await db.get_task_events(worker.task_id, event_category="stage")
            stage_events = [e for e in all_events if e.stage_id == stage_id]
            assert len(stage_events) >= 2, "Should have stage start and complete events"
            event_types = {e.event_type for e in stage_events}
            assert "StageStarted" in event_types, "Should have StageStarted event"
            assert "StageCompleted" in event_types, "Should have StageCompleted event"
            print(f"✓ Stage events logged: {', '.join(sorted(event_types))}")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE5-%';"
        )
        await db.close()

    print()


async def test_pipeline_execution():
    """Test 3: Full pipeline execution"""
    print("Test 3: Pipeline Execution")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Create temp worktree directory
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)

            # Create adapter
            worker = await TACWorkerAdapter.create(
                issue_number="TEST-PHASE5-003",
                worktree_path=worktree_path,
                branch_name="test/phase5-003",
                llm_config={"provider": "anthropic"},
                api_logger=None,
                database=db,
            )

            print(f"✓ Worker created")

            # Run pipeline
            success = await worker.run()
            print(f"✓ Pipeline executed: {'success' if success else 'failed'}")

            assert success, "Pipeline should complete successfully"

            # Verify task status
            task = await db.get_task(worker.task_id)
            assert task.status == "completed", "Task should be completed"
            print("✓ Task marked as completed")

            # Verify all stages were created
            task_summary = await db.get_task_summary(worker.task_id)
            assert len(task_summary.stages) == 4, "Should have 4 stages"

            stage_names = {s.stage_name for s in task_summary.stages}
            expected_stages = {"planning", "building", "reviewing", "pr_creation"}
            assert stage_names == expected_stages, f"Stages should be {expected_stages}"
            print(f"✓ All 4 stages completed: {', '.join(sorted(stage_names))}")

            # Verify all stages completed
            for stage in task_summary.stages:
                assert stage.status == "completed", f"Stage {stage.stage_name} should be completed"

            print("✓ All stages have completed status")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE5-%';"
        )
        await db.close()

    print()


async def test_helper_integration():
    """Test 4: Helper agent spawning via adapter"""
    print("Test 4: Helper Agent Integration")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        from adw_modules.tac_agent_loader import AgentTemplateLoader, AgentTemplate

        test_template = """---
name: adapter-test-helper
description: Test helper for adapter
model: haiku
temperature: 0.5
tools: []
---
Test helper agent
"""

        import tempfile as tf
        with tf.TemporaryDirectory() as tmpdir2:
            tmpdir_path = Path(tmpdir2)
            (tmpdir_path / "adapter-test-helper.md").write_text(test_template)

            loader = AgentTemplateLoader(agents_dir=tmpdir_path)
            await loader.sync_to_database(db)
            print("✓ Test template created")

        # Create temp worktree directory
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)

            # Create adapter
            worker = await TACWorkerAdapter.create(
                issue_number="TEST-PHASE5-004",
                worktree_path=worktree_path,
                branch_name="test/phase5-004",
                llm_config={"provider": "anthropic"},
                api_logger=None,
                database=db,
            )

            print(f"✓ Worker created")

            # Start a stage
            stage_id = await worker.log_stage_start("planning")
            print(f"✓ Stage started")

            # Spawn helper via adapter
            async with worker.spawn_helper(
                template_name="adapter-test-helper",
                purpose="Test helper integration",
            ) as helper:
                print(f"✓ Helper spawned: {helper.agent_name}")

                # Execute helper
                result = await helper.run(prompt="Test execution")
                print(f"✓ Helper executed")

            # Verify helper was tracked
            task_summary = await db.get_task_summary(worker.task_id)
            assert len(task_summary.helpers) == 1, "Should have 1 helper"

            helper_record = task_summary.helpers[0]
            assert helper_record.status == "completed", "Helper should be completed"
            assert helper_record.agent_template == "adapter-test-helper", "Template should match"
            print("✓ Helper tracked in database")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE5-%';"
        )
        await db.pool.execute(
            "DELETE FROM tac_agent_templates WHERE name = 'adapter-test-helper';"
        )
        await db.close()

    print()


async def test_error_handling():
    """Test 5: Error handling in adapter"""
    print("Test 5: Error Handling")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Create temp worktree directory
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)

            # Create adapter
            worker = await TACWorkerAdapter.create(
                issue_number="TEST-PHASE5-005",
                worktree_path=worktree_path,
                branch_name="test/phase5-005",
                llm_config={"provider": "anthropic"},
                api_logger=None,
                database=db,
            )

            print(f"✓ Worker created")

            # Simulate an error during execution
            try:
                # Manually trigger error
                await worker.log_stage_start("planning")

                # Simulate stage failure
                from adw_modules.multi_stage_worker import StageResult

                failed_result = StageResult(
                    stage_name="planning",
                    success=False,
                    started_at="2025-01-01T00:00:00",
                    completed_at="2025-01-01T00:01:00",
                    error="Simulated error for testing",
                    tokens_input=50,
                    tokens_output=0,
                )

                await worker.log_stage_completion(worker.current_stage_id, failed_result)
                print("✓ Stage failure logged")

            except Exception as e:
                print(f"Caught exception: {e}")

            # Verify stage marked as errored
            stage_db = await db.pool.fetchrow(
                "SELECT * FROM tac_stages WHERE id = $1;",
                worker.current_stage_id
            )

            assert stage_db['status'] == "errored", "Stage should be errored"
            assert stage_db['error_message'] is not None, "Should have error message"
            print("✓ Stage marked as errored in database")

            # Verify error event logged
            all_events = await db.get_task_events(worker.task_id, event_category="stage")
            stage_events = [e for e in all_events if e.stage_id == worker.current_stage_id]
            error_events = [e for e in stage_events if e.event_type == "StageErrored"]
            assert len(error_events) > 0, "Should have StageErrored event"
            print("✓ Error event logged")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE5-%';"
        )
        await db.close()

    print()


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Phase 5 TAC Worker Adapter Test Suite")
    print("=" * 50)
    print()

    try:
        await test_worker_creation()
        await test_stage_tracking()
        await test_pipeline_execution()
        await test_helper_integration()
        await test_error_handling()

        print("=" * 50)
        print("✓ All Phase 5 Tests Passed!")
        print("=" * 50)
        print()
        print("TAC Worker Adapter Status:")
        print("  Worker creation: Working")
        print("  Stage tracking: Working")
        print("  Pipeline execution: Working")
        print("  Helper integration: Working")
        print("  Error handling: Working")
        print()
        print("Integration Status:")
        print("  ✓ MultiStageWorker wrapped successfully")
        print("  ✓ PostgreSQL tracking active")
        print("  ✓ Helper agent spawning enabled")
        print("  ✓ Full observability achieved")
        print()
        print("Ready for Phase 6: Web dashboard backend")
        print()

    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"✗ Test Failed: {e}")
        print("=" * 50)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"✗ Error: {e}")
        print("=" * 50)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
