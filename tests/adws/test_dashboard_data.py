#!/usr/bin/env python3
"""Tests for dashboard data module"""

import pytest
import tempfile
from pathlib import Path
from adws.dashboard_data import DashboardData
from adws.budget_tracker import BudgetTracker


def test_dashboard_data_initialization():
    """Test dashboard data can be initialized"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000)
        assert dashboard.tracker is not None
        assert dashboard.monthly_limit == 1000000


def test_get_budget_card_data():
    """Test retrieving budget card data for dashboard"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000)

        # Record some usage
        dashboard.tracker.record_usage("w-test1", "450", 1000, 500)

        # Get card data
        card_data = dashboard.get_budget_card_data()

        assert card_data['tokens_used'] == 1500
        assert card_data['tokens_limit'] == 1000000
        assert card_data['percentage_used'] == pytest.approx(0.15, rel=0.01)
        assert 'alert_level' in card_data
        assert 'period_start' in card_data
        assert 'period_end' in card_data


def test_get_alert_status_no_alerts():
    """Test alert status when under threshold"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000)

        # Record usage below 75% threshold
        dashboard.tracker.record_usage("w-test1", "450", 100000, 50000)

        alert_status = dashboard.get_alert_status()

        assert alert_status['has_alert'] == False
        assert alert_status['alert_level'] is None


def test_get_alert_status_warning():
    """Test alert status at 75% threshold"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000,
                                 alert_thresholds=[75, 90, 95])

        # Record usage at 75% threshold
        dashboard.tracker.record_usage("w-test1", "450", 500000, 250000)

        alert_status = dashboard.get_alert_status()

        assert alert_status['has_alert'] == True
        assert alert_status['alert_level'] == 'warning'
        assert alert_status['percentage_used'] == 75.0


def test_get_alert_status_critical():
    """Test alert status at 95% threshold"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000,
                                 alert_thresholds=[75, 90, 95])

        # Record usage at 95% threshold
        dashboard.tracker.record_usage("w-test1", "450", 633333, 316667)

        alert_status = dashboard.get_alert_status()

        assert alert_status['has_alert'] == True
        assert alert_status['alert_level'] == 'critical'


def test_get_usage_trends():
    """Test retrieving usage trends for charting"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000)

        # Record some usage
        dashboard.tracker.record_usage("w-test1", "450", 1000, 500)
        dashboard.tracker.record_usage("w-test2", "451", 2000, 1000)

        trends = dashboard.get_usage_trends(days=30)

        assert isinstance(trends, list)
        assert len(trends) > 0
        assert 'date' in trends[0]
        assert 'tokens' in trends[0]
        assert 'cost' in trends[0]


def test_get_color_coded_status_green():
    """Test color coding for safe usage levels"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000)

        # Record usage at 50%
        dashboard.tracker.record_usage("w-test1", "450", 333333, 166667)

        status = dashboard.get_color_coded_status()

        assert status['color'] == 'green'
        assert status['badge'] == '✓'


def test_get_color_coded_status_yellow():
    """Test color coding for warning level"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000,
                                 alert_thresholds=[75, 90, 95])

        # Record usage at 80%
        dashboard.tracker.record_usage("w-test1", "450", 533333, 266667)

        status = dashboard.get_color_coded_status()

        assert status['color'] == 'yellow'
        assert status['badge'] == '⚠'


def test_get_color_coded_status_red():
    """Test color coding for critical level"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        dashboard = DashboardData(db_path, monthly_limit=1000000,
                                 alert_thresholds=[75, 90, 95])

        # Record usage at 96%
        dashboard.tracker.record_usage("w-test1", "450", 640000, 320000)

        status = dashboard.get_color_coded_status()

        assert status['color'] == 'red'
        assert status['badge'] == '✗'


def test_load_from_env_config():
    """Test loading budget configuration from environment"""
    import os
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Set environment variable
        os.environ['MONTHLY_TOKEN_BUDGET'] = '2000000'

        try:
            dashboard = DashboardData.from_env(db_path)
            assert dashboard.monthly_limit == 2000000
        finally:
            # Clean up
            if 'MONTHLY_TOKEN_BUDGET' in os.environ:
                del os.environ['MONTHLY_TOKEN_BUDGET']
