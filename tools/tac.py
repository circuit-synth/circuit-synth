#!/usr/bin/env python3
"""
TAC-8 Unified Monitoring and Analysis Tool

Consolidated tool for all TAC-8 operations:
- monitor: Real-time dashboard
- status: Quick summary
- view: View conversation
- report: Historical reports
- export: Export task data
- search: Search conversations
- tokens: Token usage
- errors: Find errors
- timeline: Activity timeline
- list: List all logs
"""

import json
import sys
import time
import subprocess
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
TREES_DIR = PROJECT_ROOT / "trees"
COORD_LOG = PROJECT_ROOT / "coordinator.log"

# ============================================================================
# SHARED UTILITIES
# ============================================================================

def parse_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a JSONL file into a list of events, skipping malformed lines."""
    events = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # Skip malformed lines
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    return events


def get_conversation_summary(events: List[Dict]) -> Dict[str, Any]:
    """Extract metadata and metrics from event stream."""
    summary = {
        "total_events": len(events),
        "user_messages": 0,
        "assistant_messages": 0,
        "tool_calls": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "errors": 0,
        "session_id": None,
        "model": None,
        "cwd": None,
        "start_time": None,
        "end_time": None,
        "tools_used": [],
    }

    tool_set = set()

    for event in events:
        event_type = event.get("type")

        if event_type == "system":
            summary["session_id"] = event.get("session_id")
            summary["model"] = event.get("model")
            summary["cwd"] = event.get("cwd")
            summary["start_time"] = event.get("timestamp")

        elif event_type == "user":
            summary["user_messages"] += 1

        elif event_type == "assistant":
            summary["assistant_messages"] += 1
            message = event.get("message", {})
            usage = message.get("usage", {})
            summary["total_input_tokens"] += usage.get("input_tokens", 0)
            summary["total_output_tokens"] += usage.get("output_tokens", 0)

            # Count tool uses
            content = message.get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    summary["tool_calls"] += 1
                    tool_set.add(item.get("name"))

        elif event_type == "error":
            summary["errors"] += 1

    if events:
        summary["end_time"] = events[-1].get("timestamp")

    summary["tools_used"] = list(tool_set)
    return summary


def estimate_cost(total_tokens: int) -> float:
    """Calculate estimated cost from tokens."""
    return total_tokens * 0.000015


def format_timestamp(ts: float) -> str:
    """Format unix timestamp to readable string."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def clear_screen():
    """Clear terminal screen."""
    os.system('clear')


# ============================================================================
# PROCESS UTILITIES (for monitor command)
# ============================================================================

def get_coordinator_pid():
    """Get coordinator.py PID if running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "coordinator.py"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
    except:
        return []


def get_active_workers():
    """Get active Claude worker processes."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        workers = []
        for line in result.stdout.split('\n'):
            if 'claude -p' in line and 'grep' not in line:
                parts = line.split()
                workers.append({
                    'pid': parts[1],
                    'cpu': parts[2],
                    'mem': parts[3],
                    'time': parts[9]
                })
        return workers
    except:
        return []


