# KiCad-sch-api Integration

## Overview

Circuit-synth integrates with the modern **kicad-sch-api** PyPI package to provide professional KiCad schematic generation. The kicad-sch-api was extracted from circuit-synth as a valuable standalone tool for the broader community.

## Architecture

### Hybrid Approach

Circuit-synth uses a hybrid architecture that combines the best of both systems:

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Legacy    │ ──►│   Positioned     │ ──►│  kicad-sch-api  │
│ Positioning │    │   Component      │    │  File Writing   │
│   System    │    │     Data         │    │                 │
└─────────────┘    └──────────────────┘    └─────────────────┘
      │                      │                       │
      │                      │                       ▼
      │                      │              ┌─────────────────┐
      │                      │              │  Professional   │
      │                      │              │ .kicad_sch Files│
      │                      │              └─────────────────┘
      │                      │
      ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Intelligent File Writer Selection              │
│  • Main/Hierarchical sheets ────────► Legacy writer        │
│  • Component sheets ─────────────────► kicad-sch-api       │
└─────────────────────────────────────────────────────────────┘
```

### Division of Responsibilities

#### Legacy System Handles:
- **Component positioning**: Calculates optimal component placement with collision detection
- **Hierarchical structure**: Manages multi-sheet designs and sheet symbols
- **Net connections**: Resolves hierarchical labels and connectivity
- **S-expression parsing**: Extracts positioned component data from generated schematics

#### kicad-sch-api Handles:
- **Professional file writing**: Generates industry-standard .kicad_sch files
- **Symbol library integration**: Full access to KiCad's extensive symbol libraries
- **Modern KiCad compatibility**: Works with KiCad v7.0+ file formats
- **Clean formatting**: Proper indentation and structure

## Configuration

### Automatic Detection

The integration automatically detects kicad-sch-api availability:

```python
# In src/circuit_synth/kicad/config.py
def is_kicad_sch_api_available() -> bool:
    """Check if kicad-sch-api is available"""
    try:
        import kicad_sch_api
        return True
    except ImportError:
        return False

def get_recommended_generator() -> str:
    """Get recommended schematic generator"""
    if KiCadConfig.use_modern_sch_api() and is_kicad_sch_api_available():
        return "modern"
    return "legacy"
```

### Version Requirements

- **kicad-sch-api**: >= 0.1.1 (PyPI package)
- **packaging**: >= 21.0 (for version checking)

Add to your `pyproject.toml`:
```toml
dependencies = [
    "kicad-sch-api>=0.1.1",
    "packaging>=21.0",
]
```

## Implementation Details

### Intelligent File Writer Selection

The system automatically chooses the appropriate writer based on schematic content:

```python
# In src/circuit_synth/kicad/sch_gen/schematic_writer.py
def write_schematic_file(schematic_expr: list, out_path: str):
    """Write schematic using optimal approach"""
    if is_kicad_sch_api_available():
        has_sheets = _contains_sheet_symbols(schematic_expr)
        filename = Path(out_path).name
        is_main_schematic = not ('/' in filename or filename.count('.') > 1)
        
        if has_sheets or is_main_schematic:
            logger.info(f"Using legacy writer for hierarchical schematic: {out_path}")
            return _write_with_legacy_writer(schematic_expr, out_path)
        else:
            logger.info(f"Using modern kicad-sch-api for component schematic: {out_path}")
            return _write_with_modern_api(schematic_expr, out_path)
    else:
        return _write_with_legacy_writer(schematic_expr, out_path)
```

### Positioned Component Data Extraction

The modern generator extracts positioned components from legacy S-expressions:

```python
# In src/circuit_synth/kicad/sch_gen/modern_generator.py
def _extract_positioned_components(self, schematic_expr: list) -> List[Dict]:
    """Extract positioned component data from S-expression"""
    components = []
    for item in schematic_expr:
        if isinstance(item, list) and len(item) > 0 and item[0] == 'symbol':
            component_data = self._parse_symbol_data(item)
            if component_data:
                components.append(component_data)
    return components
```

### Professional File Generation

The modern API generates clean, properly formatted KiCad files:

```python
def write_positioned_schematic(self, positioned_components: List[Dict], 
                             nets: List[Dict], title_info: Dict = None) -> str:
    """Write positioned schematic with modern API"""
    schematic = Schematic()
    
    # Add components with positions
    for comp_data in positioned_components:
        symbol = self._create_positioned_symbol(comp_data)
        schematic.add_symbol(symbol)
    
    # Generate professional output
    return schematic.to_kicad()
```

## Benefits

### For Circuit-synth Users
- **Automatic integration**: No configuration required, works transparently
- **Professional output**: Industry-standard KiCad files
- **Better compatibility**: Works with modern KiCad versions
- **Improved performance**: Optimized schematic generation

### For the Community
- **Standalone tool**: kicad-sch-api can be used independently
- **Python KiCad integration**: Easier programmatic KiCad file generation
- **Open source**: Available for other projects and tools
- **Community development**: Shared maintenance and improvement

## Standalone kicad-sch-api Usage

The kicad-sch-api package is valuable as a standalone tool:

```bash
pip install kicad-sch-api
```

```python
from kicad_sch_api import Schematic, SchematicSymbol, Position

# Create a simple schematic
schematic = Schematic()

# Add a resistor
resistor = SchematicSymbol("Device:R")
resistor.set_position(Position(100, 100))
resistor.set_reference("R1")
resistor.set_value("1k")
schematic.add_symbol(resistor)

# Generate KiCad file
kicad_content = schematic.to_kicad()
with open("circuit.kicad_sch", "w") as f:
    f.write(kicad_content)
```

## Migration Notes

### From Pure Legacy
- No changes required to existing circuit-synth code
- Integration is automatic when kicad-sch-api is installed
- Fallback to legacy system if package not available

### Performance Improvements
- Component schematics: Generated with modern API (faster, cleaner)
- Hierarchical schematics: Use legacy system for complex structures
- Automatic optimization: System chooses best approach per file

## Troubleshooting

### Debug Information
Enable detailed logging to see which writer is selected:
```python
import os
os.environ['CIRCUIT_SYNTH_LOG_LEVEL'] = 'INFO'
```

Look for messages like:
```
INFO: Using modern kicad-sch-api for component schematic: USB_Port.kicad_sch
INFO: Using legacy writer for hierarchical schematic: ESP32_C6_Dev_Board.kicad_sch
```

### Version Conflicts
If you encounter issues:
```bash
pip install --upgrade kicad-sch-api packaging
```

### Fallback Behavior
The system gracefully falls back to legacy-only mode if:
- kicad-sch-api is not installed
- Version compatibility issues occur
- Import errors are encountered

## Future Development

The hybrid architecture allows for gradual migration:
1. **Current**: Component sheets use modern API
2. **Next**: Hierarchical sheets migration
3. **Future**: Full modern API adoption

This approach ensures stability while providing immediate benefits from the modern kicad-sch-api integration.