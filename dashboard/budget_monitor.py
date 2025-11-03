#!/usr/bin/env python3
"""
Budget Monitor - Token budget tracking and alerts for Claude API Dashboard

Provides comprehensive token budget monitoring including:
- Current monthly usage vs budget
- Color-coded alert levels (green/yellow/orange/red)
- Historical usage trends
- Integration with existing token_budget.py module

Usage:
    from dashboard.budget_monitor import BudgetMonitor

    monitor = BudgetMonitor()
    status = monitor.get_budget_status()
    print(f"Budget: {status['percentage']}% used ({status['alert_level']})")
"""

import sys
from pathlib import Path

# Add adws module to path for token_budget import
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.token_budget import (
    parse_token_budget_config,
    calculate_budget_status,
    get_monthly_token_usage
)


class BudgetMonitor:
    """Monitor and track token budget usage against monthly limits
    
    Integrates with existing token_budget.py module to provide
    dashboard-friendly interface for budget monitoring.
    """

    def __init__(self, repo_root=None):
        """
        Initialize BudgetMonitor

        Args:
            repo_root: Repository root directory (defaults to auto-detect)
        """
        if repo_root is None:
            # Auto-detect: assume we're in dashboard/ directory
            repo_root = Path(__file__).parent.parent

        self.repo_root = Path(repo_root)
        self.env_file = self.repo_root / '.env'
        self.log_dir = self.repo_root / 'logs' / 'api'

    def get_budget_status(self):
        """
        Get current budget status with usage and alert level

        Returns:
            Dictionary containing:
            - monthly_budget: Configured monthly budget
            - tokens_used: Tokens used this month
            - percentage: Percentage of budget used
            - alert_level: 'green', 'yellow', 'orange', or 'red'
            - remaining: Tokens remaining in budget
        """
        # Parse budget configuration
        config = parse_token_budget_config(self.env_file)
        if not config:
            # Default budget if not configured
            monthly_budget = 1000000
        else:
            monthly_budget = config['monthly_budget']

        # Get current usage
        tokens_used = get_monthly_token_usage(self.log_dir)

        # Calculate budget status
        status = calculate_budget_status(
            tokens_used=tokens_used,
            monthly_budget=monthly_budget
        )

        return status

    def format_budget_display(self, status):
        """
        Format budget status for text display

        Args:
            status: Budget status dictionary from get_budget_status()

        Returns:
            Formatted string for display
        """
        alert_emoji = {
            'green': '🟢',
            'yellow': '🟡',
            'orange': '🟠',
            'red': '🔴'
        }

        emoji = alert_emoji.get(status['alert_level'], '⚪')

        return f"""
Token Budget Status {emoji}

Budget:    {status['monthly_budget']:,} tokens/month
Used:      {status['tokens_used']:,} tokens ({status['percentage']}%)
Remaining: {status['remaining']:,} tokens
Alert:     {status['alert_level'].upper()}
"""
