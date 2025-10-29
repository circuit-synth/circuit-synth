# FMEA Analysis Guide

## Overview

Failure Mode and Effects Analysis (FMEA) in circuit-synth provides automated reliability analysis for electronic circuit designs. The system analyzes circuits to identify potential failure modes, assess their risk, and recommend mitigation strategies.

### What is FMEA?

FMEA is a systematic methodology for:
- **Identifying** potential failure modes in components and systems
- **Analyzing** the effects of each failure on the circuit
- **Prioritizing** risks using Risk Priority Numbers (RPN)
- **Recommending** design improvements to reduce risk

### Key Features

- **Automated component analysis** - Identifies 13+ component types and their specific failure modes
- **Comprehensive failure database** - Pre-loaded with industry-standard failure modes for common components
- **Context-aware risk assessment** - Adjusts ratings based on circuit environment and stress factors
- **Professional PDF reports** - Publication-ready analysis with executive summaries and detailed tables
- **Physics-based reliability models** - References Arrhenius, Coffin-Manson, and Black's equation
- **IPC Class 3 compliance** - High-reliability assembly standards

---

## Quick Start

### Basic Usage

Analyze any circuit file (Python or JSON):

```bash
# Analyze a Python circuit file
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py

# Analyze with custom output filename
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py -o report.pdf

# Analyze a circuit directory
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli ./ESP32_Project/
```

### Python API

```python
from circuit_synth.quality_assurance import analyze_any_circuit

# Perform FMEA analysis and generate PDF report
report_path = analyze_any_circuit(
    circuit_path="my_circuit.py",
    output_pdf="FMEA_Report.pdf",
    verbose=True
)

print(f"Report generated: {report_path}")
```

---

## Understanding FMEA Reports

### Risk Priority Number (RPN)

The RPN quantifies risk severity using three factors:

**RPN = Severity × Occurrence × Detection**

Each factor is rated on a scale of 1-10:

#### Severity (S)
How serious is the effect of the failure?
- **10**: Catastrophic - Safety hazard, complete system failure
- **8-9**: Critical - Major function loss, potential damage
- **6-7**: Moderate - Partial function loss, degraded performance
- **4-5**: Minor - Small impact, reduced capability
- **1-3**: Negligible - Minimal effect, barely noticeable

#### Occurrence (O)
How likely is the failure to occur?
- **10**: Very High - Failure almost inevitable (>1 in 2)
- **8-9**: High - Repeated failures (1 in 3 to 1 in 8)
- **6-7**: Moderate - Occasional failures (1 in 20 to 1 in 80)
- **4-5**: Low - Relatively few failures (1 in 400 to 1 in 2,000)
- **1-3**: Remote - Failure unlikely (<1 in 15,000)

#### Detection (D)
How likely is the failure to be detected before reaching the customer?
- **10**: Absolute Uncertainty - Cannot detect
- **8-9**: Very Remote - Very unlikely to detect
- **6-7**: Low - Low likelihood of detection
- **4-5**: Moderate - Moderate likelihood of detection
- **2-3**: High - High likelihood of detection
- **1**: Almost Certain - Defect is obvious and will be caught

### Risk Levels

Based on the calculated RPN:

| Risk Level | RPN Range | Action Required | Priority |
|------------|-----------|-----------------|----------|
| **Critical** | ≥ 300 | Immediate action required | 🔴 HIGH |
| **High** | 125-299 | Action required before production | 🟠 HIGH |
| **Medium** | 50-124 | Monitor and improve if feasible | 🟡 MEDIUM |
| **Low** | < 50 | Acceptable risk level | 🟢 LOW |

---

## Component-Specific Failure Modes

The FMEA analyzer includes comprehensive failure mode databases for common components.

### Connectors

**Common Failure Modes:**
- **Solder joint failure** (RPN: ~378)
  - Cause: Thermal cycling, mechanical stress
  - Effect: Complete loss of connection, system failure
  - Mitigation: Add mechanical support, thicker copper pours, strain relief

- **Contact oxidation** (RPN: ~150)
  - Cause: Environmental exposure, age
  - Effect: Intermittent connection, data errors
  - Mitigation: Use gold-plated contacts, conformal coating

- **Mechanical damage** (RPN: ~112)
  - Cause: Insertion cycles, excessive force
  - Effect: Connection loss, physical damage
  - Mitigation: Specify rated mating cycles, design guide features

### Voltage Regulators

**Common Failure Modes:**
- **Thermal shutdown** (RPN: ~336)
  - Cause: Overcurrent, poor heatsinking
  - Effect: System power loss, unexpected reset
  - Mitigation: Improve heatsinking, add thermal vias, use higher-rated component

