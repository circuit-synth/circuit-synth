#!/usr/bin/env python3
"""
Phase 4 Helper Agent Spawn Mechanism Test Suite

Tests the HelperAgentManager module including:
- Helper agent spawning from templates
- Lifecycle management with context managers
- Event logging and database tracking
- Cost aggregation to parent tasks
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_database import TACDatabase
from adw_modules.tac_models import TaskCreate, StageCreate, EventCreate
from adw_modules.tac_helper_manager import HelperAgentManager
from adw_modules.tac_agent_loader import AgentTemplateLoader, AgentTemplate


# Test template for helper spawn tests
TEST_HELPER_TEMPLATE = """---
name: test-helper
description: Test helper for spawn mechanism validation
model: haiku
temperature: 0.5
tools:
  - Read
  - Bash
color: green
---

# Test Helper Agent

You are a test helper agent used for validating the spawn mechanism.
"""


async def setup_test_template(db: TACDatabase):
    """Create a test template in the database"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Write test template
        (tmpdir_path / "test-helper.md").write_text(TEST_HELPER_TEMPLATE)

        # Load and sync to database
        loader = AgentTemplateLoader(agents_dir=tmpdir_path)
        await loader.sync_to_database(db)

        print("✓ Test template created in database")


async def test_helper_spawn_basic():
    """Test 1: Basic helper agent spawning"""
    print("Test 1: Basic Helper Spawn")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE4-001"))
        stage_id = await db.create_stage(
            StageCreate(task_id=task_id, stage_name="building")
        )
        print(f"✓ Created task and stage")

        # Create helper manager
        manager = HelperAgentManager(db)
        print("✓ HelperAgentManager created")

        # Spawn a helper agent
        async with manager.spawn_helper(
            task_id=task_id,
            stage_id=stage_id,
            template_name="test-helper",
            purpose="Test basic spawn functionality",
        ) as helper:
            print(f"✓ Spawned helper: {helper.agent_name}")

            # Verify helper attributes
            assert helper.task_id == task_id, "Task ID should match"
            assert helper.stage_id == stage_id, "Stage ID should match"
            assert helper.agent_template == "test-helper", "Template should match"
            assert helper.agent_name.startswith("test-helper-"), "Name should have prefix"
            print("✓ Helper attributes verified")

            # Verify helper exists in database
            helper_db = await db.get_helper_with_events(helper.helper_id)
            assert helper_db is not None, "Helper should exist in database"
            assert helper_db.helper.status == "running", "Helper should be running"
            print("✓ Helper found in database")

        # After context exit, helper should be completed
        helper_db = await db.get_helper_with_events(helper.helper_id)
        assert helper_db.helper.status == "completed", "Helper should be completed"
        assert helper_db.helper.completed_at is not None, "Should have completion time"
        print("✓ Helper marked as completed after context exit")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE4-%';"
        )
        await db.pool.execute("DELETE FROM tac_agent_templates WHERE name = 'test-helper';")
        await db.close()

    print()


async def test_helper_execution():
    """Test 2: Helper agent execution with token tracking"""
    print("Test 2: Helper Execution & Token Tracking")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE4-002"))
        stage_id = await db.create_stage(
            StageCreate(task_id=task_id, stage_name="planning")
        )
        print("✓ Created task and stage")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Spawn and execute helper
        async with manager.spawn_helper(
            task_id=task_id,
            stage_id=stage_id,
            template_name="test-helper",
            purpose="Test execution with token tracking",
        ) as helper:
            print(f"✓ Spawned helper: {helper.agent_name}")

            # Execute helper (placeholder implementation)
            result = await helper.run(prompt="Test execution")

            assert result is not None, "Should return result"
            print(f"✓ Helper executed with result: {result['status']}")

            # Verify token usage was tracked
            assert helper.input_tokens > 0, "Should have input tokens"
            assert helper.output_tokens > 0, "Should have output tokens"
            assert helper.cost > Decimal("0"), "Should have cost"
            print(f"✓ Token usage tracked: {helper.input_tokens} in, {helper.output_tokens} out")
            print(f"✓ Cost tracked: ${helper.cost}")

        # Verify cost rolled up to task
        task = await db.get_task(task_id)
        assert task.total_cost >= helper.cost, "Cost should roll up to task"
        print(f"✓ Cost rolled up to task: ${task.total_cost}")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE4-%';"
        )
        await db.pool.execute("DELETE FROM tac_agent_templates WHERE name = 'test-helper';")
        await db.close()

    print()


