# Overlap Analysis - Detailed File Comparison

## Direct File Name Overlaps

### 1. `bulk_operations.py` (618 vs 655 lines)

#### `/kicad/sch_api/bulk_operations.py`:
- **Architecture**: Uses internal models and schematic_reader
- **Dependencies**: Heavy integration with existing kicad/ infrastructure
- **Features**: GroupBounds dataclass, DEFAULT_SPACING constants
- **Style**: More traditional class-based approach

#### `/kicad_api/schematic/bulk_operations.py`:  
- **Architecture**: Uses core.types, cleaner separation
- **Dependencies**: Modern enum-based OperationType system
- **Features**: BulkOperation dataclass, SearchEngine integration
- **Style**: More modern, dataclass-heavy approach

**Verdict**: `kicad_api/` version is more modern and better structured

### 2. `component_manager.py` (510 vs 477 lines)

#### `/kicad/sch_api/component_manager.py`:
- **Dependencies**: Complex imports from multiple kicad/ submodules
- **Features**: ComponentOperations integration, comprehensive error handling
- **Architecture**: Heavy coupling to existing kicad/ ecosystem

#### `/kicad_api/schematic/component_manager.py`:
- **Dependencies**: Clean imports from core.types and core.symbol_cache
- **Features**: PlacementEngine integration, cleaner initialization
- **Architecture**: More decoupled, modern design patterns

**Verdict**: `kicad_api/` version is cleaner and more maintainable

### 3. `symbol_geometry.py` (304 vs 271 lines)

#### `/kicad/sch_gen/symbol_geometry.py`:
- Location: Part of schematic generation subsystem
- Focus: Generation-time geometry calculations

#### `/kicad_api/schematic/symbol_geometry.py`:
- Location: Part of general schematic manipulation
- Focus: Runtime geometry operations

**Verdict**: Different purposes - may need both or merge functionality

### 4. `synchronizer.py` (979 vs 467 lines)

#### `/kicad/sch_sync/synchronizer.py`:
- **Size**: 979 lines - much larger implementation
- **Location**: Dedicated sync subsystem
- **Purpose**: Complex synchronization workflows

#### `/kicad_api/schematic/synchronizer.py`:
- **Size**: 467 lines - more focused implementation  
- **Location**: Part of general schematic operations
- **Purpose**: Core synchronization functionality

**Verdict**: `kicad/` version appears more comprehensive, `kicad_api/` more streamlined

## Functional Overlap Areas

### Symbol Caching (3 implementations in kicad/ vs 1 in kicad_api/)

#### `kicad/` Symbol Caching:
1. `kicad_symbol_cache.py` (584 lines) - Original implementation
2. `rust_accelerated_symbol_cache.py` (266 lines) - Performance variant  
3. `symbol_lib_parser.py` (698 lines) - Library parsing

#### `kicad_api/` Symbol Caching:
1. `core/symbol_cache.py` (923 lines) - Single, comprehensive implementation

**Verdict**: `kicad_api/` has better consolidated approach

### Component Operations

#### `kicad/` Component System:
- `sch_api/component_manager.py` (510 lines)
- `sch_api/component_operations.py` (225 lines)  
- `sch_api/component_search.py` (461 lines)
- Total: ~1,196 lines across 3 files

#### `kicad_api/` Component System:
- `schematic/component_manager.py` (477 lines)
- `schematic/search_engine.py` (596 lines)
- Total: ~1,073 lines across 2 files

**Verdict**: `kicad_api/` is more consolidated and efficient

## Import Analysis

### `kicad/` Import Patterns:
```python
from ..sch_editor.schematic_reader import SchematicSymbol
from .models import AlignmentOptions, MoveOptions, WireStyle
from .placement_engine import PlacementEngine
```
- Complex internal dependencies
- Requires entire kicad/ ecosystem

### `kicad_api/` Import Patterns:
```python
from ..core.types import Point, Schematic, SchematicSymbol
from ..core.symbol_cache import get_symbol_cache
```
- Clean, minimal dependencies
- Well-defined core/schematic separation

## Architecture Quality Assessment

### `kicad/` Architecture:
- ✅ **Comprehensive**: More specialized functionality
- ❌ **Complex**: Deep nested dependencies  
- ❌ **Legacy**: Multiple implementations of similar features
- ❌ **Coupling**: High interdependence between modules

### `kicad_api/` Architecture:
- ✅ **Modern**: Clean separation of concerns
- ✅ **Maintainable**: Single implementations  
- ✅ **Decoupled**: Clear core/schematic boundaries
- ❌ **Incomplete**: May be missing some specialized features

## Recommendations

### Phase 1: Use kicad_api/ as Foundation
- `kicad_api/` has superior architecture and should be the primary codebase
- Modern design patterns, better separation of concerns
- More maintainable and extensible

### Phase 2: Selective Feature Migration
From `kicad/`, preserve:
1. **PCB Generation** (`pcb_gen/`) - Not present in `kicad_api/`
2. **Netlist Export** (`netlist_exporter.py`) - Specialized functionality
3. **Project Notes** (`project_notes.py`) - Unique feature
4. **Specialized Generation** (`sch_gen/main_generator.py`) - Large comprehensive impl

### Phase 3: Integration Strategy
1. Keep `kicad_api/` intact as the new primary API
2. Create `kicad_legacy/` for preserved `kicad/` functionality  
3. Add compatibility layer between the two systems
4. Gradually migrate unique features from legacy to modern API