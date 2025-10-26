# kicad-sch-api Enhancement Proposal

## Overview

The current kicad-sch-api library provides a good foundation for KiCad schematic manipulation, but lacks public accessor properties for several important schematic elements. This document proposes enhancements to make the library more complete and usable for comprehensive schematic testing and validation.

## Current State

### Currently Public Properties
- `components` - List of circuit components
- `wires` - List of wire connections
- `junctions` - List of junction points
- `version` - Schematic format version
- `uuid` - Unique schematic identifier
- `generator` - Generator information
- `title_block` - Title block dictionary

### Currently Private/Inaccessible Elements
The following elements exist in the schematic `_data` dictionary but lack public accessor properties:

1. **Texts** (`texts`) - Free text annotations
2. **Text Boxes** (`text_boxes`) - Bounded text regions
3. **Labels** (`labels`) - Signal labels
4. **Hierarchical Labels** (`hierarchical_labels`) - Sheet hierarchical labels
5. **Rectangles** (`rectangles`) - Rectangular graphic elements
6. **Polylines** (`polylines`) - Multi-segment lines
7. **Circles** (`circles`) - Circular graphic elements
8. **Arcs** (`arcs`) - Arc graphic elements
9. **Beziers** (`beziers`) - Bezier curve elements
10. **Images** (`images`) - Embedded or linked images
11. **No-Connects** (`no_connects`) - No-connect markers
12. **Nets** (`nets`) - Net definitions
13. **Sheets** (`sheets`) - Hierarchical sheet references

## Proposed Enhancements

### 1. Add Public Properties for All Schematic Elements

Add read-only properties to the `Schematic` class:

```python
class Schematic:
    @property
    def texts(self) -> List[Dict]:
        """Get list of text elements in the schematic."""
        return self._data.get('texts', [])

    @property
    def text_boxes(self) -> List[Dict]:
        """Get list of text boxes in the schematic."""
        return self._data.get('text_boxes', [])

    @property
    def labels(self) -> List[Dict]:
        """Get list of signal labels in the schematic."""
        return self._data.get('labels', [])

    @property
    def hierarchical_labels(self) -> List[Dict]:
        """Get list of hierarchical labels in the schematic."""
        return self._data.get('hierarchical_labels', [])

    @property
    def rectangles(self) -> List[Dict]:
        """Get list of rectangles in the schematic."""
        return self._data.get('rectangles', [])

    @property
    def polylines(self) -> List[Dict]:
        """Get list of polylines in the schematic."""
        return self._data.get('polylines', [])

    @property
    def circles(self) -> List[Dict]:
        """Get list of circles in the schematic."""
        return self._data.get('circles', [])

    @property
    def arcs(self) -> List[Dict]:
        """Get list of arcs in the schematic."""
        return self._data.get('arcs', [])

    @property
    def beziers(self) -> List[Dict]:
        """Get list of Bezier curves in the schematic."""
        return self._data.get('beziers', [])

    @property
    def images(self) -> List[Dict]:
        """Get list of images in the schematic."""
        return self._data.get('images', [])

    @property
    def no_connects(self) -> List[Dict]:
        """Get list of no-connect markers in the schematic."""
        return self._data.get('no_connects', [])

    @property
    def nets(self) -> List[Dict]:
        """Get list of nets in the schematic."""
        return self._data.get('nets', [])

    @property
    def sheets(self) -> List[Dict]:
        """Get list of hierarchical sheets in the schematic."""
        return self._data.get('sheets', [])
```

### 2. Add Validation/Query Methods

Useful methods for schematic validation:

