#!/usr/bin/env python3
"""Budget monitoring module for Circuit-Synth dashboard integration"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class AlertLevel(str, Enum):
    """Budget alert severity levels"""
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


@dataclass
class TokenUsage:
    """Token usage information"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    timestamp: str
    worker_id: str
    issue_number: str


@dataclass
class BudgetAlert:
    """Budget alert notification"""
    level: AlertLevel
    message: str
    percentage_used: float
    tokens_used: int
    tokens_limit: int
    timestamp: str
    cost_estimate: float


class BudgetMonitor:
    """Monitor token budget and trigger alerts

    This is a simplified monitoring interface that wraps BudgetTracker
    for dashboard integration purposes.
    """

    def __init__(self, tracker=None):
        """Initialize monitor with optional tracker instance"""
        self.tracker = tracker
        self._alerts: List[BudgetAlert] = []

    def check_usage(self) -> Optional[BudgetAlert]:
        """Check current usage and return alert if threshold exceeded"""
        if not self.tracker:
            return None

        status = self.tracker.get_current_usage()

        if status.alert_level:
            alert_level_map = {
                'warning': AlertLevel.WARNING,
                'critical': AlertLevel.CRITICAL,
                'exceeded': AlertLevel.EXCEEDED
            }

            alert = BudgetAlert(
                level=alert_level_map.get(status.alert_level, AlertLevel.NONE),
                message=f"Token budget at {status.percentage_used:.1f}%",
                percentage_used=status.percentage_used,
                tokens_used=status.tokens_used,
                tokens_limit=status.tokens_limit,
                timestamp=status.period_start,
                cost_estimate=status.cost_estimate
            )
            self._alerts.append(alert)
            return alert

        return None

    def get_recent_alerts(self, limit: int = 10) -> List[BudgetAlert]:
        """Get recent alerts"""
        return self._alerts[-limit:]

    def clear_alerts(self):
        """Clear all cached alerts"""
        self._alerts.clear()
