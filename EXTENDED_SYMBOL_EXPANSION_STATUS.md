# Extended Symbol Expansion Feature Status

## Overview

The extended symbol expansion feature allows circuit-synth to handle KiCad symbols that extend other symbols (inheritance relationships). The main use case is components like `AMS1117-3.3` which extends `AP1117-15` in the KiCad symbol library.

**Goal**: Generate valid KiCad schematic files that contain complete symbol definitions instead of extends directives, allowing KiCad to open them without errors.

## Problem Statement

KiCad symbols can extend other symbols using `(extends "ParentName")` directive. When circuit-synth generates schematics with extended symbols, KiCad crashes with:
```
Error loading schematic: No parent for extended symbol AP1117-15 in 'file.kicad_sch'
```

This happens because the generated schematic contains the extends directive but not the parent symbol definition.

## Current Test Setup

### Primary Test Script
**Run this to test the feature:**
```bash
cd /Users/shanemattner/Desktop/circuit-synth3
python3 generate_reference_match.py
```

### Reference Target
The generated file should match:
```
/Users/shanemattner/Desktop/circuit-synth3/kicad_reference/kicad_reference.kicad_sch
```

**Important**: Ignore differences in timestamps, UUIDs, and other auto-generated values. Focus on:
- Symbol definition structure
- Property values (especially "Value" should be "AMS1117-3.3" not "AP1117-15")
- Symbol geometry sections (should be named "AMS1117-3.3_0_1" not "AP1117-15_0_1")
- No `(extends "...")` directive in the output

### Validation Test
```bash
kicad-cli sch export pdf generated_ams1117_match.kicad_sch --output test_validation.pdf
```
Should succeed without "Failed to load schematic" error.

## How the Rust Code Works

### Architecture
- **File**: `rust_modules/rust_kicad_integration/src/schematic_editor.rs`
- **Entry Point**: `ensure_lib_symbols()` function
- **Key Functions**:
  1. `extract_extends_directive()` - Detects if symbol extends another
  2. `load_symbol_from_library()` - Loads parent symbol from KiCad libraries  
  3. `expand_extended_symbol()` - Merges parent and child symbols

### Current Flow
1. **Symbol Detection**: When adding a symbol to lib_symbols, check if it has `(extends "ParentName")`
2. **Parent Loading**: If extends directive found, load parent symbol from KiCad symbol libraries
3. **Symbol Expansion**: Merge parent symbol content with child overrides
4. **Property Override**: Child properties should replace parent properties with same name
5. **Symbol Naming**: Update geometry section names from parent to child (e.g., `AP1117-15_0_1` → `AMS1117-3.3_0_1`)

### Debug Logging
The Rust code includes extensive logging with `eprintln!` statements:
- `🔍` - Symbol search and detection
- `🔗` - Extends relationship detection  
- `🔧 [EXPAND]` - Symbol expansion process
- `➕` - Symbol addition to lib_symbols
- `🔧 [RUST DEBUG]` - General debug info

## What Works ✅

1. **Extended Symbol Detection**: Successfully detects `(extends "AP1117-15")` directive
2. **Parent Symbol Loading**: Loads `Regulator_Linear:AP1117-15` from KiCad libraries
3. **Basic Symbol Expansion**: Creates complete symbol definition without extends directive
4. **Child Property Detection**: Identifies child properties that should override parent
5. **Symbol Structure**: Generates valid S-expression structure

## What Doesn't Work ❌

### 1. Property Override Logic
**Issue**: Duplicate properties in final symbol definition
```
(property "Value" "AP1117-15" ...)    # Parent property - should be removed
...
(property "Value" "AMS1117-3.3" ...)  # Child property - should remain
```

**Current Behavior**: Both properties appear, causing invalid KiCad file

### 2. Symbol Name Updates  
**Issue**: Geometry sections still use parent names
```
(symbol "AP1117-15_0_1" ...)   # Should be "AMS1117-3.3_0_1"
(symbol "AP1117-15_1_1" ...)   # Should be "AMS1117-3.3_1_1"
```

### 3. KiCad Validation
**Issue**: `kicad-cli` fails with "Failed to load schematic"
**Root Cause**: Duplicate properties create malformed S-expressions

## Previous Attempts

### Attempt 1: Simple Merge
- **Approach**: Append child properties after parent properties
- **Result**: Duplicate properties, KiCad load failure
- **Learning**: Need proper property deduplication

### Attempt 2: Property Name Tracking
- **Approach**: Track child property names, skip parent properties with same names
- **Implementation**: `HashSet<String>` to track child property names
- **Result**: Still seeing duplicates in output
- **Issue**: Logic bug in property filtering

