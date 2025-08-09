# KiCad S-Expression Refactoring - Focused Plan

## Scope: ONLY S-Expression Logic Refactoring

### What We're Refactoring
- **The 700+ line `_format_sexp` method** with 14 boolean parameters
- **String manipulation chaos** in S-expression generation
- **Mixed formatting logic** scattered across files

### What We're NOT Touching
- Circuit class API
- JSON structure  
- Component creation
- generate_kicad_project method
- Hierarchy handling
- Any working functionality

## The Actual Problem

```python
# Current: 700+ lines of this in s_expression.py
def _format_sexp(self, sexp, indent=0, parent_tag=None, 
                 in_number=False, in_project=False, 
                 in_instances=False, in_page=False,
                 in_property_value=False, in_property_name=False,
                 in_generator=False, in_symbol=False,
                 in_lib_symbols=False, in_name=False,
                 in_text=False, in_reference=False):
    # Nested if statements tracking context...
    if in_property_name and index == 1:
        # Quote this
    elif in_number and not in_property:
        # Don't quote this
    elif parent_tag == "at" and index > 0:
        # Sometimes quote
    # ... 700 more lines of this
```

## The Solution: Simple Rule Registry

### 1. Create a Clean Formatter (New File)
```python
# src/circuit_synth/kicad/formatting/clean_formatter.py

from typing import Dict, List, Set, Tuple
import sexpdata
from sexpdata import Symbol

# Simple, maintainable rule registry
FORMATTING_RULES = {
    # tag: (inline, max_elements, quote_indices, special_handling)
    'at': (True, 4, set(), None),
    'xy': (True, 3, set(), None),
    'property': (True, None, {1, 2}, 'property_handler'),
    'lib_id': (True, 2, {1}, None),
    'uuid': (True, 2, {1}, None),
    'effects': (False, None, set(), None),
    'font': (True, 2, set(), None),
    'size': (True, 3, set(), None),
    'number': (True, 2, {1}, 'number_handler'),
    'project': (False, None, {1}, None),
    'path': (False, None, {1}, None),
    'page': (True, 2, {1}, None),
    'generator': (True, 2, {1}, None),
    'instances': (False, None, set(), 'instances_handler'),
}

class CleanSExprFormatter:
    """Clean S-expression formatter with simple rules."""
    
    def __init__(self):
        self.indent_str = "  "
        
    def format(self, sexp: list, indent: int = 0) -> str:
        """Format S-expression using rule registry."""
        if not isinstance(sexp, list):
            return self._format_atom(sexp)
        
        if not sexp:
            return "()"
        
        # Get tag and rules
        tag = self._get_tag(sexp)
        inline, max_elem, quote_idx, handler = FORMATTING_RULES.get(
            tag, (False, None, set(), None)
        )
        
        # Use special handler if defined
        if handler:
            handler_method = getattr(self, f'_handle_{handler}', None)
            if handler_method:
                return handler_method(sexp, indent)
        
        # Decide inline vs multiline
        if inline and (max_elem is None or len(sexp) <= max_elem):
            return self._format_inline(sexp, quote_idx)
        else:
            return self._format_multiline(sexp, indent, quote_idx)
    
    def _get_tag(self, sexp: list) -> str:
        """Get the tag (first element) of an S-expression."""
        if sexp and isinstance(sexp[0], Symbol):
            return str(sexp[0])
        return None
    
    def _format_atom(self, atom):
        """Format a single atom."""
        if isinstance(atom, Symbol):
            return str(atom)
        elif isinstance(atom, str):
            # Only quote if contains special characters
            if self._needs_quotes(atom):
                return f'"{self._escape_string(atom)}"'
            return atom
        elif isinstance(atom, float):
            # Round to prevent 117.94999999999999
            return str(round(atom * 10000) / 10000)
        else:
            return str(atom)
    
    def _needs_quotes(self, s: str) -> bool:
        """Check if string needs quotes."""
        if not s:
            return True
        # Special characters that require quoting
        special_chars = {' ', '\n', '\t', '"', '\\', '(', ')'}
        return any(c in s for c in special_chars)
    
    def _escape_string(self, s: str) -> str:
        """Escape special characters in string."""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    
    def _format_inline(self, sexp: list, quote_indices: Set[int]) -> str:
        """Format expression on single line."""
        parts = []
        for i, elem in enumerate(sexp):
            if i in quote_indices and isinstance(elem, str):
                parts.append(f'"{self._escape_string(elem)}"')
            else:
                parts.append(self.format(elem))
        return f"({' '.join(parts)})"
    
    def _format_multiline(self, sexp: list, indent: int, quote_indices: Set[int]) -> str:
        """Format expression across multiple lines."""
        lines = []
        current_indent = self.indent_str * indent
        next_indent = self.indent_str * (indent + 1)
        
        # First element (tag) on same line as opening paren
        tag = self.format(sexp[0]) if sexp else ""
        lines.append(f"({tag}")
        
        # Rest of elements on new lines
        for i, elem in enumerate(sexp[1:], 1):
            if i in quote_indices and isinstance(elem, str):
                formatted = f'"{self._escape_string(elem)}"'
            else:
                formatted = self.format(elem, indent + 1)
            lines.append(f"{next_indent}{formatted}")
        
        lines.append(f"{current_indent})")
        return "\n".join(lines)
    
    # Special handlers for complex cases
    def _handle_property_handler(self, sexp: list, indent: int) -> str:
        """Special handling for property elements."""
        # Properties are special: (property "Name" "Value" (at x y) ...)
        if len(sexp) >= 3:
            parts = [
                str(sexp[0]),  # 'property'
                f'"{sexp[1]}"',  # name - always quoted
                f'"{sexp[2]}"',  # value - always quoted
            ]
            # Format rest normally
            for elem in sexp[3:]:
                parts.append(self.format(elem))
            return f"({' '.join(parts)})"
        return self._format_inline(sexp, {1, 2})
    
    def _handle_number_handler(self, sexp: list, indent: int) -> str:
        """Special handling for pin numbers."""
        # Pin numbers should always be quoted as strings
        if len(sexp) >= 2 and isinstance(sexp[1], (str, int)):
            parts = [str(sexp[0]), f'"{sexp[1]}"']
            for elem in sexp[2:]:
                parts.append(self.format(elem))
            return f"({' '.join(parts)})"
        return self._format_inline(sexp, {1})
    
    def _handle_instances_handler(self, sexp: list, indent: int) -> str:
        """Special handling for instances block - always multiline."""
        return self._format_multiline(sexp, indent, set())
```

