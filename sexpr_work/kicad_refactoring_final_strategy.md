# KiCad Module Refactoring - Final Strategy

## Goal
Enable clean, maintainable code for **adding and removing components and labels** from KiCad schematics.

## Critical Analysis of Each Library's Approach

### What Each Library Does Best

#### 1. **kicad-skip: Best for Manipulation**
```python
# Their approach - direct manipulation of parsed structure
schem = skip.Schematic('my.kicad_sch')
for component in schem.symbol:
    if component.reference.startswith('R'):
        component.delete()  # Clean removal
schem.save()
```
**Why it's good:** Objects know their parent, can delete themselves cleanly
**We should adopt:** Parent-aware objects, self-contained operations

#### 2. **kiutils: Best for Round-Trip Preservation**
```python
# Their approach - dataclasses that preserve formatting
@dataclass
class Symbol:
    lib_id: str
    at: Position
    _raw: dict = field(default_factory=dict)  # Preserves unknown fields
```
**Why it's good:** SCM-friendly, doesn't lose data on round-trip
**We should adopt:** Preserve unknown fields, maintain formatting

#### 3. **SKiDL: Best for Building Circuits**
```python
# Their approach - high-level circuit operations
circuit = Circuit()
r1 = Part('Device', 'R', value='10k')
circuit += r1  # Simple addition
```
**Why it's good:** Intuitive API for circuit construction
**We should adopt:** Operator overloading for natural syntax

#### 4. **Our Rust Code: Best for Data Integrity**
```rust
// Coordinate rounding prevents issues
fn round_coord(value: f64) -> f64 {
    (value * 10000.0).round() / 10000.0
}
```
**Why it's good:** Prevents floating-point formatting issues
**We should adopt:** Coordinate rounding, UUID generation

## The Strategy We Should Actually Implement

### Core Architecture

