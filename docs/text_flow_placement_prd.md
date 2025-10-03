# Text-Flow Schematic Placement Algorithm - PRD

## Overview
Implement a simple text-flow placement algorithm for schematic components that places them left-to-right, wrapping to new rows when needed, similar to how text flows on a page.

## Objectives
- Replace current broken placement logic that spreads components vertically
- Create compact, readable schematic layouts
- Automatically select appropriate sheet size (A4 or A3)

## Specifications

### 1. Sheet Sizes & Usable Areas

**A4 Sheet:**
- Total size: 210mm × 297mm
- Usable area: (12.7, 12.7) to (176.53, 196.85)
- Usable dimensions: 163.83mm wide × 184.15mm tall

**A3 Sheet:**
- Total size: 297mm × 420mm
- Usable area: (12.7, 12.7) to (407.67, 252.73)
- Usable dimensions: 394.97mm wide × 240.03mm tall

**Overflow Handling:**
- Try A4 first
- If components don't fit, try A3
- If A3 overflows, throw an error (no larger sheets supported initially)

### 2. Component Placement Rules

**Starting Position:**
- First component's bounding box top-left corner at (12.7, 12.7)
- Component center position = (12.7 + width/2, 12.7 + height/2)

**Horizontal Flow (Left-to-Right):**
- Place components left to right
- Spacing between components: 2.54mm (100 mil) horizontally
- Position calculation: `next_x = current_x + component_width + 2.54`

**Row Wrapping:**
- When component doesn't fit in current row (would exceed right boundary), wrap to next row
- Condition: `current_x + component_width > max_x`
- New row starts at x = 12.7

**Row Height:**
- Each row height = tallest component in that row
- Vertical spacing: 2.54mm (100 mil) between rows
- Next row y position: `next_y = current_y + tallest_in_row + 2.54`

**Row Alignment:**
- Components in a row are aligned by **top of bounding box**
- All components in row have same y coordinate for their top edge

### 3. Bounding Box Calculation

- Use existing `_estimate_component_bbox()` method
- Includes symbol body + pin labels + text
- Returns (width, height) in mm

### 4. Component Ordering

- Place components in the order they appear in the circuit definition
- No sorting or reordering

### 5. Position Representation

**Important Distinction:**
- **Bounding box coordinates** are top-left corner positions
- **Component position** (stored in schematic) is the **center point**

**Calculation:**
- Given bounding box top-left at (bbox_x, bbox_y):
  - component_center_x = bbox_x + width/2
  - component_center_y = bbox_y + height/2

**Example:**
- First component with width=50mm, height=40mm
- Bounding box top-left: (12.7, 12.7)
- Component center: (12.7 + 25, 12.7 + 20) = (37.7, 32.7)

### 6. Algorithm Flow

```
1. Start with A4 sheet
2. Initialize bbox_x = 12.7, bbox_y = 12.7 (bounding box top-left corner)
3. Initialize current_row_height = 0

For each component:
  a. Get component bounding box (width, height)

  b. Check if fits in current row:
     if bbox_x + width > max_x:
        - Wrap to next row
        - bbox_x = 12.7
        - bbox_y = bbox_y + current_row_height + 2.54
        - current_row_height = 0

  c. Check if fits on sheet:
     if bbox_y + height > max_y:
        - If on A4, retry with A3
        - If on A3, throw error

  d. Place component:
     - bbox_top_left = (bbox_x, bbox_y)
     - center_x = bbox_x + width/2
     - center_y = bbox_y + height/2
     - Store center position (center_x, center_y) in schematic

  e. Update for next component:
     - bbox_x += width + 2.54
     - current_row_height = max(current_row_height, height)

4. Return placements and selected sheet size
```

### 7. Integration

**Hook Point:**
- `ComponentManager.add_component()` at line 122-127
- Replace call to `placement_engine.find_position()`
- Call new text-flow placement instead

**No JSON Intermediate:**
- Calculate positions directly during schematic generation
- Update component positions in schematic immediately
- Skip JSON file generation for placement

### 8. Success Criteria

- [ ] All 16 components in RP2040 circuit fit on single sheet
- [ ] No component overlaps
- [ ] Components stay within usable area boundaries
- [ ] Sheet size automatically selected (likely A4 for RP2040)
- [ ] Schematic opens in KiCad with readable layout
- [ ] Components aligned properly in rows

## Non-Goals (Future Work)

- L-shaped layout utilizing space above title block
- Sheet sizes larger than A3
- Connectivity-based placement optimization
- Manual position overrides
- Component grouping by function

## Open Questions

None - all clarified in discussion.

## Timeline

1. Implement algorithm: 1 hour
2. Test on RP2040 circuit: 30 min
3. Debug and refinement: 30 min

**Total: ~2 hours**
