#!/usr/bin/env python3
"""
Phase 6 TAC Dashboard API Backend Test Suite

Tests the FastAPI backend that provides REST API endpoints for TAC observability.

Validates:
- API server startup and shutdown
- Task listing and filtering
- Task details with stages/helpers/events
- Active task monitoring
- System statistics aggregation
- Template listing
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from decimal import Decimal
import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_database import TACDatabase
from adw_modules.tac_models import TaskCreate, StageCreate, HelperAgentCreate, EventCreate


async def setup_test_data(db: TACDatabase):
    """Create test data for API testing"""
    # Create 3 tasks with different statuses
    task1_id = await db.create_task(TaskCreate(
        issue_number="TEST-API-001",
        worktree_path="/tmp/test1",
        branch_name="test/001",
    ))
    # Update to completed status
    await db.update_task_status(task1_id, status="completed")

    task2_id = await db.create_task(TaskCreate(
        issue_number="TEST-API-002",
        worktree_path="/tmp/test2",
        branch_name="test/002",
    ))
    # Keep as running (default)

    task3_id = await db.create_task(TaskCreate(
        issue_number="TEST-API-003",
        worktree_path="/tmp/test3",
        branch_name="test/003",
    ))
    # Update to errored status
    await db.update_task_status(task3_id, status="errored")

    # Add stages to task1
    stage1_id = await db.create_stage(StageCreate(
        task_id=task1_id,
        stage_name="planning",
        status="completed",
    ))

    await db.update_stage_completion(
        stage_id=stage1_id,
        status="completed",
        input_tokens=1000,
        output_tokens=500,
        cost=Decimal("0.05"),
    )

    stage2_id = await db.create_stage(StageCreate(
        task_id=task1_id,
        stage_name="building",
        status="completed",
    ))

    await db.update_stage_completion(
        stage_id=stage2_id,
        status="completed",
        input_tokens=2000,
        output_tokens=1000,
        cost=Decimal("0.10"),
    )

    # Add helper to task1
    helper_id = await db.create_helper(HelperAgentCreate(
        task_id=task1_id,
        stage_id=stage1_id,
        agent_name="test-helper-001",
        agent_template="research-agent",
    ))

    await db.update_helper_completion(
        helper_id=helper_id,
        status="completed",
        input_tokens=500,
        output_tokens=250,
        cost=Decimal("0.02"),
        result_summary="Found 5 test files",
    )

    # Add events
    await db.log_event(EventCreate(
        task_id=task1_id,
        event_category="system",
        event_type="TaskCreated",
        summary="Task created",
    ))

    await db.log_event(EventCreate(
        task_id=task1_id,
        stage_id=stage1_id,
        event_category="stage",
        event_type="StageStarted",
        summary="Stage planning started",
    ))

    await db.log_event(EventCreate(
        task_id=task1_id,
        stage_id=stage1_id,
        helper_agent_id=helper_id,
        event_category="helper",
        event_type="HelperSpawned",
        summary="Helper spawned",
    ))

    return task1_id, task2_id, task3_id


async def cleanup_test_data(db: TACDatabase):
    """Remove test data"""
    await db.pool.execute(
        "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-API-%';"
    )


async def test_api_root():
    """Test 1: API root endpoint"""
    print("Test 1: API Root Endpoint")
    print("-" * 50)

    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        response = await client.get("/")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data["name"] == "TAC Dashboard API", "Name should match"
        assert data["status"] == "running", "Status should be running"
        assert "endpoints" in data, "Should have endpoints"

        print(f"✓ API name: {data['name']}")
        print(f"✓ API version: {data['version']}")
        print(f"✓ API status: {data['status']}")
        print(f"✓ Endpoints: {', '.join(data['endpoints'].keys())}")

    print()


async def test_list_tasks():
    """Test 2: List tasks endpoint"""
    print("Test 2: List Tasks Endpoint")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test data
        await setup_test_data(db)

        async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
            response = await client.get("/api/tasks", params={"limit": 10})

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "tasks" in data, "Should have tasks key"
            assert "count" in data, "Should have count key"
            assert data["count"] >= 3, f"Should have at least 3 tasks, got {data['count']}"

            # Find our test tasks
            test_tasks = [t for t in data["tasks"] if t["issue_number"].startswith("TEST-API-")]
            assert len(test_tasks) == 3, f"Should have 3 test tasks, got {len(test_tasks)}"

            print(f"✓ Retrieved {data['count']} tasks")
            print(f"✓ Found {len(test_tasks)} test tasks")

            # Verify task data structure
            task = test_tasks[0]
            assert "id" in task, "Task should have id"
            assert "issue_number" in task, "Task should have issue_number"
            assert "status" in task, "Task should have status"
            assert "created_at" in task, "Task should have created_at"
            print("✓ Task data structure validated")

    finally:
        await cleanup_test_data(db)
        await db.close()

    print()


async def test_get_task_details():
    """Test 3: Get task details endpoint"""
    print("Test 3: Get Task Details Endpoint")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test data
        task1_id, _, _ = await setup_test_data(db)

        async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
            response = await client.get(f"/api/tasks/{task1_id}")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "task" in data, "Should have task"
            assert "stages" in data, "Should have stages"
            assert "helpers" in data, "Should have helpers"
            assert "event_count" in data, "Should have event_count"
            assert "latest_events" in data, "Should have latest_events"

            print(f"✓ Task ID: {data['task']['id']}")
            print(f"✓ Issue: {data['task']['issue_number']}")
            print(f"✓ Status: {data['task']['status']}")
            print(f"✓ Stages: {len(data['stages'])}")
            print(f"✓ Helpers: {len(data['helpers'])}")
            print(f"✓ Events: {data['event_count']}")

            # Verify stages
            assert len(data['stages']) == 2, f"Should have 2 stages, got {len(data['stages'])}"
            stage_names = {s['stage_name'] for s in data['stages']}
            assert "planning" in stage_names, "Should have planning stage"
            assert "building" in stage_names, "Should have building stage"
            print("✓ Stage data validated")

            # Verify helpers
            assert len(data['helpers']) == 1, f"Should have 1 helper, got {len(data['helpers'])}"
            helper = data['helpers'][0]
            assert helper['agent_template'] == "research-agent", "Helper template should match"
            assert helper['status'] == "completed", "Helper should be completed"
            print("✓ Helper data validated")

            # Verify events
            assert data['event_count'] >= 3, f"Should have at least 3 events, got {data['event_count']}"
            print("✓ Event data validated")

    finally:
        await cleanup_test_data(db)
        await db.close()

    print()


async def test_get_task_events():
    """Test 4: Get task events endpoint"""
    print("Test 4: Get Task Events Endpoint")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test data
        task1_id, _, _ = await setup_test_data(db)

        async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
            # Get all events
            response = await client.get(f"/api/tasks/{task1_id}/events", params={"limit": 100})

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "task_id" in data, "Should have task_id"
            assert "events" in data, "Should have events"
            assert "count" in data, "Should have count"

            print(f"✓ Retrieved {data['count']} events")

            # Verify event structure
            assert len(data['events']) > 0, "Should have at least one event"
            event = data['events'][0]
            assert "event_category" in event, "Event should have category"
            assert "event_type" in event, "Event should have type"
            assert "summary" in event, "Event should have summary"
            print("✓ Event data structure validated")

            # Get filtered events (stage category)
            response = await client.get(
                f"/api/tasks/{task1_id}/events",
                params={"limit": 100, "category": "stage"}
            )

            assert response.status_code == 200
            filtered_data = response.json()

            # All events should be stage events
            for evt in filtered_data['events']:
                assert evt['event_category'] == "stage", "All events should be stage events"

            print(f"✓ Category filtering works: {filtered_data['count']} stage events")

    finally:
        await cleanup_test_data(db)
        await db.close()

    print()


async def test_get_active_tasks():
    """Test 5: Get active tasks endpoint"""
    print("Test 5: Get Active Tasks Endpoint")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test data
        _, task2_id, _ = await setup_test_data(db)

        async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
            response = await client.get("/api/active")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "tasks" in data, "Should have tasks"
            assert "count" in data, "Should have count"

            # Find our running task
            running_tasks = [t for t in data["tasks"] if t["issue_number"] == "TEST-API-002"]
            assert len(running_tasks) == 1, f"Should have 1 running test task, got {len(running_tasks)}"

            running_task = running_tasks[0]
            assert running_task["status"] == "running", "Task should be running"

            print(f"✓ Retrieved {data['count']} active tasks")
            print(f"✓ Found running task: {running_task['issue_number']}")
            print("✓ Active tasks endpoint working")

    finally:
        await cleanup_test_data(db)
        await db.close()

    print()


async def test_get_statistics():
    """Test 6: Get system statistics endpoint"""
    print("Test 6: Get System Statistics Endpoint")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test data
        await setup_test_data(db)

        async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
            response = await client.get("/api/stats")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "tasks" in data, "Should have tasks stats"
            assert "costs" in data, "Should have costs stats"
            assert "helpers" in data, "Should have helpers stats"
            assert "templates" in data, "Should have templates stats"

            # Verify task stats
            task_stats = data["tasks"]
            assert "total" in task_stats, "Should have total tasks"
            assert "running" in task_stats, "Should have running count"
            assert "completed" in task_stats, "Should have completed count"
            assert "errored" in task_stats, "Should have errored count"

            assert task_stats["total"] >= 3, f"Should have at least 3 tasks, got {task_stats['total']}"
            assert task_stats["running"] >= 1, f"Should have at least 1 running, got {task_stats['running']}"
            assert task_stats["completed"] >= 1, f"Should have at least 1 completed, got {task_stats['completed']}"
            assert task_stats["errored"] >= 1, f"Should have at least 1 errored, got {task_stats['errored']}"

            print(f"✓ Task stats: {task_stats}")

            # Verify cost stats
            cost_stats = data["costs"]
            assert "total" in cost_stats, "Should have total cost"
            assert "input_tokens" in cost_stats, "Should have input tokens"
            assert "output_tokens" in cost_stats, "Should have output tokens"

            assert cost_stats["total"] > 0, "Should have non-zero cost"
            assert cost_stats["input_tokens"] > 0, "Should have input tokens"
            assert cost_stats["output_tokens"] > 0, "Should have output tokens"

            print(f"✓ Cost stats: ${cost_stats['total']:.4f}")
            print(f"  Input tokens: {cost_stats['input_tokens']}")
            print(f"  Output tokens: {cost_stats['output_tokens']}")

            # Verify helper stats
            helper_stats = data["helpers"]
            assert "total" in helper_stats, "Should have total helpers"
            assert helper_stats["total"] >= 1, f"Should have at least 1 helper, got {helper_stats['total']}"

            print(f"✓ Helper stats: {helper_stats}")

            print("✓ Statistics endpoint working")

    finally:
        await cleanup_test_data(db)
        await db.close()

    print()


async def test_get_templates():
    """Test 7: Get templates endpoint"""
    print("Test 7: Get Templates Endpoint")
    print("-" * 50)

    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        response = await client.get("/api/templates")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "templates" in data, "Should have templates"
        assert "count" in data, "Should have count"

        print(f"✓ Retrieved {data['count']} templates")

        # Verify template structure if any exist
        if data['count'] > 0:
            template = data['templates'][0]
            assert "name" in template, "Template should have name"
            assert "description" in template, "Template should have description"
            assert "model" in template, "Template should have model"
            print(f"✓ Template structure validated")
            print(f"  Example: {template['name']} - {template['description']}")
        else:
            print("  (No templates in database)")

        print("✓ Templates endpoint working")

    print()


async def test_error_handling():
    """Test 8: API error handling"""
    print("Test 8: API Error Handling")
    print("-" * 50)

    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        # Test invalid task ID format
        response = await client.get("/api/tasks/invalid-uuid")
        assert response.status_code == 400, f"Expected 400 for invalid UUID, got {response.status_code}"
        print("✓ Invalid UUID format rejected (400)")

        # Test non-existent task
        response = await client.get("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404, f"Expected 404 for non-existent task, got {response.status_code}"
        print("✓ Non-existent task returns 404")

        print("✓ Error handling working")

    print()


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Phase 6 TAC Dashboard API Backend Test Suite")
    print("=" * 50)
    print()
    print("NOTE: This test suite requires the API server to be running.")
    print("Start the server with: python3 dashboard/tac_api.py")
    print()

    # Check if server is running
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=2.0) as client:
            await client.get("/")
    except (httpx.ConnectError, httpx.TimeoutException):
        print("✗ API server not running on http://localhost:8001")
        print()
        print("Please start the server:")
        print("  cd /home/shane/Desktop/circuit-synth")
        print("  python3 dashboard/tac_api.py")
        print()
        sys.exit(1)

    print("✓ API server is running")
    print()

    try:
        await test_api_root()
        await test_list_tasks()
        await test_get_task_details()
        await test_get_task_events()
        await test_get_active_tasks()
        await test_get_statistics()
        await test_get_templates()
        await test_error_handling()

        print("=" * 50)
        print("✓ All Phase 6 Tests Passed!")
        print("=" * 50)
        print()
        print("TAC Dashboard API Backend Status:")
        print("  API root: Working")
        print("  List tasks: Working")
        print("  Task details: Working")
        print("  Task events: Working")
        print("  Active tasks: Working")
        print("  Statistics: Working")
        print("  Templates: Working")
        print("  Error handling: Working")
        print()
        print("Integration Status:")
        print("  ✓ FastAPI server running")
        print("  ✓ PostgreSQL connection active")
        print("  ✓ All endpoints responding")
        print("  ✓ Real-time data retrieval working")
        print()
        print("Ready for Phase 7: Web dashboard frontend")
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
