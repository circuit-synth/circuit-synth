# Test 68: Dynamic Sheet Sizing

## What This Tests

**Core Question**: When you add components to a circuit (either via generation or synchronization), does the KiCad schematic automatically resize the sheet to fit all components? Or do components overflow beyond the visible sheet boundary?

This tests **automatic sheet size adjustment** - ensuring the drawing sheet (A4, A3, A2, A1, A0, etc.) dynamically grows to accommodate circuit complexity.

## When This Situation Happens

- Start with small circuit (5 components) → fits on A4 sheet
- Add 50 more components → should auto-resize to A3 or larger
- Import large circuit from KiCad → should fit on appropriate sheet size
- Synchronize after adding components in Python → sheet should grow if needed

## What Should Work

1. Generate initial circuit with 10 components → fits on A4
2. Verify sheet size is A4 (297×210mm)
3. Add 50 more components (total 60) in Python
4. Regenerate/synchronize circuit
5. Sheet should automatically resize to larger format (A3: 420×297mm)
6. All 60 components visible within sheet boundaries
7. No components overflow beyond drawing sheet edge

## Current Behavior (BUG)

**Problem**: Sheet size does NOT automatically adjust during generation or synchronization.

- Initial generation with 10 components: Uses A4 ✓
- Add 50 more components: Still uses A4 ✗
- Components overflow beyond A4 boundaries ✗
- Manual sheet resize required in KiCad ✗

**This breaks real-world workflow:**
- Users add components iteratively
- Circuit grows over time
- Components disappear off-screen
- Must manually resize sheet every time

## Manual Test Instructions

```bash
cd tests/bidirectional/68_dynamic_sheet_sizing

# Step 1: Generate initial circuit with 10 resistors
uv run growing_circuit.py
open growing_circuit/growing_circuit.kicad_pro
# Verify:
#   - 10 resistors visible (R1-R10)
#   - Sheet size is A4 (297×210mm)
#   - All components fit within sheet boundaries

# Step 2: Check current sheet size in KiCad schematic
# File → Page Settings → should show "A4" paper size

# Step 3: Edit growing_circuit.py to uncomment R11-R60 (50 more components)
# Uncomment lines for r11 through r60

# Step 4: Regenerate circuit
uv run growing_circuit.py

# Step 5: Verify sheet resized in KiCad
open growing_circuit/growing_circuit.kicad_pro
# Expected:
#   - 60 resistors visible (R1-R60)
#   - Sheet size automatically changed to A3 or larger
#   - All components still fit within sheet boundaries
#   - No components overflow off-screen

# Current behavior (BUG):
#   - Sheet size still A4 (not resized)
#   - Components overflow beyond A4 boundaries
#   - Some components not visible without manual zoom/pan
```

## Expected Result

- ✅ Initial generation: 10 components fit on A4 sheet
- ✅ Sheet size detection: A4 dimensions (297×210mm)
- ✅ Add 50 components: Regeneration triggers sheet resize
- ✅ Automatic resize: Sheet grows to A3 (420×297mm) or larger
- ✅ All components visible: No overflow beyond sheet edge
- ✅ Works for both generation and synchronization

## Why This Is Important

**Real-world circuit development is iterative:**
1. Start with small proof-of-concept (5-10 components)
2. Add more components as design evolves (20, 50, 100+)
3. Each addition may push beyond current sheet size
4. Manual sheet resizing is tedious and error-prone
5. Users expect tools to handle layout automatically

**If this doesn't work:**
- Components disappear off-screen
- Users must manually resize sheet every time
- Frustrating workflow interruption
- Discourages iterative development
- Professional PCB tools handle this automatically

**If this works:**
- Seamless circuit growth from small to large
- No manual sheet management needed
- Professional tool behavior
- Encourages iterative development
- Matches user expectations

## Success Criteria

This test PASSES when:
- Initial generation: Correct sheet size chosen (A4 for 10 components)
- After adding 50 components: Sheet automatically resizes to A3 or larger
- All components visible within sheet boundaries (no overflow)
- Works for both `.generate_kicad_project()` and synchronization
- Sheet size stored correctly in `.kicad_sch` file
- KiCad displays correct sheet size in Page Settings

## Related Issues

- Issue #413: Dynamic sheet sizing not working during generation or synchronization
- Blocks: Large circuit development, iterative design workflows

## Implementation Notes

**Sheet sizes in KiCad:**
- A5: 210×148mm (smallest, ~15-20 components)
- A4: 297×210mm (default, ~30-40 components)
- A3: 420×297mm (~60-80 components)
- A2: 594×420mm (~100-150 components)
- A1: 841×594mm (~200+ components)
- A0: 1189×841mm (largest, 500+ components)

**Algorithm needed:**
1. Calculate total bounding box of all components
2. Add margins (12.7mm default)
3. Select smallest sheet size that fits
4. Update `.kicad_sch` paper size field
5. Trigger during both generation and synchronization

**Current code locations:**
- Generation: `src/circuit_synth/kicad/sch_gen/schematic_generator.py`
- Synchronization: `src/circuit_synth/kicad/synchronizer/schematic_synchronizer.py`
- Sheet size logic: Needs to be added to both

## Additional Notes

- This is a **critical usability feature**
- Affects every iterative circuit development workflow
- Should work automatically without user intervention
- Professional PCB tools (Altium, Eagle) handle this automatically
- Users expect this behavior by default
