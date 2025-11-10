#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Universal Hook Logger - Claude Code Hook
Logs all hook payloads to session-specific JSONL files
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_hook_name(input_data: dict) -> str:
    """Extract hook event name from input data."""
    return input_data.get("hook_event_name", "Unknown")


def create_log_entry(input_data: dict) -> dict:
    """Create enriched log entry with timestamp and full payload."""
    return {
        "timestamp": datetime.now().isoformat(),
        "payload": input_data
    }


def write_log_entry(session_id: str, hook_name: str, log_entry: dict) -> None:
    """Write log entry to appropriate JSONL file."""
    # Use CLAUDE_PROJECT_DIR if available, otherwise use cwd
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    
    # Create directory structure relative to project root
    log_dir = Path(project_dir) / "agents" / "hook_logs" / session_id
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create hook-specific log file
    log_file = log_dir / f"{hook_name}.jsonl"
    
    # Append to JSONL file
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract session ID and hook name
        session_id = input_data.get("session_id", "unknown")
        hook_name = get_hook_name(input_data)
        
        # Create and write log entry
        log_entry = create_log_entry(input_data)
        write_log_entry(session_id, hook_name, log_entry)
        
        # Success - exit silently
        sys.exit(0)
        
    except Exception as e:
        # Log error but don't block hook execution
        print(f"Hook logger error: {e}", file=sys.stderr)
        sys.exit(0)  # Non-blocking error


if __name__ == "__main__":
    main()