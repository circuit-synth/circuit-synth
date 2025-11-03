#!/usr/bin/env python3
"""
Circuit-Synth Token Budget Dashboard

Displays real-time token budget monitoring with:
- Current usage vs limit
- Visual indicators (green/yellow/red)
- Alert notifications
- Usage trends
- PM Agent budget decisions
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.dashboard_data import DashboardData


def format_number(num: int) -> str:
    """Format number with commas"""
    return f"{num:,}"


def get_progress_bar(percentage: float, width: int = 40, color: str = 'green') -> str:
    """Create a colored progress bar

    Args:
        percentage: Percentage value (0-100)
        width: Width of progress bar in characters
        color: Color code (green/yellow/red)
    """
    filled_width = int((percentage / 100) * width)
    empty_width = width - filled_width

    # Color codes
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'reset': '\033[0m'
    }

    color_code = colors.get(color, '')
    reset = colors['reset']

    bar = color_code + '█' * filled_width + reset + '░' * empty_width
    return f"[{bar}] {percentage:.1f}%"


def display_budget_card(dashboard: DashboardData):
    """Display budget status card"""
    data = dashboard.get_budget_card_data()
    status = dashboard.get_color_coded_status()
    alert = dashboard.get_alert_status()

    print("=" * 70)
    print("📊  TOKEN BUDGET STATUS")
    print("=" * 70)
    print()

    # Status badge
    badge_colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'reset': '\033[0m'
    }
    color = badge_colors.get(status['color'], '')
    reset = badge_colors['reset']

    print(f"Status: {color}{status['badge']} {status['status_text']}{reset}")
    print(f"Period: {data['period_start']} to {data['period_end']} ({data['days_remaining']} days remaining)")
    print()

    # Usage numbers
    print(f"Tokens Used:  {format_number(data['tokens_used'])}")
    print(f"Token Limit:  {format_number(data['tokens_limit'])}")
    print(f"Available:    {format_number(data['tokens_limit'] - data['tokens_used'])}")
    print()

    # Progress bar
    progress_bar = get_progress_bar(data['percentage_used'], width=50, color=status['color'])
    print(f"Usage: {progress_bar}")
    print()

    # Cost estimate
    print(f"Estimated Cost: ${data['cost_estimate']:.2f}")
    print()

    # Alert message if present
    if alert['has_alert']:
        alert_colors = {
            'warning': '\033[93m⚠',
            'critical': '\033[91m✗',
            'exceeded': '\033[91m✗'
        }
        alert_icon = alert_colors.get(alert['alert_level'], '⚠')
        print(f"{alert_icon}  ALERT: {alert['message']}\033[0m")
        print()


def display_usage_trends(dashboard: DashboardData, days: int = 7):
    """Display recent usage trends"""
    trends = dashboard.get_usage_trends(days=days)

    if not trends:
        print("No usage data available.")
        return

    print("=" * 70)
    print(f"📈  USAGE TRENDS (Last {days} Days)")
    print("=" * 70)
    print()

    print(f"{'Date':<12} {'Tokens':>15} {'Cost':>10} {'Workers':>10}")
    print("-" * 70)

    for entry in reversed(trends[:days]):  # Show most recent first
        date = entry['date']
        tokens = format_number(entry['tokens'])
        cost = f"${entry['cost']:.2f}"
        workers = entry['worker_count']
        print(f"{date:<12} {tokens:>15} {cost:>10} {workers:>10}")

    print()


def display_pm_agent_decision(dashboard: DashboardData):
    """Display PM Agent budget decision"""
    decision = dashboard.get_pm_agent_budget_decision()

    print("=" * 70)
    print("🤖  PM AGENT BUDGET DECISION")
    print("=" * 70)
    print()

    can_proceed = decision['can_proceed']
    icon = '\033[92m✓\033[0m' if can_proceed else '\033[91m✗\033[0m'

    print(f"Can Proceed: {icon} {'YES' if can_proceed else 'NO'}")
    print(f"Reason: {decision['reason']}")
    print(f"Tokens Available: {format_number(decision['tokens_available'])}")
    print(f"Usage: {decision['percentage_used']:.1f}%")
    print()


def display_alert_thresholds(dashboard: DashboardData):
    """Display configured alert thresholds"""
    thresholds = dashboard.tracker.alert_thresholds

    print("=" * 70)
    print("⚙️   ALERT CONFIGURATION")
    print("=" * 70)
    print()

    print(f"Monthly Limit: {format_number(dashboard.monthly_limit)} tokens")
    print(f"Cost per Million: ${dashboard.tracker.cost_per_million:.2f}")
    print(f"Reset Day: Day {dashboard.tracker.reset_day} of month")
    print()
    print(f"Alert Thresholds: {', '.join(f'{t}%' for t in thresholds)}")
    print()


def main():
    """Main dashboard entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Circuit-Synth Token Budget Dashboard')
    parser.add_argument('--db', type=str, default='adws/budget.db',
                       help='Path to budget database (default: adws/budget.db)')
    parser.add_argument('--trends-days', type=int, default=7,
                       help='Number of days to show in trends (default: 7)')
    parser.add_argument('--compact', action='store_true',
                       help='Show compact view (budget card only)')
    parser.add_argument('--from-env', action='store_true',
                       help='Load configuration from environment variables')

    args = parser.parse_args()

    # Resolve database path
    db_path = Path(args.db)
    if not db_path.is_absolute():
        # Make it relative to repo root, not script location
        repo_root = Path(__file__).parent.parent
        db_path = repo_root / args.db

    # Initialize dashboard
    if args.from_env:
        dashboard = DashboardData.from_env(db_path)
    else:
        # Use default configuration
        dashboard = DashboardData(db_path, monthly_limit=1000000)

    # Display dashboard
    print()
    print(f"Circuit-Synth Token Budget Dashboard")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Main budget card (always shown)
    display_budget_card(dashboard)

    if not args.compact:
        # PM Agent decision
        display_pm_agent_decision(dashboard)

        # Usage trends
        display_usage_trends(dashboard, days=args.trends_days)

        # Alert configuration
        display_alert_thresholds(dashboard)

    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