### Attempt 3: Child-First Merge
- **Approach**: Start with child properties, add non-conflicting parent properties
- **Result**: Partial success, child properties at end but parent duplicates remain
- **Issue**: Parent property filtering not working correctly

## Next Steps to Try

### Immediate Priority: Fix Property Deduplication

1. **Debug Property Filtering**:
   - Add more logging to show exactly which parent properties are being skipped
   - Verify that `child_property_names` HashSet contains expected values
   - Log each parent property decision (include/skip)

2. **Simplify Property Override Logic**:
   ```rust
   // Create two separate lists
   let child_properties = extract_child_properties(child_symbol);
   let non_conflicting_parent_items = filter_parent_items(parent_items, child_property_names);
   let final_items = [child_properties, non_conflicting_parent_items].concat();
   ```

3. **Test Property Extraction Separately**:
   - Create unit test that verifies child property extraction
   - Verify parent property filtering works in isolation

### Secondary Priority: Fix Symbol Names

1. **Debug Symbol Name Updates**:
   - Add logging to `update_symbol_names_in_item()` function
   - Verify it's being called for geometry sections
   - Check if the string replacement logic works

2. **Simplify Symbol Name Logic**:
   ```rust
   // Find all symbol geometry sections and update names
   for item in merged_items.iter_mut() {
       if is_symbol_geometry_section(item) {
           update_symbol_geometry_name(item, child_name);
       }
   }
   ```

### Debugging Methodology

1. **Add Extensive Logging**:
   ```rust
   eprintln!("🔧 [PROPERTY DEBUG] Child properties found: {:?}", child_property_names);
   eprintln!("🔧 [PROPERTY DEBUG] Checking parent property: {}", prop_name);
   eprintln!("🔧 [PROPERTY DEBUG] Decision for {}: {}", prop_name, if should_include { "INCLUDE" } else { "SKIP" });
   ```

2. **Test Each Component**:
   - Property extraction from child symbol
   - Property filtering from parent symbol  
   - Symbol name updates in geometry sections
   - Final S-expression serialization

3. **Compare Outputs**:
   ```bash
   # Check for duplicate properties
   grep -n "property.*Value" generated_ams1117_match.kicad_sch
   
   # Check symbol names
   grep -n "symbol.*_[01]_1" generated_ams1117_match.kicad_sch
   
   # Count total properties
   grep -c "property" generated_ams1117_match.kicad_sch
   ```

## Build and Test Cycle

### 1. Rebuild Rust Module
```bash
cd rust_modules/rust_kicad_integration
cargo build
```

### 2. Reinstall Python Package  
```bash
cd /Users/shanemattner/Desktop/circuit-synth3
uv pip install -e . --force-reinstall
```

### 3. Run Test
```bash
python3 generate_reference_match.py
```

### 4. Analyze Output
```bash
# Check for issues
grep -n "property.*Value" generated_ams1117_match.kicad_sch
kicad-cli sch export pdf generated_ams1117_match.kicad_sch --output test.pdf

# Compare with reference
diff -u kicad_reference/kicad_reference.kicad_sch generated_ams1117_match.kicad_sch | head -50
```

### 5. Debug if Needed
- Check Rust logs for property decisions
- Add more logging if behavior unclear
- Test individual components in isolation

## Questions to Resolve

1. **Property Override Priority**: Should child properties completely replace parent properties with the same name, or should we merge their attributes?

2. **Symbol Name Strategy**: Should we update symbol names in-place or create new symbol structures with correct names?

3. **Error Handling**: How should we handle cases where parent symbol loading fails or parent/child symbols are malformed?

4. **Performance**: The current approach loads parent symbols every time - should we cache loaded symbols?

5. **Validation**: Should we add KiCad format validation before writing files to catch issues earlier?

## Success Criteria

- ✅ `python3 generate_reference_match.py` runs without errors
- ✅ Generated file has no duplicate properties  
- ✅ Value property shows "AMS1117-3.3" not "AP1117-15"
- ✅ Symbol geometry sections named "AMS1117-3.3_0_1" and "AMS1117-3.3_1_1"
- ✅ `kicad-cli sch export pdf generated_ams1117_match.kicad_sch --output test.pdf` succeeds
- ✅ Generated file structure matches reference (ignoring UUIDs/timestamps)

---

**Remember**: When in doubt, add more logging and test each component individually. The current approach is on the right track but needs debugging to fix the property deduplication and symbol naming issues.