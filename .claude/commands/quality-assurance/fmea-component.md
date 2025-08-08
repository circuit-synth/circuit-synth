---
name: fmea-component
description: Deep-dive FMEA analysis for specific components
---

# Component-Specific FMEA Analysis

Performs detailed failure analysis on specific components or component types.

## Usage

```bash
/fmea-component <circuit_path> --component <ref> [options]
```

## Options

- `--component <ref>`: Component reference (e.g., U1, C1) or type (e.g., all-capacitors)
- `--physics`: Include physics-of-failure analysis
- `--thermal`: Perform thermal stress analysis
- `--lifetime`: Calculate expected lifetime
- `--alternatives`: Suggest alternative components

## What it does

1. **Component Deep Dive**
   - Extracts all component parameters
   - Identifies technology and construction
   - Analyzes operating conditions
   - Calculates stress factors

2. **Failure Mode Analysis**
   - Lists all applicable failure mechanisms
   - Calculates occurrence based on conditions
   - Assesses detection difficulty
   - Determines severity in circuit context

3. **Physics-Based Modeling**
   - Arrhenius acceleration for temperature
   - Power law for voltage stress
   - Coffin-Manson for thermal cycling
   - Electromigration modeling

4. **Recommendations**
   - Derating suggestions
   - Alternative components
   - Protection circuits
   - Test methods

## Examples

```bash
# Analyze specific MCU
/fmea-component my_circuit.py --component U1 --physics --thermal

# Analyze all capacitors with lifetime prediction
/fmea-component circuit.json --component all-capacitors --lifetime

# Deep dive on power MOSFET with alternatives
/fmea-component power_supply/ --component Q1 --physics --alternatives

# Thermal analysis of voltage regulator
/fmea-component board/ --component U3 --thermal --lifetime
```

## Output Format

```yaml
Component: U1 - STM32F407VET6
Type: Microcontroller
Package: LQFP-100

Operating Conditions:
  Supply Voltage: 3.3V (nominal)
  Junction Temperature: 85°C (calculated)
  Power Dissipation: 450mW
  Frequency: 168MHz

Stress Analysis:
  Voltage Derating: 73% (acceptable)
  Temperature Derating: 68% (marginal)
  Current Density: Within limits

Failure Modes:
  1. Flash Corruption
     - Occurrence: 3
     - Detection: 7
     - Severity: 8
     - RPN: 168
     - Mitigation: Implement CRC checks, brownout detection
  
  2. Latch-up
     - Occurrence: 2
     - Detection: 5
     - Severity: 8
     - RPN: 80
     - Mitigation: Power sequencing, input protection

Lifetime Prediction:
  MTBF: 850,000 hours
  B10 Life: 65,000 hours
  Useful Life: 10 years at 85°C

Recommendations:
  1. Reduce junction temperature to 70°C
  2. Add external watchdog timer
  3. Implement redundant flash storage
  4. Consider automotive grade variant
```

## Integration

Utilizes:
- Component failure mode database
- Manufacturer reliability data
- Physics-of-failure models
- Derating guidelines

This command is ideal for critical component qualification and selection.