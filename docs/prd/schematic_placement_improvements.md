# Schematic Placement Improvements - PRD

**Status:** Implemented
**Created:** 2025-10-06
**Owner:** circuit-synth
**Branch:** improve-schematic-placement

## 1. Executive Summary

Redesign KiCad schematic generation with accurate bounding box calculations and unified text-flow placement for components and hierarchical sheets. The key innovation is the ComponentUnit pattern: treating a component, its labels, and bounding box as a single movable unit.

## 2. Goals

1. **Accurate bounding boxes** - Bbox exactly encompasses component body + pins + connected labels
2. **Unified placement** - Components and hierarchical sheets placed together in single algorithm
3. **Label tracking** - Labels tracked at creation time, not detected by proximity
4. **Correct orientation** - Labels extend IN the direction pins point
5. **Optimal layout** - Largest-first, left-to-right, top-to-bottom with minimal spacing

## 3. Architecture

### 3.1 ComponentUnit System

**Core Concept:** Bundle component + labels + bounding box into a single unit that moves atomically.

```python
@dataclass
class ComponentUnit:
    """
    A component with its labels and bounding box as a single movable unit.
    All coordinates in global schematic coordinates.
    """
    component: SchematicSymbol
    labels: List[Label]              # Only labels connected to this component
    bbox_min_x: float
    bbox_min_y: float
    bbox_max_x: float
    bbox_max_y: float
    bbox_graphic: Optional[Rectangle] = None

    def move_to(self, new_center_x: float, new_center_y: float):
        """Move component, all labels, and bbox together atomically"""
        # Calculate offset
        dx = new_center_x - self.component.position.x
        dy = new_center_y - self.component.position.y

        # Move all elements
        self.component.position.x = new_center_x
        self.component.position.y = new_center_y

        for label in self.labels:
            label.position.x += dx
            label.position.y += dy

        self.bbox_min_x += dx
        self.bbox_min_y += dy
        self.bbox_max_x += dx
        self.bbox_max_y += dy

        if self.bbox_graphic:
            self.bbox_graphic.start.x += dx
            self.bbox_graphic.start.y += dy
            self.bbox_graphic.end.x += dx
            self.bbox_graphic.end.y += dy
```

### 3.2 Workflow

```
1. CREATE COMPONENT UNITS
   ├─ Add component to schematic
   ├─ Add pin labels and TRACK which belong to this component
   ├─ Calculate bbox including component's labels
   └─ Create ComponentUnit bundling component + labels + bbox

2. CALCULATE SHEET DIMENSIONS
   ├─ Calculate sheet width based on pin count and name length
   ├─ Calculate label extension width (longest net name)
   └─ Bbox width = sheet width + label extension

3. COMBINE FOR PLACEMENT
   ├─ Add components to placement list: [(ref, bbox_width, bbox_height)]
   ├─ Add sheets to placement list: [("SHEET_name", bbox_width, bbox_height)]
   └─ Run text-flow algorithm on combined list

4. APPLY PLACEMENTS
   ├─ Move ComponentUnits to calculated positions
   ├─ Create sheets at calculated positions
   └─ Draw bounding boxes if enabled
```

## 4. Bounding Box Calculation

### 4.1 Label Tracking (Not Detection!)

**Key Insight:** We CREATE the labels, so we already know which belong to which component. No proximity detection needed!

```python
def _add_pin_level_net_labels(self) -> Dict[str, List[Label]]:
    """
    Create hierarchical labels for component pins.

    Returns: Dict mapping component reference to its labels
             Example: {"U1": [Label("VCC"), Label("GND")], ...}
    """
    component_labels = {}

    for comp in self.schematic.components:
        comp_labels = []

        for pin in get_symbol_pins(comp.lib_id):
            net_name = get_net_for_pin(comp.reference, pin.id)
            if net_name:
                label = Label(
                    text=net_name,
                    position=calculate_pin_label_position(comp, pin),
                    orientation=pin.orientation,
                    label_type=LabelType.HIERARCHICAL
                )
                self.schematic.labels.append(label)
                comp_labels.append(label)  # Track ownership!

        component_labels[comp.reference] = comp_labels

    return component_labels
```

### 4.2 Bbox Calculation with Labels

**Critical: Labels extend IN the direction pins point**

