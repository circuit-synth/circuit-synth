# Test 55: ERC Validation

**Priority:** Priority 2 (Nice-to-have - Real-world integration)

## Overview

Tests comprehensive ERC (Electrical Rule Check) workflow: creating circuits with intentional ERC violations, validating KiCad detects them, fixing violations in Python, and verifying clean ERC.

## Test Scenario

### Initial State: Circuit with ERC Violations
1. Create circuit with 3 intentional ERC violations:
   - **Pin conflict**: Two outputs driving same net (U1 output + U2 output → conflict)
   - **Undriven input**: Input pin not connected to any driver (U3 input floating)
   - **Unconnected power pin**: Power pin not connected to power net (U4 VCC floating)

2. Generate to KiCad

3. Run KiCad ERC via kicad-cli

4. Validate ERC reports expected errors:
   - Output-to-output conflict detected
   - Undriven input detected
   - Unconnected power pin detected

### Final State: Clean ERC
5. Fix all violations in Python:
   - Change U2 from output to input (resolves conflict)
   - Connect U3 input to valid driver
   - Connect U4 VCC to power net

6. Regenerate to KiCad

7. Run ERC again

8. Validate: ERC clean (0 errors)

## Validation Levels

- **Level 3 (Electrical)**: KiCad ERC integration via kicad-cli
- **Level 4 (Tool Integration)**: Before/after ERC comparison

## Real-World Use Cases

This workflow validates:
- **Design validation**: Catch electrical errors early in Python
- **ERC automation**: Programmatic ERC checking in CI/CD
- **Error detection**: Validate circuit-synth generates ERC-clean circuits
- **Iterative fixes**: Fix violations and verify corrections

## KiCad ERC Integration

Uses kicad-cli ERC functionality:
```bash
kicad-cli sch erc --output report.json --format json circuit.kicad_sch
```

ERC checks include:
- Pin conflicts (output-output, output-power source)
- Undriven inputs
- Unconnected power pins
- Missing passive connections
- Hierarchical label mismatches

## Test Files

- `circuit_with_erc_errors.py` - Python circuit with intentional ERC violations
- `test_55_erc.py` - Automated test validating ERC workflow

## Expected Behavior

### Initial ERC (with violations)
```json
{
  "violations": [
    {
      "severity": "error",
      "type": "pin_to_pin",
      "description": "Output connected to output",
      "sheet": "/"
    },
    {
      "severity": "error",
      "type": "input_not_driven",
      "description": "Input pin not driven by any output pins"
    },
    {
      "severity": "warning",
      "type": "pin_not_connected",
      "description": "Power pin not connected"
    }
  ],
  "error_count": 2,
  "warning_count": 1
}
```

### Final ERC (clean)
```json
{
  "violations": [],
  "error_count": 0,
  "warning_count": 0
}
```

## Implementation Notes

- Uses kicad-sch-api ERC module for parsing ERC reports
- Test may SKIP if kicad-cli ERC not available in CI environment
- Validates specific ERC error types and descriptions
- Tests both error detection and successful fixes
