# System Patterns - Ratsnest Generation Implementation

## Design Patterns Used

### 1. Data Class Pattern for Type Safety
**Usage**: PadInfo and RatsnestConnection data structures

```python
@dataclass
class PadInfo:
    """Information about a pad for ratsnest calculations."""
    reference: str
    pad_number: str
    net_number: int
    net_name: str
    position: Tuple[float, float]
    layer: str

@dataclass  
class RatsnestConnection:
    """Represents a ratsnest connection between two pads."""
    from_pad: PadInfo
    to_pad: PadInfo
    length: float
    net_number: int
    net_name: str
```

**Benefits**:
- Type safety with automatic type hints
- Immutable-by-default data structures
- Clear data contracts between functions
- Automatic `__repr__` and `__eq__` methods

### 2. Strategy Pattern for Algorithm Selection
**Usage**: Multiple ratsnest topology algorithms

```python
def generate_ratsnest(self, pcb_data: Dict[str, Any], 
                     topology: str = "mst") -> List[RatsnestConnection]:
    if topology == "mst":
        connections = self.generate_minimum_spanning_tree(pads)
    elif topology == "star":  
        connections = self.generate_star_topology(pads)
    else:
        logger.warning(f"Unknown topology '{topology}', using MST")
        connections = self.generate_minimum_spanning_tree(pads)
```

**Benefits**:
- Easy to add new topology algorithms
- Runtime algorithm selection
- Clean separation of algorithm implementations
- Extensible design for future enhancements

### 3. Builder Pattern for PCB Integration
**Usage**: Gradual construction of ratsnest elements

```python
def add_ratsnest_to_pcb(self, pcb_data: Dict[str, Any], 
                       topology: str = "mst",
                       layer: str = "Dwgs.User",
                       line_width: float = 0.05) -> int:
    # Generate connections
    connections = self.generate_ratsnest(pcb_data, topology)
    
    # Build graphics elements
    for connection in connections:
        line_graphic = {
            'type': 'gr_line',
            'start': {'x': from_x, 'y': from_y},
            'end': {'x': to_x, 'y': to_y},
            'stroke': {'width': line_width, 'type': 'dash'},
            'layer': layer,
            'uuid': self._generate_uuid()
        }
        pcb_data['graphics'].append(line_graphic)
```

**Benefits**:
- Step-by-step construction of complex data structures
- Configurable parameters for customization
- Clear separation between data generation and formatting

### 4. Template Method Pattern for PCB Generation Pipeline
**Usage**: PCB generator integration with ratsnest as optional step

```python
def generate_pcb(self, generate_ratsnest: bool = True) -> bool:
    try:
        # Core PCB generation steps...
        # 1. Component placement
        # 2. Netlist application  
        # 3. Auto-routing (optional)
        # 4. File save
        
        # Template method extension point
        if generate_ratsnest:
            self._generate_ratsnest_step()
            
        return True
    except Exception as e:
        logger.error(f"Error generating PCB: {e}")
        return False

def _generate_ratsnest_step(self):
    """Template method for ratsnest generation."""
    logger.info("Generating ratsnest connections...")
    # Implementation details...
```

**Benefits**:
- Consistent pipeline structure
- Optional steps can be easily added/removed
- Clear extension points for new features
- Maintains backward compatibility

### 5. Factory Method Pattern for UUID Generation
**Usage**: Consistent UUID generation across ratsnest elements

```python
def _generate_uuid(self) -> str:
    """Generate a UUID for PCB elements."""
    import uuid
    return str(uuid.uuid4())
```

**Benefits**:
- Centralized UUID generation logic
- Easy to modify UUID generation strategy
- Consistent format across all elements

## API Design Patterns

### 1. Parameter Object Pattern
**Usage**: Circuit.to_kicad_project() method signature

```python
def to_kicad_project(self, 
                    project_name: str,
                    project_dir: str = "",
                    generate_pcb: bool = True,
                    force_regenerate: bool = True,
                    placement_algorithm: str = "connection_aware",
                    draw_bounding_boxes: bool = False,
                    generate_ratsnest: bool = True) -> None:
```

**Benefits**:
- Clear parameter naming and defaults
- Backward compatibility through default parameters
- Self-documenting API through parameter names
- Easy to extend with new options

### 2. Default Enabled Pattern
**Usage**: Ratsnest generation enabled by default

```python
generate_ratsnest: bool = True  # Default enabled
```

**Pattern Rationale**:
- New features should provide immediate value
- Users get professional output without configuration
- Can be disabled when not needed
- Follows principle of "secure by default, usable by default"

### 3. Graceful Degradation Pattern
**Usage**: Error handling in ratsnest generation

```python
if generate_ratsnest:
    try:
        # Ratsnest generation logic
        success = add_ratsnest_to_pcb(str(self.pcb_path), str(netlist_path))
        if success:
            logger.info("✓ Ratsnest connections added to PCB")
        else:
            logger.warning("⚠ No ratsnest connections generated")
    except Exception as e:
        logger.warning(f"⚠ Ratsnest generation failed: {e}")
        # Continue with PCB generation
```

**Benefits**:
- Core functionality never fails due to optional features
- Clear logging for debugging
- User gets partial results rather than complete failure

## Algorithm Implementation Patterns

### 1. Prim's Algorithm Implementation Pattern
**Usage**: Minimum spanning tree generation

