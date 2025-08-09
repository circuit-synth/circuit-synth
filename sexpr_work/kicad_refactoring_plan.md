# KiCad Module Refactoring Plan

## Executive Summary

The current KiCad module in circuit-synth suffers from excessive string manipulation, mixed abstractions, and poor separation of concerns. This document outlines a comprehensive refactoring strategy to transform the chaotic string-parsing heavy implementation into a clean, maintainable architecture using modern design patterns.

## Critical Context: Circuit-Synth Workflow

### The Actual Data Flow
```
Python @circuit code → Circuit-Synth JSON → KiCad Schematic
KiCad Schematic → Circuit-Synth JSON → Python @circuit code
```

### Key Points:
1. **Users write Python @circuit functions** - They don't manipulate schematics directly
2. **JSON is the canonical format** - All conversions go through JSON
3. **KiCad is just a target format** - We generate KiCad from JSON, not from Python objects
4. **Round-trip requirement** - Must preserve circuit information through KiCad and back

### What This Means for Refactoring:
- **No user-facing schematic manipulation API needed** - Users work with @circuit functions
- **Focus on JSON ↔ KiCad conversion** - This is where the string chaos lives
- **Adding/removing components happens in JSON** - Not in Python user code
- **The refactoring is internal** - Won't change how users write circuits

## Research: How Other Libraries Handle KiCad S-Expressions

### Libraries Analyzed

#### 1. SKiDL
- **Approach**: Direct string concatenation and template-based generation
- **File Format**: Generates older KiCad format (EESchema Version 4)
- **Key Insights**:
  - Uses simple string templates for components: `"$Comp\nL {}:{} {}\n..."`
  - No S-expression library - pure string manipulation
  - Transformation matrices for component placement
  - Separates concerns between placement, routing, and generation
  - Handles hierarchical sheets with recursive generation

#### 2. kicad-skip (psychogenic)
- **Approach**: Object-oriented wrapper around S-expressions
- **Key Features**:
  - Transforms S-expressions into navigable Python objects
  - Named attributes with TAB-completion
  - Search/filter methods: `reference_matches()`, `value_startswith()`
  - Positional search: `within_circle()`, `within_rectangle()`
- **Design Pattern**: Proxy/Wrapper pattern for intuitive access
- **Best Practice**: Makes complex structures explorable in REPL

#### 3. kiutils
- **Approach**: Dataclass-based representation
- **Key Insights**:
  - Uses Python dataclasses for type-safe file representation
  - "SCM-friendly" - preserves file layout during round-trip
  - Targets KiCad 6.0+ with modern format support
- **Design Pattern**: Data Transfer Object (DTO) pattern
- **Best Practice**: Type safety and immutability through dataclasses

#### 4. kicad-rw (PySpice)
- **Approach**: sexpdata library with future auto-learning plans
- **Current State**: Uses sexpdata for basic parsing
- **Future Vision**: Auto-generate OO API from reference files using Jinja templates
- **Key Insight**: Acknowledges lack of DTD/schema for S-expressions

#### 5. kicad_parser (realthunder)
- **Approach**: Custom parser with SexpList for duplicate keys
- **Key Feature**: Handles multiple expressions with same key
- **Data Structure**: Special SexpList type for collections

#### 6. Our Rust Implementation (origin/RUST_CODE)
- **Approach**: Type-safe structs with lexpr library
- **Key Features**:
  - Uses `lexpr` crate for S-expression handling (Rust equivalent of sexpdata)
  - Strongly typed data structures (Component, Pin, Net, etc.)
  - Clean separation: Types → S-expression generation → String formatting
  - Coordinate rounding to prevent floating point issues
  - Macro-based S-expression building with `sexp!` macro
- **Design Pattern**: Type-safe data model with serialization layer
- **Best Practices**:
  - Round coordinates to 4 decimal places
  - Generate UUIDs for all elements
  - Separate configuration from data
  - Use builder pattern for complex S-expressions

### Key Findings

#### What Works Well:
1. **sexpdata library** (used by kicad-rw and circuit-synth) - reliable S-expression parsing
2. **Dataclasses** (kiutils) - clean, type-safe representation
3. **Object wrappers** (kicad-skip) - intuitive API for users
4. **Separation of concerns** (SKiDL) - placement, routing, generation as separate phases

#### Common Pain Points:
1. **No formal schema** - KiCad lacks DTD/XSD equivalent for S-expressions
2. **Version differences** - Each KiCad version has subtle format changes
3. **Context-dependent formatting** - Quoting rules vary by context
4. **Round-trip preservation** - Maintaining file layout for SCM

#### Best Practices Identified:
1. **Layer the architecture**: Low-level parser → AST → High-level API
2. **Use existing parsers**: Don't reinvent S-expression parsing
3. **Type safety**: Leverage Python's type system (dataclasses, typing)
4. **Preserve formatting**: Keep SCM-friendly output
5. **Version abstraction**: Handle version differences in strategy layer

## Current State Analysis

### Key Problems Identified

#### 1. Heavy String Manipulation & Context Tracking
- The `s_expression.py` file contains a 700+ line `_format_sexp` method
- Uses 14 boolean parameters to track formatting context:
  - `in_number`, `in_project`, `in_instances`, `in_page`
  - `in_property_value`, `in_property_name`, `in_generator`
  - `in_symbol`, `in_lib_symbols`, `in_name`, `in_text`, `in_reference`
- Deeply nested conditional logic for quoting rules
- Error-prone and difficult to maintain

#### 2. Mixed Abstractions
- Using both `sexpdata` library AND custom string formatting simultaneously
- Multiple formatter implementations:
  - `KiCadFormatterNew` in `kicad_formatter.py`
  - `SExpressionParser._format_sexp` in `s_expression.py`
- Inconsistent quoting rules scattered throughout codebase
- No clear boundary between parsing and generation

#### 3. Duplicated Logic
- Symbol caching implemented in multiple places:
  - `circuit_synth.core.component.SymbolLibCache`
  - `circuit_synth.kicad.kicad_symbol_cache.SymbolLibCache`
- Reference management split across multiple files:
  - `integrated_reference_manager.py`
  - Various inline reference handling
