# How to Use STM32 Integration - User Guide

## Quick Start: Get STM32 Recommendations in Seconds

### Method 1: AI-Powered MCU Selection (Recommended)

Simply describe your project in natural language:

```bash
/find-stm32-mcu IoT sensor node with LoRa, 2 UARTs, SPI, low power, battery operated
```

**What you get instantly:**
- 2-3 optimal STM32 recommendations with trade-offs
- Complete pin assignments with AF numbers
- JLCPCB availability and pricing verification
- Ready circuit-synth Component code
- Package and footprint recommendations

### Method 2: Programmatic Pin Mapping

For advanced users who want direct control:

```python
from circuit_synth.stm32_pinout import STM32PinMapper

# Initialize for specific STM32 family
mapper = STM32PinMapper("g4-31_41", modm_devices_path="external_repos/modm-devices")

# Find all options for a specific peripheral
usart_options = mapper.find_pins_for_peripheral("usart1", "tx")
print(f"Found {len(usart_options)} USART1 TX options:")
for option in usart_options[:3]:
    print(f"  {option.pin.name}: {option.reasoning} (confidence: {option.confidence:.2f})")

# Get complete assignment for multiple peripherals
requirements = {
    "usart1_tx": "tx", "usart1_rx": "rx",
    "spi1_sck": "sck", "spi1_miso": "miso", "spi1_mosi": "mosi", 
    "i2c1_scl": "scl", "i2c1_sda": "sda"
}
assignments = mapper.suggest_pin_assignment(requirements)

# Use the assignments in your circuit
for peripheral, recommendation in assignments.items():
    print(f"{peripheral}: {recommendation.pin.name} ({recommendation.reasoning})")
```

## Real-World Usage Examples

### Example 1: Motor Controller Design

```bash
/find-stm32-mcu 3-phase BLDC motor controller with encoder feedback, current sensing, CAN bus
```

**Expected Response:**
```
🎯 STM32G474CBT6 - Motor Control Specialist
💡 ARM Cortex-M4F @ 170MHz, 128KB Flash, 32KB RAM
📦 LQFP-48 | 💰 $3.25@100pcs | ✅ 12K units in stock

📋 Motor Control Pin Assignment:
- TIM1_CH1: PA8 (AF6) | TIM1_CH1N: PA7 (AF6) [Phase A PWM]
- TIM1_CH2: PA9 (AF6) | TIM1_CH2N: PB0 (AF6) [Phase B PWM] 
- TIM1_CH3: PA10 (AF6) | TIM1_CH3N: PB1 (AF6) [Phase C PWM]
- ADC1_IN1: PA0 [Current sense A] | ADC1_IN2: PA1 [Current sense B]
- TIM2_CH1: PA5 | TIM2_CH2: PA6 [Encoder A/B]
- CAN1_TX: PB9 (AF9) | CAN1_RX: PB8 (AF9)

🔌 Ready Circuit-Synth Code:
mcu = Component(
    symbol="MCU_ST_STM32G4:STM32G474CBTx", 
    ref="U1",
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
)
# Complete pin connections and power supply included...
```

### Example 2: IoT Data Logger  

```bash
/find-stm32-mcu IoT data logger with WiFi module, SD card, multiple sensors via I2C/SPI, USB for configuration
```

**Expected Response:**
```
🎯 STM32G431CBT6 - IoT Optimized Choice
💡 ARM Cortex-M4 @ 170MHz, 128KB Flash, 32KB RAM
📦 LQFP-48 | 💰 $2.50@100pcs | ✅ 83K units in stock

📋 IoT Logger Pin Assignment:
- USART1_TX: PA9 (AF7) | USART1_RX: PA10 (AF7) [WiFi Module]
- SPI1_SCK: PA5 (AF5) | SPI1_MISO: PA6 (AF5) | SPI1_MOSI: PA7 (AF5) [SD Card]
- I2C1_SCL: PB8 (AF4) | I2C1_SDA: PB9 (AF4) [Sensors]
- USB_DP: PA12 | USB_DM: PA11 [Configuration Interface]

Alternative: STM32G070CBT6 ($1.45) for cost-sensitive applications
```