### 2. Adapter to Replace Existing Method
```python
# src/circuit_synth/kicad/formatting/adapter.py

from .clean_formatter import CleanSExprFormatter

# Global formatter instance
_formatter = CleanSExprFormatter()

def format_sexp_clean(sexp):
    """Drop-in replacement for the messy _format_sexp method."""
    return _formatter.format(sexp)

# Monkey patch to replace the old method (temporary during migration)
def install_clean_formatter():
    """Install the clean formatter in place of the old one."""
    from circuit_synth.kicad.core.s_expression import SExpressionParser
    
    # Save old method for rollback if needed
    SExpressionParser._format_sexp_old = SExpressionParser._format_sexp
    
    # Replace with clean version
    def clean_wrapper(self, sexp, **kwargs):
        # Ignore all the boolean parameters, just format cleanly
        return format_sexp_clean(sexp)
    
    SExpressionParser._format_sexp = clean_wrapper
```

### 3. Migration Strategy

#### Phase 1: Add Clean Formatter (No Breaking Changes)
```python
# Add new files without touching existing code
src/circuit_synth/kicad/formatting/
├── __init__.py
├── clean_formatter.py      # New clean formatter
├── adapter.py              # Adapter for compatibility
└── rules.py               # Formatting rules (if they grow)
```

