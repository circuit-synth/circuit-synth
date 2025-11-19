# PRD: BOM Cleanup Audit Script

**Created:** 2025-11-18
**Status:** Draft
**Target:** kicad-sch-api (utility script/CLI command)

---

## Problem Statement

At Alembic Guitars, the user maintains company part numbers as user-added properties on schematic components for integration with a local part database. They have dozens of legacy schematics where these properties were not consistently added.

**Core Need:** A script to scan multiple KiCad schematics and generate a report identifying:
- Components missing required custom properties (e.g., company part numbers)
- Complete property information for each flagged component (footprint, value, tolerance, etc.)
- Schematic file location for each flagged component

This enables systematic BOM cleanup across an entire design library.

---

## Proposed Solution

Create a **BOM Cleanup Audit Script** that:

1. **Scans directory trees** for `.kicad_sch` files (recursive)
2. **Loads each schematic** using kicad-sch-api
3. **Iterates over all components** in each schematic
4. **Checks for required properties** (configurable list)
5. **Generates detailed CSV/JSON report** with:
   - Schematic file path
   - Component reference
   - Component value
   - Footprint
   - Missing properties
   - Existing properties (for context)
6. **Provides summary statistics** (components scanned, issues found, compliance %)

### Solution Location Decision

**Two-Layer Architecture:**

**Layer 1: Core Implementation in kicad-sch-api**
- Core audit logic in `kicad_sch_api/cli/audit_bom.py`
- Schematic file analysis and property extraction
- Report generation (CSV/JSON)
- CLI command: `kicad-sch audit-bom`

**Rationale:**
- This is schematic file analysis, not circuit generation
- Uses kicad-sch-api's existing component property API
- Useful for ANY KiCad user doing BOM cleanup (not circuit-synth specific)
- Fits with kicad-sch-api's CLI utilities (alongside `kicad-sch bom` command)
- Can be used standalone without circuit-synth dependencies

**Layer 2: circuit-synth Wrapper**
- Python API wrapper in `circuit_synth/kicad/bom_auditor.py`
- Convenience methods for circuit-synth users
- Optional CLI command or integration with existing commands
- Delegates to kicad-sch-api for actual work

**Benefits:**
- Core functionality in the right place (kicad-sch-api)
- Easy access for circuit-synth users
- Consistent with existing pattern (circuit-synth wraps kicad-sch-api)

---

## User Workflows

### Workflow 1: Basic Audit (Default)

```bash
# Scan current directory for schematics missing "PartNumber" property
kicad-sch audit-bom --required-properties PartNumber

# Output: bom_audit_report.csv
```

**Expected Report (CSV):**
```csv
Schematic,Reference,Value,Footprint,MissingProperties,Tolerance,Manufacturer
designs/amp_v1/amp.kicad_sch,R1,10k,Resistor_SMD:R_0603_1608Metric,PartNumber,1%,Yageo
designs/amp_v1/amp.kicad_sch,C5,100nF,Capacitor_SMD:C_0805_2012Metric,PartNumber,10%,Samsung
designs/power/supply.kicad_sch,U3,AMS1117-3.3,Package_TO_SOT_SMD:SOT-223,PartNumber,,Texas Instruments
```

### Workflow 2: Multiple Required Properties

```bash
# Check for both PartNumber and Manufacturer
kicad-sch audit-bom \
  --required-properties PartNumber,Manufacturer \
  --output-format json \
  --output audit_results.json
```

**Expected JSON:**
```json
{
  "summary": {
    "total_schematics": 12,
    "total_components": 487,
    "components_missing_properties": 143,
    "compliance_percentage": 70.6
  },
  "issues": [
    {
      "schematic": "designs/amp_v1/amp.kicad_sch",
      "reference": "R1",
      "value": "10k",
      "footprint": "Resistor_SMD:R_0603_1608Metric",
      "missing_properties": ["PartNumber"],
      "existing_properties": {
        "Tolerance": "1%",
        "Manufacturer": "Yageo"
      }
    }
  ]
}
```

