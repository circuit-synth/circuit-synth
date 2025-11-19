# Schematic Design Checking Research

**Date:** 2025-11-18
**Purpose:** Research schematic design checking practices and determine how circuit-synth can help

---

## Problem Statement

User feedback (Tom Anderson) indicates need for:
- Analysis of existing KiCAD designs (not just synthesis)
- Design checkers/validators
- Schematic cleanup tools

**User's Use Case:**
> "I have a bunch of KiCAD designs that need cleanup, and I want to write a design checker."

---

## Types of Design Checks

### 1. Electrical Rule Checks (ERC)

Verify electrical connectivity and compatibility:

**Common Checks:**
- Unconnected pins (inputs, outputs)
- Shorted outputs (two outputs connected together)
- Missing power flags on power nets
- Pin type conflicts (based on electrical compatibility matrix)
- Unconnected hierarchical symbols
- Input pins not driven
- Power input pins without power source

**Severity Levels:**
- Errors: Major violations requiring correction
- Warnings: Potential issues flagged for review

### 2. Manufacturing Checks (BOM Validation)

Ensure design is manufacturable:

**Common Checks:**
- Missing Manufacturer Part Numbers (MPN)
- Missing footprints
- Missing supplier part numbers
- Obsolete or unavailable parts
- Incomplete component specifications
- Missing package information

### 3. Design Standards Compliance

Verify adherence to design guidelines:

**Common Checks:**
- Missing component properties (Power rating, Tolerance, etc.)
- Naming conventions (reference designators)
- Duplicate references
- Missing descriptions
- Incomplete datasheets
- Missing test points

### 4. Schematic Quality Checks

Ensure schematic readability and maintainability:

**Common Checks:**
- Net naming consistency
- Label placement
- Wire routing quality
- Component organization
- Annotation completeness
- Hierarchical design consistency

---

## KiCAD's Built-in ERC System

### Overview

KiCAD provides comprehensive Electrical Rules Check (ERC) through both GUI and CLI.

### Command-Line Interface

**Basic Usage:**
```bash
kicad-cli sch erc [OPTIONS] INPUT_FILE
```

**Key Options:**
- `--output OUTPUT_FILE`: Specify report filename
- `--format FORMAT`: Choose `report` or `json` format
- `--severity-error`: Report only errors
- `--severity-warning`: Report only warnings
- `--severity-all`: Include all violations
- `--exit-code-violations`: Return exit code 5 if violations exist
- `--units UNITS`: Set measurement units (mm, in, mils)

**Example:**
```bash
# Run ERC and generate report
kicad-cli sch erc --severity-all --exit-code-violations -o erc.rpt design.kicad_sch

# JSON output for parsing
kicad-cli sch erc --format json -o erc.json design.kicad_sch
```

### ERC Capabilities

**What KiCAD ERC Checks:**
1. **Pin Connectivity**
   - Unconnected input pins
   - Unconnected output pins
   - Unconnected bidirectional pins
   - Input pins not driven

2. **Pin Type Conflicts**
   - Two outputs shorted together
   - Power outputs connected
   - Pin type compatibility matrix violations

3. **Power Nets**
   - Power input pins without power source
   - Missing PWR_FLAG symbols
   - Power net connectivity

4. **Hierarchical Design**
   - Unconnected hierarchical pins
   - Sheet pin mismatches
   - Missing sheet connections

5. **Special Cases**
   - No-connect flags properly used
   - Invisible power pins

### ERC Configuration

**Customizable via GUI:**
- File → Schematic Setup → Electrical Rules → Violation Severity
- Pin type conflict matrix (click to cycle: normal/warning/error)
- Per-violation severity adjustment

### ERC Output Formats

**Report Format (.rpt):**
```
ERC messages:

** ERC messages: 2  Errors 0  Warnings 2

*** Warning: Pin to pin warning: (27.94 mm, 17.78 mm): Unconnected Pin 1 on U1
*** Warning: Pin to pin warning: (27.94 mm, 20.32 mm): Unconnected Pin 2 on U1
```

**JSON Format (.json):**
```json
{
  "violations": [
    {
      "type": "unconnected_pin",
      "severity": "warning",
      "description": "Unconnected Pin 1 on U1",
      "location": {"x": 27.94, "y": 17.78},
      "reference": "U1",
      "pin": "1"
    }
  ],
  "error_count": 0,
  "warning_count": 2
}
```

