# Test Fixtures

Shared reference circuits used across multiple test directories.

## Directory Structure

```
fixtures/
├── blank/                     # Empty circuits
│   ├── blank.py              # Python blank circuit
│   └── blank.kicad_pro       # KiCad blank project
│
├── single_resistor/          # One component
│   ├── single_resistor.py
│   └── single_resistor.kicad_pro
│
├── resistor_divider/         # Classic two-component circuit
│   ├── resistor_divider.py   # R1-R2 voltage divider
│   └── resistor_divider.kicad_pro
│
├── hierarchical_simple/      # 2-level hierarchy
│   ├── main.py
│   ├── subcircuit.py
│   └── hierarchical_simple.kicad_pro
│
└── hierarchical_complex/     # 3-level hierarchy
    ├── main.py
    ├── sub1.py
    ├── sub2.py
    └── hierarchical_complex.kicad_pro
```

## Fixture Guidelines

### Naming Convention
- Python files: `<circuit_name>.py`
- KiCad projects: `<circuit_name>.kicad_pro` with matching `.kicad_sch`
- Keep names descriptive and consistent

### Simplicity
- Fixtures should be minimal for their purpose
- Blank = truly empty
- Single resistor = one resistor only
- Resistor divider = exactly R1-R2 with VIN-VOUT-GND

### Manual Creation Required

Most fixtures require manual creation in KiCad:
1. Open KiCad
2. Create new project with fixture name
3. Add components/connections as specified
4. Save in appropriate fixtures directory
5. Commit both `.kicad_pro` and `.kicad_sch` files

### Version Control

**Do commit**:
- `.py` files
- `.kicad_pro` files
- `.kicad_sch` files
- `.kicad_pcb` files (if needed)

**Don't commit**:
- `*-backups/` directories
- Temporary files
- Lock files

## Creating New Fixtures

### 1. Blank Circuit

**Python** (`blank/blank.py`):
```python
from circuit_synth import circuit

@circuit
def blank():
    """Empty circuit for testing foundation."""
    pass
```

**KiCad**:
- New Project → blank
- Don't add any components
- Save

### 2. Single Resistor

**Python** (`single_resistor/single_resistor.py`):
```python
from circuit_synth import circuit, Net
from circuit_synth.components.passives import Device_R

@circuit
def single_resistor():
    """Single resistor test circuit."""
    r1 = Device_R()(value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    GND = Net("GND")
    r1[1] & GND
    r1[2] & GND
```

**KiCad**:
- New Project → single_resistor
- Add resistor R1
  - Value: 10k
  - Footprint: Resistor_SMD:R_0603_1608Metric
- Add power symbol GND
- Connect R1 pins to GND
- Save

### 3. Resistor Divider

**Python** (`resistor_divider/resistor_divider.py`):
```python
from circuit_synth import circuit, Net
from circuit_synth.components.passives import Device_R

@circuit
def resistor_divider():
    """Classic voltage divider circuit."""
    r1 = Device_R()(value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Device_R()(value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    VIN = Net("VIN")
    VOUT = Net("VOUT")
    GND = Net("GND")

    r1[1] & VIN
    r1[2] & VOUT
    r2[1] & VOUT
    r2[2] & GND
```

**KiCad**:
- New Project → resistor_divider
- Add resistors R1, R2 (both 10k, R_0603)
- Add power symbols: VIN, GND
- Add label: VOUT
- Wire: VIN → R1 → VOUT → R2 → GND
- Save

### 4. Hierarchical Simple

**To be created** - See test_09 for specifications

### 5. Hierarchical Complex

**To be created** - See test_09 for specifications

## Fixture Validation

Before using a fixture in tests, validate:
- ✅ Python file syntax is valid (can be imported)
- ✅ KiCad project opens without errors
- ✅ All referenced components exist in libraries
- ✅ All footprints are valid
- ✅ Netlist can be exported (`kicad-cli`)

## Updating Fixtures

If you modify a fixture:
1. Update both Python and KiCad versions
2. Run all tests that use the fixture
3. Update fixture documentation here
4. Commit changes with clear message

---

**Status**: 🚧 Manual creation required
**Estimated Time**: 1-2 hours for all fixtures
