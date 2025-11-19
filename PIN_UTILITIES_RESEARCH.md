# Pin Utilities Research

**Date:** 2025-11-18
**Purpose:** Research skidl's pin utility approach and determine what we can borrow/improve for circuit-synth

---

## Problem Statement

User feedback (Tom Anderson) indicates difficulty knowing what to call component pins when writing circuit functions. Users need an easy way to discover available pins for components before using them in code.

**Current Issue:**
```python
# User doesn't know what pins are available
comp = sch.components.add('RF_Module:ESP32-WROOM-32', 'U1', 'ESP32')
# What pins does this component have? What are they named?
# How do I connect to the SPI pins? The power pins?
```

---

## SKiDL's Approach

### skidl-part-search Command-Line Tool

SKiDL provides a `skidl-part-search` utility for searching and inspecting component libraries.

**Key Features:**
- Interactive mode for browsing components
- Displays pin information in formatted table
- Shows pin numbers, names/aliases, and electrical types

**Example Output:**
```
Showing details for: LM358 from Amplifier_Operational
Part: LM358
Library: Amplifier_Operational
Description: Low-Power, Dual Operational Amplifiers, DIP-8/SOIC-8/TO-99-8

Pins:
┏━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Pin# ┃ Names ┃ Type   ┃
┡━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ 1    │ p1,~  │ OUTPUT │
│ 2    │ -,p2  │ INPUT  │
│ 3    │ +,p3  │ INPUT  │
│ 4    │ p4,V- │ PWRIN  │
│ 5    │ +,p5  │ INPUT  │
│ 6    │ -,p6  │ INPUT  │
│ 7    │ p7,~  │ OUTPUT │
│ 8    │ p8,V+ │ PWRIN  │
└──────┴───────┴────────┘
```

**Usage:**
```bash
# Basic search
skidl-part-search opamp

# Interactive mode
skidl-part-search --interactive

# Table format (requires rich module)
skidl-part-search --table opamp

# Limit results
skidl-part-search --limit 10 opamp
```

### Python show() Function

SKiDL also provides a `show()` function in Python for displaying component pin information programmatically.

---

## User Feedback on SKiDL's Approach

**What user said:**
> "I never liked it since it was terminal based"

This suggests the terminal-based approach has limitations:
- Not integrated into development workflow
- Requires context switching (leave editor, run command, return)
- Not easily accessible when writing code
- Separate from the main API

---

## What We Can Borrow

### Good Aspects of SKiDL's Approach:
1. **Clear pin information display** - Pin number, name, and type
2. **Search functionality** - Find components by keyword
3. **Interactive browsing** - Navigate through results
4. **Formatted output** - Easy to read table format

### What We Should Improve:
1. **Integration** - Make it part of the Python API, not separate CLI
2. **Context** - Show pin info in-place during development
3. **Discoverability** - Easy to find without leaving code
4. **Rich output** - In notebooks/IDEs, show visual representation

---

## Proposed Improvements for circuit-synth/kicad-sch-api

### 1. Python API Integration

Make pin inspection part of the natural API flow:

```python
import kicad_sch_api as ksa

# Option A: Query library before placing component
symbol_info = ksa.get_symbol_info('RF_Module:ESP32-WROOM-32')
symbol_info.show_pins()  # Displays pin table

# Option B: Inspect component after placing
comp = sch.components.add('RF_Module:ESP32-WROOM-32', 'U1', 'ESP32')
comp.show_pins()  # Show pins for this instance

# Option C: Simple pin listing
pins = comp.list_pins()  # Returns list of pin info dicts
for pin in pins:
    print(f"{pin['number']}: {pin['name']} ({pin['type']})")
```

### 2. Interactive Jupyter/Notebook Support

Leverage rich display in notebooks:

```python
# In Jupyter notebook
comp = sch.components.add('RF_Module:ESP32-WROOM-32', 'U1', 'ESP32')
comp.pins  # Displays rich table automatically in notebook
```

### 3. IDE-Friendly Documentation

Make pin info available via docstrings/hints:

```python
# Type hints could include pin information
comp.connect_pin("GND")  # IDE autocomplete shows available pins
```

### 4. Search Functionality

Add library search directly in Python:

```python
import kicad_sch_api as ksa

# Search for components
results = ksa.search_symbols("esp32")
for result in results:
    print(f"{result.lib_id}: {result.description}")

# Get details
symbol = results[0]
symbol.show_pins()
```

---

## Implementation Approach

### Phase 1: Basic Pin Listing (kicad-sch-api)

**Goal:** Make existing pin data easily accessible

**Implementation:**
```python
# In kicad_sch_api/core/components.py
class Component:
    def list_pins(self) -> List[Dict[str, Any]]:
        """
        List all pins for this component.

        Returns:
            List of pin dictionaries with keys:
            - number: Pin number (str)
            - name: Pin name (str)
            - type: Pin electrical type (str)
            - position: Absolute pin position (Point)
        """
        return [
            {
                'number': pin.number,
                'name': pin.name,
                'type': pin.pin_type.value,
                'position': pin.position
            }
            for pin in self.pins
        ]

    def show_pins(self) -> None:
        """Display pin information in readable format."""
        from rich.console import Console
        from rich.table import Table

        table = Table(title=f"Pins for {self.reference} ({self.lib_id})")
        table.add_column("Pin#", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Type", style="green")

        for pin in self.pins:
            table.add_row(pin.number, pin.name, pin.pin_type.value)

        console = Console()
        console.print(table)
```

