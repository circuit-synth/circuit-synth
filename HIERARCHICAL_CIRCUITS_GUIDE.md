# Circuit-Synth Hierarchical Circuits and Subcircuits Guide

## Overview

Circuit-synth fully supports **hierarchical/nested circuits** through a clean Python API. Hierarchical circuits generate multiple KiCad schematic files (`.kicad_sch`) organized in a parent-child sheet structure, enabling large designs to be broken into manageable modules.

---

## Core Concepts

### 1. The @circuit Decorator

The `@circuit` decorator is the fundamental building block for creating circuits and subcircuits.

```python
from circuit_synth import *

@circuit(name="power_supply")
def power_supply():
    """5V to 3.3V regulation"""
    # Components added here
    regulator = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U")
    cap_in = Component(symbol="Device:C", ref="C", value="10uF")
```

**Key Features:**
- `name`: Optional circuit name (defaults to function name)
- `comments`: Whether to extract docstring as schematic annotation (default: True)
- Automatically creates a `Circuit` object
- Returns the Circuit instance for further manipulation

### 2. Subcircuits are Functions

Subcircuits are simply other `@circuit` decorated functions called from within a parent circuit function:

```python
@circuit(name="child1")
def child1():
    """Child circuit definition"""
    r2 = Component(symbol="Device:R", ref="R2", value="10k")

@circuit(name="main")
def main():
    """Main circuit with subcircuits"""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    
    # Instantiate subcircuits - this creates the parent-child relationship
    child_instance = child1()

# Execute to create the hierarchy
if __name__ == "__main__":
    circuit = main()
    circuit.generate_kicad_project(project_name="my_project")
```

**How it works:**
1. When `child1()` is called inside `main()`, it returns a Circuit object
2. The `@circuit` decorator automatically detects the parent circuit via `_CURRENT_CIRCUIT`
3. The child circuit is registered with parent via `add_subcircuit()`
4. Each subcircuit becomes a separate `.kicad_sch` file in the KiCad project

### 3. Circuit Class Hierarchy Support

The `Circuit` class has built-in subcircuit support:

```python
# Located at: src/circuit_synth/core/circuit.py

class Circuit:
    def __init__(self, name=None, description=None, auto_comments=True):
        self._parent = None                      # Parent circuit
        self._subcircuits = []                   # List of child circuits
        self._reference_manager = ReferenceManager()  # Shared reference namespace
        # ...
    
    def add_subcircuit(self, subcirc: "Circuit"):
        """Add a subcircuit and establish parent-child relationship"""
        subcirc._parent = self
        self._subcircuits.append(subcirc)
        # Link reference managers for proper namespace isolation
        subcirc._reference_manager.set_parent(self._reference_manager)
    
    @property
    def subcircuits(self):
        """Get subcircuits list"""
        return self._subcircuits
```

---

## Creating Hierarchical Circuits

### Pattern 1: Pure Hierarchical (Only Subcircuits in Root)

The root circuit contains only subcircuits, no components.

```python
@circuit(name="power")
def power_supply():
    """Power delivery subsystem"""
    regulator = Component(symbol="Regulator_Linear:AMS1117", ref="U1")
    cap = Component(symbol="Device:C", ref="C1", value="10uF")

@circuit(name="mcu")
def microcontroller():
    """MCU with clock and reset"""
    mcu = Component(symbol="MCU_Nordic:nRF52840", ref="U2")
    cap = Component(symbol="Device:C", ref="C2", value="100nF")

@circuit(name="main")
def main():
    """System combining power and MCU"""
    # Only subcircuits in root - creates hierarchical structure
    power_instance = power_supply()
    mcu_instance = microcontroller()

circuit = main()
circuit.generate_kicad_project(project_name="system")
```

**Generated KiCad Files:**
```
system/
├── system.kicad_pro
├── system.kicad_sch          (top-level sheet with 2 sheet symbols)
├── system.kicad_pcb
├── power_supply.kicad_sch    (child sheet 1)
└── microcontroller.kicad_sch (child sheet 2)
```

### Pattern 2: Mixed Design (Components + Subcircuits in Root)

The root circuit has both components and subcircuits.

