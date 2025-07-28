# Update and Commit Command

Comprehensive workflow for documenting progress, updating documentation, and committing changes.

## Usage
```
/update-and-commit [description of changes]
```

## Process

### 1. Update Memory Bank
- Use Task tool with general-purpose agent to update memory bank with latest progress
- Document technical achievements, fixes, and current status
- Include specific code changes and their impact
- Record breakthrough moments and system improvements

### 2. Update Documentation
- Review and update README.md with new capabilities
- Enhance feature descriptions in relevant sections
- Add examples if new functionality warrants them
- Update any other relevant documentation files

### 3. Commit Changes
- Check git status for modified files
- Add appropriate files (avoid temporary artifacts)
- Create comprehensive commit message with:
  - Clear summary of changes
  - Technical details of improvements
  - Functional validation results
  - Documentation updates
- Include Claude Code attribution

### 4. Cleanup
- Remove temporary test files and artifacts
- Clean up any untracked files that aren't needed
- Verify working tree is clean after cleanup

## Example
```
/update-and-commit "Fix hierarchical KiCad converter with enhanced parameter passing"
```

This command ensures consistent documentation, proper git hygiene, and comprehensive progress tracking across development sessions.