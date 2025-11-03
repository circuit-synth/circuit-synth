#!/usr/bin/env python3
"""
Export complete task data including conversation, tokens, and metadata.

Usage:
    ./tools/export-task.py gh-471
    ./tools/export-task.py gh-471 --format json
    ./tools/export-task.py gh-471 --output /path/to/export/
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

LOGS_DIR = Path("logs")
REPO_ROOT = Path(__file__).parent.parent

def parse_conversation_log(log_file: Path):
    """Parse a conversation log and extract all data."""
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

    # Extract tool calls
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
        "estimated_cost": (total_in + total_out) * 0.000015,
        "file_size": log_file.stat().st_size,
        "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
        "events": events,  # Include full conversation
    }

def export_json(task_id: str, output_dir: Path):
    """Export task data as JSON."""
    log_file = LOGS_DIR / f"{task_id}.jsonl"

    if not log_file.exists():
        print(f"Error: Log file not found: {log_file}")
        return False

    data = parse_conversation_log(log_file)

    if "error" in data:
        print(f"Error parsing log: {data['error']}")
        return False

    output_file = output_dir / f"{task_id}_export.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Exported to: {output_file}")
    print(f"   Events: {data['total_events']}")
    print(f"   Tokens: {data['tokens_total']:,}")
    print(f"   Cost: ${data['estimated_cost']:.4f}")
    print(f"   Tools: {len(data['tools_used'])}")

    return True

def export_markdown(task_id: str, output_dir: Path):
    """Export task data as Markdown report."""
    log_file = LOGS_DIR / f"{task_id}.jsonl"

    if not log_file.exists():
        print(f"Error: Log file not found: {log_file}")
        return False

    data = parse_conversation_log(log_file)

    if "error" in data:
        print(f"Error parsing log: {data['error']}")
        return False

    # Create markdown report
    md = []
    md.append(f"# Task Export: {task_id}")
    md.append("")
    md.append(f"**Generated:** {datetime.now().isoformat()}")
    md.append("")

    md.append("## Metadata")
    md.append("")
    md.append(f"- **Task ID:** {data['task_id']}")
    md.append(f"- **Session ID:** {data.get('session_id', 'N/A')}")
    md.append(f"- **Model:** {data.get('model', 'N/A')}")
    md.append(f"- **Start Time:** {data.get('start_time', 'N/A')}")
    md.append(f"- **End Time:** {data.get('end_time', 'N/A')}")
    md.append(f"- **Working Directory:** {data.get('cwd', 'N/A')}")
    md.append("")

    md.append("## Statistics")
    md.append("")
    md.append(f"- **Total Events:** {data['total_events']}")
    md.append(f"- **User Messages:** {data['user_messages']}")
    md.append(f"- **Assistant Messages:** {data['assistant_messages']}")
    md.append(f"- **Tool Calls:** {data['tool_calls']}")
    md.append(f"- **Input Tokens:** {data['tokens_in']:,}")
    md.append(f"- **Output Tokens:** {data['tokens_out']:,}")
    md.append(f"- **Total Tokens:** {data['tokens_total']:,}")
    md.append(f"- **Estimated Cost:** ${data['estimated_cost']:.4f}")
    md.append("")

    if data.get('tools_used'):
        md.append("## Tools Used")
        md.append("")
        for tool in sorted(data['tools_used']):
            md.append(f"- {tool}")
        md.append("")

    md.append("## Conversation")
    md.append("")
    md.append(f"Full conversation available in: `logs/{task_id}.jsonl`")
    md.append("")
    md.append("View with:")
    md.append("```bash")
    md.append(f"./tools/view-conversation.py logs/{task_id}.jsonl")
    md.append("```")
    md.append("")

    output_file = output_dir / f"{task_id}_export.md"
    with open(output_file, 'w') as f:
        f.write('\n'.join(md))

    print(f"✅ Exported to: {output_file}")
    print(f"   Events: {data['total_events']}")
    print(f"   Tokens: {data['tokens_total']:,}")
    print(f"   Cost: ${data['estimated_cost']:.4f}")

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Export complete task data"
    )
    parser.add_argument(
        "task_id",
        help="Task ID (e.g., gh-471)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Export format (default: both)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exports"),
        help="Output directory (default: exports/)"
    )

    args = parser.parse_args()

    # Create output directory
    args.output.mkdir(exist_ok=True)

    print(f"Exporting task: {args.task_id}")
    print(f"Format: {args.format}")
    print(f"Output: {args.output}")
    print()

    success = True

    if args.format in ["json", "both"]:
        if not export_json(args.task_id, args.output):
            success = False

    if args.format in ["markdown", "both"]:
        if not export_markdown(args.task_id, args.output):
            success = False

    if success:
        print()
        print("✅ Export complete!")
    else:
        print()
        print("❌ Export failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
