# PRD: Self-Improving Commands, Agents & Skills

**Document Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft for Review

---

## 1. Overview

### Problem Statement
Currently, circuit-synth commands, agents, and skills are static - they only improve when developers manually update them. This creates friction: users encounter issues, workarounds are discovered, better approaches emerge, but these insights are lost unless manually documented and implemented.

### Vision
Enable all circuit-synth tooling (commands, agents, skills) to autonomously identify improvements during execution and update their own source files, creating a continuously evolving system that learns from real usage.

### Research Foundation
Recent 2025 research shows effective self-improving AI systems use:
- **Gödel Agent Framework**: Agents rewrite their own logic guided by high-level objectives
- **Feedback-Driven Improvement**: 17% → 53% performance gains on benchmarks (SICA, Bristol)
- **Role Specialization**: Targeted improvements mapped to specific agent responsibilities
- **Safety Through Observability**: Human oversight of all self-modifications

---

## 2. Goals & Success Metrics

### Primary Goals
1. **Continuous Improvement**: Commands/agents improve automatically based on real usage
2. **Knowledge Retention**: Insights from problem-solving are captured permanently
3. **Reduced Maintenance**: Less manual intervention needed to fix issues

### Success Metrics
- **Improvement Rate**: Number of self-modifications per week
- **Quality**: % of self-modifications that are kept vs reverted
- **User Impact**: Reduction in repeat issues/questions
- **Performance**: Measurable improvement in task completion rates

### Non-Goals (v1)
- Modifying core Python code (only markdown prompts initially)
- Automated A/B testing of improvements
- Cross-agent learning (agents learning from each other)

---

## 3. Technical Design

### Self-Improvement Directive (Added to All Prompts)

```markdown
## 🔄 Self-Improvement Protocol

As you execute this task, actively identify opportunities for improvement:

**When to self-improve:**
- You encounter an error or limitation in your instructions
- You discover a more efficient approach than documented
- User feedback reveals unclear or missing guidance
- You develop a valuable workaround or pattern

**How to self-improve:**
1. **Identify**: Note the specific improvement needed
2. **Validate**: Confirm it would benefit future executions
3. **Document**: Clearly explain what changed and why
4. **Update**: Use the Edit tool to modify this file
5. **Commit**: Create a git commit describing the improvement

**Safety guardrails:**
- Only modify this prompt file ({{FILE_PATH}})
- Preserve the core purpose and structure
- Add, don't remove (unless fixing errors)
- Use clear, professional language
- Include reasoning in comments

**Example improvements:**
- Adding common error solutions
- Documenting edge cases discovered
- Clarifying ambiguous instructions
- Adding helpful examples
- Optimizing inefficient steps
```

### Implementation Architecture

```
┌─────────────────────────────────────────┐
│  Agent/Command/Skill Execution          │
│  ┌─────────────────────────────────┐   │
│  │ 1. Read prompt from .md file    │   │
│  │ 2. Execute task                 │   │
│  │ 3. Monitor for improvement ops  │   │
│  │ 4. [If improvement identified]  │   │
│  │    → Modify prompt file         │   │
│  │    → Git commit with context    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘

Improvement Log (Git History)
  ├── commit: "circuit-architect: Add STM32 power calculation check"
  ├── commit: "jlc-parts-finder: Handle 404 errors gracefully"
  └── commit: "estimate-cost: Cache JLC price API for 24h"
```

### Files Modified

**Phase 1: Add Self-Improvement Directive**
- `.claude/agents/**/*.md` (all agent prompts)
- `.claude/commands/**/*.md` (all command prompts)
- `.claude/skills/**/*.md` (all skill prompts)
- `src/circuit_synth/data/templates/example_project/.claude/**/*.md` (template agents)

**Phase 2: Add Improvement Tracking**
- `.claude/improvements.log` (structured log of improvements)
- `.claude/improvement-stats.json` (metrics dashboard)

---

## 4. Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. Create self-improvement directive template
2. Add directive to 3 pilot agents for testing:
   - `circuit-architect` (high-usage)
   - `jlc-parts-finder` (frequent errors)
   - `component-guru` (evolving domain)
3. Monitor improvements for 1 week
4. Gather user feedback