### Phase 2: Library Inspection (kicad-sch-api)

**Goal:** Inspect symbols before placing them

**Implementation:**
```python
# In kicad_sch_api/library/cache.py
class SymbolLibraryCache:
    def get_symbol_info(self, lib_id: str) -> SymbolInfo:
        """
        Get detailed symbol information without placing it.

        Args:
            lib_id: Library identifier (e.g., 'Device:R')

        Returns:
            SymbolInfo object with pins, description, etc.
        """
        symbol_def = self.get_symbol(lib_id)
        return SymbolInfo(symbol_def)

class SymbolInfo:
    """Read-only symbol information for inspection."""

    def __init__(self, symbol_def: SymbolDefinition):
        self._def = symbol_def

    @property
    def pins(self) -> List[PinInfo]:
        """List of pin information."""
        return [PinInfo(p) for p in self._def.pins]

    def show_pins(self) -> None:
        """Display pin table."""
        # Similar to Component.show_pins()
```

### Phase 3: Search Functionality (kicad-sch-api)

**Goal:** Search library for components

**Implementation:**
```python
# In kicad_sch_api/__init__.py
def search_symbols(
    query: str,
    library: Optional[str] = None,
    limit: int = 20
) -> List[SymbolSearchResult]:
    """
    Search for symbols in KiCAD libraries.

    Args:
        query: Search term (searches names and descriptions)
        library: Optional library name to restrict search
        limit: Maximum results to return

    Returns:
        List of matching symbols with basic info
    """
    cache = get_symbol_cache()
    results = cache.search(query, library, limit)
    return results
```

### Phase 4: Rich Display Integration (circuit-synth)

**Goal:** Beautiful display in notebooks and IDEs

**Implementation:**
```python
# Add _repr_html_ for Jupyter
class Component:
    def _repr_html_(self):
        """Rich HTML display for Jupyter notebooks."""
        html = f"<h3>{self.reference}: {self.lib_id}</h3>"
        html += "<table><tr><th>Pin#</th><th>Name</th><th>Type</th></tr>"
        for pin in self.pins:
            html += f"<tr><td>{pin.number}</td><td>{pin.name}</td><td>{pin.pin_type.value}</td></tr>"
        html += "</table>"
        return html
```

---

## Testing Strategy

### Unit Tests
```python
def test_list_pins():
    """Test pin listing returns correct data."""
    sch = ksa.create_schematic("Test")
    comp = sch.components.add('Device:R', 'R1', '10k')
    pins = comp.list_pins()

    assert len(pins) == 2
    assert pins[0]['number'] in ['1', '2']
    assert 'name' in pins[0]
    assert 'type' in pins[0]

def test_show_pins_display():
    """Test pin display generates output."""
    sch = ksa.create_schematic("Test")
    comp = sch.components.add('Device:R', 'R1', '10k')
    # Should not raise exception
    comp.show_pins()
```

### Reference Tests
```python
def test_esp32_pin_listing():
    """Verify ESP32 pins are correctly listed."""
    sch = ksa.create_schematic("Test")
    esp32 = sch.components.add('RF_Module:ESP32-WROOM-32', 'U1', 'ESP32')
    pins = esp32.list_pins()

    # ESP32-WROOM-32 should have 38 pins
    assert len(pins) >= 38

    # Check for known pins
    pin_numbers = {p['number'] for p in pins}
    assert '1' in pin_numbers  # GND
    assert '2' in pin_numbers  # 3V3
```

---

## Questions for User

1. **Which implementation priority?**
   - Start with basic `list_pins()` and `show_pins()` on Component?
   - Or start with library search functionality?

2. **Display format preference?**
   - Simple print() output?
   - Rich tables (requires rich library dependency)?
   - Both with fallback?

3. **Scope for initial release?**
   - Just Component.list_pins() and Component.show_pins()?
   - Include library inspection (get_symbol_info)?
   - Include search functionality?

4. **Integration with circuit-synth?**
   - Keep all functionality in kicad-sch-api?
   - Add circuit-synth-specific utilities?

---

## Recommendations

### Immediate Action (Phase 1)
1. Add `Component.list_pins()` method to kicad-sch-api
2. Add `Component.show_pins()` method with simple print output
3. Document in RECIPES.md with examples
4. Release as patch version (0.5.6)

### Short-term (Phase 2)
1. Add library inspection: `ksa.get_symbol_info(lib_id)`
2. Add SymbolInfo class with pin listing
3. Release as minor version (0.6.0)

### Medium-term (Phase 3)
1. Add search functionality: `ksa.search_symbols(query)`
2. Add rich table display (optional dependency)
3. Add Jupyter notebook support

---

## Related Issues

- **Issue #1:** Missing `has_property()` method (related to property inspection)
- **Issue #2:** Pin enumeration utility (THIS DOCUMENT)
- **Issue #3:** Design checking utilities (see DESIGN_CHECKING_RESEARCH.md)

---

## Next Steps

1. Get user feedback on approach
2. Create GitHub issue for pin utilities
3. Implement Phase 1 (list_pins + show_pins)
4. Write tests
5. Update documentation
6. Release to PyPI
