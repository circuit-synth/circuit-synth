#!/usr/bin/env python3
"""Dashboard data module for Circuit-Synth token budget monitoring"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

from adws.budget_tracker import BudgetTracker, BudgetStatus


class DashboardData:
    """Provides formatted data for dashboard UI"""

    def __init__(self, db_path: Path, monthly_limit: int = 1000000,
                 alert_thresholds: Optional[List[int]] = None,
                 cost_per_million: float = 3.00,
                 reset_day: int = 1):
        """Initialize dashboard data provider

        Args:
            db_path: Path to SQLite database
            monthly_limit: Monthly token budget limit
            alert_thresholds: Alert thresholds as percentages (default: [75, 90, 95])
            cost_per_million: Cost per million tokens
            reset_day: Day of month when budget resets
        """
        self.monthly_limit = monthly_limit
        self.tracker = BudgetTracker(
            db_path=db_path,
            monthly_limit=monthly_limit,
            alert_thresholds=alert_thresholds,
            cost_per_million=cost_per_million,
            reset_day=reset_day
        )

    @classmethod
    def from_env(cls, db_path: Path) -> 'DashboardData':
        """Create dashboard from environment configuration

        Reads configuration from environment variables:
        - MONTHLY_TOKEN_BUDGET: Monthly token limit (default: 1000000)
        - COST_PER_MILLION: Cost per million tokens (default: 3.00)
        - BUDGET_RESET_DAY: Day of month to reset (default: 1)
        - ALERT_THRESHOLDS: Comma-separated percentages (default: 75,90,95)
        """
        monthly_limit = int(os.getenv('MONTHLY_TOKEN_BUDGET', '1000000'))
        cost_per_million = float(os.getenv('COST_PER_MILLION', '3.00'))
        reset_day = int(os.getenv('BUDGET_RESET_DAY', '1'))

        alert_thresholds_str = os.getenv('ALERT_THRESHOLDS', '75,90,95')
        alert_thresholds = [int(x.strip()) for x in alert_thresholds_str.split(',')]

        return cls(
            db_path=db_path,
            monthly_limit=monthly_limit,
            alert_thresholds=alert_thresholds,
            cost_per_million=cost_per_million,
            reset_day=reset_day
        )

    def get_budget_card_data(self) -> Dict:
        """Get budget status data formatted for dashboard card

        Returns:
            Dict with keys: tokens_used, tokens_limit, percentage_used,
                           cost_estimate, alert_level, period_start, period_end,
                           days_remaining
        """
        status = self.tracker.get_current_usage()
        return asdict(status)

    def get_alert_status(self) -> Dict:
        """Get current alert status

        Returns:
            Dict with keys: has_alert, alert_level, percentage_used, message
        """
        status = self.tracker.get_current_usage()

        has_alert = status.alert_level is not None
        message = None

        if has_alert:
            message = (
                f"Token budget at {status.percentage_used:.1f}% "
                f"({status.tokens_used:,} / {status.tokens_limit:,} tokens). "
                f"Estimated cost: ${status.cost_estimate:.2f}"
            )

        return {
            'has_alert': has_alert,
            'alert_level': status.alert_level,
            'percentage_used': status.percentage_used,
            'message': message
        }

    def get_color_coded_status(self) -> Dict:
        """Get color-coded status for visual indicators

        Returns:
            Dict with keys: color (green/yellow/red), badge (✓/⚠/✗),
                           status_text
        """
        status = self.tracker.get_current_usage()

        if status.alert_level == 'exceeded':
            color = 'red'
            badge = '✗'
            status_text = 'Budget Exceeded'
        elif status.alert_level == 'critical':
            color = 'red'
            badge = '✗'
            status_text = 'Critical'
        elif status.alert_level == 'warning':
            color = 'yellow'
            badge = '⚠'
            status_text = 'Warning'
        else:
            color = 'green'
            badge = '✓'
            status_text = 'OK'

        return {
            'color': color,
            'badge': badge,
            'status_text': status_text,
            'percentage_used': status.percentage_used
        }

    def get_usage_trends(self, days: int = 30) -> List[Dict]:
        """Get usage trends for visualization

        Args:
            days: Number of days of history to retrieve

        Returns:
            List of dicts with daily usage data
        """
        return self.tracker.get_usage_history(days=days)

    def get_pm_agent_budget_decision(self) -> Dict:
        """Get budget decision for PM Agent

        Returns:
            Dict with keys: can_proceed, reason, tokens_available
        """
        status = self.tracker.get_current_usage()

        tokens_available = status.tokens_limit - status.tokens_used

        # PM Agent should respect budget constraints
        if status.percentage_used >= 100:
            can_proceed = False
            reason = "Monthly budget exceeded"
        elif status.alert_level == 'critical':
            can_proceed = False
            reason = f"Budget at critical level ({status.percentage_used:.1f}%)"
        elif status.alert_level == 'warning':
            # Can proceed but with caution
            can_proceed = True
            reason = f"Budget at warning level ({status.percentage_used:.1f}%) - proceed with caution"
        else:
            can_proceed = True
            reason = "Budget OK"

        return {
            'can_proceed': can_proceed,
            'reason': reason,
            'tokens_available': tokens_available,
            'percentage_used': status.percentage_used
        }

    def check_and_trigger_alerts(self) -> Optional[str]:
        """Check for budget alerts and return alert message if triggered

        Returns:
            Alert message if new alert triggered, None otherwise
        """
        return self.tracker.check_and_record_alerts()
