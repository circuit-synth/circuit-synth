# Comment Preservation Analysis

**Date:** 2025-10-25
**Issue:** Comments in Python code are not preserved during KiCad → Python import
**Test:** `02_blank_generated.py` - Added comments to function docstring and function body, both were lost after re-import

---

## 🔍 Current Behavior

### Test Scenario
1. Generate blank KiCad project from Python (`01_blank_python.py`)
2. Import KiCad → Python (`02_blank_generated.py`)
3. Add comments to generated file:
   ```python
   @circuit
   def main():
       """Generated circuit from KiCad, here's some more comments!"""

       # Here is another test comment to see if it is preserved
       # COMMENTS!!!
   ```
4. Re-run import: `uv run kicad-to-python BlankTest/ 02_blank_generated.py`

### Result
**❌ Comments are completely overwritten**

After re-import:
```python
@circuit
def main():
    """Generated circuit from KiCad"""
    # All user comments are gone
```

---

## 📊 Code Generation Architecture

### Current Implementation

Located in: `/src/circuit_synth/tools/utilities/python_code_generator.py`

#### Key Classes & Methods:

**`PythonCodeGenerator`** - Main code generation class

**Code Generation Flow:**
```
update_python_file()
  ↓
_generate_flat_code() or generate_hierarchical_code()
  ↓
Generates completely new code from scratch
  ↓
Overwrites target file (with optional backup)
```

#### Backup System (Lines 406-410)
```python
# Create backup if requested and file exists
if backup and target_path.exists():
    backup_path = target_path.with_suffix(target_path.suffix + ".backup")
    backup_path.write_text(target_path.read_text())
    logger.info(f"📋 BACKUP: Created backup at {backup_path}")
```

**Current approach:**
- Creates `.backup` file before overwriting
- **Does NOT** read or preserve any existing code structure
- **Does NOT** parse existing Python file
- Completely regenerates from KiCad data

---

## 🚨 Problem Analysis

### Why Comments Are Lost

1. **No AST Parsing**: Code generator doesn't parse existing Python file
2. **Full Regeneration**: Always generates code from scratch based on KiCad data
3. **No Comment Storage in KiCad**: KiCad schematics don't store Python comments
4. **Data Flow is One-Way**:
   ```
   KiCad Data → Python Code (fresh generation)
   ```
   There's no:
   ```
   Existing Python Code → Merge with KiCad Data → Updated Python Code
   ```

### What Information is Lost

**User additions that don't map to KiCad:**
- ✗ Python comments (inline and docstring additions)
- ✗ Custom function logic
- ✗ Additional helper functions
- ✗ Import statements (beyond circuit_synth)
- ✗ Whitespace/formatting preferences
- ✗ Variable naming conventions (uses sanitized names)

**What IS preserved:**
- ✓ Circuit structure (components, nets)
- ✓ Component values
- ✓ Connections
- ✓ Circuit name

---

## 💡 Solution Strategies

### Strategy 1: AST-Based Merging (Recommended)

**Approach:** Parse existing Python file, preserve user code, update only circuit data

**Implementation:**
```python
import ast

def update_with_preservation(target_path, new_circuit_data):
    if target_path.exists():
        # Parse existing file
        existing_ast = ast.parse(target_path.read_text())

        # Extract user comments and custom code
        user_comments = extract_comments(existing_ast)
        user_functions = extract_non_generated_functions(existing_ast)

        # Generate new circuit code
        new_circuit_ast = generate_circuit_ast(new_circuit_data)

        # Merge: preserve user content + update circuit content
        merged_ast = merge_asts(existing_ast, new_circuit_ast, user_comments)

        # Write back
        write_ast_to_file(merged_ast, target_path)
    else:
        # Fresh generation if file doesn't exist
        generate_new_file(target_path, new_circuit_data)
```

**Pros:**
- ✓ Preserves ALL user comments
- ✓ Preserves custom functions
- ✓ Maintains user's code structure
- ✓ Professional IDE-like behavior

**Cons:**
- ✗ Complex implementation
- ✗ Need to handle AST parsing edge cases
- ✗ Must track which code is "generated" vs "user-added"

