# Hierarchical Generation Bug: Flattened Circuit Structure

## Problem Statement

The KiCad-to-Python hierarchical generation system currently **flattens the circuit hierarchy** instead of preserving the nested structure, resulting in incorrect Python code that violates proper hierarchical design principles.

## Current Incorrect Behavior

### Generated Main Circuit (Wrong)
```python
@circuit(name='main')
def main():
    # ❌ ALL nets declared at main level (flattened)
    gnd = Net('GND')
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    debug_en = Net('DEBUG_EN')       # Should be local to ESP32C6
    debug_io0 = Net('DEBUG_IO0')     # Should be local to ESP32C6
    debug_rx = Net('DEBUG_RX')       # Should be local to ESP32C6
    debug_tx = Net('DEBUG_TX')       # Should be local to ESP32C6
    led_control = Net('LED_CONTROL') # Should be local to ESP32C6
    usb_dm = Net('USB_DM')
    usb_dp = Net('USB_DP')

    # ❌ ALL circuits instantiated at same level (no hierarchy)
    Power_Supply_instance = Power_Supply(gnd, vbus, vcc_3v3)
    ESP32_C6_MCU_instance = ESP32_C6_MCU(gnd, vcc_3v3, debug_en, debug_io0, debug_rx, debug_tx, led_control, usb_dm, usb_dp)
    Debug_Header_instance = Debug_Header(gnd, vcc_3v3, debug_en, debug_io0, debug_rx, debug_tx)
    LED_Blinker_instance = LED_Blinker(gnd, led_control)
    USB_Port_instance = USB_Port(gnd, vbus, usb_dm, usb_dp)
```

### Expected Hierarchical Structure (Correct)
```python
@circuit(name='main')
def main():
    # ✅ Only truly shared nets at main level
    vbus = Net('VBUS')      # Shared: USB_Port + Power_Supply
    vcc_3v3 = Net('VCC_3V3') # Shared: Power_Supply + ESP32C6
    gnd = Net('GND')        # Shared: All circuits
    usb_dp = Net('USB_DP')  # Shared: USB_Port + ESP32C6
    usb_dm = Net('USB_DM')  # Shared: USB_Port + ESP32C6

    # ✅ Only top-level circuits (3 circuits, not 5)
    usb_port_circuit = usb_port(vbus, gnd, usb_dp, usb_dm)
    power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
    esp32_circuit = esp32c6(vcc_3v3, gnd, usb_dp, usb_dm)  # Contains debug_header + led_blinker internally
```

## Root Cause Analysis

### Hierarchical Tree Structure
The KiCad parser correctly identifies the hierarchical relationships:
```
main
├── USB_Port
├── Power_Supply  
└── ESP32_C6_MCU
    ├── Debug_Header
    └── LED_Blinker
```

### Net Analysis Logic Flaw
The current hierarchical net analysis applies the **"one level above highest usage"** rule incorrectly:

1. **Identifies net usage**: `DEBUG_EN` used by `ESP32_C6_MCU` and `Debug_Header`
2. **Applies rule incorrectly**: Places net at `main` level (one above both circuits)
3. **Should apply rule correctly**: Places net at `ESP32_C6_MCU` level (one above `Debug_Header`, the deepest usage)

### Code Generation Logic Flaw
The circuit instantiation logic flattens the hierarchy:

1. **Correct approach**: Generate circuits only at their immediate parent level
2. **Current wrong approach**: Generate all circuits at the main level
3. **Missing logic**: Recursive generation within parent circuits

## Technical Analysis

### Affected Components

#### 1. Net Scope Assignment (`_analyze_hierarchical_nets`)
**Current Logic:**
```python
# Finds all circuits using a net and places it one level above the highest
if net_name in ['DEBUG_EN', 'DEBUG_IO0', 'DEBUG_RX', 'DEBUG_TX']:
    # Used by: ESP32_C6_MCU, Debug_Header
    # Places at: main level (❌ wrong)
```

**Required Logic:**
```python
# Should find the lowest common ancestor in the hierarchy tree
if net_name in ['DEBUG_EN', 'DEBUG_IO0', 'DEBUG_RX', 'DEBUG_TX']:
    # Used by: ESP32_C6_MCU, Debug_Header
    # Debug_Header is child of ESP32_C6_MCU
    # Places at: ESP32_C6_MCU level (✅ correct)
```

