# PRD: Circuit-Synth KiCad-Sch-API Migration

## Overview

Migrate circuit-synth from its current minimal KiCad integration (`kicad_api_minimal.py`) to use the robust `kicad-sch-api` PyPI package (v0.1.0+) for professional schematic generation and manipulation.

## Current State Analysis

### Circuit-Synth Current KiCad Integration
- **Minimal stub implementation** in `src/circuit_synth/kicad_api_minimal.py`
- **Basic schematic generation** via `kicad/sch_gen/main_generator.py`
- **Legacy S-expression manipulation** with custom parsers
- **Limited format preservation** and validation capabilities
- **Manual schematic writing** through `schematic_writer.py`

### KiCad-Sch-API Capabilities
- **Professional schematic manipulation** with exact format preservation
- **Modern object-oriented API** with intuitive component management
- **Symbol library caching** with performance optimization
- **Comprehensive validation** and error handling
- **Bulk operations** and advanced filtering
- **Native MCP server integration** for AI agents

## Migration Objectives

### Primary Goals
1. **Replace minimal stubs** with full kicad-sch-api integration
2. **Maintain backward compatibility** for existing circuit-synth projects
3. **Leverage professional features** for enhanced schematic quality
4. **Improve performance** through optimized symbol caching
5. **Enable advanced capabilities** like validation and bulk operations

### Success Criteria
- All existing circuit-synth functionality preserved
- Improved schematic output quality and KiCad compatibility
- Performance improvement in large schematic generation
- Enhanced error handling and validation
- Seamless integration with circuit-synth agent ecosystem

## Technical Implementation Plan

### Phase 1: Core Integration (Week 1)
**Replace minimal KiCad stubs with kicad-sch-api**

1. **Update dependencies**
   - Add kicad-sch-api>=0.1.0 PyPI dependency to `pyproject.toml`
   - Configure import paths for package access
   - Update development dependencies

2. **Create adapter layer**
   - Build `KicadSchApiAdapter` class in `src/circuit_synth/kicad/adapters/`
   - Map circuit-synth component model to kicad-sch-api objects
   - Provide backward-compatible interface for existing code

3. **Replace stub implementations**
   - Update `kicad_api_minimal.py` to use real kicad-sch-api classes
   - Maintain existing class names and method signatures
   - Add deprecation warnings for direct usage

### Phase 2: Enhanced Generation (Week 2)
**Upgrade schematic generation pipeline**

1. **Modernize main_generator.py**
   - Replace manual S-expression writing with kicad-sch-api calls
   - Leverage ComponentCollection for efficient component management
   - Use Wire and Junction collections for connection handling

2. **Integrate symbol library caching**
   - Configure SymbolLibraryCache for circuit-synth symbol paths
   - Optimize symbol lookup performance for large circuits
   - Add symbol validation and missing symbol detection

3. **Enhanced validation**
   - Replace basic validation with comprehensive SchematicValidator
   - Add electrical rule checking (ERC) integration
   - Provide detailed error reporting for debugging

### Phase 3: Advanced Features (Week 3)
**Leverage professional capabilities**

1. **Bulk operations support**
   - Enable bulk component property updates
   - Add mass footprint assignment capabilities
   - Implement batch component modification for manufacturing data

2. **Format preservation**
   - Ensure exact KiCad format compatibility
   - Preserve custom formatting and comments
   - Add round-trip testing for all generated schematics

3. **Performance optimization**
   - Implement lazy loading for large schematics
   - Add component indexing for fast lookup
   - Optimize wire routing and placement algorithms

### Phase 4: Integration & Testing (Week 4)
**Complete integration and validation**

1. **Comprehensive testing**
   - Migrate existing tests to use kicad-sch-api
   - Add format preservation tests for all reference circuits
   - Performance benchmarking against current implementation

2. **Documentation updates**
   - Update CLAUDE.md with new kicad-sch-api patterns
   - Add migration guide for existing users
   - Update API documentation and examples

3. **Backward compatibility validation**
   - Test all existing circuit-synth projects
   - Ensure agent commands continue working
   - Validate memory-bank system integration

## Technical Architecture

### Current vs. Proposed Architecture

