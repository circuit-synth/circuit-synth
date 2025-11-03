# Multi-Provider AI Routing System

Intelligent routing system for cost optimization and provider redundancy in TAC-8 Coordinator.

## Overview

The multi-provider routing system enables the coordinator to:
- **Use multiple AI providers** (Claude CLI, OpenRouter, future providers)
- **Intelligently route tasks** based on priority, labels, retry count, time-of-day
- **Optimize costs** by using cheaper models for simple tasks
- **Provide redundancy** if one provider is unavailable

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Coordinator                                          │
│  ├─ Task Queue (from GitHub issues)                 │
│  ├─ ModelRouter (selects provider/model)           │
│  ├─ ProviderManager (manages providers)            │
│  └─ Worker Spawner (executes with selected model)  │
└─────────────────────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
    ┌──────▼──────┐               ┌───────▼────────┐
    │ Claude CLI   │               │ OpenRouter API │
    │ Provider     │               │ Provider       │
    └──────────────┘               └────────────────┘
```

## Components

### 1. Provider Abstraction (`adw_modules/providers.py`)

Unified interface for multiple AI providers.

**Features:**
- Abstract `Provider` class with command building
- `ProviderManager` for loading/managing providers
- Automatic provider availability detection
- Support for CLI and API-based providers

**Example:**
```python
from adw_modules.providers import ProviderManager

provider_manager = ProviderManager(config)
provider = provider_manager.get_provider('claude-cli')
cmd = provider.build_command(prompt_file, model, output_file)
```

### 2. Model Routing (`adw_modules/routing.py`)

Rule-based intelligent model selection.

**Features:**
- Priority-ordered routing rules (100=highest)
- Condition matching (priority, labels, retry_count, hour_range)
- Falls back to config defaults when routing disabled
- Logging of routing decisions

**Example:**
```python
from adw_modules.routing import ModelRouter

router = ModelRouter(config)
provider, model = router.route({
    'priority': 'critical',
    'labels': ['security'],
    'retry_count': 0
})
# → ('claude-cli', 'claude-opus-4')
```

### 3. OpenRouter Integration (`tools/openrouter-cli.py`)

CLI wrapper for OpenRouter API, compatible with provider system.

**Features:**
- Command-line interface matching Claude CLI
- Stream-JSON output format
- Full token usage tracking
- Access to 200+ models

**Usage:**
```bash
export OPENROUTER_API_KEY="sk-..."
./tools/openrouter-cli.py \
  -p prompt.txt \
  --model anthropic/claude-3.5-sonnet \
  --output-file output.jsonl \
  --output-format stream-json
```

## Configuration

### Basic Setup (`adws/config.toml`)

```toml
# Provider configurations
[providers.claude-cli]
enabled = true
command_template = [
    "claude",
    "-p", "{prompt_file}",
    "--model", "{model}",
    "--output-format", "stream-json",
    "--verbose",
    "--dangerously-skip-permissions"
]

[providers.openrouter]
enabled = true
requires_api_key = true
api_key_env = "OPENROUTER_API_KEY"
command_template = [
    "tools/openrouter-cli.py",
    "-p", "{prompt_file}",
    "--model", "{model}",
    "--output-file", "{output_file}",
    "--output-format", "stream-json"
]

# Default provider and model
[llm]
provider = "claude-cli"
model_default = "claude-sonnet-4-5"

# Routing configuration
[routing]
enabled = false  # Set to true to enable intelligent routing
default_provider = "claude-cli"
default_model = "claude-sonnet-4-5"
```

### Routing Rules

Rules are checked in priority order (highest first).

```toml
# Critical tasks use most powerful model
[[routing.rules]]
name = "critical-issues-opus"
priority = 100
conditions = { priority = "critical" }
provider = "claude-cli"
model = "claude-opus-4"

# Retries use cheaper model (checked before priority rules)
[[routing.rules]]
name = "retry-use-haiku"
priority = 95
conditions = { retry_count = { gte = 1 } }
provider = "claude-cli"
model = "claude-haiku-4"

