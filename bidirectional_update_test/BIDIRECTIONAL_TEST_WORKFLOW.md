# Bidirectional Update Test Workflow

## Overview

This directory contains a step-by-step test of the bidirectional update logic between KiCad and circuit-synth Python format. Each step creates a separate folder to preserve state and allow retesting.

## Directory Structure

```
bidirectional_update_test/
├── BIDIRECTIONAL_TEST_WORKFLOW.md (this file)
├── initial_kicad/                   # Step 0: Manual KiCad project
├── step1_imported_python/           # Step 1: KiCad → Python conversion
├── step2_generated_kicad/           # Step 2: Python → KiCad generation
├── step3_manual_kicad_edits/        # Step 3: Manual KiCad modifications
├── step4_reimported_python/         # Step 4: Modified KiCad → Python
├── step5_python_additions/          # Step 5: Add components in Python
├── step6_bidirectional_sync/        # Step 6: Final bidirectional sync
└── test_results/                    # Analysis and comparison results
```

## Test Workflow Steps

### Step 0: Initial KiCad Project ✅ COMPLETE

**Status:** Manual creation complete
**Location:** `initial_kicad/`

**What's here:**
- Hand-created KiCad project with basic components
- Serves as the "baseline" for testing imports

**Files:**
- `initial_kicad.kicad_sch` - Schematic
- `initial_kicad.kicad_pcb` - PCB layout
- `initial_kicad.kicad_pro` - Project settings

### Step 1: KiCad → Python Import ✅ COMPLETE

**Goal:** Convert initial KiCad project to circuit-synth Python format
**Location:** `step1_imported_python/`
**Status:** SUCCESS

**Actual Output:**
```
step1_imported_python/
└── main.py                   # Generated Python circuit code
```

**Test Results:**
- [x] Import command works correctly
- [x] Components correctly identified: C1 (capacitor), U1 (ESP32-C6-MINI-1)
- [x] Component values preserved: C="C", ESP32-C6-MINI-1="ESP32-C6-MINI-1"
- [x] Net connections maintained: +3V3, GND with proper pin mappings
- [x] Footprints preserved: C_0603_1608Metric, ESP32-C6-MINI-1
- [ ] Component positions captured: Not visible in generated code

**Actual Command Used:**
```bash
cd /Users/shanemattner/Desktop/circuit-synth3/bidirectional_update_test
mkdir -p step1_imported_python
uv run kicad-to-python initial_kicad/ step1_imported_python/
# Note: Command format is: kicad-to-python <project_dir> <output_dir>
```

**Key Findings:**
- Command format differs from expected: uses project directory, not .kicad_sch file
- Output is directory-based, not single file
- Generated code includes proper @circuit decorator
- All ESP32 ground pins correctly connected to GND net
- Unconnected pins are ignored (not included in Python code)
- Output includes KiCad generation commands ready for Step 2

### Step 2: Python → KiCad Generation 🔄 NEXT

**Goal:** Generate new KiCad project from imported Python circuit
**Location:** `step2_generated_kicad/` (will be created as `initial_kicad_generated/`)

**Expected Output:**
```
initial_kicad_generated/      # New KiCad project files
├── initial_kicad_generated.kicad_sch
├── initial_kicad_generated.kicad_pcb
├── initial_kicad_generated.kicad_pro
└── initial_kicad_generated.net
```

**Test Questions:**
- [ ] Does the Python circuit generate valid KiCad files?
- [ ] Are component symbols/footprints correct?
- [ ] Are net connections preserved?
- [ ] How do positions compare to original?
- [ ] Can KiCad open the generated project?

**Command to run:**
```bash
cd step1_imported_python
uv run python main.py
# This will generate KiCad project in current directory as initial_kicad_generated/
# Then move it to step2_generated_kicad/ for organization
mkdir -p ../step2_generated_kicad
mv initial_kicad_generated/ ../step2_generated_kicad/
```

### Step 3: Manual KiCad Edits 🔄 PENDING

**Goal:** Simulate user making manual changes in KiCad
**Location:** `step3_manual_kicad_edits/`

**Manual Changes to Make:**
1. **Component Position Changes:**
   - Move 2-3 components to different positions
   - Document original vs new positions

2. **Component Value Changes:**
   - Change a resistor value (e.g., 1kΩ → 2.2kΩ)
   - Change a capacitor value (e.g., 100nF → 220nF)

3. **Component Additions:**
   - Add a new LED with current limiting resistor
   - Add decoupling capacitor

4. **Routing Changes:**
   - Manually route some connections
   - Add test points or jumpers

**Documentation:**
```
step3_manual_kicad_edits/
├── modified_project/         # KiCad project with manual changes
├── change_log.md            # What changes were made
└── screenshots/             # Before/after screenshots
    ├── before.png
    └── after.png
```

### Step 4: Re-import Modified KiCad 🔄 PENDING

**Goal:** Import manually modified KiCad back to Python
**Location:** `step4_reimported_python/`

**Expected Output:**
```
step4_reimported_python/
├── reimported_circuit.py     # Python circuit with manual changes
├── change_detection.json    # What changes were detected
└── analysis/
    ├── diff_vs_step1.md     # Comparison with original import
    └── preservation_test.md  # What user changes were preserved
```

**Test Questions:**
- [ ] Are manual component moves preserved?
- [ ] Are value changes detected and imported?
- [ ] Are new components correctly imported?
- [ ] Are manual routing changes preserved?

