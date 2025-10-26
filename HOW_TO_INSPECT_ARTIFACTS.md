# How to Inspect Test Artifacts

Your test artifacts are preserved and ready for manual inspection. Here's how to view them.

---

## Quick Start

The artifacts are in two locations:

```bash
# Test 01: Blank Projects
open tests/bidirectional_new/01_blank_projects/test_artifacts/

# Test 02: Single Component (your new fixture!)
open tests/bidirectional_new/02_single_component/test_artifacts/
```

---

## What Files to Look At

### Test 01: Blank Projects

#### Generated KiCad Files
```
tests/bidirectional_new/01_blank_projects/test_artifacts/test_01_generate_blank_kicad_from_python/
├── blank.kicad_pro     ← KiCad project file (XML format)
├── blank.kicad_sch     ← Schematic (empty, no components)
├── blank.kicad_pcb     ← PCB file (empty board with outline)
├── blank.net           ← KiCad netlist format
└── blank.json          ← JSON netlist (circuit-synth format)
```

**What to verify:**
- Open `blank.kicad_sch` in a text editor - you'll see it's valid KiCad format but empty
- Open `blank.kicad_pcb` in a text editor - contains board layers and outline (0,0 to 100,100)

#### Imported Python
```
tests/bidirectional_new/01_blank_projects/test_artifacts/test_02_import_blank_python_from_kicad/
└── imported_blank.py    ← Python code generated from blank KiCad
```

**What to verify:**
- Open `imported_blank.py` - clean Python with `@circuit` decorator and `pass` body

#### Round-Trip
```
tests/bidirectional_new/01_blank_projects/test_artifacts/test_03_blank_round_trip/
├── blank.kicad_pro     ← Generated in round-trip
├── blank.kicad_sch     ← Generated in round-trip
├── blank.json          ← Generated in round-trip
├── blank.net           ← Generated in round-trip
├── 01_python_ref.py    ← Original reference Python
└── round_trip_blank.py ← Imported back from KiCad
```

**What to verify:**
- Compare `01_python_ref.py` with `round_trip_blank.py` - should be nearly identical
- Compare `blank.kicad_sch` files from test_01 vs test_03 - should be identical (except UUIDs)

---

### Test 02: Single Component

#### Generated KiCad Files
```
tests/bidirectional_new/02_single_component/test_artifacts/test_01_generate_single_resistor_to_kicad/
├── single_resistor.kicad_pro    ← KiCad project
├── single_resistor.kicad_sch    ← Schematic with R1 resistor
├── single_resistor.json         ← JSON netlist
└── single_resistor.net          ← KiCad netlist
```

**Key points:**
- Open `single_resistor.kicad_sch` and look for:
  - Component reference: `(property "Reference" "R1"`
  - Component value: `(property "Value" "10k"`
  - Footprint: `(property "Footprint" "Resistor_SMD:R_0603_1608Metric"`
  - Position: `(at 30.48 35.56 0)` ← X, Y, rotation

#### Imported Python (HIGH QUALITY!)
```
tests/bidirectional_new/02_single_component/test_artifacts/test_02_import_single_resistor_from_kicad/
└── imported_single_resistor.py   ← EXCELLENT quality Python
```

**What to see:**
```python
r1 = Component(
    symbol="Device:R",
    ref="R1",
    value="10k",
    footprint="Resistor_SMD:R_0603_1608Metric"
)
```

All properties are preserved perfectly!

#### Round-Trip
```
tests/bidirectional_new/02_single_component/test_artifacts/test_03_single_resistor_round_trip/
├── single_resistor.kicad_pro       ← Generated in cycle 1
├── single_resistor.kicad_sch       ← Generated in cycle 1
├── single_resistor.json            ← Generated in cycle 1
├── single_resistor.net             ← Generated in cycle 1
├── 02_python_ref.py                ← Original reference Python
└── round_trip_single_resistor.py   ← Imported back from KiCad
```

**What to verify:**
- Open `02_python_ref.py` and `round_trip_single_resistor.py`
- They should be nearly identical - all component properties preserved
- KiCad files should match between test_01 and test_03 (except UUIDs)

---

## Comparing Files (Side by Side)