```python
def get_text_by_content(self, content: str) -> Optional[Dict]:
    """Find a text element by its content."""
    for text in self.texts:
        if text.get('text') == content:
            return text
    return None

def get_label_by_name(self, name: str) -> Optional[Dict]:
    """Find a label by its name."""
    for label in self.labels:
        if label.get('name') == name:
            return label
    return None

def get_net_by_name(self, name: str) -> Optional[Dict]:
    """Find a net by its name."""
    for net in self.nets:
        if net.get('name') == name:
            return net
    return None

def has_graphic_elements(self) -> bool:
    """Check if schematic has any graphic elements."""
    return bool(self.rectangles or self.circles or self.arcs or
                self.polylines or self.beziers or self.images)

def count_all_elements(self) -> Dict[str, int]:
    """Get count of all schematic elements."""
    return {
        'components': len(self.components),
        'wires': len(self.wires),
        'junctions': len(self.junctions),
        'texts': len(self.texts),
        'text_boxes': len(self.text_boxes),
        'labels': len(self.labels),
        'hierarchical_labels': len(self.hierarchical_labels),
        'rectangles': len(self.rectangles),
        'polylines': len(self.polylines),
        'circles': len(self.circles),
        'arcs': len(self.arcs),
        'beziers': len(self.beziers),
        'images': len(self.images),
        'no_connects': len(self.no_connects),
        'nets': len(self.nets),
        'sheets': len(self.sheets),
    }
```

### 3. Add Element Property Classes

For better type safety and IDE support, create wrapper classes for elements:

```python
class SchematicText:
    def __init__(self, data: Dict):
        self._data = data

    @property
    def text(self) -> str:
        return self._data.get('text', '')

    @property
    def position(self) -> Tuple[float, float]:
        return (self._data.get('at', [0])[0],
                self._data.get('at', [0, 0])[1])

    @property
    def font_size(self) -> Tuple[float, float]:
        effects = self._data.get('effects', {})
        font = effects.get('font', {})
        size = font.get('size', [])
        return (size[0] if len(size) > 0 else 0,
                size[1] if len(size) > 1 else 0)

class SchematicLabel:
    def __init__(self, data: Dict):
        self._data = data

    @property
    def name(self) -> str:
        return self._data.get('name', '')

    @property
    def position(self) -> Tuple[float, float]:
        return (self._data.get('at', [0])[0],
                self._data.get('at', [0, 0])[1])

# Similar classes for other elements...
```

## Implementation Priority

### Phase 1 (High Priority) - Basic Properties
- Add public properties for: texts, labels, hierarchical_labels, no_connects, nets
- These are commonly used in schematic validation

### Phase 2 (Medium Priority) - Graphics
- Add public properties for: rectangles, polylines, circles, arcs, beziers, images
- These enable complete schematic structure validation

### Phase 3 (Medium Priority) - Utility Methods
- Add: get_text_by_content(), get_label_by_name(), get_net_by_name()
- Add: has_graphic_elements(), count_all_elements()
- These improve usability for common operations

### Phase 4 (Low Priority) - Type Safety
- Create wrapper classes for elements
- Provides IDE autocomplete and type checking

## Benefits

1. **Complete API Coverage** - All schematic elements are accessible through public interface
2. **Better Testing** - Tests can comprehensively validate schematic structure
3. **Type Safety** - Properties and wrappers enable IDE support
4. **Consistency** - Properties follow same pattern as existing (components, wires, junctions)
5. **Backward Compatible** - Only adds new properties, doesn't change existing API

## Circuit-Synth Usage

These enhancements would enable circuit-synth tests to:

```python
# Before (accessing private _data)
texts = schematic._data.get('texts', [])
labels = schematic._data.get('labels', [])

# After (using public properties)
texts = schematic.texts
labels = schematic.labels

# New validation capabilities
assert schematic.has_graphic_elements() == False
element_counts = schematic.count_all_elements()
assert element_counts['components'] == 1
assert element_counts['nets'] > 0

# Find specific elements
gnd_label = schematic.get_label_by_name('GND')
if gnd_label:
    assert gnd_label['position'] == (10.0, 20.0)
```

## Recommendation

I recommend implementing **Phase 1** (basic properties) immediately, as these are essential for comprehensive schematic validation. Phases 2-4 can follow as needed.

The basic properties require minimal code changes and provide maximum immediate benefit for circuit-synth testing and validation workflows.
