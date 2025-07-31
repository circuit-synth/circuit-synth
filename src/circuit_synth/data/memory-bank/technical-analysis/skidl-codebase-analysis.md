# SKIDL Codebase Analysis

## Overview

SKIDL (SKiDL) is a mature, pure-Python library for electronic circuit description that has been continuously developed since ~2016. The codebase analysis reveals a sophisticated, feature-rich system with extensive capabilities beyond basic netlist generation.

## Architecture Overview

### Pure Python Architecture
SKIDL is implemented as a single Python package with modular components:

```
src/skidl/
├── __init__.py           # Main API exports
├── part.py              # Component/part management
├── net.py               # Net (wire) handling
├── pin.py               # Pin connectivity
├── bus.py               # Multi-wire buses
├── circuit.py           # Circuit container
├── group.py             # Hierarchical grouping
├── interface.py         # Interface definitions
├── pyspice.py           # SPICE simulation integration
├── schlib.py            # Symbol library management
├── part_query.py        # Component search system
├── schematics/          # Schematic generation
│   ├── place.py         # Autoplacer algorithms
│   ├── route.py         # Wire routing
│   └── node.py          # Hierarchical layout
├── netlist_to_skidl.py  # Reverse import capability
└── tools/               # EDA tool integrations
```

## Core Component System

### Part Class Implementation
**File:** `src/skidl/part.py`

The Part class is the foundation of SKIDL's component system:

```python
class Part(SkidlBaseObject):
    """A class for storing a definition of a schematic part."""
    
    def __init__(self, lib=None, name=None, dest=NETLIST, tool=None, 
                 connections=None, part_defn=None, circuit=None, 
                 ref_prefix="", ref=None, tag=None, pin_splitters=None, **kwargs):
```

**Key Features:**
- **Template System:** `dest=TEMPLATE` for reusable part definitions
- **Library Integration:** Automatic loading from KiCad symbol libraries
- **Pin Management:** Sophisticated pin numbering and naming systems
- **ERC Integration:** Built-in electrical rules checking
- **Multi-tool Support:** KiCad, SPICE, and other EDA formats

**Advanced Pin Access:**
```python
# Multiple pin access methods
part.p[1,2,3]        # Pin numbers only  
part.n["VCC","GND"]  # Pin names only
part["VCC", 1, "D0"] # Mixed names and numbers
```

### Net System Implementation
**File:** `src/skidl/net.py`

The Net class handles electrical connectivity:

```python
class Net(SkidlBaseObject):
    """Lists of connected pins are stored as nets using this class."""
    
    def __init__(self, name=None, circuit=None, *pins_nets_buses, **attribs):
        self._pins = []
        self.circuit = None
        self.code = None  # KiCad netlist number
        self.stub = False  # For schematic generation
```

**Key Features:**
- **Operator Overloading:** `&` for serial, `|` for parallel connections
- **Network Integration:** Automatic network topology analysis
- **ERC Checking:** Built-in electrical rules validation
- **Multi-format Export:** KiCad, SPICE, and other netlist formats

**Connection Syntax:**
```python
# Series connection with & operator
vcc & r1 & led & gnd

# Parallel connection with += operator  
power_net += part1["VCC"], part2["VDD"], part3["PWR"]
```

## SPICE Integration System

### PySpice Integration
**File:** `src/skidl/pyspice.py`

SKIDL provides seamless SPICE simulation integration:

```python
# Import PySpice components and simulation capabilities
from PySpice import *
from PySpice.Unit import *

# Set SPICE as default tool
set_default_tool(SPICE)

# Create ground net for SPICE (must be "0")
GND = gnd = Net("0")
gnd.fixed_name = True
```

**Key Features:**
- **Direct PySpice Integration:** Automatic component mapping to SPICE models
- **Unit Support:** Full PySpice unit system (`1@u_V`, `1000@u_Ohm`)
- **Simulation Integration:** Direct netlist export to PySpice simulator
- **Model Library:** Built-in SPICE component library

