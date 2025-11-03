"""
Token Budget Monitoring Module

Tracks and monitors monthly token usage against configured budget limits.
Provides alerts when approaching or exceeding budget thresholds.

Environment Variables:
    TOKEN_BUDGET_MONTHLY: Monthly token budget limit (required)
    TOKEN_BUDGET_ALERT_THRESHOLD_75: Alert threshold at 75% (default: 0.75)
    TOKEN_BUDGET_ALERT_THRESHOLD_90: Alert threshold at 90% (default: 0.90)
    TOKEN_BUDGET_ALERT_THRESHOLD_95: Alert threshold at 95% (default: 0.95)
    TOKEN_USAGE_DB_PATH: Path to SQLite database for usage tracking (optional)

Example:
    >>> import os
    >>> os.environ['TOKEN_BUDGET_MONTHLY'] = '1000000'
    >>> budget = TokenBudget.from_env()
    >>> status = budget.get_status()
    >>> print(f"Usage: {status['percentage_used']:.1f}%")
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class TokenBudget:
    """
    Token budget monitoring and tracking

    Tracks monthly token usage and provides alerts when approaching limits.
    Uses SQLite database to persist usage history.

    Attributes:
        monthly_limit: Maximum tokens allowed per month
        alert_threshold_75: Percentage threshold for yellow alert (default: 0.75)
        alert_threshold_90: Percentage threshold for orange alert (default: 0.90)
        alert_threshold_95: Percentage threshold for red alert (default: 0.95)
        db_path: Path to SQLite database for usage tracking
    """

    def __init__(
        self,
        monthly_limit: int,
        alert_threshold_75: float = 0.75,
        alert_threshold_90: float = 0.90,
        alert_threshold_95: float = 0.95,
        db_path: Optional[Path] = None
    ):
        """
        Initialize TokenBudget

        Args:
            monthly_limit: Maximum tokens allowed per month
            alert_threshold_75: Percentage for yellow alert (0.0-1.0)
            alert_threshold_90: Percentage for orange alert (0.0-1.0)
            alert_threshold_95: Percentage for red alert (0.0-1.0)
            db_path: Path to SQLite database (defaults to adws/token_usage.db)
        """
        self.monthly_limit = monthly_limit
        self.alert_threshold_75 = alert_threshold_75
        self.alert_threshold_90 = alert_threshold_90
        self.alert_threshold_95 = alert_threshold_95

        # Default database path in adws directory
        if db_path is None:
            adws_dir = Path(__file__).parent.parent
            db_path = adws_dir / 'token_usage.db'

        self.db_path = db_path
        self._init_database()

    @classmethod
    def from_env(cls) -> 'TokenBudget':
        """
        Create TokenBudget from environment variables

        Required environment variables:
            TOKEN_BUDGET_MONTHLY: Monthly token budget limit

        Optional environment variables:
            TOKEN_BUDGET_ALERT_THRESHOLD_75: Alert at 75% (default: 0.75)
            TOKEN_BUDGET_ALERT_THRESHOLD_90: Alert at 90% (default: 0.90)
            TOKEN_BUDGET_ALERT_THRESHOLD_95: Alert at 95% (default: 0.95)
            TOKEN_USAGE_DB_PATH: Custom database path

        Returns:
            TokenBudget instance configured from environment

        Raises:
            ValueError: If TOKEN_BUDGET_MONTHLY is not set or invalid
        """
        monthly_limit_str = os.environ.get('TOKEN_BUDGET_MONTHLY')

        if not monthly_limit_str:
            raise ValueError("TOKEN_BUDGET_MONTHLY environment variable not set")

        try:
            monthly_limit = int(monthly_limit_str)
        except ValueError:
            raise ValueError(f"Invalid TOKEN_BUDGET_MONTHLY: {monthly_limit_str}")

        # Parse optional thresholds
        alert_75 = float(os.environ.get('TOKEN_BUDGET_ALERT_THRESHOLD_75', '0.75'))
        alert_90 = float(os.environ.get('TOKEN_BUDGET_ALERT_THRESHOLD_90', '0.90'))
        alert_95 = float(os.environ.get('TOKEN_BUDGET_ALERT_THRESHOLD_95', '0.95'))

        # Parse optional database path
        db_path_str = os.environ.get('TOKEN_USAGE_DB_PATH')
        db_path = Path(db_path_str) if db_path_str else None

        return cls(
            monthly_limit=monthly_limit,
            alert_threshold_75=alert_75,
            alert_threshold_90=alert_90,
            alert_threshold_95=alert_95,
            db_path=db_path
        )

    def _init_database(self):
        """Initialize SQLite database for usage tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    month TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    operation TEXT,
                    description TEXT
                )
            ''')

            # Create index on month for faster queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_month
                ON token_usage(month)
            ''')

            conn.commit()

    def _get_current_month(self) -> str:
        """Get current month in YYYY-MM format"""
        return datetime.now().strftime('%Y-%m')

    def get_current_usage(self) -> int:
        """
        Get total token usage for current month

        Returns:
            Total tokens used in current month
        """
        current_month = self._get_current_month()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT SUM(tokens_used) FROM token_usage WHERE month = ?',
                (current_month,)
            )
            result = cursor.fetchone()[0]

            return result if result is not None else 0

    def record_usage(
        self,
        tokens_used: int,
        operation: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Record token usage

        Args:
            tokens_used: Number of tokens used
            operation: Optional operation name (e.g., 'claude_api_call')
            description: Optional description
        """
        current_month = self._get_current_month()
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO token_usage (timestamp, month, tokens_used, operation, description)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (timestamp, current_month, tokens_used, operation, description)
            )
            conn.commit()

    def get_status(self) -> Dict[str, any]:
        """
        Get current budget status

        Returns:
            Dictionary with keys:
                - monthly_limit: Monthly token limit
                - current_usage: Tokens used this month
                - percentage_used: Percentage of budget used (0-100+)
                - remaining: Tokens remaining in budget
                - alert_level: Current alert level (green/yellow/orange/red)
        """
        current_usage = self.get_current_usage()
        remaining = self.monthly_limit - current_usage
        percentage_used = (current_usage / self.monthly_limit) * 100 if self.monthly_limit > 0 else 0

        # Determine alert level
        if percentage_used < self.alert_threshold_75 * 100:
            alert_level = 'green'
        elif percentage_used < self.alert_threshold_90 * 100:
            alert_level = 'yellow'
        elif percentage_used < self.alert_threshold_95 * 100:
            alert_level = 'orange'
        else:
            alert_level = 'red'

        return {
            'monthly_limit': self.monthly_limit,
            'current_usage': current_usage,
            'percentage_used': percentage_used,
            'remaining': remaining,
            'alert_level': alert_level
        }

    def get_usage_history(self, months: int = 3) -> list:
        """
        Get usage history for past N months

        Args:
            months: Number of months to retrieve (default: 3)

        Returns:
            List of dictionaries with monthly usage data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT
                    month,
                    SUM(tokens_used) as total_tokens,
                    COUNT(*) as num_operations
                FROM token_usage
                GROUP BY month
                ORDER BY month DESC
                LIMIT ?
                ''',
                (months,)
            )

            results = []
            for row in cursor.fetchall():
                month, total_tokens, num_operations = row
                percentage = (total_tokens / self.monthly_limit) * 100

                results.append({
                    'month': month,
                    'total_tokens': total_tokens,
                    'num_operations': num_operations,
                    'percentage_used': percentage
                })

            return results

    def should_pause_operations(self) -> bool:
        """
        Check if operations should be paused due to budget limits

        Returns:
            True if budget is exceeded (>= 100% used), False otherwise
        """
        status = self.get_status()
        return status['percentage_used'] >= 100.0

    def get_budget_recommendation(self) -> str:
        """
        Get recommendation based on current usage

        Returns:
            String with budget recommendation
        """
        status = self.get_status()
        percentage = status['percentage_used']

        if percentage < 50:
            return "Budget usage is healthy. Continue normal operations."
        elif percentage < 75:
            return "Approaching mid-month budget. Monitor usage closely."
        elif percentage < 90:
            return "Warning: High budget usage. Consider reducing operations."
        elif percentage < 95:
            return "Critical: Near budget limit. Pause non-essential operations."
        else:
            return "Critical: Budget exceeded. Pause all operations until next month."
