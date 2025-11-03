"""
Tests for token budget monitoring functionality

Following TDD approach - tests written before implementation.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import os
import sys

# Add adws to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "adws"))

from adw_modules.dashboard_data import get_budget_status


class TestBudgetMonitoring:
    """Test budget monitoring functionality"""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary API log directory with sample data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            # Create sample log file for current month
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = log_dir / f"api-calls-{today}.jsonl"

            # Add sample API calls with token usage
            calls = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "task_id": "gh-450",
                    "worker_id": "w-abc123",
                    "model": "claude-sonnet-4-5",
                    "success": True,
                    "tokens_input": 5000,
                    "tokens_output": 2000,
                    "tokens_total": 7000,
                    "estimated_cost_usd": 0.045
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "task_id": "gh-451",
                    "worker_id": "w-def456",
                    "model": "claude-haiku-4",
                    "success": True,
                    "tokens_input": 3000,
                    "tokens_output": 1000,
                    "tokens_total": 4000,
                    "estimated_cost_usd": 0.0125
                }
            ]

            with open(log_file, 'w') as f:
                for call in calls:
                    f.write(json.dumps(call) + '\n')

            yield log_dir

    def test_get_budget_status_basic(self, temp_log_dir):
        """Test basic budget status calculation"""
        # Set budget via environment variable
        os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '100.00'

        status = get_budget_status(temp_log_dir)

        assert status is not None
        assert 'budget_usd' in status
        assert 'used_usd' in status
        assert 'remaining_usd' in status
        assert 'percentage_used' in status
        assert 'alert_level' in status
        assert 'month' in status

        assert status['budget_usd'] == 100.00
        assert status['used_usd'] > 0
        assert status['remaining_usd'] < 100.00
        assert 0 <= status['percentage_used'] <= 100

    def test_budget_alert_levels(self, temp_log_dir):
        """Test alert level thresholds"""
        # Test green zone (< 75%)
        os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '1000.00'
        status = get_budget_status(temp_log_dir)
        assert status['alert_level'] == 'green'
        assert status['percentage_used'] < 75

        # Test yellow zone (75-90%)
        os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '0.10'
        status = get_budget_status(temp_log_dir)
        assert status['alert_level'] in ['yellow', 'orange', 'red']

        # Test orange zone (90-95%)
        os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '0.065'
        status = get_budget_status(temp_log_dir)
        assert status['alert_level'] in ['orange', 'red']

        # Test red zone (> 95%)
        os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '0.060'
        status = get_budget_status(temp_log_dir)
        assert status['alert_level'] == 'red'

    def test_budget_missing_env_var(self, temp_log_dir):
        """Test behavior when budget env var is missing"""
        if 'MONTHLY_TOKEN_BUDGET_USD' in os.environ:
            del os.environ['MONTHLY_TOKEN_BUDGET_USD']

        status = get_budget_status(temp_log_dir)

        # Should return None when budget not configured
        assert status is None

    def test_budget_no_logs(self):
        """Test behavior with no log files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '100.00'

            status = get_budget_status(log_dir)

            assert status is not None
            assert status['used_usd'] == 0.0
            assert status['remaining_usd'] == 100.00
            assert status['percentage_used'] == 0.0
            assert status['alert_level'] == 'green'

    def test_budget_calculation_accuracy(self, temp_log_dir):
        """Test that budget calculations are accurate"""
        os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '100.00'

        status = get_budget_status(temp_log_dir)

        # From our test data: 0.045 + 0.0125 = 0.0575
        expected_used = 0.0575
        assert abs(status['used_usd'] - expected_used) < 0.001

        expected_remaining = 100.00 - expected_used
        assert abs(status['remaining_usd'] - expected_remaining) < 0.001

        expected_percentage = (expected_used / 100.00) * 100
        assert abs(status['percentage_used'] - expected_percentage) < 0.01

    def test_month_field(self, temp_log_dir):
        """Test that month field is correctly set"""
        os.environ['MONTHLY_TOKEN_BUDGET_USD'] = '100.00'

        status = get_budget_status(temp_log_dir)

        expected_month = datetime.now().strftime('%Y-%m')
        assert status['month'] == expected_month
