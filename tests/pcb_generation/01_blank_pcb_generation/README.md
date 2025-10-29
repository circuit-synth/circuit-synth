# Test 01: Blank PCB Generation

## What This Tests

Generation of a blank PCB (no components) with a rectangular board outline (200x150mm).

## When This Situation Happens

- Starting a new PCB design with an empty template
- Testing basic PCB generation infrastructure
- Verifying KiCad project structure and file creation
- Foundation test for all other PCB placement operations

## What Should Work

1. Python circuit with no components generates valid KiCad PCB
2. PCB file is created and has valid KiCad structure
3. PCB can be loaded with kicad-pcb-api without errors
4. Board outline (200x150mm rectangular) is present
5. No components in the PCB (blank)

## Why This Matters

This is the **foundation test** for PCB generation. A blank PCB:
- Proves basic PCB file generation works
- Validates KiCad project structure is correct
- Confirms board outline setup is functional
- Provides baseline for all other tests

Without this working, no other PCB tests can pass.

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

pcb = PCBBoard.load(str(pcb_file))

# Validate structure
assert pcb is not None  # PCB loads without errors
assert len(pcb.footprints) == 0  # No components (blank)
assert board_outline_exists()  # Board outline present
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/01_blank_pcb_generation

# Generate blank PCB
uv run fixture.py

# Check files created
ls -la blank_pcb/

# Open in KiCad - should be empty PCB with board outline
open blank_pcb/blank_pcb.kicad_pro
```

## Expected Result

- ✅ KiCad project generated (.kicad_pro)
- ✅ PCB file generated (.kicad_pcb)
- ✅ PCB opens successfully in KiCad
- ✅ PCB is empty (no components)
- ✅ Board outline visible (200x150mm rectangle)
- ✅ No errors during generation
- ✅ kicad-pcb-api can load PCB without errors

## Test Output Example

```
======================================================================
STEP 1: Generate blank PCB from Python
======================================================================
✅ Step 1: PCB generated successfully
   - Project file: blank_pcb.kicad_pro
   - PCB file: blank_pcb.kicad_pcb

======================================================================
STEP 2: Validate PCB structure with kicad-pcb-api
======================================================================
✅ Step 2: PCB loaded successfully
   - PCB object created: <kicad_pcb_api.PCBBoard object>

======================================================================
STEP 3: Validate board structure
======================================================================
✅ Step 3: Board structure validated
   - Footprints: 0 (expected: 0) ✓

======================================================================
STEP 4: Validate board outline
======================================================================
✅ Step 4: Board outline check
   - Edge.Cuts layer found in PCB file

======================================================================
✅ TEST PASSED: Blank PCB Generation
======================================================================
Summary:
  - PCB structure valid ✓
  - No components (blank) ✓
  - Board outline present ✓
  - Ready for placement tests ✓
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **PCB File Exists** | File system check | `.kicad_pcb` exists |
| **PCB Valid** | kicad-pcb-api.load() | Loads without error |
| **PCB Structure** | `isinstance(pcb, PCBBoard)` | True |
| **Footprints** | `len(pcb.footprints)` | 0 (blank) |
| **Board Outline** | Edge.Cuts layer | Present in file |
| **Board Dimensions** | 200x150mm | As specified |

## Test Classification

- **Category**: Foundation Test
- **Priority**: CRITICAL - Required for all other tests
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Simple (no components, no interactions)
- **Execution Time**: ~3 seconds

## Notes

- This test establishes baseline PCB generation works
- All subsequent tests build on this foundation
- No special KiCad configuration needed
- Blank PCB is starting point for all iterative workflows
