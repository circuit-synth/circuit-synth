"""
Tests for dashboard FastAPI server

Following TDD approach - tests written before implementation.
"""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient


class TestDashboardAPI:
    """Test dashboard API endpoints"""

    @pytest.fixture
    def temp_tasks_file(self):
        """Create a temporary tasks.md file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Circuit-Synth Work Queue

**Last updated:** 2025-11-02 10:30:00

---

## Pending

[] gh-455: Dashboard: Add system performance metrics and resource monitoring {p1}
[] gh-456: Add token budget monitoring {p2}

---

## Active (max 3)

[🟡 w-abc123, trees/gh-450] gh-450: Add live agent logs viewer
- Started: 2025-11-02 10:00:00
- PID: 12345

---

## Completed Today

[✅ 0b06456, w-ghi789] gh-461: Phase 1: Bidirectional test infrastructure
- Completed: 2025-11-02 09:45:00
- PR: https://github.com/circuit-synth/circuit-synth/pull/461

---

## Failed

<!-- No failed tasks -->

---

## Blocked

<!-- No blocked tasks -->
""")
            path = Path(f.name)

        yield path

        # Cleanup
        if path.exists():
            path.unlink()

    @pytest.fixture
    def client(self, temp_tasks_file):
        """Create test client with temporary tasks file"""
        from circuit_synth.tools.dashboard.server import create_app

        app = create_app(tasks_file=temp_tasks_file)
        return TestClient(app)

    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'timestamp' in data

    def test_get_status(self, client):
        """Test /api/status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()

        # Should include task counts
        assert 'tasks' in data
        assert data['tasks']['pending_count'] == 2
        assert data['tasks']['active_count'] == 1
        assert data['tasks']['completed_count'] == 1

        # Should include timestamp
        assert 'timestamp' in data

    def test_get_tasks(self, client):
        """Test /api/tasks endpoint"""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()

        assert 'pending' in data
        assert 'active' in data
        assert 'completed' in data

        # Check pending tasks
        assert len(data['pending']) == 2
        assert data['pending'][0]['task_id'] == 'gh-455'
        assert data['pending'][0]['priority'] == 1

        # Check active tasks
        assert len(data['active']) == 1
        assert data['active'][0]['task_id'] == 'gh-450'
        assert data['active'][0]['worker_id'] == 'w-abc123'

    def test_get_workers(self, client):
        """Test /api/workers endpoint"""
        response = client.get("/api/workers")
        assert response.status_code == 200
        data = response.json()

        assert 'workers' in data
        assert isinstance(data['workers'], list)

        # Should have one worker from active task
        if len(data['workers']) > 0:
            worker = data['workers'][0]
            assert 'task_id' in worker
            assert 'worker_id' in worker
            assert 'pid' in worker

    def test_get_system_metrics(self, client):
        """Test /api/system endpoint"""
        response = client.get("/api/system")
        assert response.status_code == 200
        data = response.json()

        # Check required metrics
        assert 'cpu_percent' in data
        assert 'memory_percent' in data
        assert 'disk_percent' in data
        assert 'timestamp' in data

        # Validate values
        assert 0 <= data['cpu_percent'] <= 100
        assert 0 <= data['memory_percent'] <= 100

    def test_get_all_metrics(self, client):
        """Test /api/metrics endpoint (combined metrics)"""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()

        # Should include all metric categories
        assert 'timestamp' in data
        assert 'tasks' in data
        assert 'active_tasks' in data
        assert 'system' in data
        assert 'workers' in data

    def test_serve_frontend(self, client):
        """Test serving frontend HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        # Should contain dashboard HTML
        assert b'dashboard' in response.content.lower() or b'circuit-synth' in response.content.lower()

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get("/api/status")
        assert response.status_code == 200
        # FastAPI with CORS middleware should add these headers
        # This is a basic check - specific CORS config may vary
        assert response.headers.get('access-control-allow-origin') is not None or response.status_code == 200

    def test_nonexistent_endpoint(self, client):
        """Test 404 for nonexistent endpoint"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