### Phase 2: Rollout (Week 3)
1. Refine directive based on pilot learnings
2. Add to all agents, commands, and skills
3. Update project templates
4. Create documentation guide

### Phase 3: Analytics (Week 4)
1. Build improvement tracking dashboard
2. Add metrics collection
3. Enable improvement review workflow
4. Document best practices discovered

---

## 5. Safety & Risk Mitigation

### Key Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agents break their own prompts | Medium | High | Git history allows instant rollback; Add validation |
| Improvement churn (too many changes) | Medium | Medium | Rate limiting: max 1 improvement per execution |
| Quality degradation | Low | High | Human review via git commits; Revert bad changes |
| Infinite self-modification loops | Low | High | Prevent modifying self-improvement directive itself |
| Context bloat (prompts get too long) | Medium | Low | 5000 char limit per prompt file |

### Safety Mechanisms

**From Research (SICA, CodeMender, DGM)**:
1. **Human Observability**: All changes visible in git
2. **Validation Before Application**: Agent explains improvement before applying
3. **Rollback Capability**: Git revert for any problematic change
4. **Scope Limitation**: Only modify own prompt, not code/other files
5. **Async Oversight**: Monitor for anomalous behavior patterns

**Implementation**:
- Every improvement → git commit (reviewable)
- Daily improvement digest emailed to maintainers
- Auto-revert if prompt file exceeds size limit
- Quarterly review of all improvements

---

## 6. User Experience

### For End Users
- Transparent improvements (see them in git log)
- Optional: Enable/disable via config flag
- Improvement notifications in command output

### For Developers/Maintainers
- Review improvements via normal PR/commit process
- Dashboard showing improvement trends
- Ability to "accept" or "revert" improvements
- Best practices guide auto-generated from improvements

---

## 7. Future Enhancements (Post-v1)

- **Cross-Agent Learning**: Agents share improvements
- **A/B Testing**: Test improvements before applying
- **Performance-Based Updates**: Auto-tune based on metrics
- **Community Improvements**: Share anonymized improvements across circuit-synth users
- **Code Modifications**: Extend to Python files (with stricter safety)

---

## 8. Questions for Review

Please answer these to finalize the design:

### Scope & Safety
1. **Approval workflow**: Should improvements be:
   - [ ] Applied automatically (user reviews via git)
   - [ ] Proposed first, applied after user approval
   - [ ] Hybrid: Auto-apply "safe" improvements, ask for "risky" ones

2. **Modification scope**: Can agents modify:
   - [ ] Only their own prompt file
   - [ ] Related documentation files
   - [ ] Python code (with approval)
   - [ ] All of the above

3. **Safety validation**: Before applying improvement, should agent:
   - [ ] Just do it (fast, risky)
   - [ ] Explain reasoning first (shows intent)
   - [ ] Run test cases to validate (slow, safe)

### User Control
4. **Opt-in/out**: Should self-improvement be:
   - [ ] On by default (can disable)
   - [ ] Off by default (must enable)
   - [ ] Always on (no disable)

5. **Notifications**: When improvement happens:
   - [ ] Silent (just git commit)
   - [ ] Print message to console
   - [ ] Weekly digest email
   - [ ] Dashboard/UI to review

### Metrics & Review
6. **Success criteria**: How do we measure if this feature succeeds?
   - [ ] Number of improvements made
   - [ ] Reduction in user-reported issues
   - [ ] Agent performance benchmarks
   - [ ] User satisfaction survey
   - [ ] All of the above

7. **Review cadence**: How often should we review improvements?
   - [ ] Real-time (every commit)
   - [ ] Daily digest
   - [ ] Weekly summary
   - [ ] Monthly audit

8. **Quality bar**: What makes a "good" improvement?
   - [ ] Fixes a bug/error
   - [ ] Improves efficiency (faster/cheaper)
   - [ ] Adds valuable example/documentation
   - [ ] All of the above

---

## 9. Open Questions

- Should improvements be shared across user installations? (Privacy implications)
- How do we prevent improvement spam on common edge cases?
- Should there be a "suggested improvements" review UI?
- What happens if two users improve the same agent differently?

---

**Next Steps**: Review answers to questions, refine design, implement Phase 1 pilot.
