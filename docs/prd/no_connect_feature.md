# PRD: No-Connect Pin Marking Feature

**Status:** Draft
**Created:** 2025-10-29
**Owner:** circuit-synth core team
**Priority:** Medium (blocks test 28)

---

## Executive Summary

Add support for marking component pins as "no-connect" (NC) in circuit-synth, allowing users to explicitly document unused pins and satisfy KiCad ERC checks. This feature uses a clean, net-like syntax with a special `NoConnect` object.

---

## Problem Statement

### Current State
Users cannot mark unused component pins as no-connect in circuit-synth. When components have unused pins (e.g., unused op-amp unit, extra logic gates), KiCad's ERC checker reports warnings about unconnected pins.

### User Pain Points
1. **ERC warnings on valid designs** - Unused pins trigger false-positive ERC errors
2. **No way to document intent** - Can't distinguish between "forgot to connect" vs "intentionally unused"
3. **Multi-unit component complexity** - Dual/quad op-amps, logic gates often have unused units
4. **Professional workflow blocker** - Real designs need ERC clean for manufacturing

### Example Scenario
```python
# User wants to use only Unit A of dual op-amp LM358
u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1", ...)

# Unit A pins 1,2,3 are connected
net_in += u1[3]
net_out += u1[1]
net_fb += u1[2]

# Unit B pins 5,6,7 are unused - HOW TO MARK AS NC?
# Currently: No solution, ERC will complain
```

---

## Goals

### Primary Goals
1. **Clean syntax** - Mark pins as NC using intuitive, net-like connection syntax
2. **ERC compliance** - Generate proper KiCad no-connect flags to satisfy ERC
3. **Bidirectional sync** - Round-trip NC flags between Python ↔ KiCad
4. **Documentation clarity** - Make design intent explicit in code

### Non-Goals
- Auto-detecting unused pins (user must explicitly mark)
- Converting between NC and connected states automatically
- Special handling for power pins (use existing power net logic)

---

## User Stories

### Story 1: Mark unused op-amp unit
**As a** circuit designer
**I want to** mark unused op-amp pins as no-connect
**So that** ERC checks pass without false warnings

```python
from circuit_synth import Component, Net, NoConnect

# Create dual op-amp
u1 = Component(symbol="Amplifier_Operational:LM358", ref="U1", ...)

# Use Unit A
net_in += u1[3]
net_out += u1[1]

# Mark Unit B as unused
nc = NoConnect()
u1[5] += nc  # Pin 5: no-connect
u1[6] += nc  # Pin 6: no-connect
u1[7] += nc  # Pin 7: no-connect
```

### Story 2: Import existing NC flags from KiCad
**As a** circuit designer
**I want to** import schematics with existing NC flags
**So that** manual KiCad edits are preserved

```python
# User manually adds NC flags in KiCad GUI
# Sync back to Python → NC flags should be preserved
circuit_obj = load_circuit_from_kicad("project.kicad_sch")

# Verify NC flags imported
assert u1[5].has_no_connect  # True if pin marked NC in KiCad
```

### Story 3: Remove NC flag (connect previously unused pin)
**As a** circuit designer
**I want to** connect a previously NC-marked pin
**So that** I can evolve my design

```python
# Initially marked as NC
nc = NoConnect()
u1[5] += nc

# Later: decide to use Unit B
# Connect pin 5 to a net → NC flag should be removed automatically
net_signal = Net("SIGNAL_B")
net_signal += u1[5]  # NC flag removed, pin now connected
```

---

## Proposed Solution

### API Design

#### NoConnect Class
```python
class NoConnect:
    """Special marker object for no-connect pins.

    Usage:
        nc = NoConnect()
        component[pin] += nc  # Mark pin as no-connect

    Behavior:
        - Can be reused across multiple pins
        - Not a real net (doesn't create electrical connection)
        - Generates KiCad (no_connect) directive on pin
    """

    def __init__(self):
        """Create a no-connect marker."""
        self._uuid = uuid.uuid4()  # For KiCad synchronization

    def __repr__(self):
        return "NoConnect()"
```

#### Pin Connection Behavior
```python
# When user does: component[pin] += nc
# Pin class __iadd__ method detects NoConnect object
# Sets internal flag: pin._no_connect = True
# Disconnects pin from any existing net
```