### Common ERC Issues and Fixes

**1. Power Pin Warnings**
- Issue: "Input Power pin not driven by any Output Power pins"
- Cause: Power from connectors (not marked as power sources)
- Fix: Add PWR_FLAG symbol to power nets

**2. Unconnected Pins**
- Issue: "Pin not connected"
- Cause: Pin intentionally or accidentally unconnected
- Fix: Add no-connect flag if intentional, wire if not

**3. Output Conflicts**
- Issue: "Output connected to Output"
- Cause: Two outputs driving same net
- Fix: Check design logic, add buffering if needed

---

## Industry Best Practices for Design Checks

### From EDA Vendors (Altium, Cadence, Sierra Circuits)

**Schematic Checks:**
1. Design rule compliance
2. Net connectivity validation
3. Component parameter completeness
4. Manufacturing readiness
5. Footprint validation

**BOM Validation:**
1. All components have MPN
2. All components have footprints
3. Package information complete
4. Supplier information available
5. Lifecycle status (not obsolete)

**Quality Checks:**
1. Reference designators follow standard
2. Net names are meaningful
3. Power nets properly labeled
4. Test points included
5. Documentation complete

---

## Potential circuit-synth Design Checker Features

### Level 1: Property Validation

**What user showed in example:**
```python
# Check for missing footprints
for comp in sch.components:
    if not comp.footprint:
        issues.append(f"{comp.reference}: Missing footprint")

# Check for missing MPNs
for comp in sch.components:
    if not comp.has_property("MPN"):  # NOTE: This method missing!
        issues.append(f"{comp.reference}: Missing MPN property")
```

**Implementation:**
```python
import kicad_sch_api as ksa

def check_manufacturing_readiness(sch: ksa.Schematic) -> List[str]:
    """Check if schematic is ready for manufacturing."""
    issues = []

    for comp in sch.components:
        # Check footprint
        if not comp.footprint:
            issues.append(f"{comp.reference}: Missing footprint")

        # Check MPN
        if not comp.get_property("MPN"):
            issues.append(f"{comp.reference}: Missing MPN")

        # Check package
        if not comp.get_property("Package"):
            issues.append(f"{comp.reference}: Missing package info")

        # Check datasheet
        if not comp.get_property("Datasheet"):
            issues.append(f"{comp.reference}: Missing datasheet")

    return issues
```

### Level 2: KiCAD ERC Integration

**Approach: Run KiCAD's CLI and Parse Results**

```python
import subprocess
import json
from pathlib import Path

def run_kicad_erc(schematic_path: str) -> dict:
    """
    Run KiCAD's ERC and return results.

    Args:
        schematic_path: Path to .kicad_sch file

    Returns:
        Dictionary with ERC results

    Raises:
        FileNotFoundError: If KiCAD CLI not installed
        RuntimeError: If ERC fails
    """
    # Check if kicad-cli is available
    try:
        subprocess.run(['kicad-cli', '--version'],
                      capture_output=True, check=True)
    except FileNotFoundError:
        raise FileNotFoundError(
            "kicad-cli not found. Please install KiCAD 8.0 or later."
        )

    # Generate temp output file
    output_file = Path(schematic_path).with_suffix('.erc.json')

    # Run ERC
    result = subprocess.run([
        'kicad-cli', 'sch', 'erc',
        '--format', 'json',
        '--severity-all',
        '--exit-code-violations',
        '-o', str(output_file),
        schematic_path
    ], capture_output=True, text=True)

    # Parse results
    with open(output_file) as f:
        erc_data = json.load(f)

    # Clean up temp file
    output_file.unlink()

    return {
        'violations': erc_data.get('violations', []),
        'error_count': erc_data.get('error_count', 0),
        'warning_count': erc_data.get('warning_count', 0),
        'has_violations': result.returncode == 5
    }
```

### Level 3: Custom Circuit-Synth Validators

**Beyond KiCAD's ERC:**