```python
# src/circuit_synth/kicad/core/schematic.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import sexpdata
from sexpdata import Symbol
import uuid

class SchematicElement:
    """Base class for all schematic elements."""
    
    def __init__(self, parent: Optional['Schematic'] = None):
        self.parent = parent
        self.uuid = str(uuid.uuid4())
        self._raw = {}  # Preserve unknown fields for round-trip
    
    def delete(self):
        """Remove this element from its parent."""
        if self.parent:
            self.parent.remove_element(self)
    
    def to_sexpr(self) -> list:
        """Convert to S-expression format."""
        raise NotImplementedError

@dataclass
class Component(SchematicElement):
    """A component in the schematic."""
    
    reference: str
    lib_id: str
    value: str = ""
    position: tuple[float, float] = (0, 0)
    rotation: float = 0
    footprint: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()
        # Round coordinates on init
        self.position = (round_coord(self.position[0]), 
                        round_coord(self.position[1]))
        self.rotation = round_coord(self.rotation)
    
    def move_to(self, x: float, y: float):
        """Move component to new position."""
        self.position = (round_coord(x), round_coord(y))
        if self.parent:
            self.parent.mark_dirty()
    
    def to_sexpr(self) -> list:
        """Generate S-expression for this component."""
        x, y = self.position
        
        expr = [
            Symbol('symbol'),
            [Symbol('lib_id'), self.lib_id],
            [Symbol('at'), x, y, self.rotation],
            [Symbol('unit'), 1],
            [Symbol('uuid'), self.uuid],
        ]
        
        # Add properties
        expr.extend([
            self._make_property('Reference', self.reference, x, y - 2.54),
            self._make_property('Value', self.value, x, y + 2.54),
        ])
        
        if self.footprint:
            expr.append(self._make_property('Footprint', self.footprint, x, y + 5.08))
        
        # Add preserved raw fields
        for key, value in self._raw.items():
            if key not in ['symbol', 'lib_id', 'at', 'unit', 'uuid', 'property']:
                expr.append(value)
        
        return expr
    
    def _make_property(self, name: str, value: str, x: float, y: float) -> list:
        """Create a property S-expression."""
        return [
            Symbol('property'), name, value,
            [Symbol('at'), round_coord(x), round_coord(y), 0],
            [Symbol('effects'), 
             [Symbol('font'), [Symbol('size'), 1.27, 1.27]]]
        ]

@dataclass
class Label(SchematicElement):
    """A label in the schematic."""
    
    text: str
    position: tuple[float, float] = (0, 0)
    orientation: int = 0  # 0, 90, 180, 270
    label_type: str = 'local'  # local, global, hierarchical
    
    def to_sexpr(self) -> list:
        """Generate S-expression for this label."""
        x, y = round_coord(self.position[0]), round_coord(self.position[1])
        
        tag = {
            'local': 'label',
            'global': 'global_label',
            'hierarchical': 'hierarchical_label'
        }[self.label_type]
        
        return [
            Symbol(tag), self.text,
            [Symbol('at'), x, y, self.orientation],
            [Symbol('uuid'), self.uuid]
        ]

class Schematic:
    """Main schematic class with manipulation capabilities."""
    
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath
        self.components: List[Component] = []
        self.labels: List[Label] = []
        self.wires: List[Wire] = []
        self.metadata = {
            'version': 20250114,
            'generator': 'circuit_synth',
            'paper': 'A4',
            'uuid': str(uuid.uuid4())
        }
        self._dirty = False
        
        if filepath:
            self.load(filepath)
    
    def load(self, filepath: str):
        """Load schematic from KiCad file."""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Parse with sexpdata
        parsed = sexpdata.loads(content)
        self._parse_sexpr(parsed)
        self.filepath = filepath
        self._dirty = False
    
    def save(self, filepath: Optional[str] = None):
        """Save schematic to KiCad file."""
        filepath = filepath or self.filepath
        if not filepath:
            raise ValueError("No filepath specified")
        
        sexpr = self.to_sexpr()
        content = format_sexpr(sexpr)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        self._dirty = False
    
    def add_component(self, component: Component) -> Component:
        """Add a component to the schematic."""
        component.parent = self
        self.components.append(component)
        self._dirty = True
        return component
    
    def remove_component(self, component: Component):
        """Remove a component from the schematic."""
        if component in self.components:
            self.components.remove(component)
            component.parent = None
            self._dirty = True
    
    def find_component(self, reference: str) -> Optional[Component]:
        """Find component by reference designator."""
        for comp in self.components:
            if comp.reference == reference:
                return comp
        return None
    
    def add_label(self, label: Label) -> Label:
        """Add a label to the schematic."""
        label.parent = self
        self.labels.append(label)
        self._dirty = True
        return label
    
    def remove_label(self, label: Label):
        """Remove a label from the schematic."""
        if label in self.labels:
            self.labels.remove(label)
            label.parent = None
            self._dirty = True
    
    # Operator overloading for intuitive API (from SKiDL)
    def __iadd__(self, element):
        """Add element using += operator."""
        if isinstance(element, Component):
            self.add_component(element)
        elif isinstance(element, Label):
            self.add_label(element)
        else:
            raise TypeError(f"Cannot add {type(element)} to schematic")
        return self
    
    def __isub__(self, element):
        """Remove element using -= operator."""
        if isinstance(element, Component):
            self.remove_component(element)
        elif isinstance(element, Label):
            self.remove_label(element)
        else:
            raise TypeError(f"Cannot remove {type(element)} from schematic")
        return self
    
    def to_sexpr(self) -> list:
        """Generate complete schematic S-expression."""
        expr = [
            Symbol('kicad_sch'),
            [Symbol('version'), self.metadata['version']],
            [Symbol('generator'), self.metadata['generator']],
            [Symbol('uuid'), self.metadata['uuid']],
            [Symbol('paper'), self.metadata['paper']],
        ]
        
        # Add lib_symbols section
        expr.append([Symbol('lib_symbols')])  # TODO: Populate from components
        
        # Add all components
        for component in self.components:
            expr.append(component.to_sexpr())
        
        # Add all labels
        for label in self.labels:
            expr.append(label.to_sexpr())
        
        # Add all wires
        for wire in self.wires:
            expr.append(wire.to_sexpr())
        
        # Add required sections
        expr.extend([
            [Symbol('sheet_instances'), 
             [Symbol('path'), '/', [Symbol('page'), '1']]],
            [Symbol('embedded_fonts'), Symbol('no')]
        ])
        
        return expr
    
    def mark_dirty(self):
        """Mark schematic as having unsaved changes."""
        self._dirty = True
    
    @property
    def has_changes(self) -> bool:
        """Check if schematic has unsaved changes."""
        return self._dirty
```