### Using VS Code
```bash
# Open VS Code
code tests/bidirectional_new/02_single_component/test_artifacts/

# Then use File → Compare with... to compare:
# - test_01_generate_single_resistor_to_kicad/single_resistor.kicad_sch
# - test_03_single_resistor_round_trip/single_resistor.kicad_sch
```

You should see they're identical except for UUIDs (expected).

### Using diff command
```bash
# See differences between generated and round-trip
diff tests/bidirectional_new/02_single_component/test_artifacts/test_01_generate_single_resistor_to_kicad/single_resistor.kicad_sch \
     tests/bidirectional_new/02_single_component/test_artifacts/test_03_single_resistor_round_trip/single_resistor.kicad_sch
```

Most differences will be UUIDs (which is expected and OK).

---

## Specific Things to Check

### 1. Component Properties in Schematic

Open `single_resistor.kicad_sch` and search for:
```
(property "Reference" "R1"
(property "Value" "10k"
(property "Footprint" "Resistor_SMD:R_0603_1608Metric"
```

All three should be present and correct.

### 2. Component Position in Schematic

Search for `(at` in `single_resistor.kicad_sch`:
```
(at 30.48 35.56 0)   ← X=30.48mm, Y=35.56mm, rotation=0°
```

This is where circuit-synth placed the component.

### 3. Python Import Quality

Open `imported_single_resistor.py` and verify:
- It's valid Python (should import without errors)
- Component has all properties:
  - symbol="Device:R"
  - ref="R1"
  - value="10k"
  - footprint="Resistor_SMD:R_0603_1608Metric"

### 4. Idempotency Check

Compare these files - they should be nearly identical:
- `test_01_generate.../single_resistor.kicad_sch`
- `test_03_round_trip.../single_resistor.kicad_sch`

Differences should ONLY be:
- UUID values (which change each generation - this is EXPECTED)
- Maybe minor formatting differences

Everything else should be identical.

### 5. Round-Trip Python Comparison

Compare:
- `test_02_import.../imported_single_resistor.py`
- `test_03_round_trip.../round_trip_single_resistor.py`

They should be identical (proof that round-trip preserves data).

---

## File Formats Reference

### .kicad_sch (Schematic)
- Text-based S-expression format (like Lisp)
- Contains:
  - Component symbols (from library)
  - Placed component instances
  - Connections/nets
  - Properties and metadata

### .kicad_pcb (PCB)
- Text-based S-expression format
- Contains:
  - Board dimensions and layers
  - Footprints and their positions
  - Traces and pads
  - Design rules (currently failing to generate)

### .kicad_pro (Project)
- Text-based format
- Contains project metadata and library references
- Similar to .kicad_sch format

### .json (Netlist)
- Standard JSON format
- Contains component list with properties
- Used for circuit-synth internal representation

### .net (KiCad Netlist)
- KiCad netlist format
- Contains connections between component pins

---

## Expected Quality

### What's Excellent ✅
- Schematic structure and syntax
- Component properties (all preserved)
- Position and rotation data
- Netlist generation
- Python code generation
- Round-trip idempotency

### What's Missing ⚠️
- PCB file generation (fails for single component)
- Board outline and layers
- Footprint placement data

---

## Troubleshooting

### "I don't see blank.kicad_pcb in test 02"
- ✅ Correct! It's missing because PCB generation fails for single component
- ✅ Normal for empty circuits (test 01) though
- This is a known bug in pcb_generator.py

### "The Python files look different"
- Check UUIDs - they'll be different each run
- Check timestamps - they should be absent
- Otherwise they should be identical

### "I want to view the KiCad files graphically"
- Open `.kicad_sch` or `.kicad_pro` in KiCad directly
- File → Open Project → `test_artifacts/.../single_resistor.kicad_pro`

---

## Next Steps

Once you've inspected the artifacts:

1. **Verify quality** - Check that generated schematics look correct
2. **Compare files** - Verify round-trip idempotency
3. **Test Python** - Try importing and running the generated Python files
4. **Create Test 03 fixture** - You've already done this! (02_kicad_ref with positioned resistor)

Then tests 03+ will validate:
- Position preservation
- Multiple components
- Net connectivity
- And more!

---

**Test Artifacts Ready:** ✅ All preserved and available for inspection
**Next:** Manual review of quality, then fix PCB generation bug