```python
class SchematicValidator:
    """Custom validation rules for circuit-synth."""

    def __init__(self, schematic: ksa.Schematic):
        self.sch = schematic
        self.issues = []

    def check_all(self) -> List[ValidationIssue]:
        """Run all validation checks."""
        self.check_properties()
        self.check_naming()
        self.check_power_nets()
        self.check_connectivity()
        self.check_manufacturing()
        return self.issues

    def check_properties(self):
        """Validate component properties."""
        required_props = ['MPN', 'Package', 'Datasheet']

        for comp in self.sch.components:
            for prop in required_props:
                if not comp.get_property(prop):
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        component=comp.reference,
                        message=f"Missing property: {prop}"
                    ))

    def check_naming(self):
        """Validate reference designator conventions."""
        # R for resistors, C for capacitors, etc.
        prefix_map = {
            'Device:R': 'R',
            'Device:C': 'C',
            'Device:L': 'L',
        }

        for comp in self.sch.components:
            expected_prefix = prefix_map.get(comp.lib_id)
            if expected_prefix:
                if not comp.reference.startswith(expected_prefix):
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        component=comp.reference,
                        message=f"Expected prefix '{expected_prefix}'"
                    ))

    def check_power_nets(self):
        """Validate power net naming and connections."""
        power_net_names = ['VCC', 'VDD', 'GND', 'VSS']

        # Find all labels
        power_labels = [
            label for label in self.sch.labels
            if any(pn in label.text.upper() for pn in power_net_names)
        ]

        # Check for consistent naming
        vcc_variants = set()
        for label in power_labels:
            text = label.text.upper()
            if 'VCC' in text or 'VDD' in text:
                vcc_variants.add(label.text)

        if len(vcc_variants) > 1:
            self.issues.append(ValidationIssue(
                severity='warning',
                message=f"Inconsistent power rail naming: {vcc_variants}"
            ))

    def check_connectivity(self):
        """Check for potential connectivity issues."""
        # Find components with unconnected pins
        # (This would require netlist analysis)
        pass

    def check_manufacturing(self):
        """Check manufacturing requirements."""
        for comp in self.sch.components:
            # Check footprint exists
            if not comp.footprint:
                self.issues.append(ValidationIssue(
                    severity='error',
                    component=comp.reference,
                    message="Missing footprint (required for manufacturing)"
                ))

            # Check for resistor power rating
            if comp.lib_id == 'Device:R':
                if not comp.get_property('Power'):
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        component=comp.reference,
                        message="Missing power rating"
                    ))
```

---

## Proposed API Design

### Simple Validation Functions

```python
import circuit_synth as cs

# Load schematic
circuit = cs.load_schematic("design.kicad_sch")

# Run validation checks
issues = cs.validate(circuit, checks=[
    'properties',      # Check required properties
    'manufacturing',   # Check manufacturing readiness
    'naming',          # Check naming conventions
    'power_nets',      # Check power net consistency
])

# Display results
for issue in issues:
    print(f"[{issue.severity}] {issue.component}: {issue.message}")

# Run KiCAD ERC (if available)
try:
    erc_results = cs.run_erc(circuit)
    print(f"ERC: {erc_results.error_count} errors, "
          f"{erc_results.warning_count} warnings")
except cs.KiCADNotFoundError:
    print("KiCAD not installed, skipping ERC")
```

### Advanced Validator Class

```python
import circuit_synth as cs

# Create validator with custom rules
validator = cs.SchematicValidator(circuit)

# Add custom check
@validator.add_check
def check_capacitor_voltage(component):
    """Ensure capacitors have voltage rating."""
    if component.lib_id == 'Device:C':
        if not component.get_property('Voltage'):
            return cs.ValidationIssue(
                severity='warning',
                message='Missing voltage rating'
            )

# Run all checks
results = validator.validate()

# Generate report
validator.save_report('validation_report.html')
```

---

## Implementation Strategy

### Phase 1: Basic Property Validation (circuit-synth)

**Goal:** Simple validation functions for common checks

**Deliverables:**
1. `validate_properties()` - Check required properties
2. `validate_manufacturing()` - Check manufacturing readiness
3. `ValidationIssue` dataclass
4. Basic reporting

**Timeline:** 1-2 weeks

### Phase 2: KiCAD ERC Integration (circuit-synth)

**Goal:** Run KiCAD's ERC from Python