- **Output voltage drift** (RPN: ~245)
  - Cause: Component aging, temperature variation
  - Effect: Component malfunction, reduced reliability
  - Mitigation: Use precision references, add feedback monitoring

- **Input overvoltage failure** (RPN: ~252)
  - Cause: Transient spikes, improper supply
  - Effect: Cascading component damage
  - Mitigation: Add TVS diodes, input filtering, reverse polarity protection

### Microcontrollers (MCU)

**Common Failure Modes:**
- **ESD damage** (RPN: ~288)
  - Cause: Handling discharge, environmental events
  - Effect: Complete MCU failure, system inoperable
  - Mitigation: Add TVS diodes, ESD protection circuits, guard rings

- **Clock failure** (RPN: ~144)
  - Cause: Crystal defect, oscillator circuit issue
  - Effect: System hang, timing errors
  - Mitigation: Add backup oscillator, use temperature-compensated crystal

- **Flash corruption** (RPN: ~196)
  - Cause: Power brownout, EMI
  - Effect: Firmware corruption, boot failure
  - Mitigation: Add brownout detection, power supply holdup, watchdog timer

- **I/O pin failure** (RPN: ~150)
  - Cause: Overvoltage, overcurrent on pins
  - Effect: Peripheral communication loss
  - Mitigation: Add series resistors, clamping diodes, current limiting

### Capacitors

**Common Failure Modes:**
- **Capacitance degradation** (RPN: ~245)
  - Cause: Aging, temperature stress
  - Effect: Increased ripple, filtering ineffective
  - Mitigation: Use higher-grade capacitors, voltage derating, add redundancy

- **ESR increase** (RPN: ~252)
  - Cause: Electrolyte drying (aluminum electrolytics)
  - Effect: Power supply instability, heating
  - Mitigation: Use ceramic or polymer capacitors, specify long-life grades

- **Short circuit** (RPN: ~120)
  - Cause: Dielectric breakdown, overvoltage
  - Effect: Power rail short, system damage
  - Mitigation: Voltage derating (50-80%), use X7R/X5R ceramics

- **Open circuit** (RPN: ~105)
  - Cause: Lead fracture, mechanical stress
  - Effect: Loss of filtering/decoupling
  - Mitigation: Mechanical support, avoid flexing PCB regions

### Resistors

**Common Failure Modes:**
- **Resistance drift** (RPN: ~192)
  - Cause: Temperature coefficient, aging
  - Effect: Circuit parameter changes, performance degradation
  - Mitigation: Use tight-tolerance resistors (1% or better), temperature-stable types

- **Open circuit** (RPN: ~90)
  - Cause: Overstress, manufacturing defect
  - Effect: Circuit malfunction, signal loss
  - Mitigation: Power derating, use 0.5W resistors for 0.125W applications

- **Thermal damage** (RPN: ~168)
  - Cause: Exceeded power rating
  - Effect: Resistance change, fire hazard
  - Mitigation: Calculate actual power dissipation, use larger packages

### Crystals/Oscillators

**Common Failure Modes:**
- **Frequency drift** (RPN: ~280)
  - Cause: Aging, temperature variation
  - Effect: Timing errors, communication failures
  - Mitigation: Use TCXO (temperature-compensated), proper load capacitance

- **Mechanical fracture** (RPN: ~216)
  - Cause: Shock, vibration
  - Effect: Complete loss of oscillation, system failure
  - Mitigation: Mechanical isolation, potting for high-vibration environments

- **Loss of oscillation** (RPN: ~168)
  - Cause: Drive level issues, contamination
  - Effect: System won't start or crashes
  - Mitigation: Follow manufacturer drive level specs, proper PCB layout

---

## Interpreting PDF Reports

The generated PDF report contains multiple sections:

### 1. Title Page
- Project name and date
- Author/analyzer information
- Standards reference (AIAG-VDA FMEA, IPC-A-610)

### 2. Executive Summary
Statistics and key findings:
- Total failure modes analyzed
- Count of critical/high/medium/low risk modes
- Average RPN score
- Overall risk assessment

### 3. System Overview
- Circuit description
- Subsystem breakdown
- Component count

### 4. FMEA Analysis Table
Detailed table showing:
- Component identifier
- Failure mode description
- Severity (S), Occurrence (O), Detection (D) ratings
- Calculated RPN
- Color-coded risk levels

### 5. Detailed Failure Analysis
For each high-risk failure mode:
- Root cause analysis
- Effect on system/circuit
- Specific mitigation recommendations

### 6. Risk Assessment Matrix
Visual distribution of risks across categories with action requirements