async def test_helper_result_tracking():
    """Test 3: Helper result tracking"""
    print("Test 3: Helper Result Tracking")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE4-003"))
        stage_id = await db.create_stage(
            StageCreate(task_id=task_id, stage_name="reviewing")
        )
        print("✓ Created task and stage")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Spawn helper and set result
        async with manager.spawn_helper(
            task_id=task_id,
            stage_id=stage_id,
            template_name="test-helper",
            purpose="Test result tracking",
        ) as helper:
            # Set custom result
            await helper.set_result(
                summary="Found 5 test files",
                data={
                    "files": ["test1.py", "test2.py", "test3.py", "test4.py", "test5.py"],
                    "total": 5,
                },
            )
            print("✓ Result set on helper")

        # Verify result was saved
        helper_db = await db.get_helper_with_events(helper.helper_id)
        assert helper_db.helper.result_summary == "Found 5 test files", "Summary should match"
        assert helper_db.helper.result_data is not None, "Should have result data"
        assert helper_db.helper.result_data["total"] == 5, "Data should match"
        print("✓ Result saved to database")
        print(f"  Summary: {helper_db.helper.result_summary}")
        print(f"  Data: {helper_db.helper.result_data}")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE4-%';"
        )
        await db.pool.execute("DELETE FROM tac_agent_templates WHERE name = 'test-helper';")
        await db.close()

    print()


async def test_helper_event_logging():
    """Test 4: Helper event logging"""
    print("Test 4: Helper Event Logging")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE4-004"))
        stage_id = await db.create_stage(
            StageCreate(task_id=task_id, stage_name="building")
        )
        print("✓ Created task and stage")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Spawn helper and log events
        async with manager.spawn_helper(
            task_id=task_id,
            stage_id=stage_id,
            template_name="test-helper",
            purpose="Test event logging",
        ) as helper:
            # Log custom event
            await helper.log_event(
                event_type="CustomEvent",
                summary="Testing custom event",
                content="This is a test event",
                payload={"test": True},
            )
            print("✓ Custom event logged")

            # Execute to generate more events
            await helper.run(prompt="Generate events")
            print("✓ Execution events generated")

        # Verify events were logged
        helper_db = await db.get_helper_with_events(helper.helper_id)
        assert len(helper_db.events) > 0, "Should have events"

        # Find specific event types
        event_types = {e.event_type for e in helper_db.events}
        assert "HelperSpawned" in event_types, "Should have HelperSpawned event"
        assert "CustomEvent" in event_types, "Should have CustomEvent"
        assert "HelperCompleted" in event_types, "Should have HelperCompleted event"

        print(f"✓ Found {len(helper_db.events)} events")
        print(f"  Event types: {', '.join(sorted(event_types))}")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE4-%';"
        )
        await db.pool.execute("DELETE FROM tac_agent_templates WHERE name = 'test-helper';")
        await db.close()

    print()


