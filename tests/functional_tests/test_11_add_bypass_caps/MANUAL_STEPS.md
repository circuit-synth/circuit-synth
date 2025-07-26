# Manual Test Steps for Test Case 11

## Initial Setup
1. Run the circuit.py script to generate the initial KiCad project
2. Open the generated project in KiCad
3. Notice the MCU circuit lacks proper bypass capacitors

## KiCad Modifications

### Step 1: Add VDD Bypass Capacitor
1. Open the schematic editor
2. Add a capacitor (press 'A', search for "C")
3. Place it near U1 pin 1 (VDD)
4. Set properties:
   - Reference: C3
   - Value: 100nF
   - Footprint: Capacitor_SMD:C_0603_1608Metric
5. Connect:
   - Pin 1 to 3V3 net
   - Pin 2 to GND net

### Step 2: Add VDDA Bypass Capacitor
1. Add another capacitor near U1 pin 5 (VDDA)
2. Set properties:
   - Reference: C4
   - Value: 100nF
   - Footprint: Capacitor_SMD:C_0603_1608Metric
3. Connect:
   - Pin 1 to 3V3 net
   - Pin 2 to GND net

### Step 3: Add Bulk Capacitor
1. Add a larger capacitor for bulk storage
2. Set properties:
   - Reference: C5
   - Value: 10uF
   - Footprint: Capacitor_SMD:C_0805_2012Metric
3. Connect:
   - Pin 1 to 3V3 net
   - Pin 2 to GND net

### Step 4: Add Crystal Bypass
1. Add capacitor near crystal circuit
2. Set properties:
   - Reference: C6
   - Value: 100nF
   - Footprint: Capacitor_SMD:C_0603_1608Metric
3. Connect between 3V3 and GND

### Step 5: Add Power Symbols
1. Add power symbols for clarity:
   - Add 3V3 power symbols
   - Add GND symbols
2. Place them near the bypass capacitors

### Step 6: Save and Export
1. Save the schematic
2. Run ERC to verify connections
3. Export using Circuit Synth tools

## Python Re-import
1. Run the import script to bring changes back to Python
2. Verify the generated Python code includes:
   - C3: 100nF bypass for VDD
   - C4: 100nF bypass for VDDA
   - C5: 10uF bulk capacitor
   - C6: 100nF near crystal
   - All proper connections to power nets

## Validation Checklist
- [ ] All bypass capacitors added with correct values
- [ ] Capacitors placed close to IC power pins
- [ ] Proper connections to 3V3 and GND
- [ ] Reference designators assigned sequentially
- [ ] Original circuit functionality preserved
- [ ] Power symbols added for clarity