def get_recent_logs(minutes=5):
    """Get recently modified log files."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)

    recent = []
    for log_file in LOGS_DIR.glob("gh-*.jsonl"):
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if mtime > cutoff:
            age_seconds = (now - mtime).total_seconds()
            recent.append({
                'task': log_file.stem,
                'age_seconds': age_seconds,
                'size_kb': log_file.stat().st_size / 1024
            })

    return sorted(recent, key=lambda x: x['age_seconds'])


def get_worktrees():
    """Get active worktrees."""
    if not TREES_DIR.exists():
        return []

    trees = []
    for tree_dir in TREES_DIR.iterdir():
        if tree_dir.is_dir():
            # Check for recent activity
            mtime = datetime.fromtimestamp(tree_dir.stat().st_mtime)
            age = datetime.now() - mtime

            # Check if has uncommitted changes
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=tree_dir,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                has_changes = bool(result.stdout.strip())
            except:
                has_changes = False

            trees.append({
                'name': tree_dir.name,
                'age_minutes': age.total_seconds() / 60,
                'has_changes': has_changes
            })

    return trees


def get_token_usage_today():
    """Get token usage for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    api_log = LOGS_DIR / "api" / f"api-calls-{today}.jsonl"

    if not api_log.exists():
        return {"calls": 0, "cost": 0.0, "tokens": 0}

    calls = 0
    cost = 0.0
    tokens = 0

    try:
        with open(api_log, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        calls += 1
                        cost += data.get('estimated_cost_usd', 0.0)
                        tokens += data.get('total_tokens', 0)
                    except:
                        pass
    except:
        pass

    return {"calls": calls, "cost": cost, "tokens": tokens}


# ============================================================================
# VIEW UTILITIES
# ============================================================================

def display_message(msg: Dict[str, Any], index: int):
    """Display a single message in readable format."""
    msg_type = msg.get("type", "unknown")

    # Handle Claude CLI stream-json format
    if msg_type == "system":
        print(f"\n{'='*80}")
        print(f"SYSTEM INFO #{index}")
        print(f"{'='*80}")
        print(f"Session ID: {msg.get('session_id', 'N/A')}")
        print(f"Model: {msg.get('model', 'N/A')}")
        print(f"CWD: {msg.get('cwd', 'N/A')}")
        return

    elif msg_type == "user":
        print(f"\n{'='*80}")
        print(f"USER MESSAGE #{index}")
        print(f"{'='*80}")

        # Get nested message object
        message = msg.get("message", {})

        # Get content
        content = message.get("content", [])
        if isinstance(content, str):
            print(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        print(item.get("text", ""))
                elif isinstance(item, str):
                    print(item)
        else:
            print("<no text>")

        return

    elif msg_type == "assistant":
        print(f"\n{'='*80}")
        print(f"ASSISTANT MESSAGE #{index}")
        print(f"{'='*80}")

        # Get nested message object
        message = msg.get("message", {})

        # Show usage stats if available
        usage = message.get("usage", {})
        if usage:
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            print(f"[Tokens: {input_tokens} in, {output_tokens} out]")

        # Get content array
        content = message.get("content", [])
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type", "")

                if item_type == "text":
                    text = item.get("text", "")
                    print(f"\n{text}")

                elif item_type == "tool_use":
                    tool_name = item.get("name", "unknown")
                    tool_input = item.get("input", {})
                    print(f"\n[TOOL: {tool_name}]")
                    # Show first few params
                    if isinstance(tool_input, dict):
                        for key, val in list(tool_input.items())[:3]:
                            val_str = str(val)[:100]
                            print(f"  {key}: {val_str}...")

                elif item_type == "thinking":
                    thinking_text = item.get("thinking", "")
                    print(f"\n[THINKING]")
                    print(thinking_text[:300] + ("..." if len(thinking_text) > 300 else ""))

        return

    # Handle generic error
    if msg_type == "error":
        print(f"\n{'='*80}")
        print(f"ERROR #{index}")
        print(f"{'='*80}")
        print(msg.get("error", msg))
        return

    # Unknown type - show raw
    print(f"\n{'='*80}")
    print(f"EVENT #{index} - Type: {msg_type}")
    print(f"{'='*80}")
    print(json.dumps(msg, indent=2)[:500])


def display_summary(messages: list):
    """Display conversation summary statistics."""
    summary = get_conversation_summary(messages)

    print(f"\n{'='*80}")
    print("CONVERSATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total events: {summary['total_events']}")
    print(f"System events: {1 if summary['session_id'] else 0}")
    print(f"User messages: {summary['user_messages']}")
    print(f"Assistant messages: {summary['assistant_messages']}")
    print(f"Tool calls: {summary['tool_calls']}")
    print(f"Errors: {summary['errors']}")
    print(f"{'='*80}\n")


# ============================================================================
# SUBCOMMAND FUNCTIONS
# ============================================================================

def cmd_monitor(args):
    """Real-time monitoring dashboard (from monitor-live.py)."""
    try:
        while True:
            clear_screen()

            print("=" * 80)
            print("TAC-8 COORDINATOR - LIVE MONITOR")
            print("=" * 80)
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # Coordinator status
            pids = get_coordinator_pid()
            print("COORDINATOR STATUS")
            print("-" * 80)
            if pids:
                print(f"✅ Running (PID: {', '.join(pids)})")
            else:
                print("❌ Not running")
            print()

            # Active workers
            workers = get_active_workers()
            print("ACTIVE WORKERS")
            print("-" * 80)
            if workers:
                print(f"{'PID':<10} {'CPU%':<8} {'MEM%':<8} {'TIME':<10}")
                for w in workers:
                    print(f"{w['pid']:<10} {w['cpu']:<8} {w['mem']:<8} {w['time']:<10}")
            else:
                print("No active workers")
            print()

            # Recent log activity
            recent = get_recent_logs(minutes=5)
            print("RECENT LOG ACTIVITY (last 5 minutes)")
            print("-" * 80)
            if recent:
                print(f"{'Task':<15} {'Age':<20} {'Size':<10}")
                for log in recent:
                    age_str = f"{int(log['age_seconds'])} seconds ago"
                    print(f"{log['task']:<15} {age_str:<20} {log['size_kb']:>6.1f} KB")
            else:
                print("No recent activity")
            print()

            # Worktrees
            trees = get_worktrees()
            print("WORKTREES")
            print("-" * 80)
            if trees:
                print(f"{'Task':<15} {'Age':<20} {'Changes':<10}")
                for tree in trees:
                    age_str = f"{int(tree['age_minutes'])} min ago"
                    changes = "Yes" if tree['has_changes'] else "No"
                    print(f"{tree['name']:<15} {age_str:<20} {changes:<10}")
            else:
                print("No worktrees")
            print()

            # Today's token usage
            usage = get_token_usage_today()
            print("TODAY'S API USAGE")
            print("-" * 80)
            print(f"API Calls: {usage['calls']}")
            print(f"Tokens: {usage['tokens']:,}")
            print(f"Cost: ${usage['cost']:.4f}")
            print()

            print("=" * 80)
            print("Press Ctrl+C to exit | Refresh every 5 seconds")
            print("=" * 80)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        sys.exit(0)


def cmd_status(args):
    """Quick summary (from query-logs.py summary)."""
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))

    totals = {
        "tasks": 0,
        "events": 0,
        "user_messages": 0,
        "assistant_messages": 0,
        "tool_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "errors": 0,
    }

    print(f"\n{'='*80}")
    print(f"CONVERSATION SUMMARY")
    print(f"{'='*80}\n")
    print(f"{'Task':<15} {'Events':<8} {'User':<6} {'Asst':<6} {'Tools':<6} {'Tokens In':<12} {'Tokens Out':<12}")
    print("-" * 80)

    for log_file in log_files:
        task_id = log_file.stem
        events = parse_jsonl(log_file)
        summary = get_conversation_summary(events)

        totals["tasks"] += 1
        totals["events"] += summary["total_events"]
        totals["user_messages"] += summary["user_messages"]
        totals["assistant_messages"] += summary["assistant_messages"]
        totals["tool_calls"] += summary["tool_calls"]
        totals["input_tokens"] += summary["total_input_tokens"]
        totals["output_tokens"] += summary["total_output_tokens"]
        totals["errors"] += summary["errors"]

        print(f"{task_id:<15} {summary['total_events']:<8} {summary['user_messages']:<6} "
              f"{summary['assistant_messages']:<6} {summary['tool_calls']:<6} "
              f"{summary['total_input_tokens']:<12,} {summary['total_output_tokens']:<12,}")

    print("-" * 80)
    print(f"{'TOTALS':<15} {totals['events']:<8} {totals['user_messages']:<6} "
          f"{totals['assistant_messages']:<6} {totals['tool_calls']:<6} "
          f"{totals['input_tokens']:<12,} {totals['output_tokens']:<12,}")

    print(f"\n{totals['tasks']} tasks processed")
    print(f"{totals['errors']} errors encountered")
    print(f"\nTotal tokens: {totals['input_tokens'] + totals['output_tokens']:,}")


