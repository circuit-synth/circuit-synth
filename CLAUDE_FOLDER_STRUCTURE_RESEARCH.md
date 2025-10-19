# Claude Code .claude Folder Structure Research

**Date**: 2025-10-19
**Project**: circuit-synth
**Research Focus**: Understanding nested .claude folders and consolidation opportunities

---

## Executive Summary

After comprehensive research into how Claude Code handles nested .claude folders, here are the key findings:

**RECOMMENDATION: KEEP BOTH .claude FOLDERS - They serve different purposes**

- **Root .claude** (`/circuit-synth/.claude`): For circuit-synth library development
- **Template .claude** (`/example_project/.claude`): For end-user projects created via `cs-new-project`

These folders are NOT duplicates - they have different audiences and contents, and serve distinct roles in the project architecture.

---

## 1. How Nested .claude Folders Work

### 1.1 Directory Hierarchy

Claude Code uses a **hierarchical configuration system** where settings and context are loaded based on your current working directory:

```
Priority (highest to lowest):
1. Enterprise settings (managed, system-wide)
2. Project settings (.claude/ in current working directory)
3. User settings (~/.claude/ in home directory)
4. Project local settings (.claude/settings.local.json)
```

### 1.2 Active .claude Folder

**The active .claude folder is determined by your current working directory (CWD)**:

- If you're in `/circuit-synth/` → uses `/circuit-synth/.claude`
- If you're in `/circuit-synth/example_project/` → uses `/circuit-synth/example_project/.claude`
- If you're in a user's created project → uses that project's `.claude`

**Key insight**: Claude Code is scoped to the current working directory. Only ONE .claude folder is active at a time - the one in your CWD.

### 1.3 CLAUDE.md Memory Files

For CLAUDE.md files specifically, Claude Code uses a **recursive loading mechanism**:

1. Starts in current working directory
2. Recursively searches UP to (but not including) root directory `/`
3. Loads all CLAUDE.md files found in parent directories
4. Loads child directory CLAUDE.md files **on-demand** when you interact with files in those directories

**Important**: Child directory CLAUDE.md files are NOT automatically loaded at startup - they're only included when Claude reads files within those subdirectories.

### 1.4 Commands and Agents

**Commands** (`.claude/commands/`):
- Only commands from the active .claude folder are available
- Commands can be organized in subdirectories (e.g., `commands/dev/`, `commands/setup/`)
- Subdirectory names appear in command descriptions: "(project:dev)"

**Agents** (`.claude/agents/` via mcp_settings.json):
- Only agents from the active .claude folder are registered
- No merging between parent and child .claude folders
- Each .claude folder has its own independent agent registry

### 1.5 What Does NOT Happen

Claude Code does **NOT**:
- Merge configurations from multiple .claude directories simultaneously
- Load all nested .claude folders at startup
- Automatically discover .claude folders in subdirectories
- Combine agents/commands from parent and child .claude folders

---

## 2. Current Duplication Analysis

### 2.1 File Comparison Summary

| Category | Root .claude | example_project .claude | Status |
|----------|-------------|------------------------|--------|
| **settings.json** | CIRCUIT_SYNTH_DEV=1 | CIRCUIT_SYNTH_PROJECT=1 | DIFFERENT (by design) |
| **mcp_settings.json** | 14 agents | 9 agents | DIFFERENT (subset) |
| **README.md** | 148 lines | 148 lines | IDENTICAL |
| **Commands** | dev/, setup/ | circuit-design/, development/, manufacturing/, setup/ | VERY DIFFERENT |
| **Agents** | 9 categories, 20+ agents | 3 categories, 11 agents | DIFFERENT (subset) |

### 2.2 Key Differences

#### settings.json
```json
// Root .claude (for library development)
{
  "env": {
    "PYTHONPATH": "${PYTHONPATH}:./src",
    "CIRCUIT_SYNTH_DEV": "1"
  }
}

// example_project .claude (for end users)
{
  "env": {
    "CIRCUIT_SYNTH_PROJECT": "1"
  }
}
```

#### mcp_settings.json Agents

**Root .claude** (14 agents - full development suite):
- circuit-generation-agent
- stm32-mcu-finder
- jlc-parts-finder
- dfm-agent
- circuit-architect
- component-guru
- simulation-expert
- test-plan-creator
- **interactive-circuit-designer** (PRIMARY)
- contributor (dev)
- circuit-project-creator (orchestrator)
- circuit-syntax-fixer
- circuit-validation-agent
- component-symbol-validator