### Workflow 3: Recursive Directory Scan

```bash
# Scan entire project tree
kicad-sch audit-bom \
  --path ~/AlembicGuitars/designs \
  --recursive \
  --required-properties PartNumber,Tolerance \
  --output full_audit.csv
```

### Workflow 4: Filtered Scan (Specific Component Types)

```bash
# Only audit resistors and capacitors
kicad-sch audit-bom \
  --required-properties PartNumber \
  --filter-lib-id "Device:R,Device:C" \
  --output passive_audit.csv
```

---

## Implementation Steps

### Phase 1: Core Scanning Logic (kicad-sch-api)

**Files to create:**
- `kicad_sch_api/cli/audit_bom.py` - Main audit logic
- `tests/unit/cli/test_audit_bom.py` - Unit tests

**Implementation breakdown:**

#### Step 1.1: Schema Definition
```python
# Define audit result data structures
@dataclass
class ComponentAuditResult:
    schematic_path: Path
    reference: str
    value: str
    footprint: str
    lib_id: str
    missing_properties: List[str]
    existing_properties: Dict[str, str]

@dataclass
class BOMAuditReport:
    summary: Dict[str, Any]
    issues: List[ComponentAuditResult]
```

#### Step 1.2: Single Schematic Auditor
```python
def audit_schematic(
    schematic_path: Path,
    required_properties: List[str],
    filter_lib_ids: Optional[List[str]] = None
) -> List[ComponentAuditResult]:
    """Audit single schematic for missing properties."""
    # Load schematic
    # Iterate components
    # Check for missing properties
    # Return results
```

#### Step 1.3: Directory Scanner
```python
def audit_directory(
    path: Path,
    required_properties: List[str],
    recursive: bool = False,
    filter_lib_ids: Optional[List[str]] = None
) -> BOMAuditReport:
    """Scan directory for schematics and audit all."""
    # Find all .kicad_sch files
    # Audit each schematic
    # Aggregate results
    # Generate summary statistics
```

#### Step 1.4: Report Generators
```python
def generate_csv_report(results: BOMAuditReport, output: Path):
    """Generate CSV report."""

def generate_json_report(results: BOMAuditReport, output: Path):
    """Generate JSON report."""
```

#### Step 1.5: CLI Interface
```python
# In kicad_sch_api/cli/audit_bom.py
def audit_bom(
    path: Path = Path.cwd(),
    required_properties: str = "PartNumber",  # Comma-separated
    recursive: bool = False,
    filter_lib_id: Optional[str] = None,
    output: Optional[Path] = None,
    output_format: str = "csv",  # csv or json
    exclude_dnp: bool = False,
):
    """Audit schematics for missing BOM properties."""
```

### Phase 2: Testing Strategy

**Test Plan:**
1. **Unit tests** - Test individual functions
2. **Integration tests** - Test full audit workflow
3. **Reference tests** - Test against real KiCad schematics

**Test fixtures needed:**
```
tests/reference_kicad_projects/bom_audit/
├── complete_bom.kicad_sch          # All properties present
├── missing_partnumber.kicad_sch    # Missing PartNumber on some components
├── mixed_compliance.kicad_sch      # Some complete, some missing
└── empty.kicad_sch                 # No components
```

**Example test:**
```python
def test_audit_missing_properties():
    """Test auditing schematic with missing properties."""
    result = audit_schematic(
        Path("tests/reference_kicad_projects/bom_audit/missing_partnumber.kicad_sch"),
        required_properties=["PartNumber"]
    )

    # Should find 3 components missing PartNumber
    assert len(result) == 3
    assert result[0].reference == "R1"
    assert "PartNumber" in result[0].missing_properties
    assert result[0].value == "10k"
    assert result[0].footprint == "Resistor_SMD:R_0603_1608Metric"
```

### Phase 3: CLI Integration (kicad-sch-api)

