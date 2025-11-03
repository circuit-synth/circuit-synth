# Viewing TAC-8 Conversation Logs

TAC-8 coordinator stores worker conversations in JSONL (JSON Lines) format using Claude CLI's stream-json output.

## Quick Start

```bash
# List all conversation logs
./tools/query-logs.py list

# Summary of all conversations with token counts
./tools/query-logs.py summary

# View token usage for specific task
./tools/query-logs.py tokens gh-450

# View full conversation
./tools/view-conversation.py logs/gh-449.jsonl

# View just the summary
./tools/view-conversation.py logs/gh-449.jsonl --summary

# Search for text in all conversations
./tools/query-logs.py search "error handling"

# Find conversations with errors
./tools/query-logs.py errors
```

## Log File Format

Conversation logs are stored in `logs/gh-XXX.jsonl` where XXX is the GitHub issue number.

Each line in the JSONL file is a JSON object representing an event in the conversation stream:

### Event Types

1. **System Event** (first line) - Session initialization
```json
{
  "type": "system",
  "session_id": "59f8038c-4fa8-416a-931a-f8d856c067c8",
  "model": "claude-sonnet-4-5",
  "cwd": "/home/shane/Desktop/circuit-synth/trees/gh-449",
  "tools": ["Task", "Bash", "Read", "Write", ...]
}
```

2. **User Message** - Input from user or coordinator
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {"type": "text", "text": "Fix the bug in coordinator.py"}
    ]
  },
  "session_id": "..."
}
```

3. **Assistant Message** - Claude's response
```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {"type": "text", "text": "I'll help fix the bug."},
      {"type": "tool_use", "name": "Read", "input": {"file_path": "..."}}
    ],
    "usage": {
      "input_tokens": 5000,
      "output_tokens": 200,
      "cache_read_input_tokens": 25000
    }
  },
  "session_id": "..."
}
```

## Available Tools

### 1. view-conversation.py

View a single conversation in human-readable format.

**Usage:**
```bash
# Full conversation with all events
./tools/view-conversation.py logs/gh-449.jsonl

# Just the summary
./tools/view-conversation.py logs/gh-449.jsonl --summary

# Only message events (skip system events)
./tools/view-conversation.py logs/gh-449.jsonl --messages-only
```

**Output Example:**
```
================================================================================
CONVERSATION LOG: gh-449.jsonl
Total lines: 73
================================================================================

CONVERSATION SUMMARY
Total events: 73
System events: 1
User messages: 27
Assistant messages: 45
Tool calls: 27
Errors: 0

SYSTEM INFO #1
Session ID: 59f8038c-4fa8-416a-931a-f8d856c067c8
Model: claude-sonnet-4-5

USER MESSAGE #4
Fix the spawn loop bug

ASSISTANT MESSAGE #5
[Tokens: 6 in, 92 out]

I'll help fix the spawn loop bug. Let me first read the coordinator code:

[TOOL: Read]
  file_path: adws/coordinator.py
...
```

### 2. query-logs.py

Query and analyze multiple conversation logs.

**Commands:**

#### list
List all conversation logs with sizes and event counts.

```bash
./tools/query-logs.py list
```

Output:
```
CONVERSATION LOGS (10 total)
gh-449             65.8 KB    73 events
gh-450            234.5 KB   210 events
gh-451            141.1 KB    87 events
...
```

#### summary
Show comprehensive summary of all conversations.

```bash
./tools/query-logs.py summary
```

Output:
```
Task            Events   User   Asst   Tools  Tokens In    Tokens Out
--------------------------------------------------------------------------------
gh-449          73       27     45     27     60           6,351
gh-450          210      78     128    78     540          472
gh-451          87       33     53     33     23,968       10,770
--------------------------------------------------------------------------------
TOTALS          828      308    505    306    49,402       36,403

10 tasks processed
Total tokens: 85,805
```

#### tokens
Show token usage for specific task or all tasks.

```bash
# Specific task
./tools/query-logs.py tokens gh-449

# All tasks (same as summary)
./tools/query-logs.py tokens
```

Output:
```
TOKEN USAGE: gh-449
Model: claude-sonnet-4-5

Input tokens:  60
Output tokens: 6,351
Total tokens:  6,411

