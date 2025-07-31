# Generate Circuit

**Command**: `/generate_circuit <description>`

**Purpose**: Generate complete circuit-synth Python code for specified circuit requirements, optimized for manufacturing and KiCad integration.

## Usage Examples

```bash
# ESP32 development board
/generate_circuit esp32 development board with usb-c and 3.3v regulator

# STM32 project
/generate_circuit stm32g4 board with usb uart imu and power management

# Power supply circuit
/generate_circuit 5v to 3.3v linear regulator with proper decoupling

# Sensor interface
/generate_circuit mpu6050 imu breakout board with esp32 interface
```

## Generation Capabilities

### Microcontroller Boards
- **ESP32 Variants**: ESP32-S3-MINI-1, ESP32-C3, ESP32-S2
- **STM32 Families**: STM32F4, STM32G4, STM32L4 with peripheral integration
- **Arduino Compatible**: Shields and development platforms

### Power Management
- **Linear Regulators**: NCP1117, AMS1117 with proper input/output capacitors
- **USB Power**: USB-C PD integration with protection circuits
- **Multiple Rails**: 5V, 3.3V, 1.8V power distribution

### Interface Circuits
- **USB Interfaces**: USB-C, USB-A, micro-USB with ESD protection
- **Communication**: SPI, I2C, UART level shifting and isolation
- **Programming**: SWD, JTAG debugging interfaces

### Sensor Integration
- **IMU Sensors**: MPU-6050, LSM6DS3 with proper decoupling
- **Environmental**: Temperature, humidity, pressure sensors
- **Analog Sensors**: ADC integration with filtering

## Code Generation Process

### Phase 1: Requirement Analysis
- Parse circuit description and identify components needed
- Determine power requirements and voltage rails
- Identify interface and connectivity needs

### Phase 2: Component Selection
- Choose manufacturing-ready components from JLCPCB database
- Prefer Basic parts for cost and availability
- Verify KiCad symbol and footprint availability

### Phase 3: Circuit Topology Design
- Design proper power distribution with decoupling
- Plan signal routing and interface connections
- Add protection circuits and ESD considerations

### Phase 4: Code Generation
- Generate circuit-synth Python with proven templates
- Use verified pin mappings and component configurations
- Include comprehensive project generation setup

## Generated Code Structure

```python
from circuit_synth import *

@circuit(name="project_name")
def main():
    """Generated circuit description and specifications"""
    
    # Power nets with descriptive names
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Main components with verified configurations
    esp32 = Component("RF_Module:ESP32-S3-MINI-1", ref="U1", 
                     footprint="RF_Module:ESP32-S2-MINI-1")
    esp32[1] += gnd      # Pin 1 = GND (verified)
    esp32[3] += vcc_3v3  # Pin 3 = 3V3 (verified)
    
    # Power management
    regulator = Component("Regulator_Linear:NCP1117-3.3_SOT223", 
                         ref="U2", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    regulator[1] += gnd      # Pin 1 = GND
    regulator[2] += vcc_3v3  # Pin 2 = 3.3V out
    regulator[3] += vcc_5v   # Pin 3 = 5V in
    
    # Decoupling capacitors
    cap_in = Component("Device:C", ref="C1", value="10uF", 
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_in[1] += vcc_5v
    cap_in[2] += gnd
    
    cap_out = Component("Device:C", ref="C2", value="10uF", 
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd
    
    return circuit

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("project_name", force_regenerate=True)
```

## Quality Assurance

### Electrical Validation
- **Power Distribution**: Proper voltage rail connections
- **Ground Planning**: Single-point grounding where appropriate
- **Decoupling**: Adequate decoupling capacitors for all ICs
- **Signal Integrity**: Proper impedance and routing considerations

### Manufacturing Validation
- **Component Availability**: All components in stock at JLCPCB
- **Package Selection**: Hand-assembly friendly when possible
- **Cost Optimization**: Prefer Basic parts, standard values
- **Assembly Constraints**: Consider pick-and-place limitations

### KiCad Integration
- **Symbol Verification**: All symbols exist in standard libraries
- **Footprint Accuracy**: Footprints match component packages
- **Pin Mapping**: Pin numbers verified against datasheets
- **Project Generation**: Creates error-free KiCad projects

## Advanced Features

### Design Rules Integration
```bash
# High-speed design considerations
/generate_circuit esp32 board with high-speed usb and impedance control
```

### Manufacturing Constraints
```bash
# Cost-optimized design
/generate_circuit basic stm32 development board lowest cost jlcpcb basic parts only
```

### Application-Specific
```bash
# IoT sensor node
/generate_circuit low power esp32 sensor node with battery management deep sleep
```

### Educational/Learning
```bash
# Learning project
/generate_circuit simple led blinker with stm32 for beginners step by step
```

## Output Includes

1. **Complete Python Code**: Ready to execute circuit-synth generation
2. **Component List**: All components with JLCPCB part numbers
3. **Pin Mapping**: Detailed pin assignments and connections
4. **Usage Instructions**: How to generate and open in KiCad
5. **Design Notes**: Circuit operation and design decisions

This command transforms circuit ideas into manufacturing-ready designs in minutes.