Register command in kicad-sch-api CLI:
```python
# In kicad_sch_api/cli/__init__.py
from .audit_bom import audit_bom

# Add to CLI subcommands
```

### Phase 4: circuit-synth Wrapper Layer

**Files to create:**
- `src/circuit_synth/kicad/bom_auditor.py` - Wrapper class
- `tests/unit/test_bom_auditor.py` - Unit tests for wrapper

**Implementation:**

```python
# src/circuit_synth/kicad/bom_auditor.py
"""
BOM property auditor for circuit-synth.

Wraps kicad-sch-api's audit_bom functionality with circuit-synth
friendly API and additional convenience methods.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import kicad_sch_api as ksa


class BOMPropertyAuditor:
    """
    Audit KiCad schematics for missing component properties.

    Wraps kicad-sch-api audit functionality with convenient
    interface for circuit-synth users.
    """

    def __init__(
        self,
        required_properties: List[str],
        include_properties: Optional[List[str]] = None,
        exclude_dnp: bool = False,
        filter_lib_ids: Optional[List[str]] = None
    ):
        """
        Initialize BOM property auditor.

        Args:
            required_properties: Properties that must be present
            include_properties: Additional properties to include in report
            exclude_dnp: Skip Do-Not-Populate components
            filter_lib_ids: Only audit specific component types
        """
        self.required_properties = required_properties
        self.include_properties = include_properties or []
        self.exclude_dnp = exclude_dnp
        self.filter_lib_ids = filter_lib_ids

    def audit_directory(
        self,
        path: Path,
        recursive: bool = True
    ) -> "BOMPropertyAuditReport":
        """
        Audit directory for schematics with missing properties.

        Args:
            path: Directory to scan
            recursive: Scan subdirectories

        Returns:
            BOMPropertyAuditReport with results
        """
        # Delegate to kicad-sch-api
        results = ksa.audit_bom(
            path=Path(path),
            required_properties=self.required_properties,
            recursive=recursive,
            filter_lib_ids=self.filter_lib_ids,
            exclude_dnp=self.exclude_dnp
        )

        return BOMPropertyAuditReport(results)

    def audit_schematic(
        self,
        schematic_path: Path
    ) -> "BOMPropertyAuditReport":
        """Audit single schematic file."""
        # Delegate to kicad-sch-api
        results = ksa.audit_bom(
            path=schematic_path,
            required_properties=self.required_properties,
            filter_lib_ids=self.filter_lib_ids,
            exclude_dnp=self.exclude_dnp
        )

        return BOMPropertyAuditReport(results)


class BOMPropertyAuditReport:
    """
    Report of BOM property audit results.

    Provides convenient access to audit findings and export methods.
    """

    def __init__(self, results: ksa.BOMAuditReport):
        """Initialize from kicad-sch-api results."""
        self._results = results

    @property
    def issues(self) -> List[ksa.ComponentAuditResult]:
        """List of components with missing properties."""
        return self._results.issues

    @property
    def summary(self) -> Dict[str, Any]:
        """Summary statistics."""
        return self._results.summary

    @property
    def compliance_percentage(self) -> float:
        """Percentage of components with all required properties."""
        return self.summary.get("compliance_percentage", 0.0)

    @property
    def total_components(self) -> int:
        """Total number of components scanned."""
        return self.summary.get("total_components", 0)

    @property
    def components_with_issues(self) -> int:
        """Number of components missing properties."""
        return self.summary.get("components_with_issues", 0)

    def to_csv(self, output: Path) -> Path:
        """Export report to CSV."""
        ksa.generate_csv_report(self._results, output)
        return output

    def to_json(self, output: Path) -> Path:
        """Export report to JSON."""
        ksa.generate_json_report(self._results, output)
        return output

    def print_summary(self):
        """Print summary to console."""
        print(f"\n{'='*60}")
        print(f"BOM Property Audit Report")
        print(f"{'='*60}")
        print(f"Total schematics: {self.summary.get('total_schematics', 0)}")
        print(f"Total components: {self.total_components}")
        print(f"Components with issues: {self.components_with_issues}")
        print(f"Compliance: {self.compliance_percentage:.1f}%")
        print(f"{'='*60}\n")
```

