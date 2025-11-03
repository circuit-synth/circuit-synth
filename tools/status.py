#!/usr/bin/env python3
"""
Circuit-Synth Coordinator Status Dashboard

Real-time monitoring dashboard showing:
- Active workers and task queue
- Token budget usage and alerts
- System health metrics
- Historical trends
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from adws.budget_tracker import BudgetTracker, BudgetStatus
    from adws.budget_monitor import BudgetMonitor
    BUDGET_AVAILABLE = True
except ImportError:
    BUDGET_AVAILABLE = False


class Dashboard:
    """Real-time coordinator status dashboard"""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.tasks_file = self.repo_root / "tasks.md"
        self.metrics_file = self.repo_root / "adws" / "metrics.json"
        self.budget_db = self.repo_root / "adws" / "budget.db"

        # Initialize budget tracker if available
        self.budget_tracker = None
        if BUDGET_AVAILABLE and self.budget_db.exists():
            try:
                # Get monthly limit from env or default
                import os
                monthly_limit = int(os.getenv('MONTHLY_TOKEN_BUDGET', '10000000'))
                self.budget_tracker = BudgetTracker(
                    db_path=self.budget_db,
                    monthly_limit=monthly_limit
                )
            except Exception as e:
                print(f"⚠️  Failed to initialize budget tracker: {e}")

    def get_task_counts(self) -> dict:
        """Count tasks by status from tasks.md"""
        if not self.tasks_file.exists():
            return {
                'pending': 0,
                'active': 0,
                'completed': 0,
                'failed': 0,
                'blocked': 0
            }

        content = self.tasks_file.read_text()

        return {
            'pending': content.count('[] gh-'),
            'active': content.count('[🟡 w-'),
            'completed': content.count('[✅'),
            'failed': content.count('[❌'),
            'blocked': content.count('[⏰')
        }

    def get_metrics(self) -> Optional[dict]:
        """Load coordinator metrics if available"""
        if not self.metrics_file.exists():
            return None

        try:
            return json.loads(self.metrics_file.read_text())
        except Exception:
            return None

    def get_budget_status(self) -> Optional[BudgetStatus]:
        """Get current budget status"""
        if not self.budget_tracker:
            return None

        try:
            return self.budget_tracker.get_current_usage()
        except Exception as e:
            print(f"⚠️  Error fetching budget status: {e}")
            return None

    def format_number(self, num: int) -> str:
        """Format number with commas"""
        return f"{num:,}"

    def get_alert_symbol(self, alert_level: Optional[str]) -> str:
        """Get symbol for alert level"""
        if not alert_level:
            return "🟢"
        elif alert_level == 'warning':
            return "🟡"
        elif alert_level == 'critical':
            return "🟠"
        elif alert_level == 'exceeded':
            return "🔴"
        return "⚪"

    def render_budget_card(self, status: BudgetStatus) -> list:
        """Render budget status card"""
        lines = []

        # Header with alert symbol
        symbol = self.get_alert_symbol(status.alert_level)
        lines.append(f"\n{symbol} TOKEN BUDGET")
        lines.append("─" * 50)

        # Usage bar
        percentage = min(status.percentage_used, 100)
        bar_width = 30
        filled = int((percentage / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        lines.append(f"Usage: [{bar}] {status.percentage_used:.1f}%")
        lines.append(f"Tokens: {self.format_number(status.tokens_used)} / {self.format_number(status.tokens_limit)}")
        lines.append(f"Cost Estimate: ${status.cost_estimate:.2f}")
        lines.append(f"Period: {status.period_start} to {status.period_end}")
        lines.append(f"Days Remaining: {status.days_remaining}")

        # Alert message
        if status.alert_level:
            if status.alert_level == 'exceeded':
                lines.append("\n⚠️  BUDGET EXCEEDED! Consider pausing workers.")
            elif status.alert_level == 'critical':
                lines.append("\n⚠️  CRITICAL: Budget nearly exhausted")
            elif status.alert_level == 'warning':
                lines.append("\n⚠️  WARNING: Approaching budget limit")

        return lines

    def render_task_summary(self, counts: dict) -> list:
        """Render task summary card"""
        lines = []
        lines.append("\n📋 TASK QUEUE")
        lines.append("─" * 50)
        lines.append(f"Pending:   {counts['pending']}")
        lines.append(f"Active:    {counts['active']}")
        lines.append(f"Completed: {counts['completed']}")
        lines.append(f"Failed:    {counts['failed']}")
        lines.append(f"Blocked:   {counts['blocked']}")

        total = sum(counts.values())
        lines.append(f"\nTotal: {total}")

        return lines

    def render_metrics_card(self, metrics: Optional[dict]) -> list:
        """Render system metrics card"""
        lines = []
        lines.append("\n⚙️  SYSTEM METRICS")
        lines.append("─" * 50)

        if not metrics:
            lines.append("No metrics available")
            return lines

        health = metrics.get('health', 'unknown').upper()
        health_symbol = {
            'OK': '🟢',
            'WARNING': '🟡',
            'DEGRADED': '🟠',
            'ERROR': '🔴'
        }.get(health, '⚪')

        lines.append(f"Health: {health_symbol} {health}")
        lines.append(f"Workers Launched: {metrics.get('workers_launched', 0)}")
        lines.append(f"Workers Completed: {metrics.get('workers_completed', 0)}")
        lines.append(f"Workers Failed: {metrics.get('workers_failed', 0)}")
        lines.append(f"PRs Created: {metrics.get('prs_created', 0)}")
        lines.append(f"Worktree Errors: {metrics.get('worktree_errors', 0)}")

        if metrics.get('last_update'):
            lines.append(f"\nLast Update: {metrics['last_update']}")

        return lines

    def render_usage_history(self) -> list:
        """Render recent usage history"""
        if not self.budget_tracker:
            return []

        lines = []
        lines.append("\n📊 USAGE HISTORY (Last 7 days)")
        lines.append("─" * 50)

        try:
            history = self.budget_tracker.get_usage_history(days=7)

            if not history:
                lines.append("No usage history available")
                return lines

            for entry in history[:7]:  # Show last 7 days
                date = entry['date']
                tokens = self.format_number(entry['tokens'])
                cost = entry['cost']
                workers = entry['worker_count']
                lines.append(f"{date}: {tokens} tokens, ${cost:.2f}, {workers} workers")

        except Exception as e:
            lines.append(f"Error loading history: {e}")

        return lines

    def render(self) -> str:
        """Render complete dashboard"""
        lines = []

        # Header
        lines.append("=" * 50)
        lines.append("  CIRCUIT-SYNTH COORDINATOR DASHBOARD")
        lines.append("=" * 50)
        lines.append(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Task Summary
        counts = self.get_task_counts()
        lines.extend(self.render_task_summary(counts))

        # Budget Status
        budget_status = self.get_budget_status()
        if budget_status:
            lines.extend(self.render_budget_card(budget_status))
        else:
            lines.append("\n💰 TOKEN BUDGET")
            lines.append("─" * 50)
            lines.append("Budget tracking not available")
            if not BUDGET_AVAILABLE:
                lines.append("(budget_tracker module not found)")

        # System Metrics
        metrics = self.get_metrics()
        lines.extend(self.render_metrics_card(metrics))

        # Usage History
        if budget_status:
            lines.extend(self.render_usage_history())

        # Footer
        lines.append("\n" + "=" * 50)

        return "\n".join(lines)


def main():
    """Main entry point"""
    dashboard = Dashboard()
    print(dashboard.render())


if __name__ == '__main__':
    main()
