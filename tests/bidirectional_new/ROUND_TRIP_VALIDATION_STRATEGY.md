# Round-Trip Validation Strategy

**Goal:** Dead-lock robust validation for millions of users testing bidirectional sync.

## Core Principle: Canonical Representation Comparison

Instead of comparing files directly, convert both sides to a **canonical intermediate representation** and compare that.

```
Original Python → [Canonical Form] ← Round-trip Python
                         ↕
                  KiCad Schematic
```

---

## Strategy 1: JSON Canonical Representation

### Overview
Use the KiCad JSON export as the canonical intermediate format. Both Python→KiCad and KiCad→Python produce JSON, so we compare JSON structures.

### Flow
```
Step 1: Original Python → KiCad → JSON₁
Step 2: KiCad → Round-trip Python → KiCad → JSON₂
Step 3: Compare JSON₁ ≈ JSON₂
```

### JSON Comparison Function

```python
def compare_circuit_json(json1: dict, json2: dict, tolerance: dict) -> ValidationResult:
    """
    Compare two circuit JSON representations with configurable tolerance.

    Args:
        json1: First circuit JSON (parsed dict)
        json2: Second circuit JSON (parsed dict)
        tolerance: Dict defining what differences are acceptable
            {
                'position_mm': 0.01,      # Position drift < 0.01mm OK
                'ignore_uuids': True,     # UUIDs can differ
                'ignore_timestamps': True # Timestamps can differ
            }

    Returns:
        ValidationResult with detailed diff report
    """
    result = ValidationResult()

    # 1. Component count must match exactly
    if len(json1['components']) != len(json2['components']):
        result.add_error(f"Component count: {len(json1['components'])} vs {len(json2['components'])}")

    # 2. Component-by-component comparison (order-independent)
    components1 = {c['reference']: c for c in json1['components']}
    components2 = {c['reference']: c for c in json2['components']}

    for ref, c1 in components1.items():
        if ref not in components2:
            result.add_error(f"Component {ref} missing in round-trip")
            continue

        c2 = components2[ref]

        # Compare component properties
        if c1['value'] != c2['value']:
            result.add_error(f"{ref}: value {c1['value']} → {c2['value']}")

        if c1['footprint'] != c2['footprint']:
            result.add_error(f"{ref}: footprint changed")

        # Position comparison with tolerance
        pos_diff = position_distance(c1['position'], c2['position'])
        if pos_diff > tolerance['position_mm']:
            result.add_error(f"{ref}: position drift {pos_diff:.3f}mm")

    # 3. Net topology comparison (order-independent)
    nets1 = normalize_nets(json1.get('nets', []))
    nets2 = normalize_nets(json2.get('nets', []))

    if nets1 != nets2:
        result.add_error(f"Net topology differs: {net_diff(nets1, nets2)}")

    # 4. Hierarchical structure (if present)
    if 'hierarchy' in json1 or 'hierarchy' in json2:
        if not compare_hierarchy(json1.get('hierarchy'), json2.get('hierarchy')):
            result.add_error("Hierarchical structure differs")

    return result
```

### Normalization Functions

```python
def normalize_nets(nets: list) -> set:
    """
    Convert net list to normalized, order-independent representation.

    Example:
        Input:  [{'name': 'VCC', 'pins': ['R1.1', 'C1.1']},
                 {'name': 'GND', 'pins': ['R1.2', 'C1.2']}]
        Output: {('VCC', ('C1.1', 'R1.1')),  # sorted pins
                 ('GND', ('C1.2', 'R1.2'))}
    """
    normalized = set()
    for net in nets:
        # Sort pins to make order-independent
        pins = tuple(sorted(net['pins']))
        normalized.add((net['name'], pins))
    return normalized


def position_distance(pos1: dict, pos2: dict) -> float:
    """
    Calculate Euclidean distance between two positions.

    Example:
        pos1 = {'x': 30.48, 'y': 35.56, 'rotation': 0}
        pos2 = {'x': 30.49, 'y': 35.56, 'rotation': 0}
        Returns: 0.01 mm
    """
    import math
    dx = pos1['x'] - pos2['x']
    dy = pos1['y'] - pos2['y']
    return math.sqrt(dx*dx + dy*dy)
```

### Pros
- ✅ **Deterministic**: JSON comparison is exact
- ✅ **Fast**: No parsing overhead, direct dict comparison
- ✅ **Debuggable**: Can save JSON diffs to files
- ✅ **Order-independent**: Uses sets/dicts for topology
- ✅ **Tolerance-aware**: Position drift, UUID changes OK

### Cons
- ⚠️ **JSON must be comprehensive**: Missing data in JSON = false pass
- ⚠️ **Format dependency**: Tied to JSON schema

---

## Strategy 2: Python AST Canonical Representation

### Overview
Parse Python code to AST, extract circuit definition structure, convert to canonical dict, then compare.

### Flow
```
Step 1: Original Python → [AST] → Canonical Dict₁
Step 2: Round-trip Python → [AST] → Canonical Dict₂
Step 3: Compare Dict₁ ≈ Dict₂
```

### AST Extraction Function