**Tests:**
```python
# tests/unit/test_bom_auditor.py
"""Test BOM property auditor wrapper."""

import pytest
from pathlib import Path
from circuit_synth.kicad.bom_auditor import BOMPropertyAuditor


def test_auditor_initialization():
    """Test auditor initializes with correct properties."""
    auditor = BOMPropertyAuditor(
        required_properties=["PartNumber", "Manufacturer"],
        exclude_dnp=True
    )

    assert auditor.required_properties == ["PartNumber", "Manufacturer"]
    assert auditor.exclude_dnp is True


def test_audit_directory_delegates_to_kicad_sch_api(tmp_path, monkeypatch):
    """Test that audit_directory calls kicad-sch-api correctly."""
    # This test would mock ksa.audit_bom to verify delegation
    pass


def test_report_provides_convenience_properties():
    """Test BOMPropertyAuditReport exposes useful properties."""
    # Mock results and verify report interface
    pass
```

---

## Debugging Strategy

### Strategic Logging Points

```python
# CYCLE 1: Verify schematic loading
logger.debug(f"CYCLE 1: Loading schematic {schematic_path}")
logger.debug(f"CYCLE 1: Found {len(sch.components)} components")

# CYCLE 2: Verify property extraction
for component in sch.components.all():
    logger.debug(f"CYCLE 2: Component {component.reference}")
    logger.debug(f"CYCLE 2: Properties: {component.properties.keys()}")

# CYCLE 3: Verify missing property detection
logger.debug(f"CYCLE 3: Required properties: {required_properties}")
logger.debug(f"CYCLE 3: Missing for {ref}: {missing}")

# CYCLE 4: Verify report generation
logger.debug(f"CYCLE 4: Total issues found: {len(results.issues)}")
logger.debug(f"CYCLE 4: Summary: {results.summary}")
```

### Expected Iterative Cycles (Target: 10-15 cycles)

1. **Cycles 1-3**: Understand component property API
2. **Cycles 4-6**: Implement missing property detection
3. **Cycles 7-9**: Build report generation
4. **Cycles 10-12**: Add directory scanning
5. **Cycles 13-15**: Polish CLI interface and error handling

---

## API Design

### Layer 1: kicad-sch-api (Core Implementation)

**Python API:**
```python
import kicad_sch_api as ksa

# Programmatic audit
results = ksa.audit_bom(
    path=Path("~/designs"),
    required_properties=["PartNumber", "Manufacturer"],
    recursive=True,
    filter_lib_ids=["Device:R", "Device:C"]
)

print(f"Found {len(results.issues)} components with missing properties")
for issue in results.issues:
    print(f"{issue.schematic_path}:{issue.reference} missing {issue.missing_properties}")
```

**CLI:**
```bash
# Simple usage
kicad-sch audit-bom --required-properties PartNumber

# Advanced usage
kicad-sch audit-bom \
  --path ~/designs \
  --recursive \
  --required-properties PartNumber,Manufacturer,Tolerance \
  --filter-lib-id "Device:R,Device:C" \
  --output-format json \
  --output audit_report.json \
  --exclude-dnp
```

### Layer 2: circuit-synth Wrapper

**Python API:**
```python
from circuit_synth.kicad.bom_auditor import BOMPropertyAuditor

# Audit existing schematics
auditor = BOMPropertyAuditor(
    required_properties=["PartNumber", "Manufacturer"]
)

# Scan directory
results = auditor.audit_directory(
    path="~/AlembicGuitars/designs",
    recursive=True
)

# Generate report
results.to_csv("bom_cleanup.csv")
results.to_json("bom_cleanup.json")

# Print summary
print(f"Compliance: {results.compliance_percentage:.1f}%")
print(f"Issues found: {len(results.issues)}")
```