### KiCad Integration

#### Schematic Format (.kicad_sch)
```lisp
(symbol (lib_id "Amplifier_Operational:LM358")
  (uuid "...")

  (pin "5"
    (uuid "pin-uuid")
    (no_connect (at 120.65 95.25) (uuid "nc-uuid"))
  )

  (pin "6"
    (uuid "pin-uuid")
    (no_connect (at 120.65 90.17) (uuid "nc-uuid"))
  )
)
```

**Key elements:**
- `(no_connect ...)` directive inside pin definition
- Position `(at x y)` - placed on pin location
- UUID for synchronization tracking

#### Writer Behavior
```python
# In kicad_writer.py
def _write_component_pins(self, component):
    for pin in component.pins:
        if pin.has_no_connect:
            # Write (no_connect (at x y) (uuid "..."))
            self._write_no_connect_flag(pin)
```

#### Synchronizer Behavior
```python
# In synchronizer.py
def _sync_no_connect_flags(self, python_pin, kicad_pin):
    """Bidirectional sync of no-connect flags."""

    # Python → KiCad: Add NC flag if needed
    if python_pin.has_no_connect and not kicad_pin.has_no_connect:
        kicad_pin.add_no_connect_flag()

    # KiCad → Python: Remove NC if pin now connected
    if kicad_pin.has_no_connect and python_pin.is_connected:
        kicad_pin.remove_no_connect_flag()

    # KiCad → Python: Import NC flag
    if kicad_pin.has_no_connect and not python_pin.is_connected:
        python_pin.mark_no_connect()
```

### Internal Data Model

#### Pin Class Extensions
```python
@dataclass
class Pin:
    """Component pin with connection tracking."""

    number: str
    name: str
    component: 'Component'

    # New attributes:
    _no_connect: bool = False
    _no_connect_uuid: Optional[str] = None  # For KiCad sync

    @property
    def has_no_connect(self) -> bool:
        """Check if pin is marked as no-connect."""
        return self._no_connect

    def mark_no_connect(self, nc: 'NoConnect'):
        """Mark this pin as no-connect."""
        self._no_connect = True
        self._no_connect_uuid = str(nc._uuid)
        self._disconnect_from_nets()  # Remove from any nets

    def clear_no_connect(self):
        """Clear no-connect flag."""
        self._no_connect = False
        self._no_connect_uuid = None

    def __iadd__(self, other):
        """Pin connection operator: pin += net or pin += NoConnect()"""
        if isinstance(other, NoConnect):
            self.mark_no_connect(other)
            return self
        elif isinstance(other, Net):
            self.clear_no_connect()  # Remove NC if connecting
            self._connect_to_net(other)
            return self
        else:
            raise TypeError(f"Cannot connect pin to {type(other)}")
```

---

## Technical Design

### Architecture

```
User Python Code
     ↓
  NoConnect() object
     ↓
  Pin.__iadd__() detects NoConnect
     ↓
  Pin._no_connect = True
     ↓
  KiCad Writer generates (no_connect ...)
     ↓
  KiCad .kicad_sch file
     ↓
  Synchronizer reads (no_connect ...)
     ↓
  Round-trip preservation ✓
```

### Key Components

#### 1. NoConnect Class
**File:** `src/circuit_synth/core/no_connect.py`

```python
"""No-connect marker for unused pins."""

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pin import Pin


class NoConnect:
    """Marker object for no-connect pins.

    Example:
        >>> nc = NoConnect()
        >>> component[5] += nc  # Mark pin 5 as NC
        >>> component[6] += nc  # Reuse same NC marker
    """

    def __init__(self):
        self._uuid = uuid.uuid4()

    def __repr__(self):
        return "NoConnect()"

    def __str__(self):
        return "NC"
```

#### 2. Pin Class Modifications
**File:** `src/circuit_synth/core/pin.py`

```python
# Add attributes:
_no_connect: bool = False
_no_connect_uuid: Optional[str] = None

# Add methods:
def mark_no_connect(self, nc: NoConnect) -> None: ...
def clear_no_connect(self) -> None: ...
@property
def has_no_connect(self) -> bool: ...

# Modify __iadd__ to handle NoConnect
```

#### 3. Writer Integration
**File:** `src/circuit_synth/kicad/kicad_writer.py`

