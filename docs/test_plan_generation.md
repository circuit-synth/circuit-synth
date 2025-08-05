# Test Plan Generation

Circuit-synth now includes a specialized Test Plan Creation Agent that helps generate comprehensive test procedures for your circuit designs. This ensures thorough validation before manufacturing.

## Overview

The test-plan-creator agent analyzes your circuit design and generates:
- Functional test procedures
- Performance validation tests
- Safety compliance testing
- Manufacturing test procedures
- Equipment recommendations
- Pass/fail criteria

## Quick Start

### Using with Claude Code

```bash
# Generate a test plan for your circuit
Task(subagent_type="test-plan-creator", description="Generate test plan", prompt="Create a comprehensive test plan for my ESP32 development board circuit")
```

### Using CLI Commands

```bash
# Generate a basic test plan
create-test-plan my_circuit.py

# Include performance and safety tests
create-test-plan ESP32_board.py --include-performance --include-safety

# Export to JSON format
create-test-plan circuit.py --format json --output test_plan.json

# Generate manufacturing tests
generate-manufacturing-tests board.py --ict --boundary-scan
```

## Test Plan Categories

### 1. Functional Testing
- Power-on sequence verification
- Reset and initialization testing
- GPIO functionality validation
- Communication protocol testing
- Basic operation verification

### 2. Performance Testing
- Power consumption measurement
- Frequency response characterization
- Timing analysis
- Load regulation testing
- Temperature coefficient testing

### 3. Safety and Compliance
- ESD protection verification
- Overvoltage/overcurrent protection testing
- Thermal shutdown validation
- EMI/EMC pre-compliance
- Isolation barrier testing

### 4. Manufacturing Testing
- In-circuit testing (ICT) procedures
- Boundary scan/JTAG testing
- Functional test procedures
- Burn-in test specifications
- Visual inspection checklists

## Example Usage

### Basic Test Plan Generation

```python
from circuit_synth import Component, Circuit, Net

@circuit(name="USB_Power_Supply")
def create_power_supply():
    """5V USB power supply with protection"""
    # ... circuit implementation ...
    pass

# Generate test plan using the agent
prompt = """
Analyze the USB_Power_Supply circuit and generate:
1. Functional tests for power delivery
2. Protection circuit validation
3. Manufacturing test procedures
"""

# Use with Claude Code:
# Task(subagent_type="test-plan-creator", prompt=prompt)
```

### Advanced Manufacturing Tests

```bash
# Generate comprehensive manufacturing tests
generate-manufacturing-tests complex_board.py --ict --boundary-scan --fixture

# This generates:
# - ICT test point mapping
# - Boundary scan chain configuration
# - Test fixture specifications
# - Programming procedures
```

## Output Formats

### Markdown (Default)
Human-readable test procedures with:
- Clear section headers
- Step-by-step instructions
- Tables for specifications
- Checklists for validation

### JSON
Structured data format for:
- Test automation integration
- Database storage
- API consumption
- Programmatic processing

### CSV
Spreadsheet format for:
- Test parameter matrices
- Measurement limits
- Results recording
- Excel compatibility

### Checklist
Simple format for:
- Quick reference
- Pass/fail marking
- Production floor use
- Printable forms

## Test Equipment Recommendations

The agent provides equipment specifications based on your circuit:

- **Voltage Measurements**: DMM accuracy requirements
- **Frequency Analysis**: Oscilloscope bandwidth needs
- **Current Testing**: Shunt/probe specifications
- **Safety Testing**: ESD gun, hi-pot tester requirements

## Integration with Circuit-Synth Workflow

1. **Design Phase**: Create your circuit in Python
2. **Validation Phase**: Generate test plan with the agent
3. **Simulation Phase**: Use simulation-expert agent to validate
4. **Manufacturing Phase**: Generate production tests
5. **Documentation Phase**: Export test procedures

## Best Practices

1. **Generate Early**: Create test plans during design phase
2. **Include All Categories**: Don't skip safety or manufacturing tests
3. **Define Clear Criteria**: Specify exact pass/fail thresholds
4. **Consider Production**: Design for testability from the start
5. **Update Regularly**: Revise test plans as design evolves

## Troubleshooting

### No Test Points Identified
- Ensure nets are properly named in your circuit
- Add test point components explicitly
- Use descriptive net names (VCC, GND, SIGNAL_OUT)

### Missing Equipment Specs
- Provide voltage/current ranges in circuit
- Specify frequency requirements
- Include component tolerances

### Incomplete Procedures
- Add more circuit documentation
- Include component specifications
- Provide functional descriptions

## API Reference

### Agent Tools

```python
# Analyze circuit for test points
analyze_circuit(circuit_file, analysis_type="test_points")

# Generate specific test procedure
generate_test_procedure(test_type="functional", circuit_info={})

# Get equipment recommendations
recommend_equipment(measurement_type="voltage", specifications={})

# Create validation checklist
create_validation_checklist(circuit_type="power", requirements=[])

# Export test plan
export_test_plan(format="markdown", test_procedures=[])
```

### CLI Commands

```bash
# Main test plan command
create-test-plan [OPTIONS] [CIRCUIT_FILE]
  --include-performance
  --include-safety
  --format [markdown|json|csv|checklist]
  --output PATH

# Manufacturing test command  
generate-manufacturing-tests [OPTIONS] [CIRCUIT_FILE]
  --ict
  --boundary-scan
  --fixture
```

## Contributing

To improve the test plan agent:
1. Add new test categories in `test_plan_agent.py`
2. Extend equipment database
3. Add industry-specific test templates
4. Improve circuit analysis algorithms

See the [Contributor Guide](../Contributors/README.md) for details.