- Placement logic duplicated between:
  - `collision_manager.py`
  - `connection_aware_collision_manager.py`
  - `connection_aware_collision_manager_v2.py`

#### 4. Poor Separation of Concerns
- `schematic_writer.py` (2000+ lines) mixes:
  - S-expression generation
  - Component placement logic
  - KiCad API calls
  - String formatting
  - UUID management
- No clear data model - everything operates on raw dictionaries and lists
- Business logic intertwined with formatting concerns

#### 5. Maintenance Challenges
- Adding new KiCad format features requires changes in multiple locations
- Difficult to test individual components
- No clear extension points for new functionality
- Version-specific code (kicad5, kicad6, kicad7, kicad8) duplicated

## Revised Proposed Architecture (Based on Research)

### Learning from Other Libraries

Based on our research, we should adopt the following proven approaches:

1. **Keep sexpdata** - It's proven and used by multiple libraries
2. **Add dataclass layer** (like kiutils) - For type safety and clean APIs
3. **Create intuitive wrappers** (like kicad-skip) - For user-friendly access
4. **Separate generation phases** (like SKiDL) - Placement → Routing → Formatting
5. **Version-specific strategies** - Handle KiCad version differences cleanly

### Revised Architecture Layers

```
┌─────────────────────────────────────┐
│         User API (Facade)           │  High-level operations
├─────────────────────────────────────┤
│     Dataclass Models (kiutils)      │  Type-safe representations
├─────────────────────────────────────┤
│    Object Wrappers (kicad-skip)     │  Intuitive navigation
├─────────────────────────────────────┤
│      AST (Simplified from plan)     │  Structured representation
├─────────────────────────────────────┤
│     sexpdata (Keep existing)        │  Core S-expression parsing
└─────────────────────────────────────┘
```

## Proposed Architecture

### Design Principles
1. **Separation of Concerns**: Each class has a single, well-defined responsibility
2. **Open/Closed Principle**: Open for extension, closed for modification
3. **Dependency Inversion**: Depend on abstractions, not concrete implementations
4. **Testability**: All components independently testable
5. **Explicit over Implicit**: Make formatting rules and transformations explicit

### Core Components

#### 1. S-Expression Abstract Syntax Tree (AST)

```python
# src/circuit_synth/kicad/core/ast.py
from dataclasses import dataclass
from typing import Any, List, Union
from abc import ABC, abstractmethod

class SExpr(ABC):
    """Base class for all S-expression nodes."""
    
    @abstractmethod
    def format(self, formatter: 'SExprFormatter') -> str:
        """Format this node using the provided formatter."""
        pass
    
    @abstractmethod
    def accept(self, visitor: 'SExprVisitor') -> Any:
        """Accept a visitor for tree traversal."""
        pass

@dataclass
class Symbol(SExpr):
    """Represents an unquoted symbol in S-expressions."""
    name: str
    
    def format(self, formatter):
        return self.name
    
    def accept(self, visitor):
        return visitor.visit_symbol(self)

@dataclass
class Quoted(SExpr):
    """Represents a quoted string value."""
    value: str
    
    def format(self, formatter):
        return formatter.quote_string(self.value)
    
    def accept(self, visitor):
        return visitor.visit_quoted(self)

@dataclass
class Number(SExpr):
    """Represents a numeric value."""
    value: Union[int, float]
    
    def format(self, formatter):
        if isinstance(self.value, float):
            return formatter.format_float(self.value)
        return str(self.value)
    
    def accept(self, visitor):
        return visitor.visit_number(self)

@dataclass
class SList(SExpr):
    """Represents an S-expression list."""
    elements: List[SExpr]
    tag: str = None  # First element if it's a symbol
    
    def __post_init__(self):
        if self.elements and isinstance(self.elements[0], Symbol):
            self.tag = self.elements[0].name
    
    def format(self, formatter):
        return formatter.format_list(self)
    
    def accept(self, visitor):
        return visitor.visit_list(self)
    
    def find(self, tag: str) -> Optional['SList']:
        """Find first child list with given tag."""
        for elem in self.elements:
            if isinstance(elem, SList) and elem.tag == tag:
                return elem
        return None
    
    def find_all(self, tag: str) -> List['SList']:
        """Find all child lists with given tag."""
        return [elem for elem in self.elements 
                if isinstance(elem, SList) and elem.tag == tag]
```

#### 2. Builder Pattern for KiCad Elements