```python
@circuit(name="regulator")
def regulator_circuit():
    """3.3V regulator subcircuit"""
    u = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U")
    c_in = Component(symbol="Device:C", ref="C", value="10uF")
    c_out = Component(symbol="Device:C", ref="C", value="22uF")

@circuit(name="main")
def main():
    """Root circuit with both components and subcircuits"""
    # Components in root
    r1 = Component(symbol="Device:R", ref="R", value="10k")
    
    # Subcircuits in root
    pwr = regulator_circuit()
```

**Generated KiCad Files:**
```
main/
├── main.kicad_pro
├── main.kicad_sch           (contains R1 + sheet symbol for regulator)
├── main.kicad_pcb
└── regulator.kicad_sch      (contains U, C1, C2)
```

### Pattern 3: Simple Design (Only Components, No Subcircuits)

Single flat sheet with all components.

```python
@circuit(name="blinker")
def blinker():
    """Simple LED blinker"""
    mcu = Component(symbol="MCU_Nordic:nRF52840", ref="U1")
    led = Component(symbol="Device:LED", ref="D1")
    res = Component(symbol="Device:R", ref="R1", value="1k")
    # ... connections

circuit = blinker()
circuit.generate_kicad_project(project_name="blinker")
```

**Generated KiCad Files:**
```
blinker/
├── blinker.kicad_pro
├── blinker.kicad_sch        (single sheet with all components)
└── blinker.kicad_pcb
```

---

## Connecting Across Hierarchical Levels

### Pattern: Use Nets to Connect Subcircuits

Subcircuits can share nets with parent circuits to establish connections:

```python
@circuit(name="led")
def led_circuit(vcc, gnd):
    """LED with current-limiting resistor"""
    led = Component(symbol="Device:LED", ref="D", value="red")
    res = Component(symbol="Device:R", ref="R", value="1k")
    
    led[1] += vcc
    res[1] += led[2]
    res[2] += gnd

@circuit(name="main")
def main():
    """System with shared nets"""
    # Define nets shared across hierarchy
    vcc = Net("VCC")
    gnd = Net("GND")
    
    # Power supply in root
    regulator = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U")
    regulator["VI"] += vcc
    regulator["GND"] += gnd
    
    # Subcircuit that uses those nets
    led_instance = led_circuit(vcc, gnd)
```

**How it works:**
1. Nets are created in root circuit
2. Passed to subcircuit functions as parameters
3. Subcircuit components connect to those nets
4. KiCad generates with shared hierarchical nets

---

## Important Details

### Reference Management

Each circuit has its own reference namespace:

```python
# References are local to each circuit
@circuit(name="power")
def power():
    r1 = Component(symbol="Device:R", ref="R1")  # This power's R1
    c1 = Component(symbol="Device:C", ref="C1")

@circuit(name="signal")
def signal():
    r1 = Component(symbol="Device:R", ref="R1")  # This signal's R1 (different)

@circuit(name="main")
def main():
    power_instance = power()      # power's R1, C1
    signal_instance = signal()    # signal's R1 (no collision)
```

**Key Features:**
- References are validated within circuit hierarchy scope
- Parent and child reference managers are linked
- Final references are auto-assigned if you use prefixes (e.g., `ref="R"`)
- No collisions possible - each subcircuit is isolated

### Automatic Instance Naming

When subcircuits are instantiated multiple times, they get auto-incremented names:

```python
@circuit(name="stage")
def amplifier_stage():
    """Single amplifier stage"""
    # ...

@circuit(name="main")
def main():
    """Multi-stage amplifier"""
    stage1 = amplifier_stage()  # Auto-named: stage_1
    stage2 = amplifier_stage()  # Auto-named: stage_2
    stage3 = amplifier_stage()  # Auto-named: stage_3
```

### Function Parameters for Subcircuits

Subcircuits can accept parameters to make them reusable:

