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
- Run comprehensive formatting:
  ```bash
  uv run black src/ tests/ examples/
  uv run isort src/ tests/ examples/
  ```
- Format configuration files:
  ```bash
  prettier --write "*.{json,yml,yaml}" --ignore-path .gitignore 2>/dev/null || echo "Prettier not available"
  ```
- This ensures consistent code style across the entire project

### 4. Quality Checks Before Committing
**IMPORTANT: Run basic quality checks**
- Syntax validation:
  ```bash
  find src/ tests/ examples/ -name "*.py" -exec python -m py_compile {} \; 2>/dev/null || echo "⚠️  Syntax errors found"
  ```
- Quick test run (optional):
  ```bash
  uv run pytest tests/unit/ --tb=no -q || echo "⚠️  Unit tests failing"
  ```

### 5. Commit Changes (Selective and Clean)  
**IMPORTANT: Keep commit message under 3 lines**
- Check git status and review what needs to be committed
- Add only the files that should be kept: `git add <specific-files>`
- Remove unwanted files from git tracking: `git rm <unwanted-files>`
- Use `git add .` only after cleaning unwanted files
- Commit message format:
  ```
  Brief description of change
  
  🤖 Generated with Claude Code
  ```
- NO verbose technical details in commit message

### 6. File Management Strategy
**IMPORTANT: Be selective about what gets committed**

```bash
# 1. Review git status
git status

# 2. Handle different file categories:

# Modified files we want to keep:
git add specific-file-to-keep.py

# New files we want to add:
git add new-useful-file.md

# Files to delete from git tracking:
git rm unwanted-file.py              # Remove single file
git rm -r unwanted-directory/        # Remove directory and contents
git rm '*.tmp'                       # Remove all .tmp files
git rm -r --cached file-to-untrack   # Stop tracking but keep local file

# 3. Only after cleaning, add remaining good files:
git add .

# 4. Final verification before commit:
git status  # Should show only files you want to commit

# 5. Commit with clean message:
git commit -m "Brief description"
```

### 7. Final Cleanup
- Verify working tree is clean: `git status`
- Remove any temporary test files not in git
- Ensure no untracked files remain that shouldn't be there

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