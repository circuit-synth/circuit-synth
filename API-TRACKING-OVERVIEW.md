# Claude API Usage Tracking - Complete Overview

## 🎯 Goal
Track **every Claude API call** from the TAC coordinator to monitor token usage, costs, and performance.

## 📊 What Gets Tracked

### Per API Call:
- ✅ **Tokens**: Input, output, total
- ✅ **Time**: Duration, time to first token, tokens/sec
- ✅ **Cost**: Estimated USD (by model)
- ✅ **Context**: Task ID, worker ID, model, settings
- ✅ **Content**: Prompt and response (for debugging)
- ✅ **Status**: Success/failure, error messages

### Aggregated:
- ✅ Daily/weekly/monthly totals
- ✅ Trends over time
- ✅ Cost projections
- ✅ Performance metrics
- ✅ Worker efficiency

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TAC-8 Coordinator                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  spawn_worker()                                      │   │
│  │    1. Create prompt                                  │   │
│  │    2. START LOGGING ← api_logger.start_call()       │   │
│  │    3. Spawn Claude CLI process                       │   │
│  │    4. Store metrics reference on task                │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Claude CLI Process                                  │   │
│  │    - Reads prompt                                    │   │
│  │    - Calls Anthropic API                            │   │
│  │    - Streams response to JSONL file                  │   │
│  │    - Includes token usage in output                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  check_completions()                                 │   │
│  │    1. Detect worker finished                         │   │
│  │    2. Parse JSONL output for tokens                  │   │
│  │    3. END LOGGING ← api_logger.end_call()           │   │
│  │    4. Write to logs/api/api-calls-YYYY-MM-DD.jsonl  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  logs/api/api-calls-2025-11-02.jsonl  │
        │  (One line per API call)              │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────┬───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Dashboard   │   │  CLI Report  │   │  Analysis    │
│  (Plotly)    │   │  (Terminal)  │   │  (Custom)    │
└──────────────┘   └──────────────┘   └──────────────┘
```

## 📂 File Structure

```
circuit-synth/
├── adws/
│   ├── coordinator.py                    # Main coordinator (needs integration)
│   ├── coordinator-integration-example.py # Integration guide
│   └── adw_modules/
│       └── api_logger.py                 # Core logging module
│
├── dashboard/
│   ├── api_dashboard.py                  # Plotly Dash web dashboard
│   ├── requirements.txt                  # Dashboard dependencies
│   └── README.md                         # Dashboard documentation
│
├── tools/
│   └── api-usage-report.py               # CLI reporting tool
│
└── logs/
    └── api/
        ├── api-calls-2025-11-01.jsonl    # Daily log files
        ├── api-calls-2025-11-02.jsonl
        └── ...
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r dashboard/requirements.txt
```

### 2. Integrate into Coordinator

Add to `adws/coordinator.py`:

```python
# At top of file
from adw_modules.api_logger import ClaudeAPILogger

# In Coordinator.__init__()
self.api_logger = ClaudeAPILogger(LOGS_DIR / 'api')

# In spawn_worker() - before spawning
metrics = self.api_logger.start_call(
    task_id=task.id,
    worker_id=task.worker_id,
    model=model,
    prompt_file=str(prompt_file),
    prompt_content=prompt
)
task.api_metrics = metrics

# In check_completions() - after worker finishes
log_file = LOGS_DIR / f"{task.id}.jsonl"
usage = self.api_logger.parse_stream_json_output(log_file)

self.api_logger.end_call(
    metrics=task.api_metrics,
    response_content=usage['response_content'],
    tokens_input=usage['tokens_input'],
    tokens_output=usage['tokens_output'],
    success=(task.status == 'completed'),
    error_message=task.error
)
```

See `adws/coordinator-integration-example.py` for complete code.

### 3. Start Dashboard

```bash
python dashboard/api_dashboard.py
```

Open: http://localhost:8050

### 4. View Reports (CLI)

```bash
# Today's summary
./tools/api-usage-report.py

# Last week
./tools/api-usage-report.py --week