**Python Libraries:**
- `ast` (built-in) - Parse Python to AST
- `astor` or `astunparse` - Convert AST back to code
- `tokenize` (built-in) - Extract comments (comments aren't in AST)

---

### Strategy 2: Region Markers (Simpler)

**Approach:** Mark generated code regions, preserve everything outside markers

**Implementation:**
```python
# Generated code structure:

#!/usr/bin/env python3
"""
User can add comments here - PRESERVED
"""

from circuit_synth import *

# User can add custom functions here - PRESERVED

# BEGIN GENERATED CODE - DO NOT EDIT MANUALLY
@circuit
def main():
    """Generated circuit from KiCad"""
    # Circuit definition
    net1 = Net('VIN')
    # ...
# END GENERATED CODE

# User can add code here - PRESERVED

if __name__ == '__main__':
    circuit = main()
    # User can customize generation here - PRESERVED
    circuit.generate_kicad_project(project_name="MyProject")
```

**Update Process:**
1. Parse file, find `BEGIN GENERATED CODE` / `END GENERATED CODE` markers
2. Extract code outside markers (user code)
3. Generate new circuit code
4. Write: user_code_before + new_circuit + user_code_after

**Pros:**
- ✓ Simple implementation (string manipulation)
- ✓ Clear separation of generated vs user code
- ✓ Easy to understand for users
- ✓ Works with any text editor

**Cons:**
- ✗ User can't add comments inside circuit function
- ✗ Rigid structure
- ✗ Markers can be accidentally edited

---

### Strategy 3: Sidecar Comment Files

**Approach:** Store comments in separate `.comments.json` file

**Implementation:**
```python
# .comments.json stores:
{
  "line_10": ["# This is my comment", "# Another comment"],
  "function_main_docstring_append": "Additional docstring text",
  "custom_functions": ["def my_helper(): pass"]
}
```

**Update Process:**
1. Before regenerating, extract comments and save to `.comments.json`
2. Generate new code
3. Re-apply comments from `.comments.json` to new code

**Pros:**
- ✓ Comments stored separately from generated code
- ✓ Survives regeneration
- ✓ Version controllable

**Cons:**
- ✗ Comments separated from code (confusing)
- ✗ Line number mapping complex
- ✗ Hard to maintain consistency
- ✗ Not standard practice

---

### Strategy 4: KiCad Property Storage (Future Enhancement)

**Approach:** Store Python comments as KiCad schematic properties

**Implementation:**
- Add custom properties to KiCad schematic file
- Store comments/notes in schematic properties
- Round-trip: Python comments → KiCad properties → Python comments

**Example KiCad Property:**
```s-expr
(property "python_comments"
  "# This is a user comment\n# Another comment"
)
```

**Pros:**
- ✓ Comments survive round-trip
- ✓ True bidirectional sync
- ✓ Comments visible in KiCad (as properties)

**Cons:**
- ✗ Requires KiCad schema changes
- ✗ Complex to implement
- ✗ KiCad doesn't natively support code comments
- ✗ May clutter KiCad UI

---

## 🎯 Recommended Solution

**Phase 1: Region Markers (Quick Win)**
- Implement `BEGIN/END GENERATED CODE` markers immediately
- Simple, clear, gets 80% of value
- Users can add code before/after circuit definition
- Estimated effort: 4-6 hours

**Phase 2: AST-Based Merging (Complete Solution)**
- Implement full AST parsing and merging
- Preserves comments inline within circuit functions
- Professional IDE-like behavior
- Estimated effort: 2-3 days

**Phase 3: KiCad Property Storage (Future)**
- Investigate storing comments in KiCad properties
- Full bidirectional comment support
- Requires KiCad format research
- Estimated effort: 1-2 weeks

---

## 📋 Implementation Plan

### Phase 1: Region Markers (Immediate)

**Files to modify:**
- `/src/circuit_synth/tools/utilities/python_code_generator.py`

**Changes:**
1. Update `_generate_flat_code()`:
   ```python
   def _generate_flat_code(self, circuit: Circuit) -> str:
       code_parts = []

       # Header (user-editable)
       code_parts.extend([
           "#!/usr/bin/env python3",
           '"""',
           "Circuit Generated from KiCad",
           "User comments and customizations go here",
           '"""',
           "",
           "from circuit_synth import *",
           "",
           "# Add custom imports and functions above this line",
           "",
       ])

       # BEGIN marker
       code_parts.append("# BEGIN GENERATED CODE - DO NOT EDIT")
       code_parts.append("")

       # Generated circuit function
       code_parts.append("@circuit")
       code_parts.append("def main():")
       # ... rest of circuit generation

       # END marker
       code_parts.append("")
       code_parts.append("# END GENERATED CODE")
       code_parts.append("")

       # Footer (user-editable)
       code_parts.extend([
           "# Customize generation below:",
           "if __name__ == '__main__':",
           "    circuit = main()",
           "    circuit.generate_kicad_project()",
       ])

       return "\n".join(code_parts)
   ```

2. Update `update_or_create_file()` to preserve regions:
   ```python
   def update_or_create_file(self, target_path, ...):
       if target_path.exists():
           # Read existing file
           existing_code = target_path.read_text()

           # Extract user code outside markers
           user_header = extract_before_marker(existing_code, "# BEGIN GENERATED CODE")
           user_footer = extract_after_marker(existing_code, "# END GENERATED CODE")

           # Generate new circuit code
           new_circuit = self._generate_circuit_only(circuit)

           # Combine
           final_code = user_header + "\n# BEGIN GENERATED CODE\n" + new_circuit + "\n# END GENERATED CODE\n" + user_footer

           target_path.write_text(final_code)
       else:
           # Fresh generation
           content = self._generate_flat_code(circuit)
           target_path.write_text(content)
   ```

**Testing:**
1. Generate blank project
2. Import to Python
3. Add comments before `BEGIN` and after `END`
4. Re-import
5. Verify comments preserved

---

### Phase 2: AST-Based Merging (Future)

**Libraries needed:**
```python
pip install astor  # AST to code
```

**Files to create:**
- `/src/circuit_synth/tools/utilities/python_code_merger.py`

**Key classes:**
```python
class PythonCodeMerger:
    def __init__(self):
        self.tokenizer = CommentExtractor()

    def merge_with_existing(self, existing_file, new_circuit_data):
        # Parse existing
        existing_ast = ast.parse(existing_file.read())
        existing_comments = self.tokenizer.extract_comments(existing_file)

        # Generate new circuit AST
        new_circuit_ast = self.generate_circuit_ast(new_circuit_data)

        # Merge
        merged_ast = self.merge_circuit_function(
            existing_ast,
            new_circuit_ast,
            existing_comments
        )

        # Convert back to code
        return astor.to_source(merged_ast)

    def extract_comments(self, file_path):
        """Extract all comments with line numbers"""
        with open(file_path, 'rb') as f:
            tokens = tokenize.tokenize(f.readline)
            comments = {}
            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    comments[tok.start[0]] = tok.string
            return comments
```

**Testing:**
1. Generate project with components
2. Import to Python
3. Add comments throughout circuit function
4. Re-import
5. Verify ALL comments preserved

---

## 🔬 Testing Strategy

### Test Cases for Comment Preservation

**Test 1: Header Comments**
```python
#!/usr/bin/env python3
"""
My custom circuit
Author: John Doe
Date: 2025-10-25
"""
```
Expected: ✓ Preserved

**Test 2: Inline Comments in Circuit**
```python
@circuit
def main():
    # Power supply section
    vin = Net('VIN')  # Input from barrel jack
    gnd = Net('GND')  # Ground plane
```
Expected: ✓ Preserved (Phase 2 only)

**Test 3: Custom Functions**
```python
def calculate_resistor_value(voltage, current):
    return voltage / current

@circuit
def main():
    r_value = calculate_resistor_value(5, 0.1)
    # Use r_value...
```
Expected: ✓ Preserved

**Test 4: Modified if __name__**
```python
if __name__ == '__main__':
    circuit = main()
    # Custom output directory
    circuit.generate_kicad_project(
        project_name="MyCustomName",
        output_dir="custom_output/"
    )
```
Expected: ✓ Preserved

---

## 📚 Related Issues

- **Issue #XXX**: Python comments lost during sync (to be created)
- **Future**: Support for docstring preservation
- **Future**: Custom variable names preservation
- **Future**: Import statement preservation

---

## 🤔 Open Questions

1. **How to mark "user-modified" vs "generated" code?**
   - Region markers?
   - AST metadata?
   - Git-like diff tracking?

2. **What if user modifies circuit structure in Python?**
   - Should those changes go back to KiCad?
   - Or should we warn "generated code modified"?

3. **Conflict resolution:**
   - User adds Net('VCC') in Python
   - KiCad also has VCC net
   - How to merge?

4. **Performance:**
   - AST parsing adds overhead
   - Is it acceptable for large files?
   - Should we cache parsed ASTs?

---

## 📖 References

### Python AST Resources
- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
- [astor library](https://github.com/berkerpeksag/astor)
- [tokenize for comments](https://docs.python.org/3/library/tokenize.html)

### Code Generation Patterns
- "Code Generation with Preservation" patterns
- Template-based code generation
- AST manipulation best practices

### Similar Tools
- Django migrations (preserves custom operations)
- SQLAlchemy Alembic (preserves manual edits)
- OpenAPI code generators (often overwrite completely)

---

**Status:** Analysis complete, awaiting implementation decision
**Priority:** High (affects user workflow significantly)
**Complexity:** Medium (Phase 1), High (Phase 2)