**CLI Option 1 - New command:**
```bash
# If we add a dedicated circuit-synth command
circuit-synth audit-bom \
  --path ~/designs \
  --required-properties PartNumber \
  --output audit.csv
```

**CLI Option 2 - Extend existing command:**
```bash
# Or extend existing BOM functionality (if applicable)
# TBD based on circuit-synth CLI structure
```

---

## Output Format Specifications

### CSV Format
```csv
Schematic,Reference,Value,Footprint,LibID,MissingProperties,<ExistingProperty1>,<ExistingProperty2>,...
designs/amp.kicad_sch,R1,10k,Resistor_SMD:R_0603_1608Metric,Device:R,PartNumber,1%,Yageo
```

**CSV Columns:**
- `Schematic`: Relative path to schematic file
- `Reference`: Component reference (R1, C5, U3, etc.)
- `Value`: Component value
- `Footprint`: Footprint string
- `LibID`: Library ID (Device:R, etc.)
- `MissingProperties`: Comma-separated list of missing properties
- Additional columns for common properties (Tolerance, Manufacturer, etc.)

### JSON Format
```json
{
  "summary": {
    "scan_path": "/Users/username/designs",
    "scan_date": "2025-11-18T10:30:00",
    "total_schematics": 12,
    "total_components": 487,
    "components_with_issues": 143,
    "compliance_percentage": 70.6,
    "required_properties": ["PartNumber", "Manufacturer"]
  },
  "issues": [
    {
      "schematic": "designs/amp_v1/amp.kicad_sch",
      "reference": "R1",
      "value": "10k",
      "footprint": "Resistor_SMD:R_0603_1608Metric",
      "lib_id": "Device:R",
      "missing_properties": ["PartNumber"],
      "existing_properties": {
        "Tolerance": "1%",
        "Manufacturer": "Yageo",
        "Value": "10k"
      }
    }
  ]
}
```

---

## Configuration Options

### Required CLI Arguments
- `--required-properties <prop1,prop2,...>` - Properties to check for (comma-separated)

### Optional CLI Arguments
- `--path <directory>` - Directory to scan (default: current directory)
- `--recursive` - Scan subdirectories recursively (default: false)
- `--output <file>` - Output file path (default: `bom_audit_report.csv`)
- `--output-format <csv|json>` - Report format (default: csv)
- `--filter-lib-id <lib1,lib2,...>` - Only audit specific component types
- `--exclude-dnp` - Exclude Do-Not-Populate components
- `--include-properties <prop1,prop2,...>` - Additional properties to include in report

### Configuration File Support (Future Enhancement)
```yaml
# .bom-audit.yml
required_properties:
  - PartNumber
  - Manufacturer
  - Tolerance

include_properties:
  - Datasheet
  - Supplier

exclude_lib_ids:
  - "Connector:*"
  - "Mechanical:*"
```

---

## Success Criteria

Feature is "done" when:

- [ ] Can scan single schematic for missing properties
- [ ] Can scan directory recursively for all schematics
- [ ] Generates accurate CSV reports
- [ ] Generates accurate JSON reports
- [ ] Includes summary statistics in reports
- [ ] CLI interface is intuitive and well-documented
- [ ] All tests passing (unit + integration + reference tests)
- [ ] Test coverage >80%
- [ ] Documentation added to kicad-sch-api README
- [ ] Example usage in docs/RECIPES.md

---

## Example User Workflows (Complete)

### Workflow A: Using circuit-synth (Recommended for circuit-synth users)

**Scenario:** Alembic Guitars has 47 schematics across multiple projects, needs to find all components missing PartNumber property.