**example_project .claude** (9 agents - end-user focused):
- circuit-generation-agent
- stm32-mcu-finder
- jlc-parts-finder
- dfm-agent
- circuit-architect
- component-guru
- simulation-expert
- test-plan-creator
- contributor

**Missing from template**:
- interactive-circuit-designer (primary interface!)
- circuit-project-creator (orchestrator)
- circuit-syntax-fixer
- circuit-validation-agent
- component-symbol-validator

#### Commands Structure

**Root .claude commands**:
```
commands/
├── dev/
│   ├── dead-code-analysis.md
│   ├── release-pypi.md
│   ├── review-branch.md
│   ├── review-repo.md
│   ├── run-tests.md
│   └── update-and-commit.md
└── setup/
    ├── setup-kicad-plugins.md
    └── setup_circuit_synth.md
```

**example_project .claude commands**:
```
commands/
├── circuit-design/
│   ├── analyze-design.md
│   ├── component-info.md
│   ├── design-mode.md
│   ├── design.md
│   ├── find-footprint.md
│   ├── find-pins.md
│   ├── find-symbol.md
│   ├── generate-validated-circuit.md
│   ├── generate_circuit.md
│   ├── quick-validate.md
│   ├── validate-existing-circuit.md
│   └── validate-symbol.md
├── development/
│   ├── dev-release-pypi.md
│   ├── dev-review-branch.md
│   ├── dev-review-repo.md
│   ├── dev-run-tests.md
│   └── dev-update-and-commit.md
├── manufacturing/
│   ├── find-digikey-parts.md
│   ├── find-mcu.md
│   ├── find-parts.md
│   └── find_stm32.md
└── setup/
    ├── setup-kicad-plugins.md
    └── setup_circuit_synth.md
```

### 2.3 What's Actually Identical

Only **README.md** is truly identical between the two folders (148 lines each, byte-for-byte identical).

---

## 3. Intended Use Cases

Based on research and code analysis, here's how the two .claude folders are used:

### 3.1 Root .claude (/circuit-synth/.claude)

**Purpose**: Circuit-synth library development environment
**Audience**: Circuit-synth contributors and maintainers
**Use Cases**:
- Developing circuit-synth library itself
- Running tests and release workflows
- Contributing code to the project
- Repository-level development tasks

**Key Features**:
- Development commands (`/dev:run-tests`, `/dev:release-pypi`, etc.)
- Full agent suite including validation and syntax fixing
- PYTHONPATH configuration for source code development
- Quality gates and development standards

### 3.2 Template .claude (/example_project/.claude)

**Purpose**: End-user project template
**Audience**: Engineers using circuit-synth to design circuits
**Use Cases**:
- Circuit design and generation
- Component sourcing and selection
- Manufacturing preparation
- End-user circuit projects

**Key Features**:
- Circuit design commands (`/find-symbol`, `/find-footprint`, `/generate-validated-circuit`)
- Manufacturing commands (`/find-parts`, `/find-digikey-parts`, `/find_stm32`)
- Subset of agents focused on circuit design (not library development)
- Clean environment without development tooling

**Template Copy Process**:
From `new_project.py` (lines 34-153):
```python
def create_claude_directory_from_templates(project_path: Path, developer_mode: bool = False):
    """Create a complete .claude directory structure using templates"""

    # Find template directory
    template_claude_dir = circuit_synth_dir / "data" / "templates" / "example_project" / ".claude"

    # Copy entire template .claude directory structure
    shutil.copytree(template_claude_dir, dest_claude_dir)

    # If NOT developer_mode, remove development-specific files
    if not developer_mode:
        # Remove dev commands
        # Remove development agents
        # Keep only end-user focused content
```

**When users run `cs-new-project`**:
1. The **example_project/.claude** folder gets copied to their new project
2. Development-specific content is removed (unless `--developer` flag used)
3. They get a clean, focused .claude setup for circuit design

---

## 4. Best Practices from Research

### 4.1 Official Claude Code Recommendations

**From Anthropic's Best Practices**:
- "Install only what's necessary for each project! If Claude Code has too many options, it will start to lose focus."
- Check commands into git to make them available for your team
- Organize commands in subdirectories for better structure
- Use project-level .claude for team-shared workflows