```python
# src/circuit_synth/kicad/builders/base.py
class BuilderBase:
    """Base class for all KiCad element builders."""
    
    def __init__(self):
        self._reset()
    
    def _reset(self):
        raise NotImplementedError
    
    def build(self) -> SList:
        raise NotImplementedError

# src/circuit_synth/kicad/builders/component.py
class ComponentBuilder(BuilderBase):
    """Builder for KiCad component (symbol) elements."""
    
    def _reset(self):
        self._component = SList([Symbol("symbol")])
        self._properties = []
        self._instances = []
    
    def with_lib_id(self, lib_id: str) -> 'ComponentBuilder':
        self._component.elements.append(
            SList([Symbol("lib_id"), Quoted(lib_id)])
        )
        return self
    
    def with_position(self, x: float, y: float, rotation: int = 0) -> 'ComponentBuilder':
        self._component.elements.append(
            SList([Symbol("at"), Number(x), Number(y), Number(rotation)])
        )
        return self
    
    def with_reference(self, ref: str, x: float = 0, y: float = -5) -> 'ComponentBuilder':
        prop = PropertyBuilder() \
            .with_name("Reference") \
            .with_value(ref) \
            .with_position(x, y) \
            .build()
        self._properties.append(prop)
        return self
    
    def with_value(self, value: str, x: float = 0, y: float = 5) -> 'ComponentBuilder':
        prop = PropertyBuilder() \
            .with_name("Value") \
            .with_value(value) \
            .with_position(x, y) \
            .build()
        self._properties.append(prop)
        return self
    
    def with_footprint(self, footprint: str) -> 'ComponentBuilder':
        prop = PropertyBuilder() \
            .with_name("Footprint") \
            .with_value(footprint) \
            .with_hidden(True) \
            .build()
        self._properties.append(prop)
        return self
    
    def with_uuid(self, uuid: str) -> 'ComponentBuilder':
        self._component.elements.append(
            SList([Symbol("uuid"), Quoted(uuid)])
        )
        return self
    
    def add_instance(self, project: str, path: str, reference: str, unit: int = 1) -> 'ComponentBuilder':
        self._instances.append({
            'project': project,
            'path': path,
            'reference': reference,
            'unit': unit
        })
        return self
    
    def build(self) -> SList:
        # Add properties
        for prop in self._properties:
            self._component.elements.append(prop)
        
        # Add instances if present
        if self._instances:
            instances_list = SList([Symbol("instances")])
            for inst in self._instances:
                project_block = SList([
                    Symbol("project"), Quoted(inst['project']),
                    SList([
                        Symbol("path"), Quoted(inst['path']),
                        SList([Symbol("reference"), Quoted(inst['reference'])]),
                        SList([Symbol("unit"), Number(inst['unit'])])
                    ])
                ])
                instances_list.elements.append(project_block)
            self._component.elements.append(instances_list)
        
        result = self._component
        self._reset()
        return result

# src/circuit_synth/kicad/builders/property.py
class PropertyBuilder(BuilderBase):
    """Builder for component properties."""
    
    def _reset(self):
        self._property = SList([Symbol("property")])
        self._effects = None
    
    def with_name(self, name: str) -> 'PropertyBuilder':
        self._property.elements.append(Quoted(name))
        return self
    
    def with_value(self, value: str) -> 'PropertyBuilder':
        self._property.elements.append(Quoted(value))
        return self
    
    def with_position(self, x: float, y: float, angle: int = 0) -> 'PropertyBuilder':
        self._property.elements.append(
            SList([Symbol("at"), Number(x), Number(y), Number(angle)])
        )
        return self
    
    def with_font_size(self, size: float = 1.27) -> 'PropertyBuilder':
        if not self._effects:
            self._effects = SList([Symbol("effects")])
        font = SList([Symbol("font"), 
                      SList([Symbol("size"), Number(size), Number(size)])])
        self._effects.elements.append(font)
        return self
    
    def with_hidden(self, hidden: bool = True) -> 'PropertyBuilder':
        if hidden:
            if not self._effects:
                self._effects = SList([Symbol("effects")])
            self._effects.elements.append(
                SList([Symbol("hide"), Symbol("yes")])
            )
        return self
    
    def build(self) -> SList:
        if self._effects:
            self._property.elements.append(self._effects)
        result = self._property
        self._reset()
        return result
```

#### 3. Strategy Pattern for Formatting Rules

```python
# src/circuit_synth/kicad/formatting/strategies.py
from abc import ABC, abstractmethod
from typing import List, Optional

class FormattingStrategy(ABC):
    """Base class for formatting strategies."""
    
    @abstractmethod
    def should_inline(self, slist: SList) -> bool:
        """Determine if this list should be formatted inline."""
        pass
    
    @abstractmethod
    def should_quote(self, value: Any, context: 'FormattingContext') -> bool:
        """Determine if this value should be quoted."""
        pass

class KiCadFormattingStrategy(FormattingStrategy):
    """Standard KiCad formatting rules."""
    
    # Configuration for inline formatting
    INLINE_RULES = {
        'at': {'max_elements': 4, 'always_inline': True},
        'xy': {'max_elements': 3, 'always_inline': True},
        'size': {'max_elements': 3, 'always_inline': True},
        'property': {'max_elements': 3, 'inline_indices': [0, 1, 2]},
        'lib_id': {'max_elements': 2, 'always_inline': True},
        'uuid': {'max_elements': 2, 'always_inline': True},
    }
    
    # Configuration for quoting rules
    QUOTE_RULES = {
        'property': {1: True, 2: True},  # Quote name and value
        'number': {1: True},  # Quote pin numbers
        'name': {1: True},    # Quote pin names if numeric
        'project': {1: True}, # Quote project names
        'page': {1: True},    # Quote page numbers
        'generator': {1: True}, # Quote generator values
    }
    
    def should_inline(self, slist: SList) -> bool:
        if not slist.tag:
            return False
        
        rule = self.INLINE_RULES.get(slist.tag)
        if not rule:
            return False
        
        if rule.get('always_inline'):
            return len(slist.elements) <= rule.get('max_elements', 4)
        
        return False
    
    def should_quote(self, value: Any, context: 'FormattingContext') -> bool:
        # Check tag-specific rules
        if context.parent_tag in self.QUOTE_RULES:
            index_rules = self.QUOTE_RULES[context.parent_tag]
            if context.element_index in index_rules:
                return index_rules[context.element_index]
        
        # General string quoting rules
        if isinstance(value, str):
            # Empty strings must be quoted
            if not value:
                return True
            # Strings with spaces or special chars must be quoted
            if any(c in value for c in ' \n\t"\\'):
                return True
            # Library IDs (contain ':') don't need quotes
            if ':' in value and ' ' not in value:
                return False
        
        return False

class PropertyFormattingStrategy(FormattingStrategy):
    """Special formatting for property elements."""
    
    def should_inline(self, slist: SList) -> bool:
        # Properties inline their name and value, but not effects
        return slist.tag == "property" and len(slist.elements) <= 3
    
    def should_quote(self, value: Any, context: 'FormattingContext') -> bool:
        # Property names and values are always quoted
        if context.parent_tag == "property" and context.element_index in [1, 2]:
            return True
        return False
```

#### 4. Formatter with Clean Architecture

