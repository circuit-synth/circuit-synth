"""
SQLite database schema and management for Circuit Synth logging system.
Provides persistent storage for session metadata and event indexing.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class LogDatabase:
    """
    Manages SQLite database for logging system.
    Stores session metadata and provides fast event searching.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the log database.

        Args:
            db_path: Path to the database file. Defaults to logs/circuit_synth_logs.db
        """
        self.db_path = db_path or (
            Path.home() / ".circuit-synth" / "logs" / "circuit_synth_logs.db"
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # User sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    total_events INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """
            )

            # Chat sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    chat_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    message_count INTEGER DEFAULT 0,
                    model_used TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )
            """
            )

            # Event index table for fast searching
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS event_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    chat_id TEXT,
                    event_type TEXT NOT NULL,
                    log_file TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    summary TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )
            """
            )

            # Performance metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )
            """
            )

            # LLM usage table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_usage (
                    request_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    chat_id TEXT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    cost_usd REAL,
                    duration_ms REAL,
                    success BOOLEAN,
                    error TEXT,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
                    FOREIGN KEY (chat_id) REFERENCES chat_sessions(chat_id)
                )
            """
            )

            # Create indexes for fast queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_timestamp 
                ON event_index(timestamp)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON event_index(event_type)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_session 
                ON event_index(session_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_performance_timestamp 
                ON performance_metrics(timestamp)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_llm_timestamp 
                ON llm_usage(timestamp)
            """
            )

            conn.commit()

    def create_user_session(
        self,
        session_id: str,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create a new user session record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_sessions 
                (session_id, username, start_time, ip_address, user_agent, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    username,
                    datetime.now().isoformat(),
                    ip_address,
                    user_agent,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()

    def update_user_session(
        self,
        session_id: str,
        end_time: Optional[datetime] = None,
        total_events: Optional[int] = None,
    ):
        """Update user session information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if end_time:
                updates.append("end_time = ?")
                params.append(end_time.isoformat())

            if total_events is not None:
                updates.append("total_events = ?")
                params.append(total_events)

            if updates:
                params.append(session_id)
                cursor.execute(
                    f"""
                    UPDATE user_sessions 
                    SET {', '.join(updates)}
                    WHERE session_id = ?
                """,
                    params,
                )
                conn.commit()

    def create_chat_session(
        self,
        chat_id: str,
        session_id: str,
        model_used: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create a new chat session record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions 
                (chat_id, session_id, start_time, model_used, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    chat_id,
                    session_id,
                    datetime.now().isoformat(),
                    model_used,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()

    def update_chat_session(
        self,
        chat_id: str,
        end_time: Optional[datetime] = None,
        message_count: Optional[int] = None,
        total_tokens: Optional[int] = None,
        total_cost: Optional[float] = None,
    ):
        """Update chat session information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if end_time:
                updates.append("end_time = ?")
                params.append(end_time.isoformat())

            if message_count is not None:
                updates.append("message_count = ?")
                params.append(message_count)

            if total_tokens is not None:
                updates.append("total_tokens = ?")
                params.append(total_tokens)

            if total_cost is not None:
                updates.append("total_cost = ?")
                params.append(total_cost)

            if updates:
                params.append(chat_id)
                cursor.execute(
                    f"""
                    UPDATE chat_sessions 
                    SET {', '.join(updates)}
                    WHERE chat_id = ?
                """,
                    params,
                )
                conn.commit()

    def add_event_to_index(
        self,
        timestamp: str,
        session_id: str,
        event_type: str,
        log_file: str,
        line_number: int,
        chat_id: Optional[str] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add an event to the search index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO event_index 
                (timestamp, session_id, chat_id, event_type, log_file, line_number, summary, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    timestamp,
                    session_id,
                    chat_id,
                    event_type,
                    log_file,
                    line_number,
                    summary,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()

    def add_performance_metric(
        self,
        session_id: str,
        metric_type: str,
        metric_name: str,
        value: float,
        unit: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a performance metric record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO performance_metrics 
                (timestamp, session_id, metric_type, metric_name, value, unit, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    session_id,
                    metric_type,
                    metric_name,
                    value,
                    unit,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()

    def add_llm_usage(
        self,
        request_id: str,
        session_id: str,
        model: str,
        provider: str,
        chat_id: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Add LLM usage record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO llm_usage 
                (request_id, session_id, chat_id, timestamp, model, provider,
                 prompt_tokens, completion_tokens, total_tokens, cost_usd,
                 duration_ms, success, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request_id,
                    session_id,
                    chat_id,
                    datetime.now().isoformat(),
                    model,
                    provider,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    cost_usd,
                    duration_ms,
                    success,
                    error,
                ),
            )
            conn.commit()

    def update_llm_usage(
        self,
        request_id: str,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        duration_ms: Optional[float] = None,
        success: Optional[bool] = None,
        error: Optional[str] = None,
    ):
        """Update an existing LLM usage record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if completion_tokens is not None:
                updates.append("completion_tokens = ?")
                params.append(completion_tokens)

            if total_tokens is not None:
                updates.append("total_tokens = ?")
                params.append(total_tokens)

            if cost_usd is not None:
                updates.append("cost_usd = ?")
                params.append(cost_usd)

            if duration_ms is not None:
                updates.append("duration_ms = ?")
                params.append(duration_ms)

            if success is not None:
                updates.append("success = ?")
                params.append(success)

            if error is not None:
                updates.append("error = ?")
                params.append(error)

            if updates:
                params.append(request_id)
                cursor.execute(
                    f"""
                    UPDATE llm_usage
                    SET {', '.join(updates)}
                    WHERE request_id = ?
                """,
                    params,
                )
                conn.commit()

    def search_events(
        self,
        event_type: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search for events in the index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM event_index WHERE 1=1"
            params = []

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]

            results = []
            for row in cursor.fetchall():
                event = dict(zip(columns, row))
                if event.get("metadata"):
                    event["metadata"] = json.loads(event["metadata"])
                results.append(event)

            return results

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get session info
            cursor.execute(
                """
                SELECT * FROM user_sessions WHERE session_id = ?
            """,
                (session_id,),
            )
            session_row = cursor.fetchone()

            if not session_row:
                return {}

            columns = [desc[0] for desc in cursor.description]
            session_info = dict(zip(columns, session_row))

            # Get event counts by type
            cursor.execute(
                """
                SELECT event_type, COUNT(*) as count 
                FROM event_index 
                WHERE session_id = ? 
                GROUP BY event_type
            """,
                (session_id,),
            )
            event_counts = dict(cursor.fetchall())

            # Get performance summary
            cursor.execute(
                """
                SELECT metric_type, metric_name, 
                       AVG(value) as avg_value, 
                       MIN(value) as min_value, 
                       MAX(value) as max_value
                FROM performance_metrics 
                WHERE session_id = ? 
                GROUP BY metric_type, metric_name
            """,
                (session_id,),
            )

            performance_summary = []
            for row in cursor.fetchall():
                performance_summary.append(
                    {
                        "metric_type": row[0],
                        "metric_name": row[1],
                        "avg_value": row[2],
                        "min_value": row[3],
                        "max_value": row[4],
                    }
                )

            # Get LLM usage summary
            cursor.execute(
                """
                SELECT COUNT(*) as request_count,
                       SUM(total_tokens) as total_tokens,
                       SUM(cost_usd) as total_cost,
                       AVG(duration_ms) as avg_duration_ms
                FROM llm_usage 
                WHERE session_id = ?
            """,
                (session_id,),
            )
            llm_row = cursor.fetchone()
            llm_summary = {
                "request_count": llm_row[0] or 0,
                "total_tokens": llm_row[1] or 0,
                "total_cost": llm_row[2] or 0.0,
                "avg_duration_ms": llm_row[3] or 0.0,
            }

            return {
                "session_info": session_info,
                "event_counts": event_counts,
                "performance_summary": performance_summary,
                "llm_summary": llm_summary,
            }

    def close(self):
        """Close database connection."""
        # SQLite connections are automatically closed when using context manager
        pass
