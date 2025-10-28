# PCB Bidirectional Sync Tests

Focused test suite for validating bidirectional synchronization of **component placement operations** between Python circuit definitions and KiCad PCB files.

## Status

**Phase**: Planning
**Status**: PRD Complete, Implementation Pending
**Target**: 15 focused PCB placement tests (not 25-35, routing is out of scope)
**Scope**: Component placement, footprint management, board setup
**Out of Scope**: Manual routing preservation (users route in KiCad)

## Overview

This test suite mirrors the architecture and philosophy of `tests/bidirectional/` (schematic tests), but focuses on **PCB component placement operations**:

**✅ IN SCOPE (What We Test):**
- **Component Placement**: Position preservation, auto-placement, manual adjustments
- **Footprint Management**: Footprint changes, library sync, assignment
- **Component Operations**: Add, delete, modify, rotate components
- **Board Setup**: Board outline, mounting holes, mechanical features
- **Manufacturing**: Gerber generation, pick-and-place, BOM with positions

**❌ OUT OF SCOPE (What We Don't Test):**
- **Routing**: Trace preservation, via management, autorouting (users route in KiCad)
- **Advanced Layers**: Complex stackups, power planes, copper pours (future)
- **Routing Algorithms**: Differential pairs, length matching (not circuit-synth's focus)

**Why This Scope?** Circuit-synth focuses on intelligent component placement. Users route manually in KiCad (the right tool for routing), and accept re-routing when components change. **The killer feature is placement preservation**, not routing preservation.

## Philosophy

**The Killer Feature for PCB**: **Placement preservation** when adding/modifying components during iterative development.

Just like schematic test 09 proves that manually-positioned components stay in place when regenerating, PCB test 03 will prove that **manual component placement work is preserved** when making changes in Python.

**Reality Check**: Users accept re-routing when components change (routing is manual in KiCad anyway). The critical feature is **preserving hours of placement work**, not routing work.

Without placement preservation, the tool is unusable for real PCB design. With this validated, engineers can trust circuit-synth for production boards.

## Documentation

- **[PCB_BIDIRECTIONAL_TESTS_PRD.md](./PCB_BIDIRECTIONAL_TESTS_PRD.md)**: Complete product requirements document
  - Full test specifications
  - Implementation plan
  - Validation strategies
  - Real-world workflows

## Test Categories (15 Focused Tests)

### Phase 1: Core Placement Operations (Tests 01-08)
- Blank PCB generation
- Component CRUD operations (add, delete, modify)
- ⭐ **Placement preservation** (TEST 03 - THE KILLER FEATURE)
- Footprint changes and rotation
- Round-trip placement synchronization

### Phase 2: Board & Footprint Management (Tests 09-12)
- Board outline definition
- Mounting holes placement
- Footprint library synchronization
- Component properties (DNP, MPN, custom fields)

### Phase 3: Manufacturing Output (Tests 13-15)
- Silkscreen text placement
- Fiducial markers for assembly
- Gerber/drill/pick-and-place export

### Future (Out of Scope for Initial Suite)
- Routing preservation (when/if implemented)
- Multi-layer advanced stackups
- Copper pour algorithms
- Autorouting integration

## Comparison to Schematic Tests

| Feature | Schematic Tests | PCB Tests |
|---------|----------------|-----------|
| **Test Count** | 33+ | 15 (focused scope) |
| **Killer Feature** | Position preservation (Test 09) | Placement preservation (Test 03) |
| **Primary Focus** | Connectivity/netlist | Component placement |
| **Validation API** | kicad-sch-api | kicad-pcb-api |
| **File Format** | .kicad_sch | .kicad_pcb |
| **Out of Scope** | N/A | Routing (users do in KiCad) |
| **Status** | ✅ Complete | 📋 Planning |

## Why PCB Tests Are Critical

**Current Problem:**
- ❌ No validation that manual placement survives Python changes
- ❌ No proof that component operations work bidirectionally
- ❌ No verification of footprint change workflows
- ❌ Engineers won't trust tool for real boards

**With Focused PCB Tests:**
- ✅ Validates placement preservation (hours of placement work)
- ✅ Proves component add/delete/modify operations work correctly
- ✅ Verifies footprint changes preserve positions
- ✅ Enables iterative PCB placement workflow
- ✅ **Clear expectations**: placement preserved, routing is user's responsibility
- ✅ Engineers can trust tool for production placement (route in KiCad)

## Real-World Workflows Validated

### Iterative PCB Development (Realistic)
1. Generate PCB from Python (smart auto-placement)
2. **Manually adjust component positions** in KiCad for optimal layout
3. **Route traces in KiCad** (manual routing - not automated)
4. Add decoupling caps in Python
5. Regenerate → **component positions preserved** ✅, **accept re-routing** (expected)

### Footprint Optimization (Realistic)
1. Design with 0805 passives, place and route in KiCad
2. Realize 0603 saves board space
3. Change footprints to 0603 in Python
4. Regenerate → **placement positions preserved** ✅, re-route traces (expected)

### Component Addition Workflow (Common)
1. Generate initial PCB, place and route in KiCad
2. Realize need for test points
3. Add test points in Python
4. Regenerate → **all placements preserved** ✅, test points auto-placed
5. **Adjust test point positions** in KiCad (fine-tune to accessible locations)
6. **Route test point connections** in KiCad (minimal effort)

## Implementation Timeline (Focused Scope)

- **Weeks 1-2**: Phase 1 (Tests 01-05: Core placement operations)
  - **Test 03 is highest priority** - THE KILLER FEATURE
- **Weeks 3-4**: Phase 2 (Tests 06-08: Component manipulation)
- **Weeks 5-6**: Phase 3 (Tests 09-12: Board & mechanical)
- **Weeks 7-8**: Phase 4 (Tests 13-15: Manufacturing output)

**Total**: 15 focused tests over 8 weeks (not 10 weeks for 35 tests)

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

✅ **Engineers trust circuit-synth for production PCB placement**
✅ **Manual placement work is provably preserved** (THE key metric)
✅ Component operations (add/delete/modify) validated
✅ Footprint changes preserve positions
✅ Board setup and mechanical features work
✅ Manufacturing output is accurate
✅ **15 focused placement tests all passing**
✅ **Clear expectations set: placement preserved, routing done in KiCad**

---

**Status**: 📋 Planning Complete - Ready for Implementation
**Next Milestone**: Phase 1 Implementation (Tests 01-05)