### 7. Recommendations
- Priority actions for critical items
- General design improvement recommendations
- Testing and validation suggestions

---

## Advanced Features

### Enhanced FMEA with Knowledge Base

For more comprehensive analysis using the extended knowledge base:

```python
from circuit_synth.quality_assurance.enhanced_fmea_analyzer import (
    analyze_circuit_with_enhanced_kb
)

# Perform enhanced analysis
report_path = analyze_circuit_with_enhanced_kb(
    circuit_path="my_circuit.py",
    output_pdf="Enhanced_FMEA_Report.pdf"
)
```

The enhanced analyzer includes:
- **Environmental stress modes** - Thermal cycling, vibration, humidity, ESD
- **Manufacturing defects** - Solder joint defects, tombstoning, bridging, voids
- **Silicon-level failures** - Gate oxide breakdown, electromigration, latchup
- **Package-level failures** - Wire bond failures, mold compound issues

### Custom Circuit Context

Adjust analysis based on operating environment:

```python
from circuit_synth.quality_assurance.fmea_analyzer import UniversalFMEAAnalyzer

analyzer = UniversalFMEAAnalyzer(verbose=True)
circuit_data, failure_modes = analyzer.analyze_circuit_file("circuit.py")

# Add context information
circuit_context = {
    "environment": "automotive",  # or 'consumer', 'industrial', 'medical', 'aerospace'
    "production_volume": "high",  # 'prototype', 'low', 'medium', 'high'
    "safety_critical": True,      # Increases severity ratings
    "operating_temperature": "-40 to 125C",
    "expected_lifetime": "15 years"
}

# Regenerate with context
report = analyzer.generate_report(circuit_data, failure_modes, "Automotive_FMEA.pdf")
```

### CLI Advanced Options

```bash
# Display top 20 risks instead of default 10
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli circuit.py --top 20

# Use custom RPN threshold for high-risk classification
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli circuit.py --threshold 150

# Verbose output with detailed analysis
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli circuit.py -v
```

---

## Mitigation Strategies

### General Design Principles

1. **Component Derating**
   - Voltage: Use components rated for 2× actual voltage
   - Current: Derate to 50-80% of maximum rating
   - Power: Use resistors at 25-50% of rated power
   - Temperature: Ensure components operate well below max temperature

2. **Redundancy**
   - Parallel components for critical functions
   - Backup power supplies
   - Redundant communication paths

3. **Protection Circuits**
   - TVS diodes for ESD and transient protection
   - Fuses and resettable PTC devices for overcurrent
   - Reverse polarity protection
   - Brownout detection and reset circuits

4. **Thermal Management**
   - Adequate heatsinking for power components
   - Thermal vias to spread heat
   - Keep-out zones around hot components
   - Temperature monitoring where critical

5. **Design for Test (DFT)**
   - Test points for critical signals
   - JTAG/SWD access for MCUs
   - Current monitoring points
   - Voltage monitoring test points

### Component-Specific Strategies

**Connectors:**
- Mechanical support (strain relief, mounting holes)
- Locking mechanisms for critical connections
- Gold plating for frequently mated connectors
- Conformal coating for harsh environments

**Power Supplies:**
- Input/output filtering
- Thermal management (vias, copper pours)
- Enable/disable control
- Power-good status outputs
- Soft-start circuits

**MCUs:**
- Decoupling: 100nF ceramic within 5mm of each power pin
- ESD protection on all external interfaces
- Watchdog timer implementation
- Brownout reset circuits
- Crystal layout best practices (short traces, ground guard)

**High-Speed Signals:**
- Controlled impedance traces
- Series termination resistors
- Ground planes for return current
- Minimize stub lengths
- Differential pairs for noise immunity

---

## Example Workflow

### Complete FMEA Process

1. **Design your circuit** in circuit-synth Python:

```python
from circuit_synth import Circuit, USB_C, LDO, MCU, Capacitor

with Circuit("ESP32_DevBoard") as circuit:
    usb = USB_C("J1", "USB_C_Receptacle")
    ldo = LDO("U1", "AMS1117-3.3", input_voltage="5V")
    mcu = MCU("U2", "ESP32-C6")

    # Power distribution
    usb["VBUS"] >> ldo["VIN"]
    ldo["VOUT"] >> mcu["VDD"]

    # Decoupling
    Capacitor("C1", "10uF", "0805") | (ldo["VIN"], ldo["GND"])
    Capacitor("C2", "10uF", "0805") | (ldo["VOUT"], ldo["GND"])
```

2. **Run FMEA analysis**:

```bash
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli ESP32_DevBoard.py -o FMEA_Report.pdf
```

