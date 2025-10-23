# PRD: Multi-Agent Architecture with Haiku 4.5

**Document Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft for Review

---

## 1. Overview

### Problem Statement
Circuit-synth currently uses Sonnet for most tasks, which is:
- **Slow**: Takes longer to respond (0.64s TTFT vs 0.36s for Haiku)
- **Expensive**: 3x cost ($3/$15 vs $1/$5 per million tokens)
- **Underutilized**: Many tasks don't need Sonnet's advanced reasoning

We're not leveraging parallel task execution effectively - most operations run sequentially when they could run concurrently using faster, cheaper models.

### Vision
Transform circuit-synth into a **multi-agent orchestration system** where:
- Main agent (Sonnet) coordinates high-level design decisions
- Sub-agents (Haiku 4.5) execute parallelizable tasks rapidly
- Task decomposition happens automatically
- Cost and speed are optimized through intelligent model selection

### Research Foundation
2025 multi-agent research shows:
- **Hierarchical Architecture**: Planning agents orchestrate specialized sub-agents
- **Parallel Execution**: 3x speedup with parallel task decomposition
- **Dynamic Model Selection**: Match model capabilities to task requirements
- **Cost Efficiency**: 60-80% cost reduction using tiered model strategy

---

## 2. Goals & Success Metrics

### Primary Goals
1. **Speed**: 3x faster task completion through parallelization
2. **Cost**: 50%+ reduction in API costs using Haiku for routine tasks
3. **Scale**: Handle 5-10x more concurrent operations
4. **Smart Routing**: Right model for right task automatically

### Success Metrics
- **Latency**: Average task completion time reduced by 50%
- **Cost per task**: Reduced by 40-60%
- **Parallelism**: Average 5+ sub-agents running concurrently
- **Model efficiency**: 70%+ of tasks handled by Haiku