```python
# src/circuit_synth/kicad/formatting/formatter.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FormattingContext:
    """Context information for formatting decisions."""
    parent_tag: Optional[str] = None
    element_index: int = 0
    indent_level: int = 0
    in_instances: bool = False
    in_lib_symbols: bool = False

class SExprFormatter:
    """Main formatter for S-expressions."""
    
    def __init__(self, strategy: FormattingStrategy = None, indent: str = "  "):
        self.strategy = strategy or KiCadFormattingStrategy()
        self.indent = indent
    
    def format(self, sexpr: SExpr, context: FormattingContext = None) -> str:
        """Format an S-expression tree to string."""
        if context is None:
            context = FormattingContext()
        
        if isinstance(sexpr, Symbol):
            return sexpr.name
        elif isinstance(sexpr, Quoted):
            return self.quote_string(sexpr.value)
        elif isinstance(sexpr, Number):
            return self.format_number(sexpr.value)
        elif isinstance(sexpr, SList):
            return self.format_list(sexpr, context)
        else:
            return str(sexpr)
    
    def quote_string(self, value: str) -> str:
        """Quote and escape a string value."""
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'
    
    def format_number(self, value: Union[int, float]) -> str:
        """Format a numeric value."""
        if isinstance(value, float):
            # Remove trailing zeros and decimal point if not needed
            formatted = f"{value:.10f}".rstrip('0').rstrip('.')
            return formatted
        return str(value)
    
    def format_list(self, slist: SList, context: FormattingContext) -> str:
        """Format an S-expression list."""
        if not slist.elements:
            return "()"
        
        # Determine if this should be inline
        if self.strategy.should_inline(slist):
            return self._format_inline(slist, context)
        else:
            return self._format_multiline(slist, context)
    
    def _format_inline(self, slist: SList, context: FormattingContext) -> str:
        """Format a list on a single line."""
        parts = []
        for i, elem in enumerate(slist.elements):
            child_context = FormattingContext(
                parent_tag=slist.tag,
                element_index=i,
                indent_level=context.indent_level,
                in_instances=context.in_instances or slist.tag == "instances",
                in_lib_symbols=context.in_lib_symbols or slist.tag == "lib_symbols"
            )
            
            # Apply quoting rules based on context
            if isinstance(elem, str) and self.strategy.should_quote(elem, child_context):
                parts.append(self.quote_string(elem))
            else:
                parts.append(self.format(elem, child_context))
        
        return "(" + " ".join(parts) + ")"
    
    def _format_multiline(self, slist: SList, context: FormattingContext) -> str:
        """Format a list across multiple lines with indentation."""
        lines = ["("]
        indent_str = self.indent * (context.indent_level + 1)
        
        for i, elem in enumerate(slist.elements):
            child_context = FormattingContext(
                parent_tag=slist.tag,
                element_index=i,
                indent_level=context.indent_level + 1,
                in_instances=context.in_instances or slist.tag == "instances",
                in_lib_symbols=context.in_lib_symbols or slist.tag == "lib_symbols"
            )
            
            formatted = self.format(elem, child_context)
            if i == 0:
                # First element (usually tag) stays on opening paren line
                lines[0] += formatted
            else:
                lines.append(indent_str + formatted)
        
        lines.append(self.indent * context.indent_level + ")")
        return "\n".join(lines)
```

#### 5. Visitor Pattern for Tree Transformations

```python
# src/circuit_synth/kicad/visitors/base.py
from abc import ABC, abstractmethod

class SExprVisitor(ABC):
    """Base visitor for S-expression tree traversal."""
    
    @abstractmethod
    def visit_symbol(self, symbol: Symbol) -> Any:
        pass
    
    @abstractmethod
    def visit_quoted(self, quoted: Quoted) -> Any:
        pass
    
    @abstractmethod
    def visit_number(self, number: Number) -> Any:
        pass
    
    @abstractmethod
    def visit_list(self, slist: SList) -> Any:
        pass

# src/circuit_synth/kicad/visitors/instance_updater.py
class InstanceUpdater(SExprVisitor):
    """Updates component instances in the schematic."""
    
    def __init__(self, instances_map: Dict[str, List[InstanceInfo]]):
        self.instances_map = instances_map
    
    def visit_symbol(self, symbol: Symbol) -> Symbol:
        return symbol
    
    def visit_quoted(self, quoted: Quoted) -> Quoted:
        return quoted
    
    def visit_number(self, number: Number) -> Number:
        return number
    
    def visit_list(self, slist: SList) -> SList:
        # Process symbol elements
        if slist.tag == "symbol":
            uuid_elem = slist.find("uuid")
            if uuid_elem and len(uuid_elem.elements) > 1:
                uuid = str(uuid_elem.elements[1])
                if uuid in self.instances_map:
                    # Remove old instances if present
                    slist.elements = [e for e in slist.elements 
                                    if not (isinstance(e, SList) and e.tag == "instances")]
                    # Add new instances
                    slist.elements.append(self._build_instances(self.instances_map[uuid]))
        
        # Recursively process children
        new_elements = []
        for elem in slist.elements:
            if isinstance(elem, SExpr):
                new_elements.append(elem.accept(self))
            else:
                new_elements.append(elem)
        slist.elements = new_elements
        
        return slist
    
    def _build_instances(self, instances: List[InstanceInfo]) -> SList:
        """Build instances S-expression from instance info."""
        builder = InstancesBuilder()
        for inst in instances:
            builder.add_instance(
                project=inst.project,
                path=inst.path,
                reference=inst.reference,
                unit=inst.unit
            )
        return builder.build()

# src/circuit_synth/kicad/visitors/reference_validator.py
class ReferenceValidator(SExprVisitor):
    """Validates and fixes component references."""
    
    def __init__(self):
        self.references_seen = set()
        self.errors = []
    
    def visit_list(self, slist: SList) -> SList:
        if slist.tag == "property":
            # Check for Reference property
            if len(slist.elements) > 2 and str(slist.elements[1]) == "Reference":
                ref = str(slist.elements[2])
                if ref in self.references_seen:
                    self.errors.append(f"Duplicate reference: {ref}")
                    # Auto-fix by appending number
                    counter = 1
                    while f"{ref}_{counter}" in self.references_seen:
                        counter += 1
                    new_ref = f"{ref}_{counter}"
                    slist.elements[2] = Quoted(new_ref)
                    self.references_seen.add(new_ref)
                else:
                    self.references_seen.add(ref)
        
        # Recursively process children
        for elem in slist.elements:
            if isinstance(elem, SExpr):
                elem.accept(self)
        
        return slist
```

#### 6. High-Level Facade

