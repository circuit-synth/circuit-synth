# PCB Bidirectional Sync Tests

Comprehensive test suite for validating bidirectional synchronization between Python circuit definitions and KiCad PCB files.

## Status

**Phase**: Planning
**Status**: PRD Complete, Implementation Pending
**Target**: 25+ comprehensive PCB-level bidirectional tests

## Overview

This test suite mirrors the architecture and philosophy of `tests/bidirectional/` (schematic tests), but focuses on PCB-level operations including:

- **Component Placement**: Position preservation, footprint changes, rotation
- **Routing**: Trace preservation, via placement, differential pairs
- **Layers**: Multi-layer boards, power/ground planes, copper pours
- **Design Rules**: DRC synchronization, clearances, track widths
- **Manufacturing**: Gerber generation, pick-and-place, assembly data

## Philosophy

**The Killer Feature for PCB**: Position preservation when adding components during iterative development.

Just like schematic test 09 proves that manually-positioned components stay in place when regenerating, PCB test 03 will prove that **manual PCB layout work is preserved** when making changes in Python.

Without this, the tool is unusable for real PCB design. With this validated, engineers can trust circuit-synth for production boards.

## Documentation

- **[PCB_BIDIRECTIONAL_TESTS_PRD.md](./PCB_BIDIRECTIONAL_TESTS_PRD.md)**: Complete product requirements document
  - Full test specifications
  - Implementation plan
  - Validation strategies
  - Real-world workflows

## Test Categories (Planned)

### Phase 1: Core PCB Operations (Tests 01-11)
- Blank PCB generation
- Component CRUD operations
- ⭐ **Placement preservation** (THE KILLER FEATURE)
- ⭐ **Routing preservation** (CRITICAL)
- Round-trip synchronization

### Phase 2: Layers & Design Rules (Tests 12-18)
- Multi-layer stack management
- Design rule synchronization
- Vias and layer transitions
- Differential pairs
- Power/ground planes

### Phase 3: Advanced Features (Tests 19-25)
- Keepout zones
- Board outline
- Mounting holes
- Silkscreen text
- Fiducial markers
- Gerber generation

### Phase 4: Manufacturing (Tests 26-35)
- Pick-and-place export
- Assembly drawings
- BOM with positions
- Test point reports
- Panel layouts

## Comparison to Schematic Tests

| Feature | Schematic Tests | PCB Tests |
|---------|----------------|-----------|
| **Test Count** | 33+ | 25+ (planned) |
| **Killer Feature** | Position preservation (Test 09) | Placement preservation (Test 03) |
| **Critical Feature** | Netlist validation | Routing preservation |
| **Validation API** | kicad-sch-api | kicad-pcb-api |
| **File Format** | .kicad_sch | .kicad_pcb |
| **Status** | ✅ Complete | 📋 Planning |

## Why PCB Tests Are Critical

**Current Problem:**
- ❌ No validation that manual PCB placement survives changes
- ❌ No proof that routing is preserved
- ❌ No verification of design rule synchronization
- ❌ Engineers won't trust tool for real boards

**With PCB Tests:**
- ✅ Validates placement preservation (hours of layout work)
- ✅ Proves routing survives component additions
- ✅ Verifies design rules transfer correctly
- ✅ Enables production-ready PCB workflow
- ✅ Engineers can trust tool for real projects

## Real-World Workflows Validated

### Iterative PCB Development
1. Generate PCB from Python
2. Manually place components for optimal layout
3. Route critical traces
4. Add decoupling caps in Python
5. Regenerate → **positions AND traces preserved** ✅

### Footprint Optimization
1. Design with 0805 passives
2. Layout and route
3. Change to 0603 in Python
4. Regenerate → **layout preserved** ✅

### High-Speed Design
1. Define differential pairs in Python
2. Route with length matching
3. Add termination resistors
4. Regenerate → **routing preserved** ✅

## Implementation Timeline

- **Week 1-2**: Phase 1 (Core operations, placement preservation)
- **Week 3-4**: Phase 2 (Component ops, routing preservation)
- **Week 5-6**: Phase 3 (Layers, design rules)
- **Week 7-8**: Phase 4 (Advanced features)
- **Week 9-10**: Phase 5 (Manufacturing integration)

## Getting Started

**Current Status**: PRD phase - tests not yet implemented.

**Next Steps**:
1. Review [PCB_BIDIRECTIONAL_TESTS_PRD.md](./PCB_BIDIRECTIONAL_TESTS_PRD.md)
2. Validate approach with stakeholders
3. Begin Phase 1 implementation
4. Create test 01-05 following schematic test patterns

## References

- **Schematic Tests**: `tests/bidirectional/` - proven pattern to follow
- **PCB Generator**: `src/circuit_synth/kicad/pcb_gen/pcb_generator.py`
- **kicad-pcb-api**: Primary validation library
- **PRD**: Complete specifications in this directory

## Success Criteria

This test suite succeeds when:

✅ Engineers trust circuit-synth for production PCB design
✅ Manual layout work is provably preserved
✅ Routing survives component changes
✅ Design rules sync correctly
✅ Manufacturing output is validated
✅ 25+ comprehensive tests all passing

---

**Status**: 📋 Planning Complete - Ready for Implementation
**Next Milestone**: Phase 1 Implementation (Tests 01-05)
