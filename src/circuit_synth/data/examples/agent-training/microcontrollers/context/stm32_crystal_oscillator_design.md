# STM32 Crystal Oscillator Design Guide

## Crystal Oscillator Fundamentals

### Why External Crystal?
- **Precision**: ±20ppm vs ±1% for internal RC oscillator
- **Stability**: Temperature and voltage stable timing
- **USB Compatibility**: Required for USB communication
- **UART Accuracy**: Reduces baud rate errors to <0.5%
- **Timer Precision**: Critical for PWM and measurement applications

### STM32G0 Clock Architecture
```
External Crystal (8MHz) → PLL → System Clock (up to 64MHz)
                        ↓
Internal RC (16MHz) ← HSI ← Default startup clock
```

## Crystal Selection Criteria

### Frequency Selection
- **8MHz**: Most common, good PLL multiplication options
- **16MHz**: Direct high-speed option, less PLL multiplication needed
- **25MHz**: Maximum for STM32G0 series
- **32.768kHz**: For RTC applications (separate LSE oscillator)

### Crystal Specifications
```
Parameter          | Typical Value | Notes
-------------------|---------------|-------------------------
Frequency          | 8.000000 MHz  | ±20ppm accuracy typical
Load Capacitance   | 18pF         | Determines external cap values
ESR (Resistance)   | <100Ω        | Lower is better for startup
Drive Level        | 100µW        | Maximum power dissipation
Temperature Range  | -40°C to +85°C| Industrial grade preferred
```

### Package Recommendations
- **HC-49/S SMD**: 8MHz, easy to source, good for prototypes
- **3225 SMD**: Compact, good for production
- **5032 SMD**: Higher stability, more expensive

## Load Capacitor Calculation

### Formula
```
CL = (C1 × C2)/(C1 + C2) + Cstray

Where:
CL = Crystal load capacitance (from datasheet)
C1, C2 = External load capacitors  
Cstray = PCB trace capacitance (2-5pF typical)
```

### Example Calculation
```
For 18pF load capacitance crystal:
CL = 18pF
Cstray = 3pF (estimated)

Solving for C1 = C2:
18 = (C × C)/(C + C) + 3
18 = C/2 + 3
15 = C/2
C = 30pF

However, use 18pF capacitors in practice to account for:
- MCU pin capacitance (~5pF per pin)
- PCB trace capacitance variations
- Component tolerances
```

### Standard Values
| Crystal CL | Recommended C1/C2 | Alternative |
|------------|-------------------|-------------|
| 12pF       | 12pF             | 10pF        |
| 18pF       | 18pF             | 15pF        |
| 20pF       | 22pF             | 18pF        |

## PCB Layout Guidelines

### Critical Layout Rules
1. **Keep crystal close**: <10mm trace length to MCU pins
2. **Ground plane**: Continuous ground under crystal
3. **Avoid routing**: No signals under or near crystal
4. **Component placement**: Load caps as close as possible to crystal
5. **Via placement**: Minimize vias in crystal circuit

### Optimal Layout Pattern
```
STM32 OSC_IN ←--[<5mm]--→ Crystal Pin 1
   |                         |
   ↓ [C1 to GND]         [C2 to GND] ↑
   |                         |
STM32 OSC_OUT ←--[<5mm]--→ Crystal Pin 2

Ground plane continuous under entire circuit
```

### EMI Considerations
- **Shielding**: Ground plane acts as shield
- **Drive strength**: Use lowest drive level that ensures reliable startup
- **Filtering**: Load capacitors provide high-frequency filtering
- **Isolation**: Keep switching circuits away from crystal

## STM32 Configuration

### Pin Connections
```c
// STM32G030 Crystal Pins
PF0-OSC_IN  → Crystal Pin 1 + Load Capacitor to GND
PF1-OSC_OUT → Crystal Pin 2 + Load Capacitor to GND
```

