"""
Configuration for bidirectional tests.

Provides shared fixtures and command-line options.
"""
import pytest


def pytest_addoption(parser):
    """Add custom command line options for bidirectional tests."""
    parser.addoption(
        "--keep-output",
        action="store_true",
        default=False,
        help="Keep generated output files after test (for manual inspection)"
    )


@pytest.fixture
def keep_output(request):
    """Fixture to access --keep-output flag value."""
    return request.config.getoption("--keep-output")
