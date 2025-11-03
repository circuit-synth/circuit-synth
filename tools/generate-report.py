#!/usr/bin/env python3
"""
Generate historical reports from TAC-8 logs for transparency and reproducibility.

Usage:
    # Full historical report
    ./tools/generate-report.py --all

    # Specific date
    ./tools/generate-report.py --date 2025-11-03

    # Specific task
    ./tools/generate-report.py --task gh-450

    # Timeline view
    ./tools/generate-report.py --timeline

    # Decision log (what coordinator decided and why)
    ./tools/generate-report.py --decisions
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

LOGS_DIR = Path("/home/shane/Desktop/circuit-synth/logs")
COORD_LOG = Path("/home/shane/Desktop/circuit-synth/coordinator.log")

def parse_conversation_log(log_file: Path) -> Dict[str, Any]:
    """Parse a conversation log and extract key information."""
    events = []

    try:
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        return {"error": str(e), "file": str(log_file)}

    if not events:
        return {"error": "No events", "file": str(log_file)}

    # Extract metadata
    system_event = next((e for e in events if e.get("type") == "system"), {})

    # Count messages and tool calls
    user_msgs = [e for e in events if e.get("type") == "user"]
    assistant_msgs = [e for e in events if e.get("type") == "assistant"]

    # Extract tool calls and their results
    tool_calls = []
    for msg in assistant_msgs:
        message = msg.get("message", {})
        content = message.get("content", [])
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_calls.append({
                    "tool": item.get("name"),
                    "params": item.get("input", {})
                })

    # Calculate tokens
    total_in = sum(
        msg.get("message", {}).get("usage", {}).get("input_tokens", 0)
        for msg in assistant_msgs
    )
    total_out = sum(
        msg.get("message", {}).get("usage", {}).get("output_tokens", 0)
        for msg in assistant_msgs
    )

    # Get timestamps
    start_time = system_event.get("timestamp")
    end_time = events[-1].get("timestamp") if events else None

    return {
        "task_id": log_file.stem,
        "session_id": system_event.get("session_id"),
        "model": system_event.get("model"),
        "cwd": system_event.get("cwd"),
        "start_time": start_time,
        "end_time": end_time,
        "total_events": len(events),
        "user_messages": len(user_msgs),
        "assistant_messages": len(assistant_msgs),
        "tool_calls": len(tool_calls),
        "tools_used": list(set(tc["tool"] for tc in tool_calls)),
        "tokens_in": total_in,
        "tokens_out": total_out,
        "tokens_total": total_in + total_out,
        "file_size": log_file.stat().st_size,
        "modified": datetime.fromtimestamp(log_file.stat().st_mtime),
    }

def generate_full_report():
    """Generate comprehensive report of all historical data."""
    print("=" * 80)
    print("TAC-8 HISTORICAL REPORT - COMPLETE TRANSPARENCY")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Parse all conversation logs
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))
    reports = []

    for log_file in log_files:
        report = parse_conversation_log(log_file)
        reports.append(report)

    # Summary
    print("SUMMARY")
    print("-" * 80)
    print(f"Total tasks logged: {len(reports)}")

    valid_reports = [r for r in reports if "error" not in r]
    if valid_reports:
        total_tokens = sum(r.get("tokens_total", 0) for r in valid_reports)
        total_cost = total_tokens * 0.000015  # Rough estimate

        print(f"Total events: {sum(r.get('total_events', 0) for r in valid_reports)}")
        print(f"Total tokens: {total_tokens:,}")
        print(f"Estimated cost: ${total_cost:.4f}")
        print(f"Total tool calls: {sum(r.get('tool_calls', 0) for r in valid_reports)}")

    print()

    # Timeline view
    print("TIMELINE (Most Recent First)")
    print("-" * 80)
    print(f"{'Task':<12} {'Modified':<20} {'Events':<8} {'Tokens':<12} {'Tools':<6}")
    print("-" * 80)

    for report in sorted(valid_reports, key=lambda r: r.get('modified', datetime.min), reverse=True):
        task_id = report.get('task_id', 'unknown')
        modified = report.get('modified', datetime.min).strftime('%Y-%m-%d %H:%M:%S')
        events = report.get('total_events', 0)
        tokens = report.get('tokens_total', 0)
        tools = report.get('tool_calls', 0)

        print(f"{task_id:<12} {modified:<20} {events:<8} {tokens:<12,} {tools:<6}")

    print()

    # Detailed task reports
    print("DETAILED TASK REPORTS")
    print("=" * 80)

    for report in sorted(valid_reports, key=lambda r: r.get('modified', datetime.min), reverse=True):
        if "error" in report:
            print(f"\n{report['task_id']}: ERROR - {report['error']}")
            continue

        print(f"\n{report['task_id']}")
        print("-" * 80)
        print(f"Session: {report.get('session_id', 'N/A')[:16]}...")
        print(f"Model: {report.get('model', 'N/A')}")
        print(f"Modified: {report.get('modified', 'N/A')}")
        print(f"Events: {report.get('total_events', 0)} ({report.get('user_messages', 0)} user, {report.get('assistant_messages', 0)} assistant)")
        print(f"Tokens: {report.get('tokens_in', 0):,} in, {report.get('tokens_out', 0):,} out, {report.get('tokens_total', 0):,} total")
        print(f"Tool calls: {report.get('tool_calls', 0)}")
        if report.get('tools_used'):
            print(f"Tools used: {', '.join(report.get('tools_used', []))}")

    print()
    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)

def generate_timeline():
    """Generate timeline view of all activity."""
    print("=" * 80)
    print("TAC-8 ACTIVITY TIMELINE")
    print("=" * 80)
    print()

    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))

    # Group by date
    by_date = defaultdict(list)

    for log_file in log_files:
        report = parse_conversation_log(log_file)
        if "error" not in report and report.get('modified'):
            date = report['modified'].strftime('%Y-%m-%d')
            by_date[date].append(report)

    # Print timeline
    for date in sorted(by_date.keys(), reverse=True):
        tasks = by_date[date]
        total_tokens = sum(t.get('tokens_total', 0) for t in tasks)
        total_events = sum(t.get('total_events', 0) for t in tasks)

        print(f"\n{date}")
        print("-" * 80)
        print(f"Tasks: {len(tasks)}")
        print(f"Total events: {total_events}")
        print(f"Total tokens: {total_tokens:,}")
        print()

        for task in sorted(tasks, key=lambda t: t.get('modified', datetime.min)):
            time = task['modified'].strftime('%H:%M:%S')
            print(f"  {time} - {task['task_id']}: {task.get('total_events', 0)} events, {task.get('tokens_total', 0):,} tokens")

def generate_task_report(task_id: str):
    """Generate detailed report for specific task."""
    log_file = LOGS_DIR / f"{task_id}.jsonl"

    if not log_file.exists():
        print(f"Error: Log file not found for {task_id}")
        return

    print("=" * 80)
    print(f"TASK REPORT: {task_id}")
    print("=" * 80)
    print()

    report = parse_conversation_log(log_file)

    if "error" in report:
        print(f"ERROR: {report['error']}")
        return

    # Metadata
    print("METADATA")
    print("-" * 80)
    print(f"Task ID: {report['task_id']}")
    print(f"Session ID: {report.get('session_id', 'N/A')}")
    print(f"Model: {report.get('model', 'N/A')}")
    print(f"Working Directory: {report.get('cwd', 'N/A')}")
    print(f"Modified: {report.get('modified', 'N/A')}")
    print(f"File Size: {report.get('file_size', 0) / 1024:.1f} KB")
    print()

    # Activity
    print("ACTIVITY")
    print("-" * 80)
    print(f"Total Events: {report.get('total_events', 0)}")
    print(f"User Messages: {report.get('user_messages', 0)}")
    print(f"Assistant Messages: {report.get('assistant_messages', 0)}")
    print(f"Tool Calls: {report.get('tool_calls', 0)}")
    print()

    # Tools used
    if report.get('tools_used'):
        print("TOOLS USED")
        print("-" * 80)
        for tool in sorted(report['tools_used']):
            print(f"  - {tool}")
        print()

    # Token usage
    print("TOKEN USAGE")
    print("-" * 80)
    print(f"Input Tokens: {report.get('tokens_in', 0):,}")
    print(f"Output Tokens: {report.get('tokens_out', 0):,}")
    print(f"Total Tokens: {report.get('tokens_total', 0):,}")
    print(f"Estimated Cost: ${report.get('tokens_total', 0) * 0.000015:.4f}")
    print()

    # View full conversation
    print("To view full conversation:")
    print(f"  ./tools/view-conversation.py logs/{task_id}.jsonl")
    print()

def main():
    args = sys.argv[1:]

    if not args or "--all" in args:
        generate_full_report()
    elif "--timeline" in args:
        generate_timeline()
    elif "--task" in args:
        idx = args.index("--task")
        if idx + 1 < len(args):
            generate_task_report(args[idx + 1])
        else:
            print("Error: --task requires task ID (e.g., gh-450)")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
