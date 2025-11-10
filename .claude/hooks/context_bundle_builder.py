#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Context Bundle Builder - Claude Code Hook (JSONL version)
Tracks files accessed (Read/Write) and user prompts during a Claude Code session
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def handle_file_operations(input_data: dict) -> None:
    """Handle Read/Write tool operations."""
    # Extract relevant data
    session_id = input_data.get("session_id", "unknown")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})
    
    # Only process Read and Write tools
    if tool_name not in ["Read", "Write"]:
        sys.exit(0)
    
    # Extract file path
    file_path = tool_input.get("file_path")
    if not file_path:
        sys.exit(0)
    
    # Check if Write operation was successful
    if tool_name == "Write" and tool_response:
        success = tool_response.get("success", True)
        if not success:
            sys.exit(0)
    
    # Convert absolute path to relative
    try:
        # Use CLAUDE_PROJECT_DIR if available, otherwise use cwd
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        abs_path = Path(file_path).resolve()
        project_path = Path(project_dir).resolve()
        
        # Try to make path relative to project directory
        try:
            relative_path = abs_path.relative_to(project_path)
            file_path_relative = str(relative_path)
        except ValueError:
            # If file is outside project directory, keep absolute path
            file_path_relative = file_path
    except Exception:
        # If any error, keep original path
        file_path_relative = file_path
    
    # Create the log entry
    log_entry = {
        "operation": tool_name.lower(),  # "read" or "write"
        "file_path": file_path_relative
    }
    
    # Add tool_input parameters (excluding file_path since we already have it)
    tool_input_filtered = {}
    if tool_name == "Read":
        if "limit" in tool_input:
            tool_input_filtered["limit"] = tool_input["limit"]
        if "offset" in tool_input:
            tool_input_filtered["offset"] = tool_input["offset"]
    elif tool_name == "Write":
        # For Write, we might want to track content length but not the content itself
        if "content" in tool_input:
            tool_input_filtered["content_length"] = len(tool_input.get("content", ""))
    
    # Only add tool_input if there are parameters to save
    if tool_input_filtered:
        log_entry["tool_input"] = tool_input_filtered
    
    # Write to JSONL file
    write_log_entry(session_id, log_entry)


def handle_user_prompt(input_data: dict) -> None:
    """Handle UserPromptSubmit events."""
    # Extract relevant data
    session_id = input_data.get("session_id", "unknown")
    prompt = input_data.get("prompt", "")
    
    if not prompt:
        sys.exit(0)
    
    # Create minimal log entry for prompt
    log_entry = {
        "operation": "prompt",
        "prompt": prompt[:500]  # Limit prompt length to avoid huge logs
    }
    
    # Write to JSONL file
    write_log_entry(session_id, log_entry)


def write_log_entry(session_id: str, log_entry: dict) -> None:
    """Write a log entry to the JSONL file."""
    # Generate filename with day_hour and session_id
    now = datetime.now()
    day_hour = now.strftime("%a_%H").upper()
    
    # Create directory structure
    bundle_dir = Path("agents/context_bundles")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    # Use JSONL file (JSON Lines format)
    bundle_file = bundle_dir / f"{day_hour}_{session_id}.jsonl"
    
    # Append to JSONL file (atomic operation for small writes)
    try:
        with open(bundle_file, 'a') as f:
            # Write as a single line of JSON
            f.write(json.dumps(log_entry) + '\n')
    except IOError as e:
        print(f"Error appending to context bundle: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Context Bundle Builder")
    parser.add_argument("--type", choices=["file_ops", "user_prompt"], 
                       default="file_ops",
                       help="Type of operation to handle")
    args = parser.parse_args()
    
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Route to appropriate handler
    if args.type == "file_ops":
        handle_file_operations(input_data)
    elif args.type == "user_prompt":
        handle_user_prompt(input_data)
    
    # Success - exit silently
    sys.exit(0)


if __name__ == "__main__":
    main()