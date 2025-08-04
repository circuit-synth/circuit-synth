# Key Formatting Differences Between Reference and Generated Schematics

## 1. Header Section
**Reference:**
```
(generator "eeschema")
(generator_version "9.0")
(uuid "8ea40386-79fd-4dea-8cc4-e20a6a247364")
(paper "A4")
```

**Generated:**
```
(generator "kicad_api")
(generator_version 9.0)  # Note: no quotes around version number
(uuid 9ad0211c-f30e-4cc7-bf65-64cb8792c4b9)
(paper A4)  # Note: no quotes around A4
(paper A4)  # Duplicate!
```

## 2. Symbol Properties
**Reference (compact inline):**
```
(pin_numbers
    (hide yes)
)
(property "Reference" "R"
    (at 2.032 0 90)
    (effects
        (font
            (size 1.27 1.27)
        )
    )
)
```

**Generated (expanded):**
```
(pin_numbers hide)  # More compact
(property
    "Reference"
    "R"
    (at 0.0 0.0 0)
    (effects
        (font
            (size 1.27 1.27)
        )
        (hide no)  # Extra hide directive
    )
)
```

## 3. Pin Definitions
**Reference:**
```
(pin passive line
    (at 0 3.81 270)
    (length 1.27)
    (name "~"
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
    (number "1"
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
)
```

**Generated:**
```
(pin
    passive
    line
    (at 0.0 3.81 270)  # Note: 0.0 vs 0
    (length 1.27)
    (name
        ~  # Note: no quotes around ~
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
    (number
        "1"
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
)
```

## 4. Symbol Instance
**Reference:**
```
(symbol
    (lib_id "Device:R")
    (at 125.73 81.28 0)
    (unit 1)
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (dnp no)
    (fields_autoplaced yes)
    (uuid "219d54d9-8f48-402c-807d-d317901b42be")
    (property "Reference" "R1"
        (at 128.27 80.0099 0)
        (effects
            (font
                (size 1.27 1.27)
            )
            (justify left)
        )
    )
```

**Generated:**
```
(symbol
    (lib_id Device:R)  # Note: no quotes
    (at 38.1 45.72 0)
    (in_bom yes)
    (on_board yes)
    (dnp no)
    (uuid a5f617bb-6261-4a05-95ab-2f2241f4bc01)
    (property
        "Reference"
        "R1"
        (at 38.1 40.72 0)
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
```

## 5. Other Issues
- Missing `(unit 1)` in generated symbol instance
- Missing `(exclude_from_sim no)` in generated symbol instance  
- Missing `(fields_autoplaced yes)` in generated symbol instance
- Missing `(justify left)` in Reference property effects
- Extra `(embedded_fonts no)` at end of lib_symbols in reference
- Duplicate `(paper A4)` in generated file
- Values without quotes where they should have them (e.g., "9.0" vs 9.0)
- Extra title_block section in generated file

## Key Formatting Rules Violated:
1. **Inline vs Multi-line**: Properties and pins should follow specific inline patterns
2. **Quoting**: String values like "9.0", "A4", "Device:R" need quotes
3. **Missing fields**: Several required fields are missing from symbol instances
4. **Value formatting**: Numbers like 0 vs 0.0 matter
5. **Special characters**: ~ should be quoted as "~" in some contexts