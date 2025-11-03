# Token Budget Monitoring

## Overview

Token budget monitoring tracks LLM usage across autonomous workers, provides alerts when approaching limits, and maintains historical usage data for cost analysis.

## Quick Start

View the dashboard:

```bash
python3 tools/dashboard.py
```

## Configuration

Edit `adws/config.toml`:

```toml
[budget]
monthly_limit = 1000000  # 1M tokens
alert_thresholds = [75, 90, 95]  # Alert at these percentages
currency_per_million_tokens = 3.00  # Cost per 1M tokens
reset_day = 1  # Day of month to reset budget
```

## Features

- **Real-time Tracking** - Monitor usage vs budget
- **Smart Alerts** - Get notified at 75%, 90%, 95% thresholds
- **Usage History** - Track trends over time
- **Cost Estimation** - Calculate estimated costs
- **Worker Breakdown** - See which workers use the most tokens
- **SQLite Storage** - Lightweight persistent data

## Usage

```bash
# View dashboard
python3 tools/dashboard.py

# JSON output
python3 tools/dashboard.py --json

# Watch mode
watch -n 5 python3 tools/dashboard.py
```

## Architecture

1. **budget_tracker.py** - Core tracking and database
2. **log_parser.py** - Extract usage from Claude logs
3. **tools/dashboard.py** - CLI dashboard
4. **coordinator.py** - Automatic tracking on worker completion

## Database Schema

**usage_records**: timestamp, worker_id, issue_number, tokens, cost, period

**alert_history**: timestamp, alert_level, percentage_used, message

## See Also

- [coordinator README](./README.md)
- [config.toml](./config.toml)
