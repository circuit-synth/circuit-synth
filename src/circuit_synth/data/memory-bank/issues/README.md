# Issues Folder

This folder tracks bugs, problems, and troubleshooting information for the circuit-synth project.

## Organization

### File Naming Convention
- `YYYY-MM-DD-issue-name.md` for specific issues
- `category-issues.md` for grouped issues by category
- `resolved-YYYY-MM-DD.md` for resolved issue summaries

### Categories
- **bugs/**: Software defects and unexpected behavior
- **performance/**: Performance-related issues
- **compatibility/**: Platform or KiCad version compatibility issues
- **api/**: API design problems or inconsistencies
- **documentation/**: Documentation gaps or errors
- **testing/**: Test failures or coverage gaps

### Issue Template
```markdown
# Issue Title

**Date**: YYYY-MM-DD
**Category**: bug/performance/compatibility/api/documentation/testing
**Priority**: high/medium/low
**Status**: open/investigating/resolved

## Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Expected vs actual behavior

## Environment
- OS: 
- Python version:
- KiCad version:
- circuit-synth version:

## Workaround
Any temporary workarounds

## Resolution
Final resolution (when resolved)
```