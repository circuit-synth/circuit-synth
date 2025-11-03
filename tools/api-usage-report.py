#!/usr/bin/env python3
"""
API Usage Report - Analyze Claude API usage logs

Usage:
    ./tools/api-usage-report.py                    # Today's summary
    ./tools/api-usage-report.py --date 2025-11-02  # Specific date
    ./tools/api-usage-report.py --week             # Last 7 days
    ./tools/api-usage-report.py --month            # Last 30 days
    ./tools/api-usage-report.py --detail           # Show individual calls
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.api_logger import ClaudeAPILogger


def print_summary(summary: dict):
    """Print formatted summary"""
    print(f"\n📊 API Usage Summary - {summary['date']}")
    print("=" * 60)
    print(f"Total Calls:       {summary['total_calls']:>8}")
    print(f"  ✓ Successful:    {summary['successful_calls']:>8}")
    print(f"  ✗ Failed:        {summary['failed_calls']:>8}")
    print()
    print(f"Tokens Used:       {summary['total_tokens']:>8,}")
    print(f"  → Input:         {summary['total_tokens_input']:>8,}")
    print(f"  → Output:        {summary['total_tokens_output']:>8,}")
    print()
    print(f"Cost (estimated):  ${summary['total_cost_usd']:>8.4f}")
    print()
    print(f"Avg Duration:      {summary['avg_duration_seconds']:>8.2f}s")
    print(f"Avg Tokens/sec:    {summary['avg_tokens_per_second']:>8.2f}")
    print()

    if summary['models']:
        print("By Model:")
        print("-" * 60)
        for model, stats in summary['models'].items():
            print(f"  {model}")
            print(f"    Calls:  {stats['calls']:>6}")
            print(f"    Tokens: {stats['tokens']:>6,}")
            print(f"    Cost:   ${stats['cost']:>6.4f}")
        print()


def print_detail(log_dir: Path, date: str):
    """Print detailed call information"""
    log_file = log_dir / f"api-calls-{date}.jsonl"
    if not log_file.exists():
        print(f"No log file for {date}")
        return

    print(f"\n📋 Detailed Calls - {date}")
    print("=" * 80)

    with open(log_file, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                call = json.loads(line)
                status = "✓" if call.get('success') else "✗"
                timestamp = call.get('timestamp', '').split('T')[1][:8] if call.get('timestamp') else 'N/A'
                task_id = call.get('task_id', 'N/A')
                worker_id = call.get('worker_id', 'N/A')
                tokens = call.get('tokens_total', 0)
                duration = call.get('duration_seconds', 0)
                cost = call.get('estimated_cost_usd', 0)

                print(f"{i:3}. [{status}] {timestamp} | {task_id:10} | {worker_id:10}")
                print(f"     Tokens: {tokens:>6,} | Duration: {duration:>6.1f}s | Cost: ${cost:.4f}")

                if not call.get('success') and call.get('error_message'):
                    print(f"     Error: {call['error_message'][:60]}")

                print()

            except json.JSONDecodeError:
                continue


def print_week_summary(log_dir: Path, days: int = 7):
    """Print summary for multiple days"""
    logger = ClaudeAPILogger(log_dir)

    print(f"\n📈 Last {days} Days Summary")
    print("=" * 80)

    total_calls = 0
    total_tokens = 0
    total_cost = 0.0

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        summary = logger.get_daily_summary(date)

        if summary['total_calls'] == 0:
            continue

        total_calls += summary['total_calls']
        total_tokens += summary['total_tokens']
        total_cost += summary['total_cost_usd']

        print(f"{date}  |  Calls: {summary['total_calls']:>4}  |  "
              f"Tokens: {summary['total_tokens']:>8,}  |  "
              f"Cost: ${summary['total_cost_usd']:>7.4f}")

    print("-" * 80)
    print(f"{'TOTAL':10}  |  Calls: {total_calls:>4}  |  "
          f"Tokens: {total_tokens:>8,}  |  "
          f"Cost: ${total_cost:>7.4f}")
    print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze Claude API usage')
    parser.add_argument('--date', help='Specific date (YYYY-MM-DD)')
    parser.add_argument('--week', action='store_true', help='Last 7 days')
    parser.add_argument('--month', action='store_true', help='Last 30 days')
    parser.add_argument('--detail', action='store_true', help='Show detailed calls')
    parser.add_argument('--log-dir', default='logs/api', help='Log directory')

    args = parser.parse_args()

    log_dir = Path(__file__).parent.parent / args.log_dir
    logger = ClaudeAPILogger(log_dir)

    if args.week:
        print_week_summary(log_dir, days=7)
    elif args.month:
        print_week_summary(log_dir, days=30)
    else:
        date = args.date or datetime.now().strftime('%Y-%m-%d')
        summary = logger.get_daily_summary(date)
        print_summary(summary)

        if args.detail:
            print_detail(log_dir, date)


if __name__ == '__main__':
    main()
