# Reference Circuits for Fast Generation

This directory contains complete, working circuit-synth examples that demonstrate proper syntax and professional circuit design patterns. These files serve as direct references for LLM agents during fast circuit generation.

## 📋 Available Reference Circuits

### Basic Development Boards
- **`esp32_basic.py`** - ESP32-S3 development board with USB-C, crystal, and debug header
- **`stm32_basic.py`** - STM32F411 development board with crystal, SWD debug, and reset circuit

### Sensor Integration  
- **`esp32_sensor.py`** - ESP32-S3 with MPU-6050 IMU sensor and I2C pull-up resistors

### Motor Control
- **`motor_stepper.py`** - DRV8825 stepper motor driver with current limiting and protection

### LED Control
- **`led_neopixel.py`** - 74AHCT125 level shifter for controlling 5V NeoPixel LEDs from 3.3V MCU

### Power Supply
- **`usb_power.py`** - USB-C power input with CC resistors and power delivery negotiation

## 🎯 Purpose

These reference circuits provide:

1. **Correct Syntax Examples**: Proper circuit-synth code structure with `@circuit` decorator
2. **Verified Components**: All components use validated KiCad symbols and footprints
3. **Professional Design**: Industry best practices for power, signal integrity, and protection
4. **Pin Connection Patterns**: Correct `component["pin"] += net` syntax
5. **Complete Projects**: Each file generates a working KiCad project

## 🚀 Usage in Fast Generation

When LLM agents receive circuit generation requests, they:

1. **Reference these files** for proper syntax patterns
2. **Copy working component definitions** with verified symbols/footprints  
3. **Follow connection patterns** for similar circuit types
4. **Inherit design practices** like decoupling, pull-ups, protection circuits

## 🧪 Testing Reference Circuits

Each circuit can be run independently:

```bash
# Test ESP32 basic board generation
python3 src/circuit_synth/fast_generation/reference_circuits/esp32_basic.py

# Test sensor integration circuit  
python3 src/circuit_synth/fast_generation/reference_circuits/esp32_sensor.py

# List all available reference circuits
python3 -c "from src.circuit_synth.fast_generation.reference_circuits import list_reference_circuits; list_reference_circuits()"
```

## 📚 Circuit Design Patterns Demonstrated

### Component Definition Pattern
```python
component = Component(
    symbol="Library:ComponentName",
    ref="U", 
    footprint="Package:FootprintName"
)
```

### Pin Connection Pattern  
```python
component["pin_name"] += net_name
```

### Power Distribution Pattern
```python
vcc_3v3 = Net('VCC_3V3')
gnd = Net('GND')
component["VDD"] += vcc_3v3
component["GND"] += gnd
```

### Professional Design Practices
- Power supply decoupling capacitors near each IC
- Pull-up/pull-down resistors where required
- Crystal load capacitors for oscillators
- Current limiting for LEDs and high-current signals
- ESD protection and filtering
- Proper connector pinouts and power distribution

## 🔄 Updating Reference Circuits

When adding new reference circuits:

1. **Follow naming convention**: `pattern_type.py` (e.g., `power_regulator.py`)
2. **Include complete documentation** in docstrings
3. **Use verified KiCad components** from standard libraries
4. **Test circuit generation** before committing
5. **Update `__init__.py`** to include new circuit in catalog
6. **Update this README** with new circuit description

These reference circuits form the foundation for fast, accurate circuit generation with proper professional design practices and verified component libraries.