### Example 3: Audio Processing System

```bash  
/find-stm32-mcu Audio processor with I2S input/output, USB audio class, DSP capabilities, external SRAM interface
```

## Advanced Usage Patterns

### Pattern 1: Design Iteration with Alternatives

```python
# Start with basic requirements
mapper = STM32PinMapper("g4-31_41", "external_repos/modm-devices") 

# Get multiple options
basic_requirements = {"usart1": "tx", "spi1": "sck"}
assignments = mapper.suggest_pin_assignment(basic_requirements)

# Add more peripherals and check conflicts
extended_requirements = {**basic_requirements, "i2c1": "sda", "tim1": "ch1"}
extended_assignments = mapper.suggest_pin_assignment(extended_requirements) 

# Compare options and select optimal configuration
```

### Pattern 2: Family Comparison

```python
from circuit_synth.stm32_pinout import get_supported_devices

# Compare different STM32 families for same requirements
families = ["g0-30", "g4-31_41", "f4-01_11"]
requirements = {"usart1_tx": "tx", "spi1_sck": "sck", "i2c1_sda": "sda"}

for family in families:
    try:
        mapper = STM32PinMapper(family, "external_repos/modm-devices")
        assignments = mapper.suggest_pin_assignment(requirements)
        print(f"\n{family.upper()} Family:")
        for req, rec in assignments.items():
            print(f"  {req}: {rec.pin.name} (confidence: {rec.confidence:.2f})")
    except Exception as e:
        print(f"{family}: Not available - {e}")
```

### Pattern 3: Pin Function Analysis

```python
# Analyze what functions are available on specific pins
mapper = STM32PinMapper("g4-31_41", "external_repos/modm-devices")

# Check all functions on PA9
pa9_functions = mapper.get_pin_functions("PA9")
print("PA9 available functions:")
for signal in pa9_functions:
    af_str = f"AF{signal.af}" if signal.af else "default"
    print(f"  {signal.driver}{signal.instance}.{signal.name} ({af_str})")

# Find alternative pins for USART1_TX
usart_tx_options = mapper.find_pins_for_peripheral("usart1", "tx")
print(f"\nUSART1 TX alternatives ({len(usart_tx_options)} options):")
for option in usart_tx_options:
    print(f"  {option.pin.name}: {option.reasoning}")
```

## Best Practices

### 1. Start with Natural Language
- Use `/find-stm32-mcu` for initial exploration
- Describe your project clearly: power requirements, peripherals, constraints
- Get multiple options and understand trade-offs

### 2. Verify Manufacturing Availability  
- Check JLCPCB stock levels in recommendations
- Consider alternative parts for production volumes
- Verify lead times for critical projects

### 3. Plan for Expansion
- Leave some pins unassigned for future features
- Choose MCUs with more peripherals than minimum requirements
- Consider package upgrade paths (e.g., LQFP48 → LQFP64)

### 4. Validate Pin Assignments
- Use confidence scores to understand assignment quality
- Review reasoning for critical signals
- Check for any pin conflicts before finalizing design

### 5. Integrate with Circuit Design
- Use generated circuit-synth code as starting point
- Add power supply, crystals, and decoupling capacitors
- Verify KiCad symbol and footprint availability

## Troubleshooting

### Common Issues

**"No suitable components found"**
- Check that modm-devices path is correct
- Verify STM32 family name format (e.g., "g4-31_41", not "STM32G431")
- Try broader peripheral requirements

**"Pin conflict detected"**  
- Review peripheral requirements for overlapping functions
- Use confidence scores to find best alternatives
- Consider different STM32 family with more pins

**"Symbol/footprint not found"**
- Verify KiCad library installation
- Check symbol name format in generated code
- Use `/find-symbol` command to locate correct symbols

### Getting Help

1. **Documentation**: Check memory-bank/features/2025-07-29-stm32-integration.md
2. **Examples**: Review working examples in repository
3. **Agent Support**: Use `/find-stm32-mcu` for guided recommendations
4. **Community**: GitHub Discussions for advanced use cases

This integration makes STM32 development accessible to everyone while maintaining professional quality and manufacturing readiness.