async def test_helper_error_handling():
    """Test 5: Helper error handling"""
    print("Test 5: Helper Error Handling")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE4-005"))
        stage_id = await db.create_stage(
            StageCreate(task_id=task_id, stage_name="planning")
        )
        print("✓ Created task and stage")

        # Create helper manager
        manager = HelperAgentManager(db)

        helper_id = None

        # Spawn helper and raise exception
        try:
            async with manager.spawn_helper(
                task_id=task_id,
                stage_id=stage_id,
                template_name="test-helper",
                purpose="Test error handling",
            ) as helper:
                helper_id = helper.helper_id
                print(f"✓ Spawned helper: {helper.agent_name}")

                # Raise an exception
                raise ValueError("Simulated error for testing")

        except ValueError as e:
            print(f"✓ Exception caught: {e}")

        # Verify helper was marked as errored
        assert helper_id is not None, "Should have helper_id"
        helper_db = await db.get_helper_with_events(helper_id)

        assert helper_db.helper.status == "errored", "Helper should be errored"
        assert "Simulated error" in (helper_db.helper.result_summary or ""), "Should have error message"
        print("✓ Helper marked as errored in database")

        # Verify error event was logged
        error_events = [e for e in helper_db.events if e.event_type == "HelperErrored"]
        assert len(error_events) > 0, "Should have HelperErrored event"
        print(f"✓ Error event logged")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE4-%';"
        )
        await db.pool.execute("DELETE FROM tac_agent_templates WHERE name = 'test-helper';")
        await db.close()

    print()


async def test_multiple_helpers():
    """Test 6: Multiple concurrent helpers"""
    print("Test 6: Multiple Concurrent Helpers")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE4-006"))
        stage_id = await db.create_stage(
            StageCreate(task_id=task_id, stage_name="building")
        )
        print("✓ Created task and stage")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Spawn multiple helpers concurrently
        async def spawn_and_run(purpose: str):
            async with manager.spawn_helper(
                task_id=task_id,
                stage_id=stage_id,
                template_name="test-helper",
                purpose=purpose,
            ) as helper:
                await helper.run(prompt=f"Execute {purpose}")
                return helper.helper_id

        # Spawn 3 helpers concurrently
        helper_ids = await asyncio.gather(
            spawn_and_run("Helper 1"),
            spawn_and_run("Helper 2"),
            spawn_and_run("Helper 3"),
        )

        print(f"✓ Spawned {len(helper_ids)} helpers concurrently")

        # Verify all helpers completed
        for helper_id in helper_ids:
            helper_db = await db.get_helper_with_events(helper_id)
            assert helper_db.helper.status == "completed", f"Helper {helper_id} should be completed"

        print("✓ All helpers completed successfully")

        # Verify costs rolled up to task
        task = await db.get_task(task_id)
        assert task.total_cost > Decimal("0"), "Should have aggregated cost"
        print(f"✓ Total task cost: ${task.total_cost}")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE4-%';"
        )
        await db.pool.execute("DELETE FROM tac_agent_templates WHERE name = 'test-helper';")
        await db.close()

    print()


async def test_template_not_found():
    """Test 7: Handle missing template gracefully"""
    print("Test 7: Missing Template Handling")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-PHASE4-007"))
        stage_id = await db.create_stage(
            StageCreate(task_id=task_id, stage_name="planning")
        )
        print("✓ Created task and stage")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Try to spawn with non-existent template
        try:
            async with manager.spawn_helper(
                task_id=task_id,
                stage_id=stage_id,
                template_name="non-existent-template",
                purpose="Test missing template",
            ) as helper:
                pass
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "not found" in str(e).lower(), "Should mention template not found"
            print(f"✓ Correctly raised ValueError: {e}")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-PHASE4-%';"
        )
        await db.close()

    print()


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Phase 4 Helper Spawn Mechanism Test Suite")
    print("=" * 50)
    print()

    try:
        await test_helper_spawn_basic()
        await test_helper_execution()
        await test_helper_result_tracking()
        await test_helper_event_logging()
        await test_helper_error_handling()
        await test_multiple_helpers()
        await test_template_not_found()

        print("=" * 50)
        print("✓ All Phase 4 Tests Passed!")
        print("=" * 50)
        print()
        print("Helper Spawn Mechanism Status:")
        print("  Helper spawning: Working")
        print("  Lifecycle management: Working")
        print("  Event logging: Working")
        print("  Cost aggregation: Working")
        print("  Error handling: Working")
        print("  Concurrent helpers: Working")
        print()
        print("Ready for Phase 5: Update MultiStageWorker for PostgreSQL")
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
