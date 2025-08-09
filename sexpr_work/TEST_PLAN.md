# KiCad Schematic Generation Test Plan - Multi-Unit Components

## PROBLEM
1. ~~KiCad shows "R?" instead of proper references~~ **FIXED**
2. ~~Multi-unit components not generating all units~~ **FIXED - all 7 units generated**
3. **CURRENT ISSUE**: KiCad displays "U1" for all units instead of "U1A", "U1B", "U1C", etc.

## CRITICAL REQUIREMENT
**We must NEVER require users to run annotation in KiCad. The generated schematic must be complete and display unit suffixes (A, B, C, etc.) automatically when opened.**

## OBJECTIVE
Generate KiCad schematics with **EXACT** formatting that matches working KiCad files - including automatic display of unit suffixes for multi-unit components.

## TEST CASES

### Test 1: Single Resistor (COMPLETED ✅)
Single resistor (R1) circuit - minimal test to isolate formatting issues.
**Status**: FIXED - References display correctly

### Test 2: 74HC14 Hex Inverter (IN PROGRESS)
Multi-unit component with 7 units total:
- Units 1-6: Individual inverter gates (should display as U1A-U1F)
- Unit 7: Power supply pins (should display as U1G)

**Current Status**: 
- ✅ All 7 units are generated
- ✅ Each has correct `(unit x)` field
- ✅ All share reference "U1"
- ❌ KiCad displays "U1" instead of "U1A", "U1B", etc.

## DETAILED TEST REQUIREMENTS

### Input Code (User's Perspective)
```python
# Users should only need to declare the component once
u1 = Component(
    symbol="74xx:74HC14",
    ref="U",
    value="74HC14",
    footprint="Package_SO:TSSOP-14_4.4x5mm_P0.65mm"
)
```

### Expected Output (Generated Schematic)
The system should automatically generate **7 separate symbol instances** in the schematic:

#### Symbol Instances Required:
1. **Unit 1** (pins 1,2) - First inverter gate
2. **Unit 2** (pins 3,4) - Second inverter gate  
3. **Unit 3** (pins 5,6) - Third inverter gate
4. **Unit 4** (pins 9,8) - Fourth inverter gate
5. **Unit 5** (pins 11,10) - Fifth inverter gate
6. **Unit 6** (pins 13,12) - Sixth inverter gate
7. **Unit 7** (pins 14,7) - Power supply (VCC/GND)

#### Each Symbol Instance Must Have:
```sexpr
(symbol
    (lib_id "74xx:74HC14")
    (at <x> <y> 0)
    (unit <N>)  ; Where N is 1-7
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (dnp no)
    (fields_autoplaced yes)
    (uuid "<unique-uuid>")
    (property "Reference" "U1"  ; Same reference for all units
        (at <x> <y> 0)
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
    (property "Value" "74HC14"
        ...
    )
    (property "Footprint" "Package_SO:TSSOP-14_4.4x5mm_P0.65mm"
        ...
    )
    ; All pin definitions for this unit
    (pin "1" (uuid "..."))  ; Only pins relevant to this unit
    (pin "2" (uuid "..."))
    ...
    (instances
        (project "reference"
            (path "/project-uuid"
                (reference "U1")  ; Same reference
                (unit <N>)        ; Specific unit number
            )
        )
    )
)
```

### Verification Steps

#### Step 1: Check Symbol Count
```bash
# Should find exactly 7 symbol instances for 74HC14
grep -c 'lib_id "74xx:74HC14"' reference_generated/reference_generated.kicad_sch
# Expected: 7
```

#### Step 2: Verify Unit Numbers
```bash
# Should find units 1 through 7
for i in {1..7}; do
    echo -n "Unit $i: "
    grep -c "(unit $i)" reference_generated/reference_generated.kicad_sch
done
# Expected: Each unit appears exactly once
```

#### Step 3: Verify References
```bash
# All units should have reference "U1"
grep -A 10 'lib_id "74xx:74HC14"' reference_generated/reference_generated.kicad_sch | \
    grep 'property "Reference"' | \
    grep -o '"U[0-9]*"' | sort -u
# Expected: Only "U1"
```

#### Step 4: Visual Verification in KiCad
1. Open `reference_generated/reference_generated.kicad_pro` in KiCad
2. Verify all 7 units appear on schematic
3. Check that units are labeled U1 (not U1A, U1B, etc. - KiCad handles that)
4. Verify no "?" references appear

### Key Implementation Requirements

1. **Symbol Library Parsing**: Must detect multi-unit symbols
   - Parse symbol definitions like `74HC14_1_0`, `74HC14_2_0`, etc.
   - Identify total unit count from symbol library

2. **Automatic Unit Expansion**: When user creates component
   - Detect if symbol has multiple units
   - Automatically create symbol instance for each unit
   - Assign same reference to all units
   - Set correct unit number for each instance

3. **Pin Mapping**: Each unit has different pins
   - Unit 1: pins 1,2
   - Unit 2: pins 3,4
   - Unit 3: pins 5,6
   - Unit 4: pins 9,8 (note: reversed order)
   - Unit 5: pins 11,10
   - Unit 6: pins 13,12
   - Unit 7: pins 14,7 (power pins)

4. **Placement**: Units should be placed sensibly
   - Could be in a row/column
   - Power unit typically placed separately
   - Each unit needs unique position (x,y)

### Success Criteria
✅ Single component declaration generates all 7 units
✅ All units share same reference (U1)
✅ Each unit has correct unit number (1-7)
✅ Each unit has unique UUID
✅ Each unit has unique position
❌ Units display with suffixes (U1A, U1B, etc.) without annotation
✅ No "?" references
⚠️ Structure matches reference but display differs

