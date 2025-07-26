# Manual Test Steps for Test Case 12

## Initial Setup
1. Run the circuit.py script to generate the initial KiCad project
2. Open the generated project in KiCad
3. Notice all components use very small footprints

## KiCad Modifications

### Step 1: Change Resistor Footprints
1. Open the schematic editor
2. For each resistor (R1, R2, R3):
   - Right-click → Properties
   - Change footprint from "Resistor_SMD:R_0402_1005Metric" 
     to "Resistor_SMD:R_0603_1608Metric"
   - Click OK

### Step 2: Change Capacitor Footprints
1. For capacitors C1 and C2:
   - Right-click → Properties
   - Change footprint from "Capacitor_SMD:C_0402_1005Metric"
     to "Capacitor_SMD:C_0805_2012Metric"
   - Add field "Voltage" with value "25V" for C1
   - Add field "Voltage" with value "16V" for C2

### Step 3: Convert THT LED to SMD
1. For LED D1:
   - Right-click → Properties
   - Change footprint from "LED_THT:LED_D3.0mm"
     to "LED_SMD:LED_0603_1608Metric"
   - Update orientation if needed

### Step 4: Convert THT Connector to SMD
1. For connector J1:
   - Right-click → Properties
   - Change footprint from "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
     to "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Horizontal_SMD"

### Step 5: Change IC Package
1. For U1 (LM358):
   - Right-click → Properties
   - Change footprint from "Package_SO:MSOP-8_3x3mm_P0.65mm"
     to "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
   - This provides wider pin pitch for easier soldering

### Step 6: Verify and Save
1. Review all footprint changes
2. Save the schematic
3. Optionally update PCB to verify footprints
4. Export using Circuit Synth tools

## Python Re-import
1. Run the import script to bring changes back to Python
2. Verify the generated Python code shows:
   - All resistors with 0603 footprints
   - All capacitors with 0805 footprints
   - LED with SMD footprint
   - Connector with SMD footprint
   - Op-amp with SOIC-8 footprint

## Validation Checklist
- [ ] All 0402 resistors changed to 0603
- [ ] All 0402 capacitors changed to 0805
- [ ] THT LED changed to SMD LED
- [ ] THT connector changed to SMD variant
- [ ] MSOP-8 changed to SOIC-8
- [ ] Component values unchanged
- [ ] All connections preserved
- [ ] Voltage ratings added to capacitors