```python
def generate_minimum_spanning_tree(self, pads: List[PadInfo]) -> List[RatsnestConnection]:
    if len(pads) < 2:
        return []
    
    connections = []
    connected = {0}  # Start with first pad
    unconnected = set(range(1, len(pads)))
    
    while unconnected:
        min_distance = float('inf')
        best_connection = None
        
        # Find shortest connection between connected and unconnected pads
        for connected_idx in connected:
            for unconnected_idx in unconnected:
                distance = self.calculate_distance(
                    pads[connected_idx].position,
                    pads[unconnected_idx].position
                )
                
                if distance < min_distance:
                    min_distance = distance
                    best_connection = (connected_idx, unconnected_idx)
        
        # Add best connection and update sets
        if best_connection:
            # ... create connection and update sets
    
    return connections
```

**Pattern Benefits**:
- Clear algorithm structure following textbook implementation
- Efficient O(V²) complexity for small to medium graphs
- Readable code that matches algorithm description
- Easy to verify correctness

### 2. Early Return Pattern
**Usage**: Input validation and edge cases

```python
def generate_minimum_spanning_tree(self, pads: List[PadInfo]) -> List[RatsnestConnection]:
    if len(pads) < 2:
        return []  # Early return for edge case
    
    # Main algorithm logic...
```

**Benefits**:
- Reduces nesting levels
- Clear handling of edge cases
- Fail-fast behavior
- Improved readability

### 3. Distance Calculation Pattern
**Usage**: Euclidean distance for connection optimization

```python
def calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two positions."""
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    return math.sqrt(dx*dx + dy*dy)
```

**Benefits**:
- Simple, efficient calculation
- Mathematically correct
- Easy to replace with other distance metrics if needed

## Integration Patterns

### 1. Pipeline Integration Pattern
**Usage**: Adding ratsnest step to existing PCB generation pipeline

```python
# Existing pipeline steps
pcb.save(self.pcb_path)
logger.info(f"PCB file saved to: {self.pcb_path}")

# New step added to pipeline (AFTER PCB save)
if generate_ratsnest:
    logger.info("Generating ratsnest connections...")
    # Ratsnest generation logic...
```

**Benefits**:
- Non-intrusive integration
- Maintains existing workflow
- Clear separation of concerns
- Easy to enable/disable

### 2. Dependency Injection Pattern
**Usage**: Importing ratsnest functionality where needed

```python
from circuit_synth.pcb.simple_ratsnest import add_ratsnest_to_pcb
```

**Benefits**:
- Loose coupling between modules
- Only import what's needed
- Easy to mock for testing
- Clear dependencies

### 3. Configuration Parameter Pattern
**Usage**: Consistent parameter passing through call chain

```python
# Circuit level
circuit.to_kicad_project(generate_ratsnest=True)
    ↓
# KiCad integration level  
generator.generate_pcb(generate_ratsnest=generate_ratsnest)
    ↓
# Implementation level
if generate_ratsnest:
    add_ratsnest_to_pcb(pcb_file, netlist_file)
```

**Benefits**:
- Consistent configuration across layers
- Clear parameter flow
- Easy to trace configuration source
- Type-safe parameter passing

## Error Handling Patterns

### 1. Logging-First Error Handling
**Usage**: Comprehensive logging for debugging

```python
try:
    success = add_ratsnest_to_pcb(str(self.pcb_path), str(netlist_path))
    if success:
        logger.info("✓ Ratsnest connections added to PCB")
    else:
        logger.warning("⚠ No ratsnest connections generated")
except Exception as e:
    logger.error(f"Error in ratsnest generation: {e}", exc_info=True)
```

**Benefits**:
- Comprehensive debugging information
- Clear success/failure indicators
- Stack traces for unexpected errors
- Consistent logging format

### 2. Defensive Programming Pattern
**Usage**: Input validation and null checking

```python
if netlist_path.exists():
    success = add_ratsnest_to_pcb(str(self.pcb_path), str(netlist_path))
else:
    logger.warning(f"⚠ Netlist file not found: {netlist_path}")
```

**Benefits**:
- Prevents runtime errors
- Clear error messages
- Graceful degradation
- Better user experience

## Testing Patterns

### 1. Test Data Creation Pattern
**Usage**: Creating test data structures for ratsnest testing

```python
def create_test_pad_info(ref: str, pad: str, net: int, pos: Tuple[float, float]) -> PadInfo:
    return PadInfo(
        reference=ref,
        pad_number=pad,
        net_number=net,
        net_name=f"Net_{net}",
        position=pos,
        layer="F.Cu"
    )
```

**Benefits**:
- Consistent test data creation
- Reduces test code duplication
- Easy to modify test scenarios
- Clear test data structure

### 2. Algorithm Verification Pattern
**Usage**: Testing MST and star topology algorithms

```python
def test_mst_algorithm():
    # Create test pads in known configuration
    pads = [
        create_test_pad_info("R1", "1", 1, (0, 0)),
        create_test_pad_info("R2", "1", 1, (10, 0)),
        create_test_pad_info("R3", "1", 1, (5, 10))
    ]
    
    # Generate MST
    generator = RatsnestGenerator()
    connections = generator.generate_minimum_spanning_tree(pads)
    
    # Verify expected connections and distances
    assert len(connections) == 2  # n-1 connections for MST
    # ... verify specific connections
```

**Benefits**:
- Algorithm correctness verification
- Clear test scenarios
- Quantitative validation
- Easy to extend with new test cases

These patterns demonstrate best practices in the ratsnest implementation, showing how to build robust, maintainable, and extensible code that integrates cleanly with existing systems.