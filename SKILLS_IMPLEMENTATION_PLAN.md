# Claude Skills Implementation Plan

## What Are Claude Skills?

Claude Skills are lightweight, automatically-invoked capabilities that provide fast data-driven operations:
- **Automatic**: Claude invokes them based on keywords (no explicit calls)
- **Fast**: <10 seconds vs 60+ seconds for agents
- **Progressive**: Load only needed data, not full context
- **Data-Driven**: Component lookups, templates, cached information

## .claude Directories That Need Skills

1. **`./.claude/`** - Development environment (this repo)
2. **`./src/circuit_synth/data/templates/example_project/.claude/`** - User project template (cs-new-project)
3. **`./src/circuit_synth/data/templates/project_template/pcbs/circuit-synth-v1/.claude/`** - PCB-specific template

## Proposed Directory Structure

Each `.claude` directory gets a `skills/` subdirectory:

```
.claude/
├── agents/              # Existing - complex reasoning
├── commands/            # Existing - slash commands
├── skills/              # NEW - data-driven operations
│   └── README.md       # Overview (infrastructure only for now)
├── SKILL_TEMPLATE.md   # NEW - How to create skills (top-level only)
└── settings.json       # Existing
```

## Skills to Implement (Future - Not Now)

### Phase 2 (Next PR)
- **component-search** - JLCPCB/DigiKey component sourcing with caching
- **kicad-integration** - Symbol/footprint/pin validation

### Phase 3 (Future)
- **circuit-patterns** - Voltage regulators, USB, LED drivers, etc.
- **stm32-config** - STM32 peripheral configuration from modm-devices

### Phase 4 (Future)
- **test-generation** - Test plan templates
- **simulation** - SPICE simulation setup

## This PR: Infrastructure Only

**What this PR adds:**
1. Empty `skills/` directories in all 3 `.claude` locations
2. `README.md` in each skills/ explaining it's coming soon
3. `SKILL_TEMPLATE.md` at top level showing how to create skills
4. `.gitignore` patterns for skill cache files

**What this PR does NOT add:**
- No actual skills implemented
- No component search functionality
- No KiCad integration
- No templates or data files

**Why separate infrastructure from implementation?**
- Easy to review structure without content
- Clean git history
- Template ready immediately for cs-new-project

## Each Skill's Structure (When Implemented)

```
.claude/skills/component-search/
├── SKILL.md              # Skill definition with frontmatter
├── README.md             # Usage docs
├── data/                 # Cached data (gitignored)
│   └── jlcpcb_cache.json
└── templates/            # Optional code templates
```

## SKILL.md Frontmatter Format

```markdown
---
name: component-search
description: JLCPCB/DigiKey component sourcing with caching
allowed-tools: ["Read", "Write", "Bash", "WebSearch"]
---

# Component Search Skill

## When to Use This Skill
[Invocation triggers and keywords...]

## Capabilities
[What the skill does...]

## Data Files
[Cache schemas...]
```

## Performance Targets

Once skills are implemented:
- **Response Time**: <10 seconds (vs 60+ for agents)
- **Token Usage**: 40-60% reduction
- **Cache Hit Rate**: 80%+
- **Automatic Invocation**: 90%+ accuracy

## Skills vs Agents Decision Guide

**Use Skills for:**
- Component lookups
- Symbol/footprint search
- Template selection
- Cached data retrieval

**Use Agents for:**
- Design decisions
- Complex workflows
- Interactive guidance
- Architecture planning

## Files This PR Will Add

```
SKILLS_IMPLEMENTATION_PLAN.md                     # This document (for review)
.claude/skills/README.md                          # Infrastructure placeholder
.claude/SKILL_TEMPLATE.md                         # How to create skills
src/.../example_project/.claude/skills/README.md  # Template placeholder
src/.../project_template/.claude/skills/README.md # PCB template placeholder
.gitignore                                        # Add cache patterns
```

## Review Checklist

- [ ] Agree with .claude directories to update (all 3)
- [ ] Agree with empty skills/ structure (infrastructure only)
- [ ] Agree with SKILL_TEMPLATE.md format
- [ ] Agree with .gitignore cache patterns
- [ ] Ready to implement actual skills in next PR

## Next Steps After Review

1. **This PR**: Merge infrastructure (if approved)
2. **Next PR**: Implement component-search skill
3. **Future PRs**: Implement remaining skills one-by-one

---

**Review this document first.** If approved, I'll create the actual infrastructure PR.