```python
def extract_circuit_ast(python_file: Path) -> CanonicalCircuit:
    """
    Extract circuit definition from Python AST.

    Returns canonical representation independent of code style.
    """
    import ast

    source = python_file.read_text()
    tree = ast.parse(source)

    circuit = CanonicalCircuit()

    # Find the @circuit decorated function
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for @circuit decorator
            if has_circuit_decorator(node):
                circuit.name = node.name

                # Walk function body
                for stmt in node.body:
                    # Extract component creations
                    if is_component_creation(stmt):
                        comp = extract_component(stmt)
                        circuit.add_component(comp)

                    # Extract net definitions
                    if is_net_definition(stmt):
                        net = extract_net(stmt)
                        circuit.add_net(net)

                    # Extract subcircuit calls
                    if is_subcircuit_call(stmt):
                        sub = extract_subcircuit(stmt)
                        circuit.add_subcircuit(sub)

    return circuit


class CanonicalCircuit:
    """Order-independent canonical representation of a circuit."""

    def __init__(self):
        self.name: str = ""
        self.components: dict[str, CanonicalComponent] = {}  # ref → component
        self.nets: set[CanonicalNet] = set()
        self.subcircuits: dict[str, CanonicalSubcircuit] = {}

    def __eq__(self, other):
        """Structural equality comparison."""
        return (
            self.name == other.name and
            self.components == other.components and
            self.nets == other.nets and
            self.subcircuits == other.subcircuits
        )


@dataclass(frozen=True)
class CanonicalComponent:
    """Immutable component representation for comparison."""
    reference: str
    lib_id: str
    value: str
    footprint: str
    position: tuple[float, float, int]  # (x, y, rotation)

    def __eq__(self, other):
        """Compare with position tolerance."""
        if not isinstance(other, CanonicalComponent):
            return False

        return (
            self.reference == other.reference and
            self.lib_id == other.lib_id and
            self.value == other.value and
            self.footprint == other.footprint and
            position_close(self.position, other.position, tol=0.01)
        )


@dataclass(frozen=True)
class CanonicalNet:
    """Immutable net representation for set comparison."""
    name: str
    pins: frozenset[str]  # Frozen set = order-independent

    def __hash__(self):
        return hash((self.name, self.pins))
```

### Extraction Helpers

```python
def extract_component(stmt: ast.Assign) -> CanonicalComponent:
    """
    Extract component from AST statement.

    Example AST:
        r1 = Component(ref="R1", value="10k", footprint="R_0805", at=(30.48, 35.56))

    Returns:
        CanonicalComponent(reference="R1", value="10k", ...)
    """
    # Parse ast.Call node
    call = stmt.value
    kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}

    return CanonicalComponent(
        reference=kwargs.get('ref', ''),
        lib_id=kwargs.get('lib_id', ''),
        value=kwargs.get('value', ''),
        footprint=kwargs.get('footprint', ''),
        position=kwargs.get('at', (0, 0, 0))
    )


def extract_net(stmt: ast.Expr) -> CanonicalNet:
    """
    Extract net from AST statement.

    Example AST:
        Net("VCC").connect(r1[1], c1[1])

    Returns:
        CanonicalNet(name="VCC", pins=frozenset({"r1.1", "c1.1"}))
    """
    # Parse chained method calls
    net_name = get_net_name(stmt)
    pins = extract_connected_pins(stmt)

    return CanonicalNet(
        name=net_name,
        pins=frozenset(pins)
    )
```

### Pros
- ✅ **Format-independent**: Validates actual Python semantics
- ✅ **Ignores style**: Whitespace, comments, import order don't matter
- ✅ **Direct validation**: Compares what users wrote vs what was generated
- ✅ **No file I/O**: Works on in-memory Python code

### Cons
- ⚠️ **Complex parsing**: Need to handle all Python syntax variations
- ⚠️ **Fragile to code style**: Generated code might use different patterns
- ⚠️ **Doesn't validate KiCad**: Only validates Python ↔ Python

---

## **CRITICAL: Comment and Docstring Preservation**

### Why Comments Matter

User-written comments are **just as important as functionality**:

```python
# Original circuit written by user:
@circuit
def voltage_divider():
    """
    5V → 3.3V voltage divider for ESP32 input.

    Important: R1/R2 ratio must be exactly 1.515 for 3.3V output.
    DO NOT CHANGE without recalculating!
    """

    # Upper resistor - must be 1% tolerance or better
    r1 = Component(ref="R1", value="10k", footprint="R_0805")  # Changed from 12k on 2025-10-20

    # Lower resistor - matched pair with R1
    r2 = Component(ref="R2", value="6.8k", footprint="R_0805")

    # Connect: 5V → R1 → [output=3.3V] → R2 → GND
    Net("VIN").connect(r1[1])
    Net("VOUT").connect(r1[2], r2[1])  # This is the 3.3V tap point!
    Net("GND").connect(r2[2])
```

**If round-trip loses these comments, the user's design intent is destroyed.**

### Comment Types to Preserve

1. **Function docstrings** - Circuit purpose, design notes
2. **Inline comments** - Component selection rationale
3. **End-of-line comments** - Pin connection explanations
4. **Block comments** - Section separators, warnings
5. **TODOs/NOTEs** - Future work, design considerations

