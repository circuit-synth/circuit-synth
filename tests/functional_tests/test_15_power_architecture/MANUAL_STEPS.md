# Manual Test Steps for Test Case 15

## Initial Setup
1. Run the circuit.py script to generate the initial KiCad project
2. Open the generated project in KiCad
3. Notice the linear regulator topology (L7805)

## KiCad Modifications

### Step 1: Remove Linear Regulator Components
1. Open the schematic editor
2. Delete the following components:
   - U1 (L7805)
   - C1 (330nF input cap)
   - C2 (100nF output cap)
3. Keep the protection diode D1

### Step 2: Add Switching Regulator IC
1. Add new component (press 'A'):
   - Search for "LM2596" or similar buck converter
   - Reference: U1
   - Value: LM2596S-5.0
   - Footprint: Package_TO_SOT_SMD:TO-263-5_TabPin3
2. Place near the original regulator location

### Step 3: Add Switching Components
1. Add inductor:
   - Component: Device:L
   - Reference: L1
   - Value: 33uH
   - Footprint: Inductor_SMD:L_12x12mm_H8mm
2. Add Schottky diode:
   - Component: Diode:1N5822
   - Reference: D3
   - Value: 1N5822
   - Footprint: Diode_SMD:D_SMA
3. Add input capacitor:
   - Component: Device:CP
   - Reference: C1
   - Value: 680uF
   - Footprint: Capacitor_SMD:CP_Elec_10x10.5
4. Add output capacitor:
   - Component: Device:CP
   - Reference: C2
   - Value: 220uF
   - Footprint: Capacitor_SMD:CP_Elec_8x10.5

### Step 4: Add Feedback Network
1. Add feedback resistors:
   - R2: 3.3k (top of divider)
   - R3: 1k (bottom of divider)
   - Both 0603 SMD footprint
2. Add feedforward capacitor:
   - C3: 10nF (across R2)
   - 0603 SMD footprint

### Step 5: Wire the Switching Regulator
1. Connect U1 (LM2596):
   - Pin 1 (VIN) to VIN_PROTECTED
   - Pin 2 (OUTPUT) to inductor L1 pin 1
   - Pin 3 (GND) to GND
   - Pin 4 (FEEDBACK) to junction of R2/R3
   - Pin 5 (ON/OFF) to VIN_PROTECTED (always on)
2. Connect inductor:
   - L1 pin 2 to 5V output net
3. Connect Schottky diode:
   - D3 cathode to L1 pin 1 (switch node)
   - D3 anode to GND
4. Connect feedback network:
   - R2 from 5V to FEEDBACK
   - R3 from FEEDBACK to GND
   - C3 across R2
5. Connect capacitors:
   - C1 from VIN_PROTECTED to GND
   - C2 from 5V to GND

### Step 6: Update Component Properties
1. Add properties to new components:
   - L1: Current rating = "3A"
   - D3: Voltage = "40V", Current = "3A"
   - C1: Voltage = "25V", ESR = "Low"
   - C2: Voltage = "10V", ESR = "Low"

### Step 7: Save and Export
1. Save the schematic
2. Run ERC to verify connections
3. Export using Circuit Synth tools

## Python Re-import
1. Run the import script to bring changes back to Python
2. Verify the generated Python code shows:
   - Linear regulator U1 (L7805) removed
   - Switching regulator U1 (LM2596) added
   - Inductor L1 added
   - Schottky diode D3 added
   - New capacitor values (680uF, 220uF)
   - Feedback resistors R2, R3 added
   - All connections properly established

## Validation Checklist
- [ ] Linear regulator components removed
- [ ] Switching regulator IC added
- [ ] Inductor added with correct value
- [ ] Schottky diode added
- [ ] Input/output capacitors updated
- [ ] Feedback network implemented
- [ ] All power connections maintained
- [ ] Output still provides 5V
- [ ] Test points still connected
- [ ] LED circuit unchanged