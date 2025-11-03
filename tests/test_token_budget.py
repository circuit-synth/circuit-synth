"""
Tests for token budget monitoring module

Tests token budget tracking functionality including:
- Token count formatting
- Budget status calculation
- Database operations
- Monthly usage tracking
- Dashboard integration
"""

import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
import sys

# Add adws modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules import token_budget


def test_format_token_count():
    """Test token count formatting with K/M suffixes"""
    assert token_budget.format_token_count(500) == "500"
    assert token_budget.format_token_count(5_000) == "5.0K"
    assert token_budget.format_token_count(1_500_000) == "1.5M"
    assert token_budget.format_token_count(10_250_000) == "10.2M"


def test_calculate_budget_status_ok():
    """Test budget status calculation when under warning threshold"""
    status = token_budget.calculate_budget_status(
        current_usage=50_000,
        budget_limit=1_000_000,
        threshold_warning=75,
        threshold_critical=90,
        threshold_severe=95
    )

    assert status['percentage'] == 5.0
    assert status['alert_level'] == 'ok'
    assert status['alert_emoji'] == '🟢'
    assert status['alert_message'] == ''


def test_calculate_budget_status_warning():
    """Test budget status calculation at warning threshold"""
    status = token_budget.calculate_budget_status(
        current_usage=750_000,
        budget_limit=1_000_000,
        threshold_warning=75,
        threshold_critical=90,
        threshold_severe=95
    )

    assert status['percentage'] == 75.0
    assert status['alert_level'] == 'warning'
    assert status['alert_emoji'] == '🟡'
    assert '>75%' in status['alert_message']


def test_calculate_budget_status_critical():
    """Test budget status calculation at critical threshold"""
    status = token_budget.calculate_budget_status(
        current_usage=900_000,
        budget_limit=1_000_000,
        threshold_warning=75,
        threshold_critical=90,
        threshold_severe=95
    )

    assert status['percentage'] == 90.0
    assert status['alert_level'] == 'critical'
    assert status['alert_emoji'] == '🟠'
    assert '>90%' in status['alert_message']


def test_calculate_budget_status_severe():
    """Test budget status calculation at severe threshold"""
    status = token_budget.calculate_budget_status(
        current_usage=950_000,
        budget_limit=1_000_000,
        threshold_warning=75,
        threshold_critical=90,
        threshold_severe=95
    )

    assert status['percentage'] == 95.0
    assert status['alert_level'] == 'severe'
    assert status['alert_emoji'] == '🔴'
    assert '>95%' in status['alert_message']


def test_calculate_budget_status_over_budget():
    """Test budget status calculation when over budget"""
    status = token_budget.calculate_budget_status(
        current_usage=1_100_000,
        budget_limit=1_000_000,
        threshold_warning=75,
        threshold_critical=90,
        threshold_severe=95
    )

    assert status['percentage'] == 110.0
    assert status['alert_level'] == 'over_budget'
    assert status['alert_emoji'] == '🔴'
    assert 'exceeded' in status['alert_message'].lower()


def test_initialize_database():
    """Test database initialization creates correct schema"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override get_database_path temporarily
        original_get_path = token_budget.get_database_path
        test_db = Path(tmpdir) / "test_tokens.db"
        token_budget.get_database_path = lambda: test_db

        try:
            token_budget.initialize_database()

            # Verify database exists
            assert test_db.exists()

            # Verify schema
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()

            # Check usage table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='usage'
            """)
            assert cursor.fetchone() is not None

            # Check table structure
            cursor.execute("PRAGMA table_info(usage)")
            columns = {row[1] for row in cursor.fetchall()}
            expected_columns = {
                'id', 'timestamp', 'task_id', 'model',
                'input_tokens', 'output_tokens', 'total_tokens',
                'cost', 'notes'
            }
            assert expected_columns.issubset(columns)

            conn.close()
        finally:
            token_budget.get_database_path = original_get_path


