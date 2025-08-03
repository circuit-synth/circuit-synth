---
allowed-tools: Bash(git*), Bash(uv*), Bash(black*), Bash(isort*), Edit, Read, Write, Task, Grep, Glob
description: Comprehensive workflow for documenting progress and committing changes
argument-hint: [description of changes]
---

Comprehensive workflow for documenting progress, updating documentation, and committing changes: **$ARGUMENTS**

## Process

### 1. Update Memory Bank (Keep Brief)
**IMPORTANT: Be concise - 2-3 sentences maximum**
- Create a single, focused progress entry in memory-bank/
- Document only the key technical change: what was done and why
- NO lengthy explanations or detailed code analysis

### 2. Update Documentation (Only if Needed)
- IF new user-facing features: Update README.md briefly
- IF new commands: Update CLAUDE.md
- NO documentation changes for internal fixes or refactoring

### 3. Format Code Before Committing
**IMPORTANT: Always format code before committing**
- Run formatting commands:
  ```bash
  uv run black src/
  uv run isort src/
  ```
- This ensures consistent code style across the project

### 4. Commit Changes (Concise Message)  
**IMPORTANT: Keep commit message under 3 lines**
- Check git status and add modified files only
- Commit message format:
  ```
  Brief description of change
  
  🤖 Generated with Claude Code
  ```
- NO verbose technical details in commit message

### 5. Cleanup
- Remove any temporary test files
- Verify working tree is clean

## Guidelines
- **Be concise**: Memory bank entries and commits should be brief
- **Focus on impact**: What changed and why, not how
- **Skip minor changes**: Don't document every small fix
- **User perspective**: Document what users will notice

## Example
```
/dev-update-and-commit "Add KiCad symbol search functionality"
```

This creates a focused memory bank entry and clean commit without excessive verbosity.