3. **Review the report**:
   - Check critical/high-risk failures (RPN ≥ 125)
   - Note specific recommendations
   - Identify components needing protection

4. **Implement improvements**:

```python
from circuit_synth import Circuit, USB_C, LDO, MCU, Capacitor, TVS_Diode

with Circuit("ESP32_DevBoard_v2") as circuit:
    usb = USB_C("J1", "USB_C_Receptacle")

    # Add ESD protection (addresses RPN 288 "ESD damage" failure mode)
    tvs = TVS_Diode("D1", "USBLC6-2SC6", package="SOT-23-6")
    usb["VBUS"] >> tvs["IN"]

    ldo = LDO("U1", "AMS1117-3.3", input_voltage="5V")

    # Improved thermal management (addresses RPN 336 "thermal shutdown")
    ldo.add_thermal_vias(count=9, diameter="0.3mm")

    mcu = MCU("U2", "ESP32-C6")

    # Enhanced decoupling (addresses "power supply noise" failure mode)
    Capacitor("C1", "10uF", "0805") | (ldo["VIN"], ldo["GND"])
    Capacitor("C2", "10uF", "0805") | (ldo["VOUT"], ldo["GND"])
    Capacitor("C3", "100nF", "0402") | (mcu["VDD"], mcu["GND"])  # Close to MCU
```

5. **Re-run analysis** to verify improvements:

```bash
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli ESP32_DevBoard_v2.py -o FMEA_Report_v2.pdf
```

6. **Compare reports**:
   - Verify RPN reduction for addressed failure modes
   - Check for any new failure modes introduced
   - Ensure critical failures are mitigated

---

## Best Practices

### When to Run FMEA

- **Early design phase** - Identify issues before committing to schematic
- **After major changes** - Verify modifications don't introduce new risks
- **Before prototype** - Catch issues before manufacturing
- **Pre-production review** - Final validation before volume production
- **Post-failure analysis** - Understand field failures and prevent recurrence

### Interpreting Results

**Don't aim for zero risk** - Some low-RPN failures are acceptable and expected.

**Focus on actionable items:**
- RPN ≥ 300: Must fix before proceeding
- RPN 125-299: Should fix before production
- RPN 50-124: Consider fixes if low-cost
- RPN < 50: Monitor but generally acceptable

**Consider detection difficulty:**
- High detection (D = 8-10): Add test points, design for testability
- Moderate detection (D = 4-7): Implement automated test procedures
- Low detection (D = 1-3): Failure will be caught in testing

### Continuous Improvement

- **Update knowledge base** - Add failure modes from field experience
- **Track actual failures** - Compare predictions to reality
- **Refine ratings** - Adjust S/O/D based on real-world data
- **Document lessons learned** - Build institutional knowledge
- **Automate in CI/CD** - Run FMEA on every design iteration

---

## Troubleshooting

### Common Issues

**"No circuit files found"**
- Ensure you're pointing to a `.py` or `.json` circuit file
- Check that the file exists and has the correct extension

**"reportlab not installed"**
- Install PDF generation library: `uv pip install reportlab`

**"Component not recognized"**
- Unknown components get generic failure modes
- Check component symbol naming matches KiCad conventions
- Verify reference designators are standard (R, C, U, J, etc.)

**Empty or minimal report**
- Verify circuit file has components defined
- Check that circuit.serialize() or netlist generation works
- Try running with `-v` verbose flag for diagnostic info

**RPN values seem too high/low**
- Values are based on industry standards for general electronics
- Adjust for your environment using circuit context
- Customize failure mode database for your specific domain

---

## References

### Standards
- **AIAG-VDA FMEA Handbook** - Automotive industry standard
- **IPC-A-610** - Acceptability of Electronic Assemblies
- **MIL-STD-1629A** - FMEA procedures for military systems
- **SAE J1739** - Potential Failure Mode and Effects Analysis

### Reliability Models
- **Arrhenius Equation** - Temperature acceleration factor
- **Coffin-Manson Equation** - Thermal cycling fatigue
- **Black's Equation** - Electromigration in conductors
- **MIL-HDBK-217** - Reliability prediction of electronic equipment

### Further Reading
- NASA FMEA guidelines
- IEC 60812 - Analysis techniques for system reliability
- Circuit-synth documentation: https://circuit-synth.readthedocs.io

---

## Support

For questions or issues with FMEA analysis:
- GitHub Issues: https://github.com/circuit-synth/circuit-synth/issues
- Documentation: https://circuit-synth.readthedocs.io
- Email support: support@circuit-synth.dev

---

**Last Updated:** 2025-10-25
**Version:** 0.10.12