**From Community Practices**:
- Keep project .claude folders minimal and focused
- Use global ~/.claude for personal utilities
- Version control project .claude for team consistency
- Separate concerns: dev tools vs. end-user tools

### 4.2 Template Project Patterns

**Common pattern for template-based projects**:
```
my-framework/
├── .claude/              # Framework development
│   ├── agents/
│   └── commands/
├── template/
│   └── .claude/          # User project template
│       ├── agents/       # Subset for end users
│       └── commands/     # Different focus
```

This is exactly what circuit-synth does - and it's the right pattern!

---

## 5. Specific Questions Answered

### 5.1 If I'm working in /circuit-synth/, which .claude folder is active?

**Answer**: `/circuit-synth/.claude`

This is the library development .claude with:
- Development commands (`/dev:run-tests`, `/dev:review-branch`, etc.)
- Full agent suite (14 agents)
- PYTHONPATH configuration
- Quality gates for library development

### 5.2 If I'm working in /circuit-synth/example_project/, which .claude folder is active?

**Answer**: `/circuit-synth/example_project/.claude`

This is the template .claude with:
- Circuit design commands (`/find-symbol`, `/generate-validated-circuit`, etc.)
- End-user agent subset (9 agents)
- Project environment variables
- Manufacturing-focused workflows

**Note**: The parent `/circuit-synth/.claude` is NOT active. Only the example_project .claude is loaded.

### 5.3 After running cs-new-project, which .claude gets copied?

**Answer**: `/circuit-synth/example_project/.claude` (or from packaged template)

From `new_project.py` line 56:
```python
template_claude_dir = circuit_synth_dir / "data" / "templates" / "example_project" / ".claude"
```

The template .claude gets copied to the new user project, with:
- Optional filtering for developer mode
- Removal of mcp_settings.json (not needed in user projects)
- Removal of development-specific commands/agents (unless --developer flag)

**Fallback**: If template not found, uses `/circuit-synth/.claude` as fallback (line 166)

### 5.4 Do skills/agents/commands from both folders combine or override?

**Answer**: They do NOT combine. Only the active .claude folder is used.

- Commands: Only from current .claude folder
- Agents: Only registered from current mcp_settings.json
- Settings: Only from current settings.json (with hierarchy: enterprise > project > user)

There is NO merging or combining between parent and child .claude folders.

### 5.5 What happens to the root .claude when we're inside example_project?

**Answer**: The root .claude is completely inactive when working in example_project.

- Root agents are not available
- Root commands are not available
- Root settings don't apply (except via CLAUDE.md recursive loading)

The only exception: CLAUDE.md files from parent directories are loaded recursively, so `/circuit-synth/CLAUDE.md` would be read when working in example_project.

---

## 6. Recommendation: Keep Both, Differentiate Clearly

### 6.1 Why Keep Both?

**Different Audiences**:
- Root .claude: Circuit-synth **developers** (internal team)
- Template .claude: Circuit-synth **users** (external engineers)

**Different Purposes**:
- Root .claude: Library development, testing, releases
- Template .claude: Circuit design, component sourcing, manufacturing

**Different Contents**:
- Root: Development tools, contributor agents, test runners
- Template: Design tools, component search, circuit generation

**Different Contexts**:
- Root: Source code in `src/`, tests in `tests/`
- Template: User circuits, KiCad projects, manufacturing files

### 6.2 Current Issues to Fix

#### Issue 1: Missing Critical Agents in Template

The template .claude is missing key agents that users need:

**Missing from example_project/.claude**:
- `interactive-circuit-designer` - **This is the PRIMARY interface mentioned in CLAUDE.md!**
- `circuit-project-creator` - Master orchestrator
- `circuit-syntax-fixer` - Fixes code errors
- `circuit-validation-agent` - Tests execution
- `component-symbol-validator` - Validates KiCad symbols

**Why this matters**: The root CLAUDE.md says:
```markdown
## 🎛️ CIRCUIT DESIGN AGENT (PRIMARY INTERFACE)

**🚨 FOR ALL CIRCUIT-RELATED TASKS: Use the interactive-circuit-designer agent**
```

But this agent is NOT in the template that gets copied to user projects!

#### Issue 2: Identical README.md Files

Both .claude folders have identical README.md (148 lines). This is wasteful and confusing:
- Root README should explain development agents/commands
- Template README should explain user-facing agents/commands

