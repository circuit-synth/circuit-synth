# KiCad PCB Footprint Library Integration

The PCB API includes comprehensive support for KiCad's footprint libraries, providing access to thousands of pre-made component footprints with full pad and courtyard information.

## Overview

The footprint library system automatically discovers and indexes all KiCad footprint libraries on your system, allowing you to:

- Search for footprints by name, description, tags, or keywords
- Filter by footprint type (SMD, THT, Mixed)
- Filter by pad count and physical size
- Access detailed footprint information including pad layouts
- Add footprints to PCBs with complete pad data

## Basic Usage

### Searching for Footprints

```python
from circuit_synth.kicad_api.pcb import PCBBoard

pcb = PCBBoard()

# Simple search
results = pcb.search_footprints("0603")

# Search with filters
smd_results = pcb.search_footprints("0603", filters={
    "footprint_type": "SMD"
})

# Search for specific pad count
soic8_results = pcb.search_footprints("SOIC", filters={
    "pad_count": 8
})

# Search by size constraints
small_parts = pcb.search_footprints("", filters={
    "footprint_type": "SMD",
    "max_size": (5.0, 5.0)  # Max 5x5mm
})
```

### Getting Footprint Information

```python
# Get detailed information about a specific footprint
info = pcb.get_footprint_info("Resistor_SMD:R_0603_1608Metric")

if info:
    print(f"Description: {info.description}")
    print(f"Pads: {info.pad_count}")
    print(f"Size: {info.body_size[0]}x{info.body_size[1]}mm")
    print(f"Is SMD: {info.is_smd}")
    print(f"Is THT: {info.is_tht}")
```

### Adding Footprints from Library

```python
# Add a footprint with full pad information from the library
footprint = pcb.add_footprint_from_library(
    "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "U1",           # Reference
    50, 50,         # Position (x, y)
    rotation=0,     # Rotation in degrees
    value="LM358"   # Component value
)

if footprint:
    print(f"Added {footprint.reference} with {len(footprint.pads)} pads")
```

## Advanced Features

### Filter Options

The `search_footprints()` method supports several filter options:

```python
filters = {
    "footprint_type": "SMD",      # "SMD", "THT", or "Mixed"
    "pad_count": 8,               # Exact pad count
    "pad_count": (4, 16),         # Range of pad counts
    "max_size": (10.0, 10.0),     # Maximum width and height in mm
    "library": "Resistor_SMD"     # Specific library name
}
```

### Library Management

```python
# List all available libraries
libraries = pcb.list_available_libraries()
for lib in libraries:
    print(f"Library: {lib}")

# Refresh the footprint cache (after installing new libraries)
pcb.refresh_footprint_cache()
```

### Direct Cache Access

For advanced use cases, you can access the footprint cache directly:

```python
from circuit_synth.kicad_api.pcb import get_footprint_cache

cache = get_footprint_cache()

# Add custom library paths
from pathlib import Path
cache.add_library_path(Path("/path/to/custom/libraries"))

# Get all footprints (no filter)
all_footprints = cache.search_footprints("")
print(f"Total footprints: {len(all_footprints)}")
```

## Footprint Information Structure

The `FootprintInfo` class provides comprehensive footprint data:

```python
@dataclass
class FootprintInfo:
    library: str              # Library name (e.g., "Resistor_SMD")
    name: str                 # Footprint name (e.g., "R_0603_1608Metric")
    description: str          # Human-readable description
    tags: str                 # Space-separated tags
    keywords: str             # Searchable keywords
    
    # Physical characteristics
    pad_count: int            # Number of pads
    pad_types: Set[str]       # {"smd", "thru_hole", "np_thru_hole"}
    courtyard_area: float     # Area in mm²
    body_size: Tuple[float, float]  # (width, height) in mm
    bbox: Tuple[float, float, float, float]  # Bounding box
    
    # 3D models
    models_3d: List[str]      # Paths to 3D models
    
    # Metadata
    file_path: Optional[Path]  # Path to .kicad_mod file
    last_modified: Optional[datetime]
    
    # Properties
    is_smd: bool              # True if all pads are SMD
    is_tht: bool              # True if all pads are through-hole
    is_mixed: bool            # True if has both SMD and THT pads
```

## Platform Support

The footprint library system automatically discovers KiCad libraries on all major platforms:

### macOS
- `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints`
- `~/Library/Application Support/kicad/footprints`

### Windows
- `C:\Program Files\KiCad\share\kicad\footprints`
- `%APPDATA%\kicad\footprints`

### Linux
- `/usr/share/kicad/footprints`
- `~/.local/share/kicad/footprints`

### Environment Variable
You can also set `KICAD_FOOTPRINT_DIR` to specify additional search paths.

## Performance

- Initial index building: 2-5 seconds (for ~14,000 footprints)
- Subsequent loads: <100ms (using cached index)
- Search operations: 1-5ms (index-based search)
- Full footprint parsing: Only when needed (lazy loading)
- Index location: `~/.cache/circuit_synth/footprints/footprint_index.json`

## Example Scripts

Several example scripts demonstrate footprint library usage:

1. **footprint_search_demo.py** - Basic search examples
2. **list_footprint_libraries.py** - Library statistics and analysis
3. **show_footprint_details.py** - Detailed footprint information display
4. **pcb_with_library_footprints.py** - Complete PCB using library footprints
5. **test_footprint_library.py** - Test script to verify functionality

## Troubleshooting

### No Libraries Found

If no libraries are discovered:
1. Ensure KiCad is installed
2. Check that footprint libraries are installed (may be a separate package)
3. Set `KICAD_FOOTPRINT_DIR` environment variable to your footprint directory
4. Manually add paths using `cache.add_library_path()`

### Cache Issues

If searches are slow or returning outdated results:
```python
# Clear and rebuild cache
pcb.refresh_footprint_cache()
```

Or manually delete the cache file:
```bash
rm ~/.cache/circuit_synth/footprints/footprint_cache.json
```

## Implementation Notes

- Uses `sexpdata` for parsing .kicad_mod files
- Footprints are indexed by "Library:FootprintName" format
- Pad information includes type, shape, size, position, and layers
- Search is case-insensitive and supports partial matches
- Results are sorted by relevance (exact matches first)