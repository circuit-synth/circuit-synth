# Manual Test Steps for Test Case 14

## Initial Setup
1. Run the circuit.py script to generate the initial KiCad project
2. Open the generated project in KiCad
3. Notice the non-sequential reference designators

## KiCad Modifications

### Step 1: Annotate Schematic
1. Open the schematic editor
2. Go to Tools → Annotate Schematic
3. In the Annotate dialog:
   - Select "Use the entire schematic"
   - Choose "Sort symbols by X position"
   - Select "First free after sheet number X 100"
   - Check "Reset existing annotations"
   - Keep the numbering start at 1

### Step 2: Review Annotation Order
1. Click "Annotate" button
2. Review the proposed changes:
   - Resistors should become: R1, R2, R3, R4
   - Capacitors should become: C1, C2, C3
   - ICs should become: U1, U2
   - Diodes should become: D1, D2
   - Connectors should become: J1, J2

### Step 3: Apply Annotation
1. Click OK to apply the changes
2. Verify components are renumbered left-to-right, top-to-bottom

### Step 4: Manual Adjustments (Optional)
1. If needed, manually adjust specific references:
   - Right-click component → Properties
   - Change Reference field
   - Ensure no duplicates

### Step 5: Update PCB (if exists)
1. If PCB exists, update it:
   - Tools → Update PCB from Schematic
   - Check "Re-link footprints to schematic symbols based on their reference designators"

### Step 6: Save and Export
1. Save the schematic
2. Export using Circuit Synth tools

## Python Re-import
1. Run the import script to bring changes back to Python
2. Verify the generated Python code shows:
   - Sequential resistor numbering (R1, R2, R3, R4)
   - Sequential capacitor numbering (C1, C2, C3)
   - Sequential IC numbering (U1, U2)
   - Sequential diode numbering (D1, D2)
   - Sequential connector numbering (J1, J2)

## Validation Checklist
- [ ] All resistors renumbered sequentially
- [ ] All capacitors renumbered sequentially
- [ ] All ICs renumbered sequentially
- [ ] All diodes renumbered sequentially
- [ ] All connectors renumbered sequentially
- [ ] Geographic ordering maintained (left-to-right)
- [ ] No duplicate reference designators
- [ ] All connections preserved with new references
- [ ] Component values unchanged
- [ ] Component footprints unchanged

## Expected Mapping
Original → New:
- R7 → R1
- R2 → R2
- R15 → R3
- R1 → R4
- C3 → C1
- C8 → C2
- C1 → C3
- U5 → U1
- U2 → U2
- D3 → D1
- D1 → D2
- J4 → J1
- J1 → J2