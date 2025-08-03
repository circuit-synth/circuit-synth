---
allowed-tools: Bash(find*), Bash(grep*), Bash(ls*), Bash(xargs*), Grep, Glob
description: Search KiCad symbol libraries for component symbols
argument-hint: [search term]
---

Search KiCad symbol libraries for component symbols matching: **$ARGUMENTS**

**Step 1: Find symbol library files containing the search term**
```bash
# Search for library files that contain the search term
find /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols -name "*.kicad_sym" | xargs grep -l "$ARGUMENTS"
```

**Step 2: Extract specific symbol names from relevant libraries**
```bash
# For each matching library, extract symbol names
grep -o 'symbol "[^"]*$ARGUMENTS[^"]*"' /path/to/matching/library.kicad_sym | head -10
```

**Search locations (macOS):**
- `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/`

**Search locations (Linux):**
- `/usr/share/kicad/symbols/`
- `/usr/local/share/kicad/symbols/`

**Usage Examples:**
- `/find-symbol STM32F4` - Find STM32F4 microcontroller symbols
- `/find-symbol ESP32` - Find ESP32 module symbols  
- `/find-symbol LM358` - Find operational amplifier symbols
- `/find-symbol Capacitor` - Find capacitor symbols

**Output Format:**
The command will show both the library file and the symbol names:
```
Library: MCU_ST_STM32F4.kicad_sym
Symbols:
- STM32F407VETx
- STM32F407VGTx  
- STM32F401CCFx
```

**For circuit-synth use:**
```python
# Use format: LibraryName:SymbolName (without .kicad_sym extension)
mcu = Component(
    symbol="MCU_ST_STM32F4:STM32F407VETx",
    ref="U",
    footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm"
)
```