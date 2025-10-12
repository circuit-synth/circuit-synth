# Round-Trip Requirements

## Core User Stories

### 1. Update Component Values
Generate schematic → Move components in KiCad → Change values in Python → Re-run
**Result**: Values update, positions preserved

### 2. Add Components
Generate schematic → Route wires manually → Add LED in Python → Re-run
**Result**: LED appears, existing wiring intact

### 3. Manual Refinement
Generate → Route wires + add annotations in KiCad → Re-run (no Python changes)
**Result**: All manual work preserved

### 4. Remove Components
Generate with 5 resistors → Remove R3 in Python → Re-run
**Result**: R3 deleted, others untouched

### 5. Hierarchical Updates
Generate 3-sheet project → Edit all sheets → Modify Python → Re-run
**Result**: All sheets update, manual edits preserved

---

## Must Have (P0)

| Requirement | Status | Notes |
|------------|--------|-------|
| Component position preservation | ✅ Working | Via canonical matching |
| Wire preservation | ❓ Verify | Code exists, needs testing |
| Label preservation | ❓ Verify | Code exists, needs testing |
| Value/footprint updates | ✅ Working | Updates applied |
| Add new components | ✅ Working | Collision-free placement |
| Remove components | ✅ Working | Optional preserve user components |
| Automatic mode detection | ✅ Working | Transparent to user |

## Should Have (P1)

- Annotation preservation (text boxes, graphics)
- Power symbol handling (GND, VCC flags)
- Sheet updates for hierarchical projects
- Collision warnings for new components

## Could Have (P2)

- Change summary report
- Dry-run preview mode
- Auto-backup before update
- Smart wire routing for new connections

---

## Acceptance Criteria

### Core Functionality
- [ ] Component positions preserved on re-generation
- [ ] Manually-routed wires preserved
- [ ] Net labels preserved
- [ ] Component values update from Python
- [ ] New components added without collisions
- [ ] Removed components deleted from schematic

### User Experience
- [ ] Works automatically (no configuration)
- [ ] Clear feedback on what mode is active
- [ ] Tutorial works end-to-end
- [ ] No data loss incidents

### Performance
- [ ] Update completes in <2s for 50-component schematic
- [ ] Handles 500+ component projects
- [ ] Memory usage <100MB

---

## Out of Scope

- PCB layout preservation (separate feature)
- Library symbol updates (library management)
- KiCad version migration
- Visual style matching