```python
# src/circuit_synth/kicad/facade.py
from typing import Dict, List, Optional

class KiCadSchematicGenerator:
    """High-level facade for KiCad schematic generation."""
    
    def __init__(self, 
                 formatter: SExprFormatter = None,
                 strategy: FormattingStrategy = None):
        self.formatter = formatter or SExprFormatter(strategy)
        self.component_builder = ComponentBuilder()
        self.wire_builder = WireBuilder()
        self.sheet_builder = SheetBuilder()
    
    def generate_schematic(self, circuit: Circuit) -> str:
        """Generate complete KiCad schematic from circuit."""
        # Build AST
        ast = self._build_ast(circuit)
        
        # Apply transformations
        ast = self._apply_transformations(ast, circuit)
        
        # Validate
        ast = self._validate(ast)
        
        # Format to string
        return self.formatter.format(ast)
    
    def _build_ast(self, circuit: Circuit) -> SList:
        """Build S-expression AST from circuit."""
        schematic = SchematicBuilder() \
            .with_version(20250114) \
            .with_generator("circuit_synth") \
            .with_paper_size("A4") \
            .with_title(circuit.name)
        
        # Add components
        for component in circuit.components:
            comp_ast = self._build_component(component)
            schematic.add_component(comp_ast)
        
        # Add wires
        for net in circuit.nets:
            for wire in self._nets_to_wires(net):
                schematic.add_wire(wire)
        
        # Add sheets for subcircuits
        for subcircuit in circuit.subcircuits:
            sheet_ast = self._build_sheet(subcircuit)
            schematic.add_sheet(sheet_ast)
        
        return schematic.build()
    
    def _build_component(self, component: Component) -> SList:
        """Build component AST."""
        return self.component_builder \
            .with_lib_id(component.lib_id) \
            .with_position(component.x, component.y, component.rotation) \
            .with_reference(component.ref) \
            .with_value(component.value) \
            .with_footprint(component.footprint) \
            .with_uuid(component.uuid) \
            .build()
    
    def _apply_transformations(self, ast: SList, circuit: Circuit) -> SList:
        """Apply necessary transformations to AST."""
        # Update instances
        instance_updater = InstanceUpdater(self._build_instances_map(circuit))
        ast = ast.accept(instance_updater)
        
        # Fix references
        ref_validator = ReferenceValidator()
        ast = ast.accept(ref_validator)
        
        return ast
    
    def _validate(self, ast: SList) -> SList:
        """Validate the AST."""
        validator = SchematicValidator()
        errors = validator.validate(ast)
        if errors:
            raise ValueError(f"Schematic validation failed: {errors}")
        return ast
```

#### 7. Configuration System

```yaml
# src/circuit_synth/kicad/config/formatting_rules.yaml
formatting_rules:
  version: "1.0"
  
  inline_elements:
    # Elements that should always be on one line
    always_inline:
      - tag: at
        max_elements: 4
      - tag: xy
        max_elements: 3
      - tag: size
        max_elements: 3
      - tag: uuid
        max_elements: 2
      - tag: lib_id
        max_elements: 2
    
    # Elements with partial inline formatting
    partial_inline:
      - tag: property
        inline_indices: [0, 1, 2]  # Tag, name, value inline
      - tag: symbol
        inline_indices: [0, 1]      # Tag and lib_id inline
  
  quoting_rules:
    # Context-based quoting
    by_context:
      - parent_tag: property
        indices:
          1: always  # Property name
          2: always  # Property value
      
      - parent_tag: number
        indices:
          1: always  # Pin numbers
      
      - parent_tag: project
        indices:
          1: always  # Project name
    
    # Pattern-based quoting
    by_pattern:
      - pattern: ".*:.*"  # Library IDs
        quote: never
      - pattern: "^[0-9]+$"  # Pure numbers in string context
        quote: context_dependent
      - pattern: ".*[ \t\n].*"  # Contains whitespace
        quote: always
  
  special_cases:
    # KiCad version-specific rules
    kicad_version_20250114:
      - use_instances_blocks: true
      - symbol_instances_deprecated: true
    
    kicad_version_20241001:
      - use_instances_blocks: false
      - symbol_instances_deprecated: false
```

```python
# src/circuit_synth/kicad/config/loader.py
import yaml
from pathlib import Path

class FormattingConfig:
    """Loads and manages formatting configuration."""
    
    def __init__(self, config_path: str = None):
        if config_path:
            self.config = self._load_config(config_path)
        else:
            self.config = self._load_default_config()
    
    def _load_config(self, path: str) -> dict:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_default_config(self) -> dict:
        default_path = Path(__file__).parent / 'formatting_rules.yaml'
        return self._load_config(default_path)
    
    def get_inline_rules(self) -> dict:
        return self.config['formatting_rules']['inline_elements']
    
    def get_quoting_rules(self) -> dict:
        return self.config['formatting_rules']['quoting_rules']
    
    def create_strategy(self) -> FormattingStrategy:
        """Create formatting strategy from configuration."""
        return ConfigurableFormattingStrategy(self)

class ConfigurableFormattingStrategy(FormattingStrategy):
    """Formatting strategy driven by configuration."""
    
    def __init__(self, config: FormattingConfig):
        self.config = config
        self.inline_rules = config.get_inline_rules()
        self.quoting_rules = config.get_quoting_rules()
    
    def should_inline(self, slist: SList) -> bool:
        # Check always_inline rules
        for rule in self.inline_rules.get('always_inline', []):
            if rule['tag'] == slist.tag:
                return len(slist.elements) <= rule.get('max_elements', 999)
        
        # Check partial_inline rules
        for rule in self.inline_rules.get('partial_inline', []):
            if rule['tag'] == slist.tag:
                return True  # Formatter will handle partial inlining
        
        return False
    
    def should_quote(self, value: Any, context: FormattingContext) -> bool:
        # Check context-based rules
        for rule in self.quoting_rules.get('by_context', []):
            if rule['parent_tag'] == context.parent_tag:
                if context.element_index in rule.get('indices', {}):
                    quote_rule = rule['indices'][context.element_index]
                    if quote_rule == 'always':
                        return True
                    elif quote_rule == 'never':
                        return False
        
        # Check pattern-based rules
        if isinstance(value, str):
            for rule in self.quoting_rules.get('by_pattern', []):
                import re
                if re.match(rule['pattern'], value):
                    if rule['quote'] == 'always':
                        return True
                    elif rule['quote'] == 'never':
                        return False
        
        return False
```

