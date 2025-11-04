"""
Pytest configuration and fixtures for dashboard tests.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_database_url():
    """Return test database connection URL."""
    return "postgresql://tacx:tacx@localhost:5433/tacx"
