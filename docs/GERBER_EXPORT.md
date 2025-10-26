# Gerber Manufacturing Files Export Guide

## Overview

Circuit-synth provides a complete manufacturing export solution with a single API call. Generate all necessary PCB manufacturing files (Gerbers, drill files, and optional design files) directly from your circuit definition.

## Quick Start

```python
from circuit_synth import circuit, Component

@circuit(name="MyBoard")
def my_board():
    r1 = Component(symbol="Device:R", value="10k", ref="R1")
    r2 = Component(symbol="Device:R", value="1k", ref="R2")
    c1 = Component(symbol="Device:C", value="100nF", ref="C1")
    return locals()

circuit = my_board()

# Generate all manufacturing files in one line
result = circuit.generate_gerbers(project_name="my_board")
print(f"Manufacturing files ready: {result['output_dir']}")
```

This generates all necessary files in `my_board/gerbers/`:
- Copper layers (F.Cu, B.Cu)
- Solder masks (F.Mask, B.Mask)
- Silkscreen layers (F.SilkS, B.SilkS)
- Solder paste (F.Paste, B.Paste)
- Board outline (Edge.Cuts)
- Drill files (PTH and NPTH)

## API Reference

### `Circuit.generate_gerbers()`

```python
def generate_gerbers(
    self,
    output_dir: Optional[str] = None,
    project_name: Optional[str] = None,
    include_drill: bool = True,
    drill_format: str = "excellon",
) -> Dict[str, Any]:
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | str | None | Directory where Gerber files should be written. If not provided, defaults to `{project_name}/gerbers` |
| `project_name` | str | None | Name of KiCad project directory. If not provided, defaults to circuit name |
| `include_drill` | bool | True | Also export drill files along with Gerbers |
| `drill_format` | str | "excellon" | Format for drill files: "excellon" (standard) or "gerber" |

#### Return Value

Returns a dictionary with the following keys:

```python
{
    "success": bool,              # True if Gerbers were successfully generated
    "gerber_files": [Path, ...],  # List of generated .gbr files
    "drill_files": (Path, Path),  # Tuple of (plated_holes, non_plated_holes) or None
    "project_path": Path,         # Path to KiCad project directory
    "output_dir": Path,           # Directory where Gerbers were exported
    "error": str (optional)       # Error message if generation failed
}
```

## Usage Examples

### Basic Usage

```python
# Use circuit name as project name, default output location
result = circuit.generate_gerbers()

if result["success"]:
    print(f"Generated {len(result['gerber_files'])} Gerber files")
```

### Custom Output Directory

```python
# Save Gerbers to specific location
result = circuit.generate_gerbers(
    project_name="my_design",
    output_dir="manufacturing/gerbers"
)
```

### Gerbers Only (No Drill Files)

```python
# Generate Gerbers but skip drill files
result = circuit.generate_gerbers(
    project_name="my_design",
    include_drill=False
)
```

### Gerber Format Drill Files

```python
# Use Gerber format for drill files instead of Excellon
result = circuit.generate_gerbers(
    project_name="my_design",
    drill_format="gerber"
)
```

### Check Results

```python
result = circuit.generate_gerbers(project_name="my_board")

if result["success"]:
    print(f"✓ Generated {len(result['gerber_files'])} Gerber files")
    print(f"✓ Drill files: {result['drill_files']}")
    print(f"✓ Location: {result['output_dir']}")

    # Ready to submit to manufacturer
else:
    print(f"✗ Error: {result['error']}")
```

## Exported Files

### Standard Gerber Files

All standard PCB manufacturing layers are automatically exported:

| File | Layer | Description |
|------|-------|-------------|
| `*-F.Cu.gbr` | F.Cu | Front copper (component side) |
| `*-B.Cu.gbr` | B.Cu | Back copper (solder side) |
| `*-F.Mask.gbr` | F.Mask | Front solder mask (green/red) |
| `*-B.Mask.gbr` | B.Mask | Back solder mask |
| `*-F.SilkS.gbr` | F.SilkS | Front silkscreen (component labels) |
| `*-B.SilkS.gbr` | B.SilkS | Back silkscreen |
| `*-F.Paste.gbr` | F.Paste | Front solder paste (SMT stencil) |
| `*-B.Paste.gbr` | B.Paste | Back solder paste |
| `*-Edge.Cuts.gbr` | Edge.Cuts | Board outline and dimensions |

### Drill Files

When `include_drill=True`:

| File | Description |
|------|-------------|
| `*-PTH.xln` | Through-hole drill (Excellon format) |
| `*-NPTH.xln` | Non-plated hole drill (Excellon format) |

Or with `drill_format="gerber"`:

| File | Description |
|------|-------------|
| `*-NPTH.gbr` | Non-plated holes (Gerber format) |

## How It Works

When you call `generate_gerbers()`:

1. **Project Generation**: Creates a complete KiCad project with PCB layout if needed
2. **PCB Creation**: Automatically routes and places all components
3. **Layer Preparation**: Generates all manufacturing layers
4. **Gerber Export**: Uses `kicad-cli pcb export gerbers` to generate Gerber files
5. **Drill Export**: Uses `kicad-cli pcb export drill` to generate drill files
6. **Results**: Returns paths to all generated files

## Common Workflows

### Workflow 1: Complete Manufacturing Package

```python
# Generate all manufacturing documentation and files
@circuit(name="USB_Hub")
def usb_hub():
    # ... circuit design ...
    pass

