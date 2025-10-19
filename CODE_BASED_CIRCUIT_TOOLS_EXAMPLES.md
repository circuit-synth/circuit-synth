# Code-Based Circuit Design Tools - Example Circuits Catalog

Comprehensive catalog of example circuits from code-based circuit design tools (tscircuit, atopile, JITX, SKiDL) for reference when building circuit-synth patterns library.

**Last Updated:** 2025-01-18

---

## 1. tscircuit (TypeScript/React)

**Website:** https://tscircuit.com
**GitHub:** https://github.com/tscircuit
**Registry:** https://registry.tscircuit.com
**Snippets:** https://snippets.tscircuit.com

### Example Circuits

| Circuit Name | Components | Pattern Type |
|-------------|------------|--------------|
| **USB Flashlight** | USB-C connector, LEDs, push buttons, resistors | USB + LED drivers |
| **3x5 LED Matrix** | 15 LEDs (daisy-chained), Raspberry Pi Pico | LED matrix control |
| **OR Gate Logic Circuit** | OR gate chip, USB power, resistors | USB-powered logic |
| **Blinking LED** | LED, battery, current limiting resistor | Basic LED driver |
| **Pull-up + Decoupling** | Chip breakout, pull-up resistors, decoupling caps | Signal conditioning + power filtering |
| **Basic RC Circuit** | Resistors, capacitors | Passive components |

### Available Components (Registry)

- **LEDs:** `@tsci/seveibar.red-led`
- **Buttons:** `@tsci/seveibar.push-button`
- **USB-C:** `@tsci/seveibar.smd-usb-c`
- **Logic Gates:** `@tsci/Abse2001.OR-Gate-Chip`
- **Passives:** Resistors, capacitors, inductors

### Common Patterns

✅ LED drivers with current limiting
✅ Pull-up/pull-down resistors
✅ Decoupling capacitors
✅ USB connections (USB-C)
✅ Logic gates
✅ LED matrices (multiplexed control)

---

## 2. atopile (Python-like .ato language)

**Website:** https://atopile.io
**GitHub:** https://github.com/atopile
**Packages:** https://packages.atopile.io

### Example Projects

| Project Name | Components | Pattern Type |
|-------------|------------|--------------|
| **NONOS Smart Speaker** | CM5 module, TAS5825MRHBR amplifier, ADAU145x DSP, STUSB4500 PD controller | Audio system + USB-C PD |
| **AI-Pin** | (Humane Pin clone) | Wearable device |
| **Hyperion** | 300K nit display for raves | High-brightness display |
| **SPIN** | BLDC servo motors | Motor control |

### Generics Library (github.com/atopile/generics)

**Passive Components:**
- Resistors (auto-selected from JLCPCB)
- Capacitors (auto-selected from JLCPCB)
- Inductors (experimental)
- Diodes (experimental)
- FETs (experimental)

**Active Components:**
- LV2842Kit voltage regulator (LDO)
- USB connectors (`usb-connectors/usb-connectors.ato`)
- LEDs (`LEDIndicatorRed` from `generics/leds.ato`)

**Interfaces:**
- Power interface (`generics/interfaces.ato`)
- Pair interface (differential signals)
- USB2 interface (dp, dm, gnd)

### Common Patterns

✅ Voltage regulators (LDO)
✅ USB-C connectors
✅ LED indicators
✅ Power supply filtering
✅ Parametric component selection (auto-finds resistors/caps based on specs)

---

## 3. JITX (Lisp-based language)

**Website:** https://www.jitx.com
**GitHub:** https://github.com/JITx-Inc
**Cookbook:** https://github.com/JITx-Inc/jitx-cookbook
**Docs:** https://docs.jitx.com

### JITX Cookbook Examples

| Circuit Name | Components | Pattern Type |
|-------------|------------|--------------|
| **LiPo Battery Charger** | LiPo battery charger IC, JST battery connector, USB-C, LDO regulator | USB-C to battery charging |
| **USB-C Cable Tester** | USB-C connectors, LEDs, test points, microcontroller | USB testing/debugging |
| **Apollo 4 Blue System** | Ambiq Apollo 4 Blue MCU, wireless charging, MIPI-DSI, octal SPI, 6-axis IMU | Advanced MCU system |
| **Coin Cell Power** | Coin cell battery, voltage regulation | Low-power battery system |

### JITX Standard Library (JSL)

**Power Systems:**
- DC/DC power regulation solvers
- LDO voltage regulators
- Buck regulators (inferred from power system architecture)
- Boost regulators (inferred from power system architecture)

**Connectors:**
- USB-C connectors (mapped to standard interfaces)
- JST battery connectors
- Terminal blocks

**Components:**
- Landpattern generators
- Symbol generators
- Parametric component selection

### Common Patterns