## Simplified Implementation Based on Research

### What We Should Actually Do

After analyzing existing libraries AND our own Rust implementation, here's a more pragmatic approach that respects the circuit-synth workflow:

#### Key Insights from Our Rust Code:
1. **Coordinate Rounding** - Essential to prevent `117.94999999999999` issues
2. **Type Safety Works** - Rust's strict types prevented many formatting bugs
3. **lexpr/sexpdata Are Good** - Both handle S-expressions well
4. **Separation of Concerns** - Types → Generation → Formatting is clean

### Refined Pragmatic Approach for JSON ↔ KiCad

Since the actual workflow is `Circuit JSON → KiCad → Circuit JSON`, we need to focus on:

#### 1. Clean JSON to KiCad Conversion
```python
# src/circuit_synth/kicad/json_to_kicad.py
from dataclasses import dataclass
from typing import Dict, Any, List
import json
import sexpdata

@dataclass
class KiCadConverter:
    """Converts Circuit-Synth JSON to KiCad format."""
    
    def json_to_kicad(self, json_path: str, output_path: str):
        """Main conversion entry point."""
        # Load circuit JSON
        with open(json_path) as f:
            circuit_data = json.load(f)
        
        # Convert to intermediate representation
        schematic = self._json_to_schematic(circuit_data)
        
        # Generate S-expression
        sexpr = schematic.to_sexpr()
        
        # Format and write
        formatted = format_kicad_sexpr(sexpr)
        with open(output_path, 'w') as f:
            f.write(formatted)
    
    def _json_to_schematic(self, data: Dict) -> 'SchematicData':
        """Convert JSON to internal schematic representation."""
        schematic = SchematicData()
        
        # Convert components
        for comp_data in data.get('components', []):
            component = Component(
                reference=comp_data['reference'],
                lib_id=comp_data['lib_id'],
                value=comp_data.get('value', ''),
                x=round_coord(comp_data['position']['x']),
                y=round_coord(comp_data['position']['y']),
                rotation=comp_data.get('rotation', 0)
            )
            schematic.components.append(component)
        
        # Convert nets
        for net_data in data.get('nets', []):
            schematic.nets.append(self._convert_net(net_data))
        
        return schematic
```

#### 2. Clean KiCad to JSON Conversion
```python
# src/circuit_synth/kicad/kicad_to_json.py

class KiCadParser:
    """Parses KiCad files back to Circuit-Synth JSON."""
    
    def kicad_to_json(self, kicad_path: str, output_path: str):
        """Parse KiCad file to Circuit-Synth JSON."""
        # Parse S-expression
        with open(kicad_path) as f:
            sexpr = sexpdata.loads(f.read())
        
        # Convert to intermediate representation
        schematic = self._sexpr_to_schematic(sexpr)
        
        # Convert to Circuit-Synth JSON format
        circuit_json = self._schematic_to_json(schematic)
        
        # Write JSON
        with open(output_path, 'w') as f:
            json.dump(circuit_json, f, indent=2)
    
    def _sexpr_to_schematic(self, sexpr: list) -> 'SchematicData':
        """Parse S-expression to internal representation."""
        schematic = SchematicData()
        
        for element in sexpr[1:]:  # Skip 'kicad_sch' tag
            if not isinstance(element, list):
                continue
            
            tag = str(element[0]) if element else None
            
            if tag == 'symbol':
                schematic.components.append(self._parse_component(element))
            elif tag == 'wire':
                schematic.wires.append(self._parse_wire(element))
            # ... handle other elements
        
        return schematic
    
    def _schematic_to_json(self, schematic: 'SchematicData') -> Dict:
        """Convert internal representation to Circuit-Synth JSON."""
        return {
            'components': [comp.to_dict() for comp in schematic.components],
            'nets': [net.to_dict() for net in schematic.nets],
            'metadata': schematic.metadata
        }
```

#### 3. Internal Representation (Not User-Facing)
```python
# src/circuit_synth/kicad/internal/schema.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class KiCadComponent:
    """Type-safe component representation."""
    lib_id: str
    reference: str
    value: str
    position: tuple[float, float]
    rotation: int = 0
    footprint: Optional[str] = None
    uuid: Optional[str] = None
    
    def to_sexpr(self) -> list:
        """Convert to S-expression format."""
        return build_component_sexpr(self)

@dataclass  
class KiCadSchematic:
    """Type-safe schematic representation."""
    version: int
    generator: str
    components: List[KiCadComponent]
    wires: List[KiCadWire]
    
    def to_sexpr(self) -> list:
        """Convert entire schematic to S-expression."""
        return build_schematic_sexpr(self)
```

#### 3. Create Formatting Registry (Not Complex Strategies)
```python
# Simple registry instead of complex strategy pattern
FORMATTING_RULES = {
    'property': {'inline': True, 'quote_indices': [1, 2]},
    'at': {'inline': True, 'quote_indices': []},
    'lib_id': {'inline': True, 'quote_indices': [1]},
    # ... etc
}

def format_sexpr(expr, tag=None):
    """Simple formatter using rule registry."""
    rules = FORMATTING_RULES.get(tag, {})
    # Apply rules
```

#### 4. Version-Specific Modules (Like SKiDL)
```python
# kicad/formats/v6.py
# kicad/formats/v7.py  
# kicad/formats/v8.py

# Each module knows its version's quirks
class KiCad8Formatter:
    def format_component(self, comp):
        # KiCad 8 specific formatting
        pass
```

#### 5. Essential Utilities (From Rust Experience)
```python
# kicad/utils.py
def round_coord(value: float) -> float:
    """Round to 4 decimal places to prevent floating point issues."""
    return round(value * 10000) / 10000

def generate_uuid() -> str:
    """Generate consistent UUIDs for elements."""
    return str(uuid.uuid4())

# kicad/sexpr_builder.py
class SExprBuilder:
    """Simple builder for S-expressions using sexpdata."""
    
    def __init__(self):
        self.expr = []
    
    def add(self, *elements):
        """Add elements to the expression."""
        for elem in elements:
            if isinstance(elem, float):
                self.expr.append(round_coord(elem))
            else:
                self.expr.append(elem)
        return self
    
    def add_property(self, name: str, value: str, x: float, y: float):
        """Add a property with standard formatting."""
        prop = [
            Symbol('property'), name, value,
            [Symbol('at'), round_coord(x), round_coord(y), 0],
            [Symbol('effects'), 
             [Symbol('font'), [Symbol('size'), 1.27, 1.27]]]
        ]
        self.expr.append(prop)
        return self
    
    def build(self) -> list:
        """Return the built expression."""
        return self.expr
```