### The Problem with JSON-Only Validation

JSON validates **structure** but not **documentation**:

```python
# JSON sees:
{
    'components': [
        {'reference': 'R1', 'value': '10k'},
        {'reference': 'R2', 'value': '6.8k'}
    ],
    'nets': [...]
}

# JSON CANNOT see:
# - "DO NOT CHANGE without recalculating!"
# - "Changed from 12k on 2025-10-20"
# - "This is the 3.3V tap point!"
```

**JSON validation passes even if ALL comments are lost.** ❌

---

## Hybrid Strategy: Best of Both Worlds (UPDATED)

### Recommended Approach

**Three-phase validation:**
1. **JSON** for electrical correctness (REQUIRED)
2. **AST + Comments** for code preservation (REQUIRED)
3. **Code quality** checks (OPTIONAL)

```python
def validate_round_trip(original_py: Path, kicad_dir: Path, roundtrip_py: Path):
    """
    Three-phase validation:
    1. JSON validation (electrical correctness) - REQUIRED
    2. Comment preservation (documentation) - REQUIRED
    3. AST validation (code quality) - OPTIONAL
    """

    # Phase 1: JSON Validation (REQUIRED - electrical correctness)
    # ============================================================
    orig_json = load_json(kicad_dir / "circuit.json")
    rt_kicad_dir = generate_kicad(roundtrip_py)
    rt_json = load_json(rt_kicad_dir / "circuit.json")

    json_result = compare_circuit_json(orig_json, rt_json, tolerance={
        'position_mm': 0.01,
        'ignore_uuids': True,
        'ignore_timestamps': True
    })

    if not json_result.passed:
        raise ValidationError(f"JSON validation failed:\n{json_result.errors}")


    # Phase 2: Comment Preservation (REQUIRED - documentation)
    # =========================================================
    # This is CRITICAL for user experience

    comment_result = validate_comment_preservation(original_py, roundtrip_py)

    if not comment_result.passed:
        raise ValidationError(
            f"Comment preservation failed:\n{comment_result.report()}\n\n"
            f"CRITICAL: User comments and documentation must be preserved!"
        )


    # Phase 3: AST Validation (OPTIONAL - code quality)
    # ==================================================
    orig_ast = extract_circuit_ast(original_py)
    rt_ast = extract_circuit_ast(roundtrip_py)

    ast_result = compare_circuits_loose(orig_ast, rt_ast)

    if not ast_result.passed:
        logger.warning(f"AST differs (cosmetic): {ast_result.differences}")

    return ValidationResult(
        json_validation=json_result,
        comment_validation=comment_result,  # NEW: Required
        ast_validation=ast_result,
        passed=(json_result.passed and comment_result.passed)  # Both required
    )
```

---

## Comment Preservation Validation

### Strategy: Extract and Compare Comments with Context

```python
import ast
import tokenize
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Comment:
    """A comment with context."""
    text: str
    line_number: int
    context: str  # Nearby code for matching
    type: str     # 'docstring', 'inline', 'block', 'eol'


def extract_comments(python_file: Path) -> list[Comment]:
    """
    Extract all comments from Python file with context.

    Uses tokenize module to get ALL comments (AST misses many).
    """
    comments = []
    source = python_file.read_text()
    lines = source.split('\n')

    # 1. Extract docstrings via AST
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            docstring = ast.get_docstring(node)
            if docstring:
                comments.append(Comment(
                    text=docstring,
                    line_number=node.lineno,
                    context=get_context(lines, node.lineno),
                    type='docstring'
                ))

    # 2. Extract inline/block comments via tokenize
    with python_file.open('rb') as f:
        tokens = tokenize.tokenize(f.readline)

        for token in tokens:
            if token.type == tokenize.COMMENT:
                comment_text = token.string.lstrip('#').strip()
                line_num = token.start[0]

                # Determine comment type
                if lines[line_num - 1].strip().startswith('#'):
                    comment_type = 'block'
                else:
                    comment_type = 'eol'  # end-of-line

                comments.append(Comment(
                    text=comment_text,
                    line_number=line_num,
                    context=get_context(lines, line_num),
                    type=comment_type
                ))

    return comments


def get_context(lines: list[str], line_num: int, window=2) -> str:
    """
    Get code context around a comment.

    Used to match comments even if line numbers shift.
    """
    start = max(0, line_num - window - 1)
    end = min(len(lines), line_num + window)

    context_lines = lines[start:end]

    # Remove comment lines, keep only code
    code_lines = [line for line in context_lines
                  if not line.strip().startswith('#')]

    # Normalize whitespace
    code_lines = [line.strip() for line in code_lines if line.strip()]

    return ' '.join(code_lines)


def validate_comment_preservation(
    original_py: Path,
    roundtrip_py: Path
) -> ValidationResult:
    """
    Validate that comments are preserved through round-trip.

    CRITICAL for user experience - comments are design intent.
    """
    errors = []
    warnings = []

    orig_comments = extract_comments(original_py)
    rt_comments = extract_comments(roundtrip_py)

    # Build index: context → comments
    orig_by_context = {}
    for comment in orig_comments:
        key = comment.context
        if key not in orig_by_context:
            orig_by_context[key] = []
        orig_by_context[key].append(comment)

    rt_by_context = {}
    for comment in rt_comments:
        key = comment.context
        if key not in rt_by_context:
            rt_by_context[key] = []
        rt_by_context[key].append(comment)

    # Check: All original comments present in round-trip
    for context, orig_comments_list in orig_by_context.items():
        rt_comments_list = rt_by_context.get(context, [])

        for orig_comment in orig_comments_list:
            # Look for matching comment text
            found = False
            for rt_comment in rt_comments_list:
                # Fuzzy match: normalize whitespace
                orig_normalized = normalize_comment_text(orig_comment.text)
                rt_normalized = normalize_comment_text(rt_comment.text)

                if orig_normalized == rt_normalized:
                    found = True
                    break

            if not found:
                errors.append(
                    f"Comment lost near line {orig_comment.line_number}: "
                    f'"{orig_comment.text[:60]}..."'
                )

    # Check: No spurious comments added
    for context, rt_comments_list in rt_by_context.items():
        orig_comments_list = orig_by_context.get(context, [])

        if len(rt_comments_list) > len(orig_comments_list):
            extra_count = len(rt_comments_list) - len(orig_comments_list)
            warnings.append(
                f"{extra_count} extra comment(s) added near: {context[:40]}..."
            )

    # Statistics
    stats = {
        'original_comments': len(orig_comments),
        'roundtrip_comments': len(rt_comments),
        'docstrings': sum(1 for c in orig_comments if c.type == 'docstring'),
        'inline_comments': sum(1 for c in orig_comments if c.type in ('inline', 'block', 'eol')),
    }

    return ValidationResult(
        passed=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        stats=stats
    )


def normalize_comment_text(text: str) -> str:
    """Normalize comment text for comparison."""
    # Remove extra whitespace
    normalized = ' '.join(text.split())

    # Case-insensitive comparison
    normalized = normalized.lower()

    # Remove punctuation variations
    import string
    normalized = normalized.translate(str.maketrans('', '', string.punctuation))

    return normalized
```