**Example SPICE Circuit:**
```python
from skidl.pyspice import *

# Create SPICE components with units
vs = V(ref="VS", dc_value=1@u_V)
r = R(value=1000@u_Ohm)

# Connect using SKIDL operators
vs["p"] & r & gnd & vs["n"]

# Generate and simulate
circ = generate_netlist()
sim = circ.simulator()
dc_vals = sim.dc(VS=slice(0, 10, 0.1))
```

## Schematic Generation System

### Autoplacer Implementation
**File:** `src/skidl/schematics/place.py`

SKIDL includes sophisticated schematic layout algorithms:

```python
def add_placement_bboxes(parts, **options):
    """Expand part bounding boxes to include space for subsequent routing."""
    
def snap_to_grid(part_or_blk):
    """Snap Part or PartBlock to grid."""
```

**Key Features:**
- **Force-Directed Placement:** Physics-based component placement
- **Hierarchical Layout:** Supports nested subcircuit blocks
- **Grid Alignment:** Automatic snap-to-grid functionality
- **Routing Awareness:** Placement considers wire routing requirements

**Placement Algorithm:**
1. **Grouping:** Parts grouped by connectivity
2. **Force-Directed:** Attractive forces from nets, repulsive from overlaps
3. **Grid Snapping:** Final alignment to routing grid
4. **Hierarchical:** Nested placement for subcircuits

### Routing System
**File:** `src/skidl/schematics/route.py`

Advanced wire routing for clean schematics:
- **Orthogonal Routing:** Manhattan-style wire routing
- **Obstacle Avoidance:** Routes around existing components
- **Bundle Optimization:** Groups related signals together
- **Junction Minimization:** Reduces wire crossings

## Hierarchical Design System

### SubCircuit Decorator
**File:** `src/skidl/group.py`

SKIDL provides hierarchical design through decorators:

```python
@SubCircuit
def voltage_regulator(vin, vout, gnd):
    """Create a voltage regulator subcircuit."""
    reg = Part("Regulator_Linear", "AMS1117-3.3")
    cap_in = Part("Device", "C", value="10uF")
    cap_out = Part("Device", "C", value="10uF")
    
    # Connect components
    vin += reg["IN"], cap_in[1]
    vout += reg["OUT"], cap_out[1] 
    gnd += reg["GND"], cap_in[2], cap_out[2]
```

**Key Features:**
- **Context Management:** Automatic hierarchical grouping
- **Tag Support:** Component tagging for organization
- **Circuit Integration:** Seamless integration with parent circuits
- **Result Passing:** Return values from subcircuits

## Part Library System

### Advanced Search Capabilities
**File:** `src/skidl/part_query.py`

SKIDL provides comprehensive component search:

```python
# Search functions available
search("STM32*")           # Search for parts
search_parts("microcontroller") 
search_footprints("*QFP*")
show("Device:R")           # Show part details
show_part("LM358")
show_footprint("SOIC-8")
```

**Key Features:**
- **Pattern Matching:** Regex and wildcard support
- **Multi-library Search:** Search across multiple libraries
- **Detailed Information:** Full part specifications and pin data
- **Footprint Integration:** Automatic footprint association

### Library Management
**File:** `src/skidl/schlib.py`

Sophisticated library management system:
- **Multi-format Support:** KiCad, SPICE, and custom formats
- **Backup Libraries:** Fallback library system for missing symbols
- **Caching:** Performance optimization for large libraries
- **Dependency Resolution:** Automatic library dependency handling

## ERC (Electrical Rules Checking)

### Built-in ERC System
**File:** `src/skidl/erc.py`

Comprehensive electrical rules checking:

```python
# ERC functions for parts and nets
dflt_part_erc(part)  # Check part connectivity
dflt_net_erc(net)    # Check net electrical properties
```

**Checks Performed:**
- **Unconnected Pins:** Detect floating inputs/outputs
- **Multiple Drivers:** Identify net conflicts
- **Power Connectivity:** Validate power and ground connections
- **Pin Type Compatibility:** Check electrical compatibility

## Bidirectional Import System

### Netlist Import Capability
**File:** `src/skidl/netlist_to_skidl.py`

SKIDL can import existing netlists and convert them to code:

```python
def netlist_to_skidl(netlist_src):
    """Convert a netlist into an equivalent SKiDL program."""
    
def template_comp_to_skidl(template_comp):
    """Instantiate a component that will be used as a template."""
```

