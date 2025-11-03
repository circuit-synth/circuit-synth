# API Usage Tracking

Monitors all Claude API calls to prevent token exhaustion and control costs.

## Quick Start

```bash
pip install -r dashboard/requirements.txt
python dashboard/api_dashboard.py  # http://localhost:8050
./tools/api-usage-report.py --week # CLI reports
```

## Components

- `adws/adw_modules/api_logger.py` - Core tracking
- `dashboard/api_dashboard.py` - Web dashboard  
- `tools/api-usage-report.py` - CLI tool

## Integration

See api_logger.py docstrings for coordinator.py integration.
