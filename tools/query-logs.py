#!/usr/bin/env python3
"""
Query TAC-8 conversation logs for analysis.

Usage:
    # Summary of all conversations
    ./tools/query-logs.py summary

    # Token usage for a specific task
    ./tools/query-logs.py tokens --task gh-450

    # List all tasks with conversation logs
    ./tools/query-logs.py list

    # Find conversations with errors
    ./tools/query-logs.py errors

    # Search for specific text in conversations
    ./tools/query-logs.py search "error handling"
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

LOGS_DIR = Path("/home/shane/Desktop/circuit-synth/logs")

def parse_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a JSONL file into a list of events."""
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
    """Summarize a conversation from events."""
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
    }

    for event in events:
        event_type = event.get("type")

        if event_type == "system":
            summary["session_id"] = event.get("session_id")
            summary["model"] = event.get("model")

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

        elif event_type == "error":
            summary["errors"] += 1

    return summary

def cmd_list():
    """List all conversation logs."""
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))

    print(f"\n{'='*80}")
    print(f"CONVERSATION LOGS ({len(log_files)} total)")
    print(f"{'='*80}\n")

    for log_file in log_files:
        task_id = log_file.stem
        size_kb = log_file.stat().st_size / 1024
        events = parse_jsonl(log_file)

        print(f"{task_id:15} {size_kb:7.1f} KB  {len(events):4} events")

def cmd_summary():
    """Show summary of all conversations."""
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

def cmd_tokens(task_id: str = None):
    """Show token usage for a specific task or all tasks."""
    if task_id:
        log_file = LOGS_DIR / f"{task_id}.jsonl"
        if not log_file.exists():
            print(f"Error: Log file not found: {log_file}")
            return

        events = parse_jsonl(log_file)
        summary = get_conversation_summary(events)

        print(f"\n{'='*80}")
        print(f"TOKEN USAGE: {task_id}")
        print(f"{'='*80}\n")
        print(f"Model: {summary['model']}")
        print(f"Session: {summary['session_id']}\n")
        print(f"Input tokens:  {summary['total_input_tokens']:,}")
        print(f"Output tokens: {summary['total_output_tokens']:,}")
        print(f"Total tokens:  {summary['total_input_tokens'] + summary['total_output_tokens']:,}")
        print(f"\nMessages: {summary['user_messages']} user, {summary['assistant_messages']} assistant")
        print(f"Tool calls: {summary['tool_calls']}")
    else:
        cmd_summary()

def cmd_errors():
    """Find all conversations with errors."""
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

def cmd_search(query: str):
    """Search for text in conversations."""
    log_files = sorted(LOGS_DIR.glob("gh-*.jsonl"))
    query_lower = query.lower()

    print(f"\n{'='*80}")
    print(f"SEARCH RESULTS: '{query}'")
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
        print(f"No matches found for '{query}'")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        cmd_list()
    elif command == "summary":
        cmd_summary()
    elif command == "tokens":
        task_id = sys.argv[2] if len(sys.argv) > 2 else None
        if task_id and not task_id.startswith("--"):
            cmd_tokens(task_id)
        else:
            cmd_tokens()
    elif command == "errors":
        cmd_errors()
    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: search requires a query string")
            sys.exit(1)
        cmd_search(" ".join(sys.argv[2:]))
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
