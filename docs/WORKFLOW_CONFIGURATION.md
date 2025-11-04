# TAC-X Workflow Configuration Guide

This guide explains how to configure TAC-X pipeline with custom LLM providers and models.

## Overview

TAC-X supports multiple LLM providers through a flexible workflow configuration system:

- **Anthropic**: Claude models (Sonnet, Opus, Haiku)
- **OpenAI**: GPT models (GPT-4, GPT-4 Turbo, GPT-4o)
- **OpenRouter**: Universal gateway to 100+ models from multiple providers

## Configuration Format

Workflows are defined in YAML format with these key elements:

```yaml
workflow:
  name: "Custom Pipeline"
  version: "1.0.0"
  description: "Description of workflow"

  stages:
    - name: planning
      agent: planner
      provider: anthropic
      model: claude-sonnet-4-5
      fallback: openai/gpt-4
      temperature: 1.0
      max_tokens: 8192
      tools: ["Read", "Grep", "Glob", "Bash"]

    - name: building
      agent: builder
      provider: openai
      model: gpt-4-turbo
      temperature: 1.0
      # ... more stages ...
```

## Provider Configuration

### Anthropic (Direct)

Use Anthropic's official API directly:

```yaml
- name: planning
  provider: anthropic
  model: claude-sonnet-4-5  # or claude-opus-4, claude-haiku-4-5
```

**Requirements:**
- Set `ANTHROPIC_API_KEY` environment variable
- Install: `pip install anthropic`

**Available Models:**
- `claude-sonnet-4-5` - Best for complex reasoning (recommended)
- `claude-opus-4` - Most capable, highest cost
- `claude-haiku-4-5` - Fastest, lowest cost

### OpenAI (Direct)

Use OpenAI's official API directly:

```yaml
- name: reviewing
  provider: openai
  model: gpt-4-turbo  # or gpt-4, gpt-4o, gpt-4o-mini
```

**Requirements:**
- Set `OPENAI_API_KEY` environment variable
- Install: `pip install openai`

**Available Models:**
- `gpt-4-turbo` - Fast and capable
- `gpt-4o` - Multimodal, efficient
- `gpt-4o-mini` - Lightweight, cost-effective

### OpenRouter (Universal Gateway)

OpenRouter provides unified access to 100+ models from multiple providers:

```yaml
- name: building
  provider: openrouter
  model: anthropic/claude-3.5-sonnet  # OpenRouter model path
```

**Requirements:**
- Set `OPENROUTER_API_KEY` environment variable
- Install: `pip install openai` (OpenRouter uses OpenAI-compatible API)

**Example Models:**
- `anthropic/claude-3.5-sonnet` - Claude via OpenRouter
- `anthropic/claude-3-haiku` - Fast Claude model
- `openai/gpt-4-turbo` - GPT-4 via OpenRouter
- `meta-llama/llama-3.1-70b` - Open source Llama
- `google/gemini-pro` - Google's Gemini
- `mistralai/mixtral-8x7b` - Mistral model

**Benefits:**
- Single API key for all providers
- Automatic fallbacks
- Cost tracking across providers
- Access to open-source models

## Fallback Configuration

Configure fallback models for reliability:

```yaml
- name: planning
  provider: anthropic
  model: claude-sonnet-4-5
  fallback: openai/gpt-4  # Falls back to GPT-4 if Claude fails
```

Fallback format:
- `provider/model` - Explicit provider and model
- Automatically tries fallback if primary fails

## Example Workflows

### Cost-Optimized Workflow

Use cheaper models where appropriate:

```yaml
workflow:
  name: "Cost-Optimized Pipeline"
  stages:
    - name: planning
      provider: openrouter
      model: anthropic/claude-3-haiku  # Cheap, fast planning
      fallback: anthropic/claude-3.5-sonnet

    - name: building
      provider: anthropic
      model: claude-sonnet-4-5  # Complex implementation needs quality

    - name: reviewing
      provider: openrouter
      model: openai/gpt-4o-mini  # Lightweight review

    - name: pr_creation
      provider: anthropic
      model: claude-haiku-4-5  # Simple PR creation
```

**Estimated Cost:** ~$0.10-0.30 per issue

### High-Quality Workflow

Use best models for maximum quality:

```yaml
workflow:
  name: "Premium Quality Pipeline"
  stages:
    - name: planning
      provider: anthropic
      model: claude-opus-4  # Best reasoning

    - name: building
      provider: anthropic
      model: claude-opus-4  # Best implementation

    - name: reviewing
      provider: openai
      model: gpt-4-turbo  # Cross-validation with different model

    - name: pr_creation
      provider: anthropic
      model: claude-sonnet-4-5  # Quality PR descriptions
```

**Estimated Cost:** ~$1-3 per issue

### Mixed Provider Workflow

Combine multiple providers for diversity:

```yaml
workflow:
  name: "Multi-Provider Pipeline"
  stages:
    - name: planning
      provider: openrouter
      model: anthropic/claude-3.5-sonnet
      fallback: openai/gpt-4

    - name: building
      provider: anthropic
      model: claude-sonnet-4-5
      fallback: openrouter/meta-llama/llama-3.1-70b

    - name: reviewing
      provider: openai
      model: gpt-4-turbo  # Different model for independent review
      fallback: openrouter/google/gemini-pro

    - name: pr_creation
      provider: openrouter
      model: anthropic/claude-3-haiku
```