**Deliverables:**
1. `run_erc()` - Execute kicad-cli and parse results
2. Graceful handling when KiCAD not installed
3. JSON result parsing
4. Integration with ValidationIssue format

**Timeline:** 1 week

### Phase 3: Advanced Validators (circuit-synth)

**Goal:** Custom validation rules beyond KiCAD ERC

**Deliverables:**
1. `SchematicValidator` class
2. Plugin system for custom checks
3. Power net validation
4. Naming convention checks
5. Connectivity analysis

**Timeline:** 2-3 weeks

### Phase 4: Reporting and Visualization

**Goal:** Beautiful, actionable reports

**Deliverables:**
1. HTML report generation
2. Markdown report format
3. Interactive visualization (if in notebook)
4. Export to JSON/CSV

**Timeline:** 1 week

---

## Testing Strategy

### Unit Tests

```python
def test_validate_properties():
    """Test property validation."""
    circuit = create_test_circuit()
    comp = circuit.add_component('Device:R', 'R1', '10k')

    # Without MPN - should flag
    issues = validate_properties(circuit)
    assert any('MPN' in issue.message for issue in issues)

    # With MPN - should pass
    comp.set_property('MPN', 'RC0603FR-0710KL')
    issues = validate_properties(circuit)
    assert not any('MPN' in issue.message for issue in issues)

def test_run_erc_not_installed():
    """Test ERC when KiCAD not installed."""
    circuit = create_test_circuit()

    with pytest.raises(cs.KiCADNotFoundError):
        cs.run_erc(circuit)
```

### Integration Tests

```python
def test_full_validation_workflow():
    """Test complete validation workflow."""
    circuit = cs.load_schematic("test_design.kicad_sch")

    # Run all validations
    validator = cs.SchematicValidator(circuit)
    results = validator.validate()

    # Should find known issues
    assert results.error_count > 0
    assert results.warning_count > 0

    # Generate report
    report_path = validator.save_report('test_report.html')
    assert report_path.exists()
```

---

## Questions for User

1. **Priority order?**
   - Start with simple property validation?
   - Or jump to KiCAD ERC integration?

2. **Validation rules?**
   - What properties are "required" for your workflow?
   - Any specific naming conventions?
   - Custom validation rules needed?

3. **KiCAD dependency?**
   - Acceptable to require KiCAD installation for ERC?
   - Or make it optional feature?

4. **Reporting format?**
   - Simple list of issues?
   - HTML report?
   - Both?

5. **Repository location?**
   - Add to circuit-synth?
   - Or separate package (circuit-synth-lint)?

---

## Recommendations

### Immediate Action (2-3 weeks)

**Phase 1: Property Validation**
1. Add `validate_properties()` to circuit-synth
2. Add `validate_manufacturing()` to circuit-synth
3. Create `ValidationIssue` dataclass
4. Add example in RECIPES.md
5. Release as minor version (0.12.0)

**Phase 2: KiCAD ERC Integration**
1. Add `run_erc()` with kicad-cli integration
2. Handle missing KiCAD gracefully
3. Parse JSON output
4. Add tests with real KiCAD installation
5. Document in README
6. Release as minor version (0.13.0)

### Short-term (1-2 months)

**Phase 3: Advanced Validators**
1. Create SchematicValidator class
2. Add power net validation
3. Add naming convention checks
4. Plugin system for custom checks
5. Release as minor version (0.14.0)

### Medium-term (2-3 months)

**Phase 4: Reporting**
1. HTML report generation
2. Interactive notebook display
3. Export formats (JSON, CSV)
4. Release as minor version (0.15.0)

---

## Related Tools to Research

1. **KiBot** - KiCAD automation tool with validation
2. **KiCad Python** - Official KiCAD Python bindings
3. **PyKiCad** - Alternative Python interface
4. **Circuit-Lint** - Generic circuit validation (if exists)

---

## Next Steps

1. Get user feedback on approach
2. Create GitHub issues for each phase
3. Start with Phase 1: Property validation
4. Write tests
5. Update documentation
6. Release to PyPI

---

## Notes

- User wants analysis tools, not just synthesis
- Cleanup of existing designs is primary use case
- Terminal-based tools are less desirable
- Integration with Python API is key
- KiCAD's built-in ERC is powerful, should leverage it
- Custom validators needed for manufacturing checks
