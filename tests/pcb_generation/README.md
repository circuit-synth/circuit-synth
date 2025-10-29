# PCB Bidirectional Sync Tests

Focused test suite for validating bidirectional synchronization of **component placement operations** between Python circuit definitions and KiCad PCB files.

## Status

**Phase**: Planning
**Status**: PRD Complete, Implementation Pending
**Target**: 18 comprehensive PCB tests (no duplication, all critical operations)
**Scope**: Placement preservation, canonical update, collision avoidance, layer assignment, via management, manufacturing
**Out of Scope**: Schematic→PCB generation (KiCad does this), complex routing preservation

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

## Test Categories (18 Comprehensive Tests)

### Phase 1: Core Placement Operations (Tests 01-07)
- Blank PCB generation
- ⭐ **Placement preservation** (TEST 02 - THE KILLER FEATURE)
- Component add with **collision avoidance + smart auto-placement**
- Component delete
- ⭐ **Canonical update** (TEST 05 - ALL component fields sync + position preserved)
- Component rotation
- Round-trip regeneration

### Phase 2: Board & Footprint Management (Tests 08-11)
- ⭐ **Component layer assignment** (TEST 08 - F.Cu vs B.Cu - CRITICAL)
- Board outline definition
- Mounting holes placement
- Footprint library synchronization

### Phase 3: Via Management (Tests 12-14) ⭐
- **Through-hole vias** (connects all layers)
- **Blind vias** (outer to inner layer)
- **Buried vias** (inner to inner layer)
- Essential for multi-layer boards (4+ layers)

### Phase 4: Board Features (Tests 15-16)
- **Silkscreen features** (text + graphics combined)
- Fiducial markers for assembly

### Phase 5: Manufacturing Output (Tests 17-18)
- Gerber & drill file export
- Pick-and-place export (includes BOM data)

### Future (Not Current Scope)
- Simple trace drawing (point-to-point in Python)
- Orthogonal routing (90° angle auto-routing)
- Trace preservation when adding components
- Copper pour/zone tests
- Advanced DRC synchronization

## Comparison to Schematic Tests

| Feature | Schematic Tests | PCB Tests |
|---------|----------------|-----------|
| **Test Count** | 33+ | 18 (no duplication, all critical ops) |
| **Killer Feature** | Position preservation (Test 09) | Placement preservation (Test 02) |
| **Secondary Focus** | Netlist validation | Canonical update (Test 05), Layer assignment (Test 08) |
| **Tertiary Focus** | Component operations | Collision avoidance (Test 03), Via management (Tests 12-14) |
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

**With Comprehensive PCB Tests (18 Tests):**
- ✅ Validates placement preservation (hours of placement work) - TEST 02
- ✅ Validates canonical update (ALL component fields sync) - TEST 05
- ✅ Validates layer assignment (F.Cu vs B.Cu, double-sided boards) - TEST 08
- ✅ Proves component add/delete/modify operations work correctly - TESTS 03-04
- ✅ Validates collision avoidance + smart auto-placement - TEST 03
- ✅ Verifies footprint changes preserve positions - TEST 05
- ✅ **Validates via placement** (through-hole, blind, buried) - TESTS 12-14
- ✅ Verifies manufacturing output accuracy (Gerbers, PnP) - TESTS 17-18
- ✅ Enables iterative PCB workflow (placement + vias)
- ✅ **Clear expectations**: circuit-synth for placement/vias, KiCad for complex routing
- ✅ **No duplication** - 18 focused tests, all critical operations covered
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

- **Weeks 1-2**: Phase 1 (Tests 01-07: Core placement operations)
  - **Test 02 is highest priority** - THE KILLER FEATURE (placement preservation)
  - **Test 03** - Collision avoidance + smart auto-placement
  - **Test 05 is critical** - Canonical update (ALL fields sync + position preserved)
- **Weeks 3-4**: Phase 2 (Tests 08-11: Board & footprint management)
  - **Test 08 is critical** - Component layer assignment (F.Cu vs B.Cu)
- **Weeks 5-6**: Phase 3 (Tests 12-14: Via management) ⭐
  - Essential for multi-layer boards (through-hole, blind, buried)
- **Weeks 7-8**: Phase 4 (Tests 15-16: Board features)
  - Test 15 combines silkscreen text + graphics (efficient)
- **Weeks 9-10**: Phase 5 (Tests 17-18: Manufacturing output)
  - Test 18 combines PnP + BOM (efficient)

**Total**: 18 comprehensive tests over 10 weeks (no duplication, all critical operations covered)

## Getting Started

**Current Status**: PRD phase - tests not yet implemented.

**Next Steps**:
1. Review [PCB_BIDIRECTIONAL_TESTS_PRD.md](./PCB_BIDIRECTIONAL_TESTS_PRD.md)
2. Validate approach with stakeholders
3. Begin Phase 1 implementation (Tests 01-07)
4. Focus on critical tests first: Test 02 (placement preservation), Test 05 (canonical update), Test 08 (layer assignment)

## References

- **Schematic Tests**: `tests/bidirectional/` - proven pattern to follow
- **PCB Generator**: `src/circuit_synth/kicad/pcb_gen/pcb_generator.py`
- **kicad-pcb-api**: Primary validation library
- **PRD**: Complete specifications in this directory

## Success Criteria

This test suite succeeds when:

✅ **Engineers trust circuit-synth for production PCB development**
✅ **Manual placement work is provably preserved** (TEST 02 - THE key metric)
✅ **ALL component fields sync correctly** (TEST 05 - canonical update validation)
✅ **Component layer assignment works** (TEST 08 - F.Cu vs B.Cu for double-sided boards)
✅ **Collision avoidance + smart auto-placement** (TEST 03 - when adding new components)
✅ Component operations (add/delete/modify) validated (TESTS 03-04, 06-07)
✅ **Via placement works** (TESTS 12-14 - through-hole, blind, buried for multi-layer boards)
✅ Board setup and mechanical features work (TESTS 09-11)
✅ Silkscreen features work (TEST 15 - text + graphics)
✅ Manufacturing output is accurate (TESTS 17-18 - Gerbers + PnP/BOM)
✅ **18 comprehensive tests all passing** (no duplication, all critical operations covered)
✅ **Clear expectations: circuit-synth regenerates PCB preserving manual work**

---

**Status**: 📋 Planning Complete - Ready for Implementation
**Next Milestone**: Phase 1 Implementation (Tests 01-07)
**Focus**: Critical tests - Test 02 (placement preservation), Test 05 (canonical update), Test 08 (layer assignment)
