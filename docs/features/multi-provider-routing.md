# Multi-Provider Model Routing Architecture

## Vision

Enable flexible routing of tasks to different AI providers and models based on task characteristics, enabling:
- **Cost optimization** - Use cheap models for simple tasks, expensive for complex
- **Provider diversity** - Switch between Claude, OpenRouter, OpenAI, Grok, etc.
- **Workflow layers** - Different models for different stages (planning vs execution)
- **Easy swapping** - Change providers/models via config, no code changes

## Current State (PR #488)

**What works:**
- Command template uses `{prompt_file}` and `{model}` placeholders
- Single model configurable via `config.toml`
- API logger tracks tokens/costs

**Limitations:**
- Only supports Claude CLI
- Hardcoded cost table (3 Claude models)
- No task-based routing
- No provider abstraction

## Proposed Architecture

### 1. Provider Abstraction

Each provider has its own configuration:

```toml
[providers.claude-cli]
enabled = true
command_template = ["claude", "-p", "{prompt_file}", "--model", "{model}", ...]

[providers.openrouter]
enabled = true
api_key_env = "OPENROUTER_API_KEY"
command_template = ["curl", "-X", "POST", "https://openrouter.ai/api/v1/...", ...]

[providers.openai]
enabled = true
command_template = ["openai", "api", "chat.completions.create", ...]
```

### 2. Model Catalog

Define models with costs and capabilities:

```toml
[[models]]
name = "claude-sonnet-4-5"
provider = "claude-cli"
cost_per_million_input = 3.0
cost_per_million_output = 15.0
capabilities = ["code", "reasoning", "vision"]

[[models]]
name = "deepseek/deepseek-chat"
provider = "openrouter"
cost_per_million_input = 0.14
cost_per_million_output = 0.28
capabilities = ["code", "cheap"]
```

### 3. Routing Rules

Route tasks to models based on conditions:

```toml
[routing]
default_model = "claude-sonnet-4-5"

[[routing.rules]]
condition = "priority == 0"
model = "claude-opus-4"
reason = "Critical tasks get best model"

[[routing.rules]]
condition = "labels contains 'documentation'"
model = "claude-haiku-4"
reason = "Docs don't need expensive model"

[[routing.rules]]
condition = "hour >= 22 or hour <= 6"
model = "deepseek/deepseek-chat"
reason = "Night jobs use budget model"
```

## Implementation Plan

### Phase 1: Dynamic Cost Loading (Quick Win)

**Goal:** Remove hardcoded costs, load from config

```python
# api_logger.py - instead of hardcoded dict
class ClaudeAPILogger:
    def __init__(self, log_dir: Path, model_catalog: dict):
        self.log_dir = log_dir
        self.cost_table = self._build_cost_table(model_catalog)

    def _build_cost_table(self, catalog):
        """Build cost lookup from config models"""
        return {
            model['name']: {
                'input': model['cost_per_million_input'],
                'output': model['cost_per_million_output']
            }
            for model in catalog
        }
```

**Benefit:** Can add new models to config without code changes

### Phase 2: Provider Abstraction (Medium Effort)

**Goal:** Support multiple providers

```python
# adw_modules/providers.py
class Provider:
    def __init__(self, name, config):
        self.name = name
        self.command_template = config['command_template']
        self.enabled = config.get('enabled', True)

    def build_command(self, prompt_file, model, output_file):
        """Build command from template with substitutions"""
        cmd = []
        for part in self.command_template:
            cmd.append(
                part.replace('{prompt_file}', str(prompt_file))
                    .replace('{model}', model)
                    .replace('{output_file}', str(output_file))
            )
        return cmd

# coordinator.py
class Coordinator:
    def __init__(self, config_path):
        # Load all providers
        self.providers = {
            name: Provider(name, cfg)
            for name, cfg in self.config['providers'].items()
            if cfg.get('enabled', True)
        }
```

**Benefit:** Can switch providers by changing config

### Phase 3: Model Routing (Powerful)

**Goal:** Intelligently route tasks to models

```python
# adw_modules/routing.py
class ModelRouter:
    def __init__(self, routing_config, models):
        self.rules = routing_config['rules']
        self.default = routing_config['default_model']
        self.models = {m['name']: m for m in models}

    def select_model(self, task) -> str:
        """Select model based on task attributes"""
        context = {
            'priority': task.priority,
            'labels': task.labels,
            'retry_count': task.error_tracking.attempt_count,
            'hour': datetime.now().hour
        }

        # Evaluate rules in order
        for rule in self.rules:
            if self._eval_condition(rule['condition'], context):
                print(f"🎯 Routing: {rule['reason']}")
                return rule['model']

        return self.default

# coordinator.py - in spawn_worker()
model = self.router.select_model(task)
provider = self.models[model]['provider']
cmd = self.providers[provider].build_command(prompt_file, model, log_file)
```

**Benefit:** Automatic cost optimization, context-aware routing

### Phase 4: Multi-Stage Workflows (Advanced)

**Goal:** Different models for different workflow stages

```toml
[workflows.standard]
stages = [
    { name = "plan", model = "claude-haiku-4" },
    { name = "implement", model = "claude-sonnet-4-5" },
    { name = "review", model = "claude-opus-4" }
]

[workflows.budget]
stages = [
    { name = "plan", model = "gpt-4o-mini" },
    { name = "implement", model = "deepseek/deepseek-chat" },
    { name = "review", model = "claude-haiku-4" }
]
```

## Use Cases

### Example 1: Cost Optimization
```toml
# p0 (critical) → Claude Opus ($$$)
# p1 (normal) → Claude Sonnet ($$)
# p2+ (low) → DeepSeek ($)
# Night hours → DeepSeek ($)
```

**Result:** 70% cost reduction on non-critical tasks

### Example 2: Provider Failover
```toml
[[routing.rules]]
condition = "provider_status['claude-cli'] == 'down'"
model = "anthropic/claude-3.5-sonnet"  # OpenRouter fallback
```

**Result:** High availability even if Claude CLI fails

### Example 3: Experimentation
```toml
[[routing.rules]]
condition = "task.id ends_with '0'"  # 10% of tasks
model = "grok-beta"
reason = "A/B test Grok performance"
```

**Result:** Easy to test new models on subset of traffic

## Migration Path

**Phase 1** (PR #489 - Quick):
- Move costs from hardcoded to config
- Update API logger to read from config
- Backward compatible with current setup

**Phase 2** (PR #490 - Medium):
- Add provider abstraction
- Keep current Claude CLI as default
- Add OpenRouter as optional provider

**Phase 3** (PR #491 - Powerful):
- Implement routing engine
- Add example routing rules
- Dashboard shows model distribution

**Phase 4** (Future):
- Multi-stage workflows
- Cost budget management
- Model performance analytics

## Benefits

1. **Cost Control** - Use expensive models only when needed
2. **Flexibility** - Easy to try new providers (OpenRouter has 200+ models)
3. **Resilience** - Failover to backup providers
4. **Experimentation** - A/B test models without code changes
5. **Optimization** - Learn which models work best for which tasks

## See Also

- `config.example.toml` - Full example configuration
- `adws/config.toml` - Current simple configuration
- PR #488 - Current API tracking implementation
