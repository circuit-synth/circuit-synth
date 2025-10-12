# Round-Trip Architecture

## Overview

Two code paths: **Generation** (new projects) and **Update** (existing projects)

```
Circuit.generate_kicad_project()
    ↓
SchematicGenerator.generate_project()
    ↓
_check_existing_project()
    ↓
    ├─ NO → Generation Path (create from scratch)
    │        └─> SchematicWriter.generate_s_expr()
    │
    └─ YES → Update Path (preserve manual work)
             └─> _update_existing_project()
                 └─> APISynchronizer
                     ├─> Match components (3 strategies)
                     ├─> Process matches (update values)
                     ├─> Process unmatched (add/preserve/remove)
                     └─> Save (preserve format)
```

## Automatic Mode Detection

`main_generator.py:628-643`

System automatically detects existing `.kicad_pro` and `.kicad_sch` files:
- **Found** → Update mode (preserve work)
- **Not found** → Generation mode (create fresh)
- **Update fails** → Fallback to regeneration

User never needs to choose - it just works.

## Component Matching (APISynchronizer)

Three strategies run in sequence:

1. **ReferenceMatchStrategy**: Match by reference (R1 → R1)
2. **ConnectionMatchStrategy**: Match by net connections
3. **ValueFootprintStrategy**: Match by value + footprint

First match wins, no conflicts allowed.

## Position Preservation

`main_generator.py:1140-1221`

When existing schematic detected:
1. Load existing schematic with kicad-sch-api
2. Extract component positions
3. Use canonical circuit matching to find correspondences
4. Apply preserved positions to matched components
5. New components placed collision-free

## Key Implementation Files

| File | Purpose | Key Functions |
|------|---------|--------------|
| `main_generator.py` | Entry point | `generate_project()`, `_update_existing_project()` |
| `synchronizer.py` | Core update logic | `sync_with_circuit()`, `_match_components()` |
| `hierarchical_synchronizer.py` | Multi-sheet support | `sync_with_circuit()` with subcircuits |
| `sync_strategies.py` | Matching algorithms | 3 strategy classes |
| `component_manager.py` | Component operations | `add_component()`, `update_component()` |

## Data Flow

1. **Load**: Read existing schematic with kicad-sch-api
2. **Extract**: Get circuit components from Python
3. **Match**: Find correspondences using strategies
4. **Process**: Update matched, add new, preserve/remove unmatched
5. **Save**: Write back with format preservation

## Hierarchical Support

`hierarchical_synchronizer.py`

Multi-sheet projects handled specially:
- Synchronizes each sheet independently
- Tracks sheet UUIDs for hierarchical paths
- Aggregates results across sheets
- Handles hierarchical label updates

## Format Preservation

All saving goes through kicad-sch-api's `ExactFormatter`:
- Preserves KiCad-compatible S-expression format
- Maintains indentation and quoting
- Ensures round-trip compatibility
- Fixed paper format quoting bug (was missing quotes)

## Error Handling

- **Update fails** → Fallback to regeneration
- **Component not found** → Skip gracefully
- **Match conflict** → First match wins
- **Invalid data** → Log error, continue

## Performance

- Component matching: O(n*m) with 3 strategies
- Position lookup: O(n) with hash map
- File I/O: Single read, single write per schematic
- Typical project: <2s total time