### Non-Goals (v1)
- Building custom model router (use Claude Code's built-in)
- Training custom task classifiers
- Cross-project agent sharing

---

## 3. Model Selection Strategy

### When to Use Each Model

| Model | Cost | Speed | Use Cases |
|-------|------|-------|-----------|
| **Sonnet 4.5** | $3/$15 | Slower (0.64s TTFT) | - Complex circuit design decisions<br>- Multi-constraint optimization<br>- Ambiguous requirements resolution<br>- Code generation<br>- Strategic planning |
| **Haiku 4.5** | $1/$5 | Fast (0.36s TTFT, 3x faster) | - File searches<br>- Data extraction<br>- Simple transformations<br>- Component lookups<br>- Validation checks<br>- Tool execution |

### Research-Backed Decision Matrix

**From 2025 benchmarks**:
- **Haiku**: 88.1% on HumanEval (code), 41.6% on GPQA (reasoning)
- **Sonnet**: 93.7% on HumanEval (code), 65.0% on GPQA (reasoning)

**Recommendation**: Use Haiku for tasks with <30% reasoning requirement, Sonnet for complex reasoning.

---

## 4. Technical Design

### Architecture: Orchestrator + Workers

```
┌────────────────────────────────────────────────────────┐
│  Main Agent (Sonnet 4.5) - Orchestrator                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Receive user request                         │  │
│  │  2. Decompose into parallelizable tasks          │  │
│  │  3. Assign tasks to appropriate sub-agents       │  │
│  │  4. Launch sub-agents in parallel                │  │
│  │  5. Aggregate results                            │  │
│  │  6. Synthesize final response                    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                          ↓ Parallel dispatch
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Sub-Agent 1   │  │ Sub-Agent 2   │  │ Sub-Agent 3   │
│ (Haiku 4.5)   │  │ (Haiku 4.5)   │  │ (Haiku 4.5)   │
│               │  │               │  │               │
│ Search files  │  │ Lookup JLC    │  │ Validate KiCad│
│ for symbols   │  │ components    │  │ symbols       │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Task Decomposition Examples

**Example 1: "Design ESP32-C6 Dev Board"**
```
Main Agent (Sonnet):
├─ Understand requirements
├─ Create circuit architecture
└─ Launch parallel sub-agents (Haiku):
   ├─ Search for ESP32-C6 symbol
   ├─ Find USB-C footprint
   ├─ Lookup voltage regulator on JLC
   ├─ Search for crystal oscillator
   └─ Validate power supply design
```

**Example 2: "Check manufacturing readiness"**
```
Main Agent (Sonnet):
├─ Define DFM criteria
└─ Launch parallel checks (Haiku):
   ├─ Verify all components in JLC stock
   ├─ Check minimum trace width
   ├─ Validate drill sizes
   ├─ Count unique part numbers
   └─ Estimate assembly cost
```

### Implementation in CLAUDE.md

**Current**:
```markdown
When working on tasks, use the Task tool to invoke specialized agents.
```

**Proposed**:
```markdown
## 🚀 Multi-Agent Task Execution Strategy

**Default: Parallel decomposition with Haiku 4.5**

When you receive a task:
1. **Decompose**: Break into independent sub-tasks
2. **Classify**: Determine which need Sonnet vs Haiku
3. **Parallelize**: Launch multiple agents in ONE message
4. **Aggregate**: Combine results

**Model selection guidelines**:
- **Haiku 4.5** (fast, cheap) - Default for:
  - File/symbol searches, data extraction
  - Component lookups (JLC, DigiKey)
  - Validation checks, tool execution

- **Sonnet 4.5** (smart, slow) - Only when needed for:
  - Complex design decisions
  - Multi-constraint optimization
  - Code generation with nuance

**Parallel execution pattern**:
Always launch independent tasks together in a single response.
```

---

## 5. Implementation Plan

### Phase 1: Update CLAUDE.md (Week 1)
1. Add multi-agent execution guidelines
2. Add model selection decision tree
3. Add parallel execution examples
4. Test with 5 common workflows

### Phase 2: Agent Model Hints (Week 2)
1. Add `preferred_model: haiku-4.5` to agent metadata
2. Update fast agents (jlc-parts-finder, component-symbol-validator)
3. Keep complex agents on Sonnet (circuit-architect, interactive-circuit-designer)
4. Create model selection validator

### Phase 3: Monitoring & Optimization (Week 3)
1. Add metrics: model usage, parallelism, cost, latency
2. Build dashboard showing cost savings
3. Identify bottlenecks
4. Optimize task decomposition patterns

### Phase 4: Claude Code Ecosystem Integration (Week 4)
**NEW**: Create `/review-claude-ecosystem` command that:
- Searches web for latest Claude Code features
- Reviews our agents/commands/skills inventory
- Suggests updates, improvements, additions
- Identifies deprecated patterns
- Recommends new Claude Code skills to install

---

## 6. Detailed Component Design

### 6.1 Model Selection Metadata in Agents

**Add to each agent .md file**:
```yaml
---
preferred_model: haiku-4.5  # or sonnet-4.5
reasoning_complexity: low   # low, medium, high
parallelizable: true        # can run in parallel with others
---
```

**Examples**:
- `jlc-parts-finder.md`: `preferred_model: haiku-4.5, reasoning_complexity: low`
- `circuit-architect.md`: `preferred_model: sonnet-4.5, reasoning_complexity: high`

### 6.2 New Command: `/review-claude-ecosystem`

**Purpose**: Keep circuit-synth aligned with Claude Code latest features

**Workflow**:
1. Search web for "Claude Code latest features 2025"
2. Search "Claude Code MCP servers"
3. Search "Claude Code skills best practices"
4. Compare against our `.claude/` inventory
5. Generate report with:
   - New features we should adopt
   - Deprecated patterns we're using
   - Missing skills/commands we should add
   - Optimization opportunities

**Output**: Markdown report + suggested PRs

---

## 7. Cost & Performance Analysis

### Current State (Baseline)
- **Model**: 95% Sonnet, 5% Haiku
- **Parallelism**: 1-2 concurrent tasks average
- **Cost**: $15/million output tokens
- **Latency**: 2-5 seconds per agent call

### Target State (Post-Implementation)
- **Model**: 30% Sonnet, 70% Haiku
- **Parallelism**: 5-8 concurrent tasks average
- **Cost**: $7/million output tokens (53% reduction)
- **Latency**: 0.5-2 seconds per agent call (60% improvement)

### ROI Calculation
For 10,000 agent calls/month:
- **Current cost**: ~$150/month
- **Target cost**: ~$70/month
- **Savings**: $80/month (53%)
- **Speed improvement**: 3x faster on parallelizable workflows

---

## 8. Risk Mitigation

### Key Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Haiku makes mistakes on complex tasks | High | Validate outputs; fallback to Sonnet |
| Over-parallelization causes conflicts | Medium | Implement task dependency tracking |
| Cost optimization reduces quality | High | Monitor quality metrics; A/B test |
| User confusion from model switching | Low | Make it transparent in logs |

### Fallback Strategy
- If Haiku fails → auto-retry with Sonnet
- If parallel execution conflicts → sequential retry
- Quality regression → revert to Sonnet default

---

## 9. Questions for Review

Please answer to finalize design:

### Model Selection
1. **Default model**: Should Haiku be:
   - [ ] Default for all new agents (opt-out to Sonnet)
   - [ ] Opt-in per agent (default Sonnet)
   - [ ] Auto-selected based on task complexity

2. **Fallback behavior**: If Haiku fails:
   - [ ] Auto-retry with Sonnet (slower, more expensive, reliable)
   - [ ] Fail and ask user (manual intervention)
   - [ ] Use hybrid: Haiku first, Sonnet on error

3. **Model hints in agents**: Should agents:
   - [ ] Specify preferred model in YAML frontmatter
   - [ ] Let orchestrator decide dynamically
   - [ ] Both (agent preference as hint, orchestrator overrides if needed)

### Parallelization
4. **Parallel execution**: When to parallelize:
   - [ ] Always (unless dependencies detected)
   - [ ] Only for explicitly marked "parallelizable" agents
   - [ ] Let main agent decide per task

5. **Concurrency limit**: Max parallel agents:
   - [ ] 3-5 (conservative)
   - [ ] 5-10 (aggressive)
   - [ ] Unlimited (trust Claude Code)
   - [ ] User-configurable

### Monitoring
6. **Metrics to track**:
   - [ ] Model usage (Haiku vs Sonnet %)
   - [ ] Cost per task
   - [ ] Latency improvements
   - [ ] Quality (error rates)
   - [ ] All of the above

7. **Dashboard**: Where to show metrics:
   - [ ] Terminal output after each task
   - [ ] Web dashboard (separate tool)
   - [ ] Weekly digest email
   - [ ] `.claude/metrics.json` file

### Claude Code Ecosystem
8. **Review cadence**: How often to run `/review-claude-ecosystem`:
   - [ ] Weekly (automated)
   - [ ] Monthly (manual trigger)
   - [ ] On-demand only
   - [ ] After Claude Code releases

9. **Auto-updates**: Should ecosystem review:
   - [ ] Just suggest updates (user applies)
   - [ ] Auto-apply safe updates (user reviews)
   - [ ] Fully automated (with rollback)

---

## 10. Open Questions

- Should we build a "task complexity analyzer" to classify tasks automatically?
- How do we handle agent state between parallel executions?
- Should we cache Haiku results for repeated queries?
- What happens if 10 parallel Haiku calls all fail - do we retry all with Sonnet?

---

## 11. Future Enhancements (Post-v1)

- **Adaptive model selection**: Learn from outcomes which model works best for which tasks
- **Speculative parallelism**: Run Haiku and Sonnet in parallel, use fastest correct result
- **Cross-agent optimization**: Share learnings between agent instances
- **Custom model routing**: Train classifier to predict best model for task
- **MCP integration**: Leverage Model Context Protocol for advanced orchestration

---

**Next Steps**: Review answers, refine design, implement Phase 1 CLAUDE.md updates.
