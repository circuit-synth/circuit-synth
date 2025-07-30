# Blue Pill Clone Specifications

**Reference:** STM32-base project documentation
**Target:** Create circuit-synth implementation of popular Blue Pill dev board

## Core Specifications

### Microcontroller
- **Part:** STM32F103C8T6
- **Manufacturer:** ST-Microelectronics
- **Core:** Arm Cortex-M3
- **Max Clock:** 72MHz
- **Package:** LQFP 48 pins
- **Flash:** 64KiB
- **SRAM:** 20KiB

### Oscillators
- **HSI:** 8MHz (internal)
- **LSI:** 40kHz (internal)
- **HSE:** 8MHz (external crystal)
- **LSE:** 32.768kHz (external crystal)

### Power Supply
- **Input Sources:** +3.3V pins, +5V pins, USB connector (+5V)
- **Regulator:** TX6211B (SOT23-5)
  - Input: +3.6V to +5.5V
  - Output: +3.3V @ 300mA
  - Manufacturer: Shanghai TX Electronics

### PCB Specifications
- **Color:** Blue
- **Size:** 23mm x 53mm
- **Mounting:** Breadboard compatible

## Circuit Sections for Implementation

### 1. Power Supply Circuit
- USB connector (Micro USB)
- TX6211B voltage regulator (5V to 3.3V)
- Power LED indicator
- Decoupling capacitors

### 2. STM32 Core Circuit  
- STM32F103C8T6 microcontroller
- 8MHz HSE crystal oscillator
- 32.768kHz LSE crystal (optional)
- Decoupling capacitors
- Reset circuit

### 3. Programming/Debug Interface
- SWD header (4-pin)
  - 3V3 (VCC)
  - DIO (SWDIO) - PA13
  - CLK (SWCLK) - PA14
  - GND
- USB programming interface
  - D- (PA11)
  - D+ (PA12)
  - **Note:** May need 1.5kΩ pullup resistor fix

### 4. User I/O
- Reset button (NRST, active low)
- BOOT0 jumper
- BOOT1 jumper (connected to PB2)
- User LED (PC13, sink mode)
- Two 20-pin headers for GPIO access

## Headers and Connectors

### Header 1 (20 pins)
| Pin | Name | Connected To |
|-----|------|--------------|
| 1   | VB   | VBAT        |
| 2   | C13  | PC13        |
| 3   | C14  | PC14        |
| 4   | C15  | PC15        |
| 5   | A0   | PA0         |
| 6   | A1   | PA1         |
| 7   | A2   | PA2         |
| 8   | A3   | PA3         |
| 9   | A4   | PA4         |
| 10  | A5   | PA5         |
| 11  | A6   | PA6         |
| 12  | A7   | PA7         |
| 13  | B0   | PB0         |
| 14  | B1   | PB1         |
| 15  | B10  | PB10        |
| 16  | B11  | PB11        |
| 17  | R    | NRST        |
| 18  | 3.3  | +3.3V       |
| 19  | G    | GND         |
| 20  | G    | GND         |

### Header 2 (20 pins)
| Pin | Name | Connected To |
|-----|------|--------------|
| 1   | 3.3  | +3.3V       |
| 2   | G    | GND         |
| 3   | 5V   | +5V         |
| 4   | B9   | PB9         |
| 5   | B8   | PB8         |
| 6   | B7   | PB7         |
| 7   | B6   | PB6         |
| 8   | B5   | PB5         |
| 9   | B4   | PB4         |
| 10  | B3   | PB3         |
| 11  | A15  | PA15        |
| 12  | A12  | PA12        |
| 13  | A11  | PA11        |
| 14  | A10  | PA10        |
| 15  | A9   | PA9         |
| 16  | A8   | PA8         |
| 17  | B15  | PB15        |
| 18  | B14  | PB14        |
| 19  | B13  | PB13        |
| 20  | B12  | PB12        |

## Design Warnings & Considerations
1. **USB Power Warning:** +5V pins directly connected to USB +5V with no protection
2. **USB D+ Resistor:** May have wrong value (10kΩ or 4.7kΩ instead of 1.5kΩ)
3. **No VDDA/VSSA pins:** Analog supply tied to digital supply
4. **Simple reset circuit:** Basic button to NRST

## Circuit-Synth Implementation Strategy

### Hierarchical Design Approach
1. **Power Supply Subcircuit**
   - USB connector and protection
   - TX6211B regulator circuit
   - Power LED and decoupling

2. **STM32 Core Subcircuit**
   - MCU with decoupling capacitors
   - Crystal oscillator circuits
   - Reset button circuit

3. **Programming Interface Subcircuit**
   - SWD header connections
   - USB data lines
   - Boot configuration jumpers

4. **I/O Header Subcircuits**
   - GPIO header pin mappings
   - Power and ground distribution
   - User LED circuit

### Component Reuse Opportunities
- Standard decoupling capacitor patterns
- Crystal oscillator circuits
- LED indicator circuits
- Header connector patterns
- Power supply sections for other dev boards

This specification provides the complete technical foundation for implementing the Blue Pill clone in circuit-synth.