---

## Example: Comment Preservation Test

```python
def test_comment_preservation_simple():
    """Test that inline comments are preserved."""

    # Original circuit with comments
    original = '''
@circuit
def my_circuit():
    """This is a voltage divider."""  # Function docstring

    # This is an important resistor
    r1 = Component(ref="R1", value="10k")  # Upper resistor

    # Lower resistor - must match R1!
    r2 = Component(ref="R2", value="10k")
    '''

    # After round-trip, all comments must be present
    result = validate_comment_preservation(
        Path("original.py"),
        Path("roundtrip.py")
    )

    assert result.passed, f"Comments lost:\n{result.report()}"
    assert result.stats['docstrings'] == 1
    assert result.stats['inline_comments'] == 3
```

---

## Critical Comment Scenarios

### Scenario 1: Block Comments

```python
# ============================================================
# POWER SUPPLY SECTION
# ============================================================
# 5V input from USB, regulated to 3.3V
# DO NOT use linear regulator - too much heat!
# Must use switching regulator (buck converter)
# ============================================================

power_circuit()
```

**Must preserve:** All 6 comment lines, in order

---

### Scenario 2: End-of-Line Comments

```python
Net("VCC").connect(r1[1], c1[1])  # Power input - bypass cap required!
Net("OUT").connect(r1[2], c2[1])  # 3.3V output - DO NOT exceed 100mA
Net("GND").connect(c1[2], c2[2])  # Common ground reference
```

**Must preserve:** All 3 EOL comments, associated with correct lines

---

### Scenario 3: Docstrings

```python
@circuit
def esp32_power_supply():
    """
    Power supply for ESP32-C6 module.

    Input: 5V from USB
    Output: 3.3V @ 500mA max

    Design notes:
    - Uses AP2112K-3.3 LDO regulator
    - C1 and C2 are ceramic 10uF X7R
    - Tested up to 85°C ambient

    Author: John Doe
    Date: 2025-10-26
    Revision: v1.2
    """
```

**Must preserve:** Entire docstring, including formatting and metadata

---

## Updated Success Metrics

- ✅ **Zero false positives**: Valid round-trips never fail
- ✅ **Zero false negatives**: Invalid round-trips always caught
- ✅ **100% comment preservation**: All user comments preserved
- ✅ **Fast**: < 100ms per validation
- ✅ **Debuggable**: Clear error messages showing exact differences
- ✅ **Scalable**: Works for 1 component or 10,000 components

---

## Final Validation Strategy

**BOTH are REQUIRED for valid round-trip:**

1. ✅ **JSON validation** → Electrical correctness
2. ✅ **Comment preservation** → Documentation correctness

**OPTIONAL but recommended:**

3. ⚠️ **AST validation** → Code quality

```python
# Final test:
def test_03_round_trip():
    """Round-trip with comprehensive validation."""

    # ... generate round-trip ...

    result = validate_round_trip(original_py, kicad_dir, roundtrip_py)

    # Both JSON and comments must pass
    assert result.json_validation.passed, "Circuit structure differs"
    assert result.comment_validation.passed, "Comments lost - USER INTENT LOST!"

    print(f"✅ Test PASSED: Circuit and documentation preserved")
```

