# Comment Preservation Analysis: Robustness for Millions of Circuits

**Date:** 2025-10-26
**Status:** Analysis & Recommendations
**Priority:** CRITICAL for user experience

---

## Executive Summary

The current comment preservation strategy in `CommentExtractor` has **critical weaknesses** that will cause problems at scale (millions of circuits, users, scenarios). This document analyzes these weaknesses and proposes robust alternatives.

**Key Finding:** The current strategy moves all comments to the top of the function, **destroying the association between comments and the code they document**. This makes comments useless for large circuits and causes silent data corruption when component order changes.

---

## Current Strategy Overview

### What It Does

```python
# 1. Format with Black (line_length=200) to normalize
existing_content = self._format_code_with_black(existing_content_raw, line_length=200)

# 2. Extract ALL content from function body
user_comments_map = self.extract_comments_from_function(existing_file, function_name)

# 3. Filter out generated patterns
generated_patterns = ['pass', '# Create components', '# Create nets']

# 4. Reinsert ALL comments at TOP of function body
merged_body = self.reinsert_comments(generated_func_body, user_comments_map)
```

### Example Transformation

**Before (user wrote):**
```python
@circuit
def voltage_divider():
    """5V → 3.3V voltage divider."""

    r1 = Component(ref="R1", value="10k")  # Upper resistor - critical value!
    r2 = Component(ref="R2", value="6.8k")  # Lower resistor - changed from 5.6k

    Net("VCC").connect(r1[1])
    Net("OUT").connect(r1[2], r2[1])  # This is the 3.3V tap point
    Net("GND").connect(r2[2])
```

**After round-trip:**
```python
@circuit
def voltage_divider():
    """5V → 3.3V voltage divider."""

    # Upper resistor - critical value!
    # Lower resistor - changed from 5.6k
    # This is the 3.3V tap point

    r1 = Component(ref="R1", value="10k")
    r2 = Component(ref="R2", value="6.8k")

    Net("VCC").connect(r1[1])
    Net("OUT").connect(r1[2], r2[1])
    Net("GND").connect(r2[2])
```

**Problem:** Comments are preserved but **context is lost**. Which comment applies to which component?

---

## Critical Weaknesses (Scale Analysis)

### 🔴 Problem 1: Comment-Code Association is Lost

**Scenario:** User carefully documents each component with inline comments.

**Original (Intent Clear):**
```python
r1 = Component(ref="R1", value="10k")  # This value is critical for 3.3V output
r2 = Component(ref="R2", value="20k")  # Changed from 15k on 2025-10-20
r3 = Component(ref="R3", value="5.6k")  # Pull-up resistor for I2C bus
```

**After Round-Trip (Intent Lost):**
```python
# This value is critical for 3.3V output
# Changed from 15k on 2025-10-20
# Pull-up resistor for I2C bus

r1 = Component(ref="R1", value="10k")
r2 = Component(ref="R2", value="20k")
r3 = Component(ref="R3", value="5.6k")
```

**Impact:**
- ❌ User cannot tell which comment applies to which component
- ❌ Documentation becomes useless
- ❌ For 1M users, this causes massive confusion and frustration
- ❌ Users stop writing comments (defeats entire purpose)

---

### 🔴 Problem 2: Component Order Changes Cause Silent Data Corruption

**Scenario:** KiCad or Python generation reorders components.

**Round 1 - User writes:**
```python
r1 = Component(ref="R1", value="10k")  # Upper resistor in voltage divider
r2 = Component(ref="R2", value="20k")  # Lower resistor in voltage divider
```

**Round 2 - Generated code reorders (alphabetically, by position, etc.):**
```python
# Upper resistor in voltage divider
# Lower resistor in voltage divider

r2 = Component(ref="R2", value="20k")  # NOW WRONG - comment says "upper" but it's R2
r1 = Component(ref="R1", value="10k")  # NOW WRONG - comment says "lower" but it's R1
```

**Impact:**
- ❌ **SILENT DATA CORRUPTION** - comments become WRONG, not just missing
- ❌ User trusts wrong information
- ❌ Can lead to circuit design errors
- ❌ No warning - system silently makes documentation incorrect

**Severity:** CRITICAL - this is worse than losing comments entirely.

---

### 🔴 Problem 3: Large Circuits Become Unusable

**Scenario:** User has 100+ components with detailed comments.

**Original (100 components):**
```python
r1 = Component(...)  # Power input stage - 5V from USB
r2 = Component(...)  # Voltage divider top - 10k precision resistor
r3 = Component(...)  # Voltage divider bottom - 6.8k matched pair
# ... 97 more components with specific comments ...
c1 = Component(...)  # Bypass capacitor - 10uF ceramic X7R
c2 = Component(...)  # Output filter - 100nF C0G for stability
```