#### Issue 3: Template Has Development Commands

The template includes `development/dev-*` commands that end users don't need:
- `dev-release-pypi.md`
- `dev-review-branch.md`
- `dev-review-repo.md`

These are filtered out during `cs-new-project` (line 76-95), but they shouldn't be in the template in the first place.

### 6.3 Recommended Changes

#### Change 1: Add Missing Agents to Template

**File**: `/example_project/.claude/mcp_settings.json`

Add these agents to the template:
```json
{
  "agents": {
    "interactive-circuit-designer": {
      "description": "Professional interactive circuit design agent for collaborative engineering partnership throughout the complete design lifecycle",
      "file": "agents/circuit-design/interactive-circuit-designer.md"
    },
    "circuit-project-creator": {
      "description": "Master orchestrator for complete circuit project generation from natural language prompts",
      "file": "agents/orchestration/circuit-project-creator.md"
    },
    "circuit-syntax-fixer": {
      "description": "Circuit syntax specialist that fixes code errors while preserving design intent",
      "file": "agents/circuit-design/circuit-syntax-fixer.md"
    },
    "circuit-validation-agent": {
      "description": "Circuit validation specialist that tests generated code execution",
      "file": "agents/circuit-design/circuit-validation-agent.md"
    }
  }
}
```

Also copy the corresponding agent .md files to example_project/.claude/agents/

#### Change 2: Differentiate README.md Files

**Root .claude/README.md** should focus on:
- Development workflow
- Testing and release process
- Contributor onboarding
- Library architecture

**Template .claude/README.md** should focus on:
- Circuit design workflow
- Component sourcing
- Manufacturing preparation
- End-user quick start

#### Change 3: Remove Development Commands from Template

Remove these from `/example_project/.claude/commands/development/`:
- `dev-release-pypi.md`
- `dev-review-branch.md`
- `dev-review-repo.md`
- `dev-review-repo.md`
- `dev-run-tests.md`
- `dev-update-and-commit.md`

These should only exist in root .claude for developers.

**Alternative**: Keep them but make the filtering in `new_project.py` more robust.

#### Change 4: Add Explanation Comment to Both

Add a comment at the top of each settings.json:

**Root .claude/settings.json**:
```json
{
  "_comment": "Circuit-synth LIBRARY DEVELOPMENT environment - for contributors working on circuit-synth itself",
  "description": "Circuit-Synth Library Development Environment",
  ...
}
```

**Template .claude/settings.json**:
```json
{
  "_comment": "Circuit-synth PROJECT template - gets copied to user projects via cs-new-project",
  "description": "Circuit-Synth Project Environment",
  ...
}
```

---

## 7. Migration Plan

### Phase 1: Immediate Fixes (High Priority)

**Goal**: Fix the missing agents issue so user projects work as documented

1. **Copy missing agents to template** (30 min)
   ```bash
   # Copy agent files
   cp .claude/agents/circuit-design/interactive-circuit-designer.md \
      example_project/.claude/agents/circuit-design/

   cp .claude/agents/orchestration/circuit-project-creator.md \
      example_project/.claude/agents/orchestration/

   cp .claude/agents/circuit-design/circuit-syntax-fixer.md \
      example_project/.claude/agents/circuit-design/

   cp .claude/agents/circuit-design/circuit-validation-agent.md \
      example_project/.claude/agents/circuit-design/
   ```

2. **Update template mcp_settings.json** (10 min)
   - Add the 4 missing agents to the agents section

3. **Test the template** (15 min)
   ```bash
   # Run cs-new-project and verify agents are available
   uv run cs-new-project --minimal
   # Check that interactive-circuit-designer is listed
   ```

4. **Commit and deploy** (5 min)

**Total time**: ~1 hour

### Phase 2: Documentation Cleanup (Medium Priority)

**Goal**: Make it clear what each .claude folder is for

1. **Create differentiated README.md files** (1 hour)
   - Root: Focus on development workflow
   - Template: Focus on circuit design workflow

2. **Add explanatory comments to settings.json** (15 min)

3. **Update CLAUDE.md in both locations** (30 min)
   - Root CLAUDE.md: Explain this is for library development
   - Template CLAUDE.md: Explain this is for user projects

**Total time**: ~2 hours

### Phase 3: Command Cleanup (Low Priority)

**Goal**: Remove confusion about which commands belong where

