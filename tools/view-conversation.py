#!/usr/bin/env python3
"""
View Claude CLI conversation logs in human-readable format.

Usage:
    ./tools/view-conversation.py logs/gh-450.jsonl
    ./tools/view-conversation.py logs/gh-450.jsonl --messages-only
    ./tools/view-conversation.py logs/gh-450.jsonl --summary
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def parse_stream_json_line(line: str) -> Dict[str, Any]:
    """Parse a single line of stream-json output."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError as e:
        return {"error": f"Parse error: {e}", "raw": line[:100]}

def format_timestamp(ts: float) -> str:
    """Format unix timestamp to readable string."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

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
    total = len(messages)

    # Count by type for Claude CLI stream-json format
    user_msgs = sum(1 for m in messages if m.get("type") == "user")
    assistant_msgs = sum(1 for m in messages if m.get("type") == "assistant")
    system_msgs = sum(1 for m in messages if m.get("type") == "system")

    tool_calls = 0
    errors = 0

    for msg in messages:
        # Count tool uses in assistant messages (nested in message.content)
        if msg.get("type") == "assistant":
            message = msg.get("message", {})
            content = message.get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_calls += 1

        # Count errors
        if msg.get("type") == "error":
            errors += 1

    print(f"\n{'='*80}")
    print("CONVERSATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total events: {total}")
    print(f"System events: {system_msgs}")
    print(f"User messages: {user_msgs}")
    print(f"Assistant messages: {assistant_msgs}")
    print(f"Tool calls: {tool_calls}")
    print(f"Errors: {errors}")
    print(f"{'='*80}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: view-conversation.py <jsonl-file> [--messages-only] [--summary]")
        sys.exit(1)

    jsonl_file = Path(sys.argv[1])
    messages_only = "--messages-only" in sys.argv
    summary_only = "--summary" in sys.argv

    if not jsonl_file.exists():
        print(f"Error: File not found: {jsonl_file}")
        sys.exit(1)

    # Parse all messages
    messages = []
    with open(jsonl_file, 'r') as f:
        for line in f:
            if line.strip():
                msg = parse_stream_json_line(line)
                messages.append(msg)

    if summary_only:
        display_summary(messages)
        return

    # Display file info
    print(f"\n{'='*80}")
    print(f"CONVERSATION LOG: {jsonl_file.name}")
    print(f"Total lines: {len(messages)}")
    print(f"{'='*80}")

    # Display summary first
    if not messages_only:
        display_summary(messages)

    # Display each message
    for idx, msg in enumerate(messages, 1):
        if messages_only and msg.get("type") != "message":
            continue
        display_message(msg, idx)

    print(f"\n{'='*80}")
    print(f"END OF CONVERSATION")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
