# FMEA (Failure Mode and Effects Analysis) Guide

## Overview

Circuit-Synth's FMEA module provides comprehensive failure analysis for electronic circuit designs, helping identify potential failure modes, assess risks, and recommend mitigation strategies. The system uses a knowledge base of over 20 YAML files containing physics-based failure models and industry standards.

## Features

- **Comprehensive Knowledge Base**: 20+ YAML files covering component failures, environmental stress, and manufacturing defects
- **Physics-Based Models**: Arrhenius, Coffin-Manson, Black's equation for accurate predictions
- **IPC Class 3 Compliance**: Analysis aligned with high-reliability assembly standards
- **Detailed PDF Reports**: 50+ page reports with 19 sections of analysis
- **300+ Failure Modes**: Analyzes hundreds of potential failure modes per circuit

## Quick Start

### Basic Usage

```python
from circuit_synth.quality_assurance import UniversalFMEAAnalyzer, FMEAReportGenerator

# Initialize analyzer
analyzer = UniversalFMEAAnalyzer()

# Analyze a circuit file
circuit_context, components = analyzer.analyze_circuit_file("my_circuit.py")

# Generate failure modes
failure_modes = []
for component in components:
    modes = analyzer.analyze_component(component, circuit_context)
    failure_modes.extend(modes)

# Generate PDF report
generator = FMEAReportGenerator("My Circuit")
report_path = generator.generate_fmea_report(
    circuit_data={"components": components},
    failure_modes=failure_modes
)
```

### Enhanced Analysis with Knowledge Base

```python
from circuit_synth.quality_assurance import EnhancedFMEAAnalyzer
from circuit_synth.quality_assurance import ComprehensiveFMEAReportGenerator

# Use enhanced analyzer with full knowledge base
analyzer = EnhancedFMEAAnalyzer()

# Set circuit context for better analysis
circuit_context = {
    'environment': 'industrial',  # or 'consumer', 'automotive', 'aerospace'
    'production_volume': 'high',  # or 'low', 'medium', 'prototype'
    'safety_critical': True,      # Affects severity ratings
    'operating_temperature': '-20 to +85C',
    'expected_lifetime': '15 years'
}

# Analyze components
all_failure_modes = []
for component in components:
    failure_modes = analyzer.analyze_component(component, circuit_context)
    all_failure_modes.extend(failure_modes)

# Generate comprehensive 50+ page report
generator = ComprehensiveFMEAReportGenerator(
    project_name="Industrial Controller",
    author="Engineering Team"
)

analysis_results = {
    'circuit_data': circuit_data,
    'failure_modes': all_failure_modes,
    'circuit_context': circuit_context,
    'components': components
}

report_path = generator.generate_comprehensive_report(
    analysis_results=analysis_results,
    output_path="Comprehensive_FMEA_Report.pdf"
)
```

## Command Line Usage

### Using the FMEA CLI Tool

```bash
# Analyze a circuit file
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py

# Specify output path
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py -o custom_report.pdf

# Set custom RPN threshold for high-risk items
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py --threshold 150

# Show more top risks in console output
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py --top 20
```

### Using the cs-new-project Agent

```bash
# The FMEA agent is automatically included in new projects
cs-new-project my-project

# The agent will be available for quality analysis
# Use it through the agent interface for circuit review
```

## Knowledge Base Structure

The FMEA knowledge base is organized into categories:

```
knowledge_base/fmea/
├── failure_modes/
│   ├── component_specific/
│   │   ├── capacitors.yaml        # Ceramic, electrolytic, tantalum failures
│   │   ├── resistors.yaml         # Thick/thin film, power resistor failures
│   │   ├── connectors.yaml        # USB-C, headers, power jack failures
│   │   ├── inductors.yaml         # Core saturation, thermal failures
│   │   ├── integrated_circuits.yaml # Silicon and package level failures
│   │   └── crystals_oscillators.yaml # Frequency drift, aging
│   ├── environmental/
│   │   ├── thermal.yaml           # Temperature cycling, thermal shock
│   │   ├── mechanical.yaml        # Vibration, shock, flexure
│   │   └── electrical.yaml        # ESD, EMI, overvoltage
│   ├── manufacturing/
│   │   └── solder_defects.yaml    # Assembly and soldering issues
│   ├── pcb_specific/
│   │   └── substrate_failures.yaml # Trace, via, laminate failures
│   └── assembly_process/
│       └── advanced_assembly_defects.yaml # BGA, Class 3 requirements
└── standards/
    └── industry_standards.yaml    # IPC, JEDEC, MIL-STD references
```

## RPN (Risk Priority Number) Calculation

RPN = Severity (S) × Occurrence (O) × Detection (D)

- **Severity (1-10)**: Impact of failure on system
- **Occurrence (1-10)**: Likelihood of failure
- **Detection (1-10)**: Difficulty of detecting failure

### Risk Categories

| Risk Level | RPN Range | Action Required |
|------------|-----------|-----------------|
| Critical | ≥ 300 | Immediate design change required |
| High | 125-299 | Action before production |
| Medium | 50-124 | Monitor and improve if feasible |
| Low | < 50 | Acceptable risk level |

