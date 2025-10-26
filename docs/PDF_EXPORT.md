# PDF Schematic Export Guide

## Overview

Circuit-synth provides a simple, one-line API to export your circuit schematics as professional PDF documents. Perfect for documentation, sharing designs, reviews, and archival purposes.

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

# Generate PDF in one line
result = circuit.generate_pdf_schematic(project_name="my_board")
```

This generates `my_board/my_board.pdf` with all schematic pages.

## API Reference

### `Circuit.generate_pdf_schematic()`

```python
def generate_pdf_schematic(
    self,
    output_file: Optional[str] = None,
    project_name: Optional[str] = None,
    black_and_white: bool = False,
    theme: Optional[str] = None,
    exclude_drawing_sheet: bool = False,
    pages: Optional[str] = None,
) -> Dict[str, Any]:
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_file` | str | None | Path where PDF should be written. If not provided, defaults to `{project_name}/{project_name}.pdf` |
| `project_name` | str | None | Name of KiCad project directory. If not provided, defaults to circuit name |
| `black_and_white` | bool | False | Export in black and white instead of color |
| `theme` | str | None | Color theme to use for export (optional, KiCad-dependent) |
| `exclude_drawing_sheet` | bool | False | Exclude the drawing sheet (title block and borders) from PDF |
| `pages` | str | None | Page range to export (e.g., "1,3-5" for pages 1, 3, 4, 5). If not specified, all pages are exported |

#### Return Value

Returns a dictionary with the following keys:

```python
{
    "success": bool,           # True if PDF was successfully generated
    "file": Path,              # Path to generated PDF file
    "project_path": Path,      # Path to KiCad project directory
    "error": str (optional)    # Error message if generation failed
}
```

## Usage Examples

### Basic Usage

```python
# Use circuit name as project name, default PDF location
result = circuit.generate_pdf_schematic()
```

### Custom Output Path

```python
# Save PDF to specific location
result = circuit.generate_pdf_schematic(
    project_name="my_design",
    output_file="documentation/schematic.pdf"
)
```

### Black and White Export

For printing or when color is not needed:

```python
result = circuit.generate_pdf_schematic(
    project_name="my_design",
    black_and_white=True
)
```

### Exclude Title Block

Remove the drawing sheet (title block and borders):

```python
result = circuit.generate_pdf_schematic(
    project_name="my_design",
    exclude_drawing_sheet=True
)
```

### Export Specific Pages

For multi-page schematics, export only certain pages:

```python
result = circuit.generate_pdf_schematic(
    project_name="my_design",
    pages="1"              # Only first page
)

result = circuit.generate_pdf_schematic(
    project_name="my_design",
    pages="1,3-5"          # Pages 1, 3, 4, 5
)

result = circuit.generate_pdf_schematic(
    project_name="my_design",
    pages="2-"             # Pages 2 and onwards
)
```

### With Color Theme

Use a specific color theme (theme names depend on KiCad installation):

```python
result = circuit.generate_pdf_schematic(
    project_name="my_design",
    theme="solarized"      # If available in your KiCad
)
```

### Check Result

```python
result = circuit.generate_pdf_schematic(project_name="my_board")

if result["success"]:
    print(f"PDF exported to: {result['file']}")
    print(f"Project path: {result['project_path']}")

    # PDF file is ready to share or print
else:
    print(f"Error: {result['error']}")
```

## How It Works

When you call `generate_pdf_schematic()`:

1. **Project Generation**: If a KiCad project doesn't exist, circuit-synth generates one by calling `generate_kicad_project()`
2. **Schematic Creation**: The circuit is exported to a `.kicad_sch` file
3. **PDF Export**: `kicad-cli sch export pdf` is invoked on the schematic
4. **Results**: The method returns the path and metadata

## Common Workflows

### Workflow 1: Document Your Design

```python
# 1. Design your circuit
@circuit(name="USB_Hub")
def usb_hub():
    # ... components ...
    pass

# 2. Generate PDF for documentation
circuit = usb_hub()
result = circuit.generate_pdf_schematic()

# 3. Share or archive the PDF
# - Email to colleagues
# - Upload to design repository
# - Print for reference
```

### Workflow 2: Generate Multiple Document Formats

```python
# Generate both BOM and PDF for manufacturing documentation
circuit = my_circuit()

# BOM for ordering
bom_result = circuit.generate_bom()

# PDF for assembly documentation
pdf_result = circuit.generate_pdf_schematic()