Messages: 27 user, 45 assistant
Tool calls: 27
```

#### search
Search for specific text across all conversations.

```bash
./tools/query-logs.py search "error handling"
./tools/query-logs.py search "spawn loop"
```

Output:
```
SEARCH RESULTS: 'spawn loop'

gh-452: 3 match(es)
  Event #45: I found the spawn loop issue in the coordinator...
  Event #67: The spawn loop occurs when worktrees are removed...
  Event #89: Fixed the spawn loop by preserving recent work...
```

#### errors
Find all conversations that encountered errors.

```bash
./tools/query-logs.py errors
```

## Manual Viewing

You can also view logs manually using standard Unix tools:

```bash
# View file directly
cat logs/gh-449.jsonl | less

# Count events
wc -l logs/gh-449.jsonl

# Extract just user messages
grep '"type":"user"' logs/gh-449.jsonl | jq '.message.content[0].text'

# Extract token counts
grep '"type":"assistant"' logs/gh-449.jsonl | jq '.message.usage'

# Pretty-print specific line
sed -n '5p' logs/gh-449.jsonl | jq '.'
```

## API Call Logs

Separate from conversation logs, API call metrics are stored in `logs/api/api-calls-YYYY-MM-DD.jsonl`.

**Format:**
```json
{
  "timestamp": "2025-11-03T10:30:45Z",
  "task_id": "gh-450",
  "model": "claude-sonnet-4-5",
  "prompt_tokens": 5000,
  "completion_tokens": 200,
  "cache_creation_tokens": 1500,
  "cache_read_tokens": 25000,
  "total_tokens": 31700,
  "estimated_cost_usd": 0.42,
  "duration_seconds": 3.2
}
```

**Viewing:**
```bash
# Today's API calls
cat logs/api/api-calls-2025-11-03.jsonl | jq '.'

# Total cost today
cat logs/api/api-calls-2025-11-03.jsonl | jq '.estimated_cost_usd' | awk '{sum+=$1} END {print sum}'

# Calls by model
cat logs/api/api-calls-*.jsonl | jq -r '.model' | sort | uniq -c
```

## Troubleshooting

### Corrupted JSONL Files

Some log files may become corrupted (all null bytes or encoding errors). Common causes:
- Worker crash during write
- Disk full during logging
- Interrupted file system operations

**Detection:**
```bash
# Check file type
file logs/gh-450.jsonl

# If it shows "data" instead of "JSON text data", file is corrupted
```

**Recovery:**
- Corrupted files show 0 events in query tools
- Original data is lost - cannot be recovered
- Future workers will create new logs

### Encoding Errors

Some files may have UTF-8 encoding errors from binary data or invalid characters.

**Workaround:**
```bash
# Use errors='ignore' when reading
cat logs/gh-455.jsonl | iconv -f utf-8 -t utf-8 -c | jq '.'
```

The query tools automatically skip malformed lines.

## Next Steps: SQLite Integration

Currently, all logs are in JSONL format. The planned SQLite logging system will:

1. **Keep JSONL as source of truth** for full conversation content
2. **Add SQLite database** for fast queries and aggregations
3. **Index metadata** in SQLite (task IDs, timestamps, token counts, session IDs)
4. **Link to JSONL** via file path references in database

See: `docs/design/TAC-8-SIMPLIFIED-LOGGING.md` for full design.

**Benefits of SQLite addition:**
- Fast queries without parsing JSONL
- Relationships between tasks, workers, sessions
- Aggregations (total cost per day, tokens by model)
- Historical trends and analytics
- Dashboard integration

**JSONL stays for:**
- Full conversation content (don't duplicate in DB)
- Sequential append-only writes
- Easy grep/search
- Long-term archival (compress old files)

---

**Tools Location:**
- `./tools/view-conversation.py` - View single conversation
- `./tools/query-logs.py` - Query multiple conversations

**Log Locations:**
- `logs/gh-*.jsonl` - Worker conversation logs
- `logs/api/api-calls-*.jsonl` - API call metrics

**Design Docs:**
- `docs/design/TAC-8-SIMPLIFIED-LOGGING.md` - SQLite logging design
- `docs/design/TAC-8-COMPREHENSIVE-LOGGING.md` - Original complex design (superseded)
