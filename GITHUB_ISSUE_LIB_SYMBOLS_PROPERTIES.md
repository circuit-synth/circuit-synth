# Bug Report: lib_symbols Properties Generated as Dictionary Strings Instead of Simple Values

## Bug Description

Generated KiCad schematic files contain incorrect property formatting in the `lib_symbols` section. Properties are being serialized as dictionary strings instead of simple values, causing KiCad to display "?" next to component references.

## Expected vs Actual Behavior

**Expected Format** (from original KiCad files):
```
(property "Reference" "R"
    (at 2.032 0 90)
    (effects
        (font
            (size 1.27 1.27)
        )
    )
)
```

**Actual Format** (from generated files):
```
(property "Reference" "{'value': 'R', 'position': {'x': 2.032, 'y': 0.0, 'rotation': 90.0}, 'effects': {'font_size': [1.27, 1.27]}}"
    (at 0.0 0.0 0)
    (effects
        (font
            (size 1.27 1.27)
        )
        (hide no)
    )
)
```

## Impact

- Component references show as "?" in KiCad GUI instead of proper designators (R1, R2, etc.)
- Generated schematics are technically valid but visually incorrect
- Affects all component property types (Reference, Value, Description, etc.)

## Reproduction Steps

1. Create a simple circuit with components:
   ```python
   from circuit_synth import *
   
   @circuit(name='test')
   def test():
       r1 = Component(symbol="Device:R", ref="R1", value="10k")
   
   if __name__ == '__main__':
       circuit = test()
       circuit.generate_kicad_project(project_name="test_project")
   ```

2. Run the Python script to generate KiCad files
3. Examine the generated `.kicad_sch` file's `lib_symbols` section
4. Open in KiCad - component references will show as "?"

## Investigation Results

### ✅ Components Working Correctly

1. **KiCad Symbol Parser** (`kicad_symbol_parser.py`):
   - Correctly extracts enhanced property data from `.kicad_sym` files
   - Raw data: `'Reference': {'value': 'R', 'position': {...}, 'effects': {...}}`
   - This dictionary format is correct and expected

2. **Symbol Cache** (`symbol_cache.py`):
   - `_convert_to_symbol_definition()` properly extracts simple values from dictionary properties
   - Debug output: `reference_prefix: 'R'`, `name: 'R'`, `description: 'Resistor'`
   - SymbolDefinition objects contain correct simple string values

3. **S-Expression Generation (Isolated Testing)**:
   ```python
   # Direct testing works correctly
   cache = SymbolLibraryCache()
   symbol_def = cache.get_symbol('Device:R')
   parser = SExpressionParser()
   sexp = parser._symbol_definition_to_sexp(symbol_def)
   # Result: Reference: 'R', Value: 'R', Description: 'Resistor' ✅
   ```

### ❌ Broken Component

**Full Workflow S-Expression Generation**: When running the complete circuit generation workflow, `_generate_lib_symbols()` produces dictionary strings instead of simple values.

## Root Cause Analysis

The issue occurs specifically in the **system integration** between components. Individual components work correctly in isolation, but fail when integrated in the complete workflow.

### Evidence

| Test Type | SymbolDefinition Values | S-Expression Output | Status |
|-----------|------------------------|-------------------|---------|
| Isolated Symbol Cache | `reference_prefix: 'R'` | N/A | ✅ |
| Isolated S-Expression | `reference_prefix: 'R'` | `Reference: 'R'` | ✅ |
| Full Workflow | Unknown | `Reference: "{'value': 'R', ...}"` | ❌ |

### Hypothesis

During the full workflow, either:
1. A different SymbolDefinition object is being used with corrupted data
2. The symbol data is being modified between creation and S-expression generation  
3. There's a different symbol loading mechanism being triggered in `_generate_lib_symbols()`

## Debugging Information

### Debug Modifications Applied

1. **Symbol Cache** (`symbol_cache.py:742-745`):
   ```python
   if isinstance(reference_prop, dict):
       reference = reference_prop.get("value", "U")
       logger.debug(f"Extracted reference from dict: {reference_prop} -> {reference}")
   ```

2. **S-Expression Generator** (`s_expression.py:1444-1459`):
   ```python
   logger.debug(f"Processing properties for {symbol_def.lib_id}:")
   logger.debug(f"  symbol_def.reference_prefix = {repr(symbol_def.reference_prefix)}")
   # Added logging for all property processing steps
   ```

### Test Files

- **Minimal Reproduction**: `/tests/kicad_to_python/02_dual_hierarchy/test/main.py`
- **Expected Output**: `/tests/kicad_to_python/02_dual_hierarchy/02_dual_hierarchy/child1.kicad_sch` (lines 18-19)
- **Actual Output**: `/tests/kicad_to_python/02_dual_hierarchy/02_dual_hierarchy_generated/child1.kicad_sch` (lines 18-19)

## Environment

- **Branch**: `kicad-to-python`
- **Python Version**: 3.12.9
- **KiCad Version**: 9.0
- **Platform**: macOS Darwin 24.6.0

## Suggested Investigation Steps

1. **Enable Full Debug Logging**:
   ```bash
   cd tests/kicad_to_python/02_dual_hierarchy/test_debug
   uv run python main.py 2>&1 | grep -A10 -B5 "FULL_WORKFLOW\|Processing properties\|reference_prefix"
   ```

2. **Compare Symbol Objects**: Add logging to compare SymbolDefinition objects between isolated and full workflow execution

3. **Trace Property Value Source**: Add breakpoints in `_generate_lib_symbols()` to identify where dictionary strings originate

## Code Locations

- **Symbol Cache**: `src/circuit_synth/kicad_api/core/symbol_cache.py:730-879`
- **S-Expression Generator**: `src/circuit_synth/kicad_api/core/s_expression.py:1395-1418` (`_generate_lib_symbols()`)
- **Property Processing**: `src/circuit_synth/kicad_api/core/s_expression.py:1443-1463` (`_symbol_definition_to_sexp()`)
- **KiCad Symbol Parser**: `src/circuit_synth/kicad/kicad_symbol_parser.py:127-179`

## Workaround

None currently available. The issue affects all generated schematics.

## Priority

**High** - Affects visual correctness of all generated KiCad schematics, making them difficult to use and review.

---

**Labels**: `bug`, `kicad-integration`, `schematic-generation`, `high-priority`

**Assignee**: Development team

**Milestone**: Next release