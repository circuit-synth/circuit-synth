# S-Expression Formatter Refactoring Status

## Overview
Refactoring the KiCad S-expression formatter from a complex 700+ line method to a clean, maintainable rule-based system.

## Completed ✅

### Phase 1: Analysis and Planning
- Analyzed existing `_format_sexp` method (700+ lines, 14 boolean parameters)
- Researched other implementations (SKiDL, kiutils, kicad-rw)
- Created comprehensive refactoring plan

### Phase 2: Clean Formatter Implementation
- Created `clean_formatter.py` with rule-based formatting
- Implemented `FormatRule` dataclass for configuration
- Added `FormattingRules` registry for tag-specific rules
- Implemented custom handlers for complex elements (properties, pins)

### Phase 3: Shadow Mode Integration
- Integrated clean formatter into `SExpressionParser`
- Added environment variable controls:
  - `CIRCUIT_SYNTH_USE_CLEAN_FORMATTER=1` - Use clean formatter
  - `CIRCUIT_SYNTH_SHADOW_MODE=1` - Compare both formatters
- Implemented output comparison and difference logging
- Added conversion from sexpdata format to plain lists

### Phase 4: Initial Testing
- Created comprehensive test suite (`test_shadow_mode.py`)
- Verified both formatters work independently
- Confirmed shadow mode comparison functionality
- Tested with real circuits

## Current Differences

The formatters produce functionally equivalent output with these formatting differences:

1. **Indentation**: Old uses tabs, new uses 2 spaces
2. **Quoting**: Improved consistency in string quoting
3. **Structure**: Cleaner separation of concerns

## Next Steps 🚀

### Phase 5: Rule Refinement
- [ ] Fine-tune quoting rules to match KiCad conventions exactly
- [ ] Add more custom handlers for special elements
- [ ] Optimize performance for large files

### Phase 6: Comprehensive Testing
- [ ] Test with all reference circuits
- [ ] Run against production KiCad files
- [ ] Performance benchmarking
- [ ] Edge case testing

### Phase 7: Migration
- [ ] Run shadow mode in production for validation
- [ ] Gradually enable clean formatter for subsets
- [ ] Full migration once confidence is high
- [ ] Remove old `_format_sexp` method

## Usage

### Testing Shadow Mode
```bash
# Enable shadow mode (compares both formatters)
export CIRCUIT_SYNTH_SHADOW_MODE=1
uv run python your_script.py

# Use clean formatter only
export CIRCUIT_SYNTH_USE_CLEAN_FORMATTER=1
uv run python your_script.py
```

### Running Tests
```bash
# Run shadow mode tests
uv run python tests/kicad/test_shadow_mode.py

# Run formatter migration tests
uv run python tests/kicad/test_formatter_migration.py
```

## Benefits

1. **Maintainability**: Rule-based system is much easier to understand and modify
2. **Extensibility**: Adding new formatting rules is straightforward
3. **Performance**: Cleaner code path, potential for optimization
4. **Testing**: Each rule can be tested independently
5. **Debugging**: Clear separation makes issues easier to locate

## Risk Mitigation

- **Shadow Mode**: Allows safe testing in production without affecting output
- **Gradual Migration**: Can enable for specific use cases first
- **Comprehensive Testing**: Extensive test coverage before full migration
- **Rollback Capability**: Environment variables allow instant rollback

## Architecture

```
SExpressionParser
├── dumps() - Entry point
│   ├── Shadow Mode: Run both, compare, use old
│   ├── Clean Mode: Use new formatter
│   └── Legacy Mode: Use old formatter
├── _format_sexp() - Old formatter (700+ lines)
└── _format_with_clean() - New formatter wrapper
    └── CleanSExprFormatter
        ├── FormattingRules - Registry of rules
        └── FormatRule - Individual formatting rules
```