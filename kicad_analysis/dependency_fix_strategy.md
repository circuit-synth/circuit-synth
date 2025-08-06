# Dependency Fix Strategy

## Problem Identified

The `sch_gen/schematic_writer.py` (the core working system) has imports from:
1. `kicad_api` - Modern system (OK)
2. `integrated_reference_manager` - Which imports from `sch_api` (Problem)

## Dependencies to Fix

### Files that import from sch_api:
1. `sch_gen/integrated_reference_manager.py` - Line 11
2. `sch_gen/integrated_placement.py` - Multiple imports
3. `sch_gen/api_integration_plan.py` - Multiple imports

## Fix Strategy

### Option 1: Replace sch_api imports with kicad_api equivalents
Since both provide similar functionality, replace:
- `sch_api.ReferenceManager` → `kicad_api` equivalent
- `sch_api.PlacementEngine` → `kicad_api.schematic.placement.PlacementEngine` (already used!)

### Option 2: Remove integration files entirely
These seem to be transition/integration files that may not be essential:
- `integrated_reference_manager.py` (244 lines)
- `integrated_placement.py` (279 lines)  
- `api_integration_plan.py` (216 lines)

## Investigation Needed

Check if these integration files are actually used in the working execution path or if they're just transition helpers that can be removed.