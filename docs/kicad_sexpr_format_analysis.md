# KiCad S-Expression Format Analysis

## Overview
KiCad uses S-expressions (symbolic expressions) for all its file formats since version 6.0. This analysis is based on actual KiCad files and official documentation.

## File Structure

### Top-Level Structure
```lisp
(kicad_sch
  (version 20250114)
  (generator "circuit_synth")
  (generator_version "9.0")
  (uuid "73f681eb-68b1-42a6-bfdd-5dd3100f5499")
  (paper "A4")
  (lib_symbols ...)
  ; Component instances
  (symbol ...)
  (symbol ...)
  ; Hierarchical labels
  (hierarchical_label ...)
  ; Other elements
)
```

## Key Format Characteristics

### 1. **No Dotted Pairs**
KiCad uses **list notation exclusively**, never dotted pairs:
- ✅ Correct: `(uuid "3928d965-a820-48b7-9e9f-7238f7774e70")`
- ❌ Wrong: `(uuid . "3928d965-a820-48b7-9e9f-7238f7774e70")`

### 2. **Attribute-Based Structure**
Elements use key-value pairs, not positional arguments:
```lisp
(symbol
  (lib_id "Device:R")        ; Named attribute
  (at 100 100 0)             ; Position with values
  (unit 1)                   ; Named with value
  (uuid "...")               ; Named with string
)
```

### 3. **Nested Parentheses**
Deep nesting for properties and effects:
```lisp
(property "Reference" "R1"
  (at 100 97.46 0)
  (effects
    (font
      (size 1.27 1.27)
    )
    (justify left)
  )
)
```

## Symbol (Component) Format

### Symbol Instance in Schematic
```lisp
(symbol
  (lib_id "Device:C")                ; Library reference
  (at 162.56 66.04 0)                ; X Y rotation
  (unit 1)                           ; Unit number
  (exclude_from_sim no)              ; Simulation flag
  (in_bom yes)                       ; BOM inclusion
  (on_board yes)                     ; Board placement
  (dnp no)                           ; Do Not Populate
  (fields_autoplaced yes)            ; Auto-placement flag
  (uuid "e4890586-c70f-495a-a5b4-fb7770a52e3f")
  
  ; Properties with nested effects
  (property "Reference" "C1"
    (at 162.56 61.04 0)
    (effects
      (font (size 1.27 1.27))
      (justify left)
    )
  )
  
  (property "Value" "10uF"
    (at 162.56 71.04 0)
    (effects
      (font (size 1.27 1.27))
      (justify left)
    )
  )
  
  (property "Footprint" "Capacitor_SMD:C_0805_2012Metric"
    (at 162.56 76.04 0)
    (effects
      (font (size 1.27 1.27))
      (hide yes)
    )
  )
  
  ; Instance tracking for hierarchy
  (instances
    (project "ESP32_C6_Dev_Board"
      (path "/f6e4bbdf-7565-4122-8308-8c7c210730ff/..."
        (reference "C1")
        (unit 1)
      )
    )
  )
)
```

## Hierarchical Label Format

```lisp
(hierarchical_label
  GND                          ; Label text (no quotes if simple)
  (shape input)                ; Direction: input/output/bidirectional/passive
  (at 38.1 88.9 270)          ; X Y rotation
  (effects
    (font
      (size 1.27 1.27)
    )
    (justify right)            ; Text justification
  )
  (uuid "486bce57-87bc-45e9-a95b-4dd7e1c256b7")
)
```

## Key Syntax Rules

### 1. **Token Rules**
- All tokens are **lowercase**: `symbol`, `lib_id`, `at`
- No whitespace in tokens (use underscore): `fields_autoplaced`
- Tokens delimited by parentheses `(` and `)`

### 2. **String Quoting**
- Simple identifiers don't need quotes: `GND`, `yes`, `no`
- Complex strings need quotes: `"Device:R"`, `"10uF"`
- UUIDs always quoted: `"e4890586-c70f-495a-a5b4-fb7770a52e3f"`
- Library IDs always quoted: `"Capacitor_SMD:C_0805_2012Metric"`