circuit = usb_hub()

# BOM for component ordering
bom_result = circuit.generate_bom()
print(f"BOM: {bom_result['file']}")

# PDF for review and documentation
pdf_result = circuit.generate_pdf_schematic()
print(f"Schematic: {pdf_result['file']}")

# Gerbers for PCB manufacturing
gerber_result = circuit.generate_gerbers()
print(f"Manufacturing files: {gerber_result['output_dir']}")

# Now you have a complete manufacturing package!
```

### Workflow 2: Submit to JLCPCB

```python
# Generate Gerbers optimized for JLCPCB
result = circuit.generate_gerbers(
    project_name="my_design",
    output_dir="jlcpcb/gerbers",
    include_drill=True,        # JLCPCB needs drill files
    drill_format="excellon"    # Use standard Excellon format
)

# Now upload to JLCPCB:
# 1. Go to JLCPCB website
# 2. Click "Quote Now" or "Add Gerber"
# 3. Upload all files from {result['output_dir']}
# 4. JLCPCB auto-detects layers and generates quote
```

### Workflow 3: Submit to PCBWay

```python
# Generate Gerbers for PCBWay
result = circuit.generate_gerbers(
    project_name="my_design",
    output_dir="pcbway/gerbers"
)

# Upload to PCBWay:
# 1. Log in to PCBWay account
# 2. Click "Instant Quote"
# 3. Upload all files from {result['output_dir']}
# 4. Review board specifications and place order
```

### Workflow 4: Review Before Manufacturing

```python
import subprocess

# Generate Gerbers
result = circuit.generate_gerbers()

# Create ZIP file for manufacturer
import zipfile
zip_path = Path("manufacturing.zip")
with zipfile.ZipFile(zip_path, 'w') as zf:
    for gerber in result['gerber_files']:
        zf.write(gerber, arcname=gerber.name)
    if result['drill_files']:
        for drill in result['drill_files']:
            if drill:
                zf.write(drill, arcname=drill.name)

print(f"Manufacturing package: {zip_path}")

# View Gerbers in KiCad for review
kicad_pcb = result['project_path'] / f"{result['project_path'].name}.kicad_pcb"
subprocess.run(["kicad", str(kicad_pcb)])
```

## File Format Details

### Gerber Format

- **Standard**: RS-274X (extended Gerber)
- **Units**: Millimeters (mm)
- **Precision**: Standard KiCad precision
- **Extensions**: Use Protel format (.gbr, .gbl, etc.) for universal compatibility

### Drill File Format

**Excellon (default)**:
- Extension: .xln (KiCad convention)
- Format: Standard Excellon format
- Units: Millimeters
- Compatible with: All PCB manufacturers

**Gerber Drill**:
- Extension: .gbr
- Format: Gerber drill format
- Compatible with: Advanced manufacturing software

## Requirements

- **KiCad 8.0 or later** (for kicad-cli gerber export support)
- **kicad-cli available in PATH**: Ensure KiCad is properly installed
- **Python 3.8+**: Circuit-synth requires Python 3.8 or later
- **Complete circuit design**: All components must be defined and connected

### Verify KiCad Installation

```bash
# Check if kicad-cli is available
kicad-cli --version

# If not found, add KiCad to PATH (examples)

# Linux
export PATH="/usr/lib/kicad/bin:$PATH"

# macOS
export PATH="/Applications/KiCad/Contents/MacOS:$PATH"

