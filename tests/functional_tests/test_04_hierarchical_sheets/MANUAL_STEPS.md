# Manual Test Steps for Hierarchical Sheets

## Test 4.1: Python to KiCad Hierarchy

### Step 1: Generate Hierarchical Circuit
```bash
cd tests/functional_tests/test_04_hierarchical_sheets
python circuit.py
```

### Step 2: Verify in KiCad
1. Open `test_04_hierarchical/test_04_hierarchical.kicad_pro` in KiCad
2. Open the schematic editor
3. Verify you see:
   - Main sheet with C1, J1, and a hierarchical sheet symbol
   - Double-click the sheet symbol to enter the voltage divider sub-sheet
   - Verify R1 and R2 are present in the sub-sheet

## Test 4.2: KiCad to Python Hierarchy

### Step 1: Generate Flat Circuit
```bash
python flat_circuit.py
```

### Step 2: Add Hierarchical Sheet in KiCad
1. Open `test_04_flat/test_04_flat.kicad_pro` in KiCad
2. Open the schematic editor
3. You should see C1, D1, and R1 in a flat arrangement

**Create Hierarchical Sheet:**
1. Place → Hierarchical Sheet (or press 'S')
2. Draw a rectangle for the sheet
3. Fill in the dialog:
   - Sheet name: `sensor_circuit`
   - Sheet file name: `sensor_circuit.kicad_sch`
4. Click OK

**Add Components to Sub-sheet:**
1. Double-click the sheet symbol to enter it
2. Add components:
   - U1: Device:R_Photo (photoresistor)
   - R2: Device:R (10k pull-down)
3. Add hierarchical labels:
   - Place → Hierarchical Label (or press 'H')
   - Add "VCC" (Input)
   - Add "SENSOR_OUT" (Output)
   - Add "GND" (Passive)
4. Connect:
   - U1 pin 1 to VCC
   - U1 pin 2 to SENSOR_OUT and R2 pin 1
   - R2 pin 2 to GND
5. Save and go back to main sheet (Alt+Backspace)

**Connect Sheet Pins:**
1. Right-click the sheet symbol → Import Sheet Pins
2. Connect the sheet pins:
   - VCC pin to VCC net
   - GND pin to GND net
   - SENSOR_OUT to a new net (can leave unconnected for test)

### Step 3: Import to Python
```bash
python -m circuit_synth.scripts.sync_from_kicad \
    --kicad-project test_04_flat/ \
    --circuit-synth . \
    --output hierarchical_from_kicad.py
```

### Step 4: Verify Import
1. Open `hierarchical_from_kicad.py`
2. Verify:
   - Main circuit components are present
   - Hierarchical sheet is represented
   - Sub-sheet components are included

## Test 4.3: Modify Hierarchical Connections

### In KiCad:
1. Add or remove hierarchical pins
2. Change inter-sheet connections
3. Re-import and verify changes

### In Python:
1. Modify sheet connections in code
2. Re-export and verify in KiCad

## Expected Results
- ✓ Python hierarchical structures appear correctly in KiCad
- ✓ KiCad hierarchical sheets import with proper structure
- ✓ Sheet instances and references are preserved
- ✓ Inter-sheet connections sync properly

## Notes
- Sheet file names must be unique within a project
- Hierarchical pins define the interface between sheets
- Pin directions (Input/Output/Bidirectional/Passive) should match usage