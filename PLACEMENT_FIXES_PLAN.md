# Component Placement and Bounding Box Fixes - Master Plan

**Status:** In Progress
**Start Date:** 2025-10-14
**Repository:** circuit-synth, kicad-sch-api

---

## 🎯 Overview

Fix component placement accuracy and bounding box calculations to eliminate:
- Label text overlapping bounding boxes
- Pin text shooting past pin connections
- Incorrect designator positions
- Component collisions (especially large components)

---

## 📋 Task List

### Phase 1: Quick Wins (circuit-synth)

#### ✅ Issue #158: Fix text width ratio for pin labels
- **Branch:** `fix/text-width-ratio`
- **Files:** `src/circuit_synth/kicad/sch_gen/symbol_geometry.py`
- **Change:** `DEFAULT_PIN_TEXT_WIDTH_RATIO = 1.0` → `0.65`
- **Test:** Generate schematic with `draw_bounding_boxes=True`, verify labels fit within boxes
- **Status:** ✅ Complete
- **PR:** #163 (merged)

---

#### ✅ Issue #159: Add KiCad pin name offset
- **Branch:** `fix/pin-name-offset`
- **Files:** `src/circuit_synth/kicad/sch_gen/symbol_geometry.py`
- **Changes:**
  - Add `PIN_NAME_OFFSET = 0.508  # 20 mils`
  - Update `_get_pin_bounds()` to calculate from endpoint, not origin
- **Test:** Verify pin labels align with KiCad's native placement
- **Status:** ⬜ Not Started
- **PR:** _pending_

---

#### ✅ Issue #160: Adaptive designator placement
- **Branch:** `fix/adaptive-designators`
- **Files:** `src/circuit_synth/kicad/sch_gen/symbol_geometry.py`
- **Changes:**
  - Replace fixed `property_spacing = 3.0` with `max(3.0, height * 0.15)`
  - Scale property_width based on component width
- **Test:** Generate circuits with small/medium/large components, verify appropriate spacing
- **Status:** ⬜ Not Started
- **PR:** _pending_

---

#### ✅ Issue #161: Unify bounding box calculations
- **Branch:** `fix/unified-bounding-box`
- **Files:**
  - `src/circuit_synth/kicad/sch_gen/symbol_geometry.py`
  - `src/circuit_synth/kicad/schematic/text_flow_placement.py`
- **Changes:**
  - Remove `calculate_placement_bounding_box()` (no labels)
  - Remove `calculate_visual_bounding_box()` (with labels)
  - Keep only `calculate_bounding_box()` with pin labels included
  - Update text-flow placer to use single bbox
  - Add post-placement validation
- **Test:** Generate complex circuits, verify no visual overlaps
- **Status:** ⬜ Not Started
- **PR:** _pending_
- **Dependencies:** Issues #158, #159 (affects bbox size)

---

### Phase 2: Architectural Changes (kicad-sch-api)

#### ✅ Issue #6: Move geometry logic to kicad-sch-api
- **Branch:** `feature/geometry-module`
- **Files:**
  - NEW: `kicad_sch_api/geometry/__init__.py`
  - NEW: `kicad_sch_api/geometry/symbol_bbox.py`
  - NEW: `kicad_sch_api/geometry/font_metrics.py`
  - MOVE FROM circuit-synth: `SymbolBoundingBoxCalculator`
- **Changes:**
  - Create `geometry` package in kicad-sch-api
  - Move symbol geometry parsing from circuit-synth
  - Extract actual KiCad font metrics from source
  - Add per-character width tables
  - Comprehensive tests with known dimensions
- **Test:** All circuit-synth tests pass after migration
- **Status:** ⬜ Not Started
- **PR:** _pending_
- **Dependencies:** Phase 1 complete (validates approach)

---

#### Update circuit-synth to use kicad-sch-api geometry
- **Branch:** `refactor/use-kicad-sch-api-geometry`
- **Files:**
  - DELETE: `src/circuit_synth/kicad/sch_gen/symbol_geometry.py`
  - UPDATE: All files importing symbol_geometry
  - UPDATE: `requirements.txt` / `pyproject.toml` for kicad-sch-api version
- **Changes:**
  - Replace local geometry with `from kicad_sch_api.geometry import ...`
  - Remove duplicate code
  - Update all callers
- **Test:** Full regression test suite
- **Status:** ⬜ Not Started
- **PR:** _pending_
- **Dependencies:** kicad-sch-api#6 merged

---

### Phase 3: Cleanup

#### Remove duplicate .claude commands
- **Branch:** `chore/cleanup-claude-commands`
- **Files:**
  - Moved circuit-design commands from root to templates
  - Moved manufacturing commands from root to templates
  - Synced example_project with templates
  - Added DEBUGGING_GUIDE.md
- **Changes:** Reorganized .claude structure for clarity - root for framework dev, templates for circuit design
- **Test:** Verified command structure and organization
- **Status:** ✅ Complete
- **PR:** #164 (merged)

---

## 🔄 Workflow

For each task:

1. **Checkout branch:** `git checkout -b <branch-name>`
2. **Implement changes** as specified in issue
3. **Test thoroughly:**
   - Run existing tests
   - Generate test schematics
   - Visual verification in KiCad
4. **Commit with descriptive message**
5. **Push and create PR:** `gh pr create`
6. **Merge to main** after review
7. **Mark task complete** in this document: Change ⬜ to ✅

---

## 📊 Progress Tracking

- **Phase 1:** 1/4 complete (25%)
- **Phase 2:** 0/2 complete (0%)
- **Phase 3:** 1/1 complete (100%)
- **Overall:** 2/7 complete (29%)

---

## 🧪 Testing Strategy

### Test Circuits
Create comprehensive test suite covering:
- Small components (resistors, capacitors)
- Medium components (connectors, regulators)
- Large components (MCUs with 50+ pins)
- Mixed circuits with all sizes
- Long net names (hierarchical labels)

### Validation Checks
For each fix:
- [ ] Bounding boxes match visual extent
- [ ] No component overlaps
- [ ] Pin labels positioned correctly
- [ ] Designators readable and well-placed
- [ ] Professional appearance
- [ ] Works with `draw_bounding_boxes=True`

### Regression Tests
- [ ] All existing pytest tests pass
- [ ] Round-trip preservation tests pass
- [ ] Previously working circuits still work
- [ ] No performance degradation

---

## 📝 Notes

- This document is **NOT** committed to git
- Update ⬜/✅ status as tasks complete
- Add PR links when created
- Document any blockers or issues
- Track dependencies between tasks

---

## 🔗 Related Documents

- `PLACEMENT_ISSUES_ANALYSIS.md` - Detailed technical analysis
- `test_placement_issues.py` - Reproduction test script
- GitHub Issues: #158, #159, #160, #161, kicad-sch-api#6

---

**Last Updated:** 2025-10-14
**Next Task:** Issue #159 - Add KiCad pin name offset
