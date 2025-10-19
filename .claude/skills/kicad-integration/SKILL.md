---
name: kicad-integration
description: Fast KiCad symbol and footprint lookup for circuit-synth components
allowed-tools: ["Bash", "Grep", "Glob", "Read"]
---

# KiCad Integration Skill

## When to Use This Skill

Invoke this skill when the user:
- Asks about KiCad symbols: "find symbol for...", "what symbol...", "symbol for resistor"
- Asks about footprints: "find footprint", "what footprint for...", "0603 footprint"
- Needs to validate components: "check if symbol exists", "validate Device:R"
- Mentions KiCad terms: "KiCad library", "symbol library", "footprint library"

## Capabilities

### Symbol Search
- Search KiCad symbol libraries by component type
- Find exact symbol names with library prefix
- Search across all standard KiCad libraries
- Return `Library:Symbol` format ready for circuit-synth

### Footprint Search
- Search footprint libraries by package type
- Find SMD and through-hole footprints
- Search by size (0603, 0805, LQFP, etc.)
- Return `Library:Footprint` format

### Validation
- Verify symbol exists in KiCad libraries
- Check footprint compatibility
- Validate library:name format

## Usage Examples

### Example 1: Find Symbol
**User:** "find the symbol for a resistor"

**Process:**
1. Search KiCad libraries for "resistor" or common component types
2. Use Grep to search .kicad_sym files
3. Return exact symbol name

**Output:**
```
Found resistor symbol:
- Device:R (basic resistor)
- Device:R_Small (compact version)
- Device:R_US (US style)

Recommended: Device:R
```

### Example 2: Find Footprint
**User:** "what footprint for 0603 resistor"

**Process:**
1. Search footprint libraries for "0603" and "resistor"
2. Look in Resistor_SMD library
3. Return matching footprints

**Output:**
```
Found 0603 footprints:
- Resistor_SMD:R_0603_1608Metric
- Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder

Recommended: Resistor_SMD:R_0603_1608Metric
```

### Example 3: Validate Component
**User:** "check if MCU_ST_STM32F4:STM32F411CEUx exists"

**Process:**
1. Parse library and symbol name
2. Search for MCU_ST_STM32F4 library
3. Verify STM32F411CEUx symbol exists

**Output:**
```
✓ Symbol exists: MCU_ST_STM32F4:STM32F411CEUx
Package: LQFP-48
Recommended footprint: Package_QFP:LQFP-48_7x7mm_P0.5mm
```

## KiCad Library Locations

Search these paths in order:
1. `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/` (macOS)
2. `/usr/share/kicad/symbols/` (Linux)
3. `~/kicad/symbols/` (custom user libraries)

Footprint paths:
1. `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/` (macOS)
2. `/usr/share/kicad/footprints/` (Linux)
3. `~/kicad/footprints/` (custom user libraries)

## Search Strategy

### Symbol Search
```bash
# Find symbol files
find /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols -name "*.kicad_sym"

# Search for component in symbol files
grep -l "STM32F411" /path/to/symbols/*.kicad_sym

# Extract exact symbol name
grep "symbol.*STM32F411" file.kicad_sym
```

### Footprint Search
```bash
# Find footprint directories
find /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints -type d -name "*Resistor*"

# Search for specific footprint
find /path/to/footprints -name "*0603*.kicad_mod"
```

## Common Symbol Libraries

- **Device** - Basic components (R, C, L, LED, diode)
- **Connector** - Headers, USB, barrel jacks
- **Connector_Generic** - Generic connectors
- **MCU_ST_STM32F4** - STM32F4 family microcontrollers
- **MCU_Espressif** - ESP32 modules
- **Regulator_Linear** - LDOs and linear regulators
- **Regulator_Switching** - Buck/boost converters
- **RF_Module** - Wireless modules
- **power** - Power symbols (GND, VCC, +5V)

## Common Footprint Libraries

- **Resistor_SMD** - SMD resistors
- **Capacitor_SMD** - SMD capacitors
- **Package_QFP** - QFP packages (LQFP, TQFP)
- **Package_SO** - SOIC, SSOP packages
- **Package_TO_SOT_SMD** - SOT-23, SOT-223
- **Connector_USB** - USB connectors
- **LED_SMD** - SMD LEDs

## Performance

- **Symbol Search**: <3 seconds
- **Footprint Search**: <3 seconds
- **Validation**: <1 second

## Best Practices

### Return Format
Always return in circuit-synth compatible format:
- Symbol: `Library:SymbolName`
- Footprint: `Library:FootprintName`

### Multiple Results
If multiple matches, prioritize:
1. Most commonly used variant
2. Standard packages (0603, 0805 for passives)
3. Hand-solder friendly options when available

### Error Handling
If symbol/footprint not found:
1. Suggest similar alternatives
2. Check spelling/capitalization
3. Recommend searching KiCad website

## Limitations

- Only searches standard KiCad libraries (not custom user libraries unless in standard locations)
- Symbol/footprint must exist in installed KiCad version
- Requires KiCad to be installed on the system

## Related Tools

Uses existing circuit-synth commands:
- `/find-symbol` - Symbol search command
- `/find-footprint` - Footprint search command

This skill provides the same functionality but automatically invoked by Claude.
