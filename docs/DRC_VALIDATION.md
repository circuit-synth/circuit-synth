# Design Rule Check (DRC) Validation

## Overview

The DRC (Design Rule Check) validation system in circuit-synth provides automated layout verification to catch manufacturing issues before fabrication. It integrates with both KiCad's native DRC engine and provides Python-based checks for faster iteration during automated PCB generation.

## Features

### Core Capabilities

- **Via Placement Validation**: Ensures vias don't short to pads or traces on different nets
- **Clearance Validation**: Verifies minimum spacing between all copper features
- **Trace Width Compliance**: Checks that all traces meet minimum width requirements
- **Copper on Edge Cuts**: Detects copper features incorrectly placed on edge cuts layer
- **Drill Size Validation**: Validates drill sizes are within manufacturing limits
- **Annular Ring Checks**: Ensures vias have sufficient copper around drill holes
- **Auto-Fix Suggestions**: Provides actionable fixes for common violations

## Usage

### Basic DRC Validation

```python
from circuit_synth.pcb import PCBBoard, run_enhanced_drc

# Load or create a PCB
pcb = PCBBoard()
# ... add components, tracks, vias ...

# Run DRC validation
result, fixes = run_enhanced_drc(pcb)

# Check results
if result.is_valid:
    print("DRC passed!")
else:
    print(f"Found {result.error_count} errors")
    for issue in result.issues:
        print(f"  {issue}")

# Review suggested fixes
if fixes:
    print(f"\nAvailable fixes: {len(fixes)}")
    for fix in fixes:
        print(f"  - {fix.description}")
```

### Custom Design Rules

You can define custom design rules for specific manufacturing processes:

```python
from circuit_synth.pcb.drc import DRCRule, EnhancedDRCValidator

# Define custom rules (e.g., for 4-layer board with tight spacing)
custom_rules = DRCRule(
    name="high_density",
    description="Rules for high-density 4-layer boards",
    min_trace_width=0.10,      # 100µm minimum trace width
    min_trace_spacing=0.10,    # 100µm minimum spacing
    min_via_diameter=0.3,      # 300µm minimum via
    min_via_drill=0.15,        # 150µm minimum drill
    min_via_annular_ring=0.075,# 75µm annular ring
    min_clearance=0.15,        # 150µm clearance
    edge_clearance=1.0         # 1mm from board edge
)

# Run DRC with custom rules
validator = EnhancedDRCValidator(custom_rules)
result = validator.validate_pcb(pcb)
```

### Integration with PCB Generation

DRC validation is automatically integrated into the PCB generation workflow:

```python
from circuit_synth.kicad.pcb_gen import PCBGenerator

generator = PCBGenerator(project_dir="my_project", project_name="my_pcb")

# DRC runs automatically after placement (before routing)
success = generator.generate_pcb(
    run_drc=True,              # Enable DRC validation (default: True)
    drc_fail_on_error=False    # Continue even if DRC finds errors
)
```

To halt generation on DRC errors:

```python
success = generator.generate_pcb(
    run_drc=True,
    drc_fail_on_error=True  # Stop if DRC finds errors
)
```

### Using KiCad's Native DRC

For comprehensive validation, you can also use KiCad's built-in DRC engine:

```python
from circuit_synth.pcb import PCBBoard

pcb = PCBBoard("my_board.kicad_pcb")

# Run KiCad's DRC (requires KiCad installation)
drc_result = pcb.run_drc(
    output_file="drc_report.json",
    severity="error",
    format="json"
)

if drc_result.success:
    print("No violations found")
else:
    print(f"Violations: {len(drc_result.violations)}")
    print(f"Warnings: {len(drc_result.warnings)}")
    print(f"Unconnected: {len(drc_result.unconnected_items)}")
```

## DRC Categories

The enhanced DRC validator checks for the following categories of violations:

### Via Placement (`VIA_PLACEMENT`)
- Vias shorting to pads on different nets
- Insufficient clearance from vias to traces
- Via placement near board edges

### Clearance (`CLEARANCE`)
- Pad-to-pad clearances on different nets
- Track-to-track clearances
- Pad-to-track clearances

### Trace Width (`TRACE_WIDTH`)
- Traces below minimum width
- Zero-width tracks

### Copper on Edge Cuts (`COPPER_EDGE`)
- Copper features on Edge.Cuts layer
- Insufficient clearance from board edges

### Drill Size (`DRILL_SIZE`)
- Drill holes below minimum diameter
- Drill holes exceeding maximum diameter
- Via drills outside manufacturing limits

### Annular Ring (`ANNULAR_RING`)
- Insufficient copper around via drill holes
- Risk of drill breakout

### Short Circuits (`SHORT_CIRCUIT`)
- Potential short circuits between nets
- (Comprehensive detection requires KiCad DRC)

## Design Rules Reference

### Default Rules

```python
DRCRule(
    min_trace_width=0.15,       # 150µm (6 mil)
    min_trace_spacing=0.15,     # 150µm (6 mil)
    min_via_diameter=0.4,       # 400µm (16 mil)
    min_via_drill=0.2,          # 200µm (8 mil)
    min_via_annular_ring=0.05,  # 50µm (2 mil)
    min_clearance=0.2,          # 200µm (8 mil)
    min_drill_size=0.15,        # 150µm (6 mil)
    max_drill_size=6.3,         # 6.3mm (standard limit)
    edge_clearance=0.5          # 500µm from edge
)
```

### Common Manufacturing Classes

**Standard PCB (Class 2)**
```python
DRCRule(
    min_trace_width=0.15,
    min_clearance=0.20,
    min_via_diameter=0.45,
    min_via_drill=0.25
)
```

