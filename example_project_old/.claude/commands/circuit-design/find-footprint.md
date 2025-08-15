---
allowed-tools: Bash(find*), Bash(grep*), Bash(ls*), Grep, Glob
description: Search KiCad footprint libraries for component footprints
argument-hint: [search term]
---

Search KiCad footprint libraries for component footprints matching: **$ARGUMENTS**

**Step 1: Find footprint libraries (.pretty directories)**
```bash
# Search for footprint library directories
find /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints -name "*.pretty" | grep -i "$ARGUMENTS"
```

**Step 2: Search within specific libraries for footprint files**
```bash
# Search for .kicad_mod files containing the search term
find /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints -name "*$ARGUMENTS*.kicad_mod"
```

**Step 3: Search within library directories**
```bash
# List footprints in specific libraries (example: Package_QFP.pretty)
ls /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_QFP.pretty/ | grep -i "$ARGUMENTS"
```

**Search locations (macOS):**
- `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/`

**Search locations (Linux):**
- `/usr/share/kicad/footprints/`
- `/usr/local/share/kicad/footprints/`

**Usage Examples:**
- `/find-footprint LQFP` - Find LQFP package footprints
- `/find-footprint 0603` - Find 0603 passive component footprints
- `/find-footprint QFN` - Find QFN package footprints
- `/find-footprint SOT23` - Find SOT-23 footprints

**Output Format:**
The command will show library names and footprint files:
```
Library: Package_QFP.pretty
Footprints:
- LQFP-100_14x14mm_P0.5mm.kicad_mod
- LQFP-64_10x10mm_P0.5mm.kicad_mod
- LQFP-48_7x7mm_P0.5mm.kicad_mod
```

**For circuit-synth use:**
```python
# Use format: LibraryName:FootprintName (without .pretty and .kicad_mod extensions)
mcu = Component(
    symbol="MCU_ST_STM32F4:STM32F407VETx",
    ref="U", 
    footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm"
)
```