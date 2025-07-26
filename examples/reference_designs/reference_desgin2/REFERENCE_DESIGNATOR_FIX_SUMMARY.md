# KiCad Reference Designator Bug Fix Summary

## Issue
Components in hierarchical KiCad schematics were displaying as "R?", "C?", "U?" instead of proper reference numbers like "R1", "R2", "C1".

## Root Cause
The issue was caused by generating BOTH:
1. Instances embedded within each symbol (new KiCad format)
2. A symbol_instances table at the end of the file (old KiCad format)

This dual approach was confusing KiCad version 20250114.

## Solution
Modified `schematic_writer.py` to detect the KiCad version and:
- For KiCad version 20250114 and later: Skip the symbol_instances table (instances are embedded in symbols)
- For older versions: Continue adding the symbol_instances table

## Key Changes

### 1. Added Version Detection
```python
# Check KiCad version
kicad_version = None
for item in schematic_sexpr:
    if isinstance(item, list) and len(item) > 1 and item[0] == sexpdata.Symbol("version"):
        kicad_version = item[1]
        break
```

### 2. Conditional symbol_instances Table
```python
if kicad_version and isinstance(kicad_version, (int, str)):
    version_num = int(str(kicad_version))
    if version_num < 20250114:
        self._add_symbol_instances_table(schematic_sexpr)
    else:
        logger.info("Skipping symbol instances table for new KiCad format")
```

### 3. Instances Embedded in Symbols
Each symbol now correctly includes its own instances section:
```
(instances
    (project "python_generated_reference_design"
        (path /hierarchical/path/here
            (reference R1)
            (unit 1)
        )
    )
)
```

## Verification
- Components now display with correct references (R1, R2, C1, etc.) in KiCad
- Generated files match the expected format for KiCad version 20250114
- Both main and sub-sheets have properly formatted instances

## Files Modified
- `circuit_synth_repos/Circuit_Synth_Core/src/circuit_synth_core/kicad/sch_gen/schematic_writer.py`
- Added extensive logging to `s_expression.py` for debugging (can be removed later)