#### 2. Circuit Instantiation Logic (`_generate_main_circuit_code`)
**Current Logic:**
```python
# Instantiates ALL circuits at main level
for circuit_name in all_circuits:
    generate_instantiation_at_main_level(circuit_name)
```

**Required Logic:**
```python
# Instantiates circuits only at their immediate parent level
for circuit_name in top_level_circuits_only:
    generate_instantiation_with_internal_hierarchy(circuit_name)
```

## Proposed Solution Architecture

### Phase 1: Hierarchical Tree Analysis Enhancement

#### 1.1 Lowest Common Ancestor (LCA) Algorithm
```python
def find_lowest_common_ancestor(self, net_users: List[str], hierarchy_tree: Dict[str, List[str]]) -> str:
    """
    Find the lowest common ancestor for a set of net users in the hierarchy tree.
    
    Args:
        net_users: List of circuit names that use the net
        hierarchy_tree: Dict mapping parent -> list of children
        
    Returns:
        Circuit name where the net should be created
    """
    # Build reverse mapping: child -> parent
    child_to_parent = {}
    for parent, children in hierarchy_tree.items():
        for child in children:
            child_to_parent[child] = parent
    
    # Find all ancestors for each net user
    all_ancestors = []
    for user in net_users:
        ancestors = self._get_ancestors(user, child_to_parent)
        all_ancestors.append(set(ancestors))
    
    # Find common ancestors
    common_ancestors = set.intersection(*all_ancestors) if all_ancestors else set()
    
    # Return the deepest (lowest) common ancestor
    if not common_ancestors:
        return "main"  # Fallback to root
    
    # Find the deepest ancestor (highest depth in tree)
    deepest_ancestor = min(common_ancestors, 
                          key=lambda x: self._get_depth(x, hierarchy_tree))
    return deepest_ancestor
```

#### 1.2 Net Scope Determination
```python
def _determine_net_scope(self, net_name: str, net_users: List[str], 
                        hierarchy_tree: Dict[str, List[str]]) -> str:
    """
    Determine the correct scope (circuit) where a net should be created.
    
    This implements the "lowest common ancestor" rule for hierarchical nets.
    """
    # Special cases for global nets
    if net_name in ['GND', 'VCC', 'VBUS']:
        return "main"
    
    # For local nets (used by single circuit), create locally
    if len(net_users) == 1:
        return net_users[0]
    
    # For shared nets, find lowest common ancestor
    return self.find_lowest_common_ancestor(net_users, hierarchy_tree)
```

### Phase 2: Hierarchical Code Generation

#### 2.1 Recursive Circuit Generation
```python
def _generate_hierarchical_circuit(self, circuit_name: str, hierarchy_tree: Dict[str, List[str]], 
                                 net_assignments: Dict[str, str]) -> str:
    """
    Generate Python code for a circuit and its children recursively.
    
    Args:
        circuit_name: Name of circuit to generate
        hierarchy_tree: Parent -> children mapping
        net_assignments: Net name -> scope circuit mapping
        
    Returns:
        Generated Python code as string
    """
    code_lines = []
    
    # Generate nets that belong to this circuit scope
    local_nets = [net for net, scope in net_assignments.items() if scope == circuit_name]
    for net_name in local_nets:
        code_lines.append(f"    {net_name.lower()} = Net('{net_name}')")
    
    if local_nets:
        code_lines.append("")  # Blank line after nets
    
    # Generate components for this circuit
    circuit = self.circuits[circuit_name]
    for component in circuit.components:
        code_lines.append(self._generate_component_code(component))
    
    # Generate child circuit instantiations
    children = hierarchy_tree.get(circuit_name, [])
    for child_name in children:
        # Determine nets to pass to child
        child_nets = self._get_child_interface_nets(child_name, net_assignments)
        params = ", ".join(child_nets)
        code_lines.append(f"    {child_name.lower()}_circuit = {child_name.lower()}({params})")
    
    if children:
        code_lines.append("")  # Blank line after instantiations
    
    return "\n".join(code_lines)
```