def test_record_usage():
    """Test recording token usage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override get_database_path temporarily
        original_get_path = token_budget.get_database_path
        test_db = Path(tmpdir) / "test_tokens.db"
        token_budget.get_database_path = lambda: test_db

        try:
            # Record usage
            token_budget.record_usage(
                task_id="gh-450",
                model="claude-sonnet-4-5",
                input_tokens=1000,
                output_tokens=500,
                cost=0.05,
                notes="Test task"
            )

            # Verify record exists
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM usage WHERE task_id = ?", ("gh-450",))
            row = cursor.fetchone()

            assert row is not None
            assert row[2] == "gh-450"  # task_id
            assert row[3] == "claude-sonnet-4-5"  # model
            assert row[4] == 1000  # input_tokens
            assert row[5] == 500  # output_tokens
            assert row[6] == 1500  # total_tokens
            assert abs(row[7] - 0.05) < 0.001  # cost
            assert row[8] == "Test task"  # notes

            conn.close()
        finally:
            token_budget.get_database_path = original_get_path


def test_get_monthly_usage():
    """Test retrieving monthly token usage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override get_database_path temporarily
        original_get_path = token_budget.get_database_path
        test_db = Path(tmpdir) / "test_tokens.db"
        token_budget.get_database_path = lambda: test_db

        try:
            # Initialize database
            token_budget.initialize_database()

            # Record some usage for current month
            token_budget.record_usage("gh-450", "model-1", 1000, 500, 0.05)
            token_budget.record_usage("gh-451", "model-2", 2000, 1000, 0.10)

            # Get monthly usage
            now = datetime.now()
            usage = token_budget.get_monthly_usage(now.year, now.month)

            # Should be sum of total tokens: 1500 + 3000 = 4500
            assert usage == 4500
        finally:
            token_budget.get_database_path = original_get_path


def test_get_monthly_usage_no_database():
    """Test get_monthly_usage returns 0 when database doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override get_database_path to non-existent path
        original_get_path = token_budget.get_database_path
        test_db = Path(tmpdir) / "nonexistent.db"
        token_budget.get_database_path = lambda: test_db

        try:
            # Should return 0 without error
            usage = token_budget.get_monthly_usage()
            assert usage == 0
        finally:
            token_budget.get_database_path = original_get_path


def test_load_budget_config_no_env():
    """Test load_budget_config returns None when no budget configured"""
    # Temporarily clear environment variables
    original_env = os.environ.copy()
    os.environ.pop('MONTHLY_TOKEN_BUDGET', None)

    try:
        config = token_budget.load_budget_config()
        assert config is None
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_load_budget_config_with_env():
    """Test load_budget_config with configured budget"""
    # Set environment variables
    original_env = os.environ.copy()
    os.environ['MONTHLY_TOKEN_BUDGET'] = '1.0'  # 1 million
    os.environ['BUDGET_ALERT_THRESHOLD_WARNING'] = '75'
    os.environ['BUDGET_ALERT_THRESHOLD_CRITICAL'] = '90'
    os.environ['BUDGET_ALERT_THRESHOLD_SEVERE'] = '95'

    try:
        config = token_budget.load_budget_config()

        assert config is not None
        assert config['budget_limit'] == 1_000_000
        assert config['thresholds']['warning'] == 75
        assert config['thresholds']['critical'] == 90
        assert config['thresholds']['severe'] == 95
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_get_budget_info_no_config():
    """Test get_budget_info returns None when no budget configured"""
    # Temporarily clear environment variables
    original_env = os.environ.copy()
    os.environ.pop('MONTHLY_TOKEN_BUDGET', None)

    try:
        info = token_budget.get_budget_info()
        assert info is None
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_get_budget_info_with_config():
    """Test get_budget_info with configured budget"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override get_database_path temporarily
        original_get_path = token_budget.get_database_path
        test_db = Path(tmpdir) / "test_tokens.db"
        token_budget.get_database_path = lambda: test_db

        # Set environment variables
        original_env = os.environ.copy()
        os.environ['MONTHLY_TOKEN_BUDGET'] = '1.0'  # 1 million
        os.environ['BUDGET_ALERT_THRESHOLD_WARNING'] = '75'
        os.environ['BUDGET_ALERT_THRESHOLD_CRITICAL'] = '90'
        os.environ['BUDGET_ALERT_THRESHOLD_SEVERE'] = '95'

        try:
            # Initialize and record usage
            token_budget.initialize_database()
            token_budget.record_usage("gh-450", "model-1", 400_000, 100_000, 1.0)

            # Get budget info - should use database since no logs directory
            info = token_budget.get_budget_info()

            assert info is not None
            assert info['current_usage'] == 500_000
            assert info['budget_limit'] == 1_000_000
            assert info['percentage'] == 50.0
            assert info['alert_level'] == 'ok'
            assert info['alert_emoji'] == '🟢'
        finally:
            os.environ.clear()
            os.environ.update(original_env)
            token_budget.get_database_path = original_get_path