**After Round-Trip:**
```python
# Power input stage - 5V from USB
# Voltage divider top - 10k precision resistor
# Voltage divider bottom - 6.8k matched pair
# ... 97 more comments ...
# Bypass capacitor - 10uF ceramic X7R
# Output filter - 100nF C0G for stability

r1 = Component(...)
r2 = Component(...)
r3 = Component(...)
# ... 97 more components ...
c1 = Component(...)
c2 = Component(...)
```

**Impact:**
- ❌ 100 comments at top - impossible to match to components
- ❌ User must manually re-associate every comment
- ❌ For large circuits (1000+ components), this is **completely unusable**
- ❌ Users abandon the tool

**Severity:** CRITICAL for professional/industrial use cases.

---

### 🔴 Problem 4: Multiple Comment Types Conflated

Current system treats all comments identically, destroying structure.

**Original (Structured Documentation):**
```python
@circuit
def power_supply():
    """Main power supply circuit."""

    # ================================================
    # POWER INPUT SECTION
    # ================================================
    # Accepts 5V from USB-C connector
    # Maximum current: 2A
    # ================================================

    r1 = Component(ref="R1", value="10k")  # Current sense resistor

    # ================================================
    # VOLTAGE REGULATION SECTION
    # ================================================

    # TODO: Replace with buck converter for better efficiency
    r2 = Component(ref="R2", value="5.6k")  # Feedback resistor - CRITICAL VALUE

    # NOTE: C1 must be ceramic X7R or better
    c1 = Component(ref="C1", value="10uF")  # Output capacitor
```

**After Round-Trip (Structure Destroyed):**
```python
# ================================================
# POWER INPUT SECTION
# ================================================
# Accepts 5V from USB-C connector
# Maximum current: 2A
# ================================================
# Current sense resistor
# ================================================
# VOLTAGE REGULATION SECTION
# ================================================
# TODO: Replace with buck converter for better efficiency
# Feedback resistor - CRITICAL VALUE
# NOTE: C1 must be ceramic X7R or better
# Output capacitor

r1 = Component(ref="R1", value="10k")
r2 = Component(ref="R2", value="5.6k")
c1 = Component(ref="C1", value="10uF")
```

**Impact:**
- ❌ Section headers mixed with inline comments
- ❌ TODOs/NOTEs lose context
- ❌ Visual structure destroyed
- ❌ Professional documentation becomes unreadable

---

### 🔴 Problem 5: AST-Based Filtering is Fragile

**Current Implementation (lines 583-598 in `comment_extractor.py`):**

```python
tree = ast.parse(existing_content)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id in ('Component', 'Net'):
                    # Mark this line as generated (don't preserve)
                    component_line_ranges.add(node.lineno)
```

**Fails in these cases:**

```python
# Case 1: Method chaining
comp = Component(ref="R1", value="10k")  # This comment IS preserved (bug)
comp.set_footprint("R_0805")  # But this line isn't detected as component code

# Case 2: List comprehension
components = [Component(ref=f"R{i}", value="10k") for i in range(10)]  # Lost

# Case 3: Conditional creation
if voltage > 3.3:
    r1 = Component(ref="R1", value="10k")  # Preserved incorrectly

# Case 4: Import alias
from circuit_synth import Component as C
comp = C(ref="R1", value="10k")  # Not detected! Preserved incorrectly

# Case 5: Factory function
def make_resistor(ref, value):
    return Component(ref=ref, value=value)

r1 = make_resistor("R1", "10k")  # Not detected as Component
```

**Impact:**
- ❌ Comments accidentally preserved (should be removed)
- ❌ Comments accidentally deleted (should be preserved)
- ❌ Inconsistent behavior across different coding styles
- ❌ Breaks for advanced Python patterns

---

### 🔴 Problem 6: Multi-Line Formatting Loses Parameter Comments

**Original (User Documents Each Parameter):**
```python
r1 = Component(
    ref="R1",
    value="10k",
    footprint="R_0805",  # Changed to 0805 for space constraints
    at=(30.48, 35.56)    # Positioned near C1 for short trace
)
```

**After Black (line_length=200):**
```python
r1 = Component(ref="R1", value="10k", footprint="R_0805", at=(30.48, 35.56))
# Comments on parameters are COMPLETELY LOST
```

**Impact:**
- ❌ Parameter-specific annotations destroyed
- ❌ Design rationale lost (why 0805? why that position?)
- ❌ Users stop documenting parameters
- ❌ Professional documentation impossible

---

### 🔴 Problem 7: Docstring Changes Overwritten

**Scenario:** User updates function docstring with design notes.

**User writes:**
```python
@circuit
def power_supply():
    """
    5V → 3.3V regulator using LDO.

    CRITICAL DESIGN NOTES:
    - Do not exceed 500mA load
    - Changed from LDO to buck converter (2025-10-20)
    - Tested at 85°C ambient temperature
    - Efficiency: 92% at 300mA load

    Bill of Materials:
    - U1: AP2112K-3.3 LDO regulator
    - C1, C2: 10uF ceramic X7R capacitors

    Author: John Doe
    Revision: v2.1
    """
```

