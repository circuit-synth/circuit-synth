#!/usr/bin/env python3
"""
Phase 2 Database Module Test Suite

Tests TACDatabase class with async operations against real PostgreSQL container.
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_database import TACDatabase
from adw_modules.tac_models import (
    TaskCreate,
    StageCreate,
    HelperAgentCreate,
    EventCreate,
)


async def test_connection():
    """Test 1: Database connection and pool creation"""
    print("Test 1: Database Connection")
    print("-" * 50)

    db = TACDatabase()
    await db.connect(min_size=2, max_size=5)

    assert db.pool is not None, "Pool should be created"
    print("✓ Connection pool created")

    await db.close()
    assert db.pool is None, "Pool should be None after close"
    print("✓ Connection pool closed")
    print()


async def test_task_crud():
    """Test 2: Task CRUD operations"""
    print("Test 2: Task CRUD Operations")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    # Create task
    task_create = TaskCreate(
        issue_number="TEST-PHASE2-001",
        workflow_config={"name": "test-workflow", "version": "1.0"},
        metadata={"test": True},
    )

    task_id = await db.create_task(task_create)
    print(f"✓ Created task: {task_id}")
    assert isinstance(task_id, UUID), "Should return UUID"

    # Get task
    task = await db.get_task(task_id)
    assert task is not None, "Task should exist"
    assert task.issue_number == "TEST-PHASE2-001", "Issue number should match"
    assert task.status == "running", "Status should be running"
    print(f"✓ Retrieved task: {task.issue_number}")

    # Update task status
    updated = await db.update_task_status(task_id, "completed", current_stage="pr_creation")
    assert updated, "Update should succeed"
    print("✓ Updated task status to completed")

    # Verify update
    task = await db.get_task(task_id)
    assert task.status == "completed", "Status should be updated"
    assert task.current_stage == "pr_creation", "Stage should be updated"
    assert task.completed_at is not None, "Completed_at should be set"
    print("✓ Verified task update")

    # Get by issue number
    task_by_issue = await db.get_task_by_issue("TEST-PHASE2-001")
    assert task_by_issue is not None, "Should find by issue"
    assert task_by_issue.id == task_id, "Should be same task"
    print("✓ Retrieved task by issue number")

    await db.close()
    print()


async def test_stage_operations():
    """Test 3: Stage operations"""
    print("Test 3: Stage Operations")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    # Create task first
    task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE2-002"))
    print(f"✓ Created task: {task_id}")

    # Create stage
    stage_create = StageCreate(
        task_id=task_id,
        stage_name="planning",
        provider="openrouter",
        model="google/gemini-2.5-flash",
        temperature=Decimal("0.7"),
    )

    stage_id = await db.create_stage(stage_create)
    print(f"✓ Created stage: {stage_id}")
    assert isinstance(stage_id, UUID), "Should return UUID"

    # Verify task's current_stage was updated
    task = await db.get_task(task_id)
    assert task.current_stage == "planning", "Task current_stage should update"
    print("✓ Task current_stage updated to 'planning'")

    # Complete stage
    updated = await db.update_stage_completion(
        stage_id,
        status="completed",
        input_tokens=1500,
        output_tokens=800,
        cost=Decimal("0.025"),
        output_file="/tmp/plan.md",
    )
    assert updated, "Stage update should succeed"
    print("✓ Stage completed with cost $0.025")

    # Verify cost rollup trigger (should happen automatically)
    task = await db.get_task(task_id)
    assert task.total_cost == Decimal("0.025"), f"Cost should rollup (got {task.total_cost})"
    assert task.total_input_tokens == 1500, "Input tokens should rollup"
    assert task.total_output_tokens == 800, "Output tokens should rollup"
    print("✓ Cost rollup trigger working")

    # Get stage with events
    stage_with_events = await db.get_stage_with_events(stage_id)
    assert stage_with_events is not None, "Should retrieve stage"
    assert stage_with_events.stage.id == stage_id, "Stage ID should match"
    print("✓ Retrieved stage with events")

    await db.close()
    print()


async def test_helper_operations():
    """Test 4: Helper agent operations"""
    print("Test 4: Helper Agent Operations")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    # Create task and stage
    task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE2-003"))
    stage_id = await db.create_stage(
        StageCreate(task_id=task_id, stage_name="building")
    )
    print(f"✓ Created task and stage")

    # Create helper
    helper_create = HelperAgentCreate(
        task_id=task_id,
        stage_id=stage_id,
        agent_name="research-agent-abc123",
        agent_template="research-agent",
        provider="openrouter",
        model="claude-haiku",
    )

    helper_id = await db.create_helper(helper_create)
    print(f"✓ Created helper: {helper_id}")

    # Complete helper
    updated = await db.update_helper_completion(
        helper_id,
        status="completed",
        input_tokens=500,
        output_tokens=200,
        cost=Decimal("0.008"),
        result_summary="Researched codebase and found 3 relevant files",
        result_data={"files": ["file1.py", "file2.py", "file3.py"]},
    )
    assert updated, "Helper update should succeed"
    print("✓ Helper completed with cost $0.008")

    # Verify cost rollup includes helper cost
    task = await db.get_task(task_id)
    # Task should have no stage costs yet, only helper cost
    assert task.total_cost == Decimal("0.008"), f"Cost should include helper (got {task.total_cost})"
    print("✓ Helper cost added to task total")

    # Get helper with events
    helper_with_events = await db.get_helper_with_events(helper_id)
    assert helper_with_events is not None, "Should retrieve helper"
    assert helper_with_events.helper.id == helper_id, "Helper ID should match"
    assert helper_with_events.helper.result_summary is not None, "Should have summary"
    print("✓ Retrieved helper with events")

    await db.close()
    print()


async def test_event_logging():
    """Test 5: Event logging"""
    print("Test 5: Event Logging")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    # Create task and stage
    task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE2-004"))
    stage_id = await db.create_stage(
        StageCreate(task_id=task_id, stage_name="planning")
    )
    print("✓ Created task and stage")

    # Log various events
    event1_id = await db.log_event(
        EventCreate(
            task_id=task_id,
            stage_id=stage_id,
            event_category="stage",
            event_type="Info",
            content="Planning stage started",
            summary="Planning initiated",
        )
    )
    print(f"✓ Logged event 1: {event1_id}")

    event2_id = await db.log_event(
        EventCreate(
            task_id=task_id,
            stage_id=stage_id,
            event_category="hook",
            event_type="PreToolUse",
            content="About to use Read tool",
            summary="Reading files",
            payload={"tool": "Read", "args": {"file_path": "/test.py"}},
        )
    )
    print(f"✓ Logged event 2: {event2_id}")

    event3_id = await db.log_event(
        EventCreate(
            task_id=task_id,
            event_category="system",
            event_type="Info",
            content="Task processing started",
        )
    )
    print(f"✓ Logged event 3: {event3_id}")

    # Get all events
    events = await db.get_task_events(task_id, limit=10)
    assert len(events) == 3, f"Should have 3 events (got {len(events)})"
    print(f"✓ Retrieved {len(events)} events")

    # Get filtered events
    hook_events = await db.get_task_events(task_id, event_category="hook")
    assert len(hook_events) == 1, "Should have 1 hook event"
    assert hook_events[0].event_type == "PreToolUse", "Should be PreToolUse"
    print("✓ Filtered events by category")

    await db.close()
    print()


async def test_task_summary():
    """Test 6: Task summary with aggregated data"""
    print("Test 6: Task Summary")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    # Create task
    task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE2-005"))
    print("✓ Created task")

    # Create 2 stages
    stage1_id = await db.create_stage(
        StageCreate(task_id=task_id, stage_name="planning")
    )
    await db.update_stage_completion(
        stage1_id, "completed", 1000, 500, Decimal("0.015")
    )

    stage2_id = await db.create_stage(
        StageCreate(task_id=task_id, stage_name="building")
    )
    await db.update_stage_completion(
        stage2_id, "completed", 2000, 1000, Decimal("0.030")
    )
    print("✓ Created 2 stages")

    # Create 1 helper
    helper_id = await db.create_helper(
        HelperAgentCreate(
            task_id=task_id,
            stage_id=stage1_id,
            agent_name="test-agent-xyz",
            agent_template="test-agent",
        )
    )
    await db.update_helper_completion(
        helper_id, "completed", 300, 150, Decimal("0.005")
    )
    print("✓ Created 1 helper")

    # Log some events
    await db.log_event(
        EventCreate(
            task_id=task_id,
            stage_id=stage1_id,
            event_category="stage",
            event_type="Info",
            content="Stage started",
        )
    )
    await db.log_event(
        EventCreate(
            task_id=task_id,
            event_category="system",
            event_type="Info",
            content="Task started",
        )
    )
    print("✓ Logged 2 events")

    # Get task summary
    summary = await db.get_task_summary(task_id)
    assert summary is not None, "Summary should exist"
    assert len(summary.stages) == 2, "Should have 2 stages"
    assert len(summary.helpers) == 1, "Should have 1 helper"
    assert summary.event_count == 2, "Should have 2 events"
    assert len(summary.latest_events) == 2, "Should have 2 latest events"

    # Verify total costs
    expected_total = Decimal("0.015") + Decimal("0.030") + Decimal("0.005")
    assert summary.task.total_cost == expected_total, f"Total cost should be {expected_total}"
    print(f"✓ Task summary complete (cost: ${summary.task.total_cost})")

    await db.close()
    print()


async def test_active_tasks():
    """Test 7: Get active tasks"""
    print("Test 7: Active Tasks Query")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    # Create some tasks
    task1_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE2-006"))
    task2_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE2-007"))
    task3_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE2-008"))

    # Complete one
    await db.update_task_status(task2_id, "completed")
    print("✓ Created 3 tasks (1 completed, 2 running)")

    # Get active tasks
    active_tasks = await db.get_active_tasks()
    active_issue_numbers = {t.issue_number for t in active_tasks}

    assert "TEST-PHASE2-006" in active_issue_numbers, "Task 006 should be active"
    assert "TEST-PHASE2-007" not in active_issue_numbers, "Task 007 should not be active"
    assert "TEST-PHASE2-008" in active_issue_numbers, "Task 008 should be active"
    print(f"✓ Found {len([t for t in active_tasks if t.issue_number.startswith('TEST-PHASE2')])} active test tasks")

    await db.close()
    print()


async def test_cleanup():
    """Test 8: Cleanup test data"""
    print("Test 8: Cleanup")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    # Delete all test tasks
    delete_query = "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE2-%';"
    await db.pool.execute(delete_query)

    # Verify cleanup
    count_query = "SELECT COUNT(*) FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE2-%';"
    remaining = await db.pool.fetchval(count_query)

    assert remaining == 0, f"Should have no test tasks remaining (got {remaining})"
    print("✓ All test data cleaned up")

    await db.close()
    print()


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Phase 2 Database Module Test Suite")
    print("=" * 50)
    print()

    try:
        await test_connection()
        await test_task_crud()
        await test_stage_operations()
        await test_helper_operations()
        await test_event_logging()
        await test_task_summary()
        await test_active_tasks()
        await test_cleanup()

        print("=" * 50)
        print("✓ All Phase 2 Tests Passed!")
        print("=" * 50)
        print()
        print("Database Module Status:")
        print("  TACDatabase class: Working")
        print("  Connection pooling: Working")
        print("  Task CRUD: Working")
        print("  Stage CRUD: Working")
        print("  Helper CRUD: Working")
        print("  Event logging: Working")
        print("  Cost rollup triggers: Working")
        print("  Aggregated queries: Working")
        print()
        print("Ready for Phase 3: Agent template system")
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
