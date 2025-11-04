"""
Unit tests for TAC Dashboard API endpoints.

Tests all REST API endpoints for correct functionality, error handling,
and data validation.
"""

import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tac_api import app


@pytest.fixture
async def client():
    """Create async HTTP client for testing API."""
    # Manually trigger startup event
    from tac_api import startup, shutdown

    # Initialize database connection
    await startup()

    # Create client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await shutdown()


class TestTasksEndpoint:
    """Tests for GET /api/tasks endpoint."""

    @pytest.mark.asyncio
    async def test_get_tasks_returns_200(self, client):
        """Test that tasks endpoint returns 200 OK."""
        response = await client.get("/api/tasks")
        assert response.status_code == 200, "Should return 200 OK"

    @pytest.mark.asyncio
    async def test_get_tasks_returns_correct_structure(self, client):
        """Test that tasks endpoint returns correct JSON structure."""
        response = await client.get("/api/tasks")
        data = response.json()

        assert "tasks" in data, "Response should have 'tasks' key"
        assert "count" in data, "Response should have 'count' key"
        assert isinstance(data["tasks"], list), "tasks should be a list"
        assert isinstance(data["count"], int), "count should be an integer"

    @pytest.mark.asyncio
    async def test_get_tasks_with_limit(self, client):
        """Test that tasks endpoint respects limit parameter."""
        response = await client.get("/api/tasks?limit=10")
        assert response.status_code == 200
        data = response.json()

        # Count should not exceed limit
        assert data["count"] <= 10, "Should not exceed limit"

    @pytest.mark.asyncio
    async def test_get_tasks_validates_task_structure(self, client):
        """Test that each task has required fields."""
        response = await client.get("/api/tasks")
        data = response.json()

        if data["count"] > 0:
            task = data["tasks"][0]
            required_fields = [
                "id", "issue_number", "status",
                "total_cost", "total_input_tokens", "total_output_tokens",
                "created_at"
            ]

            for field in required_fields:
                assert field in task, f"Task should have '{field}' field"