**After Round-Trip (Generic Template Docstring):**
```python
@circuit
def power_supply():
    """Power supply circuit."""  # ALL USER DOCUMENTATION LOST
```

**Current System:** Does NOT preserve docstring changes (only preserves comments in function body).

**Impact:**
- ❌ Design documentation lost
- ❌ BOM information lost
- ❌ Test results lost
- ❌ Authorship/revision history lost

**Severity:** CRITICAL - docstrings are PRIMARY documentation location.

---

### 🔴 Problem 8: No Validation or Warnings

**Current behavior:** Silent data loss or corruption, no user feedback.

```python
# User writes 50 carefully documented components
# Round-trip happens
# Comments are moved to top (context lost)
# NO WARNING TO USER
# User opens file, sees comments at top, confused
```

**Impact:**
- ❌ User doesn't know comments were moved
- ❌ No indication of potential data loss
- ❌ No option to review changes before accepting
- ❌ Silent failures destroy user trust

---

## Scalability Analysis

| Circuit Size | Comment Count | Current Strategy | Impact |
|--------------|---------------|------------------|--------|
| Small (1-10 components) | 5-10 comments | **Acceptable** | Context mostly preserved |
| Medium (10-100 components) | 20-100 comments | **Problematic** | Context difficult to recover |
| Large (100-1000 components) | 100-500 comments | **Unusable** | Context completely lost |
| Massive (1000+ components) | 500+ comments | **Broken** | Tool abandonment |

**Conclusion:** Current strategy **does not scale** beyond small circuits.

---

## Edge Cases That Break Current System

### Edge Case 1: Dynamic Component Creation

```python
# User writes:
for i in range(10):
    # Resistor in voltage divider chain  <- Which resistor?
    r = Component(ref=f"R{i}", value="10k")
```

After round-trip: Comment moved to top, no indication which resistor(s) it refers to.

---

### Edge Case 2: Conditional Components

```python
if high_power_mode:
    # Use 5W resistor for high power  <- Lost context
    r1 = Component(ref="R1", value="10k", footprint="R_2512")
else:
    # Use standard 0.25W resistor  <- Lost context
    r1 = Component(ref="R1", value="10k", footprint="R_0805")
```

After round-trip: Both comments at top, both refer to `r1`, contradictory.

---

### Edge Case 3: Helper Functions

```python
def voltage_divider(vin, vout):
    """Create voltage divider resistor pair."""
    # Calculate resistor values
    r1_value = calculate_r1(vin, vout)  # Precision calculation
    r2_value = calculate_r2(vin, vout)  # Matched pair required

    r1 = Component(ref="R1", value=r1_value)
    r2 = Component(ref="R2", value=r2_value)
```

After round-trip: Comments about calculation lost (not associated with components).

---

### Edge Case 4: Import Variations

```python
# Variation 1:
from circuit_synth import Component
r1 = Component(ref="R1", value="10k")

# Variation 2:
from circuit_synth.core import Component as Comp
r1 = Comp(ref="R1", value="10k")  # Not detected by AST filter

# Variation 3:
import circuit_synth as cs
r1 = cs.Component(ref="R1", value="10k")  # Not detected
```

AST filtering breaks for non-standard imports.

---

## Root Cause Analysis

### Why Does Current System Fail?

**1. No Semantic Understanding**
- System treats comments as "text lines near code"
- Doesn't understand WHAT the comment is documenting

**2. Position-Based Association**
- Comments matched by line offset, not semantic relationship
- Line offsets change when code is regenerated

**3. Batch Processing**
- All comments extracted, filtered, then reinserted together
- Individual associations lost in batch

**4. One-Size-Fits-All**
- Same strategy for all comment types (section, inline, parameter, TODO)
- Different comment types need different handling

---

# 🟢 Robust Strategies for Millions of Circuits

## Strategy 1: Structured Metadata in JSON ⭐ **RECOMMENDED**

### Concept

Store comments explicitly as metadata in the KiCad JSON representation.

### Current KiCad JSON Schema

```json
{
  "components": [
    {
      "reference": "R1",
      "value": "10k",
      "footprint": "R_0805",
      "position": [30.48, 35.56, 0]
    }
  ],
  "nets": [
    {
      "name": "VCC",
      "pins": ["R1.1", "C1.1"]
    }
  ]
}
```

### Enhanced JSON Schema with Comment Metadata