```
CURRENT ARCHITECTURE:
circuit-synth/
├── src/circuit_synth/
│   ├── kicad_api_minimal.py          # Minimal stubs
│   └── kicad/sch_gen/
│       ├── main_generator.py         # Manual S-expr generation
│       ├── schematic_writer.py       # Custom formatter
│       └── collision_manager.py      # Basic placement

PROPOSED ARCHITECTURE:
circuit-synth/
├── dependencies: kicad-sch-api>=0.1.0 # Professional KiCad API via PyPI
├── src/circuit_synth/
│   ├── kicad/
│   │   ├── adapters/
│   │   │   └── kicad_sch_adapter.py  # Adapter layer
│   │   ├── sch_gen/
│   │   │   └── modern_generator.py   # Uses kicad-sch-api
│   │   └── integration/
│   │       └── api_bridge.py         # Compatibility layer
│   └── kicad_api_minimal.py          # Deprecated stubs
```

### Integration Points

1. **Component Creation**
   ```python
   # Current: Manual S-expression
   component_sexpr = f'(symbol (lib_id "{lib_id}") (at {x} {y} 0)...)'
   
   # Proposed: kicad-sch-api
   component = sch.components.add(lib_id, ref, value, position=(x, y))
   ```

2. **Schematic Management**
   ```python
   # Current: Manual file writing
   with open(file_path, 'w') as f:
       f.write(generate_schematic_content())
   
   # Proposed: Professional API
   sch = ksa.create_schematic("My Circuit")
   sch.save(file_path, preserve_format=True)
   ```

3. **Symbol Library Integration**
   ```python
   # Current: No caching
   symbol_data = parse_symbol_library(path)
   
   # Proposed: Cached performance
   cache = ksa.get_symbol_cache()
   symbol = cache.get_symbol(lib_id)
   ```

## Risk Assessment & Mitigation

### High-Risk Areas
1. **Backward compatibility break** - Mitigation: Comprehensive adapter layer
2. **Performance regression** - Mitigation: Benchmarking and optimization
3. **Missing symbol libraries** - Mitigation: Enhanced library sourcing
4. **Agent integration issues** - Mitigation: Incremental testing

### Low-Risk Areas
1. **Format preservation** - kicad-sch-api is designed for this
2. **Memory-bank integration** - No changes to git-based system
3. **Component database** - Enhanced with better validation

## Success Metrics

### Technical Metrics
- **100% backward compatibility** for existing circuit-synth projects
- **50%+ performance improvement** in large schematic generation
- **Zero format preservation issues** in KiCad compatibility
- **10x reduction** in schematic-related bugs

### User Experience Metrics
- **Faster circuit generation** with optimized symbol caching
- **Better error messages** with comprehensive validation
- **Enhanced debugging** with professional diagnostics
- **Improved reliability** with robust error handling

## Dependencies & Prerequisites

### Required Updates
- `pyproject.toml`: Add kicad-sch-api>=0.1.0 PyPI dependency ✅ COMPLETED
- Development environment: Standard pip/uv installation
- CI/CD: Update test pipelines for new integration

### External Dependencies
- KiCad symbol libraries (existing)
- Python 3.12+ (already required)
- Git submodule management (existing)

## Timeline & Milestones

### Week 1: Foundation
- [x] PyPI package dependency integration
- [ ] Basic adapter layer implementation
- [ ] Stub replacement with real classes

### Week 2: Core Features
- [ ] Modern schematic generation
- [ ] Symbol library caching integration
- [ ] Enhanced validation implementation

### Week 3: Advanced Capabilities
- [ ] Bulk operations support
- [ ] Format preservation validation
- [ ] Performance optimization

### Week 4: Validation & Release
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Backward compatibility validation

## Decision Points

### Architecture Decisions
1. **Adapter Pattern**: Use adapter layer to maintain API compatibility
2. **Gradual Migration**: Replace components incrementally, not wholesale
3. **Performance First**: Leverage kicad-sch-api's optimization features
4. **Format Preservation**: Prioritize exact KiCad compatibility

### Implementation Strategy
1. **Start with adapters** to minimize breaking changes
2. **Test extensively** with existing circuit-synth projects
3. **Optimize performance** using symbol caching and indexing
4. **Maintain agent compatibility** throughout migration

## Expected Outcomes

### Immediate Benefits
- **Professional-grade schematic generation** with exact format preservation
- **Reduced bugs** through comprehensive validation
- **Better performance** with optimized symbol handling
- **Enhanced debugging** with detailed error reporting

### Long-term Benefits
- **Foundation for advanced features** like hierarchical design
- **Better KiCad ecosystem integration** with standard APIs
- **Improved maintainability** through proven, tested code
- **Enhanced AI agent capabilities** with robust schematic manipulation

---

**Status**: Ready for implementation  
**Priority**: High - Core infrastructure improvement  
**Effort**: 4 weeks (80-100 hours engineering time)  
**Risk**: Medium - Managed through incremental migration strategy