#### Phase 2: Test in Parallel
```python
# In test files, compare outputs
def test_formatter_equivalence():
    """Ensure clean formatter produces equivalent output."""
    test_sexp = [...] # Various test cases
    
    old_output = old_format_sexp(test_sexp)
    new_output = format_sexp_clean(test_sexp)
    
    # Should produce functionally equivalent KiCad files
    assert kicad_loads(old_output) == kicad_loads(new_output)
```

#### Phase 3: Switch Over
```python
# In s_expression.py, replace the monster method
class SExpressionParser:
    def _format_sexp(self, sexp, **kwargs):
        # Old 700+ line method replaced with:
        from circuit_synth.kicad.formatting import format_sexp_clean
        return format_sexp_clean(sexp)
```

#### Phase 4: Clean Up
- Remove old boolean parameters
- Delete unused code
- Update tests

## Benefits of This Approach

### 1. **Maintainability**
- 700+ lines → ~200 lines
- 14 boolean parameters → 0 parameters
- Nested if/elif chaos → Simple rule lookup

### 2. **Extensibility**
```python
# Adding new formatting rule is trivial:
FORMATTING_RULES['new_element'] = (True, 3, {1}, None)

# Or add special handler:
def _handle_new_element_handler(self, sexp, indent):
    # Custom logic here
    pass
```

### 3. **Performance**
- O(1) rule lookup vs nested conditionals
- Less Python call stack depth
- Cleaner code = better JIT optimization

### 4. **Testability**
```python
def test_property_formatting():
    formatter = CleanSExprFormatter()
    sexp = [Symbol('property'), 'Reference', 'R1', ...]
    result = formatter.format(sexp)
    assert result == '(property "Reference" "R1" ...)'
```

## What This Doesn't Change

- ✅ Circuit API remains exactly the same
- ✅ JSON structure unchanged
- ✅ generate_kicad_project works as before
- ✅ All existing functionality preserved
- ✅ Output KiCad files remain compatible

## Implementation Timeline

### Week 1: Create Clean Formatter
- Implement CleanSExprFormatter class
- Define FORMATTING_RULES registry
- Add special handlers for complex cases
- Write comprehensive tests

### Week 2: Validate Equivalence  
- Test on example projects
- Compare with existing output
- Handle edge cases
- Performance benchmarks

### Week 3: Deploy and Clean Up
- Replace old method
- Remove boolean parameters
- Update documentation
- Delete old code

## Testing Strategy

```python
# Test with real circuits
def test_with_esp32_example():
    """Test with the ESP32 example project."""
    from example_project.circuit_synth.main import main_circuit
    
    circuit = main_circuit()
    
    # Generate with old formatter
    old_formatter_output = circuit.generate_kicad_project("old_output")
    
    # Switch to new formatter
    install_clean_formatter()
    
    # Generate with new formatter
    new_formatter_output = circuit.generate_kicad_project("new_output")
    
    # Both should work in KiCad
    assert kicad_can_open("old_output/ESP32_C6_Dev_Board.kicad_sch")
    assert kicad_can_open("new_output/ESP32_C6_Dev_Board.kicad_sch")
```

## Success Metrics

1. **Code Reduction**: 700+ lines → <200 lines (70%+ reduction)
2. **Complexity**: Cyclomatic complexity from ~100 → <20
3. **Performance**: Same or better (benchmark on 100+ component circuits)
4. **Compatibility**: 100% of existing circuits still work
5. **Maintainability**: New rules added in <5 lines of code

## Conclusion

This focused refactoring:
- **Only touches S-expression formatting** (the actual problem)
- **Doesn't break anything** (gradual migration)
- **Makes the code maintainable** (simple rule registry)
- **Preserves all functionality** (100% compatible)
- **Can be done in 3 weeks** (realistic timeline)

The key insight: We don't need complex patterns or complete rewrites. Just replace the chaotic string manipulation with a simple, rule-based formatter.