---

## Robustness Guarantees

### 1. Order Independence
All comparisons use **sets, dicts, frozensets** - order doesn't matter:
```python
# These are equivalent:
nets1 = {Net("VCC", pins=["R1.1", "C1.1"]), Net("GND", pins=["R1.2"])}
nets2 = {Net("GND", pins=["R1.2"]), Net("VCC", pins=["C1.1", "R1.1"])}
assert normalize_nets(nets1) == normalize_nets(nets2)  # ✅ Pass
```

### 2. Tolerance for Floating Point
Position comparisons use **epsilon tolerance**:
```python
pos1 = (30.48, 35.56)
pos2 = (30.480001, 35.560001)  # Floating point rounding
assert position_close(pos1, pos2, tol=0.01)  # ✅ Pass
```

### 3. UUID/Timestamp Ignoring
Non-semantic data is **filtered out**:
```python
def filter_metadata(data: dict) -> dict:
    """Remove non-semantic fields before comparison."""
    ignored_keys = {'uuid', 'timestamp', 'generator', 'version'}
    return {k: v for k, v in data.items() if k not in ignored_keys}
```

### 4. Net Topology Normalization
Nets are compared by **connectivity graph**, not syntax:
```python
# These are topologically equivalent:
net1 = Net("VCC").connect(r1[1], c1[1], c2[1])
net2 = Net("VCC").connect(c1[1], r1[1]).connect(c2[1])

# Both normalize to:
normalized = CanonicalNet(name="VCC", pins=frozenset({"r1.1", "c1.1", "c2.1"}))
```

### 5. Hierarchical Path Normalization
Subcircuit paths are **canonicalized**:
```python
# Different import paths, same circuit:
path1 = "submodules.power_supply.PowerSupply"
path2 = "power_supply.PowerSupply"  # Relative import

# Normalize to:
canonical = "PowerSupply"  # Just the class name
```

---

## Implementation Plan

### Phase 1: JSON Validation (Week 1)
1. ✅ Create `compare_circuit_json()` function
2. ✅ Add normalization helpers (nets, positions)
3. ✅ Integrate into test 01, 02, 03
4. ✅ Validate with existing test fixtures

### Phase 2: AST Validation (Week 2)
1. ✅ Create `extract_circuit_ast()` parser
2. ✅ Build `CanonicalCircuit` classes
3. ✅ Add to tests as "code quality check"
4. ✅ Log warnings, don't fail tests initially

### Phase 3: Refinement (Week 3)
1. ✅ Add position tolerance configuration per test
2. ✅ Create detailed diff reporting
3. ✅ Add test for edge cases (empty circuits, large circuits)
4. ✅ Performance testing (millions of comparisons)

---

## Example Test Usage

```python
def test_03_round_trip():
    """Round-trip with comprehensive validation."""
    test_dir = Path(__file__).parent
    output_dir = clean_dir(test_dir / "generated_roundtrip")

    # Step 1: Generate original KiCad
    shutil.copy(test_dir / "01_python_ref.py", output_dir / "original.py")
    run_python(output_dir / "original.py")
    orig_kicad = output_dir / "blank"

    # Step 2: Import back to Python
    roundtrip_py = output_dir / "roundtrip.py"
    run_kicad_to_python(orig_kicad / "blank.kicad_pro", roundtrip_py)

    # Step 3: COMPREHENSIVE VALIDATION
    result = validate_round_trip(
        original_py=output_dir / "original.py",
        kicad_dir=orig_kicad,
        roundtrip_py=roundtrip_py
    )

    # Assert with detailed error message
    assert result.passed, f"Round-trip validation failed:\n{result.report()}"
    print(f"✅ Test 1.3 PASSED: {result.summary()}")
```

---

## Success Metrics

- ✅ **Zero false positives**: Valid round-trips never fail
- ✅ **Zero false negatives**: Invalid round-trips always caught
- ✅ **Fast**: < 100ms per validation
- ✅ **Debuggable**: Clear error messages showing exact differences
- ✅ **Scalable**: Works for 1 component or 10,000 components

---

## Robustness for Millions of Different Circuits

### The Challenge

This validation must work **perfectly** for:
- ✅ Empty circuits (0 components)
- ✅ Simple circuits (1-10 components)
- ✅ Medium circuits (10-100 components)
- ✅ Complex circuits (100-1000 components)
- ✅ Massive circuits (1000-10,000+ components)
- ✅ Flat hierarchies (single file)
- ✅ Deep hierarchies (10+ levels of subcircuits)
- ✅ Mixed component types (resistors, ICs, connectors, custom)
- ✅ Different naming conventions (R1, R_LOAD, resistor_pullup_1, r[5])
- ✅ Unusual net topologies (star, chain, mesh, disconnected)
- ✅ Edge cases (duplicate components, floating pins, NC pins)

### Critical Requirements

**1. Order Independence (Mandatory)**

Circuits can have components/nets in any order:
```python
# These MUST be considered identical:
Circuit A: [R1, R2, C1, C2]
Circuit B: [C1, R1, C2, R2]

# Implementation:
components = {c['reference']: c for c in json['components']}  # Dict, not list
nets = {frozenset(net['pins']): net for net in json['nets']}  # Set, not list
```

