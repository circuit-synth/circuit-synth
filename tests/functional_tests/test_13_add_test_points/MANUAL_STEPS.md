# Manual Test Steps for Test Case 13

## Initial Setup
1. Run the circuit.py script to generate the initial KiCad project
2. Open the generated project in KiCad
3. Notice the circuit lacks test points and debug connectors

## KiCad Modifications

### Step 1: Add Signal Test Points
1. Open the schematic editor
2. Add test points (search for "TestPoint"):
   - TP1 on SENSOR_RAW net
     - Reference: TP1
     - Value: SENSOR_RAW
     - Footprint: TestPoint:TestPoint_Pad_D1.5mm
   - TP2 on SENSOR_FILTERED net
     - Reference: TP2
     - Value: SENSOR_FILT
     - Footprint: TestPoint:TestPoint_Pad_D1.5mm
   - TP3 on ADC_INPUT net
     - Reference: TP3
     - Value: ADC_IN
     - Footprint: TestPoint:TestPoint_Pad_D1.5mm

### Step 2: Add Power Test Points
1. Add power rail test points:
   - TP4 on 5V net
     - Reference: TP4
     - Value: 5V
     - Footprint: TestPoint:TestPoint_Pad_D2.0mm
   - TP5 on 3V3 net
     - Reference: TP5
     - Value: 3V3
     - Footprint: TestPoint:TestPoint_Pad_D2.0mm

### Step 3: Add Ground Test Points
1. Add ground test points near sensitive areas:
   - TP6 near op-amp (GND)
     - Reference: TP6
     - Value: GND_ANA
     - Footprint: TestPoint:TestPoint_Pad_D1.5mm
   - TP7 near digital section (GND)
     - Reference: TP7
     - Value: GND_DIG
     - Footprint: TestPoint:TestPoint_Pad_D1.5mm

### Step 4: Add Debug UART Connector
1. Add a 3-pin connector for UART debug:
   - Component: Conn_01x03_Pin
   - Reference: J3
   - Value: DEBUG_UART
   - Footprint: Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical
   - Note: Leave TX/RX pins unconnected (for future MCU connection)
   - Connect pin 3 to GND

### Step 5: Add I2C Debug Header
1. Add a 4-pin connector for I2C debugging:
   - Component: Conn_01x04_Pin
   - Reference: J4
   - Value: I2C_DEBUG
   - Footprint: Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical
   - Connect:
     - Pin 1 to 3V3
     - Pin 2 to GND
     - Pin 3 to I2C_SDA
     - Pin 4 to I2C_SCL

### Step 6: Add Current Measurement Points
1. Add test points for current measurement:
   - Break the 5V connection to U1
   - Add two test points:
     - TP8: 5V_IN (before break)
     - TP9: 5V_REG (after break)
   - Add 0Ω resistor R4 between them (or jumper)

### Step 7: Save and Export
1. Save the schematic
2. Verify all test points are connected
3. Export using Circuit Synth tools

## Python Re-import
1. Run the import script to bring changes back to Python
2. Verify the generated Python code includes:
   - All test points (TP1-TP9)
   - Debug UART connector (J3)
   - I2C debug header (J4)
   - Current measurement setup

## Validation Checklist
- [ ] Signal test points added (TP1-TP3)
- [ ] Power test points added (TP4-TP5)
- [ ] Ground test points added (TP6-TP7)
- [ ] Debug UART connector added
- [ ] I2C debug header added
- [ ] Current measurement points added
- [ ] All test points have appropriate footprints
- [ ] Original circuit functionality preserved