✅ LiPo battery charging systems
✅ LDO voltage regulators
✅ USB-C power delivery
✅ Microcontroller systems with peripherals
✅ Wireless charging
✅ Display interfaces (MIPI-DSI)
✅ IMU sensor integration
✅ Test point placement

---

## 4. SKiDL (Python)

**Website:** https://devbisme.github.io/skidl/
**GitHub:** https://github.com/devbisme/skidl
**PyPI:** https://pypi.org/project/skidl/

### Example Circuits

| Circuit Name | Components | Pattern Type |
|-------------|------------|--------------|
| **LED Matrix** | LED array with template-based instantiation | LED matrix control |
| **ESP32 Board** | ESP32, 5V to 3V regulator, voltage divider | MCU with power regulation |
| **Voltage Divider** | Resistors | Basic analog circuit |

### Features

- **Templates:** Parametric component templates for arrays
- **ERC:** Electrical rules checking (unconnected pins, drive conflicts)
- **SPICE Integration:** Run simulations directly on SKiDL circuits
- **Version Control:** Git-friendly text-based design

### Common Patterns

✅ LED matrices (template-based)
✅ Voltage dividers
✅ Voltage regulators (5V to 3.3V)
✅ Parametric circuit generation

---

## Pattern Comparison Matrix

| Pattern Type | tscircuit | atopile | JITX | SKiDL | circuit-synth |
|-------------|-----------|---------|------|-------|--------------|
| **LED with current limiting** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Voltage divider** | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Pull-up/pull-down resistors** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Decoupling capacitors** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **LDO voltage regulator** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Buck converter** | ❌ | ❌ | ✅* | ❌ | ❌ |
| **Boost converter** | ❌ | ❌ | ✅* | ❌ | ❌ |
| **USB-C connector** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Battery charging** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Crystal oscillator** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Motor driver (H-bridge)** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **LED matrix** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Logic gates** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **I2C pull-ups** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **SPI bus** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **IMU sensor integration** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Wireless charging** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Display interfaces (MIPI-DSI)** | ❌ | ❌ | ✅ | ❌ | ❌ |

\* Inferred from JSL power system architecture

---

## Circuit-Synth Gap Analysis

### ✅ What We Have

1. **Power supply** (AMS1117-3.3 LDO with decoupling caps)
2. **USB-C** (with CC resistors + ESD protection)
3. **LED blinker** (LED with current limiting resistor)
4. **Debug header** (connector pattern)
5. **ESP32-C6 integration** (MCU example)

### ❌ Missing Common Patterns

**High Priority (widely used):**
1. **Voltage divider** - ADC input scaling, feedback networks
2. **Pull-up/pull-down resistor networks** - I2C, digital inputs
3. **Decoupling capacitor networks** - Power supply filtering
4. **Crystal oscillator** - MCU clock source (HSE/LSE)
5. **I2C pull-ups** - Standard 2-wire interface
6. **SPI bus pattern** - Multi-wire communication

**Medium Priority (useful):**
7. **Buck converter** - Efficient step-down regulation
8. **Boost converter** - Step-up regulation
9. **Battery charging circuit** - LiPo/Li-ion charging
10. **H-bridge motor driver** - Bidirectional motor control
11. **LED matrix** - Multiplexed LED arrays
12. **Logic level shifter** - Voltage translation

**Low Priority (specialized):**
13. **MIPI-DSI interface** - Display connections
14. **Wireless charging** - Qi charging circuits
15. **IMU sensor connections** - Accelerometer/gyro integration

---

## Recommendations for circuit-synth

### Phase 1: Fill Common Gaps (Immediate)

Create circuit pattern files for the most commonly used patterns:

```python
# 1. voltage_divider.py - ADC scaling, feedback networks
# 2. pull_up_resistor.py - I2C, digital inputs
# 3. pull_down_resistor.py - Button inputs, digital signals
# 4. decoupling_caps.py - Power supply filtering
# 5. crystal_oscillator.py - STM32/MCU clock source
# 6. i2c_pull_ups.py - Standard I2C bus configuration
```

### Phase 2: Power Management (Next)

```python
# 7. buck_converter.py - Efficient step-down regulation
# 8. boost_converter.py - Step-up regulation
# 9. battery_charger.py - LiPo charging circuit
```

### Phase 3: Advanced Patterns (Future)

```python
# 10. motor_driver.py - H-bridge for DC motors
# 11. led_matrix.py - Multiplexed LED array
# 12. logic_level_shifter.py - 3.3V ↔ 5V translation
```

---

## Notes

- **tscircuit** focuses on web-first circuit design with React modularity
- **atopile** emphasizes parametric design with automatic component selection from JLCPCB
- **JITX** targets professional use with advanced power system solvers and AI-assisted routing
- **SKiDL** provides Python-based schematic capture with SPICE integration

All tools support version control, parametric design, and KiCad integration to varying degrees.

---

**Generated:** 2025-01-18
**Purpose:** Reference for circuit-synth circuit-patterns skill development