### 3. **Numeric Values**
- Coordinates are floating point: `162.56 66.04`
- Rotation in degrees: `0`, `90`, `180`, `270`
- Sizes typically in mm: `1.27`
- Integers for counts: `unit 1`

### 4. **Boolean Values**
- Use `yes`/`no` not `true`/`false`
- Examples: `(in_bom yes)`, `(dnp no)`

## Common Elements

### Position/At Token
```lisp
(at X Y [rotation])
; Examples:
(at 100 100)        ; No rotation
(at 100 100 0)      ; Explicit 0° rotation
(at 38.1 88.9 270)  ; 270° rotation
```

### Effects Token
```lisp
(effects
  (font
    (size WIDTH HEIGHT)     ; Usually same value
  )
  (justify left|center|right)
  (hide yes|no)            ; Optional
)
```

### UUID Token
```lisp
(uuid "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
```
- Always quoted
- Standard UUID v4 format
- Unique for each element

## Wire and Connection Elements

### Wire
```lisp
(wire
  (pts
    (xy 100 100)
    (xy 150 100)
  )
  (stroke
    (width 0.254)
    (type default)
  )
  (uuid "...")
)
```

### Junction
```lisp
(junction
  (at 100 100)
  (diameter 1.0)
  (color 0 0 0 1)  ; RGBA
  (uuid "...")
)
```

### No Connect
```lisp
(no_connect
  (at 100 100)
  (uuid "...")
)
```

## Library Symbol Definitions

In the `lib_symbols` section:
```lisp
(lib_symbols
  (symbol "Device:R"
    (pin_numbers hide)
    (pin_names (offset 0.254))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    
    (property "Reference" "R"
      (at 0 0 0)
      (effects ...)
    )
    
    ; Graphics shapes
    (symbol "Device:R_0_1"
      (rectangle
        (start -1.016 2.54)
        (end 1.016 -2.54)
        (stroke (width 0.254) (type default))
        (fill (type none))
      )
    )
    
    ; Pin definitions
    (symbol "Device:R_1_1"
      (pin passive line
        (at 0 3.81 270)
        (length 1.27)
        (name "~" (effects ...))
        (number "1" (effects ...))
      )
    )
  )
)
```

## Important Implementation Notes

### For Rust Implementation with lexpr

1. **Always use `Value::list`**, never `Value::cons`
2. Build nested structures with `Vec<Value>`
3. Order matters for some elements (e.g., `at` values)
4. Maintain proper indentation for readability (though not required)

### Example Rust Code (Correct)
```rust
// Correct: List notation
let uuid_sexp = Value::list(vec![
    Value::symbol("uuid"),
    Value::string("3928d965-a820-48b7-9e9f-7238f7774e70"),
]);

// Position with values
let at_sexp = Value::list(vec![
    Value::symbol("at"),
    Value::from(100.0),
    Value::from(100.0),
    Value::from(0),
]);
```

## Version History

- KiCad 6.0: Introduced S-expression format
- KiCad 7.0: Minor additions, same core structure
- KiCad 8.0: Current stable version
- KiCad 9.0: Development version (as of 2024)

Version token format: `YYYYMMDD` (e.g., `20250114`)

## Why S-Expressions?

KiCad chose S-expressions because:
1. **Human readable** - Easy to understand and edit manually
2. **Hierarchical** - Natural for nested electronic design data
3. **Proven** - Based on Specctra DSN format
4. **Version control friendly** - Text-based, diffable
5. **Extensible** - Easy to add new attributes without breaking compatibility

## Common Pitfalls

1. **Don't use dotted pairs** - KiCad doesn't support them
2. **Quote complex strings** - Library IDs, footprints, UUIDs
3. **Use correct boolean values** - `yes`/`no` not `true`/`false`
4. **Maintain token case** - All lowercase for tokens
5. **Include all required fields** - Missing fields can cause parse errors