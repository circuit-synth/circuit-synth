# Test 23: Canonical Rename Detection (Python → KiCad)

## What This Tests

Tests whether the system can detect a component rename (R1 → R3) as a single rename operation rather than incorrectly treating it as delete+add. This requires **canonical circuit analysis** to understand circuit structure beyond reference matching.

## When This Situation Happens

- User has circuit with R1 resistor
- Decides to rename R1 to R3 (or R_PULLUP, etc.) for better organization
- Changes `ref="R1"` to `ref="R3"` in Python code
- Regenerates KiCad project
- Expects R1 to be renamed to R3, NOT deleted and re-added

## What Should Work

1. Circuit generated with R1 at specific position
2. Python code modified: `ref="R1"` → `ref="R3"` (no other changes)
3. Sync detects this as **RENAME** operation (canonical analysis)
4. KiCad updated: R1 renamed to R3
5. Position preserved (component doesn't move)
6. **ONE component** total in schematic (not two!)

## Current Broken Behavior

**Without canonical analysis**, the system:
1. Looks for R1 in Python → not found
2. Looks for R3 in schematic → not found
3. Incorrectly concludes: Delete R1, Add R3
4. Creates duplicate components

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/23_rename_python_canonical

# Step 1: Generate initial KiCad project with R1
uv run single_resistor.py
open single_resistor/single_resistor.kicad_pro
# Verify: ONE resistor labeled R1

# Step 2: Edit single_resistor.py - rename R1 to R3
# Change: ref="R1" → ref="R3"
# Keep everything else the same (value, footprint, etc.)

# Step 3: Regenerate KiCad project
uv run single_resistor.py

# Step 4: Check synchronization summary in logs
# Should detect rename, not delete+add

# Step 5: Open regenerated KiCad project
open single_resistor/single_resistor.kicad_pro

# Step 6: Verify correct behavior
# Expected: ONE resistor labeled R3 at original position
# Current broken: TWO resistors (R1 + R3)
```

## Expected Result (With Canonical Analysis)

**Sync Summary:**
```
📋 Synchronization Summary
Components in schematic: R1
Components in Python:    R3

Actions:
   🔄 Rename: R1 → R3 (canonical match detected)
```

**KiCad Schematic:**
- ✅ ONE resistor total
- ✅ Reference: R3
- ✅ Position preserved from R1
- ✅ Value preserved: 10k
- ✅ Footprint preserved: R_0603_1608Metric

## Actual Result (Without Canonical Analysis) ❌

**Sync Summary (INCORRECT):**
```
📋 Synchronization Summary
Components in schematic: R1
Components in Python:    R3

Actions:
   ⚠️ Remove: R1 (not in Python code)
   ➕ Add: R3 (new in Python)
```

**KiCad Schematic (BROKEN):**
- ❌ TWO resistors (R1 not deleted due to #336, R3 added)
- ❌ R1 at original position
- ❌ R3 at new auto-placed position
- ❌ Duplicate circuit

## Why This Is Critical

**Canonical Circuit Analysis** is essential for:
- Detecting renames vs. delete+add
- Understanding circuit structure semantically
- Preserving user intent during sync
- Avoiding duplicate components
- Maintaining schematic cleanliness

Without it, users cannot:
- Rename components for clarity (R1 → R_PULLUP)
- Reorganize reference designators
- Refactor circuit structure
- Trust bidirectional sync

## Canonical Analysis Algorithm

The system should:

1. **Fingerprint components** by properties beyond reference:
   - Symbol type (Device:R)
   - Value (10k)
   - Footprint (R_0603_1608Metric)
   - Position (if placed)
   - Connections (if any)

2. **Match by fingerprint**, not reference:
   - Schematic: 1 resistor (Device:R, 10k, 0603) ref=R1
   - Python: 1 resistor (Device:R, 10k, 0603) ref=R3
   - **Match detected!** → This is a rename

3. **Detect operation**:
   - Same fingerprint, different ref → RENAME
   - Same fingerprint, different value → UPDATE_VALUE
   - Different fingerprint → DELETE + ADD

## Related Issues

- **#338** - Component rename treated as delete+add (this test validates the fix)
- **#336** - Component deletion doesn't work (compounds rename issue)
- **#335** - PCB sync broken

## Test Environment

- circuit-synth version: 0.11.0
- Git commit: d14015d2

## Success Criteria

This test PASSES when:
- Renaming R1 → R3 in Python results in ONE component in KiCad
- Component labeled R3 appears at R1's original position
- No duplicate components created
- Sync summary shows "🔄 Rename" operation