### Formatting Layer (Separate Concern)

```python
# src/circuit_synth/kicad/formatting/formatter.py

# Simple rule-based formatter
FORMATTING_RULES = {
    # tag_name: (inline, max_elements, quote_indices)
    'at': (True, 4, []),
    'property': (True, 3, [1, 2]),
    'lib_id': (True, 2, [1]),
    'uuid': (True, 2, [1]),
    'effects': (False, None, []),
    'font': (True, 2, []),
}

def format_sexpr(expr, indent=0) -> str:
    """Format S-expression with KiCad-specific rules."""
    if not isinstance(expr, list):
        return _format_atom(expr)
    
    if not expr:
        return "()"
    
    # Get formatting rules for this expression
    tag = str(expr[0]) if expr else None
    inline, max_elem, quote_idx = FORMATTING_RULES.get(tag, (False, None, []))
    
    # Decide if inline based on rules and size
    if inline and (max_elem is None or len(expr) <= max_elem):
        return _format_inline(expr, quote_idx)
    else:
        return _format_multiline(expr, indent, quote_idx)

def _format_atom(atom):
    """Format a single atom."""
    if isinstance(atom, sexpdata.Symbol):
        return str(atom)
    elif isinstance(atom, str):
        # Quote strings with special characters
        if any(c in atom for c in ' \n\t"\\') or atom == '':
            return f'"{atom.replace(chr(92), chr(92)*2).replace('"', chr(92)+'"')}"'
        return atom
    elif isinstance(atom, float):
        return str(round_coord(atom))
    else:
        return str(atom)

def _format_inline(expr, quote_indices):
    """Format expression on single line."""
    parts = []
    for i, elem in enumerate(expr):
        if i in quote_indices and not isinstance(elem, list):
            parts.append(f'"{elem}"')
        else:
            parts.append(format_sexpr(elem))
    return f"({' '.join(parts)})"

def _format_multiline(expr, indent, quote_indices):
    """Format expression across multiple lines."""
    lines = []
    indent_str = "  " * indent
    next_indent = "  " * (indent + 1)
    
    # First element on same line as opening paren
    first = format_sexpr(expr[0]) if expr else ""
    lines.append(f"({first}")
    
    # Rest on new lines
    for i, elem in enumerate(expr[1:], 1):
        if i in quote_indices and not isinstance(elem, list):
            formatted = f'"{elem}"'
        else:
            formatted = format_sexpr(elem, indent + 1)
        lines.append(f"{next_indent}{formatted}")
    
    lines.append(f"{indent_str})")
    return "\n".join(lines)
```

### Utility Functions

```python
# src/circuit_synth/kicad/utils.py

def round_coord(value: float) -> float:
    """Round coordinate to prevent floating point issues."""
    return round(value * 10000) / 10000

def generate_uuid() -> str:
    """Generate KiCad-compatible UUID."""
    return str(uuid.uuid4())

def validate_rotation(angle: float) -> float:
    """Ensure rotation is 0, 90, 180, or 270."""
    normalized = angle % 360
    valid = [0, 90, 180, 270]
    closest = min(valid, key=lambda x: abs(x - normalized))
    return float(closest)
```

## Usage Examples

### Adding Components and Labels

```python
from circuit_synth.kicad import Schematic, Component, Label

# Create or load schematic
schem = Schematic('my_circuit.kicad_sch')

# Add a resistor
r1 = Component(
    reference='R1',
    lib_id='Device:R',
    value='10k',
    position=(100, 50)
)
schem += r1  # Natural addition

# Add a capacitor
c1 = schem.add_component(Component(
    reference='C1',
    lib_id='Device:C',
    value='100nF',
    position=(150, 50)
))

# Add a label
vcc_label = Label(
    text='VCC',
    position=(100, 40),
    label_type='global'
)
schem += vcc_label

# Save changes
schem.save()
```

### Removing Components

