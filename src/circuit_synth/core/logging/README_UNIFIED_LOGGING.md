# Circuit Synth Unified Logging System

## Overview

The unified logging system replaces the previous complex multi-file, multi-logger architecture with a **single, simple, comprehensive log stream**. All events from all users go into one human-readable log file that's easy to search, grep, and understand.

## Key Benefits

1. **Simplicity**: One log file, one logger instance, one clear API
2. **Readability**: Human-friendly format that's easy to scan
3. **Comprehensive**: All events in chronological order with full context
4. **Performance**: No database overhead, simple file rotation
5. **Debugging**: Easy correlation across users, sessions, and operations

## Log Format

```
2025-06-27 21:45:30.123 [INFO ] [AUTH    ] user=admin session=admin_20250627_214530 | User login successful
2025-06-27 21:45:35.456 [INFO ] [CHAT    ] user=admin chat=chat_abc123 | New chat: "Voltage Regulator"
2025-06-27 21:45:40.789 [INFO ] [LLM     ] user=admin chat=chat_abc123 req=req_xyz789 | Request to gemini-2.5-flash (150 tokens)
```

Format: `TIMESTAMP [LEVEL] [COMPONENT] CONTEXT | MESSAGE`

## Quick Start

```python
from circuit_synth.core.logging.unified_logger import (
    logger, log_auth, log_chat, log_llm_request, log_llm_response,
    log_circuit_start, log_circuit_complete, log_error
)

# Log user login
log_auth("User login successful", user="admin", session=session_id)

# Log LLM interaction
log_llm_request(user="admin", chat=chat_id, request_id=req_id, 
                model="gemini-2.5-flash", prompt_preview=prompt[:100], tokens=150)

# Log circuit generation
log_circuit_start(user="admin", chat=chat_id, generation_id=gen_id, 
                  circuit_type="voltage_regulator")

# Log errors with context
try:
    # ... some operation ...
except Exception as e:
    log_error("CIRCUIT", "Operation failed", error=e, user="admin", chat=chat_id)
```

## Component Categories

- **AUTH**: Login/logout events
- **CHAT**: Chat creation and management
- **LLM**: AI model requests and responses
- **CIRCUIT**: Circuit generation pipeline
- **FILES**: File operations (save/download)
- **PERF**: Performance metrics
- **ERROR**: All errors with context

## Common Usage Patterns

### 1. Basic Logging
```python
logger.info("SYSTEM", "Dashboard started", port=8080)
logger.warning("LLM", "Rate limit approaching", requests_remaining=10)
logger.error("CIRCUIT", "Generation failed", error=e, user=user, chat=chat)
```

### 2. Performance Tracking
```python
# Using context manager
with logger.timer("circuit_execution", user=user, chat=chat):
    # ... do work ...
    pass  # Duration logged automatically
```

### 3. Circuit Generation Flow
```python
# Start
log_circuit_start(user, chat, generation_id, "voltage_regulator")

# Progress
logger.circuit_progress(user, chat, generation_id, "Python code generated", "1.2KB")

# Complete
log_circuit_complete(user, chat, generation_id, files=4, size_kb=15.6)
```

## Searching Logs

The unified format makes searching easy:

```bash
# All activity for one user
grep "user=admin" logs/circuit_synth.log

# All LLM requests
grep "\[LLM     \]" logs/circuit_synth.log

# All errors
grep "\[ERROR\]" logs/circuit_synth.log

# Specific chat
grep "chat=chat_abc123" logs/circuit_synth.log

# Today's circuit generations
grep "$(date +%Y-%m-%d)" logs/circuit_synth.log | grep "\[CIRCUIT \]"

# Performance issues (>5 seconds)
grep "\[PERF    \]" logs/circuit_synth.log | grep -E "[5-9]\.[0-9]s|[0-9]{2,}\.[0-9]s"
```

## Configuration

Environment variables:
- `CIRCUIT_SYNTH_LOG_LEVEL`: Set to DEBUG, INFO, WARNING, ERROR (default: INFO)
- `CIRCUIT_SYNTH_LOG_CONSOLE`: Set to "true" for console output during development
- `CIRCUIT_SYNTH_LOG_FILE`: Override default log file path

## Migration from Old System

See `migration_guide.py` for detailed examples of replacing old logging calls.

### Quick Migration

Old:
```python
dashboard_logger = DashboardLogger(username, session_id)
dashboard_logger.log_event('login_success', username=username)
```

New:
```python
log_auth("User login successful", user=username, session=session_id)
```

## File Management

- Log files rotate at 100MB
- Keeps 10 backup files (circuit_synth.log.1, .2, etc.)
- Old logs can be compressed/archived as needed

## Best Practices

1. **Always include user context**: Every log should have `user=` when applicable
2. **Use consistent IDs**: session_id, chat_id, request_id, generation_id
3. **Keep messages concise**: Details go in context parameters
4. **Use appropriate levels**: INFO for normal flow, ERROR for failures
5. **Include measurements**: File sizes, durations, token counts

## Troubleshooting

### Log file not created
- Check logs/ directory exists and is writable
- Verify no permission issues

### Missing context in logs
- Ensure you're passing user/chat/session parameters
- Check you're using the convenience functions correctly

### Performance concerns
- Logs are written synchronously but efficiently
- File rotation happens automatically
- No database overhead unlike old system

## Summary

The unified logging system provides comprehensive visibility into Circuit Synth operations while being dramatically simpler than the previous architecture. One file, one format, complete context - everything you need for debugging and monitoring.