## TEST METHODOLOGY

### Step 1: Generate Test Files
```bash
cd /Users/shanemattner/Desktop/circuit-synth3/sexpr_work
./run_reference_example.sh
```

### Step 2: Compare Generated vs Reference
```bash
# Exact diff comparison
diff -u reference/reference.kicad_sch reference_generated/reference_generated.kicad_sch

# Focus on critical sections
grep -A 10 "(instances" reference/reference.kicad_sch
grep -A 10 "(instances" reference_generated/reference_generated.kicad_sch
```

### Step 3: Verify in KiCad
1. Open `reference_generated/reference_generated.kicad_pro` in KiCad
2. Check if resistor shows "R1" or "R?"
3. No manual annotation should be needed

## CRITICAL FORMATTING REQUIREMENTS

### 1. Instances Block (MOST CRITICAL)
```sexpr
(instances
    (project "reference_generated"
        (path "/uuid"
            (reference "R1")
            (unit 1)
        )
    )
)
```
- `(project "name"` must be on SAME LINE
- `(path "/uuid"` must be on SAME LINE
- Tab indentation throughout

### 2. Pin Formatting
```sexpr
(pin passive line   # All on ONE line
    (at 0 3.81 270)
    (length 1.27)
    (name "~"       # Name on same line as tag
        (effects ...))
    (number "1"     # Number on same line as tag
        (effects ...))
)
```

### 3. Library Symbol Properties
```sexpr
(pin_numbers hide)      # NOT (pin_numbers (hide yes))
(pin_names (offset 0))  # NOT 0.254
```

### 4. Number Formatting
- No unnecessary decimals: `0` not `0.0`
- Keep needed decimals: `45.72` stays as is

## SUCCESS CRITERIA
1. **KiCad displays "R1"** instead of "R?" ✅ PRIMARY GOAL
2. **Zero diff** between reference and generated (except UUIDs)
3. **No manual fixes needed** in KiCad

## FILE STRUCTURE
```
sexpr_work/
├── reference/                 # KiCad-created reference (single R1)
│   └── reference.kicad_sch   
├── reference_generated/       # Circuit-synth output
│   └── reference_generated.kicad_sch
├── reference_circuit-synth/   # Python source
│   └── main.py               # Single resistor circuit
└── run_reference_example.sh   # Test script
```

## KNOWN ISSUES TO FIX
1. ✅ Instances block formatting
2. ✅ Pin_numbers format  
3. ✅ Offset value (0 not 0.254)
4. ⚠️ Pin formatting (must be single line)
5. ⚠️ Property positions still differ
6. ⚠️ Generator field differences

## FINDINGS AND DISCOVERIES

### What We've Learned About Multi-Unit Components

1. **File Structure Success**:
   - Successfully generating all 7 units with correct `(unit x)` fields
   - Each unit has proper instances block with unit number
   - References are correctly shared (all "U1")
   - UUIDs are unique for each unit

2. **Display Issue - Unit Suffixes Not Showing**:
   - KiCad shows "U1" for all units instead of "U1A", "U1B", etc.
   - The `(unit x)` field is present and correct in the file
   - Reference schematic shows proper suffixes without manual annotation
   - **This suggests we're missing a critical field or property**

3. **Key Implementation Details**:
   - Bypassed ComponentManager's duplicate reference check
   - Directly creating SchematicSymbol objects for each unit
   - Using SymbolInstance objects (not dicts) for instances
   - Project settings have correct `subpart_first_id: 65` (ASCII 'A')

4. **Testing Approach**:
   - Using `/Users/shanemattner/Desktop/circuit-synth3/sexpr_work/run_reference_example.sh`
   - Script cleans cache on every run to ensure fresh generation
   - Comparing generated files directly with reference files

5. **ROOT CAUSE IDENTIFIED**:
   - **lib_symbols section is incomplete!**
   - Reference has 14 symbol definitions: `74HC14_1_0` through `74HC14_7_1` (2 per unit)
   - Our generated file only has 2: `74HC14_0_1` and `74HC14_1_1`
   - **KiCad needs complete symbol definitions for ALL units in lib_symbols**
   - Without these, KiCad can't display unit suffixes (A, B, C, etc.)
   - Each unit needs both _0 (background) and _1 (foreground) symbol definitions

## SOLUTION APPROACH

To fix the unit suffix display issue:

1. **Populate lib_symbols with ALL unit definitions**:
   - When detecting a multi-unit component, must extract ALL unit symbols from KiCad library
   - Each unit needs both drawing layers (_0 and _1)
   - Example for 74HC14: Need 74HC14_1_0, 74HC14_1_1, ..., 74HC14_7_0, 74HC14_7_1

2. **Symbol extraction from KiCad libraries**:
   - Parse the actual .kicad_sym files to get complete symbol definitions
   - Must include all graphical elements for each unit
   - Preserve exact formatting from library

3. **Implementation location**:
   - Likely in `s_expression.py` where lib_symbols is populated
   - Or in symbol_cache where symbols are loaded
   - Must ensure ALL units are included, not just unit 1

## DEBUGGING CHECKLIST
- [x] Instances block formatted correctly
- [x] Project name matches file name  
- [x] UUID paths are valid
- [x] Tab indentation used throughout
- [x] No extra decimals in coordinates
- [x] Pin formatting matches exactly
- [ ] Unit suffixes display without annotation
- [x] All units generated with correct unit numbers
- [ ] Investigate symbol library definitions for unit naming