```python
@circuit(name="filter")
def rc_filter(vin, vout, gnd, r_ohms="1k", c_farads="1uF"):
    """Configurable RC low-pass filter"""
    r = Component(symbol="Device:R", ref="R", value=r_ohms)
    c = Component(symbol="Device:C", ref="C", value=c_farads)
    
    r[1] += vin
    r[2] += vout
    c[1] += vout
    c[2] += gnd

@circuit(name="main")
def main():
    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")
    
    # Use filter with different values
    filter1 = rc_filter(vin, vout, gnd, "10k", "100nF")   # 160 Hz cutoff
    filter2 = rc_filter(vin, vout, gnd, "100k", "1uF")    # 16 Hz cutoff
```

---

## KiCad Generation Details

### Sheet Files

When you call `generate_kicad_project()`:

1. **Top-level sheet** (`.kicad_sch`): Contains sheet symbols for each subcircuit
2. **Subcircuit sheets** (`subcircuit_name.kicad_sch`): Contains actual components
3. **Project file** (`.kicad_pro`): KiCad project metadata
4. **PCB file** (`.kicad_pcb`): Generated PCB layout (if `generate_pcb=True`)

**File Structure:**
```
project_name/
├── project_name.kicad_pro       # Project metadata
├── project_name.kicad_sch       # Top-level schematic
├── project_name.kicad_pcb       # PCB layout
├── subcircuit1.kicad_sch        # First subcircuit
├── subcircuit2.kicad_sch        # Second subcircuit
└── ...
```

### Placement Algorithm

The generator intelligently chooses layout based on circuit structure:

```python
# From src/circuit_synth/kicad/schematic/project_generator.py

if has_components and has_subcircuits:
    # Mixed: Use unified placement for both
    _generate_root_with_unified_placement(circuit, schematic_path)
elif has_subcircuits:
    # Pure hierarchical: Create separate sheets for each
    _generate_hierarchical_design(circuit, schematic_path)
else:
    # Simple: Single sheet with all components
    _generate_simple_design(circuit, schematic_path)
```

---

## Full Example: Multi-Level Hierarchical Circuit

```python
from circuit_synth import *

# Level 3: Basic building blocks
@circuit(name="resistor_pair")
def resistor_divider(vin, vout, gnd, r1_val="10k", r2_val="10k"):
    """Simple voltage divider"""
    r1 = Component(symbol="Device:R", ref="R", value=r1_val)
    r2 = Component(symbol="Device:R", ref="R", value=r2_val)
    
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd

# Level 2: Subsystems
@circuit(name="power_supply")
def power_supply(vbus, vcc_3v3, gnd):
    """3.3V regulator with decoupling"""
    u = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U")
    c_in = Component(symbol="Device:C", ref="C", value="10uF")
    c_out = Component(symbol="Device:C", ref="C", value="22uF")
    
    u["VI"] += vbus
    u["VO"] += vcc_3v3
    u["GND"] += gnd
    
    c_in[1] += vbus
    c_in[2] += gnd
    c_out[1] += vcc_3v3
    c_out[2] += gnd

@circuit(name="signal_chain")
def signal_chain(vin, vout, gnd):
    """Filter and buffer stage"""
    filter_instance = resistor_divider(vin, vout, gnd, "1k", "1k")

# Level 1: Top-level system
@circuit(name="system")
def system():
    """Complete system"""
    # Shared nets
    vbus = Net("VBUS")
    vcc = Net("VCC_3V3")
    gnd = Net("GND")
    sig_in = Net("SIG_IN")
    sig_out = Net("SIG_OUT")
    
    # Subsystems
    pwr = power_supply(vbus, vcc, gnd)
    sig = signal_chain(sig_in, sig_out, gnd)
    
    # Main circuit components
    conn_in = Component(symbol="Connector:USB_C", ref="J")
    mcu = Component(symbol="MCU_Nordic:nRF52840", ref="U")

# Generate
if __name__ == "__main__":
    circuit = system()
    result = circuit.generate_kicad_project(project_name="multi_level_system")
    print(f"Generated at: {result['project_path']}")
```

**Generated KiCad Structure:**
```
multi_level_system/
├── multi_level_system.kicad_pro
├── multi_level_system.kicad_sch       (top: power_supply, signal_chain sheets + components)
├── multi_level_system.kicad_pcb
├── power_supply.kicad_sch             (level 2: regulator + caps)
└── signal_chain.kicad_sch             (level 2: calls resistor_divider sheet)
    └── resistor_pair.kicad_sch        (level 3: two resistors)
```

