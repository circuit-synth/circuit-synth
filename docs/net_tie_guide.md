# Net-Tie Insertion Guide

## Overview

Net-ties are zero-ohm connections that make component relationships explicit in circuit schematics, particularly for decoupling capacitors and power distribution networks. They improve schematic readability and guide PCB placement without affecting electrical behavior.

## What Are Net-Ties?

A net-tie is a KiCad component that electrically connects two nets together while keeping them logically separate in the schematic. Think of it as a "visible short circuit" that helps document design intent.

### Visual Example

**Without Net-Ties:**
```
VCC_3V3
  |
  +---- C1 ---- GND  (100nF decoupling)
  |
  +---- C2 ---- GND  (10µF bulk)
  |
  +---- U1.VDD
  |
  +---- U1.VDDA
```

**With Net-Ties:**
```
VCC_3V3
  |
  +---- NT1 ---- C1 ---- GND  (clearly decouples U1.VDD)
  |       |
  |       +---- U1.VDD
  |
  +---- NT2 ---- C2 ---- GND  (clearly decouples U1.VDDA)
          |
          +---- U1.VDDA
```

The second schematic makes it immediately obvious which capacitor serves which power pin.

## Benefits

1. **Clear Schematics**: Shows which decoupling cap serves which power pin
2. **Better Placement**: Placement algorithms group components connected via net-ties
3. **Explicit Topology**: Power distribution structure is visible
4. **No Electrical Impact**: Net-ties are zero-ohm connections
5. **Manufacturing Friendly**: Automatically excluded from BOM

## Usage

### Automatic Insertion

Circuit-synth can automatically insert net-ties for decoupling capacitors:

```python
from circuit_synth import Circuit, Component, Net, circuit

@circuit(name="Auto_Net_Ties")
def auto_example(VCC, GND):
    # Create an IC
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )

    # Create decoupling caps
    cap1 = Component(symbol="Device:C", ref="C", value="100nF")
    cap2 = Component(symbol="Device:C", ref="C", value="10uF")

    # Connect everything
    mcu["VDD"] += VCC
    mcu["VSS"] += GND
    cap1["1"] += VCC
    cap1["2"] += GND
    cap2["1"] += VCC
    cap2["2"] += GND

# Create and use the circuit
vcc = Net("VCC_3V3")
gnd = Net("GND")
circuit = auto_example(vcc, gnd)

# Insert net-ties automatically
net_ties = circuit.insert_decoupling_net_ties()
print(f"Inserted {len(net_ties)} net-ties")

# Generate KiCad project
circuit.generate_kicad_project("my_project")
```

### Targeted Insertion

Insert net-ties only for a specific component:

```python
# Only insert net-ties for the MCU
mcu = Component(symbol="MCU_ST_STM32F4:STM32F411CEUx", ref="U1")
# ... connect everything ...

net_ties = circuit.insert_decoupling_net_ties(target_component=mcu)
```

### Manual Insertion

For custom grouping (filtering caps, timing networks, etc.):

```python
from circuit_synth import Circuit, Component, Net

circuit = Circuit(name="Manual_Example")
vcc = Net("VCC_3V3")
gnd = Net("GND")

# Create components to group
cap1 = Component(symbol="Device:C", ref="C1", value="1uF")
cap2 = Component(symbol="Device:C", ref="C2", value="100nF")

cap1["2"] += gnd
cap2["2"] += gnd

# Manually insert net-tie to group them together
net_tie = circuit.insert_net_tie(
    component1=cap1,
    pin1="1",
    component2=cap2,
    pin2="1",
    power_net=vcc
)
```

### Configuration

Customize net-tie insertion behavior:

```python
from circuit_synth import NetTieConfig

config = NetTieConfig(
    auto_decoupling=True,           # Enable auto-insertion
    min_decoupling_cap=1e-9,        # 1nF minimum
    max_decoupling_cap=1e-3,        # 1000uF maximum
    net_tie_prefix="NT",            # Reference prefix
    net_tie_symbol="Device:NetTie_2"  # KiCad symbol
)

net_ties = circuit.insert_decoupling_net_ties(config=config)
```

