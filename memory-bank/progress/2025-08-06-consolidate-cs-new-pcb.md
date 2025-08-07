# Consolidate cs-new-pcb into cs-new-project

## Summary
Consolidated duplicate `cs-new-pcb` and `cs-new-project` commands into single `cs-new-project` command. Fixed incomplete .claude directory generation to include commands and complete agent setup.

## Key Changes
- Removed `cs-new-pcb` command entry from pyproject.toml
- Enhanced `cs-new-project` to create complete .claude directory with commands structure
- Fixed circular import issue preventing proper agent loading

## Impact
Users now have a single, fully-functional project creation command instead of confusing dual options.