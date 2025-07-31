# USB-C Interface Design Guide

## USB-C Connector Basics

### Pin Configuration (USB 2.0 Mode)
```
A1/B1: GND     - Ground reference (both sides for reversibility)
A4/B4: VBUS    - Power delivery (5V default, up to 20V with PD)
A5:    CC1     - Configuration Channel 1 (determines orientation)
A6/B6: D+      - USB Data Plus differential pair
A7/B7: D-      - USB Data Minus differential pair
A8/B8: SBU1/2  - Sideband Use (alternate modes)
```

### Power Delivery Classes
- **USB 2.0**: 5V @ 0.5A (2.5W) - basic USB power
- **USB BC 1.2**: 5V @ 1.5A (7.5W) - battery charging
- **USB-C Default**: 5V @ 3A (15W) - higher current capability
- **USB PD**: 5V-20V @ 3-5A (15W-100W) - requires PD controller

## Configuration Channel (CC) Design

### CC Resistor Values (Device/Sink Side)
- **No Connection**: Floating - not connected
- **Default USB**: 5.1kΩ to GND - USB 2.0/3.0 device
- **1.5A Capability**: 1.5kΩ to GND - can sink 1.5A at 5V
- **3A Capability**: 1kΩ to GND - can sink 3A at 5V

### CC Resistor Implementation
```python
# Standard USB 2.0 device (most common)
r_cc = Component("Device:R", ref="R1", value="5.1K", footprint="0603")
r_cc[1] += usb_connector["A5"]  # CC1 pin
r_cc[2] += gnd                  # Pulldown to ground
```

## ESD Protection Strategy

### VBUS Protection
- **Purpose**: Protect against power surges and ESD events
- **Component**: TVS diode or ESD protection diode
- **Voltage**: 5V clamping voltage (ESD5Z5.0T1G)
- **Placement**: Close to connector, between VBUS and GND

### Data Line Protection  
- **Purpose**: Protect USB data lines from ESD damage
- **Component**: Low-capacitance ESD diodes
- **Specification**: < 1pF capacitance to avoid signal degradation
- **Placement**: After series resistors, close to protected circuitry

```python
# VBUS ESD protection
esd_vbus = Component("Diode:ESD5Z5.0T1G", ref="D1", footprint="SOD-523")
esd_vbus[1] += vbus_5v  # Cathode to VBUS
esd_vbus[2] += gnd      # Anode to ground

# Data line ESD protection
esd_dp = Component("Diode:ESD5Zxx", ref="D2", footprint="SOD-523")
esd_dp[1] += usb_dp     # Protect data line
esd_dp[2] += gnd        # Clamp to ground
```

## Signal Integrity Considerations

### Series Termination Resistors
- **Value**: 22Ω typical for USB 2.0 data lines
- **Purpose**: Improve signal integrity, reduce reflections
- **Placement**: Close to connector, before ESD protection
- **Tolerance**: 1% precision resistors recommended

### Differential Pair Routing
- **Impedance**: 90Ω ±10% differential impedance
- **Trace Width**: Calculated based on PCB stackup
- **Spacing**: Maintain consistent spacing between D+ and D-
- **Length Matching**: ±0.1mm between D+ and D- traces

### PCB Layout Guidelines
```
USB Connector → [22Ω Series R] → [ESD Protection] → MCU/System
      |                              |
    [GND]                          [GND]
```

## Power Supply Design

### Decoupling Strategy
- **Bulk Capacitance**: 10µF-47µF ceramic capacitor near connector
- **High Frequency**: 100nF ceramic capacitor for switching noise
- **Placement**: As close as possible to VBUS pin

### Current Handling
- **Trace Width**: Minimum 0.5mm for 1.5A, 1mm for 3A
- **Via Count**: Multiple vias for current distribution
- **Thermal Management**: Consider copper pour for heat dissipation

## Connector Selection

### Mechanical Considerations
- **Through-Hole**: Better mechanical strength, harder to manufacture
- **SMD Horizontal**: Good compromise, easier assembly
- **SMD Vertical**: Space-efficient but less mechanical strength

### Recommended Parts
```python
# Horizontal mount (most common)
usb_c = Component(
    "Connector:USB_C_Receptacle_USB2.0", 
    ref="J1",
    footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
)

# Vertical mount (space constrained)
usb_c = Component(
    "Connector:USB_C_Receptacle_USB2.0",
    ref="J1", 
    footprint="Connector_USB:USB_C_Receptacle_Palconn_UTC16-G"
)
```

## Common Design Mistakes

### CC Resistor Issues
- ❌ Wrong resistor value (host won't recognize device)
- ❌ Missing CC resistor (device won't enumerate)
- ❌ CC resistor on both CC1 and CC2 (violates USB-C spec)

### ESD Protection Problems
- ❌ No ESD protection (device vulnerable to damage)
- ❌ High capacitance ESD devices (degrades signal quality)
- ❌ ESD devices before series resistors (reduces effectiveness)

### Layout Issues
- ❌ Long traces between connector and protection
- ❌ Poor differential pair routing on data lines
- ❌ Inadequate current handling for power traces
- ❌ No ground plane under connector

## Testing and Validation

### Electrical Tests
- **CC Resistance**: Measure 5.1kΩ ±5% from CC1 to GND
- **VBUS Voltage**: 5V ±5% under rated load current
- **Data Line Impedance**: 90Ω ±10% differential
- **ESD Survival**: IEC 61000-4-2 (±8kV contact, ±15kV air)

### Mechanical Tests
- **Insertion Force**: < 35N typical
- **Retention Force**: > 10N minimum
- **Durability**: 10,000 insertion cycles minimum

### USB Compliance
- **USB-IF Certification**: Required for commercial products
- **Signal Quality**: Eye diagram analysis at 480Mbps
- **Power Delivery**: Compliance with USB PD specification