#### 2.2 Interface Net Detection
```python
def _get_child_interface_nets(self, child_circuit: str, net_assignments: Dict[str, str]) -> List[str]:
    """
    Determine which nets should be passed as parameters to a child circuit.
    
    Args:
        child_circuit: Name of the child circuit
        net_assignments: Net name -> scope circuit mapping
        
    Returns:
        List of net variable names to pass as parameters
    """
    interface_nets = []
    
    # Find all nets used by the child circuit
    child_circuit_obj = self.circuits[child_circuit]
    child_nets = set(child_circuit_obj.nets.keys())
    
    # For each net used by child, check if it's defined in a parent scope
    for net_name in child_nets:
        net_scope = net_assignments.get(net_name)
        
        # If net is defined in parent scope, it's an interface net
        if net_scope and net_scope != child_circuit:
            interface_nets.append(net_name.lower())
    
    return sorted(interface_nets)  # Sort for consistency
```

### Phase 3: Top-Level Circuit Identification

#### 3.1 Hierarchy Root Detection
```python
def _identify_top_level_circuits(self, hierarchy_tree: Dict[str, List[str]]) -> List[str]:
    """
    Identify circuits that should be instantiated at the main level.
    
    Args:
        hierarchy_tree: Parent -> children mapping
        
    Returns:
        List of circuit names that are direct children of main
    """
    # Find circuits that have no parent (except main)
    all_children = set()
    for children in hierarchy_tree.values():
        all_children.update(children)
    
    # Circuits that are children of main
    main_children = hierarchy_tree.get("main", [])
    
    return main_children
```

## Implementation Strategy

### Step 1: Enhance Net Analysis
1. **Replace simple level detection** with LCA algorithm
2. **Add hierarchy depth calculation** utilities
3. **Implement ancestor traversal** functions
4. **Test with complex hierarchical structures**

### Step 2: Refactor Code Generation
1. **Separate top-level from hierarchical generation**
2. **Implement recursive circuit generation**
3. **Add interface net detection logic**
4. **Generate proper parameter passing**

### Step 3: Validation Framework
1. **Create test cases** for various hierarchy patterns
2. **Validate net scope assignments**
3. **Verify circuit instantiation levels**
4. **Test with real-world hierarchical designs**

## Generalization Requirements

### Universal Hierarchy Support
- **No hardcoded circuit names** - algorithm works with any hierarchy
- **Dynamic depth handling** - supports arbitrary nesting levels  
- **Flexible net scoping** - adapts to different sharing patterns
- **Scalable to complex designs** - handles hundreds of circuits

### Algorithm Properties
- **O(n²) complexity** maximum for net analysis
- **Deterministic output** - same input always produces same result
- **Error handling** - graceful degradation for malformed hierarchies
- **Memory efficient** - suitable for large circuit designs

## Expected Benefits

### Code Quality Improvements
1. **Proper encapsulation** - nets scoped to appropriate levels
2. **Cleaner interfaces** - only necessary parameters passed
3. **Maintainable structure** - hierarchical organization preserved
4. **Professional patterns** - follows industry best practices

### Functional Correctness
1. **Accurate representation** - matches original hierarchical design
2. **Correct net connectivity** - no missing or extra connections
3. **Proper abstraction** - implementation details hidden appropriately
4. **Testable components** - each level can be validated independently

### Development Workflow
1. **Easier debugging** - issues isolated to appropriate hierarchy levels
2. **Better reusability** - subcircuits can be used independently
3. **Clearer documentation** - structure matches design intent
4. **Scalable complexity** - supports large, complex designs

## Testing Strategy

### Unit Tests
- **LCA algorithm correctness** with various tree structures
- **Net scope assignment** validation
- **Interface detection** accuracy
- **Code generation** format verification

### Integration Tests  
- **Complete workflow** KiCad → Python → KiCad round-trip
- **Hierarchy preservation** through full pipeline
- **Net connectivity validation** at each hierarchy level
- **Real-world circuit examples** (ESP32, STM32, complex MCU boards)

### Regression Tests
- **Existing functionality** must remain unaffected
- **Simple circuits** (non-hierarchical) should work unchanged
- **Performance benchmarks** - no significant slowdown
- **Output format consistency** - existing tools compatibility

---

**Status**: Bug identified and solution architecture defined  
**Priority**: High - affects core hierarchical generation functionality  
**Complexity**: Medium - requires algorithmic enhancement but follows established patterns  
**Impact**: Critical - enables proper professional hierarchical circuit design workflow