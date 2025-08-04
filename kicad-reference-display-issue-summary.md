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

### ✅ ISSUE RESOLVED (2025-08-04)
- **Root cause identified**: Symbol library property values were being serialized as Python dictionary strings
- **Fix applied**: Modified `_create_symbol_definition` in `schematic_writer.py` to extract actual value from property info dict
- **Issue resolved**: KiCad now displays proper references (R1, R2, etc.) instead of "R?"

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

## Final Solution

The issue was caused by changes to the symbol parser between v0.2.2 and v0.3.0. The parser was modified to store property information as dictionaries containing value, position, and effects data, instead of simple strings. This caused the schematic writer to generate malformed symbol definitions with Python dictionary strings as property values.

**Complete fix required reverting two files to v0.2.2:**

1. **Symbol Parser** (`src/circuit_synth/kicad/kicad_symbol_parser.py`):
   - Reverted to store properties as simple strings: `result["properties"][prop_name] = prop_value`
   - Removed the complex dictionary structure that stored position and effects

2. **Schematic Writer** (`src/circuit_synth/kicad/sch_gen/schematic_writer.py`):
   - Already reverted in initial fix attempt
   - Works correctly with simple string property values

The root cause was a mismatch between what the parser produced (complex dictionaries) and what the schematic writer expected (simple strings). By reverting both files to their v0.2.2 versions, the reference display issue is completely resolved.

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