def cmd_view(args):
    """View conversation (from view-conversation.py)."""
    jsonl_file = LOGS_DIR / f"{args.task}.jsonl"

    if not jsonl_file.exists():
        print(f"Error: File not found: {jsonl_file}")
        sys.exit(1)

    # Parse all messages
    messages = parse_jsonl(jsonl_file)

    if args.summary:
        display_summary(messages)
        return

    # Display file info
    print(f"\n{'='*80}")
    print(f"CONVERSATION LOG: {jsonl_file.name}")
    print(f"Total lines: {len(messages)}")
    print(f"{'='*80}")

    # Display summary first
    if not args.messages_only:
        display_summary(messages)

    # Display each message
    for idx, msg in enumerate(messages, 1):
        if args.messages_only and msg.get("type") != "message":
            continue
        display_message(msg, idx)

    print(f"\n{'='*80}")
    print(f"END OF CONVERSATION")
    print(f"{'='*80}\n")


def cmd_report(args):
    """Historical reports (from generate-report.py)."""
    print("=" * 80)
    print("TAC-8 HISTORICAL REPORT - COMPLETE TRANSPARENCY")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Parse all conversation logs
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))
    reports = []

    for log_file in log_files:
        events = parse_jsonl(log_file)
        if not events:
            continue

        summary = get_conversation_summary(events)
        summary['task_id'] = log_file.stem
        summary['file_size'] = log_file.stat().st_size
        summary['modified'] = datetime.fromtimestamp(log_file.stat().st_mtime)
        reports.append(summary)

    # Summary
    print("SUMMARY")
    print("-" * 80)
    print(f"Total tasks logged: {len(reports)}")

    if reports:
        total_tokens = sum(r["total_input_tokens"] + r["total_output_tokens"] for r in reports)
        total_cost = estimate_cost(total_tokens)

        print(f"Total events: {sum(r['total_events'] for r in reports)}")
        print(f"Total tokens: {total_tokens:,}")
        print(f"Estimated cost: ${total_cost:.4f}")
        print(f"Total tool calls: {sum(r['tool_calls'] for r in reports)}")

    print()

    # Timeline view
    print("TIMELINE (Most Recent First)")
    print("-" * 80)
    print(f"{'Task':<12} {'Modified':<20} {'Events':<8} {'Tokens':<12} {'Tools':<6}")
    print("-" * 80)

    for report in sorted(reports, key=lambda r: r['modified'], reverse=True):
        task_id = report['task_id']
        modified = report['modified'].strftime('%Y-%m-%d %H:%M:%S')
        events = report['total_events']
        tokens = report['total_input_tokens'] + report['total_output_tokens']
        tools = report['tool_calls']

        print(f"{task_id:<12} {modified:<20} {events:<8} {tokens:<12,} {tools:<6}")

    print()

    # Detailed task reports
    print("DETAILED TASK REPORTS")
    print("=" * 80)

    for report in sorted(reports, key=lambda r: r['modified'], reverse=True):
        print(f"\n{report['task_id']}")
        print("-" * 80)
        session_id = report.get('session_id', 'N/A')
        if session_id and len(session_id) > 16:
            session_id = session_id[:16] + "..."
        print(f"Session: {session_id}")
        print(f"Model: {report.get('model', 'N/A')}")
        print(f"Modified: {report['modified']}")
        print(f"Events: {report['total_events']} ({report['user_messages']} user, {report['assistant_messages']} assistant)")
        total_tokens = report['total_input_tokens'] + report['total_output_tokens']
        print(f"Tokens: {report['total_input_tokens']:,} in, {report['total_output_tokens']:,} out, {total_tokens:,} total")
        print(f"Tool calls: {report['tool_calls']}")
        if report.get('tools_used'):
            print(f"Tools used: {', '.join(report['tools_used'])}")

    print()
    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)