class TestStatisticsEndpoint:
    """Tests for GET /api/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_returns_200(self, client):
        """Test that stats endpoint returns 200 OK."""
        response = await client.get("/api/stats")
        assert response.status_code == 200, "Should return 200 OK"

    @pytest.mark.asyncio
    async def test_get_stats_returns_correct_structure(self, client):
        """Test that stats endpoint returns correct JSON structure."""
        response = await client.get("/api/stats")
        data = response.json()

        # Check top-level keys
        assert "tasks" in data, "Should have tasks statistics"
        assert "costs" in data, "Should have cost statistics"
        assert "helpers" in data, "Should have helper statistics"
        assert "templates" in data, "Should have template statistics"

        # Check tasks structure
        assert "total" in data["tasks"], "tasks should have total count"
        assert "running" in data["tasks"], "tasks should have running count"
        assert "completed" in data["tasks"], "tasks should have completed count"
        assert "errored" in data["tasks"], "tasks should have errored count"

        # Check costs structure
        assert "total" in data["costs"], "costs should have total"
        assert "input_tokens" in data["costs"], "costs should have input_tokens"
        assert "output_tokens" in data["costs"], "costs should have output_tokens"

        # Check helpers structure
        assert "total" in data["helpers"], "helpers should have total"

        # Check templates structure
        assert "active" in data["templates"], "templates should have active count"

    @pytest.mark.asyncio
    async def test_get_stats_returns_valid_numbers(self, client):
        """Test that stats endpoint returns valid numeric values."""
        response = await client.get("/api/stats")
        data = response.json()

        # All counts should be non-negative integers
        assert data["tasks"]["total"] >= 0, "total tasks should be >= 0"
        assert data["tasks"]["running"] >= 0, "running tasks should be >= 0"
        assert data["tasks"]["completed"] >= 0, "completed tasks should be >= 0"
        assert data["tasks"]["errored"] >= 0, "errored tasks should be >= 0"

        # Total cost should be non-negative
        assert data["costs"]["total"] >= 0, "total cost should be >= 0"

        # Token counts should be non-negative
        assert data["costs"]["input_tokens"] >= 0, "input tokens should be >= 0"
        assert data["costs"]["output_tokens"] >= 0, "output tokens should be >= 0"

    @pytest.mark.asyncio
    async def test_get_stats_task_counts_add_up(self, client):
        """Test that task status counts are consistent."""
        response = await client.get("/api/stats")
        data = response.json()

        total = data["tasks"]["total"]
        running = data["tasks"]["running"]
        completed = data["tasks"]["completed"]
        errored = data["tasks"]["errored"]

        # Running + completed + errored should equal total
        assert running + completed + errored <= total, \
            "Sum of status counts should not exceed total"


class TestTaskDetailEndpoint:
    """Tests for GET /api/tasks/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_task_with_valid_uuid(self, client):
        """Test that task detail endpoint works with valid UUID."""
        # First get a task UUID
        tasks_response = await client.get("/api/tasks")
        tasks = tasks_response.json()["tasks"]

        if len(tasks) == 0:
            pytest.skip("No tasks in database to test")

        task_id = tasks[0]["id"]

        # Get task details
        response = await client.get(f"/api/tasks/{task_id}")

        assert response.status_code == 200, "Should return 200 OK for valid UUID"

    @pytest.mark.asyncio
    async def test_get_task_returns_correct_structure(self, client):
        """Test that task detail endpoint returns correct structure."""
        # Get a task UUID
        tasks_response = await client.get("/api/tasks")
        tasks = tasks_response.json()["tasks"]

        if len(tasks) == 0:
            pytest.skip("No tasks in database to test")

        task_id = tasks[0]["id"]
        response = await client.get(f"/api/tasks/{task_id}")
        data = response.json()

        # Check structure
        assert "task" in data, "Should have task data"
        assert "stages" in data, "Should have stages list"
        assert "helpers" in data, "Should have helpers list"
        assert "event_count" in data, "Should have event count"
        assert "latest_events" in data, "Should have events list"

        # Verify types
        assert isinstance(data["task"], dict), "task should be a dict"
        assert isinstance(data["stages"], list), "stages should be a list"
        assert isinstance(data["helpers"], list), "helpers should be a list"
        assert isinstance(data["event_count"], int), "event_count should be an int"
        assert isinstance(data["latest_events"], list), "latest_events should be a list"

    @pytest.mark.asyncio
    async def test_get_task_with_invalid_uuid_returns_400(self, client):
        """Test that invalid UUID returns 400 Bad Request."""
        response = await client.get("/api/tasks/invalid-uuid-format")

        assert response.status_code == 400, "Should return 400 for invalid UUID"
        assert "Invalid task ID format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_task_with_nonexistent_uuid_returns_404(self, client):
        """Test that non-existent UUID returns 404 Not Found."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/tasks/{fake_uuid}")

        assert response.status_code == 404, "Should return 404 for non-existent task"
        assert "Task not found" in response.json()["detail"]


class TestActiveTasksEndpoint:
    """Tests for GET /api/active endpoint."""

    @pytest.mark.asyncio
    async def test_get_active_tasks_returns_200(self, client):
        """Test that active tasks endpoint returns 200 OK."""
        response = await client.get("/api/active")
        assert response.status_code == 200, "Should return 200 OK"

    @pytest.mark.asyncio
    async def test_get_active_tasks_returns_list(self, client):
        """Test that active tasks endpoint returns a list."""
        response = await client.get("/api/active")
        data = response.json()

        assert "tasks" in data, "Should have 'tasks' key"
        assert isinstance(data["tasks"], list), "tasks should be a list"


class TestConcurrency:
    """Tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_stats_requests(self, client):
        """Test that API handles concurrent stats requests."""
        import asyncio

        # Make 10 concurrent requests
        tasks = [client.get("/api/stats") for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200, "All concurrent requests should succeed"

    @pytest.mark.asyncio
    async def test_concurrent_task_list_requests(self, client):
        """Test that API handles concurrent task list requests."""
        import asyncio

        # Make 10 concurrent requests
        tasks = [client.get("/api/tasks") for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200, "All concurrent requests should succeed"

        # All should return same data (since database doesn't change)
        first_data = responses[0].json()
        for response in responses[1:]:
            assert response.json()["count"] == first_data["count"], \
                "All responses should return consistent data"


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_limit_parameter(self, client):
        """Test that invalid limit parameter is handled."""
        response = await client.get("/api/tasks?limit=not-a-number")

        # FastAPI should return 422 for validation error
        assert response.status_code in [200, 422], \
            "Should either use default or return validation error"

    @pytest.mark.asyncio
    async def test_negative_limit_parameter(self, client):
        """Test that negative limit is handled."""
        response = await client.get("/api/tasks?limit=-1")

        # Should either use default or validate
        assert response.status_code in [200, 422], \
            "Should handle negative limit gracefully"


class TestPerformance:
    """Tests for API performance."""

    @pytest.mark.asyncio
    async def test_task_list_response_time(self, client):
        """Test that task list endpoint responds quickly."""
        import time

        start = time.time()
        response = await client.get("/api/tasks")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Should respond within 1 second, took {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_stats_response_time(self, client):
        """Test that stats endpoint responds quickly."""
        import time

        start = time.time()
        response = await client.get("/api/stats")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Should respond within 1 second, took {elapsed:.2f}s"
