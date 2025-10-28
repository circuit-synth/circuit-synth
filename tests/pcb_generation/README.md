# PCB Bidirectional Sync Tests

Focused test suite for validating bidirectional synchronization of **component placement operations** between Python circuit definitions and KiCad PCB files.

## Status

**Phase**: Planning
**Status**: PRD Complete, Implementation Pending
**Target**: 21 comprehensive PCB tests (placement + vias + manufacturing)
**Scope**: Component placement, via management, footprint management, board setup, manufacturing
**Out of Scope**: Complex trace routing preservation (users route in KiCad)

## Overview

This test suite mirrors the architecture and philosophy of `tests/bidirectional/` (schematic tests), but focuses on **PCB component placement operations**:

**✅ IN SCOPE (What We Test):**
- **Component Placement**: Position preservation, auto-placement, manual adjustments
- **Via Management**: Through-hole vias, blind vias, buried vias (essential for multi-layer)
- **Footprint Management**: Footprint changes, library sync, assignment
- **Component Operations**: Add, delete, modify, rotate components
- **Board Setup**: Board outline, mounting holes, mechanical features
- **Board Features**: Silkscreen text, fiducials, graphics
- **Manufacturing**: Gerber/drill generation, pick-and-place, BOM with positions

**❌ OUT OF SCOPE (What We Don't Test):**
- **Complex Routing**: Trace preservation, differential pairs, autorouting (users route in KiCad)
- **Advanced Layers**: Power/ground plane zones, copper pours (future)
- **Routing Algorithms**: Length matching, impedance control (not circuit-synth's focus)

**Future Scope (Nice-to-Have):**
- **Simple Trace Drawing**: Basic Python-defined point-to-point traces
- **Orthogonal Routing**: 90° angle traces from vias to pads

**Why This Scope?** Circuit-synth focuses on intelligent component placement and essential board elements (vias). Users do complex routing in KiCad (the right tool for manual routing). **The killer features are placement preservation + via management**.

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

## Test Categories (21 Comprehensive Tests)

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

### Phase 3: Via Management (Tests 13-15) ⭐ NEW
- **Through-hole vias** (connects all layers)
- **Blind vias** (outer to inner layer)
- **Buried vias** (inner to inner layer)
- Essential for multi-layer boards (4+ layers)

### Phase 4: Board Features (Tests 16-18)
- Silkscreen text placement
- Fiducial markers for assembly
- Silkscreen graphics (logos, polarity marks)

### Phase 5: Manufacturing Output (Tests 19-21)
- Gerber & drill file export
- Pick-and-place export
- BOM with positions export

### Future (Not Current Scope)
- Simple trace drawing (point-to-point in Python)
- Orthogonal routing (90° angle auto-routing)
- Trace preservation when adding components
- Copper pour/zone tests
- Advanced DRC synchronization

## Comparison to Schematic Tests

| Feature | Schematic Tests | PCB Tests |
|---------|----------------|-----------|
| **Test Count** | 33+ | 21 (placement + vias + mfg) |
| **Killer Feature** | Position preservation (Test 09) | Placement preservation (Test 03) |
| **Secondary Focus** | Netlist validation | Via management (Tests 13-15) |
| **Primary Focus** | Connectivity/netlist | Component placement + vias |
| **Validation API** | kicad-sch-api | kicad-pcb-api |
| **File Format** | .kicad_sch | .kicad_pcb |
| **Out of Scope** | N/A | Complex routing (users do in KiCad) |
| **Status** | ✅ Complete | 📋 Planning |

## Why PCB Tests Are Critical

**Current Problem:**
- ❌ No validation that manual placement survives Python changes
- ❌ No proof that component operations work bidirectionally
- ❌ No verification of footprint change workflows
- ❌ Engineers won't trust tool for real boards

**With Comprehensive PCB Tests:**
- ✅ Validates placement preservation (hours of placement work)
- ✅ Proves component add/delete/modify operations work correctly
- ✅ Verifies footprint changes preserve positions
- ✅ **Validates via placement** (through-hole, blind, buried) for multi-layer boards
- ✅ Verifies manufacturing output accuracy (Gerbers, PnP, BOM)
- ✅ Enables iterative PCB workflow (placement + vias)
- ✅ **Clear expectations**: circuit-synth for placement/vias, KiCad for complex routing
- ✅ Engineers can trust tool for production boards

## Real-World Workflows Validated

### Iterative PCB Development (Realistic)
1. Generate PCB from Python (smart auto-placement, auto-via power/ground)
2. **Manually adjust component positions** in KiCad for optimal layout
3. **Route traces in KiCad** (manual routing - not automated)
4. Add decoupling caps + power vias in Python
5. Regenerate → **component positions preserved** ✅, **vias added** ✅, **accept re-routing** (expected)

### Footprint Optimization (Realistic)
1. Design with 0805 passives, place and route in KiCad
2. Realize 0603 saves board space
3. Change footprints to 0603 in Python
4. Regenerate → **placement positions preserved** ✅, re-route traces (expected)

### Multi-Layer Board Workflow (4-Layer Example)
1. Generate 4-layer PCB from Python (F.Cu, In1.Cu, In2.Cu, B.Cu)
2. Place components in KiCad for optimal layout
3. Add through-hole vias for power/ground in Python
4. Add blind vias (F.Cu → In1.Cu) for dense routing in Python
5. Regenerate → **all positions preserved** ✅, **vias added** ✅
6. **Route signal traces in KiCad** (use vias for layer transitions)
7. **Verify connectivity** with DRC in KiCad

## Implementation Timeline

- **Weeks 1-2**: Phase 1 (Tests 01-05: Core placement operations)
  - **Test 03 is highest priority** - THE KILLER FEATURE
- **Weeks 3-4**: Phase 2 (Tests 06-08: Component manipulation)
- **Weeks 5-6**: Phase 3 (Tests 09-12: Board & mechanical)
- **Weeks 7-8**: Phase 4 (Tests 13-15: Via management) ⭐ NEW
  - Essential for multi-layer boards
- **Weeks 9-10**: Phase 5 (Tests 16-18: Board features)
- **Weeks 11-12**: Phase 6 (Tests 19-21: Manufacturing output)

**Total**: 21 comprehensive tests over 12 weeks

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

✅ **Engineers trust circuit-synth for production PCB development**
✅ **Manual placement work is provably preserved** (THE key metric)
✅ Component operations (add/delete/modify) validated
✅ Footprint changes preserve positions
✅ **Via placement works** (through-hole, blind, buried) for multi-layer boards
✅ Board setup and mechanical features work
✅ Manufacturing output is accurate
✅ **21 comprehensive tests all passing**
✅ **Clear expectations set: circuit-synth for placement/vias, KiCad for complex routing**

---

**Status**: 📋 Planning Complete - Ready for Implementation
**Next Milestone**: Phase 1 Implementation (Tests 01-05)