**High-Density (Class 3)**
```python
DRCRule(
    min_trace_width=0.10,
    min_clearance=0.15,
    min_via_diameter=0.30,
    min_via_drill=0.15
)
```

**Prototype-Friendly**
```python
DRCRule(
    min_trace_width=0.20,
    min_clearance=0.25,
    min_via_diameter=0.60,
    min_via_drill=0.30
)
```

## Auto-Fix System

The DRC validator provides suggested fixes for common violations:

```python
result, fixes = run_enhanced_drc(pcb)

# Review available fixes
for fix in fixes:
    print(f"Fix: {fix.description}")
    print(f"Type: {fix.fix_type}")
    print(f"Parameters: {fix.parameters}")

# Apply fixes (when implemented)
# validator = EnhancedDRCValidator()
# for fix in fixes:
#     validator.apply_fix(pcb, fix)
```

### Available Fix Types

- `adjust_track_width`: Increase track width to meet minimum
- `move_via`: Relocate via to avoid clearance violation
- `adjust_via_size`: Increase via diameter for proper annular ring

## Best Practices

### 1. Run DRC Early and Often

```python
# Run DRC after placement, before routing
generator.generate_pcb(run_drc=True)

# Run again after manual edits
result, fixes = run_enhanced_drc(pcb)
```

### 2. Use Appropriate Rules for Your Manufacturer

Different PCB manufacturers have different capabilities. Always check your manufacturer's design rules and adjust accordingly.

```python
# JLCPCB standard capabilities
jlcpcb_rules = DRCRule(
    name="jlcpcb_standard",
    min_trace_width=0.127,  # 5 mil
    min_clearance=0.127,    # 5 mil
    min_drill_size=0.20     # 8 mil
)
```

### 3. Review Warnings

Not all DRC issues are errors. Review warnings to understand potential manufacturing risks:

```python
if result.warning_count > 0:
    print("Warnings to review:")
    for issue in result.issues:
        if issue.severity == ValidationSeverity.WARNING:
            print(f"  {issue}")
```

### 4. Combine Python and KiCad DRC

For best results, use both validation systems:

```python
# 1. Fast Python-based checks during development
result, fixes = run_enhanced_drc(pcb)

# 2. Comprehensive KiCad DRC before finalization
if result.is_valid:
    kicad_result = pcb.run_drc()
    if kicad_result.success:
        print("Ready for manufacturing!")
```

## Troubleshooting

### Via Placement Errors

**Issue**: Vias violating clearance to pads
- **Fix**: Increase spacing or move via location
- **Prevention**: Use larger component spacing during placement

### Trace Width Violations

**Issue**: Tracks below minimum width
- **Fix**: Manually adjust track width or use auto-fix
- **Prevention**: Set minimum width in routing settings

### Drill Size Errors

**Issue**: Drill holes too small or too large
- **Fix**: Adjust via or pad drill parameters
- **Prevention**: Verify footprint libraries meet design rules

### Edge Clearance Warnings

**Issue**: Components too close to board edge
- **Fix**: Increase board size or move components
- **Prevention**: Set appropriate margin in PCB generation

## API Reference

### Core Classes

#### `DRCRule`
Design rule definition with manufacturing constraints.

#### `DRCCategory`
Enumeration of DRC violation categories.

#### `DRCFix`
Suggested fix for a DRC violation.

#### `EnhancedDRCValidator`
Main validator class with comprehensive checks.

### Functions

#### `run_enhanced_drc(pcb_board, rules=None)`
Convenience function to run DRC validation.

**Parameters:**
- `pcb_board`: PCBBoard instance
- `rules`: Optional DRCRule object (uses defaults if None)

**Returns:**
- Tuple of (ValidationResult, List[DRCFix])

### ValidationResult

**Properties:**
- `is_valid`: True if no errors found
- `error_count`: Number of errors
- `warning_count`: Number of warnings
- `issues`: List of ValidationIssue objects

**Methods:**
- `add_error(category, message, location, affected_items)`
- `add_warning(category, message, location, affected_items)`
- `print_summary()`: Print validation summary

## Examples

### Example 1: Basic Validation

```python
from circuit_synth.pcb import PCBBoard, run_enhanced_drc

pcb = PCBBoard("my_design.kicad_pcb")
result, fixes = run_enhanced_drc(pcb)

print(f"Errors: {result.error_count}")
print(f"Warnings: {result.warning_count}")
print(f"Valid: {result.is_valid}")
```

### Example 2: Custom Rules for High-Density Board

```python
from circuit_synth.pcb.drc import DRCRule, EnhancedDRCValidator

rules = DRCRule(
    name="hd_multilayer",
    min_trace_width=0.10,
    min_clearance=0.10,
    min_via_diameter=0.30
)

validator = EnhancedDRCValidator(rules)
result = validator.validate_pcb(pcb)
```

### Example 3: Automated Workflow

```python
from circuit_synth.kicad.pcb_gen import PCBGenerator

generator = PCBGenerator("project", "design")

# Generate with DRC validation
if generator.generate_pcb(run_drc=True, drc_fail_on_error=True):
    print("PCB generated and validated successfully!")
else:
    print("DRC validation failed - review errors")
```

## Contributing

To add new DRC checks:

1. Add check method to `EnhancedDRCValidator` class
2. Call method from `validate_pcb()`
3. Add appropriate DRC category
4. Create fix suggestions when applicable
5. Add tests to `tests/pcb/test_drc.py`

See `src/circuit_synth/pcb/drc.py` for implementation details.