**Why:** Generated code may order components differently than original.

---

**2. Semantic Equivalence (Mandatory)**

Different representations of the same circuit:
```python
# These are semantically identical:
Net("VCC").connect(R1[1], C1[1], C2[1])  # Single statement

Net("VCC").connect(R1[1], C1[1])         # Multiple statements
Net("VCC").connect(C2[1])

# Both normalize to:
CanonicalNet(name="VCC", pins=frozenset({"R1.1", "C1.1", "C2.1"}))
```

**Why:** Round-trip may restructure net definitions while preserving connectivity.

---

**3. Floating Point Tolerance (Mandatory)**

Position comparisons must handle floating point precision:
```python
# These positions are "the same":
pos1 = (30.48000000, 35.56000000)
pos2 = (30.48000001, 35.56000002)  # Rounding error from KiCad export/import

# Implementation:
def position_close(p1, p2, tol=0.01):  # 0.01mm = 10 microns
    return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol
```

**Why:** KiCad uses millimeters with floating point, export/import introduces rounding.

---

**4. Metadata Filtering (Mandatory)**

Non-semantic data must be ignored:
```python
# These MUST be considered identical despite different UUIDs:
component1 = {
    'reference': 'R1',
    'value': '10k',
    'uuid': 'f7053937-8cf6-4ba7-b82c-8343885b8eb5',  # Different
    'timestamp': '2025-10-26T11:24:12'               # Different
}

component2 = {
    'reference': 'R1',
    'value': '10k',
    'uuid': 'a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d',  # Different
    'timestamp': '2025-10-26T15:42:33'               # Different
}

# Filter before comparison:
IGNORED_KEYS = {'uuid', 'timestamp', 'generator', 'version', 'sheet_instances'}
```

**Why:** UUIDs and timestamps are regenerated on each export.

---

**5. Reference Normalization (Critical)**

Component references might have different formats:
```python
# These should be matched if they refer to the same component:
"R1" == "R1"              # ✅ Exact match
"R_LOAD" == "R_LOAD"      # ✅ Exact match

# But also handle:
"R1" vs "r1"              # ⚠️ Case sensitivity - circuit dependent
"R[1]" vs "R1"            # ⚠️ Array notation - need to normalize
"U1:R1" vs "R1"           # ⚠️ Hierarchical path - need to extract

# Normalization strategy:
def normalize_reference(ref: str) -> str:
    """Normalize component reference for comparison."""
    # Keep case-sensitive by default (R1 != r1 in KiCad)
    # Extract hierarchical path if present
    if ':' in ref:
        return ref.split(':')[-1]  # "U1:R1" → "R1"
    return ref
```

**Why:** Round-trip through hierarchical designs may add/remove path prefixes.

---

**6. Net Name Canonicalization (Critical)**

Net names might vary while preserving connectivity:
```python
# These are the same net:
"Net-(R1-Pad1)"     # Auto-generated name
"VCC"               # User-assigned name

# Strategy: Compare by connectivity, not name
def nets_equivalent(net1, net2):
    """Two nets are equivalent if they connect the same pins."""
    return frozenset(net1['pins']) == frozenset(net2['pins'])

# Group by connectivity:
nets_by_pins = {}
for net in nets:
    pin_set = frozenset(net['pins'])
    nets_by_pins[pin_set] = net
```

**Why:** KiCad may auto-rename nets, but connectivity is preserved.

---

**7. Hierarchical Path Resolution (Complex Circuits)**

Subcircuit instances may have different instance names:
```python
# Original:
subcircuit("PowerSupply", instance="PS1")

# Round-trip might generate:
subcircuit("PowerSupply", instance="U1")

# Strategy: Match by subcircuit TYPE, not instance name
def normalize_hierarchy(hierarchy):
    """Convert hierarchy to type-based tree."""
    return {
        'type': hierarchy['type'],           # Must match
        'children': [normalize_hierarchy(c) for c in hierarchy.get('children', [])],
        # Ignore instance name
    }
```

**Why:** Instance names may be regenerated, but structure/type must match.

---

**8. Performance at Scale (10,000+ components)**

Validation must complete quickly even for massive circuits:

```python
# BAD: O(n²) comparison
for c1 in circuit1.components:
    for c2 in circuit2.components:  # n² iterations!
        if c1.reference == c2.reference:
            compare(c1, c2)

# GOOD: O(n) comparison using dicts
components1 = {c['reference']: c for c in circuit1['components']}
components2 = {c['reference']: c for c in circuit2['components']}

for ref, c1 in components1.items():  # n iterations
    c2 = components2.get(ref)        # O(1) lookup
    if c2:
        compare(c1, c2)
```

**Complexity targets:**
- Component comparison: O(n)
- Net comparison: O(n)
- Position comparison: O(n)
- Total: O(n) where n = number of components

---

**9. Edge Case Handling**

Must gracefully handle unusual circuits:

```python
def compare_circuit_json(json1, json2, tolerance):
    """Robust comparison handling edge cases."""

    # Edge case 1: Empty circuits
    if not json1.get('components') and not json2.get('components'):
        return ValidationResult(passed=True, message="Both circuits empty")

    # Edge case 2: Components with no nets (floating components)
    # This is valid - don't fail
    if not json1.get('nets'):
        json1['nets'] = []
    if not json2.get('nets'):
        json2['nets'] = []

    # Edge case 3: Missing optional fields
    for component in json1.get('components', []):
        component.setdefault('value', '')
        component.setdefault('footprint', '')
        component.setdefault('position', (0, 0, 0))

    # Edge case 4: NC (No Connect) pins
    # Filter out NC pins from net comparison
    def filter_nc_pins(nets):
        return [net for net in nets if net['name'] != 'NC']

    # Proceed with comparison...
```

---

**10. Deterministic Comparison Order**

Results must be identical across runs:

```python
# BAD: Dictionary iteration order (Python 3.6+) is insertion order
# But JSON parsing might have different order
components = circuit['components']

# GOOD: Sort before comparison to ensure deterministic order
components = sorted(circuit['components'], key=lambda c: c['reference'])
nets = sorted(circuit['nets'], key=lambda n: n['name'])

# Report differences in sorted order:
for ref in sorted(components1.keys()):
    # ...
```

**Why:** Test results must be reproducible for CI/CD.

---

## Validation Strategy Selection Matrix

| Circuit Type | Component Count | Hierarchy | Recommended Strategy | Validation Time |
|--------------|----------------|-----------|---------------------|-----------------|
| Empty | 0 | Flat | JSON only | <1ms |
| Simple | 1-10 | Flat | JSON + AST | <10ms |
| Medium | 10-100 | 1-2 levels | JSON only | <50ms |
| Complex | 100-1000 | 2-5 levels | JSON only | <200ms |
| Massive | 1000-10,000+ | 5-10 levels | JSON only (optimized) | <1000ms |

**JSON scales linearly. AST parsing becomes expensive for large circuits.**

---

## Implementation: Production-Ready Validation Function

```python
from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path


@dataclass
class ValidationResult:
    """Comprehensive validation result."""
    passed: bool
    errors: list[str]
    warnings: list[str]
    stats: dict

    def report(self) -> str:
        """Generate detailed report."""
        if self.passed:
            return f"✅ PASSED ({self.stats['components']} components, {self.stats['nets']} nets)"

        report = "❌ FAILED - Differences found:\n"
        for error in self.errors:
            report += f"  - {error}\n"

        if self.warnings:
            report += "\nWarnings:\n"
            for warning in self.warnings:
                report += f"  ⚠️  {warning}\n"

        return report


def validate_round_trip_json(
    original_json: dict,
    roundtrip_json: dict,
    tolerance: Optional[dict] = None
) -> ValidationResult:
    """
    Production-grade round-trip validation.

    Handles millions of different circuits robustly.
    """
    if tolerance is None:
        tolerance = {
            'position_mm': 0.01,
            'ignore_uuids': True,
            'ignore_timestamps': True,
        }

    errors = []
    warnings = []

    # Filter metadata
    orig = filter_metadata(original_json, tolerance)
    rt = filter_metadata(roundtrip_json, tolerance)

    # 1. Component count
    orig_comp_count = len(orig.get('components', []))
    rt_comp_count = len(rt.get('components', []))

    if orig_comp_count != rt_comp_count:
        errors.append(f"Component count: {orig_comp_count} → {rt_comp_count}")

    # 2. Component-by-component (O(n) using dict)
    orig_comps = {normalize_reference(c['reference']): c
                  for c in orig.get('components', [])}
    rt_comps = {normalize_reference(c['reference']): c
                for c in rt.get('components', [])}

    for ref in sorted(orig_comps.keys()):  # Deterministic order
        if ref not in rt_comps:
            errors.append(f"Component {ref} missing in round-trip")
            continue

        c1, c2 = orig_comps[ref], rt_comps[ref]

        # Value comparison
        if c1.get('value') != c2.get('value'):
            errors.append(f"{ref}: value '{c1.get('value')}' → '{c2.get('value')}'")

        # Footprint comparison
        if c1.get('footprint') != c2.get('footprint'):
            errors.append(f"{ref}: footprint changed")

        # Position comparison with tolerance
        if 'position' in c1 and 'position' in c2:
            if not position_close(c1['position'], c2['position'],
                                 tolerance['position_mm']):
                dist = position_distance(c1['position'], c2['position'])
                errors.append(f"{ref}: position drift {dist:.4f}mm")

    # Check for new components in round-trip
    for ref in sorted(rt_comps.keys()):
        if ref not in orig_comps:
            errors.append(f"Component {ref} added in round-trip (shouldn't happen)")

    # 3. Net topology (O(n) using sets)
    orig_nets = normalize_nets(orig.get('nets', []))
    rt_nets = normalize_nets(rt.get('nets', []))

    missing_nets = orig_nets - rt_nets
    extra_nets = rt_nets - orig_nets

    for net in missing_nets:
        errors.append(f"Net lost: {net[0]} connecting {sorted(net[1])}")

    for net in extra_nets:
        errors.append(f"Net added: {net[0]} connecting {sorted(net[1])}")

    # 4. Hierarchy comparison (if present)
    if 'hierarchy' in orig or 'hierarchy' in rt:
        if not compare_hierarchy_structures(
            orig.get('hierarchy'),
            rt.get('hierarchy')
        ):
            errors.append("Hierarchical structure differs")

    # Generate stats
    stats = {
        'components': orig_comp_count,
        'nets': len(orig.get('nets', [])),
        'hierarchy_levels': count_hierarchy_depth(orig.get('hierarchy')),
    }

    return ValidationResult(
        passed=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        stats=stats
    )


def normalize_reference(ref: str) -> str:
    """Normalize component reference."""
    # Extract from hierarchical path
    if ':' in ref:
        ref = ref.split(':')[-1]
    return ref


def normalize_nets(nets: list) -> set:
    """Convert nets to normalized set representation."""
    normalized = set()
    for net in nets:
        # Skip NC (no-connect) nets
        if net.get('name') == 'NC':
            continue

        pins = tuple(sorted(net.get('pins', [])))
        normalized.add((net['name'], pins))

    return normalized


def position_distance(p1: tuple, p2: tuple) -> float:
    """Euclidean distance between positions."""
    import math
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx*dx + dy*dy)


def position_close(p1: tuple, p2: tuple, tol: float) -> bool:
    """Check if positions are within tolerance."""
    return position_distance(p1, p2) < tol


def filter_metadata(data: dict, tolerance: dict) -> dict:
    """Remove non-semantic metadata before comparison."""
    import copy
    filtered = copy.deepcopy(data)

    ignored_keys = set()
    if tolerance.get('ignore_uuids'):
        ignored_keys.add('uuid')
    if tolerance.get('ignore_timestamps'):
        ignored_keys.update(['timestamp', 'date', 'updated_at'])

    def recursive_filter(obj):
        if isinstance(obj, dict):
            return {k: recursive_filter(v)
                   for k, v in obj.items()
                   if k not in ignored_keys}
        elif isinstance(obj, list):
            return [recursive_filter(item) for item in obj]
        else:
            return obj

    return recursive_filter(filtered)


def compare_hierarchy_structures(h1: Optional[dict], h2: Optional[dict]) -> bool:
    """Compare hierarchical structures by type, ignoring instance names."""
    if h1 is None and h2 is None:
        return True
    if h1 is None or h2 is None:
        return False

    # Compare type/class
    if h1.get('type') != h2.get('type'):
        return False

    # Compare children recursively
    children1 = h1.get('children', [])
    children2 = h2.get('children', [])

    if len(children1) != len(children2):
        return False

    # Sort children by type for deterministic comparison
    children1_sorted = sorted(children1, key=lambda c: c.get('type', ''))
    children2_sorted = sorted(children2, key=lambda c: c.get('type', ''))

    for c1, c2 in zip(children1_sorted, children2_sorted):
        if not compare_hierarchy_structures(c1, c2):
            return False

    return True


def count_hierarchy_depth(hierarchy: Optional[dict]) -> int:
    """Count maximum depth of hierarchy tree."""
    if not hierarchy:
        return 0

    children = hierarchy.get('children', [])
    if not children:
        return 1

    return 1 + max(count_hierarchy_depth(c) for c in children)
```