```python
# workflow_audit.py
from pathlib import Path
from circuit_synth.kicad.bom_auditor import BOMPropertyAuditor

# Step 1: Configure auditor
auditor = BOMPropertyAuditor(
    required_properties=["PartNumber"],
    include_properties=["Tolerance", "Manufacturer"],  # Include in report for context
    exclude_dnp=True  # Skip DNP components
)

# Step 2: Run audit
results = auditor.audit_directory(
    path=Path("~/AlembicGuitars/designs"),
    recursive=True
)

# Step 3: Print summary
results.print_summary()
# Output:
# ============================================================
# BOM Property Audit Report
# ============================================================
# Total schematics: 47
# Total components: 1,247
# Components with issues: 312
# Compliance: 75.0%
# ============================================================

# Step 4: Export detailed report
results.to_csv("bom_cleanup_report.csv")
results.to_json("bom_cleanup_report.json")

print(f"Report exported: bom_cleanup_report.csv")
print(f"Use this report to systematically add PartNumber properties")

# Step 5: After adding properties, re-run to verify
final_results = auditor.audit_directory(
    path=Path("~/AlembicGuitars/designs"),
    recursive=True
)

final_results.print_summary()
# Output:
# Compliance: 100.0%
# All components have required properties!
```

### Workflow B: Using kicad-sch-api CLI (Direct)

**For users who prefer command-line tools:**

```bash
# Step 1: Run initial audit
cd ~/AlembicGuitars
kicad-sch audit-bom \
  --path designs \
  --recursive \
  --required-properties PartNumber \
  --output bom_cleanup_report.csv

# Output:
# Scanning designs/ recursively...
# Found 47 schematics
# Scanned 1,247 components
# Found 312 components missing required properties
# Compliance: 75.0%
# Report written to: bom_cleanup_report.csv

# Step 2: Open CSV in Excel/LibreOffice
open bom_cleanup_report.csv

# Step 3: Use report to systematically add PartNumber properties
# - Group by value/footprint to find common parts
# - Look up part numbers in supplier catalogs
# - Add properties in KiCad

# Step 4: Re-run audit to verify completion
kicad-sch audit-bom \
  --path designs \
  --recursive \
  --required-properties PartNumber \
  --output bom_cleanup_final.csv

# Output:
# Compliance: 100.0%
# All components have required properties!
```

### Workflow C: Integration into circuit-synth scripts

**For automated BOM validation in circuit generation:**

```python
from circuit_synth.core import circuit, Component
from circuit_synth.kicad.bom_auditor import BOMPropertyAuditor

# Generate circuit (existing code)
@circuit(name="PowerSupply")
def power_supply():
    # ... circuit definition ...
    return locals()

circ = power_supply()
circ.generate_kicad_project(name="power_supply")

# Audit the generated schematic
auditor = BOMPropertyAuditor(
    required_properties=["PartNumber", "Manufacturer"]
)

results = auditor.audit_schematic(
    Path("power_supply/power_supply.kicad_sch")
)

# Validate compliance before releasing design
if results.compliance_percentage < 100:
    print(f"WARNING: BOM compliance is {results.compliance_percentage:.1f}%")
    results.to_csv("missing_properties.csv")
    raise ValueError("Design has components missing required properties!")
else:
    print("✓ All components have required properties")
```

---

## Future Enhancements (Out of Scope for MVP)

1. **Property value validation** - Check if PartNumber follows company format
2. **Part database integration** - Cross-reference against local part database
3. **Auto-fix suggestions** - Suggest common part numbers based on value/footprint
4. **HTML report generation** - Interactive report with filtering/sorting
5. **Diff mode** - Compare two audit reports to track cleanup progress
6. **CI/CD integration** - Fail builds if compliance drops below threshold
7. **Batch property updates** - Apply property changes from CSV file

---

## Open Questions for User

1. **Property names:** What exact property name(s) do you use? "PartNumber", "CompanyPartNumber", "MPN"?
2. **Report format preference:** CSV or JSON? Or both?
3. **Filtering needs:** Do you want to exclude certain component types (connectors, mounting holes)?
4. **Additional properties:** Beyond PartNumber, what other properties would be useful in the report? (Tolerance, Manufacturer, Datasheet?)
5. **Output destination:** Command-line tool OK, or do you need GUI/web interface?

