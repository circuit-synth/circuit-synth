# Ratsnest Generation System - 2025-07-28

## Feature Overview

The ratsnest generation system provides visual airwire connections in PCB designs, showing unrouted net connections between pads. This is a fundamental feature for PCB layout design, helping designers understand connection requirements and routing topology.

## Core Components

### 1. Comprehensive Ratsnest Generator
**File**: `src/circuit_synth/pcb/ratsnest_generator.py`

**Key Classes**:
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

class RatsnestGenerator:
    """Generates ratsnest connections for PCB designs."""
```

**Topology Algorithms**:
- **Minimum Spanning Tree (MST)**: Uses Prim's algorithm for optimal total wire length
- **Star Topology**: Connects all pads to first pad for simple networks

### 2. Simple Ratsnest Converter
**File**: `src/circuit_synth/pcb/simple_ratsnest.py`

**Functionality**:
- Direct netlist-to-ratsnest conversion using regex parsing
- Efficient star topology generation
- Direct PCB file integration

```python
def add_ratsnest_to_pcb(pcb_file: str, netlist_file: str) -> bool:
    """Add ratsnest entries from netlist to PCB file."""
```

## API Integration

### Circuit Class Enhancement
**File**: `src/circuit_synth/core/circuit.py`

```python
def to_kicad_project(self, 
                    project_name: str,
                    project_dir: str = "",
                    generate_pcb: bool = True,
                    force_regenerate: bool = True,
                    placement_algorithm: str = "connection_aware",
                    draw_bounding_boxes: bool = False,
                    generate_ratsnest: bool = True) -> None:  # NEW PARAMETER
```

### PCB Generator Integration
**File**: `src/circuit_synth/kicad/pcb_gen/pcb_generator.py`

```python
def generate_pcb(self,
                placement_algorithm: str = "connection_aware",
                board_width: float = 100.0,
                board_height: float = 80.0,
                auto_route: bool = False,
                routing_passes: int = 4,
                routing_effort: float = 1.0,
                generate_ratsnest: bool = True) -> bool:  # NEW PARAMETER
```

## Technical Implementation

### Pad Information Extraction
The system analyzes PCB data structures to extract:
- Component footprint positions
- Individual pad positions relative to footprints
- Net assignments for each pad
- Layer information

### Connection Algorithms

#### Minimum Spanning Tree (MST)
- **Algorithm**: Prim's algorithm implementation
- **Goal**: Minimize total wire length across all connections
- **Use Case**: Complex nets with multiple connections
- **Performance**: O(V²) where V is number of pads

#### Star Topology
- **Algorithm**: Connect all pads to first pad
- **Goal**: Simple radial connections
- **Use Case**: Power/ground networks, simple nets
- **Performance**: O(V) where V is number of pads

### KiCad Integration
Generated ratsnest connections are added as:
- **Element Type**: `gr_line` graphics elements
- **Line Style**: Dashed lines for visual distinction
- **Layer**: Technical layers (e.g., "Dwgs.User")
- **UUID**: Unique identifiers for each connection

## Pipeline Integration

### Generation Workflow
1. **PCB Layout Generation**: Complete component placement and PCB file creation
2. **File Save**: Write PCB file to disk
3. **Ratsnest Generation**: Extract netlist and generate connections (NEW STEP)
4. **PCB Update**: Add ratsnest elements to saved PCB file
5. **Project Update**: Update project files with final PCB

### Error Handling
- Graceful degradation when netlist files are missing
- Comprehensive logging for debugging
- Backward compatibility with existing projects
- No interference with core PCB generation

## Usage Examples

### Basic Usage (Default Enabled)
```python
@circuit
def amplifier():
    # Define circuit
    return circuit

# Generate with ratsnest (default behavior)
amplifier().to_kicad_project("amplifier_design")
```

### Explicit Control
```python
# Enable ratsnest generation
amplifier().to_kicad_project(
    "amplifier_with_ratsnest",
    generate_ratsnest=True
)

# Disable ratsnest generation
amplifier().to_kicad_project(
    "amplifier_no_ratsnest", 
    generate_ratsnest=False
)
```

### Direct PCB Generator Usage
```python
from circuit_synth.kicad.pcb_gen.pcb_generator import PCBGenerator

