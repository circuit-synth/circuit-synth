#!/usr/bin/env python3
"""
Parse worker logs to extract token usage information

Supports Claude's stream-json format logs.
"""

import json
from pathlib import Path
from typing import Tuple


def parse_claude_log(log_path: Path) -> Tuple[int, int]:
    """
    Parse Claude JSON log file to extract token usage

    Args:
        log_path: Path to .jsonl log file

    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    input_tokens = 0
    output_tokens = 0

    if not log_path.exists():
        return (0, 0)

    try:
        with open(log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)

                    # Claude API response format includes usage
                    if entry.get('type') == 'message_stop':
                        # Final message with usage stats
                        usage = entry.get('message', {}).get('usage', {})
                        input_tokens = usage.get('input_tokens', 0)
                        output_tokens = usage.get('output_tokens', 0)

                    # Also check for usage in metadata
                    elif 'usage' in entry:
                        usage = entry['usage']
                        input_tokens = max(input_tokens, usage.get('input_tokens', 0))
                        output_tokens = max(output_tokens, usage.get('output_tokens', 0))

                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue

    except Exception as e:
        print(f"Warning: Error parsing log {log_path}: {e}")
        return (0, 0)

    return (input_tokens, output_tokens)


def extract_usage_from_issue_log(issue_number: str, logs_dir: Path) -> Tuple[int, int]:
    """
    Extract token usage from a specific issue's log file

    Args:
        issue_number: GitHub issue number
        logs_dir: Directory containing log files

    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    log_path = logs_dir / f"gh-{issue_number}.jsonl"
    return parse_claude_log(log_path)