---

## Technical Notes

### Architecture Decision: Two-Layer Approach

**Layer 1: kicad-sch-api (Core Implementation)**

Core implementation lives in kicad-sch-api because:
- This is schematic file analysis, not circuit generation
- Uses existing component property APIs in kicad-sch-api
- Useful for ANY KiCad user, not just circuit-synth users
- Fits with existing BOM export CLI (`kicad-sch bom`)
- No dependency on circuit-synth's circuit definition DSL
- Can be used standalone for any KiCad project

**Layer 2: circuit-synth (Wrapper)**

Wrapper layer in circuit-synth provides:
- Pythonic, circuit-synth-friendly API
- Convenient interface for circuit-synth users
- Integration with circuit-synth workflows
- Optional validation hooks for generated circuits
- Consistent with existing pattern (circuit-synth wraps kicad-sch-api)

**Benefits of two-layer approach:**
1. Core functionality available to all KiCad users (via kicad-sch-api)
2. Convenient access for circuit-synth users (via wrapper)
3. Clear separation of concerns
4. No circular dependencies
5. Both repos benefit from the feature

### Performance Considerations

- Scanning 50 schematics with 1000+ components should complete in <10 seconds
- Use kicad-sch-api's component iteration (`for comp in sch.components.all()`)
- Avoid re-parsing files - load once, scan once
- Consider progress bars for large scans (use `rich` library)

---

## Timeline Estimate

**Conservative estimate: 6-8 hours across 15-20 iterative cycles**

**Layer 1: kicad-sch-api (Core) - 4-5 hours**
- **Planning & PRD:** 1 hour (complete)
- **Core implementation:** 2-3 hours (10 cycles)
  - Cycle 1-3: Component property extraction
  - Cycle 4-6: Missing property detection
  - Cycle 7-9: Report generation
  - Cycle 10-12: Directory scanning
- **Testing:** 1 hour (3 cycles)
  - Create test fixtures
  - Write unit tests
  - Write integration tests
- **Documentation:** 30 min (update kicad-sch-api README)

**Layer 2: circuit-synth (Wrapper) - 2-3 hours**
- **Wrapper implementation:** 1 hour (3-5 cycles)
  - BOMPropertyAuditor class
  - BOMPropertyAuditReport class
  - Delegation to kicad-sch-api
- **Testing:** 1 hour (2-3 cycles)
  - Unit tests for wrapper
  - Integration tests
- **Documentation:** 30 min (update circuit-synth docs)

**Total: 6-8 hours, could be split across 2-3 sessions**
- Session 1: kicad-sch-api core (4-5 hours)
- Session 2: circuit-synth wrapper (2-3 hours)

**Implementation Order (Dependencies):**
1. **First:** Implement and test kicad-sch-api core
2. **Second:** Implement circuit-synth wrapper (depends on kicad-sch-api)
3. **Note:** Must update kicad-sch-api dependency in circuit-synth after Layer 1 is complete

---

## Implementation Strategy

### Dependency Flow

```
┌─────────────────────────────────────┐
│  Layer 1: kicad-sch-api             │
│  ───────────────────────────────    │
│  • audit_bom() function             │
│  • ComponentAuditResult dataclass   │
│  • BOMAuditReport dataclass         │
│  • generate_csv_report()            │
│  • generate_json_report()           │
│  • CLI: kicad-sch audit-bom         │
└─────────────────────────────────────┘
                 ▲
                 │ imports & delegates
                 │
┌─────────────────────────────────────┐
│  Layer 2: circuit-synth             │
│  ───────────────────────────────    │
│  • BOMPropertyAuditor (wrapper)     │
│  • BOMPropertyAuditReport (wrapper) │
│  • Convenience methods              │
│  • Optional CLI integration         │
└─────────────────────────────────────┘
```

### Development Workflow