def cmd_export(args):
    """Export task data (from export-task.py)."""
    log_file = LOGS_DIR / f"{args.task}.jsonl"

    if not log_file.exists():
        print(f"Error: Log file not found: {log_file}")
        sys.exit(1)

    events = parse_jsonl(log_file)
    if not events:
        print(f"Error: No events in log file")
        sys.exit(1)

    summary = get_conversation_summary(events)
    summary['task_id'] = log_file.stem
    summary['file_size'] = log_file.stat().st_size
    summary['modified'] = datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
    summary['estimated_cost'] = estimate_cost(summary['total_input_tokens'] + summary['total_output_tokens'])
    summary['events'] = events  # Include full conversation

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    print(f"Exporting task: {args.task}")
    print(f"Format: {args.format}")
    print(f"Output: {output_dir}")
    print()

    success = True

    if args.format in ["json", "both"]:
        output_file = output_dir / f"{args.task}_export.json"
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"✅ Exported JSON to: {output_file}")
        print(f"   Events: {summary['total_events']}")
        print(f"   Tokens: {summary['total_input_tokens'] + summary['total_output_tokens']:,}")
        print(f"   Cost: ${summary['estimated_cost']:.4f}")
        print(f"   Tools: {len(summary['tools_used'])}")
        print()

    if args.format in ["markdown", "both"]:
        # Create markdown report
        md = []
        md.append(f"# Task Export: {args.task}")
        md.append("")
        md.append(f"**Generated:** {datetime.now().isoformat()}")
        md.append("")

        md.append("## Metadata")
        md.append("")
        md.append(f"- **Task ID:** {summary['task_id']}")
        md.append(f"- **Session ID:** {summary.get('session_id', 'N/A')}")
        md.append(f"- **Model:** {summary.get('model', 'N/A')}")
        md.append(f"- **Start Time:** {summary.get('start_time', 'N/A')}")
        md.append(f"- **End Time:** {summary.get('end_time', 'N/A')}")
        md.append(f"- **Working Directory:** {summary.get('cwd', 'N/A')}")
        md.append("")

        md.append("## Statistics")
        md.append("")
        md.append(f"- **Total Events:** {summary['total_events']}")
        md.append(f"- **User Messages:** {summary['user_messages']}")
        md.append(f"- **Assistant Messages:** {summary['assistant_messages']}")
        md.append(f"- **Tool Calls:** {summary['tool_calls']}")
        md.append(f"- **Input Tokens:** {summary['total_input_tokens']:,}")
        md.append(f"- **Output Tokens:** {summary['total_output_tokens']:,}")
        md.append(f"- **Total Tokens:** {summary['total_input_tokens'] + summary['total_output_tokens']:,}")
        md.append(f"- **Estimated Cost:** ${summary['estimated_cost']:.4f}")
        md.append("")

        if summary.get('tools_used'):
            md.append("## Tools Used")
            md.append("")
            for tool in sorted(summary['tools_used']):
                md.append(f"- {tool}")
            md.append("")

        md.append("## Conversation")
        md.append("")
        md.append(f"Full conversation available in: `logs/{args.task}.jsonl`")
        md.append("")
        md.append("View with:")
        md.append("```bash")
        md.append(f"./tools/tac.py view {args.task}")
        md.append("```")
        md.append("")

        output_file = output_dir / f"{args.task}_export.md"
        with open(output_file, 'w') as f:
            f.write('\n'.join(md))

        print(f"✅ Exported Markdown to: {output_file}")
        print(f"   Events: {summary['total_events']}")
        print(f"   Tokens: {summary['total_input_tokens'] + summary['total_output_tokens']:,}")
        print(f"   Cost: ${summary['estimated_cost']:.4f}")
        print()

    if success:
        print("✅ Export complete!")
    else:
        print("❌ Export failed!")
        sys.exit(1)


