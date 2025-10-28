# Test 52: Unicode Component Names

**Priority:** Priority 2 (Nice-to-have - Edge case)

## Test Scenario

Tests whether circuit-synth and KiCad can correctly handle Unicode characters in various circuit elements:

1. Create circuit with unicode in component references/values:
   - Component reference: R_π (R with pi symbol - Greek)
   - Component value: "1kΩ" (with Omega symbol - Greek)
   - Net name: "信号" (Chinese for "signal")
   - Text annotation: "温度センサー" (Japanese for "temperature sensor")

2. Generate to KiCad, validate:
   - Unicode preserved in references
   - Unicode preserved in values
   - Unicode preserved in net names
   - Unicode preserved in text
   - Files are valid UTF-8

3. Synchronize back, validate:
   - All unicode preserved through round-trip
   - No encoding errors or mojibake

## Validation Levels

- **Level 2**: Unicode text present in .kicad_sch (UTF-8 encoded)
- **Level 3**: Netlist contains unicode correctly

## Unicode Scripts Tested

- **Greek**: π (pi), Ω (omega)
- **Chinese**: 信号 (signal)
- **Japanese**: 温度センサー (temperature sensor)

## Expected Behavior

### If Unicode is Supported:
- All unicode characters preserved through generation and synchronization
- .kicad_sch files contain valid UTF-8 encoding
- Netlist contains unicode without corruption
- Round-trip maintains exact unicode strings

### If Unicode is Not Supported (XFAIL):
- May see encoding errors during generation
- May see mojibake (corrupted characters) in output
- Round-trip may lose unicode information
- KiCad may not display unicode correctly

## Key Requirements

- Test multiple unicode scripts (Greek, Japanese, Chinese)
- Validate UTF-8 encoding in .kicad_sch files
- Check for encoding errors or mojibake
- May XFAIL if KiCad or circuit-synth doesn't support unicode properly

## Notes

- KiCad 6+ generally supports UTF-8 encoding
- This test validates that circuit-synth preserves encoding correctly
- Different platforms (Windows/Linux/Mac) may have different unicode handling
- File system encoding may affect results