### Example: Actual Circuit-Synth Workflow
```python
# What users write (unchanged):
from circuit_synth import Circuit, Component, Net

@circuit
def my_amplifier():
    """User writes circuits in Python - this doesn't change."""
    r1 = Component("Device:R", value="10k", ref="R")
    c1 = Component("Device:C", value="100nF", ref="C")
    
    net_vcc = Net("VCC")
    net_gnd = Net("GND")
    
    r1[1] += net_vcc
    r1[2] += net_gnd
    c1[1] += net_vcc
    c1[2] += net_gnd

# What happens internally (the part we're refactoring):

# 1. Circuit-Synth generates JSON (existing, unchanged)
circuit_json = {
    "components": [
        {"reference": "R1", "lib_id": "Device:R", "value": "10k", 
         "position": {"x": 100, "y": 50}},
        {"reference": "C1", "lib_id": "Device:C", "value": "100nF",
         "position": {"x": 150, "y": 50}}
    ],
    "nets": [
        {"name": "VCC", "pins": [{"ref": "R1", "pin": "1"}, {"ref": "C1", "pin": "1"}]},
        {"name": "GND", "pins": [{"ref": "R1", "pin": "2"}, {"ref": "C1", "pin": "2"}]}
    ]
}

# 2. Our refactored code converts JSON to KiCad (cleaner)
converter = KiCadConverter()
converter.json_to_kicad("circuit.json", "circuit.kicad_sch")

# 3. User edits in KiCad, we convert back (cleaner)
parser = KiCadParser()
parser.kicad_to_json("edited.kicad_sch", "updated_circuit.json")

# 4. Circuit-Synth regenerates Python (existing, unchanged)
```

## What Specifically Needs Refactoring

### Files to Refactor (Priority Order)

1. **src/circuit_synth/kicad/core/s_expression.py** (2048 lines)
   - The 700+ line `_format_sexp` method with 14 boolean parameters
   - **Refactor to:** Simple formatter with rule registry

2. **src/circuit_synth/kicad/sch_gen/schematic_writer.py** (2000+ lines)
   - Mixed responsibilities: placement, generation, formatting
   - **Refactor to:** Separate JSON→Internal and Internal→S-Expr converters

3. **src/circuit_synth/kicad/sch_gen/kicad_formatter.py** (500+ lines)
   - Complex strategy pattern with nested conditionals
   - **Refactor to:** Simple rule-based formatter

### The Core Refactoring Tasks

```python
# BEFORE: Chaos in s_expression.py
def _format_sexp(self, sexp, indent=0, parent_tag=None, 
                 in_number=False, in_project=False, 
                 in_instances=False, in_page=False,
                 in_property_value=False, in_property_name=False,
                 in_generator=False, in_symbol=False,
                 in_lib_symbols=False, in_name=False,
                 in_text=False, in_reference=False):
    # 700+ lines of nested conditionals...

# AFTER: Clean separation
class KiCadFormatter:
    def format(self, sexpr: list) -> str:
        """Format S-expression using rule registry."""
        rules = FORMATTING_RULES.get(self._get_tag(sexpr), {})
        return self._apply_rules(sexpr, rules)
```

### What Stays the Same

1. **User API** - @circuit functions don't change
2. **JSON Format** - Circuit-Synth JSON structure unchanged  
3. **sexpdata** - Keep using it for S-expression parsing
4. **File locations** - Same module structure

## Implementation Plan

### Phase 1: Core Refactoring (Week 1)
- [ ] Create AST node classes (`SExpr`, `Symbol`, `Quoted`, `Number`, `SList`)
- [ ] Implement basic visitor pattern
- [ ] Write comprehensive unit tests for AST operations
- [ ] Create basic formatter without strategies

### Phase 2: Builder Pattern Implementation (Week 2)
- [ ] Implement `ComponentBuilder`
- [ ] Implement `WireBuilder`
- [ ] Implement `SheetBuilder`
- [ ] Implement `SchematicBuilder`
- [ ] Create property and effects builders
- [ ] Write tests for all builders

### Phase 3: Formatting Strategy System (Week 3)
- [ ] Define `FormattingStrategy` interface
- [ ] Implement `KiCadFormattingStrategy`
- [ ] Create specialized strategies for different element types
- [ ] Implement configuration-driven strategy
- [ ] Write YAML configuration files
- [ ] Test formatting with various configurations

### Phase 4: Visitor Implementations (Week 4)
- [ ] Implement `InstanceUpdater` visitor
- [ ] Implement `ReferenceValidator` visitor
- [ ] Implement `NetConnector` visitor
- [ ] Implement `HierarchyResolver` visitor
- [ ] Create transformation pipeline
- [ ] Write integration tests

### Phase 5: Facade and Integration (Week 5)
- [ ] Implement `KiCadSchematicGenerator` facade
- [ ] Create adapters for existing circuit structures
- [ ] Implement backward compatibility layer
- [ ] Write migration scripts for existing code
- [ ] Create performance benchmarks

### Phase 6: Testing and Validation (Week 6)
- [ ] Comprehensive unit test coverage (>90%)
- [ ] Integration tests with real circuits
- [ ] Performance testing and optimization
- [ ] Validate output against KiCad
- [ ] Test with all KiCad versions (6, 7, 8)
- [ ] Document breaking changes

### Phase 7: Migration and Deployment (Week 7)
- [ ] Create migration guide
- [ ] Update all existing code to use new system
- [ ] Deprecate old formatting code
- [ ] Update documentation
- [ ] Create examples and tutorials
- [ ] Release new version

## Benefits of This Approach

### 1. Maintainability
- Clear separation of concerns
- Each component has a single responsibility
- Easy to understand and modify