1. **Remove dev commands from template** (30 min)
   - Delete `example_project/.claude/commands/development/dev-*` files
   - OR improve filtering in `new_project.py`

2. **Organize root commands better** (1 hour)
   - Consider renaming dev/ to development/ for consistency
   - Add README in commands/ explaining organization

**Total time**: ~1.5 hours

---

## 8. Key Takeaways

### What We Learned

1. **Claude Code uses CWD-based .claude activation** - only one .claude folder is active at a time
2. **No merging happens** - parent and child .claude folders are completely independent
3. **Template pattern is correct** - having separate .claude for library dev and user projects is the right approach
4. **Current implementation has gaps** - missing critical agents in template
5. **Documentation needs work** - identical README files cause confusion

### What We Should Do

1. **Keep both .claude folders** - they serve different purposes
2. **Fix the template** - add missing agents so user projects work as documented
3. **Differentiate clearly** - make it obvious which is for what
4. **Document the pattern** - explain in contributor docs why there are two

### What We Should NOT Do

1. **Don't consolidate** - we need both folders for different audiences
2. **Don't create automatic merging** - Claude Code doesn't support it
3. **Don't copy everything** - users don't need development tools
4. **Don't leave gaps** - ensure template has everything users need

---

## 9. References

### Official Documentation
- [Claude Code Settings](https://docs.claude.com/en/docs/claude-code/settings)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Claude Code Common Workflows](https://docs.claude.com/en/docs/claude-code/common-workflows)

### GitHub Issues
- [Nested CLAUDE.md context #705](https://github.com/anthropics/claude-code/issues/705)
- [CLAUDE.md in subfolders #3529](https://github.com/anthropics/claude-code/issues/3529)
- [Better Monorepo Support #2365](https://github.com/anthropics/claude-code/issues/2365)
- [Enhance Memory System #4275](https://github.com/anthropics/claude-code/issues/4275)

### Community Resources
- [ClaudeLog - Configuration Guide](https://claudelog.com/configuration/)
- [Cooking with Claude Code](https://www.siddharthbharath.com/claude-code-the-complete-guide/)
- [Claude Code Templates](https://github.com/davila7/claude-code-templates)

### Code References
- `/src/circuit_synth/tools/project_management/new_project.py` (lines 34-303)
- `/.claude/mcp_settings.json` (14 agents)
- `/example_project/.claude/mcp_settings.json` (9 agents)

---

## Appendix: Complete Agent Comparison

### Root .claude Agents (14 total)

| Agent | Purpose | Category |
|-------|---------|----------|
| circuit-generation-agent | Circuit code generation | circuit-generation |
| stm32-mcu-finder | STM32 selection | microcontrollers |
| jlc-parts-finder | JLCPCB sourcing | manufacturing |
| dfm-agent | Design for Manufacturing | manufacturing |
| circuit-architect | Master coordinator | circuit-design |
| component-guru | Component sourcing | manufacturing |
| simulation-expert | SPICE validation | circuit-design |
| test-plan-creator | Test procedures | circuit-design |
| **interactive-circuit-designer** | **PRIMARY INTERFACE** | **circuit-design** |
| contributor | Onboarding | development |
| circuit-project-creator | Master orchestrator | orchestration |
| circuit-syntax-fixer | Error fixing | circuit-design |
| circuit-validation-agent | Code testing | circuit-design |
| component-symbol-validator | Symbol validation | circuit-design |

### Template .claude Agents (9 total)

| Agent | Purpose | Category |
|-------|---------|----------|
| circuit-generation-agent | Circuit code generation | circuit-generation |
| stm32-mcu-finder | STM32 selection | microcontrollers |
| jlc-parts-finder | JLCPCB sourcing | manufacturing |
| dfm-agent | Design for Manufacturing | manufacturing |
| circuit-architect | Master coordinator | circuit-design |
| component-guru | Component sourcing | manufacturing |
| simulation-expert | SPICE validation | circuit-design |
| test-plan-creator | Test procedures | circuit-design |
| contributor | Onboarding | development |

### Missing from Template (5 agents)

1. **interactive-circuit-designer** ⚠️ CRITICAL - This is the PRIMARY interface!
2. **circuit-project-creator** - Master orchestrator
3. **circuit-syntax-fixer** - Error fixing
4. **circuit-validation-agent** - Code testing
5. **component-symbol-validator** - Symbol validation

---

**END OF RESEARCH DOCUMENT**