def cmd_search(args):
    """Search conversations (from query-logs.py search)."""
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))
    query_lower = args.query.lower()

    print(f"\n{'='*80}")
    print(f"SEARCH RESULTS: '{args.query}'")
    print(f"{'='*80}\n")

    found = False

    for log_file in log_files:
        task_id = log_file.stem
        events = parse_jsonl(log_file)

        matches = []

        for i, event in enumerate(events):
            # Search in assistant text
            if event.get("type") == "assistant":
                message = event.get("message", {})
                content = message.get("content", [])
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        if query_lower in text.lower():
                            matches.append((i + 1, text[:200]))

            # Search in user text
            elif event.get("type") == "user":
                message = event.get("message", {})
                content = message.get("content", [])
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        if query_lower in text.lower():
                            matches.append((i + 1, text[:200]))

        if matches:
            found = True
            print(f"\n{task_id}: {len(matches)} match(es)")
            for event_num, text in matches[:3]:  # Show first 3 matches
                print(f"  Event #{event_num}: {text}...")

    if not found:
        print(f"No matches found for '{args.query}'")


def cmd_tokens(args):
    """Token usage (from query-logs.py tokens)."""
    if args.task:
        log_file = LOGS_DIR / f"{args.task}.jsonl"
        if not log_file.exists():
            print(f"Error: Log file not found: {log_file}")
            return

        events = parse_jsonl(log_file)
        summary = get_conversation_summary(events)

        print(f"\n{'='*80}")
        print(f"TOKEN USAGE: {args.task}")
        print(f"{'='*80}\n")
        print(f"Model: {summary['model']}")
        print(f"Session: {summary['session_id']}\n")
        print(f"Input tokens:  {summary['total_input_tokens']:,}")
        print(f"Output tokens: {summary['total_output_tokens']:,}")
        print(f"Total tokens:  {summary['total_input_tokens'] + summary['total_output_tokens']:,}")
        print(f"\nMessages: {summary['user_messages']} user, {summary['assistant_messages']} assistant")
        print(f"Tool calls: {summary['tool_calls']}")
    else:
        # Show all tasks
        cmd_status(args)


