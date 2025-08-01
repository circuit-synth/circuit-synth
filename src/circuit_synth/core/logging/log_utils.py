"""
Utility functions for the Circuit Synth logging system.
Provides helper functions for session management, formatting, and directory operations.
"""

import gzip
import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


def generate_session_id(username: str) -> str:
    """
    Generate a unique session ID for a user.

    Args:
        username: The username for the session

    Returns:
        A unique session ID in format: username_YYYYMMDD_HHMMSS_uniqueid
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{username}_{timestamp}_{unique_id}"


def generate_chat_id() -> str:
    """
    Generate a unique chat ID.

    Returns:
        A unique chat ID
    """
    return f"chat_{uuid.uuid4()}"


def generate_request_id(prefix: str = "req") -> str:
    """
    Generate a unique request ID for tracking API calls.

    Args:
        prefix: Prefix for the request ID

    Returns:
        A unique request ID
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def ensure_log_directory(path: Path) -> Path:
    """
    Ensure a log directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        The path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_log_directory(username: str, date: Optional[datetime] = None) -> Path:
    """
    Get the log directory for a specific user and date.

    Args:
        username: The username
        date: The date (defaults to today)

    Returns:
        Path to the user's log directory for the specified date
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    log_dir = Path.home() / ".circuit-synth" / "logs" / "users" / username / date_str
    return ensure_log_directory(log_dir)


def get_system_log_directory(date: Optional[datetime] = None) -> Path:
    """
    Get the system log directory for a specific date.

    Args:
        date: The date (defaults to today)

    Returns:
        Path to the system log directory for the specified date
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    log_dir = Path.home() / ".circuit-synth" / "logs" / "system" / date_str
    return ensure_log_directory(log_dir)


def format_event_for_logging(event: Dict[str, Any]) -> str:
    """
    Format an event dictionary for logging.

    Args:
        event: The event dictionary

    Returns:
        JSON string representation of the event
    """

    # Ensure all values are serializable
    def make_serializable(obj):
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return str(obj)
        return obj

    serializable_event = json.loads(json.dumps(event, default=make_serializable))

    return json.dumps(serializable_event, separators=(",", ":"))


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a log line into timestamp and event data.

    Args:
        line: A log line

    Returns:
        Dictionary with 'timestamp' and 'event' keys, or None if parsing fails
    """
    try:
        # Expected format: "2025-06-27T09:30:45.123 {json_data}"
        parts = line.strip().split(" ", 1)
        if len(parts) != 2:
            return None

        timestamp_str, json_str = parts
        event = json.loads(json_str)

        return {"timestamp": timestamp_str, "event": event}
    except (json.JSONDecodeError, ValueError):
        return None


def compress_old_logs(days_old: int = 7):
    """
    Compress log files older than specified days.

    Args:
        days_old: Number of days after which to compress logs
    """
    cutoff_date = datetime.now() - timedelta(days=days_old)
    log_base = Path.home() / ".circuit-synth" / "logs"

    for log_type in ["users", "system", "performance", "master"]:
        type_dir = log_base / log_type
        if not type_dir.exists():
            continue

        # For user logs, we need to go one level deeper
        if log_type == "users":
            for user_dir in type_dir.iterdir():
                if user_dir.is_dir():
                    _compress_date_directories(user_dir, cutoff_date)
        else:
            _compress_date_directories(type_dir, cutoff_date)


def _compress_date_directories(parent_dir: Path, cutoff_date: datetime):
    """
    Compress date directories older than cutoff date.

    Args:
        parent_dir: Parent directory containing date directories
        cutoff_date: Date before which to compress
    """
    for date_dir in parent_dir.iterdir():
        if not date_dir.is_dir():
            continue

        # Try to parse the directory name as a date
        try:
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
            if dir_date < cutoff_date:
                # Compress this directory
                archive_path = date_dir.with_suffix(".tar.gz")
                if not archive_path.exists():
                    shutil.make_archive(
                        str(date_dir),
                        "gztar",
                        root_dir=str(date_dir.parent),
                        base_dir=date_dir.name,
                    )
                    # Remove the original directory after successful compression
                    shutil.rmtree(date_dir)
                    print(f"Compressed old logs: {date_dir} -> {archive_path}")
        except ValueError:
            # Not a date directory, skip
            continue


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hex string of the file hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_log_file_stats(log_path: Path) -> Dict[str, Any]:
    """
    Get statistics about a log file.

    Args:
        log_path: Path to the log file

    Returns:
        Dictionary with file statistics
    """
    if not log_path.exists():
        return {}

    stats = log_path.stat()
    return {
        "path": str(log_path),
        "size_bytes": stats.st_size,
        "size_mb": round(stats.st_size / (1024 * 1024), 2),
        "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "line_count": sum(1 for _ in open(log_path, "r", encoding="utf-8")),
    }


def search_logs(
    pattern: str, log_paths: List[Path], max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for a pattern in log files.

    Args:
        pattern: Search pattern (substring match)
        log_paths: List of log file paths to search
        max_results: Maximum number of results to return

    Returns:
        List of matching log entries
    """
    results = []
    pattern_lower = pattern.lower()

    for log_path in log_paths:
        if not log_path.exists():
            continue

        with open(log_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if pattern_lower in line.lower():
                    parsed = parse_log_line(line)
                    if parsed:
                        parsed["file"] = str(log_path)
                        parsed["line_number"] = line_num
                        results.append(parsed)

                        if len(results) >= max_results:
                            return results

    return results


def create_session_summary(session_id: str, log_dir: Path) -> Dict[str, Any]:
    """
    Create a summary of a user session from logs.

    Args:
        session_id: The session ID to summarize
        log_dir: Directory containing session logs

    Returns:
        Dictionary with session summary
    """
    summary = {
        "session_id": session_id,
        "events": [],
        "event_counts": {},
        "start_time": None,
        "end_time": None,
        "duration_seconds": 0,
    }

    # Find the session log file
    session_files = list(log_dir.glob(f"*{session_id.split('_', 1)[1]}*.log"))
    if not session_files:
        return summary

    for session_file in session_files:
        with open(session_file, "r", encoding="utf-8") as f:
            for line in f:
                parsed = parse_log_line(line)
                if parsed and parsed["event"].get("session_id") == session_id:
                    event = parsed["event"]
                    event_type = event.get("event_type", "unknown")

                    # Track event counts
                    summary["event_counts"][event_type] = (
                        summary["event_counts"].get(event_type, 0) + 1
                    )

                    # Track start and end times
                    timestamp = parsed["timestamp"]
                    if not summary["start_time"] or timestamp < summary["start_time"]:
                        summary["start_time"] = timestamp
                    if not summary["end_time"] or timestamp > summary["end_time"]:
                        summary["end_time"] = timestamp

    # Calculate duration
    if summary["start_time"] and summary["end_time"]:
        start_dt = datetime.fromisoformat(summary["start_time"].replace("T", " "))
        end_dt = datetime.fromisoformat(summary["end_time"].replace("T", " "))
        summary["duration_seconds"] = (end_dt - start_dt).total_seconds()

    return summary