# Detailed calls
./tools/api-usage-report.py --detail
```

## 📈 Dashboard Features

### Summary Cards
- Total API calls
- Successful calls
- Total tokens used
- Estimated cost (USD)

### Token Timeline
- Hourly granularity
- Stacked area: input vs output tokens
- Interactive zoom/pan

### Cost Tracking
- Daily cost bars
- Cumulative cost line
- Dual y-axis

### Model Breakdown
- Pie chart: token usage by model
- Hover: tokens + cost per model

### Task Performance
- Scatter: duration vs tokens
- Color: success/failure
- Hover: task ID, worker ID, cost

### Activity Heatmap
- Hourly activity patterns
- By date and hour
- Color intensity: number of calls

### Auto-Refresh
- Updates every 30 seconds
- Manual refresh button
- Configurable time ranges (24h/7d/30d)

## 💰 Cost Estimation

Built-in pricing (per million tokens):

| Model | Input | Output |
|-------|-------|--------|
| Sonnet 4.5 | $3.00 | $15.00 |
| Opus 4 | $15.00 | $75.00 |
| Haiku 4 | $0.25 | $1.25 |

Example calculation:
- Input: 10,000 tokens = $0.03
- Output: 2,000 tokens = $0.03
- **Total: $0.06 per call**

## 🔍 Example Log Entry

```json
{
  "timestamp": "2025-11-02T21:30:45.123456",
  "task_id": "gh-456",
  "worker_id": "w-abc123",
  "model": "claude-sonnet-4-5",
  "prompt_file": "/path/to/gh-456-prompt.txt",
  "prompt_length": 4582,
  "response_length": 12453,
  "tokens_input": 12500,
  "tokens_output": 3200,
  "tokens_total": 15700,
  "start_time": 1730595045.123,
  "end_time": 1730595090.321,
  "duration_seconds": 45.198,
  "time_to_first_token": 2.3,
  "tokens_per_second": 70.8,
  "success": true,
  "error_message": null,
  "exit_code": 0,
  "settings": {"worktree": "/path/to/trees/gh-456"},
  "estimated_cost_usd": 0.0855
}
```

## 📊 Sample CLI Report

```
📊 API Usage Summary - 2025-11-02
============================================================
Total Calls:            42
  ✓ Successful:         38
  ✗ Failed:              4

Tokens Used:       658,234
  → Input:         524,187
  → Output:        134,047

Cost (estimated):  $  3.5823

Avg Duration:         45.23s
Avg Tokens/sec:       70.45

By Model:
------------------------------------------------------------
  claude-sonnet-4-5
    Calls:     38
    Tokens:   625,891
    Cost:   $  3.4012

  claude-haiku-4
    Calls:      4
    Tokens:    32,343
    Cost:   $  0.1811
```

## 🎛️ Accessing Dashboard Remotely

### Option 1: Direct Access (if firewall allows)
```
http://<raspberry-pi-ip>:8050
```

### Option 2: SSH Tunnel (recommended)
```bash
# On your laptop
ssh -L 8050:localhost:8050 shane@<raspberry-pi-ip>

# Then open browser to:
http://localhost:8050
```

## 🔧 Configuration

### Change Cost Rates

Edit `adws/adw_modules/api_logger.py`:

```python
COST_PER_MILLION_TOKENS = {
    'claude-sonnet-4-5': {'input': 3.0, 'output': 15.0},
    # Update with current pricing
}
```

### Change Auto-Refresh Interval

Edit `dashboard/api_dashboard.py`:

```python
dcc.Interval(
    id='interval-component',
    interval=30*1000,  # 30 seconds (change this)
    n_intervals=0
)
```

### Change Log Directory

Edit when initializing logger:

```python
logger = ClaudeAPILogger(Path('/custom/log/directory'))
```

## 🐛 Troubleshooting

### No data in dashboard
1. Check if logs exist: `ls -la logs/api/`
2. Verify coordinator has API logging integrated
3. Check file permissions: `chmod -R 755 logs/`

### Dashboard won't start
```bash
# Install dependencies
pip install -r dashboard/requirements.txt

# Check port not in use
lsof -i :8050

# If port in use, change in api_dashboard.py
app.run_server(port=8051)  # Use different port
```

### Coordinator still spawning workers
```bash
# Stop systemd service (requires sudo)
sudo systemctl stop circuit-synth-coordinator.service
sudo systemctl disable circuit-synth-coordinator.service

# Verify stopped
systemctl status circuit-synth-coordinator.service
```

## 📝 Next Steps

1. **Stop the coordinator** (saves tokens during development):
   ```bash
   sudo systemctl stop circuit-synth-coordinator.service
   ```

2. **Integrate API logging** into `coordinator.py` using the example

3. **Test with one task** to verify logging works

4. **Start dashboard** to view real-time metrics

5. **Re-enable coordinator** when ready:
   ```bash
   sudo systemctl start circuit-synth-coordinator.service
   ```

## 🎯 Benefits

✅ **Never wonder about token usage again** - Everything tracked
✅ **Control costs** - See exactly where money goes
✅ **Optimize performance** - Identify slow/expensive calls
✅ **Debug issues** - Full context for every API call
✅ **Plan budget** - Trend analysis and projections
✅ **Interactive exploration** - Dash dashboard makes it easy

## 📚 Documentation

- **API Logger**: `adws/adw_modules/api_logger.py` (docstrings)
- **Dashboard**: `dashboard/README.md`
- **Integration**: `adws/coordinator-integration-example.py`
- **CLI Tool**: `./tools/api-usage-report.py --help`

---

**Questions? Issues?** Check the troubleshooting section or file an issue.
