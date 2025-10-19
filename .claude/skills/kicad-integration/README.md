# KiCad Integration Skill

Fast symbol and footprint lookup for circuit-synth components.

## Quick Start

Just ask naturally:
- "find the symbol for a resistor"
- "what footprint for 0603 capacitor"
- "does Device:R exist in KiCad?"

Claude will automatically invoke this skill and search KiCad libraries.

## What This Skill Does

**Symbol Search:**
- Finds KiCad symbols by component type
- Returns exact `Library:Symbol` format
- Searches all standard KiCad libraries

**Footprint Search:**
- Finds footprints by package type
- Returns exact `Library:Footprint` format
- Prioritizes common packages (0603, 0805, LQFP, etc.)

**Validation:**
- Verifies symbols/footprints exist
- Checks library paths
- Suggests alternatives if not found

## Example Usage

### Finding a Symbol
```
You: "find resistor symbol"

Claude (via skill):
Found resistor symbol:
- Device:R (basic resistor)
- Device:R_Small (compact version)

Recommended: Device:R
```

### Finding a Footprint
```
You: "0805 resistor footprint"

Claude (via skill):
Found footprint:
Resistor_SMD:R_0805_2012Metric

Perfect for 0805 size SMD resistors.
```

### Validating a Component
```
You: "check if MCU_ST_STM32F4:STM32F411CEUx exists"

Claude (via skill):
✓ Symbol exists: MCU_ST_STM32F4:STM32F411CEUx
Recommended footprint: Package_QFP:LQFP-48_7x7mm_P0.5mm
```

## Common Symbols

| Component | Symbol |
|-----------|--------|
| Resistor | `Device:R` |
| Capacitor | `Device:C` |
| LED | `Device:LED` |
| USB Micro | `Connector:USB_B_Micro` |
| STM32F411 | `MCU_ST_STM32F4:STM32F411CEUx` |
| ESP32 | `RF_Module:ESP32-S3-MINI-1` |
| 3.3V Regulator | `Regulator_Linear:AMS1117-3.3` |

## Common Footprints

| Package | Footprint |
|---------|-----------|
| 0603 Resistor | `Resistor_SMD:R_0603_1608Metric` |
| 0805 Capacitor | `Capacitor_SMD:C_0805_2012Metric` |
| LQFP-48 | `Package_QFP:LQFP-48_7x7mm_P0.5mm` |
| SOT-223 | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` |

## Performance

- Symbol search: <3 seconds
- Footprint search: <3 seconds
- Validation: <1 second

Much faster than agents (60+ seconds).

## Invocation

This skill is **automatically invoked** when you mention:
- "symbol", "footprint", "KiCad"
- "find", "search", "validate"
- Component types: "resistor", "capacitor", "STM32", etc.

No need to explicitly call it - just ask naturally!

## Limitations

- Requires KiCad installed on system
- Searches standard libraries only
- macOS and Linux paths (Windows support TBD)

## Related

- See `SKILL.md` for complete technical details
- Uses existing `/find-symbol` and `/find-footprint` commands
- Complements `component-search` skill (for JLCPCB sourcing)