# Normal/high priority use Sonnet
[[routing.rules]]
name = "high-priority-sonnet"
priority = 90
conditions = { priority = ["high", "normal"] }
provider = "claude-cli"
model = "claude-sonnet-4-5"

# Off-hours use cheaper model
[[routing.rules]]
name = "off-hours-haiku"
priority = 70
conditions = { hour_range = [0, 8] }
provider = "claude-cli"
model = "claude-haiku-4"

# Documentation tasks use Haiku
[[routing.rules]]
name = "docs-haiku"
priority = 60
conditions = { labels = ["documentation", "docs"] }
provider = "claude-cli"
model = "claude-haiku-4"
```

### Condition Types

| Condition | Type | Description | Example |
|-----------|------|-------------|---------|
| `priority` | String or List | Match task priority | `"critical"` or `["high", "normal"]` |
| `labels` | List | Match any of these labels | `["docs", "documentation"]` |
| `retry_count` | Dict or Int | Numeric comparison | `{ gte = 1 }` (greater than or equal to 1) |
| `hour_range` | List[int, int] | Time-based routing | `[0, 8]` (midnight to 8am) |

Retry count operators:
- `gte`: Greater than or equal
- `lte`: Less than or equal
- `eq`: Equal to

## Tools

### `tools/show-providers.py`

Display configured providers and their status.

```bash
$ ./tools/show-providers.py

======================================================================
🔌 Configured AI Providers
======================================================================

Provider Status:
  ✓ claude-cli
  ✗ openrouter           (OPENROUTER_API_KEY not set)

======================================================================
Available Providers:
  ✓ claude-cli

Current default:
  Provider: claude-cli
  Model: claude-sonnet-4-5
======================================================================
```

### `tools/show-routing.py`

View routing rules and test scenarios.

```bash
$ ./tools/show-routing.py

======================================================================
🧭 Model Routing Configuration
======================================================================

Router enabled: False
Default: claude-cli/claude-sonnet-4-5

Routing Rules (priority order):
  [100] critical-issues-opus
      Conditions: {'priority': 'critical'}
      Target: claude-cli/claude-opus-4
  [95] retry-use-haiku
      Conditions: {'retry_count': {'gte': 1}}
      Target: claude-cli/claude-haiku-4
...

======================================================================
ROUTING DECISION TESTS
======================================================================

Scenario: Critical security issue
  Attrs: {'priority': 'critical', 'labels': ['security'], 'retry_count': 0}
  → Routed to: claude-cli / claude-opus-4

Scenario: Documentation update
  Attrs: {'priority': 'low', 'labels': ['documentation'], 'retry_count': 0}
  → Routed to: claude-cli / claude-haiku-4
```

## Usage

### Enable Routing

1. Edit `adws/config.toml`:
```toml
[routing]
enabled = true
```

2. Restart coordinator or reload config

### Add OpenRouter Support

1. Get API key from [OpenRouter](https://openrouter.ai/)

2. Set environment variable:
```bash
export OPENROUTER_API_KEY="sk-..."
```

3. Verify availability:
```bash
./tools/show-providers.py
# Should show openrouter as available
```

4. Add routing rules that use OpenRouter:
```toml
[[routing.rules]]
name = "low-priority-openrouter"
priority = 40
conditions = { priority = "low" }
provider = "openrouter"
model = "anthropic/claude-3.5-haiku"  # Note: OpenRouter uses / namespacing
```

### Monitor Routing Decisions

Check coordinator logs for routing decisions:
```
✓ Rule matched: critical-issues-opus → claude-cli/claude-opus-4
  Task attrs: {'priority': 'critical', 'labels': ['security'], 'retry_count': 0}
