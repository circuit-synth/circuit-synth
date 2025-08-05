"""
Example: Test Plan Generation for Circuit Designs

This example demonstrates how to generate comprehensive test plans
for circuit-synth designs using the test-plan-creator agent.
"""

from circuit_synth import Component, Circuit, Net


@circuit(name="ESP32_USB_Power_Board")
def create_esp32_board():
    """
    ESP32 development board with USB-C power and 3.3V regulation.
    
    Features:
    - USB-C power input with protection
    - 3.3V LDO regulation for ESP32
    - USB-to-UART bridge for programming
    - User LED and button
    """
    # Power nets
    vbus = Net("VBUS")
    vcc_3v3 = Net("VCC_3V3")
    gnd = Net("GND")
    
    # USB-C Connector
    usb_c = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
    )
    usb_c["VBUS"] += vbus
    usb_c["GND"] += gnd
    
    # Protection components
    tvs_diode = Component(
        symbol="Device:D_TVS",
        ref="D",
        value="USBLC6-2SC6",
        footprint="Package_TO_SOT_SMD:SOT-23-6"
    )
    tvs_diode[1] += vbus
    tvs_diode[2] += gnd
    
    # 3.3V Voltage Regulator
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    regulator["VI"] += vbus
    regulator["VO"] += vcc_3v3
    regulator["GND"] += gnd
    
    # Input capacitor
    c_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c_in[1] += vbus
    c_in[2] += gnd
    
    # Output capacitor
    c_out = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c_out[1] += vcc_3v3
    c_out[2] += gnd
    
    # ESP32-C6 Module
    esp32 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    esp32["3V3"] += vcc_3v3
    esp32["GND"] += gnd
    
    # User LED
    led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    led_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    led[1] += vcc_3v3
    led[2] += led_resistor[1]
    led_resistor[2] += esp32["IO8"]
    
    # User Button
    button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    button[1] += esp32["IO9"]
    button[2] += gnd
    
    # Pull-up for button
    pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    pullup[1] += vcc_3v3
    pullup[2] += esp32["IO9"]


# Example of how the test-plan-creator agent would analyze this circuit
test_plan_prompt = """
Analyze the ESP32_USB_Power_Board circuit and generate a comprehensive test plan including:

1. Functional Testing:
   - Power-on sequence verification
   - USB-C power delivery validation
   - 3.3V regulator performance
   - ESP32 boot sequence
   - LED and button functionality

2. Performance Testing:
   - Input voltage range (USB spec compliance)
   - Output voltage regulation under load
   - Power consumption measurements
   - Thermal performance

3. Safety Testing:
   - TVS diode protection validation
   - Over-voltage protection
   - Short circuit protection
   - ESD testing on exposed connectors

4. Manufacturing Testing:
   - In-circuit test points
   - Programming interface validation
   - Visual inspection checklist

Please generate the test plan in markdown format with specific test procedures,
required equipment, and pass/fail criteria.
"""