---

## API Reference

### Circuit Class Methods

```python
class Circuit:
    # Subcircuit management
    def add_subcircuit(self, subcirc: "Circuit")
    @property
    def subcircuits(self) -> List["Circuit"]
    
    # Reference management
    def add_component(self, comp: "Component")
    def finalize_references(self)
    
    # Net management
    def add_net(self, net: Net)
    @property
    def nets(self) -> Dict[str, Net]
    
    # Generation
    def generate_kicad_project(
        self,
        project_name: str,
        generate_pcb: bool = True,
        force_regenerate: bool = False,
        placement_algorithm: str = "hierarchical",
        **kwargs
    ) -> Dict[str, Any]
```

### @circuit Decorator

```python
@circuit(
    name: Optional[str] = None,     # Circuit name (defaults to function name)
    comments: bool = True            # Extract docstring as annotation
)
def my_circuit():
    """Optional docstring becomes schematic annotation"""
    # Define components and nets here
```

---

## Testing Subcircuits

```python
import pytest
from circuit_synth import *

def test_power_supply_hierarchy():
    """Verify power supply creates proper hierarchy"""
    
    @circuit(name="power")
    def power():
        regulator = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U")
    
    @circuit(name="main")
    def main():
        power_instance = power()
    
    circuit = main()
    
    # Test hierarchy
    assert len(circuit.subcircuits) == 1
    assert circuit.subcircuits[0].name == "power"
    assert circuit.subcircuits[0]._parent is circuit
    
    # Test generation
    result = circuit.generate_kicad_project(project_name="test_hier")
    assert result["success"] == True
    assert result["project_path"].exists()
```

---

## Troubleshooting

### Issue: Reference Collision in Different Sheets

**Problem**: Same reference in parent and child (e.g., both have "R1")

**Solution**: Each sheet has its own reference namespace - this is allowed!
```python
@circuit(name="child")
def child():
    r1 = Component(symbol="Device:R", ref="R1")  # Child's R1

@circuit(name="main")
def main():
    r1 = Component(symbol="Device:R", ref="R1")  # Parent's R1
    child_instance = child()  # No collision - different sheets
```

### Issue: Subcircuits Not Appearing in KiCad

**Solution**: Subcircuits must be instantiated (called as functions):
```python
@circuit(name="main")
def main():
    # WRONG: just defining function
    # define_subcircuit()  # This doesn't create the circuit!
    
    # CORRECT: calling function
    sub = my_subcircuit()  # This creates and registers it
```

### Issue: Nets Not Shared Between Sheets

**Solution**: Pass nets as function parameters:
```python
@circuit(name="child")
def child(vcc, gnd):  # Accept nets as parameters
    comp = Component(symbol="Device:R", ref="R")
    comp[1] += vcc   # Use passed nets
    comp[2] += gnd

@circuit(name="main")
def main():
    vcc = Net("VCC")
    gnd = Net("GND")
    
    child_instance = child(vcc, gnd)  # Pass nets to child
```

---

## Files to Explore

Core implementation:
- `/src/circuit_synth/core/circuit.py` - Circuit class with subcircuit support
- `/src/circuit_synth/core/decorators.py` - @circuit decorator implementation
- `/src/circuit_synth/kicad/schematic/sheet_manager.py` - KiCad sheet creation
- `/src/circuit_synth/kicad/schematic/project_generator.py` - Hierarchical generation logic

Examples:
- `/tests/kicad_to_python/02_dual_hierarchy/` - Simple 2-level hierarchy
- `/tests/kicad_to_python/03_dual_hierarchy_connected/` - Hierarchy with net connections
- `/tests/kicad_to_python/04_esp32_c6_hierarchical/` - Complex real-world example

Legacy tests (archived but useful):
- `/tests/bidirectional/_archive_legacy_tests/22_add_subcircuit_sheet/` - Subcircuit creation
- `/tests/bidirectional/_archive_legacy_tests/44_subcircuit_hierarchical_ports/` - Sheet pins