### Open Source Workflow

Use open-source models via OpenRouter:

```yaml
workflow:
  name: "Open Source Pipeline"
  stages:
    - name: planning
      provider: openrouter
      model: meta-llama/llama-3.1-70b

    - name: building
      provider: openrouter
      model: mistralai/mixtral-8x7b

    - name: reviewing
      provider: openrouter
      model: meta-llama/llama-3.1-70b

    - name: pr_creation
      provider: openrouter
      model: mistralai/mistral-7b
```

**Estimated Cost:** ~$0.05-0.15 per issue

## Using Workflows

### Default Workflow

If no custom workflow is specified, TAC-X uses the default:

```python
# No configuration needed - uses default
worker = MultiStageWorker(
    task_id="gh-123",
    issue_number="123",
    worktree_path="/path/to/worktree",
    branch_name="auto/w-123",
    llm_config=config,
    api_logger=logger
)
```

### Custom Workflow from YAML

Load workflow from YAML file:

```python
from adw_modules.workflow_config import WorkflowConfig

# Load custom workflow
workflow = WorkflowConfig.from_yaml(Path("custom-workflow.yaml"))

# Use it
worker = MultiStageWorker(
    # ... other params ...
    workflow_config=workflow
)
```

### Programmatic Workflow

Create workflow in code:

```python
from adw_modules.workflow_config import WorkflowConfig, StageConfig

workflow = WorkflowConfig(
    name="Custom Pipeline",
    version="1.0.0",
    description="Programmatically created workflow",
    stages=[
        StageConfig(
            name="planning",
            agent="planner",
            provider="openrouter",
            model="anthropic/claude-3.5-sonnet",
            temperature=1.0
        ),
        # ... more stages ...
    ]
)

worker = MultiStageWorker(
    # ... other params ...
    workflow_config=workflow
)
```

## Workflow Artifacts

TAC-X automatically generates workflow artifacts:

- `.tac/workflow.yaml` - Workflow configuration used
- `.tac/workflow-diagram.md` - Mermaid diagram visualization
- `.tac/stages/*.jsonl` - Per-stage execution logs with provider/model info

## Environment Variables

Required environment variables by provider:

```bash
# Anthropic (direct)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI (direct)
export OPENAI_API_KEY="sk-..."

# OpenRouter (universal gateway)
export OPENROUTER_API_KEY="sk-or-v1-..."
```

Get API keys:
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys
- OpenRouter: https://openrouter.ai/keys

## Cost Estimation

TAC-X tracks token usage and estimates costs per stage:

```python
# Cost estimates are logged to .tac/stages/*.jsonl
# Access via analyze-pipeline.py tool:

$ python3 tools/analyze-pipeline.py gh-123
# Shows token usage and cost breakdown per stage
```

Approximate costs (per issue):

| Workflow Type | Total Cost | Notes |
|---------------|------------|-------|
| Default (Sonnet/Haiku) | $0.20-0.50 | Balanced quality/cost |
| Cost-Optimized | $0.10-0.30 | Uses Haiku/GPT-4o-mini |
| High-Quality | $1.00-3.00 | Uses Opus/GPT-4 |
| Open Source | $0.05-0.15 | Via OpenRouter |

## Best Practices

1. **Start with defaults** - TAC-X defaults are well-tested and balanced
2. **Use fallbacks** - Always configure fallback models for reliability
3. **Match model to task** - Simple tasks (PR creation) don't need expensive models
4. **Track costs** - Use `analyze-pipeline.py` to monitor spending
5. **Test workflows** - Validate custom workflows with small issues first
6. **Provider diversity** - Use different providers for planning vs reviewing for independent validation

## Troubleshooting

### API Key Not Found

```
ValueError: ANTHROPIC_API_KEY environment variable not set
```

**Solution:** Set the required API key in your environment:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Provider Not Available

```
ValueError: Unknown provider: custom_provider
```

**Solution:** Check supported providers:

```python
from adw_modules.llm_providers import ProviderRegistry
print(ProviderRegistry.list_providers())
# Output: ['anthropic', 'openai', 'openrouter']
```

### Model Not Found

OpenRouter models may have different names than direct API models. Check OpenRouter documentation for exact model paths.

### Fallback Not Working

Ensure fallback is specified in correct format:

```yaml
fallback: openai/gpt-4  # Correct: provider/model
fallback: gpt-4  # Also works: infers provider from name
```

## Adding Custom Providers

To add a custom LLM provider:

1. Create provider class extending `LLMProvider`
2. Implement `invoke()` method
3. Register with `ProviderRegistry.register()`

See `adws/adw_modules/llm_providers.py` for examples.

## Further Reading

- [TAC-X Architecture](../README.md)
- [Provider Abstraction Source](../adws/adw_modules/llm_providers.py)
- [Workflow Config Source](../adws/adw_modules/workflow_config.py)
- [OpenRouter Models](https://openrouter.ai/models)
