# Claude API Usage Dashboard

Real-time monitoring and analysis of Claude API usage for the TAC-8 coordinator.

## Features

### 📊 Live Metrics
- **Summary Cards**: Total calls, success rate, tokens, cost
- **Token Timeline**: Input/output tokens over time (hourly granularity)
- **Cost Tracking**: Daily and cumulative cost tracking
- **Model Breakdown**: Token usage distribution by model (pie chart)
- **Task Performance**: Duration vs tokens scatter plot
- **Activity Heatmap**: Hourly activity patterns by day

### 🔄 Real-time Updates
- Auto-refreshes every 30 seconds
- Manual refresh button
- Configurable time ranges (24h, 7d, 30d)

### 💡 Interactive Features
- Hover for detailed information
- Zoom and pan on all graphs
- Filter by time range
- Click to explore

## Installation

```bash
# Install dashboard dependencies
pip install -r dashboard/requirements.txt
```

## Usage

### Start the Dashboard

```bash
python dashboard/api_dashboard.py
```

Then open in browser: **http://localhost:8050**

### Command-Line Reports

For quick terminal-based reports:

```bash
# Today's summary
./tools/api-usage-report.py

# Specific date
./tools/api-usage-report.py --date 2025-11-02

# Last 7 days
./tools/api-usage-report.py --week

# Last 30 days
./tools/api-usage-report.py --month

# Show detailed calls
./tools/api-usage-report.py --detail
```

## How It Works

### 1. API Logging (Automatic)

The coordinator logs every Claude API call to `logs/api/api-calls-YYYY-MM-DD.jsonl`:

```json
{
  "timestamp": "2025-11-02T21:30:00",
  "task_id": "gh-456",
  "worker_id": "w-abc123",
  "model": "claude-sonnet-4-5",
  "tokens_input": 12500,
  "tokens_output": 3200,
  "tokens_total": 15700,
  "duration_seconds": 45.2,
  "tokens_per_second": 70.8,
  "estimated_cost_usd": 0.0855,
  "success": true
}
```

### 2. Data Storage

- **Format**: JSONL (one JSON object per line)
- **Location**: `logs/api/api-calls-YYYY-MM-DD.jsonl`
- **Rotation**: Daily (one file per day)
- **Retention**: Keep as long as needed (analyze trends)

### 3. Metrics Tracked

**Request Info:**
- Timestamp, task ID, worker ID
- Model, prompt file, prompt length

**Response Info:**
- Response length
- Tokens (input/output/total)
- Success/failure status
- Error messages

**Performance:**
- Duration (total, time to first token)
- Tokens per second
- Exit code

**Cost:**
- Estimated cost per call
- Cost by model
- Daily/cumulative totals

## Cost Estimation

Prices per million tokens (approximate):

| Model | Input | Output |
|-------|-------|--------|
| Sonnet 4.5 | $3.00 | $15.00 |
| Opus 4 | $15.00 | $75.00 |
| Haiku 4 | $0.25 | $1.25 |

## Integration

### Adding to Coordinator

See `adws/coordinator-integration-example.py` for full integration example.

**Key steps:**

1. **Import logger:**
   ```python
   from adw_modules.api_logger import ClaudeAPILogger
   ```

2. **Initialize in `__init__`:**
   ```python
   self.api_logger = ClaudeAPILogger(LOGS_DIR / 'api')
   ```

3. **Start tracking in `spawn_worker()`:**
   ```python
   metrics = self.api_logger.start_call(
       task_id=task.id,
       worker_id=task.worker_id,
       model=model,
       prompt_file=str(prompt_file),
       prompt_content=prompt
   )
   task.api_metrics = metrics
   ```

4. **Complete tracking in `check_completions()`:**
   ```python
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

## Dashboard Access

### Local Access (on RPi)
```
http://localhost:8050
```

### Remote Access (from your computer)
```
http://<rpi-ip-address>:8050
```

### SSH Tunnel (if firewall blocks access)
```bash
ssh -L 8050:localhost:8050 shane@<rpi-ip>
```
Then access: `http://localhost:8050`

## Troubleshooting

### No data showing
- Check if coordinator is running with API logging enabled
- Verify logs exist in `logs/api/`
- Check file permissions

### Dashboard won't start
- Install dependencies: `pip install -r dashboard/requirements.txt`
- Check port 8050 is not in use: `lsof -i :8050`

### Slow performance
- Reduce time range (use 7 days instead of 30)
- Archive old log files
- Increase auto-refresh interval in code

## Files

```
circuit-synth/
├── adws/
│   └── adw_modules/
│       └── api_logger.py          # Core logging module
├── dashboard/
│   ├── api_dashboard.py           # Plotly Dash dashboard
│   ├── requirements.txt           # Dashboard dependencies
│   └── README.md                  # This file
├── tools/
│   └── api-usage-report.py        # CLI reporting tool
└── logs/
    └── api/
        └── api-calls-*.jsonl      # Daily log files
```

## Future Enhancements

Potential additions:
- [ ] Budget alerts (email/Slack when approaching limit)
- [ ] Cost projections (forecast monthly spend)
- [ ] Worker efficiency rankings
- [ ] Anomaly detection (unusually high token usage)
- [ ] Export to CSV/Excel for accounting
- [ ] Historical comparison (week-over-week, month-over-month)
- [ ] Real-time worker monitoring (live updates while running)
- [ ] Token quota management (pause workers at threshold)