```python
def _write_component_pin(self, pin, position):
    """Write pin with optional no-connect flag."""

    # Write pin definition
    self._write_pin_geometry(pin)

    # Add no-connect if flagged
    if pin.has_no_connect:
        nc_x, nc_y = self._calculate_nc_position(pin, position)
        self._write_no_connect(nc_x, nc_y, pin._no_connect_uuid)

def _write_no_connect(self, x, y, nc_uuid):
    """Write KiCad no-connect directive."""
    self.write(f'(no_connect (at {x} {y}) (uuid "{nc_uuid}"))')
```

#### 4. Synchronizer Integration
**File:** `src/circuit_synth/kicad/synchronizer.py`

```python
def _sync_pin_no_connect(self, py_pin, kicad_pin):
    """Sync no-connect flags bidirectionally."""

    # Python → KiCad: Add NC if missing
    if py_pin.has_no_connect and not self._kicad_has_nc(kicad_pin):
        self._add_kicad_no_connect(kicad_pin, py_pin._no_connect_uuid)
        self._changes.append(f"➕ Added no-connect: {py_pin}")

    # Python → KiCad: Remove NC if pin connected
    elif not py_pin.has_no_connect and self._kicad_has_nc(kicad_pin):
        self._remove_kicad_no_connect(kicad_pin)
        self._changes.append(f"➖ Removed no-connect: {py_pin}")

    # KiCad → Python: Import NC flag
    elif self._kicad_has_nc(kicad_pin) and not py_pin.is_connected:
        nc_uuid = self._extract_nc_uuid(kicad_pin)
        py_pin._no_connect = True
        py_pin._no_connect_uuid = nc_uuid
        self._changes.append(f"📥 Imported no-connect: {py_pin}")
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
**Goal:** Basic NoConnect functionality working

**Tasks:**
1. Create `NoConnect` class (`src/circuit_synth/core/no_connect.py`)
2. Extend `Pin` class with NC attributes and methods
3. Modify `Pin.__iadd__()` to handle NoConnect objects
4. Add unit tests for Pin + NoConnect interaction
5. Update `__init__.py` exports

**Acceptance Criteria:**
- `nc = NoConnect()` creates object
- `pin += nc` marks pin as no-connect
- `pin.has_no_connect` returns True after marking
- Connecting pin to net clears NC flag

### Phase 2: KiCad Writer (Week 2)
**Goal:** Generate valid no-connect directives

**Tasks:**
1. Add `_write_no_connect()` to `kicad_writer.py`
2. Calculate NC position based on pin location
3. Integrate NC writing into component pin output
4. Test with real KiCad (open in GUI, verify ERC)

**Acceptance Criteria:**
- Generated `.kicad_sch` contains `(no_connect ...)` directives
- KiCad opens schematic without errors
- ERC passes with NC flags on unused pins
- NC symbols visible in KiCad GUI (small X on pins)

### Phase 3: Synchronizer (Week 3)
**Goal:** Bidirectional sync of NC flags

**Tasks:**
1. Add NC parsing to KiCad schematic reader
2. Implement `_sync_pin_no_connect()` in synchronizer
3. Handle NC → connected transition (remove NC)
4. Handle connected → NC transition (add NC)
5. Import existing NC flags from KiCad

**Acceptance Criteria:**
- Python NC flag → KiCad NC directive (sync adds)
- KiCad NC directive → Python flag (import)
- Removing NC in Python removes from KiCad
- Connecting NC pin in Python removes NC flag
- Position preservation works with NC changes

### Phase 4: Test 28 Integration (Week 4)
**Goal:** Complete test 28 validation

**Tasks:**
1. Update `opamp_with_unused_pins.py` fixture
2. Create `test_28_add_no_connect.py` automated test
3. Manual validation in KiCad GUI
4. Update test documentation

**Test Workflow:**
```
Step 1: Generate op-amp circuit (Unit B unused)
Step 2: Mark Unit B pins as NC
Step 3: Sync → verify NC flags in KiCad
Step 4: Run ERC → verify passes
```

**Acceptance Criteria:**
- Test 28 passes automated checks
- Manual validation successful
- ERC clean after adding NC flags
- Documentation complete

---

## Success Metrics

### Technical Metrics
- ✅ NoConnect API functional (unit tests passing)
- ✅ KiCad writer generates valid `(no_connect ...)` directives
- ✅ Synchronizer preserves NC flags (bidirectional)
- ✅ Position preservation works with NC changes
- ✅ Test 28 passes automated and manual validation

### User Experience Metrics
- ✅ Clean, intuitive syntax (`pin += nc`)
- ✅ ERC passes with NC-marked pins
- ✅ No manual KiCad editing needed for NC flags
- ✅ Round-trip sync preserves user intent

---

## Testing Strategy

### Unit Tests
```python
# test_no_connect.py