## Report Sections

The comprehensive FMEA report includes:

1. **Executive Summary** - Key findings and critical issues
2. **Introduction and Scope** - Analysis objectives and boundaries
3. **FMEA Methodology** - Standards and calculation methods
4. **System Architecture Analysis** - Functional blocks and interfaces
5. **Component Criticality Analysis** - Single points of failure
6. **Detailed Failure Mode Analysis** - 15-20 pages of failure modes
7. **Environmental Stress Analysis** - Thermal and mechanical stress
8. **Manufacturing and Assembly Analysis** - Process defects
9. **Risk Assessment Matrix** - Visual risk distribution
10. **Physics of Failure Analysis** - Mathematical models
11. **Reliability Predictions** - MTBF calculations
12. **Mitigation Strategies** - Design improvements
13. **Testing and Validation Plan** - Test requirements
14. **Compliance and Standards** - Regulatory compliance
15. **Recommendations** - Priority action items
16. **Appendices** - Complete failure mode database

## Component Type Detection

The analyzer automatically detects component types from:

- **Symbol names**: e.g., "Device:R" → Resistor
- **Reference designators**: e.g., "U1" → IC, "C1" → Capacitor
- **Footprints**: e.g., "BGA" → Ball Grid Array package
- **Values**: e.g., "10uF" → Electrolytic capacitor

## Environmental Contexts

### Consumer Electronics
- Operating: 0-70°C
- Lower stress factors
- Standard detection levels

### Industrial
- Operating: -20 to +85°C
- Higher occurrence rates
- Enhanced detection requirements

### Automotive
- Operating: -40 to +125°C
- Increased severity and occurrence
- Strict quality requirements

### Aerospace/Military
- Operating: -55 to +125°C
- Maximum severity ratings
- Zero-defect requirements

## Physics Models

### Arrhenius Model (Temperature Acceleration)
```
AF = exp(Ea/k × (1/Tu - 1/Ts))
Ea = Activation energy (0.7eV typical)
```

### Coffin-Manson Model (Thermal Cycling)
```
Nf = A × (ΔT)^-n
n = 2.0-2.5 for solder joints
```

### Black's Equation (Electromigration)
```
MTTF = A × J^-n × exp(Ea/kT)
J = Current density
```

## Best Practices

1. **Set Appropriate Context**: Always specify environment and criticality
2. **Review Critical Failures**: Focus on RPN ≥ 300 items first
3. **Update Knowledge Base**: Add new failure modes as discovered
4. **Validate Mitigations**: Test recommended improvements
5. **Regular Updates**: Re-run FMEA after design changes

## API Reference

### UniversalFMEAAnalyzer

```python
analyzer = UniversalFMEAAnalyzer()

# Analyze circuit file
circuit_context, components = analyzer.analyze_circuit_file(filepath)

# Analyze individual component
failure_modes = analyzer.analyze_component(component_info, circuit_context)

# Identify component type
component_type = analyzer.identify_component_type(component_info)
```

### EnhancedFMEAAnalyzer

```python
analyzer = EnhancedFMEAAnalyzer()

# Includes all UniversalFMEAAnalyzer methods plus:
# - Automatic knowledge base loading
# - Context-aware modifiers
# - Physics-based predictions
```

### FMEAReportGenerator

```python
generator = FMEAReportGenerator(project_name, author)

# Generate standard report (8-10 pages)
report_path = generator.generate_fmea_report(
    circuit_data=circuit_data,
    failure_modes=failure_modes,
    output_path="report.pdf"
)
```

### ComprehensiveFMEAReportGenerator

```python
generator = ComprehensiveFMEAReportGenerator(project_name, author)

# Generate comprehensive report (50+ pages)
report_path = generator.generate_comprehensive_report(
    analysis_results=analysis_results,
    output_path="comprehensive_report.pdf"
)
```

## Troubleshooting

### No Failure Modes Detected
- Verify component information includes 'symbol' or 'type' fields
- Check that circuit file is properly formatted
- Ensure knowledge base files are present in knowledge_base/fmea/

### Report Generation Fails
- Install reportlab: `uv pip install reportlab`
- Check write permissions for output directory
- Verify all required fields in analysis_results

### Knowledge Base Not Loading
- Check knowledge_base/fmea/ directory exists
- Verify YAML files are properly formatted
- Look for error messages during analyzer initialization

## Examples

See `examples/quality_assurance/` for complete examples:
- `basic_fmea_analysis.py` - Simple circuit analysis
- `comprehensive_fmea_report.py` - Full report generation
- `custom_knowledge_base.py` - Adding custom failure modes

## Contributing

To add new failure modes to the knowledge base:

1. Create or edit YAML file in appropriate category
2. Follow existing structure for consistency
3. Include physics models where applicable
4. Add test cases for new failure modes
5. Submit PR with description of additions

## References

- SAE J1739: FMEA Standard
- IPC-A-610: Acceptability of Electronic Assemblies
- MIL-STD-883: Test Method Standard for Microcircuits
- JEDEC Standards: Component Qualification
- IPC-7095: BGA Design and Assembly Process Implementation