```json
{
  "components": [
    {
      "reference": "R1",
      "value": "10k",
      "footprint": "R_0805",
      "position": [30.48, 35.56, 0],

      "user_comments": {
        "above": [
          "Upper resistor in voltage divider",
          "CRITICAL: Do not change without recalculating"
        ],
        "inline": "Changed from 12k on 2025-10-20",
        "parameters": {
          "value": "Precision value for 3.3V output",
          "footprint": "0805 size for space constraints",
          "position": "Near C1 for short trace"
        }
      }
    }
  ],

  "nets": [
    {
      "name": "VCC",
      "pins": ["R1.1", "C1.1"],
      "user_comments": {
        "inline": "Power rail - bypass cap required!",
        "above": ["Main power distribution net"]
      }
    }
  ],

  "function_metadata": {
    "docstring": "5V → 3.3V voltage divider.\n\nCRITICAL: Do not exceed 500mA...",
    "section_comments": {
      "before_R1": [
        "========================================",
        "POWER INPUT SECTION",
        "========================================"
      ],
      "after_R5": [
        "TODO: Add current limiting resistor"
      ]
    }
  }
}
```

### Workflow

**Python → KiCad (Comment Extraction):**

```python
def extract_comments_to_json(python_file: Path) -> dict:
    """Extract comments from Python and store in JSON metadata."""

    extractor = CommentExtractor()
    circuit_json = parse_circuit_to_json(python_file)

    # Parse Python file
    source = python_file.read_text()
    tree = ast.parse(source)
    lines = source.split('\n')

    # For each component in circuit
    for component in circuit_json['components']:
        ref = component['reference']

        # Find component assignment line in AST
        comp_line = find_component_assignment_line(tree, ref)

        if comp_line:
            # Extract comments ABOVE component
            above_comments = []
            for i in range(max(0, comp_line - 5), comp_line):
                line = lines[i].strip()
                if line.startswith('#'):
                    above_comments.append(line.lstrip('#').strip())

            # Extract INLINE comment (end-of-line)
            line = lines[comp_line]
            if '#' in line:
                inline_comment = line.split('#', 1)[1].strip()
            else:
                inline_comment = None

            # Store in JSON metadata
            component['user_comments'] = {
                'above': above_comments,
                'inline': inline_comment,
                'parameters': {}  # TODO: Extract from multi-line format
            }

    return circuit_json
```

**KiCad → Python (Comment Injection):**

```python
def inject_comments_from_json(circuit_json: dict) -> str:
    """Generate Python code with comments from JSON metadata."""

    code = []

    # Function docstring from metadata
    if 'function_metadata' in circuit_json:
        docstring = circuit_json['function_metadata'].get('docstring')
        if docstring:
            code.append(f'"""{docstring}"""')
            code.append('')

    # Section comments and components
    for component in circuit_json['components']:
        ref = component['reference']
        comments = component.get('user_comments', {})

        # Section comments before component
        section_key = f"before_{ref}"
        if 'function_metadata' in circuit_json:
            section_comments = circuit_json['function_metadata'].get('section_comments', {}).get(section_key, [])
            for comment in section_comments:
                code.append(f"# {comment}")

        # Comments above component
        for comment in comments.get('above', []):
            code.append(f"# {comment}")

        # Component line with inline comment
        var_name = ref.lower()
        comp_line = f'{var_name} = Component(ref="{ref}", value="{component["value"]}"'

        if component.get('footprint'):
            comp_line += f', footprint="{component["footprint"]}"'

        if component.get('position'):
            pos = component['position']
            comp_line += f', at=({pos[0]}, {pos[1]})'

        comp_line += ')'

        # Add inline comment if exists
        if comments.get('inline'):
            comp_line += f'  # {comments["inline"]}'

        code.append(comp_line)
        code.append('')

    return '\n'.join(code)
```

### Pros

✅ **Perfect Preservation**
- Comments stay with their objects (component, net, etc.)
- Association never lost
- Survives any code reordering

✅ **Scalable**
- Works for 1 component or 10,000 components
- O(n) complexity
- No ambiguity

✅ **Handles All Comment Types**
- Inline comments (end-of-line)
- Above comments (block before component)
- Parameter comments (multi-line format)
- Section comments (between components)
- Docstrings (function-level)

✅ **Robust to Code Changes**
- Component order changes? Comments follow
- Component renamed? Comments follow (by reference)
- Component deleted? Comments deleted too (correct behavior)

✅ **Idempotent**
- Round-trip → Round-trip → ... always produces same result
- No accumulation of duplicate comments

✅ **Debuggable**
- JSON metadata is human-readable
- Easy to inspect what comments are stored
- Can manually edit JSON if needed

### Cons

⚠️ **Implementation Complexity**
- Requires JSON schema extension
- Need to update Python → KiCad exporter
- Need to update KiCad → Python importer

⚠️ **Not Backwards Compatible**
- Old JSON files don't have comment metadata
- Need migration strategy for existing circuits

⚠️ **Requires Two-Phase Extraction**
- Phase 1: Extract circuit structure
- Phase 2: Extract comments and associate with structure