```python
def _create_component_units(self, component_labels: Dict[str, List[Label]]) -> List[ComponentUnit]:
    """Create ComponentUnit for each component with accurate bbox"""
    units = []

    for comp in self.schematic.components:
        # 1. Get base bbox (body + pins) from symbol geometry
        lib_data = SymbolLibCache.get_symbol_data(comp.lib_id)
        local_min_x, local_min_y, local_max_x, local_max_y = \
            calculate_placement_bounding_box(lib_data)

        # 2. Convert to global coordinates
        global_min_x = comp.position.x + local_min_x
        global_min_y = comp.position.y + local_min_y
        global_max_x = comp.position.x + local_max_x
        global_max_y = comp.position.y + local_max_y

        # 3. Extend bbox to include THIS COMPONENT'S labels
        labels = component_labels.get(comp.reference, [])

        for label in labels:
            label_length = len(label.text) * 1.27  # 1.27mm per character

            # Labels extend IN the direction the pin points
            if label.orientation == 0:  # Right pin → label extends RIGHT
                global_max_x = max(global_max_x, label.position.x + label_length)

            elif label.orientation == 90:  # Up pin → label extends UP
                global_min_y = min(global_min_y, label.position.y - label_length)

            elif label.orientation == 180:  # Left pin → label extends LEFT
                global_min_x = min(global_min_x, label.position.x - label_length)

            elif label.orientation == 270:  # Down pin → label extends DOWN
                global_max_y = max(global_max_y, label.position.y + label_length)

        # 4. Create ComponentUnit
        unit = ComponentUnit(
            component=comp,
            labels=labels,
            bbox_min_x=global_min_x,
            bbox_min_y=global_min_y,
            bbox_max_x=global_max_x,
            bbox_max_y=global_max_y
        )
        units.append(unit)

    return units
```

## 5. Unified Text-Flow Placement

### 5.1 Sheet Bounding Box Calculation

Hierarchical sheets have bounding boxes that include:
1. Sheet rectangle dimensions (based on pin count)
2. Pin label extensions beyond the sheet rectangle

```python
def calculate_sheet_bbox(sheet_name: str, subcircuit) -> Tuple[float, float, float, float]:
    """Calculate sheet dimensions including label extensions"""

    # Sheet height based on pin count
    pin_count = len(subcircuit.nets)
    pin_spacing = 2.54
    padding = 5.08
    sheet_height = max(20.32, (pin_count * pin_spacing) + (2 * padding))

    # Sheet width based on name length
    min_width = 25.4
    char_width = 1.5
    name_width = len(sheet_name) * char_width + 10
    sheet_width = max(min_width, name_width)

    # Label extension (labels extend to the right of sheet)
    max_label_length = max((len(net.name) for net in subcircuit.nets), default=0)
    label_width = max_label_length * 1.27 + 10

    # Bbox width = sheet width + label extension
    bbox_width = sheet_width + label_width
    bbox_height = sheet_height

    return (sheet_width, sheet_height, bbox_width, bbox_height)
```

### 5.2 Combined Placement

Components and sheets are placed together in a single algorithm:

```python
def place_with_text_flow(items: List[Tuple[str, float, float]],
                        spacing: float = 15.0) -> List[Tuple[str, float, float]]:
    """
    Text-flow placement: largest-first, left-to-right, top-to-bottom.

    Args:
        items: List of (reference, width, height) for components and sheets
        spacing: Spacing between bounding box edges (default 15mm)

    Returns:
        List of (reference, center_x, center_y) positions
    """
    # Sort by area (largest first)
    sorted_items = sorted(items, key=lambda x: x[1] * x[2], reverse=True)

    placements = []
    current_x = sheet.min_x
    current_y = sheet.min_y
    row_height = 0.0

    for ref, width, height in sorted_items:
        # Check if fits in current row
        if current_x + width > sheet.max_x:
            # Wrap to next row
            current_x = sheet.min_x
            current_y += row_height + spacing
            row_height = 0.0

        # Calculate center position
        center_x = current_x + width / 2
        center_y = current_y + height / 2

        placements.append((ref, center_x, center_y))

        # Update for next item
        current_x += width + spacing
        row_height = max(row_height, height)

    return placements
```

### 5.3 Applying Placements

```python
# Separate components from sheets
placement_map = {ref: (x, y) for ref, x, y in placements}

# Apply to components
for unit in component_units:
    if unit.component.reference in placement_map:
        x, y = placement_map[unit.component.reference]
        unit.move_to(x, y)  # Moves component + labels + bbox atomically

# Apply to sheets
for child in self.circuit.child_instances:
    sheet_ref = f"SHEET_{child['sub_name']}"
    if sheet_ref in placement_map:
        x, y = placement_map[sheet_ref]
        child["x"] = x
        child["y"] = y
```

## 6. Sheet Bounding Box Visualization

When `draw_bounding_boxes=True`, sheets also get visual bounding box rectangles:

```python
def _add_subcircuit_sheets(self):
    """Create hierarchical sheets at pre-calculated positions"""
    for child_info in self.circuit.child_instances:
        # Get position and dimensions from placement
        cx = child_info.get("x", 50.0)
        cy = child_info.get("y", 50.0)
        sheet_width = child_info.get("sheet_width", 30.0)
        sheet_height = child_info.get("sheet_height", 30.0)

        # Create sheet
        sheet = Sheet(
            name=sub_name,
            filename=f"{sub_name}.kicad_sch",
            position=Point(sheet_x, sheet_y),
            size=(sheet_width, sheet_height)
        )
        self.schematic.sheets.append(sheet)

        # Draw bounding box (includes label extension)
        if self.draw_bounding_boxes:
            bbox_width = child_info.get("bbox_width", sheet_width + 20)
            bbox_height = child_info.get("bbox_height", sheet_height)

            bbox_min_x = cx - (bbox_width / 2)
            bbox_min_y = cy - (bbox_height / 2)
            bbox_max_x = cx + (bbox_width / 2)
            bbox_max_y = cy + (bbox_height / 2)

            bbox_rect = Rectangle(
                start=Point(bbox_min_x, bbox_min_y),
                end=Point(bbox_max_x, bbox_max_y),
                stroke_width=0.127,
                stroke_type="solid",
                fill_type="none"
            )
            self.schematic.add_rectangle(bbox_rect)
```

## 7. Key Implementation Details

### 7.1 Modified Files

- `src/circuit_synth/kicad/sch_gen/schematic_writer.py` - Main placement logic
- `src/circuit_synth/kicad/sch_gen/symbol_geometry.py` - Pin label bbox calculations
- `src/circuit_synth/kicad/sch_gen/main_generator.py` - Placement workflow
- `src/circuit_synth/kicad/schematic/component_unit.py` - ComponentUnit dataclass
- `src/circuit_synth/kicad/schematic/text_flow_placement.py` - Placement algorithm

### 7.2 Key Methods

- `_add_pin_level_net_labels()` - Creates labels and returns Dict[str, List[Label]]
- `_create_component_units()` - Creates ComponentUnit objects with accurate bboxes
- `_draw_component_unit_bboxes()` - Draws visual debugging rectangles
- `_place_components()` - Unified text-flow placement for sheets and components
- `_add_subcircuit_sheets()` - Creates sheets at calculated positions with bboxes

### 7.3 Constants

```python
LABEL_CHAR_WIDTH = 1.27      # mm per character (KiCad default)
COMPONENT_SPACING = 15.0     # mm between bbox edges
SHEET_MIN_WIDTH = 25.4       # mm minimum sheet width
SHEET_MIN_HEIGHT = 20.32     # mm minimum sheet height
PIN_SPACING = 2.54           # mm between sheet pins
SHEET_PADDING = 5.08         # mm padding inside sheet
```

## 8. Comparison: Before vs After

### Before
- ❌ Proximity-based label detection (30mm radius)
- ❌ Labels from nearby components incorrectly included in bbox
- ❌ Bbox dimensions changed based on placement location
- ❌ Components and sheets placed separately
- ❌ Label orientation logic inverted (labels extended opposite pin direction)
- ❌ No way to move component + labels + bbox as unit

### After
- ✅ Label tracking at creation time (no detection needed)
- ✅ Bbox includes only the component's own labels
- ✅ Bbox dimensions independent of placement location
- ✅ Components and sheets placed together in unified algorithm
- ✅ Labels correctly extend IN pin direction
- ✅ ComponentUnit moves all elements atomically

## 9. Testing

### Test Cases

**Simple Component (Resistor)**
- Minimal bbox around body + 2 labels (one each end)
- Width = body_width + 2 × label_length

**Large Component (RP2040)**
- Bbox includes all 57 pin labels
- Left-side labels extend bbox left
- Top-side labels extend bbox up
- No proximity false positives

**Hierarchical Sheet**
- Bbox = sheet_width + label_extension
- All pin labels fully enclosed
- Visual bbox matches calculated dimensions

**Unified Placement**
- Sheets and components mixed in left-to-right flow
- Largest items first
- Consistent 15mm spacing
- Top-aligned rows

### Success Criteria

- ✅ All hierarchical labels fully enclosed by bounding boxes
- ✅ No labels from component A in component B's bbox
- ✅ Sheets placed alongside components
- ✅ Bounding boxes accurately represent visual extent
- ✅ Moving ComponentUnit moves all elements together
- ✅ Bbox dimensions don't change when component moves

## 10. Future Enhancements

- Connection-aware placement (minimize wire crossings)
- Smarter packing algorithms (tetris-style)
- User-configurable spacing and alignment
- Bbox color coding by component type
- Export bbox data for external layout tools
- Support for rotated components in bbox calculation

## 11. Known Limitations

- Sheet sizes limited to A4 and A3
- Simple left-to-right flow (no optimization for connectivity)
- No manual position overrides
- Fixed 15mm spacing (not user-configurable via API)

---

**Status:** Fully implemented and merged into main branch.
