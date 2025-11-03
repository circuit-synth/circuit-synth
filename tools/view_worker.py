#!/usr/bin/env python3
"""
View worker agent conversation logs in readable format.

Usage:
    python tools/view_worker.py 471
    python tools/view_worker.py 471 --detailed
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def format_timestamp(ts):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ts


def view_conversation(issue_number: int, detailed: bool = False):
    """Display worker conversation from JSONL logs"""
    log_file = Path(f"logs/gh-{issue_number}.jsonl")

    if not log_file.exists():
        print(f"❌ No log file found: {log_file}")
        return

    print(f"\n{'='*80}")
    print(f"Worker Conversation - Issue #{issue_number}")
    print(f"{'='*80}\n")

    message_count = 0
    tool_count = 0

    with open(log_file) as f:
        for line in f:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get('type')

            # System init
            if event_type == 'system' and event.get('subtype') == 'init':
                print(f"🚀 Session Started")
                print(f"   Working Directory: {event.get('cwd', 'unknown')}")
                print(f"   Session ID: {event.get('session_id', 'unknown')[:8]}...")
                print(f"   Model: {event.get('model', 'unknown')}")
                print()

            # Assistant messages
            elif event_type == 'assistant':
                msg = event.get('message', {})
                content = msg.get('content', [])

                for item in content:
                    if item.get('type') == 'text':
                        message_count += 1
                        text = item.get('text', '')

                        # Summarize long messages unless detailed
                        if not detailed and len(text) > 300:
                            text = text[:300] + f"... [+{len(text)-300} chars]"

                        print(f"💬 Assistant #{message_count}")
                        print(f"   {text}")
                        print()

                    elif item.get('type') == 'tool_use':
                        tool_count += 1
                        tool_name = item.get('name', 'unknown')
                        tool_input = item.get('input', {})

                        print(f"🔧 Tool #{tool_count}: {tool_name}")

                        # Show key parameters
                        if tool_name == 'Read':
                            print(f"   File: {tool_input.get('file_path', 'unknown')}")
                        elif tool_name == 'Write':
                            print(f"   File: {tool_input.get('file_path', 'unknown')}")
                            print(f"   Size: {len(tool_input.get('content', ''))} chars")
                        elif tool_name == 'Edit':
                            print(f"   File: {tool_input.get('file_path', 'unknown')}")
                            print(f"   Old: {tool_input.get('old_string', '')[:50]}...")
                            print(f"   New: {tool_input.get('new_string', '')[:50]}...")
                        elif tool_name == 'Bash':
                            print(f"   Command: {tool_input.get('command', 'unknown')}")
                        elif tool_name == 'Grep':
                            print(f"   Pattern: {tool_input.get('pattern', 'unknown')}")
                            print(f"   Path: {tool_input.get('path', 'cwd')}")
                        else:
                            if detailed:
                                print(f"   Parameters: {json.dumps(tool_input, indent=6)}")
                        print()

            # System messages
            elif event_type == 'system':
                if detailed:
                    subtype = event.get('subtype', 'unknown')
                    print(f"⚙️  System: {subtype}")
                    print()

    print(f"\n{'='*80}")
    print(f"Summary: {message_count} messages, {tool_count} tool uses")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python tools/view_worker.py <issue_number> [--detailed]")
        sys.exit(1)

    issue = int(sys.argv[1])
    detailed = '--detailed' in sys.argv

    view_conversation(issue, detailed)
