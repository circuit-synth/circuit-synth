# ESP32-S3 Design Guide

## ESP32-S3-MINI-1 Module Overview

### Module Features
- **ESP32-S3 SoC**: Dual-core Xtensa LX7 @ 240MHz
- **Integrated Flash**: 8MB built-in flash memory
- **Integrated PSRAM**: Optional 8MB PSRAM (check part number)
- **Crystal Oscillator**: 40MHz crystal included
- **RF Shielding**: Built-in antenna and RF matching
- **Power Management**: Integrated LDO and power sequencing

### Key Specifications
- **Operating Voltage**: 3.0V - 3.6V (3.3V nominal)
- **Supply Current**: 20-240mA (depending on operating mode)
- **Deep Sleep Current**: < 10µA typical
- **GPIO Count**: 45 programmable GPIOs
- **Package**: LGA-56 (7.2mm × 7.2mm)

## Power Supply Design

### Power Requirements
```
Operating Modes:
- Active (CPU + WiFi): 160-240mA @ 3.3V
- Active (CPU only): 20-50mA @ 3.3V  
- Light Sleep: 0.5-2mA @ 3.3V
- Deep Sleep: 5-10µA @ 3.3V
```

### Decoupling Strategy
```python
# Primary power decoupling - 10µF ceramic
cap_power = Component(
    symbol="Device:C", ref="C1", value="10uF",
    footprint="Capacitor_SMD:C_0805_2012Metric"
)

# High frequency decoupling - 100nF ceramic (optional)
cap_hf = Component(
    symbol="Device:C", ref="C2", value="100nF", 
    footprint="Capacitor_SMD:C_0603_1608Metric"
)
```

### Power Supply Recommendations
- **Linear Regulator**: 3.3V LDO for low noise applications
- **Switching Regulator**: Buck converter for battery-powered applications
- **USB Power**: Direct 3.3V regulation from 5V USB-C input

## Pin Configuration and Usage

### Critical Boot Pins
```
Pin 41 (IO0): Boot mode selection
  - HIGH: Normal boot from flash
  - LOW: Download/programming mode
  - Requires 10K pull-up resistor to 3.3V

Pin 3 (EN): Enable/Reset
  - HIGH: Normal operation
  - LOW: Hold in reset
  - Requires 10K pull-up resistor to 3.3V
```

### Safe GPIO Pins (No Boot Conflicts)
```
Safe for outputs: IO1, IO2, IO3, IO4, IO5, IO6, IO7, IO8, IO9, IO10
Safe for inputs: IO11, IO12, IO13, IO14, IO15, IO16, IO17, IO18
```

### Pins to Avoid During Boot
```
IO45, IO46: Used for internal flash - DO NOT USE
IO19, IO20: Used for USB - avoid unless needed for USB
IO26-IO32: ADC2 pins - cannot use with WiFi active
```

## Reset and Boot Control

### Standard Reset Circuit
```python
# EN pin pull-up for normal operation
r_en = Component("Device:R", ref="R1", value="10K", footprint="0603")
r_en[1] += esp32["EN"]    # Pin 3
r_en[2] += vcc_3v3        # Pull-up to 3.3V

# Optional reset button (connect between EN and GND)
# Button press pulls EN low = reset
```

### Boot Mode Control
```python
# IO0 pull-up for normal boot
r_io0 = Component("Device:R", ref="R2", value="10K", footprint="0603") 
r_io0[1] += esp32["IO0"]  # Pin 41
r_io0[2] += vcc_3v3       # Pull-up to 3.3V

# Programming interface: connect IO0 to GND via button for download mode
```

## Programming Interface

### UART Programming
```python
# Connect to USB-UART bridge (CP2102, CH340, etc.)
esp32["TXD0"] += uart_rx  # ESP32 TX to UART RX
esp32["RXD0"] += uart_tx  # ESP32 RX to UART TX

# Auto-reset circuit for programming (optional)
# Requires additional transistors and capacitors
```

### JTAG Programming (Advanced)
```python
# JTAG pins for debugging
esp32["MTCK"] += jtag_tck  # Clock
esp32["MTDO"] += jtag_tdo  # Data Out  
esp32["MTDI"] += jtag_tdi  # Data In
esp32["MTMS"] += jtag_tms  # Mode Select
```

