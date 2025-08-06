# Code Size Analysis

## Summary Statistics

### `/src/circuit_synth/kicad/` - Total: ~21,000+ lines
**Largest files:**
- `netlist_exporter.py`: 2,206 lines
- `sch_gen/main_generator.py`: 1,744 lines  
- `sch_gen/schematic_writer.py`: 1,597 lines
- `pcb_gen/pcb_generator.py`: 1,098 lines
- `sch_sync/synchronizer.py`: 979 lines

### `/src/circuit_synth/kicad_api/` - Total: ~15,000+ lines
**Largest files:**
- `core/s_expression.py`: 2,065 lines
- `schematic/placement.py`: 1,115 lines
- `core/symbol_cache.py`: 923 lines
- `schematic/design_rule_checker.py`: 762 lines
- `schematic/bulk_operations.py`: 655 lines

## Key Observations

### Code Volume
- **kicad/**: ~21,000+ lines (40% larger)
- **kicad_api/**: ~15,000+ lines (more compact)

### Architecture Patterns
- **kicad/**: More specialized, distributed functionality across sub-packages
- **kicad_api/**: More centralized, streamlined architecture

### Functionality Distribution

#### kicad/ Major Components:
1. **Schematic Generation** (`sch_gen/`): ~6,500 lines
2. **Netlist Export**: 2,206 lines  
3. **PCB Generation**: 1,098 lines
4. **Schematic API** (`sch_api/`): ~2,500 lines
5. **Schematic Editing** (`sch_editor/`): ~1,500 lines
6. **Synchronization** (`sch_sync/`): ~1,600 lines

#### kicad_api/ Major Components:
1. **S-Expression Parser**: 2,065 lines
2. **Placement Engine**: 1,115 lines
3. **Symbol Cache**: 923 lines
4. **Design Rule Checker**: 762 lines
5. **Search & Discovery**: ~1,200 lines
6. **Connection Management**: ~1,500 lines

## Overlapping Functionality Analysis

### Direct File Name Overlaps:
1. `bulk_operations.py` - Both directories (618 vs 655 lines)
2. `component_manager.py` - Both directories (510 vs 477 lines)
3. `symbol_geometry.py` - Both directories (304 vs 271 lines)
4. `synchronizer.py` - Both directories (979 vs 467 lines)

### Functional Overlaps:
- **Symbol caching**: `kicad/` has 3 implementations, `kicad_api/` has 1 modern one
- **Component management**: Both have extensive component handling
- **Schematic operations**: Both provide schematic manipulation
- **Synchronization**: Both have sync capabilities but different approaches

## Quality Indicators

### kicad/ Characteristics:
- More legacy code patterns
- Multiple implementations of similar features
- Complex nested directory structure
- Backup files present (`schematic_writer_backup.py`)

### kicad_api/ Characteristics:  
- Modern, clean architecture
- Single, well-designed implementations
- Comprehensive export list in `__init__.py`
- Better separation of concerns
- Graceful import error handling

## Recommendations

Based on size and architecture analysis:

1. **kicad_api/** appears to be the better foundation - cleaner, more modern
2. **kicad/** has more specialized functionality that may need to be preserved
3. Key functionality to extract from **kicad/**:
   - PCB generation (`pcb_gen/`)
   - Specialized netlist export features
   - Project notes management
   - Some advanced schematic generation features

4. **kicad_api/** should be the primary codebase with selective imports from **kicad/**