### Clock Configuration (STM32CubeMX)
```c
// Enable HSE (High Speed External) oscillator
RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
RCC_OscInitStruct.HSEState = RCC_HSE_ON;

// Configure PLL to multiply 8MHz → 64MHz
RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV1;    // 8MHz / 1 = 8MHz
RCC_OscInitStruct.PLL.PLLN = 16;               // 8MHz × 16 = 128MHz
RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;    // 128MHz / 2 = 64MHz
```

### Startup Timing
- **Crystal startup**: 2-10ms typical (depends on crystal and load caps)
- **PLL lock time**: <200µs after crystal stable
- **Total startup**: <10ms from power-on to stable system clock

## Component Selection Guide

### Crystal Recommendations
```python
# 8MHz fundamental mode crystal
crystal = Component(
    symbol="Device:Crystal",
    ref="Y1",
    value="8MHz",
    footprint="Crystal:Crystal_SMD_HC49-SD"
)
```

**Verified Parts (JLCPCB Available)**:
- **8MHz HC-49S**: C12674 (>50k stock, $0.08)
- **8MHz 3225**: C9002 (>20k stock, $0.12)
- **16MHz HC-49S**: C12675 (>30k stock, $0.09)

### Load Capacitor Selection
```python
# 18pF load capacitors (C0G/NP0 dielectric)
cap_load = Component(
    symbol="Device:C",
    ref="C", 
    value="18pF",
    footprint="Capacitor_SMD:C_0603_1608Metric"
)
```

**Requirements**:
- **Dielectric**: C0G (NP0) for temperature stability
- **Tolerance**: ±5% or better
- **Voltage**: 50V minimum (safety margin)
- **Package**: 0603 preferred for hand soldering

## Testing and Validation

### Oscilloscope Measurements
1. **Frequency Check**: Measure at OSC_OUT pin
   - Expected: Crystal frequency ±20ppm
   - Use 10:1 probe to minimize loading

2. **Amplitude Check**: Measure peak-to-peak voltage
   - Expected: 0.5V to 3.0V pk-pk
   - Too low: Increase drive level
   - Too high: Decrease drive level or add series resistor

3. **Startup Time**: Measure time from power-on to stable oscillation
   - Expected: <10ms typical
   - Slow startup: Check load capacitor values

### Software Verification
```c
// Check if HSE is ready and PLL locked
if (HAL_RCC_GetSysClockFreq() == 64000000) {
    // System clock correct
} else {
    // Clock configuration error
}

// Measure actual frequency using timer capture
// Expected: Crystal frequency within ±20ppm
```

### Common Issues and Solutions

#### Crystal Won't Start
- **Cause**: Load capacitors too large, low drive level
- **Solution**: Reduce load caps by 2-5pF, increase drive level

#### Frequency Drift  
- **Cause**: Temperature effects, poor layout
- **Solution**: Use temperature-compensated crystal, improve layout

#### EMI Issues
- **Cause**: Strong drive level, poor shielding
- **Solution**: Reduce drive level, improve ground plane

#### Intermittent Operation
- **Cause**: Marginal oscillation, noise coupling
- **Solution**: Check load caps, improve power supply decoupling

## Production Considerations

### Quality Control
- **Frequency measurement**: All units within ±50ppm
- **Startup reliability**: 100% success rate at temperature extremes
- **EMI compliance**: Verify emissions meet regulatory requirements

### Cost Optimization
- **Standard frequencies**: 8MHz, 16MHz have best pricing/availability
- **Package size**: Larger packages generally more stable but more expensive
- **Load capacitance**: Standard values (18pF, 22pF) have better pricing

### Supply Chain
- **Dual sourcing**: Always have backup crystal supplier
- **Stock monitoring**: Crystals can have long lead times
- **Testing**: Incoming inspection for frequency and startup characteristics

This crystal oscillator design provides reliable, precise timing for STM32 applications while maintaining cost-effectiveness and ease of manufacturing.