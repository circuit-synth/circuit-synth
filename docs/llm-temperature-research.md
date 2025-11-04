# LLM Temperature Settings for Autonomous Coding Agents

## Research Summary

This document summarizes research on optimal temperature settings for Large Language Model (LLM) autonomous coding agents, specifically for software development tasks like those performed by TAC-X workers.

## Temperature Basics

Temperature is a hyperparameter that controls randomness in LLM outputs:
- **Range:** 0.0 to 1.0 (some APIs support up to 2.0)
- **Low temperature (0.0-0.5):** More deterministic, focused, and predictable outputs
- **High temperature (0.7-1.0):** More creative, diverse, and random outputs
- **Default:** Most APIs default to 1.0

## Key Findings for Code Generation

### General Recommendations

**For code generation tasks requiring precision, accuracy, and factual consistency:**
- **Recommended range: 0.0 - 0.5**
- **Common practice: 0.0 or 0.2**
- Low temperatures prioritize predictability and consistency

### Claude-Specific Findings

**Temperature Behavior:**
- Default: 1.0
- Range: 0.0 - 1.0
- **Important:** Even at temperature 0.0, Claude models do NOT guarantee complete determinism
- Temperature 0.0 makes outputs more consistent and predictable, but some variability remains

**Recommended for Different Tasks:**
- **Analytical/multiple-choice tasks:** Closer to 0.0
- **Creative/generative tasks:** Closer to 1.0
- **Code generation:** Typically 0.0 for maximum consistency

### Experimental Results

One study ran 36 combinations of temperature and top_p values for code generation:
- Found that Mistral-medium's performance improved from 54 to 87 points with:
  - `top_p: 0.3`
  - `temperature: 0.9`
- However, repeating the benchmark showed no significant change, suggesting optimal settings vary by use case

**Conclusion:** Optimal settings are highly task-dependent and require experimentation.

## Best Practices

1. **Start with low temperature (0.2-0.5)** for code generation and refactoring
2. **Test empirically** with your specific models and use cases
3. **Quantitatively measure performance** at various temperature settings
4. **Don't assume determinism** even at temperature 0.0
5. **Consider the task type:**
   - Planning/analysis: 0.0-0.3
   - Code implementation: 0.0-0.5
   - Code review: 0.2-0.5
   - Creative tasks (docs, PR descriptions): 0.7-1.0

## Current TAC-X Configuration

### Current Settings
All TAC-X pipeline stages use:
```yaml
temperature: 1.0
```

This is **quite high** for autonomous coding tasks and may lead to:
- Less consistent outputs
- More variability between runs
- Potentially less focused code generation
- Higher chance of hallucinations

### Recommended Updates

Based on research, TAC-X stages should use lower temperatures:

```yaml
stages:
  - name: planning
    temperature: 0.3  # Analysis and planning task

  - name: building
    temperature: 0.2  # Code generation - needs consistency

  - name: reviewing
    temperature: 0.4  # Code review - some flexibility helpful

  - name: pr_creation
    temperature: 0.8  # Creative writing task
```

## References

- [Promptfoo: Choosing the right temperature for your LLM](https://www.promptfoo.dev/docs/guides/evaluate-llm-temperature/)
- [Vellum: LLM Temperature Guide](https://www.vellum.ai/llm-parameters/temperature)
- [Medium: Definitive Guide to LLM Temperatures](https://medium.com/thinking-sand/the-definitive-guide-to-llm-temperatures-abab311260a6)
- [Prompt Engineering Guide: LLM Settings](https://www.promptingguide.ai/introduction/settings)
- [OpenAI Community: Best Temperature for Code Generation](https://community.openai.com/t/best-temperature-for-code-generation/737935)

## Actionable Recommendations

1. **Immediate action:** Lower temperatures for TAC-X coding stages (planning, building, reviewing) to 0.2-0.4
2. **Keep higher temperature** (0.8-1.0) for PR creation stage (creative writing)
3. **Test and measure:** Monitor worker success rates with different temperature settings
4. **Document results:** Track which temperatures work best for different issue types

---

*Last updated: 2025-11-04*
*Research conducted for TAC-X autonomous worker optimization*