### Implementation Effort

- **Schema Design**: 1 day
- **Python → JSON Comment Extraction**: 3 days
- **JSON → Python Comment Injection**: 2 days
- **Testing & Edge Cases**: 2 days
- **Total**: ~1-2 weeks

---

## Strategy 2: Structured Comment Annotations

### Concept

Teach users to write structured comments with explicit tags that specify what they're documenting.

### Example Syntax

```python
@circuit
def power_supply():
    """
    5V → 3.3V voltage divider.

    @design_note: Changed from LDO to buck converter for efficiency
    @test_status: Verified at 85°C ambient, 92% efficiency at 300mA
    @author: John Doe
    @date: 2025-10-26
    @revision: v2.1
    """

    # @section: Power Input Stage
    # Accepts 5V from USB-C connector, max 2A

    # @component: R1
    # @purpose: Upper resistor in voltage divider
    # @critical: Do not change without recalculating output voltage
    # @changed: Increased from 10k to 12k on 2025-10-20
    r1 = Component(ref="R1", value="12k")  # @inline: Precision 1% tolerance

    # @component: R2
    # @purpose: Lower resistor in voltage divider
    # @note: Matched pair with R1
    r2 = Component(ref="R2", value="6.8k")

    # @net: VCC
    # @purpose: Main power distribution
    # @critical: Bypass cap required at each IC
    Net("VCC").connect(r1[1], c1[1])  # @inline: Power input
```

### Parser

```python
import re
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class StructuredComment:
    """A structured comment with explicit associations."""
    target_type: str  # 'component', 'net', 'section', 'function'
    target_id: str    # 'R1', 'VCC', etc. (or None for section/function)
    tags: Dict[str, str]  # {tag: value}

def extract_structured_comments(code: str) -> List[StructuredComment]:
    """Extract @tag: value annotations from code."""

    comments = []
    current_target = None
    current_tags = {}

    for line in code.split('\n'):
        # Check for target declarations
        if match := re.match(r'#\s*@(component|net|section):\s*(\w+)', line):
            # Save previous target if exists
            if current_target:
                comments.append(StructuredComment(
                    target_type=current_target[0],
                    target_id=current_target[1],
                    tags=current_tags
                ))

            # Start new target
            current_target = (match.group(1), match.group(2))
            current_tags = {}

        # Check for tag: value pairs
        elif match := re.match(r'#\s*@(\w+):\s*(.+)', line):
            tag = match.group(1)
            value = match.group(2)
            current_tags[tag] = value

        # Check for inline comments
        elif '@inline:' in line:
            inline_match = re.search(r'#\s*@inline:\s*(.+)', line)
            if inline_match and current_target:
                current_tags['inline'] = inline_match.group(1)

    # Save last target
    if current_target:
        comments.append(StructuredComment(
            target_type=current_target[0],
            target_id=current_target[1],
            tags=current_tags
        ))

    return comments

def preserve_structured_comments(original_code: str, generated_code: str) -> str:
    """Preserve structured comments during code generation."""

    # Extract structured comments from original
    orig_comments = extract_structured_comments(original_code)

    # Build comment index: target_id → StructuredComment
    comment_index = {}
    for comment in orig_comments:
        key = f"{comment.target_type}:{comment.target_id}"
        comment_index[key] = comment

    # Inject comments into generated code
    result_lines = []
    for line in generated_code.split('\n'):
        # Check if this line creates a component
        if match := re.match(r'(\w+)\s*=\s*Component\(ref="(\w+)"', line):
            var_name = match.group(1)
            ref = match.group(2)

            # Look up comments for this component
            key = f"component:{ref}"
            if key in comment_index:
                comment = comment_index[key]

                # Add above comments
                for tag in ['purpose', 'critical', 'note', 'changed']:
                    if tag in comment.tags:
                        result_lines.append(f"# @{tag}: {comment.tags[tag]}")

                # Add line with inline comment
                if 'inline' in comment.tags:
                    line += f"  # @inline: {comment.tags['inline']}"

        result_lines.append(line)

    return '\n'.join(result_lines)
```

### Pros

✅ **Explicit Associations**
- No ambiguity - user declares what's being documented
- Comments survive any reordering

✅ **User Control**
- Users choose what to preserve with @preserve or similar tag
- Can mark important vs. temporary comments

✅ **Semantic Tags**
- @critical, @purpose, @changed, etc. convey meaning
- Can generate reports (all @critical notes, all @changed history)

✅ **Backwards Compatible**
- Existing comments without tags still work (fallback to current strategy)
- Users can gradually adopt structured comments

✅ **IDE-Friendly**
- Syntax highlighting can recognize @tags
- Auto-completion for common tags
- Linters can validate tag structure

### Cons

⚠️ **User Learning Curve**
- Users must learn annotation syntax
- More verbose than simple comments
- Not intuitive for beginners

