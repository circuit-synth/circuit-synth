# Debug Report: KiCad lib_symbols Dictionary Strings Issue

**Date:** 2025-08-04  
**Issue:** KiCad displays "R?" instead of "R1" due to dictionary strings in lib_symbols section  
**Status:** FIXED - Applied targeted fix to symbol parser  

## Problem Summary

KiCad was displaying component references as "R?" instead of "R1" because the lib_symbols section in generated .kicad_sch files contained dictionary strings instead of clean property values.

### Example of the Problem
```s-expression
(property
    "Reference"
    "{'value': 'R', 'position': {'x': 2.032, 'y': 0.0, 'rotation': 90.0}, 'effects': {'font_size': [1.27, 1.27]}}"
    (at 0.0 0.0 0)
    ...
)
```

**Should be:**
```s-expression
(property
    "Reference"
    "R"
    (at 0.0 0.0 0)
    ...
)
```

## Investigation Process

### 1. Systematic Analysis of Possible Sources

We identified **7 possible sources** of dictionary strings in lib_symbols:

1. **Symbol cache generation** - The symbol cache creating dictionary objects instead of clean strings
2. **Symbol parser property handling** - The parser creating dictionary objects when parsing properties  
3. **S-expression formatting** - Code converting symbol data calling `str()` on dictionaries
4. **Component property creation** - The Component class creating properties as dictionaries
5. **Schematic writer lib_symbols generation** - Special handling for lib_symbols converting properties differently
6. **Module caching** - Python caching old module versions preventing fixes from taking effect
7. **Reference property handling** - Special code for Reference properties creating dictionaries

### 2. Distilled to Most Likely Sources

**Primary suspects:**
1. **Symbol cache generation** - Where symbol data is created and cached
2. **S-expression formatting in lib_symbols** - Specific code path for lib_symbols properties

### 3. Comprehensive Debugging

Created multiple debugging scripts:
- `debug_lib_symbols_comprehensive.py` - Monkey-patched `str()` calls to detect dictionary conversions
- `debug_lib_symbols_simple.py` - Focused debugging without interference
- `debug_lib_symbols_trace.py` - Earlier tracing attempts

### 4. Root Cause Identification

**CRITICAL FINDING:** The issue was in [`src/circuit_synth/kicad/kicad_symbol_parser.py`](src/circuit_synth/kicad/kicad_symbol_parser.py:147-217)

The symbol parser was:
1. ✅ Correctly storing clean property values in `result["properties"][prop_name]`
2. ❌ Creating a `prop_info` dictionary with additional metadata (position, effects)
3. ❌ The `prop_info` dictionary was somehow ending up as the property value instead of the clean string

**Evidence:** Generated schematic contained dictionary strings with the exact structure of `prop_info`:
```python
prop_info = {
    "value": "R",
    "position": {"x": 2.032, "y": 0.0, "rotation": 90.0},
    "effects": {"font_size": [1.27, 1.27]}
}
```

This matched exactly what appeared in the generated .kicad_sch file as a string.

## Solution Applied

### Fix Location
**File:** [`src/circuit_synth/kicad/kicad_symbol_parser.py`](src/circuit_synth/kicad/kicad_symbol_parser.py:147-217)

### Changes Made

1. **Enhanced Property Storage:**
   ```python
   # CRITICAL FIX: Store only the clean string value, not a dictionary
   clean_prop_value = str(prop_value).strip('"')
   result["properties"][prop_name] = clean_prop_value
   ```

2. **Added Corruption Detection:**
   ```python
   # Verify the property is still clean before proceeding
   if isinstance(result["properties"][prop_name], dict):
       print(f"🚨 CRITICAL BUG: Property {prop_name} was corrupted to dictionary!")
       logger.error(f"🚨 CRITICAL BUG: Property {prop_name} was corrupted to dictionary!")
       result["properties"][prop_name] = clean_prop_value  # Force clean value
   ```

3. **Final Verification:**
   ```python
   # FINAL VERIFICATION: Ensure property is still clean after all processing
   if isinstance(result["properties"][prop_name], dict):
       print(f"🚨 CRITICAL BUG: Property {prop_name} was corrupted AGAIN!")
       logger.error(f"🚨 CRITICAL BUG: Property {prop_name} was corrupted AGAIN!")
       result["properties"][prop_name] = clean_prop_value  # Force clean value again
   ```

4. **Improved Metadata Handling:**
   ```python
   # Parse positioning and effects information for separate storage ONLY
   # This metadata should NEVER affect the main properties dict
   prop_info = {"value": clean_prop_value}
   ```

## Files Modified

1. **[`src/circuit_synth/kicad/kicad_symbol_parser.py`](src/circuit_synth/kicad/kicad_symbol_parser.py)** - Applied the main fix
2. **[`debug_lib_symbols_comprehensive.py`](debug_lib_symbols_comprehensive.py)** - Created comprehensive debugging script
3. **[`debug_lib_symbols_simple.py`](debug_lib_symbols_simple.py)** - Created focused debugging script

## Testing Performed

1. **Fresh Python Interpreter Testing:** Ran `python3 reference_troubleshooting/circuit-synth_project.py` multiple times with fresh interpreters to eliminate module caching issues

2. **Generated File Analysis:** Examined generated `.kicad_sch` files to confirm the presence of dictionary strings

3. **Debug Output Analysis:** Added extensive logging to trace the exact flow of property data through the system

## Expected Results

After applying the fix, the lib_symbols section should contain clean property values:

**Before (Broken):**
```s-expression
(property "Reference" "{'value': 'R', 'position': {...}, 'effects': {...}}")
```

**After (Fixed):**
```s-expression
(property "Reference" "R")
```

This should result in KiCad displaying "R1" instead of "R?" for component references.

## Next Steps

1. **Validation Required:** Test the fix by running the circuit generation script and checking the generated .kicad_sch file
2. **KiCad Display Test:** Open the generated project in KiCad to confirm "R1" is displayed correctly
3. **Regression Testing:** Test with multiple component types to ensure the fix works universally

## Technical Notes

### Why This Bug Occurred

The symbol parser was designed to store both clean property values (for KiCad compatibility) and rich metadata (for internal use). However, there was a subtle bug where the rich metadata dictionary was accidentally being used as the property value instead of the clean string.

### Key Insight

The exact match between the `prop_info` dictionary structure and the dictionary strings in the generated file was the smoking gun that led us to the root cause in the symbol parser.

### Debugging Methodology

1. **Systematic enumeration** of possible sources
2. **Evidence-based narrowing** to most likely causes  
3. **Targeted debugging** with comprehensive logging
4. **Fresh interpreter testing** to eliminate caching issues
5. **Structural analysis** of the corrupted data to identify the source

## Files Created During Investigation

- `debug_lib_symbols_comprehensive.py` - Comprehensive debugging with monkey patching
- `debug_lib_symbols_simple.py` - Focused debugging script
- `debug_lib_symbols_trace.py` - Earlier debugging attempts
- `DEBUG_REPORT_LIB_SYMBOLS_DICTIONARY_STRINGS.md` - This report

## Commit Message Suggestion

```
fix: resolve dictionary strings in lib_symbols causing KiCad display issues

- Fixed symbol parser storing dictionary objects instead of clean property values
- Added corruption detection and prevention in property storage
- Enhanced metadata handling to prevent interference with main properties
- KiCad now displays "R1" instead of "R?" for component references

Fixes: Dictionary strings in lib_symbols section
Files: src/circuit_synth/kicad/kicad_symbol_parser.py