print(f"Manufacturing package ready:")
print(f"  BOM: {bom_result['file']}")
print(f"  Schematic: {pdf_result['file']}")
```

### Workflow 3: Black & White for Printing

```python
# Generate print-friendly B/W PDF without title block
result = circuit.generate_pdf_schematic(
    project_name="my_design",
    black_and_white=True,
    exclude_drawing_sheet=True
)

# Ready to print on paper
```

### Workflow 4: Export Specific Pages

```python
# For large designs with multiple pages,
# export only the pages needed for a specific review

result = circuit.generate_pdf_schematic(
    project_name="my_design",
    pages="1-3"  # Only power and signal pages
)
```

## Requirements

- **KiCad 7.0 or later** (for kicad-cli PDF support)
- **kicad-cli available in PATH**: Ensure KiCad is properly installed
- **Python 3.8+**: Circuit-synth requires Python 3.8 or later

### Verify KiCad Installation

```bash
# Check if kicad-cli is available
kicad-cli --version

# If not found, add KiCad to PATH (macOS example)
export PATH="/Applications/KiCad/Contents/MacOS:$PATH"
```

## Troubleshooting

### Error: "kicad-cli not found"

**Problem**: `generate_pdf_schematic()` fails with "kicad-cli not found in PATH"

**Solution**:
1. Ensure KiCad 7.0+ is installed
2. Add KiCad to your PATH:
   ```bash
   # Linux
   export PATH="/usr/lib/kicad/bin:$PATH"

   # macOS
   export PATH="/Applications/KiCad/Contents/MacOS:$PATH"

   # Windows (in PowerShell)
   $env:Path += ";C:\Program Files\KiCad\bin"
   ```
3. Verify: `kicad-cli --version`

### Error: "Schematic file not found"

**Problem**: PDF export fails because schematic file doesn't exist

**Solution**:
- This usually means the KiCad project generation failed
- Check that `generate_kicad_project()` runs successfully first
- Look for error messages in the result dictionary

### PDF is blank or incomplete

**Problem**: Generated PDF has no content or pages

**Solution**:
- Verify all components have `ref` parameters assigned
- Check that component symbols exist in KiCad libraries
- Try exporting the project manually in KiCad to debug

## Performance Notes

- **First Export**: Takes 10-30 seconds (includes project generation)
- **Subsequent Exports**: Takes 5-10 seconds (reuses existing project)
- **Large Designs**: Multi-page schematics may take slightly longer

## Integration with Documentation Systems

### Sphinx/ReadTheDocs

```python
# Generate PDF for documentation build
result = circuit.generate_pdf_schematic(
    project_name="my_circuit",
    output_file="_static/schematics/my_circuit.pdf"
)
```

### GitHub Pages

```python
# Generate PDF for GitHub Pages static content
result = circuit.generate_pdf_schematic(
    project_name="my_circuit",
    output_file="docs/pdf/my_circuit.pdf"
)

# Commit the PDF for distribution
```

### Jupyter Notebooks

```python
# In Jupyter, display schematic info
result = circuit.generate_pdf_schematic()

if result["success"]:
    from IPython.display import Markdown
    display(Markdown(f"### Schematic exported to {result['file']}"))
```

## Advanced Topics

### Batch PDF Generation

Generate PDFs for multiple circuits:

```python
from pathlib import Path

circuits = [
    ("power_stage", power_circuit()),
    ("signal_chain", signal_circuit()),
    ("control", control_circuit()),
]

for name, circuit_obj in circuits:
    result = circuit_obj.generate_pdf_schematic(
        project_name=name,
        output_file=f"documentation/{name}_schematic.pdf"
    )
    print(f"Exported: {result['file']}")
```

### Theme Support

Available themes depend on your KiCad installation. Common themes:
- `default` (KiCad default)
- `solarized` (if installed)
- Custom themes in KiCad config

Check available themes in KiCad:
```
File → Preferences → Appearance → Color Theme
```

## API Stability

The `generate_pdf_schematic()` method is part of circuit-synth's public API and will be maintained with backward compatibility. The return dictionary structure is guaranteed to include `success`, `file`, and `project_path` fields in all future versions.

## See Also

- [BOM Export Guide](BOM_EXPORT.md)
- [KiCad CLI Documentation](https://docs.kicad.org/latest/en/cli/cli.html)
- [Circuit-synth README](../README.md)