⚠️ **Adoption Challenge**
- Existing circuits have no structured comments
- Users might not adopt (prefer simple #comments)
- Requires documentation and examples

⚠️ **Still Requires Parsing**
- Need to extract and inject annotations
- Complex regex/parsing logic

⚠️ **No Standard**
- Custom syntax (not Python standard)
- Could conflict with other tools

### Implementation Effort

- **Syntax Design**: 1 day
- **Parser Implementation**: 2 days
- **Injection Logic**: 2 days
- **Documentation & Examples**: 1 day
- **Total**: ~1 week

---

## Strategy 3: Diff-Based Comment Preservation

### Concept

Compare original and generated code semantically, then match comments to their associated code elements using heuristics.

### Algorithm

```python
def preserve_comments_by_diff(original_py: Path, generated_code: str) -> str:
    """
    Preserve comments using semantic diffing and heuristic matching.
    """

    # 1. Parse both to canonical circuit representation
    orig_circuit = parse_circuit_to_canonical(original_py)
    gen_circuit = parse_circuit_to_canonical_str(generated_code)

    # 2. Build comment index from original code
    comment_index = {}

    for component in orig_circuit.components:
        # Find component in original source
        comp_node = find_component_node_in_ast(original_py, component.reference)

        if comp_node:
            # Extract comments "near" this component
            nearby_comments = extract_comments_near_line(
                original_py,
                comp_node.lineno,
                window=5  # Look 5 lines above/below
            )

            comment_index[component.reference] = {
                'above': nearby_comments['above'],
                'inline': nearby_comments['inline'],
                'below': nearby_comments['below']
            }

    # 3. Inject comments into generated code
    result = []
    gen_lines = generated_code.split('\n')

    for i, line in enumerate(gen_lines):
        # Check if this line creates a component
        if match := re.match(r'(\w+)\s*=\s*Component\(ref="(\w+)"', line):
            ref = match.group(2)

            if ref in comment_index:
                comments = comment_index[ref]

                # Add above comments
                for comment in comments['above']:
                    result.append(comment)

                # Add line with inline comment
                if comments['inline']:
                    line += f"  {comments['inline']}"

        result.append(line)

    return '\n'.join(result)


def extract_comments_near_line(file_path: Path, line_num: int, window: int = 5) -> dict:
    """
    Extract comments near a specific line.

    Returns:
        {
            'above': [comment lines before target],
            'inline': inline comment on target line,
            'below': [comment lines after target]
        }
    """
    with open(file_path) as f:
        lines = f.readlines()

    comments = {'above': [], 'inline': None, 'below': []}

    # Check above (within window)
    for i in range(max(0, line_num - window), line_num):
        line = lines[i].strip()
        if line.startswith('#'):
            comments['above'].append(lines[i].rstrip())
        elif line:  # Non-empty, non-comment line breaks the "above" group
            comments['above'] = []  # Reset - only want contiguous comments

    # Check inline (on target line)
    target_line = lines[line_num]
    if '#' in target_line:
        # Extract inline comment
        parts = target_line.split('#', 1)
        if len(parts) == 2:
            comments['inline'] = '#' + parts[1].rstrip()

    # Check below (within window)
    for i in range(line_num + 1, min(len(lines), line_num + window + 1)):
        line = lines[i].strip()
        if line.startswith('#'):
            comments['below'].append(lines[i].rstrip())
        elif line:  # Non-empty line ends "below" group
            break

    return comments
```

### Pros

✅ **No Schema Changes**
- Works with existing JSON format
- No user-facing syntax changes

✅ **Backwards Compatible**
- Works on existing code immediately
- No migration needed

✅ **Simple User Experience**
- Users write normal comments
- No special annotations required

### Cons

⚠️ **Heuristic-Based**
- "Near" is ambiguous (how many lines?)
- False positives (comment matched to wrong component)
- False negatives (comment not matched to any component)

⚠️ **Complex Edge Cases**
- What if two components on adjacent lines? Which comment belongs to which?
- What if there's a blank line between comment and component?
- What about comments between components?

⚠️ **Not Robust**
- Heuristics fail for unusual code structures
- Different users = different coding styles = different failures

⚠️ **Still Loses Context**
- Section comments hard to associate
- TODOs between components ambiguous

### Implementation Effort

- **Canonical Parser**: 2 days (if not exists)
- **Comment Extraction Heuristics**: 3 days
- **Injection Logic**: 2 days
- **Edge Case Handling**: 3 days
- **Total**: ~2 weeks

**Verdict:** Complex implementation, unreliable results. **Not recommended.**

---

## Strategy 4: Best-Effort with Clear Warnings (Current System Enhanced)

### Concept

Keep current system but add **explicit warnings** so users know what to expect.

### Enhanced Current System

```python
def reinsert_comments_with_warning(
    generated_lines: List[str],
    comments_map: Dict[int, List[str]]
) -> List[str]:
    """
    Re-insert comments at top of function with CLEAR WARNING to user.
    """

    if not comments_map:
        return generated_lines

    # Count comments
    comment_count = sum(len(lines) for lines in comments_map.values())

    # Generate warning header
    warning = [
        "# " + "=" * 70,
        "# USER COMMENTS (moved to top - manual review recommended)",
        "# " + "=" * 70,
        f"# {comment_count} comment(s) extracted from previous version.",
        "# These comments may have lost their original context.",
        "# Please review and reposition as needed.",
        "#",
        "# TIP: Use structured comments like '@component: R1' for",
        "# automatic association in future round-trips.",
        "# " + "=" * 70,
        "",
    ]

    # Collect all comments
    all_comments = []
    for offset in sorted(comments_map.keys()):
        for comment_line in comments_map[offset]:
            all_comments.append(comment_line)

    # Insert warning + comments at top
    result = warning + all_comments + [""] + generated_lines

    return result
```

### Pros

✅ **Quick to Implement**
- Minimal changes to existing system
- 1 day implementation

✅ **User Awareness**
- Clear warning about context loss
- Users know to review manually

✅ **No Breaking Changes**
- Existing code continues to work
- No migration needed

### Cons

⚠️ **Still Loses Context**
- Core problem not solved
- Just made user aware of problem

⚠️ **Not Scalable**
- Large circuits still unusable
- Manual review not practical for 100+ comments

⚠️ **Warning Fatigue**
- Users will ignore warning after seeing it multiple times
- Doesn't actually solve the problem

**Verdict:** **NOT RECOMMENDED** - this is a band-aid, not a solution.

---

## Hybrid Strategy: Phased Approach ⭐ **RECOMMENDED IMPLEMENTATION PLAN**

Combine multiple strategies in phases:

### Phase 1: JSON Metadata Foundation (Required)

**Goal:** Store comments robustly in JSON metadata.

**Implementation:**
1. Extend JSON schema with `user_comments` fields
2. Update Python → KiCad exporter to extract comments to JSON
3. Update KiCad → Python importer to inject comments from JSON

**Timeline:** 2 weeks

**Benefit:** Solves 90% of problems for 100% of users (automatic, no user training required).

---

### Phase 2: Structured Annotations (Optional)

**Goal:** Let power users opt-in to explicit annotation syntax.

**Implementation:**
1. Design annotation syntax (`@component: R1`, `@purpose:`, etc.)
2. Add parser for annotations
3. Integrate with JSON metadata system
4. Document with examples

**Timeline:** 1 week

**Benefit:** Provides explicit control for advanced users and professional documentation.

---

### Phase 3: Validation & Warnings (Quality)

**Goal:** Detect and warn about comment preservation issues.

**Implementation:**
1. Add validation in round-trip tests
2. Warn user if comments can't be associated
3. Provide suggestions for improvement
4. Report comment preservation stats

**Timeline:** 1 week

**Benefit:** User confidence, early detection of problems.

---

### Phase 4: IDE Support (Nice-to-Have)

**Goal:** Make structured comments easy to write.

**Implementation:**
1. VS Code extension with snippet support
2. Auto-completion for @tags
3. Syntax highlighting for annotations
4. Validation linting

**Timeline:** 2-3 weeks

**Benefit:** Adoption of structured comments, better UX.

---

## Implementation Roadmap

### Week 1-2: JSON Metadata (Core)

```
Day 1-2:   Design enhanced JSON schema
Day 3-4:   Implement comment → JSON extraction
Day 5-6:   Implement JSON → comment injection
Day 7-8:   Integration testing
Day 9-10:  Edge case handling
```

**Deliverable:** Comment preservation via JSON metadata (automatic, robust).

---

### Week 3: Structured Annotations (Optional)

```
Day 1:     Design annotation syntax
Day 2-3:   Implement parser
Day 4-5:   Integration with JSON system
```

**Deliverable:** Users can use @tags for explicit control.

---

### Week 4: Validation & Testing

```
Day 1-2:   Write validation functions
Day 3-4:   Add to round-trip tests
Day 5:     Documentation and examples
```

**Deliverable:** Comprehensive test coverage, validated comment preservation.

---

## Decision Matrix

| Strategy | Robustness | Implementation | User Impact | Recommended? |
|----------|-----------|----------------|-------------|--------------|
| **JSON Metadata** | ⭐⭐⭐⭐⭐ Excellent | 2 weeks | Zero (automatic) | ✅ **YES** |
| **Structured Annotations** | ⭐⭐⭐⭐ Very Good | 1 week | Medium (opt-in) | ✅ **YES** (Phase 2) |
| **Diff-Based** | ⭐⭐ Poor | 2 weeks | Zero | ❌ **NO** (unreliable) |
| **Enhanced Current** | ⭐ Very Poor | 1 day | High (confusion) | ❌ **NO** (band-aid) |
| **Hybrid (JSON + Annotations)** | ⭐⭐⭐⭐⭐ Excellent | 3 weeks | Low (mostly automatic) | ✅ **YES** ⭐ |

---

## For Round-Trip Validation

### Validation Strategy

```python
def validate_comments_robust(
    original_py: Path,
    original_json: Path,
    roundtrip_py: Path,
    roundtrip_json: Path
) -> ValidationResult:
    """
    Comprehensive comment validation using JSON metadata.
    """

    errors = []
    warnings = []

    # Load JSON metadata
    orig_data = json.loads(original_json.read_text())
    rt_data = json.loads(roundtrip_json.read_text())

    # 1. Validate component comments preserved
    for comp in orig_data['components']:
        ref = comp['reference']
        orig_comments = comp.get('user_comments', {})

        # Find matching component in round-trip
        rt_comp = next((c for c in rt_data['components'] if c['reference'] == ref), None)

        if rt_comp is None:
            errors.append(f"Component {ref} missing in round-trip")
            continue

        rt_comments = rt_comp.get('user_comments', {})

        # Compare comment metadata
        if orig_comments != rt_comments:
            errors.append(f"{ref}: comments differ")
            errors.append(f"  Original: {orig_comments}")
            errors.append(f"  Round-trip: {rt_comments}")

    # 2. Validate net comments preserved
    for net in orig_data.get('nets', []):
        name = net['name']
        orig_comments = net.get('user_comments', {})

        rt_net = next((n for n in rt_data.get('nets', []) if n['name'] == name), None)

        if rt_net and orig_comments:
            rt_comments = rt_net.get('user_comments', {})
            if orig_comments != rt_comments:
                errors.append(f"Net {name}: comments differ")

    # 3. Validate docstring preserved
    orig_docstring = orig_data.get('function_metadata', {}).get('docstring')
    rt_docstring = rt_data.get('function_metadata', {}).get('docstring')

    if orig_docstring != rt_docstring:
        errors.append("Function docstring differs")

    # 4. Validate structured annotations preserved (if present)
    orig_annotations = extract_structured_comments(original_py.read_text())
    rt_annotations = extract_structured_comments(roundtrip_py.read_text())

    if len(orig_annotations) != len(rt_annotations):
        warnings.append(f"Structured annotation count: {len(orig_annotations)} → {len(rt_annotations)}")

    # 5. Generate statistics
    stats = {
        'components_with_comments': sum(1 for c in orig_data['components'] if c.get('user_comments')),
        'nets_with_comments': sum(1 for n in orig_data.get('nets', []) if n.get('user_comments')),
        'total_comment_lines': count_comment_lines(orig_data),
        'structured_annotations': len(orig_annotations),
    }

    return ValidationResult(
        passed=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        stats=stats
    )
```

---

## Recommendations

### For Immediate Implementation (Weeks 1-2)

✅ **Implement JSON Metadata Strategy**
- Most robust solution
- Automatic for users (no training needed)
- Solves 90% of problems
- 2-week implementation

### For Future Enhancement (Week 3+)

✅ **Add Structured Annotations**
- Provides explicit control for power users
- Complements JSON metadata
- 1-week implementation

### Do NOT Implement

❌ **Diff-Based Strategy**
- Unreliable heuristics
- Complex implementation
- Poor results

❌ **Current System with Warnings**
- Doesn't solve core problem
- Users will ignore warnings
- Not scalable

---

## Success Metrics

After implementation, validate with these metrics:

1. **100% Comment Preservation**
   - All comments in original → all comments in round-trip
   - In correct locations (associated with correct code)

2. **Zero Context Loss**
   - Comments stay with their components
   - Inline comments remain inline
   - Section comments stay in sections

3. **Idempotent**
   - Round-trip → Round-trip → ... produces identical results
   - No comment duplication or drift

4. **Scalable**
   - Works for 1 component circuits
   - Works for 10,000 component circuits
   - Performance < 100ms for 1000 components

5. **User Satisfaction**
   - Survey: "Comments are preserved correctly" > 95% agree
   - No GitHub issues about lost comments

---

## Conclusion

**Current System:** Fundamentally broken at scale, will cause massive user frustration.

**Recommended Solution:** JSON Metadata + Structured Annotations (Hybrid approach).

**Timeline:** 3-4 weeks for complete implementation.

**Impact:** Transform from "unusable for large circuits" to "robust for millions of circuits."

---

**Next Steps:**

1. Review this analysis
2. Approve JSON metadata approach
3. Design enhanced JSON schema
4. Begin implementation (Week 1)

**Questions?**
- Should we support backwards compatibility with old JSON (no comment metadata)?
- What should happen when user deletes a component (delete comments too or preserve?)?
- Should we have a "review comments" UI before accepting round-trip changes?