def test_no_connect_creation():
    """NoConnect object can be created."""
    nc = NoConnect()
    assert isinstance(nc, NoConnect)

def test_pin_mark_no_connect():
    """Pin can be marked as no-connect."""
    pin = Pin(number="5", ...)
    nc = NoConnect()
    pin += nc
    assert pin.has_no_connect is True

def test_pin_clear_no_connect_on_net():
    """Connecting pin to net clears NC flag."""
    pin = Pin(number="5", ...)
    nc = NoConnect()
    pin += nc
    assert pin.has_no_connect is True

    net = Net("SIGNAL")
    pin += net
    assert pin.has_no_connect is False
    assert pin in net.pins

def test_no_connect_reusable():
    """Single NoConnect object can mark multiple pins."""
    nc = NoConnect()
    pin1 = Pin(number="5", ...)
    pin2 = Pin(number="6", ...)

    pin1 += nc
    pin2 += nc

    assert pin1.has_no_connect is True
    assert pin2.has_no_connect is True
```

### Integration Tests
```python
# test_no_connect_integration.py

def test_no_connect_generates_kicad():
    """NoConnect generates valid KiCad directives."""
    circuit = opamp_with_nc_pins()
    circuit.generate_kicad_project(...)

    # Read .kicad_sch
    sch_content = read_file("output.kicad_sch")

    # Verify (no_connect ...) directives present
    assert '(no_connect' in sch_content
    assert 'pin "5"' in sch_content  # Pin 5 has NC

def test_no_connect_sync_adds():
    """Sync adds NC flag to KiCad."""
    # Generate without NC
    circuit = opamp_circuit()
    circuit.generate_kicad_project(...)

    # Add NC in Python
    u1 = circuit.components["U1"]
    nc = NoConnect()
    u1[5] += nc

    # Sync
    circuit.sync()

    # Verify KiCad has NC
    sch = load_kicad_sch("output.kicad_sch")
    assert sch.get_pin("U1", "5").has_no_connect

def test_no_connect_sync_removes():
    """Sync removes NC when pin connected."""
    # Generate with NC
    circuit = opamp_with_nc()
    circuit.generate_kicad_project(...)

    # Connect pin in Python
    u1 = circuit.components["U1"]
    net = Net("SIGNAL")
    net += u1[5]  # Was NC, now connected

    # Sync
    circuit.sync()

    # Verify KiCad NC removed
    sch = load_kicad_sch("output.kicad_sch")
    assert not sch.get_pin("U1", "5").has_no_connect
```

### Manual Test (Test 28)
```bash
cd tests/bidirectional/28_add_no_connect

# Step 1: Generate op-amp circuit
uv run opamp_with_unused_pins.py
open opamp_with_unused_pins/opamp_with_unused_pins.kicad_pro

# Verify:
# - Op-amp rendered correctly (after Issue #407 fixed)
# - Unit A pins connected (1,2,3)
# - Unit B pins unconnected (5,6,7) - NO NC flags yet

# Step 2: Run test to add NC flags
pytest test_28_add_no_connect.py -v

# Step 3: Open in KiCad again
# Verify:
# - Unit B pins now have small X symbols (NC flags)
# - Run ERC → should pass (no unconnected pin warnings)

# Step 4: Test round-trip
# Manually remove NC in KiCad, sync back
# Python should detect NC flag removed
```

---

## Edge Cases & Error Handling

### Edge Case 1: Pin already connected to net
**Scenario:** User tries to mark connected pin as NC

```python
net = Net("SIGNAL")
pin += net  # Pin connected

nc = NoConnect()
pin += nc  # What happens?
```

**Behavior:**
- Disconnect pin from net
- Mark as NC
- Log warning: "Pin was connected to SIGNAL, disconnecting for NC"

### Edge Case 2: Pin marked NC, then connected
**Scenario:** User changes mind, connects NC pin

```python
nc = NoConnect()
pin += nc  # Pin marked NC