**Phase 1: kicad-sch-api (Required First)**
1. Implement core audit logic in kicad-sch-api
2. Write comprehensive tests
3. Verify functionality standalone
4. Release new version of kicad-sch-api (e.g., 0.x.y)
5. ✓ Core functionality complete and tested

**Phase 2: circuit-synth (Depends on Phase 1)**
1. Update circuit-synth dependency: `kicad-sch-api>=0.x.y`
2. Implement BOMPropertyAuditor wrapper
3. Implement BOMPropertyAuditReport wrapper
4. Write tests (can mock kicad-sch-api during development)
5. Integration test with actual kicad-sch-api
6. ✓ Wrapper complete and tested

---

## Test Strategy (Detailed)

### Test Fixtures

Complete test fixture specifications in [`TEST_FIXTURES_BOM_AUDIT.md`](TEST_FIXTURES_BOM_AUDIT.md).

**6 realistic test schematics representing Alembic Guitars use cases:**

| Fixture | Components | Compliance | Purpose |
|---------|------------|------------|---------|
| amp_power_supply.kicad_sch | 8 | 100% | Perfect compliance - all properties present |
| vintage_preamp.kicad_sch | 12 | 0% | Legacy design - no properties |
| overdrive_pedal.kicad_sch | 15 | 60% | Partial migration - passives done, ICs pending |
| di_box.kicad_sch | 10 | 70% | Edge cases - DNP components, connectors |
| clean_boost.kicad_sch | 9 | 55% | Property variations - MPN vs PartNumber |
| empty_test.kicad_sch | 0 | N/A | Edge case - empty schematic |

**Total coverage:** 54 components across 6 schematics

### Test Generation

Test fixtures generated using circuit-synth Python scripts:
- `tests/fixtures/bom_audit/01_generate_amp_power_supply.py`
- `tests/fixtures/bom_audit/02_generate_vintage_preamp.py`
- `tests/fixtures/bom_audit/03_generate_overdrive_pedal.py`
- `tests/fixtures/bom_audit/04_generate_di_box.py`
- `tests/fixtures/bom_audit/05_generate_clean_boost.py`
- `tests/fixtures/bom_audit/06_generate_empty_test.py`

**Why generate programmatically:**
- Reproducible test fixtures
- Precise control over properties
- Easy to regenerate if needed
- Documents expected component structure
- Consistent with circuit-synth workflow

### Test Implementation

Test files using generated fixtures:

**Unit tests (kicad-sch-api):**
```
tests/unit/cli/test_audit_bom.py
├── TestBOMAuditCore
│   ├── test_perfect_compliance (amp_power_supply)
│   ├── test_zero_compliance (vintage_preamp)
│   ├── test_partial_compliance (overdrive_pedal)
│   ├── test_dnp_exclusion (di_box)
│   ├── test_component_type_filtering (overdrive_pedal)
│   ├── test_property_variations (clean_boost)
│   └── test_empty_schematic (empty_test)
├── TestBOMAuditReports
│   ├── test_csv_report_format
│   └── test_json_report_format
└── TestBOMAuditDirectory
    ├── test_recursive_scan
    └── test_non_recursive_scan
```

**Integration tests (circuit-synth):**
```
tests/integration/test_bom_auditor_integration.py
├── TestBOMPropertyAuditor
│   ├── test_auditor_initialization
│   ├── test_audit_directory
│   └── test_audit_schematic
└── TestBOMPropertyAuditReport
    ├── test_report_properties
    ├── test_to_csv
    ├── test_to_json
    └── test_print_summary
```

---

## Related Work

### Existing Tools
- `kicad-cli sch export bom` - Exports BOM but doesn't validate properties
- circuit-synth's `generate_bom()` - Exports BOM for generated circuits
- kicad-sch-api's `export_bom()` - CLI wrapper for kicad-cli BOM export

### This Tool's Unique Value
- **Validation-focused** rather than export-focused
- **Multi-schematic scanning** across entire project trees
- **Property compliance reporting** with detailed missing property tracking
- **Audit trail** for systematic BOM cleanup projects
