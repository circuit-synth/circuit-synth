# Test 54: DRC Validation Integration

**Priority:** Priority 2 (Nice-to-have - Real-world integration)

## Overview

This test validates integration with KiCad's Design Rule Check (DRC) / Electrical Rule Check (ERC) system via `kicad-cli`. It demonstrates that circuit-synth can:

1. Generate circuits with **intentional ERC violations**
2. Run KiCad ERC via `kicad-cli sch erc`
3. Parse and validate ERC reports
4. Fix violations in Python code
5. Regenerate and verify violations are resolved

**Why This Matters:** In real-world PCB design, catching electrical errors early (unconnected pins, power not driven, etc.) prevents costly board respins. This test validates that circuit-synth integrates with KiCad's validation tools.

## Test Scenario

### Phase 1: Generate Circuit with Violations
Create schematic with **2 intentional ERC violations**:
1. **Unconnected input pin** - floating input on op-amp
2. **Missing footprint** - component without PCB footprint assigned (warning)

### Phase 2: Run ERC and Validate Violations
- Use `kicad-cli sch erc` to run electrical rule check
- Parse JSON output
- Verify **expected violations are detected**
- Validate specific error messages

### Phase 3: Fix Violations in Python
Modify Python circuit code to fix all violations:
1. **Connect floating input** - add net connection to op-amp input
2. **Add footprint** - assign PCB footprint to component

### Phase 4: Regenerate and Verify Clean
- Regenerate KiCad schematic from fixed Python code
- Run ERC again
- Validate: **0 errors** (clean ERC)

## Validation Levels

### Level 1: File Generation
- Schematic file generated successfully
- ERC report file created

### Level 2: ERC Integration
- `kicad-cli sch erc` executes successfully
- JSON output parseable
- Violation counts match expectations

### Level 3: Electrical Validation
- Before: 3 specific violations detected
- After: 0 violations (clean ERC)
- Violations correctly identify problematic pins/nets

## Test Structure

```
tests/bidirectional/54_drc_validation/
├── README.md                           # This file
├── circuit_with_violations.py          # Python circuit with intentional ERC violations
└── test_54_drc.py                      # Automated test runner
```

## Usage

### Run Test
```bash
# Run test (will SKIP if kicad-cli ERC not available)
uv run pytest tests/bidirectional/54_drc_validation/test_54_drc.py -v

# Keep output for debugging
uv run pytest tests/bidirectional/54_drc_validation/test_54_drc.py -v --keep-output
```

### Manual Testing
```bash
cd tests/bidirectional/54_drc_validation

# Generate circuit with violations
uv run circuit_with_violations.py

# Run ERC manually
kicad-cli sch erc \
  --output circuit_with_violations/circuit_with_violations_erc.json \
  --format json \
  --severity-all \
  circuit_with_violations/circuit_with_violations.kicad_sch

# View ERC report
cat circuit_with_violations/circuit_with_violations_erc.json
```

## Expected Violations (Before Fix)

### 1. Unconnected Input Pin (Error)
```
Type: input_pin_not_driven / pin_not_connected
Severity: error
Description: Pin 3 (non-inverting input) of U1 is not connected
```

### 2. Missing Footprint (Warning)
```
Type: missing_footprint
Severity: warning
Description: Symbol R1 has no footprint assigned
```

Note: Power pin violations may also appear depending on KiCad version and ERC settings.

## CI/CD Considerations

- **May skip in CI** if `kicad-cli` not available
- Uses `pytest.mark.skipif` to check for `kicad-cli` availability
- Provides informative skip message
- Can be run locally where KiCad is installed

## Real-World Application

This test pattern is useful for:
1. **Pre-release validation** - catch electrical errors before committing
2. **Automated design review** - integrate ERC into CI/CD
3. **Design rule enforcement** - ensure all circuits meet ERC standards
4. **Teaching tool** - demonstrate common electrical errors and fixes

## Implementation Details

### ERC Command Used
```bash
kicad-cli sch erc \
  --output <output.json> \
  --format json \
  --severity-all \
  <input.kicad_sch>
```

### JSON Report Structure
```json
{
  "coordinate_units": "mm",
  "source": "circuit.kicad_sch",
  "violations": [
    {
      "type": "unconnected_pin",
      "severity": "error",
      "description": "Pin not connected",
      "items": [...]
    }
  ]
}
```

## Test Success Criteria

- ✅ Circuit with violations generates successfully
- ✅ ERC detects at least 1 violation (unconnected pin or missing footprint)
- ✅ ERC report JSON is parseable
- ✅ Specific violation types identified correctly
- ✅ Fixed circuit generates successfully
- ✅ Fixed circuit has fewer violations than original (ideally 0)
- ✅ Test skips gracefully if `kicad-cli` unavailable

## Known Limitations

1. **ERC availability** - Requires KiCad 7.0+ with `kicad-cli` ERC support
2. **Platform differences** - ERC rules may vary slightly across KiCad versions
3. **Violation specificity** - Exact error messages depend on KiCad version
4. **PCB DRC not tested** - This test focuses on schematic ERC only (PCB DRC would require `.kicad_pcb` file)

## Related Tests

- **31_isolated_component** - Tests unconnected components (related to unconnected pin violations)
- **30_component_missing_footprint** - Tests missing footprint handling
- **16_add_power_symbol** - Tests power symbol connections (related to power pin violations)

## Future Enhancements

1. **PCB DRC integration** - Test PCB-level design rules (trace width, clearance, etc.)
2. **Custom ERC rules** - Test user-defined electrical rules
3. **Batch ERC** - Test ERC on hierarchical designs with multiple sheets
4. **ERC fix suggestions** - Auto-generate Python fixes for common ERC violations