---

## Testing the Validator (Meta-Testing)

The validator itself must be tested against edge cases:

```python
def test_validator_robustness():
    """Test that validator handles edge cases correctly."""

    # Test 1: Empty circuits
    assert validate_round_trip_json({}, {}).passed

    # Test 2: Single component
    circuit = {
        'components': [{'reference': 'R1', 'value': '10k'}]
    }
    assert validate_round_trip_json(circuit, circuit).passed

    # Test 3: Different component order (must pass)
    circuit1 = {'components': [{'reference': 'R1'}, {'reference': 'R2'}]}
    circuit2 = {'components': [{'reference': 'R2'}, {'reference': 'R1'}]}
    assert validate_round_trip_json(circuit1, circuit2).passed

    # Test 4: Position tolerance
    circuit1 = {'components': [{'reference': 'R1', 'position': (30.48, 35.56)}]}
    circuit2 = {'components': [{'reference': 'R1', 'position': (30.480001, 35.560001)}]}
    assert validate_round_trip_json(circuit1, circuit2).passed

    # Test 5: UUID differences (must pass)
    circuit1 = {'components': [{'reference': 'R1', 'uuid': 'abc'}]}
    circuit2 = {'components': [{'reference': 'R1', 'uuid': 'xyz'}]}
    assert validate_round_trip_json(circuit1, circuit2).passed

    # Test 6: Value mismatch (must fail)
    circuit1 = {'components': [{'reference': 'R1', 'value': '10k'}]}
    circuit2 = {'components': [{'reference': 'R1', 'value': '20k'}]}
    assert not validate_round_trip_json(circuit1, circuit2).passed

    # Test 7: Net connectivity preserved
    circuit1 = {'nets': [{'name': 'VCC', 'pins': ['R1.1', 'C1.1']}]}
    circuit2 = {'nets': [{'name': 'VCC', 'pins': ['C1.1', 'R1.1']}]}  # Different order
    assert validate_round_trip_json(circuit1, circuit2).passed
```

---

**Recommendation:** Start with JSON validation (simpler, faster, sufficient), add AST validation later for code quality insights.