# Example test plan structure that would be generated
example_test_plan = """
# Test Plan: ESP32_USB_Power_Board

## 1. Overview
**Circuit Description**: ESP32 development board with USB-C power input and 3.3V regulation
**Test Objectives**: Validate functionality, performance, safety, and manufacturability
**Required Equipment**:
- Digital Multimeter (6.5 digit precision)
- Oscilloscope (100MHz bandwidth minimum)
- USB-C Power Delivery Analyzer
- Electronic Load (0-2A, 0-5V)
- ESD Gun (IEC 61000-4-2 compliant)

## 2. Test Setup
### 2.1 Connection Diagram
- Connect USB-C power source to J1
- Attach oscilloscope probes to test points
- Connect electronic load to 3.3V output

### 2.2 Safety Precautions
- Ensure proper grounding
- Use current-limited power supply
- ESD protection for operator

## 3. Functional Tests

### 3.1 Power-On Sequence
**Procedure**:
1. Apply 5V via USB-C connector
2. Measure VBUS voltage at C1
3. Measure VCC_3V3 at C2
4. Verify ESP32 EN pin goes high

**Expected Results**:
- VBUS: 5.0V ± 5%
- VCC_3V3: 3.3V ± 2%
- Power-on time: < 100ms

**Pass Criteria**: All voltages within specification, stable power-up

### 3.2 Voltage Regulation
**Procedure**:
1. Vary input voltage 4.5V to 5.5V
2. Apply loads 0-500mA on 3.3V rail
3. Measure output voltage stability

**Expected Results**:
- Line regulation: < 1%
- Load regulation: < 2%
- Ripple: < 50mVpp

### 3.3 LED Control Test
**Procedure**:
1. Program ESP32 with test firmware
2. Toggle IO8 high/low
3. Verify LED operation

**Pass Criteria**: LED turns on/off with IO8 state

## 4. Performance Tests

### 4.1 Power Consumption
**Test Points**: VBUS current, 3.3V current
**Conditions**: 
- Idle mode
- Active mode (WiFi on)
- Deep sleep mode

**Expected Values**:
- Idle: < 50mA @ 3.3V
- Active: < 250mA @ 3.3V  
- Deep sleep: < 10µA @ 3.3V

### 4.2 Thermal Performance
**Procedure**:
1. Run at full load for 30 minutes
2. Measure regulator temperature
3. Check for thermal shutdown

**Pass Criteria**: Temperature < 85°C, no thermal shutdown

## 5. Safety Tests

### 5.1 ESD Protection
**Standard**: IEC 61000-4-2 Level 2
**Test Points**: USB-C connector, user button
**Procedure**: Apply ±4kV contact, ±8kV air discharge
**Pass Criteria**: Circuit continues normal operation

### 5.2 Over-Voltage Protection
**Procedure**:
1. Apply 6V to USB-C (exceeds spec)
2. Verify TVS diode clamps voltage
3. Check for component damage

**Pass Criteria**: No damage, TVS clamps at ~5.5V

## 6. Manufacturing Tests

### 6.1 ICT Test Points
- VBUS: Accessible at C1
- VCC_3V3: Accessible at C2
- GND: Multiple points available
- Programming: UART pins on ESP32

### 6.2 Programming Validation
**Procedure**:
1. Connect UART programmer
2. Flash test firmware
3. Verify successful programming

### 6.3 Visual Inspection
- [ ] All components placed correctly
- [ ] No solder bridges
- [ ] Correct component orientation
- [ ] Silkscreen legible

## 7. Test Results Recording

| Test | Result | Value | Notes |
|------|--------|-------|-------|
| VBUS Voltage | _____ | _____V | Target: 5.0V |
| 3.3V Output | _____ | _____V | Target: 3.3V |
| Idle Current | _____ | _____mA | Max: 50mA |
| ESD Test | _____ | Pass/Fail | Level 2 |

## 8. Troubleshooting Guide

**No 3.3V Output**:
- Check U1 regulator connections
- Verify VBUS present
- Check enable pin state

**High Current Draw**:
- Check for shorts on 3.3V rail
- Verify ESP32 not in reset loop
- Check LED current limiting resistor

**USB Not Recognized**:
- Verify D+/D- connections
- Check USB-C cable orientation
- Validate CC resistors
"""

if __name__ == "__main__":
    print("Test Plan Generation Example")
    print("=" * 50)
    print("\nThis example shows how the test-plan-creator agent would:")
    print("1. Analyze the circuit topology")
    print("2. Identify critical test points") 
    print("3. Generate comprehensive test procedures")
    print("4. Define pass/fail criteria")
    print("5. Recommend test equipment")
    print("\nTo use the agent with Claude Code:")
    print('Task(subagent_type="test-plan-creator", prompt=test_plan_prompt)')
    print("\nSee the example test plan structure above for expected output.")