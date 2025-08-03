# Python Code Generation from KiCad Still Needed

## Issue
After fixing `cs-init-pcb` to organize files properly, we still need to implement proper Python circuit-synth code generation from existing KiCad schematics.

## Current State
- ✅ `cs-init-pcb` now organizes KiCad files in `kicad/` directory
- ✅ **FIXED**: Now copies complete working circuit examples from `example_project/`
- ✅ **FIXED**: Creates functional `main.py` with all subcircuit files
- ❌ **Still Missing**: Automatic conversion of existing KiCad schematic to circuit-synth Python code

## What's Missing
1. **KiCad Schematic Parser**: Read `.kicad_sch` files and extract:
   - Components with symbols, footprints, values
   - Net connections between components
   - Component placement/arrangement information

2. **Circuit-Synth Code Generator**: Convert parsed data to:
   - `Component()` declarations with correct symbols/footprints
   - `Net()` declarations with proper naming
   - Component-to-net connections (`component[pin] += net`)
   - Proper `@circuit` decorator usage

3. **Multi-Sheet Support**: Handle hierarchical schematics with:
   - Sub-circuit definitions
   - Hierarchical net connections
   - Proper circuit composition

## Priority
**Medium** - `cs-init-pcb` now provides working examples, but true KiCad-to-circuit-synth conversion would be the ultimate solution.

## Possible Approaches
1. **Native Python Parser**: Parse KiCad S-expression format directly
2. **KiCad CLI Integration**: Use `kicad-cli` to export netlist, then parse
3. **Hybrid Approach**: Parse schematic for structure, netlist for connections

## Next Steps
1. Research KiCad file format documentation
2. Implement basic schematic parser for components and nets
3. Build circuit-synth code generator
4. Test with real KiCad projects
5. Integrate into `cs-init-pcb` workflow

## Impact When Fixed
Users could run `cs-init-pcb` on existing KiCad projects and immediately get circuit-synth Python code that matches their original schematic exactly, enabling perfect round-trip conversion.

## Current Workaround
Users get working ESP32-C6 examples and can manually adapt the circuit code to match their original schematic, which is much easier than starting from scratch.