## Peripheral Connections

### SPI Interface
```python
# SPI Master configuration
esp32["IO12"] += spi_miso  # Master In, Slave Out
esp32["IO11"] += spi_mosi  # Master Out, Slave In  
esp32["IO13"] += spi_sck   # Clock
esp32["IO10"] += spi_cs    # Chip Select
```

### I2C Interface  
```python
# I2C Master configuration
esp32["IO8"] += i2c_sda    # Data line
esp32["IO9"] += i2c_scl    # Clock line

# External pull-up resistors required (2.2K-10K)
r_sda = Component("Device:R", ref="R_SDA", value="4.7K", footprint="0603")
r_scl = Component("Device:R", ref="R_SCL", value="4.7K", footprint="0603")
```

### UART Interface
```python
# Additional UART (UART1)
esp32["IO17"] += uart1_tx  # UART1 Transmit
esp32["IO18"] += uart1_rx  # UART1 Receive
```

## LED and Status Indicators

### Status LED Design
```python
# LED on GPIO2 (safe pin, no boot conflicts)
r_led = Component("Device:R", ref="R_LED", value="330R", footprint="0603")
led = Component("Device:LED", ref="D1", value="LED", footprint="0603")

esp32["IO2"] += r_led[1]   # GPIO2 to current limiting resistor
r_led[2] += led[1]         # Resistor to LED anode
led[2] += gnd              # LED cathode to ground

# Current calculation: I = (3.3V - 2.1V) / 330Ω = 3.6mA
```

### RGB LED Control
```python
# WS2812B addressable LED
esp32["IO48"] += ws2812_din  # Data input to LED strip
# Requires 5V power supply for WS2812B LEDs
```

## PCB Layout Guidelines

### Power Delivery
- **Ground Plane**: Continuous ground plane under module
- **Power Traces**: Minimum 0.5mm width for power connections
- **Decoupling Placement**: Within 5mm of power pins

### RF Considerations
- **Antenna Clearance**: 5mm clearance around antenna area
- **Ground Plane**: Solid ground plane under module
- **Component Placement**: Keep high-speed signals away from antenna

### Thermal Management
- **Thermal Vias**: Add thermal vias under module for heat dissipation
- **Component Spacing**: Allow airflow around module
- **Heat Sinks**: Consider for high-power applications

## Common Design Mistakes

### Power Supply Issues
- ❌ Insufficient decoupling capacitance (causes brown-out resets)
- ❌ Wrong voltage level (ESP32-S3 is 3.3V, not 5V tolerant)
- ❌ Inadequate current capacity (causes instability during WiFi transmission)

### Boot Configuration Errors
- ❌ Missing pull-up resistors on EN and IO0
- ❌ Wrong resistor values (too low causes high current)
- ❌ Conflicting signals on boot pins during startup

### GPIO Usage Problems
- ❌ Using flash pins IO45/IO46 for other purposes
- ❌ Not considering boot-time pin states
- ❌ Exceeding GPIO current limits (40mA max per pin)

### Layout Issues
- ❌ Poor antenna placement (near metal objects)
- ❌ High-speed signals near antenna (causes interference)
- ❌ Inadequate ground plane (affects RF performance)

## Testing and Validation

### Power Supply Tests
- **Supply Voltage**: 3.3V ±3% under all load conditions
- **Supply Current**: Measure in different operating modes
- **Ripple**: < 100mV peak-to-peak on power supply

### Boot and Programming Tests
- **Boot Sequence**: Verify normal boot with IO0 high
- **Programming Mode**: Verify download mode with IO0 low
- **Reset Function**: Verify reset when EN pulled low

### RF Performance Tests
- **WiFi Range**: Test in open air and with obstacles
- **Power Consumption**: Measure during WiFi transmission
- **Regulatory Compliance**: FCC/CE certification if required

### GPIO Functionality Tests
- **Digital I/O**: Test all configured GPIO pins
- **Analog Inputs**: Test ADC functionality on ADC1 pins
- **PWM Outputs**: Test PWM generation capability
- **Communication**: Test SPI, I2C, UART interfaces