**Command to run:**
```bash
uv run kicad-to-python step3_manual_kicad_edits/modified_project/circuit.kicad_sch \
  --output step4_reimported_python/reimported_circuit.py \
  --compare-with step1_imported_python/imported_circuit.py
```

### Step 5: Python Circuit Additions 🔄 PENDING

**Goal:** Add new components in Python code
**Location:** `step5_python_additions/`

**Changes to Make in Python:**
1. **Add Power Supply Circuit:**
   - Voltage regulator (3.3V LDO)
   - Input/output capacitors
   - Power indicator LED

2. **Add Communication Interface:**
   - USB-C connector
   - ESD protection diodes
   - Series resistors

**Expected Output:**
```
step5_python_additions/
├── enhanced_circuit.py       # Python circuit with additions
├── addition_log.md          # What was added
└── analysis/
    ├── new_components.json   # List of added components
    └── integration_notes.md  # How additions integrate
```

**Test Questions:**
- [ ] Can we add components without affecting existing ones?
- [ ] Are existing user modifications preserved?
- [ ] Do new and old components integrate properly?

### Step 6: Final Bidirectional Sync 🔄 PENDING

**Goal:** Generate final KiCad project with both manual and Python changes
**Location:** `step6_bidirectional_sync/`

**Expected Output:**
```
step6_bidirectional_sync/
├── final_project/           # Complete KiCad project
│   ├── final.kicad_sch     # All changes integrated
│   ├── final.kicad_pcb     # Updated PCB
│   └── final.kicad_pro     # Project settings
├── sync_report.md          # What happened during sync
└── validation/
    ├── component_check.json # All components accounted for
    ├── net_check.json      # All connections verified
    └── position_check.json # Position preservation verified
```

**Test Questions:**
- [ ] Are ALL components present (original + manual + Python)?
- [ ] Are user position changes preserved?
- [ ] Are Python additions correctly placed?
- [ ] Are all net connections correct?
- [ ] Is the final project valid and openable in KiCad?

**Command to run:**
```bash
cd step5_python_additions
uv run python enhanced_circuit.py --output step6_bidirectional_sync/final_project
```

## Validation Tests

### Test Matrix

| Feature | Step 1 | Step 2 | Step 4 | Step 6 | Status |
|---------|--------|--------|--------|--------|--------|
| Component Import | ✓ | - | ✓ | ✓ | 🔄 |
| Net Import | ✓ | - | ✓ | ✓ | 🔄 |
| Position Import | ✓ | - | ✓ | ✓ | 🔄 |
| Value Import | ✓ | - | ✓ | ✓ | 🔄 |
| KiCad Generation | - | ✓ | - | ✓ | 🔄 |
| Position Preservation | - | ? | ✓ | ✓ | 🔄 |
| Manual Change Detection | - | - | ✓ | ✓ | 🔄 |
| Python Addition Integration | - | - | - | ✓ | 🔄 |

### Success Criteria

**For Each Step:**
- [ ] Commands run without errors
- [ ] Output files are generated
- [ ] Generated files are valid (KiCad can open them)
- [ ] All expected components/nets are present

**For Complete Workflow:**
- [ ] Original components preserved
- [ ] Manual KiCad changes preserved  
- [ ] Python additions integrated
- [ ] Final project opens and works in KiCad
- [ ] No data loss at any step

## Commands Quick Reference

```bash
# Step 1: Import KiCad to Python ✅ WORKS
uv run kicad-to-python initial_kicad/ step1_imported_python/

# Step 2: Generate KiCad from Python  
cd step1_imported_python && uv run python main.py && mkdir -p ../step2_generated_kicad && mv initial_kicad_generated/ ../step2_generated_kicad/

# Step 4: Re-import modified KiCad
uv run kicad-to-python step3_manual_kicad_edits/modified_project/ step4_reimported_python/

# Step 6: Final sync
cd step5_python_additions && uv run python enhanced_circuit.py
```

## Troubleshooting

### Common Issues

**Import Failures:**
```bash
# Check if kicad-to-python command exists
uv run kicad-to-python --help

# Try alternative import methods
uv run python -m circuit_synth.tools.kicad_importer
```

**Generation Failures:**
```bash
# Check Python circuit syntax
uv run python -m py_compile imported_circuit.py

# Run with verbose logging
uv run python imported_circuit.py --verbose
```

**File Permission Issues:**
```bash
# Ensure directories are writable
chmod -R 755 bidirectional_update_test/
```

## Next Actions

1. **Run Step 1:** Start with KiCad → Python import
2. **Document Results:** Update this file with actual results
3. **Proceed Incrementally:** Only move to next step when current step passes
4. **Fix Issues:** If any step fails, debug before proceeding

## Status Tracking

- [x] Step 0: Initial KiCad project created
- [x] Step 1: KiCad → Python import ✅ SUCCESS
- [ ] Step 2: Python → KiCad generation  
- [ ] Step 3: Manual KiCad modifications
- [ ] Step 4: Re-import modified KiCad
- [ ] Step 5: Python circuit additions
- [ ] Step 6: Final bidirectional sync

**Current Status:** Ready for Step 2 - Python → KiCad generation

**Step 1 Results:**
- Import successfully parsed ESP32-C6-MINI-1 + capacitor
- Generated clean Python code with @circuit decorator
- All connections properly mapped (+3V3, GND)
- Ready to test round-trip generation