## How It Works

### Automatic Detection

Circuit-synth identifies decoupling capacitors by looking for:

1. **Component Type**: Must be a capacitor (symbol contains `Device:C`)
2. **Pin Connections**:
   - One pin connected to a power net (VCC, VDD, etc.)
   - Other pin connected to ground (GND, VSS, etc.)
3. **Capacitance Value**: Within decoupling range (default: 1nF to 1000µF)
4. **Associated IC**: Shares a power net with an IC component

### Net-Tie Insertion Process

For each detected decoupling capacitor:

1. Create a net-tie component (excluded from BOM)
2. Create intermediate net: `{power_net}_to_{cap_ref}`
3. Reconnect topology:
   - IC power pin → Original power net
   - Capacitor positive pin → Intermediate net
   - Net-tie pin 1 → Intermediate net
   - Net-tie pin 2 → Original power net
   - Capacitor negative pin → Ground

Result: **IC_PIN → CAP → NET_TIE → POWER_RAIL**

### Placement Integration

Net-tie groupings are used by placement algorithms:

```python
# Extract net-tie groupings for placement
from circuit_synth.pcb.placement.grouping import extract_net_tie_groupings

groupings = extract_net_tie_groupings(circuit)
# Returns: {'C1': ['U1', 'NT1'], 'U1': ['C1', 'NT1'], ...}

# Use with force-directed placement
placer.place(
    components=components,
    connections=connections,
    net_tie_groups=groupings,
    net_tie_weight=5.0  # Higher weight = stronger attraction
)
```

Components grouped by net-ties receive stronger attractive forces in the placement algorithm, encouraging them to be placed adjacent to each other.

## Power Net Detection

Circuit-synth automatically recognizes common power net naming patterns:

**Power Nets:**
- VCC, VDD, VEE, VBUS, VBAT
- V3V3, V5V, V12V, V1V8, V2V5
- +3V3, +5V, +12V
- VDDA, VDDD, VDDIO, VDDCORE

**Ground Nets:**
- GND, VSS, VSSA
- AGND, DGND

You can extend detection by using these naming patterns for custom power rails.

## API Reference

### Circuit Methods

#### `circuit.insert_decoupling_net_ties(target_component=None, config=None)`

Insert net-ties for decoupling capacitors.

**Parameters:**
- `target_component` (Component, optional): Only process caps for this component
- `config` (NetTieConfig, optional): Configuration for net-tie insertion

**Returns:**
- `List[Component]`: List of inserted net-tie components

**Example:**
```python
net_ties = circuit.insert_decoupling_net_ties()
```

#### `circuit.insert_net_tie(component1, pin1, component2, pin2, power_net)`

Manually insert a net-tie between two components.

**Parameters:**
- `component1` (Component): First component to group
- `pin1` (str): Pin name on component1
- `component2` (Component): Second component to group
- `pin2` (str): Pin name on component2
- `power_net` (Net): Power net they connect to via net-tie

**Returns:**
- `Component`: The inserted net-tie component

**Example:**
```python
net_tie = circuit.insert_net_tie(cap1, "1", cap2, "1", vcc)
```

#### `circuit.get_net_tie_groups()`

Get component groupings defined by net-ties.

**Returns:**
- `Dict[str, List[str]]`: Mapping of net-tie refs to grouped component refs

**Example:**
```python
groups = circuit.get_net_tie_groups()
# {'NT1': ['C1', 'U1'], 'NT2': ['C2', 'U2']}
```

### NetTieConfig Class

Configuration for net-tie insertion behavior.

