# Bill of Materials (BOM) Export Guide

## Overview

Circuit-synth provides a simple, one-line API to export manufacturing-ready Bills of Materials from your circuit code. BOMs are exported in standard CSV format compatible with all major PCB manufacturers including JLCPCB, PCBWay, and OSH Park.

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

# Generate BOM in one line
result = circuit.generate_bom(project_name="my_board")
```

This generates `my_board/my_board.csv`:
```
"Refs","Value","Footprint","Qty","DNP"
"C1","100nF","","1",""
"R1","10k","","1",""
"R2","1k","","1",""
```

## API Reference

### `Circuit.generate_bom()`

```python
def generate_bom(
    self,
    output_file: Optional[str] = None,
    project_name: Optional[str] = None,
    fields: Optional[str] = None,
    labels: Optional[str] = None,
    group_by: Optional[str] = None,
    exclude_dnp: bool = False,
) -> Dict[str, Any]:
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_file` | str | None | Path where CSV BOM should be written. If not provided, defaults to `{project_name}/{project_name}.csv` |
| `project_name` | str | None | Name of KiCad project directory. If not provided, defaults to circuit name |
| `fields` | str | None | Comma-separated fields to export from schematic (e.g., "Reference,Value,Footprint"). If not specified, KiCad exports default fields |
| `labels` | str | None | Comma-separated column headers for BOM. Must match number of fields |
| `group_by` | str | None | Field to group references by when exporting (e.g., "Value" to consolidate identical parts) |
| `exclude_dnp` | bool | False | If True, exclude "Do not populate" components from BOM |

#### Return Value

Returns a dictionary with the following keys:

```python
{
    "success": bool,           # True if BOM was successfully generated
    "file": Path,              # Path to generated CSV file
    "component_count": int,    # Number of components in BOM
    "project_path": Path,      # Path to KiCad project directory
    "error": str (optional)    # Error message if generation failed
}
```

## Usage Examples

### Basic Usage

```python
# Use circuit name as project name, default CSV location
result = circuit.generate_bom()
```

### Custom Output Path

```python
# Save BOM to specific location
result = circuit.generate_bom(
    project_name="my_design",
    output_file="manufacturing/bom.csv"
)
```

### Group Components by Value

Consolidate identical components:

```python
result = circuit.generate_bom(
    project_name="my_design",
    group_by="Value"
)

# Result BOM shows consolidated quantities:
# "R1,R2,R3","10k","","3",""  # Three 10k resistors grouped together
# "C1,C2,C3","100nF","","3","" # Three 100nF capacitors grouped together
```

### Exclude DNP (Do Not Populate) Components

```python
# For designs with optional components marked DNP
result = circuit.generate_bom(
    project_name="my_design",
    exclude_dnp=True
)
```

### Custom Fields and Labels

```python
# Export specific fields with custom column headers
result = circuit.generate_bom(
    project_name="my_design",
    fields="Reference,Value,Footprint,Quantity",
    labels="Designator,Part Value,Package,Qty"
)
```

### Check Result

```python
result = circuit.generate_bom(project_name="my_board")

if result["success"]:
    print(f"BOM exported to: {result['file']}")
    print(f"Component count: {result['component_count']}")

    # Read the generated CSV
    with open(result['file'], 'r') as f:
        print(f.read())
else:
    print(f"Error: {result['error']}")
```

## How It Works

When you call `generate_bom()`:

1. **Project Generation**: If a KiCad project doesn't exist, circuit-synth generates one by calling `generate_kicad_project()`
2. **Schematic Creation**: The circuit is exported to a `.kicad_sch` file
3. **BOM Export**: `kicad-cli sch export bom` is invoked on the schematic
4. **CSV Generation**: KiCad exports a standard CSV format BOM
5. **Results**: The method returns the path and metadata

## Generated CSV Format

The default CSV format includes:

| Column | Description |
|--------|-------------|
| `Refs` | Component references (e.g., "R1", "R2", "C1") |
| `Value` | Component value (e.g., "10k", "100nF") |
| `Footprint` | Component footprint (blank if not assigned) |
| `Qty` | Quantity of this component |
| `DNP` | Do Not Populate flag (empty if not set) |

## Requirements

- **KiCad 8.0 or later** (for kicad-cli support)
- **kicad-cli available in PATH**: Ensure KiCad is properly installed
- **Python 3.12+**: Circuit-synth requires Python 3.12 or later

### Verify KiCad Installation

```bash
# Check if kicad-cli is available
kicad-cli --version

# If not found, add KiCad to PATH (macOS example)
export PATH="/Applications/KiCad/Contents/MacOS:$PATH"
```

## Common Workflows

### Workflow 1: Generate BOM for Manufacturing

```python
# 1. Design your circuit
@circuit(name="USB_Hub")
def usb_hub():
    # ... components ...
    pass

# 2. Generate BOM
circuit = usb_hub()
result = circuit.generate_bom()

# 3. Upload to manufacturer
# - Open result['file'] in spreadsheet (optional edits)
# - Upload to JLCPCB/PCBWay along with Gerber files
```

### Workflow 2: Generate Grouped BOM for Ordering

```python
# Consolidate identical parts for easier ordering
result = circuit.generate_bom(
    project_name="my_design",
    group_by="Value"
)

# CSV now shows:
# "R1,R2,R3,R4,R5","10k","0603","5",""
# This makes it easier to order 5 units of 10k resistor
```

### Workflow 3: Automated Manufacturing Package

```python
# Generate complete manufacturing package
def create_manufacturing_package(circuit_obj, output_dir):
    # Generate BOM
    bom_result = circuit_obj.generate_bom(
        project_name=output_dir,
        group_by="Value"
    )

    # Later: Add Gerbers, assembly drawings, etc.
    print(f"Manufacturing package ready:")
    print(f"  BOM: {bom_result['file']}")
    print(f"  Project: {bom_result['project_path']}")
```

## Troubleshooting

### Error: "kicad-cli not found"

**Problem**: `generate_bom()` fails with "kicad-cli not found in PATH"

**Solution**:
1. Ensure KiCad 8.0+ is installed
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

**Problem**: BOM export fails because schematic file doesn't exist

**Solution**:
- This usually means the KiCad project generation failed
- Check that `generate_kicad_project()` runs successfully first
- Look for error messages in the result dictionary

### Empty BOM

**Problem**: Generated BOM has no components

**Solution**:
- Verify all components have `ref` parameters assigned
- Check that component symbols exist in KiCad libraries
- Ensure components aren't marked as "DNP" if you want them included

## Integration with Manufacturing

### JLCPCB Upload

1. Generate BOM: `result = circuit.generate_bom()`
2. In JLCPCB order form, upload `{result['file']}`
3. JLCPCB auto-parses the CSV and shows component availability

### PCBWay Upload

1. Generate BOM: `result = circuit.generate_bom()`
2. In PCBWay order form, upload `{result['file']}`
3. PCBWay shows pricing and lead times

### OSH Park (No assembly)

1. BOMs are for reference only (OSH Park doesn't provide assembly)
2. Use for component ordering from separate suppliers

## API Stability

The `generate_bom()` method is part of circuit-synth's public API and will be maintained with backward compatibility. The return dictionary structure is guaranteed to include `success`, `file`, and `component_count` fields in all future versions.

## See Also

- [README.md - BOM Export Section](../README.md#-bill-of-materials-bom-export)
- [KiCad CLI Documentation](https://docs.kicad.org/latest/en/cli/cli.html)
- Issue #274: BOM Export Integration
- Issue #278: Manufacturing Package Generation (planned)
