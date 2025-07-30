# Improved Naming and Examples Organization

## Summary
Renamed "chips/" to "component_info/" for broader scope and reorganized duplicate examples into a clean, categorized structure.

## Key Changes
- **Renamed directory**: `chips/` → `component_info/` (better represents all component types)
- **Updated all imports**: Changed from `circuit_synth.chips.*` to `circuit_synth.component_info.*`
- **Reorganized examples**: Consolidated duplicate examples from `src/circuit_synth/examples/` and `src/circuit_synth/kicad_api/examples/` into top-level `examples/` with categories:
  - `examples/basic/` - Simple usage examples
  - `examples/advanced/` - Complex feature demonstrations  
  - `examples/testing/` - Test and validation scripts
  - `examples/tools/` - Utility scripts
- **Updated documentation**: CLAUDE.md reflects new naming and structure

## Benefits
- **Clearer naming**: "component_info" encompasses passives, sensors, and all component types
- **Eliminated duplication**: Removed 24 duplicate example files  
- **Better organization**: Examples categorized by complexity and purpose
- **Maintained compatibility**: All imports work correctly with graceful fallbacks

## Impact
Repository is now more professional with clearer naming conventions and organized examples that guide users from basic to advanced usage.