pcb_gen = PCBGenerator(project_dir, project_name)
success = pcb_gen.generate_pcb(
    placement_algorithm="connection_aware",
    generate_ratsnest=True  # Enable ratsnest
)
```

## Performance Characteristics

### Computational Complexity
- **MST Algorithm**: O(V²) where V is number of pads per net
- **Star Algorithm**: O(V) where V is number of pads per net
- **Overall**: Linear in total number of nets

### Memory Usage
- **Efficient Processing**: One net at a time
- **Minimal Overhead**: Small data structures for pad information
- **Scalable**: Handles large circuits effectively

### Integration Impact
- **Low Overhead**: Minimal impact on PCB generation time
- **Post-Processing**: Runs after PCB generation to avoid interference
- **Optional**: Can be disabled for faster generation when not needed

## Visualization Features

### Visual Representation
- **Line Style**: Dashed lines for clear identification as airwires
- **Layer Placement**: Technical layers that don't interfere with routing
- **UUID Tracking**: Each connection has unique identifier for updates

### KiCad Compatibility
- **S-expression Format**: Proper KiCad file format compliance
- **Layer Standards**: Uses standard KiCad technical layers
- **Graphics Elements**: Standard `gr_line` elements for visualization

## Future Enhancement Opportunities

### Advanced Algorithms
- **Steiner Tree**: More optimal connection topology
- **Layer-Aware Routing**: Different strategies for different layers
- **Impedance Consideration**: Signal integrity aware connections

### Visualization Improvements
- **Color Coding**: Different colors for power, signal, ground nets
- **Line Weight Variation**: Different weights for different net priorities
- **Multi-Layer Support**: 3D ratsnest visualization

### Integration Enhancements
- **Real-Time Updates**: Dynamic ratsnest during interactive design
- **Auto-Router Integration**: Direct integration with routing algorithms
- **Design Rule Awareness**: Consider design rules during generation

## Testing and Validation

### Integration Testing
- Tested with reference design examples
- Verified KiCad file compatibility
- Confirmed visual output in KiCad

### Error Handling Validation
- Missing netlist file scenarios
- Invalid PCB data handling
- Graceful degradation testing

### Performance Testing
- Large circuit handling (100+ components)
- Memory usage validation
- Generation time impact assessment

## Technical Benefits

### For PCB Design Workflow
- **Visual Guidance**: Clear understanding of required connections
- **Routing Planning**: Optimal path identification for manual routing
- **Design Verification**: Visual confirmation of net connectivity
- **Professional Output**: Industry-standard PCB visualization

### For Circuit-Synth Framework
- **Feature Completeness**: Brings PCB generation closer to professional EDA tools
- **User Experience**: Significantly improves PCB design workflow
- **Integration Quality**: Clean API integration without breaking changes
- **Performance**: Efficient algorithms with minimal overhead

## Success Metrics

### Functional Validation
- ✅ Ratsnest connections generated for all test circuits
- ✅ KiCad compatibility maintained with generated files
- ✅ Both MST and star topologies working correctly
- ✅ Pipeline integration working seamlessly

### Quality Assurance
- ✅ Comprehensive error handling and logging
- ✅ Backward compatibility preserved
- ✅ Clean API integration without breaking changes
- ✅ Efficient performance with minimal overhead

### User Experience
- ✅ Default enabled behavior provides immediate value
- ✅ Simple API for controlling ratsnest generation
- ✅ Professional visual output in KiCad
- ✅ Clear documentation and examples available

## Implementation Details

### File Locations
```
src/circuit_synth/
├── pcb/
│   ├── ratsnest_generator.py    # Comprehensive ratsnest generation
│   └── simple_ratsnest.py       # Simple netlist-to-ratsnest converter
├── core/
│   └── circuit.py               # API integration (generate_ratsnest parameter)
└── kicad/pcb_gen/
    └── pcb_generator.py         # Pipeline integration
```

### Dependencies
- **Core Python**: Standard library (math, dataclasses, collections)
- **Circuit-Synth Core**: Integration with existing PCB generation pipeline
- **KiCad Compatibility**: S-expression format generation

### Configuration Options
- **Topology Selection**: MST vs Star algorithms
- **Layer Assignment**: Configurable target layer for ratsnest lines
- **Line Styling**: Configurable line width and style
- **Enable/Disable**: Full control over ratsnest generation

This ratsnest generation system represents a significant enhancement to Circuit-Synth's PCB design capabilities, providing professional-grade visual feedback for PCB layout design and routing planning.