**Key Features:**
- **KiCad Netlist Import:** Parse existing KiCad netlists
- **Code Generation:** Generate equivalent SKIDL Python code
- **Component Mapping:** Map netlist components to SKIDL parts
- **Template Generation:** Create reusable component templates

## Advanced Features Analysis

### 1. Network Topology Analysis
**File:** `src/skidl/network.py`

SKIDL includes sophisticated network analysis:
- **Series/Parallel Detection:** Automatic topology recognition
- **Network Simplification:** Reduce complex networks
- **Impedance Calculation:** Basic electrical parameter computation

### 2. Interface System
**File:** `src/skidl/interface.py`

Structured interface definitions for modular design:
```python
# Define reusable interfaces  
PowerInterface = Interface("vcc", "gnd")
SPIInterface = Interface("clk", "mosi", "miso", "cs")
```

### 3. Multi-tool Integration
**Directory:** `src/skidl/tools/`

Support for multiple EDA tools:
- **KiCad:** Full KiCad symbol and netlist support
- **SPICE:** Complete PySpice integration
- **Altium:** Basic Altium netlist export
- **Generic:** Tool-agnostic netlist formats

## Code Architecture Insights

### 1. Mature Object Model
The codebase shows 8+ years of refinement:
- **Consistent API:** Well-defined interfaces across modules
- **Error Handling:** Comprehensive exception system
- **Documentation:** Extensive docstrings and examples
- **Testing:** Comprehensive test suite with edge cases

### 2. Performance Optimizations
- **Lazy Loading:** Parts loaded only when accessed
- **Caching:** Symbol and library data caching
- **Efficient Data Structures:** Optimized for large circuits
- **Memory Management:** Proper cleanup and garbage collection

### 3. Extensibility
- **Plugin Architecture:** Support for custom EDA tools
- **Custom Components:** Easy addition of new part types
- **Operator Overloading:** Natural Python syntax for connections
- **Callback System:** Hooks for custom processing

## Comparison with Documentation Claims

The code analysis reveals capabilities that match and exceed documentation:

**Confirmed Capabilities:**
- ✅ **SPICE Integration:** Comprehensive PySpice support
- ✅ **Schematic Generation:** Full autoplacer and routing
- ✅ **ERC System:** Built-in electrical rules checking
- ✅ **Library Management:** Advanced search and query
- ✅ **Hierarchical Design:** Mature subcircuit system

**Additional Capabilities Found:**
- ✅ **Bidirectional Import:** Netlist-to-code conversion
- ✅ **Advanced Placement:** Force-directed placement algorithms
- ✅ **Network Analysis:** Topology recognition and simplification
- ✅ **Multi-tool Support:** Extensive EDA tool integration

## Limitations Identified

### 1. No PCB Layout Generation
SKIDL generates netlists but does not create PCB layouts:
- Relies on external PCB tools for physical layout
- No component placement on PCB
- No trace routing for manufacturing

### 2. KiCad Integration Limitations
While comprehensive for netlists, KiCad integration has gaps:
- Cannot import existing KiCad schematic files
- Limited schematic editing capabilities
- No bidirectional schematic synchronization

### 3. Complex Learning Curve
The extensive feature set creates complexity:
- Multiple connection syntaxes (`&`, `+=`, indexing)
- Large API surface with many options
- Requires understanding of multiple EDA concepts

## Conclusion

The SKIDL codebase represents a mature, sophisticated system for programmatic circuit design with capabilities that significantly exceed initial assessments:

**Strengths:**
- **Comprehensive SPICE Integration** with PySpice
- **Advanced Schematic Generation** with autoplacer and routing
- **Sophisticated Component System** with extensive library management
- **Mature Architecture** with 8+ years of development
- **Extensive ERC System** for design validation
- **Bidirectional Capabilities** for netlist import

**Limitations:**
- **No PCB Layout Generation** (netlist-only for PCB)
- **Complex API** with steep learning curve
- **Limited KiCad Bidirectional** integration
- **Academic Focus** rather than professional workflow integration

SKIDL represents the most mature and feature-complete solution in the programmatic electronics design space, with particular strength in simulation integration and schematic generation capabilities.