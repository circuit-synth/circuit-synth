# Component Rename Detection - Entity Relationship Diagram (ERD)

## Current System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Bidirectional Sync Process                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Component Extraction                          │
│                                                                       │
│  ┌──────────────────┐                    ┌───────────────────┐     │
│  │ Circuit (Python) │                    │ Schematic (KiCad) │     │
│  │                  │                    │                   │     │
│  │  Components:     │                    │  Components:      │     │
│  │  - circuit_id    │                    │  - reference      │     │
│  │  - reference     │                    │  - value          │     │
│  │  - value         │                    │  - symbol         │     │
│  │  - symbol        │                    │  - position       │     │
│  │  - footprint     │                    │  - footprint      │     │
│  └──────────────────┘                    └───────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Component Matching Phase                        │
│                                                                       │
│  Strategy Pipeline (executed in order):                              │
│                                                                       │
│  1. ReferenceMatchStrategy                                           │
│     ┌────────────────────────────────────────────────────────┐     │
│     │ Match: circuit.reference == kicad.reference            │     │
│     │ Input: R2 (Python) vs R1 (KiCad)                       │     │
│     │ Result: NO MATCH ✓ (correct - different references)    │     │
│     └────────────────────────────────────────────────────────┘     │
│                                                                       │
│  2. ConnectionMatchStrategy                                          │
│     ┌────────────────────────────────────────────────────────┐     │
│     │ Match: by net connections and pin topology             │     │
│     │ Input: R2 has no nets, R1 has no nets                  │     │
│     │ Result: NO MATCH ✓ (correct - no connections)          │     │
│     └────────────────────────────────────────────────────────┘     │
│                                                                       │
│  3. ValueFootprintStrategy  ⚠️ PROBLEM HERE                         │
│     ┌────────────────────────────────────────────────────────┐     │
│     │ Match: by value + footprint similarity                 │     │
│     │ Input: R2 (10k, 0603) vs R1 (10k, 0603)                │     │
│     │ Result: MATCH ❌ (WRONG - matches by value/footprint!)  │     │
│     │                                                          │     │
│     │ Issue: This strategy assumes value+footprint is unique  │     │
│     │ But in renames, old and new have SAME value/footprint  │     │
│     │ Strategy cannot distinguish rename from "same type"     │     │
│     └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Matching Results                                │
│                                                                       │
│  matches = {                                                         │
│      "circuit_id_R2": "R1"  ❌ WRONG!                                │
│  }                                                                    │
│                                                                       │
│  Interpretation: "R2 in Python code matches R1 in schematic"         │
│                  → Sync thinks R1 is correct, just update value      │
│                  → Reference stays "R1" in schematic                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Process Matches Phase                           │
│                                                                       │
│  For matched pair (circuit_id_R2 → R1):                             │
│                                                                       │
│  1. Check if update needed:                                          │
│     - circuit.reference = "R2"                                       │
│     - kicad.reference = "R1"                                         │
│     - _needs_update() checks: value, footprint, BOM flags           │
│     - ❌ Does NOT check reference!                                   │
│                                                                       │
│  2. Update component:                                                │
│     - update_component(ref="R1", value="10k", ...)                  │
│     - ❌ Reference parameter is the KEY, not a field to update       │
│     - Result: R1 stays R1, only value/footprint updated             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Final Schematic State                           │
│                                                                       │
│  Component in schematic:                                             │
│  - Reference: "R1"  ❌ WRONG (should be R2)                          │
│  - Value: "10k"     ✓                                                │
│  - Footprint: R_0603_1608Metric  ✓                                  │
│                                                                       │
│  User expectation: Reference should be "R2"                          │
│  Actual result: Reference stays "R1"                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Problem Summary

**Root Cause:** `ValueFootprintStrategy` matches components by value+footprint, which causes it to match R2→R1 even though they have different references.

**Why This Fails:**
1. User renames R1 to R2 in Python code
2. Both components have same value (10k) and footprint (0603)
3. `ReferenceMatchStrategy` correctly fails to match (R2 ≠ R1)
4. `ValueFootprintStrategy` incorrectly matches R2→R1 (same value+footprint)
5. Sync thinks "R1 exists and matches R2, no rename needed"
6. Reference stays R1 in schematic

## Data Flow

```
Circuit Components:
{
  "R2_uuid": {
    "reference": "R2",
    "value": "10k",
    "symbol": "Device:R",
    "footprint": "Resistor_SMD:R_0603_1608Metric"
  }
}

KiCad Components:
{
  "R1": SchematicSymbol(
    reference="R1",
    value="10k",
    lib_id="Device:R",
    footprint="Resistor_SMD:R_0603_1608Metric",
    position=(30.48, 35.56),
    ...
  )
}

Matching Process:
1. ReferenceMatchStrategy: "R2" ≠ "R1" → No match
2. ConnectionMatchStrategy: No nets → No match
3. ValueFootprintStrategy: "10k" + "0603" == "10k" + "0603" → MATCH ❌

Result:
matches = { "R2_uuid": "R1" }  ← WRONG!

Process:
- Matched as R2→R1
- _needs_update() only checks value/footprint (not reference)
- update_component(ref="R1", ...) keeps R1 as reference
- Reference never gets updated to R2
```

## Entity Relationships

```
┌────────────────┐
│ APISynchronizer│
└────────┬───────┘
         │
         │ contains
         ▼
┌────────────────┐
│   strategies   │ (List[SyncStrategy])
└────────┬───────┘
         │
         ├─────────────┬─────────────────┬──────────────────┐
         │             │                 │                  │
         ▼             ▼                 ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌───────────────────┐
│  Reference   │ │ Connection   │ │ ValueFootprint    │
│   Match      │ │   Match      │ │    Match          │
│  Strategy    │ │  Strategy    │ │   Strategy        │
└──────────────┘ └──────────────┘ └───────────────────┘
     │                 │                    │
     │                 │                    │
     ▼                 ▼                    ▼
  Exact ref         Net topology      Value+Footprint
   matching          matching            matching
                                      ⚠️ TOO BROAD
```

## Key Insights

1. **Strategy Order Matters**: Strategies are tried in sequence, first match wins
2. **ValueFootprintStrategy is Too Broad**: Matches any component with same value+footprint
3. **No Rename Detection**: System has no concept of "this is a rename"
4. **No Reference Update**: `update_component()` uses reference as KEY, not as updatable field
5. **Position is Ignored**: Components at same position are not considered

## Solution Requirements

The fix must:
1. Detect when a component is renamed (same position + value + footprint, different reference)
2. Handle reference updates properly (rename operation, not just property update)
3. Prevent ValueFootprintStrategy from matching renamed components
4. Preserve position when renaming (don't move the component)