### 2. Extensibility
- New KiCad versions can be supported by adding strategies
- New element types just need new builders
- Transformations can be added as visitors

### 3. Testability
- Each component can be tested independently
- Formatting rules are explicit and testable
- No hidden dependencies

### 4. Performance
- AST allows for efficient tree operations
- Visitors can traverse once for multiple transformations
- Formatting is a single pass operation

### 5. Configuration
- Formatting rules externalized to YAML
- Easy to adjust for different use cases
- Version-specific rules in configuration

### 6. Type Safety
- Strong typing with dataclasses
- Clear interfaces with ABC
- Reduced runtime errors

## Migration Strategy

### Step 1: Parallel Implementation
- Build new system alongside existing code
- No breaking changes initially
- Allow gradual migration

### Step 2: Adapter Layer
```python
class LegacyAdapter:
    """Adapter to use new system with old interface."""
    
    def __init__(self):
        self.generator = KiCadSchematicGenerator()
    
    def format_kicad_schematic(self, circuit_dict, **kwargs):
        """Old interface, new implementation."""
        circuit = self._convert_to_circuit(circuit_dict)
        return self.generator.generate_schematic(circuit)
```

### Step 3: Deprecation Warnings
```python
def old_format_function(*args, **kwargs):
    warnings.warn(
        "This function is deprecated. Use KiCadSchematicGenerator instead.",
        DeprecationWarning,
        stacklevel=2
    )
    adapter = LegacyAdapter()
    return adapter.format_kicad_schematic(*args, **kwargs)
```

### Step 4: Documentation Update
- Update all examples to use new API
- Create migration guide with before/after examples
- Document breaking changes

### Step 5: Remove Legacy Code
- After deprecation period (2-3 releases)
- Remove old formatting code
- Clean up codebase

## Risk Mitigation

### Risks and Mitigations

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Comprehensive test suite before changes
   - **Mitigation**: Parallel implementation with adapter layer

2. **Risk**: Performance regression
   - **Mitigation**: Benchmark current implementation
   - **Mitigation**: Profile new implementation
   - **Mitigation**: Optimize hot paths

3. **Risk**: KiCad format changes
   - **Mitigation**: Configuration-driven formatting
   - **Mitigation**: Version-specific strategies
   - **Mitigation**: Regular KiCad compatibility testing

4. **Risk**: User adoption resistance
   - **Mitigation**: Maintain backward compatibility
   - **Mitigation**: Clear migration guide
   - **Mitigation**: Demonstrate clear benefits

## Success Metrics

### Quantitative Metrics
- Code complexity reduction: Target 50% reduction in cyclomatic complexity
- Test coverage: Achieve >90% coverage
- Performance: Maintain or improve current performance
- Bug reduction: 75% fewer formatting-related bugs

### Qualitative Metrics
- Developer satisfaction: Easier to understand and modify
- Maintainability: New features implementable in <1 day
- Documentation: Clear, comprehensive, with examples
- Community feedback: Positive response to changes

## Comparison: Original Plan vs Research-Informed Approach

### Original Plan (Overengineered)
- Complex AST with visitor pattern
- Strategy pattern for formatting
- Builder pattern for every element  
- Configuration-driven with YAML
- **Pros**: Very flexible, academically clean
- **Cons**: Overengineered, long implementation time

### Research-Informed Approach (Pragmatic)
- Keep sexpdata, wrap with dataclasses
- Simple formatting registry (dict-based)
- Version-specific modules
- Direct conversion methods
- **Pros**: Quick to implement, proven patterns, maintains compatibility
- **Cons**: Less flexible, some duplication

### Lessons from Our Rust Implementation

Our Rust code in `origin/RUST_CODE` branch showed us that:

1. **Type Safety Prevents Bugs** - Rust's strict typing caught many formatting issues at compile time
2. **Coordinate Rounding is Critical** - Must round to 4 decimal places to avoid `117.94999999999999` 
3. **lexpr ≈ sexpdata** - Both libraries handle S-expressions well, no need to change
4. **Simple Builder Pattern Works** - Not complex visitor pattern, just simple builders
5. **Separation Works** - Clean layers: Types → Generation → Formatting

The Rust implementation is actually simpler than our original plan and it works well. We should apply these lessons to the Python refactoring.

### Recommendation for Circuit-Synth Context

**Focus on JSON ↔ KiCad conversion**, not user-facing APIs, because:

1. **Users don't see this code** - They write @circuit functions, not schematic manipulation
2. **JSON is the interface** - All data flows through Circuit-Synth JSON format
3. **Internal refactoring only** - Won't break existing user code
4. **Simpler scope** - Just clean up the conversion layer, not redesign the API

**The Actual Refactoring Needed:**

```
Current Mess:                     Clean Architecture:
                                 
700+ line _format_sexp     →     JSON → SchematicData → S-Expr → Formatted String
with 14 boolean params           (Clear transformation pipeline)

Mixed string manipulation  →     Dataclasses for type safety
and sexpdata usage               sexpdata for parsing/generation
                                 Separate formatting layer

Context tracking chaos     →     Simple rule registry
in_number, in_project...         FORMATTING_RULES dict
```

**Implementation Approach:**
1. **Keep sexpdata** - It works for parsing/generating S-expressions
2. **Add dataclass layer** - Type-safe intermediate representation
3. **Simple formatting rules** - Dict-based, not complex strategies
4. **Clear pipeline** - JSON → Internal → S-Expr → String
5. **Round-trip preservation** - Maintain unknown fields for compatibility

The key insight from researching other libraries and understanding circuit-synth workflow: **This is an internal conversion problem, not an API design problem**. We just need clean, maintainable code for JSON ↔ KiCad conversion.

## Conclusion

The proposed refactoring transforms the KiCad module from a string manipulation nightmare into a clean, maintainable architecture. By applying established design patterns and SOLID principles, we create a system that is:

- **Easier to understand**: Clear abstractions and separation of concerns
- **Easier to test**: Independent components with clear interfaces
- **Easier to extend**: New features through composition, not modification
- **Easier to maintain**: Bugs isolated to specific components

This investment in architecture will pay dividends in reduced maintenance burden, faster feature development, and improved reliability.