net = Net("SIGNAL")
pin += net  # Connect to net
```

**Behavior:**
- Clear NC flag
- Connect to net
- Normal connection (no warning needed)

### Edge Case 3: Multiple NoConnect objects on same pin
**Scenario:** User marks pin twice

```python
nc1 = NoConnect()
nc2 = NoConnect()

pin += nc1
pin += nc2  # Second NC on same pin
```

**Behavior:**
- Replace UUID with nc2's UUID
- Still only one NC flag (idempotent)
- Log debug: "Pin already NC, updating UUID"

### Edge Case 4: Import KiCad NC without Python code
**Scenario:** User manually adds NC in KiCad

**Behavior:**
- Synchronizer detects NC directive in KiCad
- Sets `pin._no_connect = True`
- Preserves NC on sync back
- Log: "📥 Imported no-connect from KiCad: U1 pin 5"

### Edge Case 5: Power pins marked as NC
**Scenario:** User tries to mark power pin as NC

```python
u1 = Component(symbol="Amplifier_Operational:LM358", ...)
nc = NoConnect()
u1[4] += nc  # Pin 4 is V- power pin
```

**Behavior:**
- **Warning:** "Pin 4 (V-) is a power pin, NC may cause issues"
- Still allow (user knows best)
- Note: Power pins should typically connect to power nets, not NC

---

## Documentation Plan

### User Documentation

#### API Reference (`docs/api/no_connect.md`)
```markdown
# NoConnect API

## Overview
Mark component pins as no-connect to satisfy ERC checks.

## Basic Usage
\`\`\`python
from circuit_synth import Component, NoConnect

nc = NoConnect()
component[pin_number] += nc
\`\`\`

## Examples
[Full examples with op-amps, logic gates, etc.]
```

#### Tutorial (`docs/tutorials/unused_pins.md`)
```markdown
# Tutorial: Handling Unused Pins

Learn how to properly mark unused component pins as no-connect.

## When to Use No-Connect
- Unused op-amp units
- Extra logic gates in IC package
- Optional component features
- Deliberate open-collector outputs
```

### Code Documentation
```python
class NoConnect:
    """Marker for no-connect pins.

    No-connect flags explicitly document that a pin is intentionally
    left unconnected. This satisfies KiCad ERC checks and makes design
    intent clear.

    Usage:
        >>> from circuit_synth import Component, NoConnect
        >>>
        >>> # Create component with unused pins
        >>> u1 = Component(symbol="Amplifier_Operational:LM358", ...)
        >>>
        >>> # Mark unused pins as no-connect
        >>> nc = NoConnect()
        >>> u1[5] += nc  # Pin 5: no-connect
        >>> u1[6] += nc  # Pin 6: no-connect
        >>> u1[7] += nc  # Pin 7: no-connect

    Notes:
        - Reusable across multiple pins
        - Disconnects pin from any existing nets
        - Generates KiCad (no_connect) directive
        - Bidirectional sync preserves NC flags

    See Also:
        - Tutorial: docs/tutorials/unused_pins.md
        - Test 28: tests/bidirectional/28_add_no_connect/
    """
```

---

## Risks & Mitigations

### Risk 1: KiCad format changes
**Impact:** Medium
**Probability:** Low
**Mitigation:**
- Test against multiple KiCad versions (8.0+)
- Use kicad-cli for validation
- Version detection in parser

### Risk 2: Pin position calculation errors
**Impact:** Low (visual only)
**Probability:** Medium
**Mitigation:**
- NC position follows pin geometry
- Validate with kicad-cli schematic check
- Manual testing in KiCad GUI

### Risk 3: Synchronizer complexity
**Impact:** High
**Probability:** Medium
**Mitigation:**
- Comprehensive unit tests
- Automated bidirectional sync tests
- Test 28 provides end-to-end validation

### Risk 4: User confusion (NC vs disconnected)
**Impact:** Medium
**Probability:** Low
**Mitigation:**
- Clear documentation
- Helpful error messages
- Tutorial with examples

---

## Alternatives Considered

### Alternative 1: Pin method API
```python
# Rejected: Less fluent syntax
u1.pin(5).mark_no_connect()
u1.pin(6).mark_no_connect()
```