```python
# Load existing schematic
schem = Schematic('my_circuit.kicad_sch')

# Find and remove all resistors
for comp in list(schem.components):
    if comp.reference.startswith('R'):
        schem -= comp  # Natural removal

# Or use the delete method (kicad-skip style)
comp = schem.find_component('U1')
if comp:
    comp.delete()

# Save changes
schem.save()
```

### Modifying Components

```python
# Load and modify
schem = Schematic('my_circuit.kicad_sch')

# Move all capacitors down by 10mm
for comp in schem.components:
    if comp.reference.startswith('C'):
        x, y = comp.position
        comp.move_to(x, y + 10)

# Change all 10k resistors to 100k
for comp in schem.components:
    if comp.value == '10k' and comp.reference.startswith('R'):
        comp.value = '100k'

# Check if we have unsaved changes
if schem.has_changes:
    schem.save()
```

## Why This Approach Is Best

### 1. **Maintainability**
- **Clear separation**: Data model → S-expression → Formatting
- **Single responsibility**: Each class does one thing
- **No string manipulation**: Use sexpdata for parsing/generation
- **Type hints**: Full typing for IDE support

### 2. **Extensibility**
- **Easy to add elements**: Just subclass `SchematicElement`
- **Version handling**: Can add version-specific formatters
- **Plugin points**: Can override `to_sexpr()` for custom behavior
- **Preserve unknown fields**: Won't break on new KiCad versions

### 3. **Best Practices from Each Library**
- **kicad-skip**: Parent-aware objects, self-deletion
- **kiutils**: Dataclasses, round-trip preservation
- **SKiDL**: Operator overloading, intuitive API
- **Our Rust**: Coordinate rounding, UUID generation
- **sexpdata**: Proven S-expression handling

### 4. **Specific to Our Goal**
- **Adding components**: Simple with `+=` or `add_component()`
- **Removing components**: Simple with `-=` or `delete()`
- **Finding components**: Built-in search methods
- **Tracking changes**: Dirty flag for save management

## Implementation Priority

### Phase 1: Core (Week 1)
1. Implement `SchematicElement`, `Component`, `Label` classes
2. Basic `Schematic` class with add/remove
3. Simple S-expression generation
4. Basic formatting

### Phase 2: Loading (Week 2)
1. Parse existing KiCad files
2. Preserve unknown fields
3. Round-trip testing
4. Handle all component types

### Phase 3: Polish (Week 3)
1. Advanced search methods
2. Batch operations
3. Performance optimization
4. Comprehensive tests

## Migration Strategy

```python
# Old code
circuit_dict = {...}  # Complex nested dict
formatted = format_kicad_schematic(circuit_dict)

# New code (with adapter)
from circuit_synth.kicad.adapter import dict_to_schematic
schem = dict_to_schematic(circuit_dict)
formatted = schem.save()

# Future code (native)
schem = Schematic()
schem += Component(...)
schem.save('output.kicad_sch')
```

## Testing Strategy

```python
import unittest
from circuit_synth.kicad import Schematic, Component

class TestSchematicManipulation(unittest.TestCase):
    def test_add_component(self):
        schem = Schematic()
        comp = Component(reference='R1', lib_id='Device:R')
        schem += comp
        
        self.assertEqual(len(schem.components), 1)
        self.assertEqual(comp.parent, schem)
        self.assertTrue(schem.has_changes)
    
    def test_remove_component(self):
        schem = Schematic()
        comp = Component(reference='R1', lib_id='Device:R')
        schem += comp
        schem -= comp
        
        self.assertEqual(len(schem.components), 0)
        self.assertIsNone(comp.parent)
    
    def test_round_trip(self):
        # Load, modify, save, reload
        schem = Schematic('test.kicad_sch')
        original_count = len(schem.components)
        
        schem += Component(reference='R99', lib_id='Device:R')
        schem.save('test_out.kicad_sch')
        
        schem2 = Schematic('test_out.kicad_sch')
        self.assertEqual(len(schem2.components), original_count + 1)
```

## Conclusion

This approach combines the best ideas from all libraries while staying pragmatic:
- **Simple enough** to implement in 2-3 weeks
- **Clean enough** for long-term maintenance
- **Flexible enough** for future KiCad versions
- **Intuitive enough** for users to enjoy using

The key insight: Don't overthink it. Use proven patterns, keep layers separate, and make the API a joy to use.