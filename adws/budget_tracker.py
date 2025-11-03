#!/usr/bin/env python3
"""
Token budget tracking for Circuit-Synth Autonomous Coordinator

Tracks token usage, provides alerts, and monitors against monthly budgets.
Simplified version compatible with budget_monitor.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class UsageRecord:
    """Single token usage record"""
    timestamp: str
    worker_id: str
    issue_number: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    cost_estimate: float


@dataclass
class BudgetStatus:
    """Current budget status"""
    period_start: str
    period_end: str
    tokens_used: int
    tokens_limit: int
    percentage_used: float
    cost_estimate: float
    alert_level: Optional[str]  # None, 'warning', 'critical', 'exceeded'
    days_remaining: int


class BudgetTracker:
    """Tracks token usage and manages budget alerts"""

    def __init__(self, db_path: Path, monthly_limit: int = 1000000,
                 alert_thresholds: Optional[List[int]] = None,
                 cost_per_million: float = 3.00,
                 reset_day: int = 1):
        """
        Initialize budget tracker

        Args:
            db_path: Path to SQLite database file
            monthly_limit: Monthly token budget
            alert_thresholds: List of percentage thresholds for alerts [75, 90, 95]
            cost_per_million: Cost per 1M tokens in USD
            reset_day: Day of month to reset budget (1-28)
        """
        self.db_path = db_path
        self.monthly_limit = monthly_limit
        self.alert_thresholds = alert_thresholds or [75, 90, 95]
        self.cost_per_million = cost_per_million
        self.reset_day = reset_day

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Create database schema if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Usage records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    issue_number TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    cost_estimate REAL NOT NULL,
                    period_month TEXT NOT NULL
                )
            """)

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_period_month
                ON usage_records(period_month)
            """)

            # Alerts history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    percentage_used REAL NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    message TEXT NOT NULL
                )
            """)

            conn.commit()

    def _get_current_period(self) -> Tuple[date, date]:
        """Get start and end dates for current budget period"""
        today = date.today()

        if today.day >= self.reset_day:
            # Current period started this month
            start = date(today.year, today.month, self.reset_day)
            # Next period starts next month
            if today.month == 12:
                end = date(today.year + 1, 1, self.reset_day)
            else:
                end = date(today.year, today.month + 1, self.reset_day)
        else:
            # Current period started last month
            if today.month == 1:
                start = date(today.year - 1, 12, self.reset_day)
            else:
                start = date(today.year, today.month - 1, self.reset_day)
            end = date(today.year, today.month, self.reset_day)

        return start, end

    def _get_period_key(self, dt: date) -> str:
        """Get period key (YYYY-MM) for a date"""
        start, _ = self._get_current_period()
        return start.strftime("%Y-%m")

    def record_usage(self, worker_id: str, issue_number: str,
                    input_tokens: int, output_tokens: int,
                    model: str = "claude-sonnet-4-5") -> UsageRecord:
        """
        Record token usage for a worker

        Args:
            worker_id: Worker identifier
            issue_number: GitHub issue number
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            model: Model name used

        Returns:
            UsageRecord object
        """
        timestamp = datetime.now().isoformat()
        total_tokens = input_tokens + output_tokens
        cost_estimate = (total_tokens / 1_000_000) * self.cost_per_million
        period_key = self._get_period_key(date.today())

        record = UsageRecord(
            timestamp=timestamp,
            worker_id=worker_id,
            issue_number=issue_number,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            model=model,
            cost_estimate=cost_estimate
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usage_records
                (timestamp, worker_id, issue_number, input_tokens, output_tokens,
                 total_tokens, model, cost_estimate, period_month)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, worker_id, issue_number, input_tokens, output_tokens,
                  total_tokens, model, cost_estimate, period_key))
            conn.commit()

        return record

    def get_current_usage(self) -> BudgetStatus:
        """
        Get current budget status for the current period

        Returns:
            BudgetStatus object with current usage and alert level
        """
        start, end = self._get_current_period()
        period_key = self._get_period_key(date.today())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_estimate), 0) as total_cost
                FROM usage_records
                WHERE period_month = ?
            """, (period_key,))

            row = cursor.fetchone()
            tokens_used = row[0] if row else 0
            cost_estimate = row[1] if row else 0.0

        percentage_used = (tokens_used / self.monthly_limit * 100) if self.monthly_limit > 0 else 0

        # Determine alert level
        alert_level = None
        if percentage_used >= 100:
            alert_level = 'exceeded'
        elif percentage_used >= max(self.alert_thresholds):
            alert_level = 'critical'
        elif percentage_used >= min(self.alert_thresholds):
            alert_level = 'warning'

        days_remaining = (end - date.today()).days

        return BudgetStatus(
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            tokens_used=tokens_used,
            tokens_limit=self.monthly_limit,
            percentage_used=percentage_used,
            cost_estimate=cost_estimate,
            alert_level=alert_level,
            days_remaining=days_remaining
        )

    def check_and_record_alerts(self, status: Optional[BudgetStatus] = None) -> Optional[str]:
        """
        Check if current usage crosses alert threshold and record alert

        Args:
            status: Optional pre-computed BudgetStatus (will fetch if None)

        Returns:
            Alert message if threshold crossed, None otherwise
        """
        if status is None:
            status = self.get_current_usage()

        # Check if we've crossed a threshold since last alert
        for threshold in sorted(self.alert_thresholds):
            if status.percentage_used >= threshold:
                # Check if we already alerted at this level for current period
                period_key = self._get_period_key(date.today())

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM alert_history
                        WHERE alert_level = ?
                        AND timestamp >= ?
                    """, (f"{threshold}%", status.period_start))

                    count = cursor.fetchone()[0]

                    if count == 0:
                        # New alert! Record it
                        alert_msg = (
                            f"⚠️  Token budget at {status.percentage_used:.1f}% "
                            f"({status.tokens_used:,} / {status.tokens_limit:,} tokens). "
                            f"Estimated cost: ${status.cost_estimate:.2f}"
                        )

                        cursor.execute("""
                            INSERT INTO alert_history
                            (timestamp, alert_level, percentage_used, tokens_used, message)
                            VALUES (?, ?, ?, ?, ?)
                        """, (datetime.now().isoformat(), f"{threshold}%",
                              status.percentage_used, status.tokens_used, alert_msg))
                        conn.commit()

                        return alert_msg

        return None

    def get_usage_history(self, days: int = 30) -> List[Dict]:
        """
        Get usage history for the last N days

        Args:
            days: Number of days to look back

        Returns:
            List of usage records as dictionaries
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    DATE(timestamp) as date,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimate) as cost,
                    COUNT(*) as worker_count
                FROM usage_records
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (cutoff_iso,))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_worker_usage(self, period_current: bool = True) -> List[Dict]:
        """
        Get usage breakdown by worker

        Args:
            period_current: If True, only current period; else all time

        Returns:
            List of worker usage statistics
        """
        period_key = self._get_period_key(date.today()) if period_current else None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    worker_id,
                    issue_number,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimate) as cost,
                    MAX(timestamp) as last_activity
                FROM usage_records
            """

            if period_key:
                query += " WHERE period_month = ?"
                params = (period_key,)
            else:
                params = ()

            query += " GROUP BY worker_id, issue_number ORDER BY tokens DESC"

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def export_usage_report(self) -> Dict:
        """
        Export comprehensive usage report

        Returns:
            Dictionary with complete usage statistics
        """
        from dataclasses import asdict

        status = self.get_current_usage()
        history = self.get_usage_history(30)
        workers = self.get_worker_usage(period_current=True)

        return {
            'current_status': asdict(status),
            'daily_history_30d': history,
            'worker_breakdown': workers,
            'generated_at': datetime.now().isoformat()
        }
