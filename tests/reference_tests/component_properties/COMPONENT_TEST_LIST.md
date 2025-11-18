# Component Property Text Positioning - Test List

## Status Legend
- ✅ TESTED - Text positioning verified
- 🔄 IN PROGRESS - Currently testing
- ⏳ PENDING - Not yet tested

## Test Progress: 3/26 components tested

---

## Category 1: Basic Passives (3/7 tested)

| Symbol | Status | Notes |
|--------|--------|-------|
| Device:R | ✅ TESTED | Properties to right, footprint to left |
| Device:C | ✅ TESTED | Properties to right (wider), footprint below |
| Device:LED | ✅ TESTED | Properties above component |
| Device:R_Small | ⏳ PENDING | Smaller resistor variant |
| Device:C_Small | ⏳ PENDING | Smaller capacitor variant |
| Device:C_Polarized_Small | ⏳ PENDING | Polarized capacitor |
| Device:L | ⏳ PENDING | Inductor |

---

## Category 2: Diodes & Protection (0/4 tested)

| Symbol | Status | Notes |
|--------|--------|-------|
| Device:D_TVS | ⏳ PENDING | TVS protection diode |
| Device:D_TVS_Dual_AAC | ⏳ PENDING | Dual TVS diode |
| Device:D_Zener | ⏳ PENDING | Zener diode |
| Diode:ESD9B3.3ST5G | ⏳ PENDING | ESD protection diode |

---

## Category 3: ICs & Microprocessors (0/6 tested) ⭐ HIGH PRIORITY

| Symbol | Status | Notes |
|--------|--------|-------|
| RF_Module:ESP32-WROOM-32 | ⏳ PENDING | **Microprocessor - 38 pins** |
| Regulator_Linear:AMS1117-3.3 | ⏳ PENDING | **LDO voltage regulator - SOT-223** |
| Regulator_Switching:TPS54202DDC | ⏳ PENDING | **Buck converter - SOT-23-6** |
| Interface_UART:MAX3485 | ⏳ PENDING | **RS-485 transceiver - SOIC-8** |
| 74xx:74LS245 | ⏳ PENDING | **Level shifter - SOIC-20** |
| Reference_Voltage:REF3030 | ⏳ PENDING | **Voltage reference** |

---

## Category 4: Connectors (0/5 tested)

| Symbol | Status | Notes |
|--------|--------|-------|
| Connector:USB_C_Receptacle | ⏳ PENDING | USB-C connector |
| Connector:Barrel_Jack | ⏳ PENDING | DC barrel jack |
| Connector:Screw_Terminal_01x02 | ⏳ PENDING | 2-pole terminal |
| Connector:Screw_Terminal_01x03 | ⏳ PENDING | 3-pole terminal |
| Connector:TestPoint | ⏳ PENDING | Test point |

---

## Category 5: Switches & Transistors (0/3 tested)

| Symbol | Status | Notes |
|--------|--------|-------|
| Switch:SW_Push | ⏳ PENDING | Tactile switch |
| Switch:SW_DIP_x04 | ⏳ PENDING | 4-way DIP switch |
| Transistor_FET:AO3401A | ⏳ PENDING | P-channel MOSFET |

---

## Testing Priority

### Round 1: Critical ICs (Most Complex) ⭐
1. **RF_Module:ESP32-WROOM-32** - Large module, many pins
2. **74xx:74LS245** - Wide IC, 20 pins
3. **Interface_UART:MAX3485** - SOIC-8
4. **Regulator_Linear:AMS1117-3.3** - SOT-223
5. **Regulator_Switching:TPS54202DDC** - SOT-23-6
6. **Transistor_FET:AO3401A** - SOT-23

### Round 2: Connectors
7. **Connector:USB_C_Receptacle** - Complex connector
8. **Connector:Barrel_Jack** - Standard connector
9. **Connector:Screw_Terminal_01x02** - Terminal block

### Round 3: Protection & Small Parts
10. Device:D_TVS
11. Device:L
12. Switch:SW_Push

### Round 4: Variants (if needed)
13. Device:R_Small, Device:C_Small, etc.

---

## Current Focus

**NEXT TO TEST:** `RF_Module:ESP32-WROOM-32` (ESP32 microprocessor)

---

## Test File Locations

Each component gets its own directory:
```
tests/reference_tests/component_properties/
├── Device_R/                    ✅ Done
├── Device_C/                    ✅ Done
├── Device_LED/                  ✅ Done
├── RF_Module_ESP32-WROOM-32/    ⏳ Next
├── 74xx_74LS245/
├── Interface_UART_MAX3485/
└── ...
```
