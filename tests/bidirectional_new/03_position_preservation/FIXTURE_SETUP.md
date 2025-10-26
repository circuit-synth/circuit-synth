# Creating the 03_position_preservation KiCad Fixture

## Step-by-Step Instructions

You need to create a KiCad project with a single resistor positioned at a specific location.

### 1. Create the Project

1. Open KiCad
2. Select File → New Project
3. Name it: `03_kicad_ref`
4. Save in: `/Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/03_position_preservation/03_kicad_ref/`

### 2. Add the Resistor Symbol

1. Click "Schematic editor" or double-click the .kicad_sch file
2. Click "Add Symbol" (or press A)
3. Search for "Device:R" (basic resistor)
4. Click on it and place on the schematic
5. Right-click the resistor → Properties or press E
6. Set Reference to: `R1`
7. Set Value to: `10k`
8. Click OK
9. Save the schematic (Ctrl+S)

### 3. Position the Resistor (IMPORTANT)

1. Click on R1 to select it
2. Right-click and select "Properties" or press E
3. Note the current position (X, Y)
4. Try to set position to approximately:
   - X: 30.48 mm (or similar - any reasonable position)
   - Y: 35.56 mm
5. If you can't directly edit position in properties, manually drag the component
   - Click and drag R1 to a clear position on the schematic
   - Position doesn't need to be exact - tests will extract whatever position you set
6. Save schematic again

### 4. Copy Project Files

After saving in KiCad, you should have created:
- `03_kicad_ref.kicad_pro`
- `03_kicad_ref.kicad_sch`
- `03_kicad_ref.kicad_prl`
- `03_kicad_ref-backups/` (directory)

All these should be in:
`/Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/03_position_preservation/03_kicad_ref/`

They should already be there if you created the project in that location.

### 5. Verify

Run this command to verify the fixture is set up:
```bash
ls -la /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional_new/03_position_preservation/03_kicad_ref/
```

You should see:
- ✓ 03_kicad_ref.kicad_pro
- ✓ 03_kicad_ref.kicad_sch
- ✓ 03_kicad_ref.kicad_prl
- ✓ 03_kicad_ref-backups/ (directory)

## What the Tests Do

Once the fixture is in place:
- **test_01**: Extracts the position (X, Y, rotation) from your schematic
- **test_02**: Verifies position survives a round-trip cycle
- **tests_03-06**: Will be implemented later to test advanced position scenarios

The tests don't care about the exact coordinates - they'll work with whatever position you set in KiCad. The important thing is that the position is extracted and preserved.

## Troubleshooting

If you see "Reference KiCad schematic not found" error:
- Make sure the 03_kicad_ref.kicad_sch file exists in the right directory
- Check the path: `/tests/bidirectional_new/03_position_preservation/03_kicad_ref/`

If position extraction fails:
- Make sure the resistor is named R1 (not R or R_1)
- Make sure it's using Device:R symbol (not a different resistor)
- Check that schematic is saved with the component