def cmd_errors(args):
    """Find errors (from query-logs.py errors)."""
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))

    print(f"\n{'='*80}")
    print(f"CONVERSATIONS WITH ERRORS")
    print(f"{'='*80}\n")

    found_errors = False

    for log_file in log_files:
        task_id = log_file.stem
        events = parse_jsonl(log_file)

        errors = [e for e in events if e.get("type") == "error"]

        if errors:
            found_errors = True
            print(f"\n{task_id}: {len(errors)} error(s)")
            for err in errors:
                print(f"  - {err.get('error', str(err)[:100])}")

    if not found_errors:
        print("No errors found in conversation logs.")


def cmd_timeline(args):
    """Activity timeline (from generate-report.py --timeline)."""
    print("=" * 80)
    print("TAC-8 ACTIVITY TIMELINE")
    print("=" * 80)
    print()

    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))

    # Group by date
    by_date = defaultdict(list)

    for log_file in log_files:
        events = parse_jsonl(log_file)
        if not events:
            continue

        summary = get_conversation_summary(events)
        summary['task_id'] = log_file.stem
        summary['modified'] = datetime.fromtimestamp(log_file.stat().st_mtime)

        date = summary['modified'].strftime('%Y-%m-%d')
        by_date[date].append(summary)

    # Print timeline
    for date in sorted(by_date.keys(), reverse=True):
        tasks = by_date[date]
        total_tokens = sum(t['total_input_tokens'] + t['total_output_tokens'] for t in tasks)
        total_events = sum(t['total_events'] for t in tasks)

        print(f"\n{date}")
        print("-" * 80)
        print(f"Tasks: {len(tasks)}")
        print(f"Total events: {total_events}")
        print(f"Total tokens: {total_tokens:,}")
        print()

        for task in sorted(tasks, key=lambda t: t['modified']):
            time = task['modified'].strftime('%H:%M:%S')
            tokens = task['total_input_tokens'] + task['total_output_tokens']
            print(f"  {time} - {task['task_id']}: {task['total_events']} events, {tokens:,} tokens")


def cmd_list(args):
    """List all logs (from query-logs.py list)."""
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))

    print(f"\n{'='*80}")
    print(f"CONVERSATION LOGS ({len(log_files)} total)")
    print(f"{'='*80}\n")

    for log_file in log_files:
        task_id = log_file.stem
        size_kb = log_file.stat().st_size / 1024
        events = parse_jsonl(log_file)

        print(f"{task_id:15} {size_kb:7.1f} KB  {len(events):4} events")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="TAC-8 Unified Monitoring and Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # monitor subcommand
    parser_monitor = subparsers.add_parser('monitor', help='Real-time monitoring dashboard')
    parser_monitor.set_defaults(func=cmd_monitor)

    # status subcommand
    parser_status = subparsers.add_parser('status', help='Quick summary of all logs')
    parser_status.set_defaults(func=cmd_status)

    # view subcommand
    parser_view = subparsers.add_parser('view', help='View conversation log')
    parser_view.add_argument('task', help='Task ID (e.g., gh-450)')
    parser_view.add_argument('--messages-only', action='store_true', help='Show only messages')
    parser_view.add_argument('--summary', action='store_true', help='Show only summary')
    parser_view.set_defaults(func=cmd_view)

    # report subcommand
    parser_report = subparsers.add_parser('report', help='Generate historical report')
    parser_report.set_defaults(func=cmd_report)

    # export subcommand
    parser_export = subparsers.add_parser('export', help='Export task data')
    parser_export.add_argument('task', help='Task ID (e.g., gh-471)')
    parser_export.add_argument('--format', choices=['json', 'markdown', 'both'], default='both',
                              help='Export format (default: both)')
    parser_export.add_argument('--output', default='exports', help='Output directory (default: exports/)')
    parser_export.set_defaults(func=cmd_export)

    # search subcommand
    parser_search = subparsers.add_parser('search', help='Search conversations')
    parser_search.add_argument('query', help='Search query')
    parser_search.set_defaults(func=cmd_search)

    # tokens subcommand
    parser_tokens = subparsers.add_parser('tokens', help='Show token usage')
    parser_tokens.add_argument('task', nargs='?', help='Task ID (optional, shows all if omitted)')
    parser_tokens.set_defaults(func=cmd_tokens)

    # errors subcommand
    parser_errors = subparsers.add_parser('errors', help='Find conversations with errors')
    parser_errors.set_defaults(func=cmd_errors)

    # timeline subcommand
    parser_timeline = subparsers.add_parser('timeline', help='Activity timeline')
    parser_timeline.set_defaults(func=cmd_timeline)

    # list subcommand
    parser_list = subparsers.add_parser('list', help='List all conversation logs')
    parser_list.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