```

## Cost Optimization Examples

### Example 1: Retry Strategy

**Problem:** Failed tasks retry with same expensive model.

**Solution:** Use cheaper model for retries.

```toml
[[routing.rules]]
name = "retry-use-haiku"
priority = 95
conditions = { retry_count = { gte = 1 } }
model = "claude-haiku-4"
```

**Savings:** If 20% of tasks retry, save ~80% on retry costs (Haiku is 5x cheaper than Sonnet).

### Example 2: Off-Hours Optimization

**Problem:** Non-urgent tasks run 24/7 with expensive models.

**Solution:** Use cheaper models during off-hours.

```toml
[[routing.rules]]
name = "off-hours-haiku"
priority = 70
conditions = { hour_range = [0, 8] }
model = "claude-haiku-4"
```

**Savings:** ~30% of tasks during off-hours, 80% cost reduction = 24% overall savings.

### Example 3: Task-Type Routing

**Problem:** Simple documentation tasks use expensive models.

**Solution:** Route by label to cheaper models.

```toml
[[routing.rules]]
name = "docs-haiku"
priority = 60
conditions = { labels = ["documentation", "docs"] }
model = "claude-haiku-4"
```

**Savings:** If 15% of tasks are docs, save ~12% overall.

### Combined Impact

All three strategies combined:
- Retries: 24% savings on 20% of tasks = 4.8%
- Off-hours: 24% savings overall = 24%
- Docs: 12% savings on 15% of tasks = 1.8%

**Total potential savings: ~30%** with no reduction in quality for appropriate tasks.

## Adding New Providers

### Step 1: Create Provider Wrapper (if API-based)

For API-based providers, create a CLI wrapper in `tools/`:

```python
#!/usr/bin/env python3
"""
MyProvider CLI wrapper
"""

import argparse
import json
from pathlib import Path

def call_myprovider_api(prompt, model, api_key):
    # Call provider API
    pass

def write_stream_json_output(output_file, response):
    # Write stream-JSON format
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prompt', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output-file', required=True)
    args = parser.parse_args()

    # Implementation
    pass

if __name__ == '__main__':
    main()
```

### Step 2: Add Provider Config

Edit `adws/config.toml`:

```toml
[providers.myprovider]
enabled = true
requires_api_key = true
api_key_env = "MYPROVIDER_API_KEY"
command_template = [
    "tools/myprovider-cli.py",
    "-p", "{prompt_file}",
    "--model", "{model}",
    "--output-file", "{output_file}"
]
```

### Step 3: Add Routing Rules

```toml
[[routing.rules]]
name = "myprovider-fallback"
priority = 10
conditions = { retry_count = { gte = 2 } }
provider = "myprovider"
model = "myprovider/some-model"
```

### Step 4: Verify

```bash
./tools/show-providers.py
# Should show myprovider as available
```

## Troubleshooting

### Provider shows as unavailable

**Check:**
1. API key set: `echo $PROVIDER_API_KEY`
2. Command exists: `which command` or check `tools/` directory
3. Command executable: `ls -la tools/provider-cli.py`

**Debug:**
```bash
./tools/show-providers.py  # Shows detailed status
```

### Routing not working

**Check:**
1. Routing enabled: `grep "enabled = true" adws/config.toml`
2. Rules configured: `./tools/show-routing.py`
3. Task attributes correct: Check coordinator logs

**Debug:**
```bash
./tools/show-routing.py  # Shows routing decisions
# Enable debug logging in coordinator
```

### OpenRouter authentication fails

**Check:**
1. API key correct: `echo $OPENROUTER_API_KEY`
2. Test directly:
```bash
./tools/openrouter-cli.py \
  -p test-prompt.txt \
  --model anthropic/claude-3.5-sonnet \
  --output-file test-output.jsonl
```

## Future Enhancements

Planned improvements:
- [ ] Dynamic cost-based routing (select cheapest model that meets requirements)
- [ ] Provider failover (try backup provider if primary fails)
- [ ] Model performance tracking (success rate, avg duration)
- [ ] Load balancing across providers
- [ ] Rate limit awareness
- [ ] Per-user/per-project provider preferences
- [ ] Web UI for routing rule management

## Related Documents

- [API Tracking System](../api-tracking/README.md)
- [Live Model Pricing](../live-pricing/README.md)
- [Error Handling](../error-handling/README.md)
- [Coordinator Architecture](../../ARCHITECTURE.md)

## Version History

- **2025-11-03**: Initial implementation
  - Provider abstraction layer
  - Model routing engine
  - OpenRouter support
  - Configuration and tools