# Windows (in PowerShell)
$env:Path += ";C:\Program Files\KiCad\bin"
```

## Troubleshooting

### Error: "PCB must be saved to a file"

**Problem**: Gerber export fails with "PCB must be saved to a file before exporting Gerbers"

**Solution**:
- This is an internal error - the PCB should be automatically saved
- Try deleting the project directory and regenerating
- Check for file permission issues in the project directory

### Error: "kicad-cli not found"

**Problem**: `generate_gerbers()` fails with "kicad-cli not found in PATH"

**Solution**:
1. Ensure KiCad 8.0+ is installed
2. Add KiCad to your PATH (see Verify KiCad Installation section above)
3. Verify: `kicad-cli --version`

### Gerber files are empty or incomplete

**Problem**: Generated Gerbers have no content

**Solution**:
- Verify all components have proper `ref` parameters
- Check that component symbols exist in KiCad libraries
- Ensure the circuit has proper connections and power nets
- Try manually generating PCB in KiCad to debug

### Drill files missing

**Problem**: No drill files in result, but they were requested

**Solution**:
- Check that PCB has plated holes (vias or component holes)
- Verify `include_drill=True` is set
- Try with `drill_format="gerber"` as alternative

### File permissions error

**Problem**: "Permission denied" when writing Gerbers

**Solution**:
- Check that output directory is writable
- Ensure project directory has proper permissions
- Try specifying an absolute path for output_dir

## Performance Notes

- **First Export**: Takes 20-60 seconds (includes full project generation and PCB layout)
- **Subsequent Exports**: Takes 5-15 seconds (reuses existing project)
- **Large Designs**: 100+ component designs may take 1-2 minutes for initial generation

## Manufacturer Compatibility

### JLCPCB

```python
result = circuit.generate_gerbers(
    project_name="design",
    include_drill=True,
    drill_format="excellon"
)

# All files ready for upload
# JLCPCB will auto-detect layers and generate quote
```

**Notes**:
- Upload all .gbr and .xln files together
- JLCPCB automatically detects layer types
- Assembly files optional but recommended for SMT assembly

### PCBWay

```python
result = circuit.generate_gerbers(
    project_name="design",
    include_drill=True
)

# Upload all Gerber and drill files
# PCBWay auto-detects board specifications
```

**Notes**:
- Similar to JLCPCB
- Supports both Excellon and Gerber drill formats
- Can request design review before manufacturing

### OSH Park

```python
result = circuit.generate_gerbers(
    project_name="design",
    include_drill=True
)

# Upload all files in a ZIP archive
# OSH Park has specific requirements - check their website
```

**Notes**:
- Excellent for hobby/prototype boards
- USA-based manufacture
- Lower volume pricing
- Check OSH Park file format requirements on their website

## Advanced Topics

### Batch Manufacturing Export

Generate Gerbers for multiple circuit variants:

```python
designs = {
    "v1.0": esp32_board_v1(),
    "v1.1": esp32_board_v1_1(),
    "v2.0": esp32_board_v2(),
}

for version, circuit_obj in designs.items():
    result = circuit_obj.generate_gerbers(
        project_name=f"esp32_{version}",
        output_dir=f"manufacturing/{version}/gerbers"
    )
    print(f"Generated: {result['output_dir']}")
```

### Layer Customization

While circuit-synth exports standard layers by default, you can access the underlying KiCadCLI for custom layer selections:

```python
from circuit_synth.pcb.kicad_cli import get_kicad_cli
from pathlib import Path

# Generate base project
result = circuit.generate_gerbers(project_name="my_design")

# Export custom layers if needed
cli = get_kicad_cli()
pcb_file = result['project_path'] / "my_design.kicad_pcb"

# Custom layers (e.g., only copper, no paste/mask)
custom_gerbers = cli.export_gerbers(
    pcb_file=pcb_file,
    output_dir=result['output_dir'],
    layers=["F.Cu", "B.Cu", "Edge.Cuts"]
)
```

### Manufacturing Documentation Package

Create a complete package with all necessary documents:

```python
import zipfile
from pathlib import Path

circuit = my_circuit()

# Generate all documents
bom = circuit.generate_bom(project_name="design")
pdf = circuit.generate_pdf_schematic(project_name="design")
gerbers = circuit.generate_gerbers(project_name="design")

# Create manufacturing package
with zipfile.ZipFile("design_manufacturing.zip", 'w') as zf:
    # Add BOM
    zf.write(bom['file'], arcname=bom['file'].name)

    # Add schematic
    zf.write(pdf['file'], arcname=pdf['file'].name)

    # Add all Gerber files
    for gerber in gerbers['gerber_files']:
        zf.write(gerber, arcname=gerber.name)

    # Add drill files
    if gerbers['drill_files']:
        for drill in gerbers['drill_files']:
            if drill:
                zf.write(drill, arcname=drill.name)

print(f"Manufacturing package: design_manufacturing.zip")
```

## API Stability

The `generate_gerbers()` method is part of circuit-synth's public API and will be maintained with backward compatibility. The return dictionary structure is guaranteed to include `success`, `gerber_files`, `drill_files`, `project_path`, and `output_dir` fields in all future versions.

## See Also

- [BOM Export Guide](BOM_EXPORT.md)
- [PDF Schematic Export Guide](PDF_EXPORT.md)
- [KiCad CLI Documentation](https://docs.kicad.org/latest/en/cli/cli.html)
- [Gerber File Format Specification](https://en.wikipedia.org/wiki/Gerber_format)
- [Circuit-synth README](../README.md)
