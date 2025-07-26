# KiCad CLI Integration for PCB API

This module provides a comprehensive interface to KiCad's command-line tools, enabling automated PCB validation, manufacturing file generation, and more.

## Features

### 1. Automatic KiCad CLI Detection
The module automatically detects the `kicad-cli` executable on different platforms:
- **macOS**: Searches in `/Applications/KiCad/` and user Applications
- **Windows**: Searches in Program Files directories
- **Linux**: Searches in standard binary locations

### 2. Design Rule Check (DRC)
Run comprehensive design rule checks on PCB files:
```python
from circuit_synth.kicad_api.pcb import PCBBoard

pcb = PCBBoard("my_board.kicad_pcb")
result = pcb.run_drc()

print(f"DRC Success: {result.success}")
print(f"Violations: {len(result.violations)}")
print(f"Warnings: {len(result.warnings)}")
print(f"Unconnected: {len(result.unconnected_items)}")
```

### 3. Basic Rule Checking (No KiCad Required)
Quick validation without KiCad CLI:
```python
violations = pcb.check_basic_rules()
# Checks for:
# - Missing board outline
# - Overlapping components
# - Unconnected pads
# - Invalid track widths
```

### 4. Manufacturing File Export
Export all necessary files for PCB manufacturing:

#### Gerber Files
```python
gerber_files = pcb.export_gerbers("output/gerbers/")
# Exports: F.Cu, B.Cu, F.Mask, B.Mask, F.SilkS, B.SilkS, Edge.Cuts, etc.
```

#### Drill Files
```python
plated, non_plated = pcb.export_drill("output/drill/")
# Generates: PTH.drl (plated holes), NPTH.drl (non-plated holes)
```

#### Pick and Place
```python
pnp_file = pcb.export_pick_and_place("output/positions.csv")
# For automated assembly
```

## Low-Level CLI Interface

For direct access to any KiCad CLI command:

```python
from circuit_synth.kicad_api.pcb import get_kicad_cli

cli = get_kicad_cli()

# Run any command
result = cli.run_command(["pcb", "export", "svg", "board.kicad_pcb"])

# Get version
version = cli.get_version()
```

## Custom DRC Rules

KiCad CLI uses DRC rules embedded in the PCB file. Custom rules must be defined in:

1. **PCB Setup Section**: Rules are stored in the PCB file itself
2. **Project .kicad_dru File**: Project-specific rule files
3. **KiCad GUI**: Use the GUI to configure rules that will be saved with the PCB

### Example: Adding Rules Programmatically
```python
# Future enhancement - add rules to PCB setup section
# Currently, rules must be configured in KiCad GUI
```

## Error Handling

The module provides specific exception types:

```python
from circuit_synth.kicad_api.pcb import KiCadCLIError, KiCadCLINotFoundError

try:
    result = pcb.run_drc()
except KiCadCLINotFoundError:
    print("KiCad is not installed")
except KiCadCLIError as e:
    print(f"Command failed: {e}")
    print(f"Return code: {e.return_code}")
    print(f"Error output: {e.stderr}")
```

## Platform-Specific Notes

### macOS
- KiCad CLI is typically at: `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`
- May require full disk access permissions

### Windows
- Located in: `C:\Program Files\KiCad\<version>\bin\kicad-cli.exe`
- Add to PATH for easier access

### Linux
- Usually in: `/usr/bin/kicad-cli` or `/usr/local/bin/kicad-cli`
- Install via package manager or AppImage

## Examples

See the `examples/` directory for complete examples:
- `test_kicad_cli.py` - Comprehensive test of all CLI features
- `drc_example.py` - Real-world DRC example with intentional issues

## Requirements

- KiCad 7.0 or later (for CLI support)
- Python 3.7+
- No additional Python dependencies beyond the base PCB API

## Future Enhancements

1. **Custom DRC Rule Injection**: Programmatically add rules to PCB files
2. **3D Export**: Export 3D models via CLI
3. **Netlist Import**: Import netlists from schematics
4. **Batch Processing**: Process multiple PCBs efficiently
5. **CI/CD Integration**: GitHub Actions for automated DRC