**Why rejected:** More verbose, breaks flow

### Alternative 2: Component method API
```python
# Rejected: Bulk operations only
u1.mark_no_connect([5, 6, 7])
```

**Why rejected:** Can't mark pins incrementally

### Alternative 3: Special net name
```python
# Rejected: Conceptually wrong
nc_net = Net("NO_CONNECT")
u1[5] += nc_net
```

**Why rejected:** NC is not a net, causes confusion

### Alternative 4: Pin attribute
```python
# Rejected: Not intuitive
u1[5].no_connect = True
```

**Why rejected:** Inconsistent with net connection syntax

**Winner: Option 2 (NoConnect object)** - Clean, intuitive, reusable

---

## Open Questions

1. **Should NoConnect be a singleton?**
   - Pro: Save memory, one global NC object
   - Con: Harder to track which NC marked which pin
   - **Decision:** Not singleton, allow multiple instances (better for UUID tracking)

2. **Should we auto-detect unused pins?**
   - Pro: Convenience, automatic ERC compliance
   - Con: May mark pins user forgot to connect
   - **Decision:** No auto-detection, explicit only (user must mark)

3. **How to handle NC on bidirectional pins?**
   - Example: I2C SDA/SCL pins sometimes pulled up externally
   - **Decision:** Allow NC, trust user intent (they know circuit requirements)

4. **Should NC prevent future connections?**
   - Should we error if user connects NC pin later?
   - **Decision:** No error, silently clear NC (allow design evolution)

---

## Success Criteria Summary

✅ **Feature Complete When:**
1. NoConnect API implemented and tested
2. KiCad writer generates valid `(no_connect ...)` directives
3. Synchronizer handles bidirectional NC flag sync
4. Test 28 passes (automated + manual validation)
5. Documentation complete (API ref + tutorial)
6. ERC passes with NC-marked pins in KiCad

✅ **User Can:**
1. Mark unused pins as no-connect with `pin += nc`
2. Generate KiCad schematics with NC flags
3. Sync NC changes bidirectionally (Python ↔ KiCad)
4. Pass ERC checks without false warnings
5. Evolve designs (connect/disconnect pins with NC)

---

## Timeline

**Total: 4 weeks**

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1 | Core Infrastructure | NoConnect class + Pin extensions |
| 2 | KiCad Writer | Generate valid NC directives |
| 3 | Synchronizer | Bidirectional sync working |
| 4 | Test 28 + Docs | Complete validation + documentation |

**Milestone 1 (Week 2):** Can generate KiCad with NC flags
**Milestone 2 (Week 3):** Bidirectional sync functional
**Milestone 3 (Week 4):** Test 28 validated, feature complete

---

## Appendix

### KiCad No-Connect Format Reference

```lisp
(kicad_sch (version 20231120) (generator "circuit-synth")

  (symbol (lib_id "Amplifier_Operational:LM358")
    (at 120.65 92.71 0) (unit 1)
    (uuid "component-uuid")

    (pin "1" (uuid "pin1-uuid"))
    (pin "2" (uuid "pin2-uuid"))
    (pin "3" (uuid "pin3-uuid"))
    (pin "4" (uuid "pin4-uuid"))

    (pin "5"
      (uuid "pin5-uuid")
      (no_connect (at 133.35 95.25) (uuid "nc-uuid-1"))
    )

    (pin "6"
      (uuid "pin6-uuid")
      (no_connect (at 133.35 90.17) (uuid "nc-uuid-2"))
    )

    (pin "7"
      (uuid "pin7-uuid")
      (no_connect (at 133.35 85.09) (uuid "nc-uuid-3"))
    )

    (pin "8" (uuid "pin8-uuid"))
  )
)
```

**Key observations:**
- `(no_connect ...)` nested inside `(pin ...)`
- Position `(at x y)` matches pin location
- Each NC has unique UUID for sync tracking
- Multiple NC flags on same component allowed

### Related GitHub Issues
- Issue #407: Multi-unit component rendering (LM358)
- Issue #406: Subcircuit sheet generation (blocks test 22, 24)
- Test 28: Add no-connect (this PRD's implementation target)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-29
**Next Review:** After Phase 1 completion

🤖 Generated with [Claude Code](https://claude.com/claude-code)
