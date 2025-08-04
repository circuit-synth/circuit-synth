# KiCad Reference Display Issue ("R?" instead of "R1")

## Problem
Component references are displaying as "R?" instead of proper designators like "R1", "R2" in KiCad schematic viewer, despite the schematic files containing correct reference assignments.

## Background
- Issue emerged between v0.2.2 and v0.3.0 releases
- S-expression formatting changes broke KiCad's ability to parse component references
- Problem is in the circuit-synth to KiCad file generation pipeline

## Root Cause Analysis
The issue stems from malformed S-expression formatting in the KiCad schematic generation pipeline. While the schematic files contain correct reference data (e.g., `(reference R1)`), KiCad cannot properly parse and display them due to formatting issues.

## Attempted Solutions

### ✅ Completed (2025-08-04)
1. **Created hotfix branch**: `hotfix/revert-sexpression-v0.2.2`
2. **Identified problem files**: Located S-expression formatting issues in:
   - `src/circuit_synth/kicad_api/core/s_expression.py`
   - `src/circuit_synth/kicad/sch_gen/kicad_formatter.py` 
   - `src/circuit_synth/kicad/sch_gen/schematic_writer.py`
3. **Reverted core files**: Replaced formatter and writer files with v0.2.2 versions
4. **Verified schematic data**: Confirmed generated `.kicad_sch` files contain correct reference assignments

### 🔄 Current Status
- **Files reverted successfully**: Formatter and writer files now match v0.2.2
- **Schematic data correct**: References properly assigned as R1, R2 in file
- **Display issue persists**: KiCad still shows "R?" instead of proper references

## Key Findings
- The schematic file contains correct reference data: `(reference R1)`, `(reference R2)`
- Property formatting shows some Python dictionary remnants in symbol definitions
- Component instances have proper reference assignments in the `instances` sections
- Example problematic property formatting:
  ```
  (property
      "Reference"
      "{'value': 'R', 'position': {'x': 2.032, 'y': 0.0, 'rotation': 90.0}, 'effects': {'font_size': [1.27, 1.27]}}"
      ...
  ```

## Next Steps Required
1. **Investigate additional pipeline files**: Other S-expression generation components may need reverting
2. **Check property value formatting**: Address Python dictionary strings in property values
3. **Test complete pipeline**: Verify end-to-end generation produces KiCad-compatible output
4. **Consider symbol library issues**: May need to examine symbol definition formatting
5. **Review symbol property generation**: Fix the Python dict serialization in symbol properties

## Technical Context
- **Branch**: `hotfix/revert-sexpression-v0.2.2`
- **Test files**: `test_complete_revert/` directory contains generated circuit for testing
- **Key insight**: The issue is formatting-related, not reference assignment logic
- **Files reverted to v0.2.2**:
  - `src/circuit_synth/kicad/sch_gen/kicad_formatter.py`
  - `src/circuit_synth/kicad/sch_gen/schematic_writer.py`

## Working vs Broken Examples

### ✅ Working (Component Instances)
```
(symbol
    (lib_id Device:R)
    (property
        "Reference"
        "R2"
        (at 60.96 63.58 0)
        ...
    )
    (instances
        (project
            "test_complete_revert"
            (path "/cc603315-0be2-44f9-bf79-576816ca7b1a"
                (reference R2)
                (unit 1)
            )
        )
    )
)
```

### ❌ Broken (Symbol Library Definitions)
```
(property
    "Reference"
    "{'value': 'R', 'position': {'x': 2.032, 'y': 0.0, 'rotation': 90.0}, 'effects': {'font_size': [1.27, 1.27]}}"
    ...
)
```

## Critical Note
This is a critical S-expression formatting regression that prevents proper component reference display in KiCad, affecting the core circuit-synth to KiCad workflow.

## Date
- Issue reported: 2025-08-04
- Investigation started: 2025-08-04
- Current status: Partial fix applied, display issue persists