**Attributes:**
- `auto_decoupling` (bool): Enable automatic insertion (default: True)
- `min_decoupling_cap` (float): Minimum capacitance in farads (default: 1e-9)
- `max_decoupling_cap` (float): Maximum capacitance in farads (default: 1e-3)
- `net_tie_prefix` (str): Reference prefix for net-ties (default: "NT")
- `net_tie_symbol` (str): KiCad symbol to use (default: "Device:NetTie_2")
- `net_tie_footprint` (str): Footprint (default: "" for schematic-only)

**Example:**
```python
config = NetTieConfig(
    auto_decoupling=True,
    min_decoupling_cap=1e-9,  # 1nF
    max_decoupling_cap=1e-3,  # 1000µF
    net_tie_prefix="NT"
)
```

## Best Practices

### When to Use Net-Ties

**Good Use Cases:**
- Decoupling capacitors for multi-power-domain ICs
- Multiple ICs sharing the same power rail
- Filter networks with multiple caps
- Making power distribution topology explicit

**Not Needed:**
- Single IC with one decoupling cap (relationship is obvious)
- Very simple circuits (< 5 components)
- When schematic clarity isn't important

### Naming Conventions

Follow KiCad's standard power net naming:
- Use `VCC_3V3`, `VDD_CORE`, etc. for power rails
- Use `GND`, `AGND`, `DGND` for ground
- Consistent naming helps automatic detection

### Configuration Tips

**Capacitance Range:**
- Default range (1nF - 1000µF) works for most designs
- Narrow range if you have special-purpose caps
- Extend range for power supply designs with large bulk caps

**Net-Tie Weight:**
- Default weight of 5.0 works well for most layouts
- Increase for tighter grouping (up to 10.0)
- Decrease if placement is too constrained (down to 2.0)

## Examples

See `examples/net_tie_example.py` for complete working examples:

1. **MCU with automatic net-ties**: STM32 with multiple power domains
2. **Multiple ICs**: Per-IC decoupling on shared power rail
3. **Manual insertion**: Custom grouping for filter networks

Run the example:
```bash
cd examples
python net_tie_example.py
```

## Troubleshooting

### Net-ties not inserted

**Possible causes:**
1. Capacitor value outside decoupling range
2. Not connected to power/ground nets
3. Power net name not recognized

**Solutions:**
- Check capacitor values are in range (default: 1nF - 1000µF)
- Verify connections to power and ground
- Use standard power net names (VCC, VDD, etc.)
- Adjust `NetTieConfig` if needed

### Too many net-ties inserted

**Solution:**
- Use `target_component` parameter to limit insertion
- Adjust capacitance range in `NetTieConfig`
- Consider if all caps really need net-ties

### Placement not using net-tie groups

**Solution:**
- Ensure placement algorithm supports net-tie groups
- Check that `extract_net_tie_groupings()` is called
- Pass `net_tie_groups` parameter to placement algorithm

## Technical Details

### KiCad Net-Tie Format

Net-ties use the standard KiCad `Device:NetTie_2` symbol:
- Two passive pins
- Excluded from BOM (`in_bom = no`)
- Included on board (`on_board = yes`)
- Zero-ohm electrical connection

### Database Schema

Net-tie metadata is stored in component `_extra_fields`:
```python
net_tie._extra_fields = {
    'groups_with': 'C1,U1',      # Grouped components
    'associated_ic': 'U1',        # Associated IC
    'exclude_from_bom': True      # BOM exclusion flag
}
```

### Placement Algorithm Integration

Net-tie groups are extracted and passed to placement algorithms as bidirectional mappings:

```python
{
    'C1': ['U1', 'NT1'],
    'U1': ['C1', 'NT1'],
    'NT1': ['C1', 'U1']
}
```

The force-directed placement algorithm applies higher spring constants to net-tie connections, pulling grouped components closer together.

## See Also

- [Component Placement Guide](placement_guide.md)
- [Power Distribution Best Practices](power_design.md)
- [KiCad Integration](kicad_integration.md)
