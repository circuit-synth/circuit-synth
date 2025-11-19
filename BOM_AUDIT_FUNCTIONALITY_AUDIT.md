# BOM Audit Feature - kicad-sch-api Functionality Audit

**Date:** 2025-11-18
**Purpose:** Verify we have all necessary functionality in kicad-sch-api to implement BOM property audit feature.

---

## Required Functionality Checklist

### ✅ AVAILABLE: Component Iteration

**Need:** Iterate over all components in a schematic

**Available in kicad-sch-api:**
```python
# In kicad_sch_api/collections/components.py
class ComponentCollection:
    def all(self) -> Iterator[Component]:
        """Iterate over all components."""
        for comp_data in self._items:
            yield Component(comp_data, self)
```

**Usage:**
```python
sch = ksa.Schematic.load("design.kicad_sch")
for component in sch.components.all():
    print(f"{component.reference}: {component.value}")
```

**Status:** ✅ Ready to use

---

### ✅ AVAILABLE: Property Access

**Need:** Read component properties dictionary

**Available in kicad-sch-api:**
```python
# In kicad_sch_api/collections/components.py
class Component:
    @property
    def properties(self) -> Dict[str, str]:
        """Dictionary of all component properties."""
        return self._data.properties

    def get_property(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get property value by name."""
        return self._data.properties.get(name, default)
```

**Usage:**
```python
for component in sch.components.all():
    part_num = component.get_property("PartNumber")
    if not part_num:
        print(f"{component.reference} missing PartNumber")

    # Or access dict directly
    all_props = component.properties
    if "PartNumber" not in all_props:
        print(f"{component.reference} missing PartNumber")
```

**Status:** ✅ Ready to use

---

### ✅ AVAILABLE: Basic Component Metadata

**Need:** Access reference, value, footprint, lib_id

**Available in kicad-sch-api:**
```python
# In kicad_sch_api/collections/components.py
class Component:
    @property
    def reference(self) -> str:
        """Component reference (e.g., 'R1')."""
        return self._data.reference

    @property
    def value(self) -> str:
        """Component value (e.g., '10k')."""
        return self._data.value

    @property
    def footprint(self) -> Optional[str]:
        """Component footprint."""
        return self._data.footprint

    @property
    def lib_id(self) -> str:
        """Library ID (e.g., 'Device:R')."""
        return self._data.lib_id
```

**Usage:**
```python
for component in sch.components.all():
    result = {
        "reference": component.reference,
        "value": component.value,
        "footprint": component.footprint,
        "lib_id": component.lib_id,
    }
```

**Status:** ✅ Ready to use

---

### ✅ AVAILABLE: DNP (Do Not Populate) Status

**Need:** Check if component is marked "Do Not Populate"

**Available in kicad-sch-api:**
```python
# In kicad_sch_api/collections/components.py
class Component:
    @property
    def in_bom(self) -> bool:
        """Whether component appears in bill of materials."""
        return self._data.in_bom
```

**Usage:**
```python
for component in sch.components.all():
    if not component.in_bom:
        print(f"{component.reference} is DNP (Do Not Populate)")
        continue  # Skip if --exclude-dnp flag set
```

**Note:** `in_bom=False` means the component is DNP

**Status:** ✅ Ready to use

---

### ✅ AVAILABLE: Schematic Loading

**Need:** Load .kicad_sch files from disk

**Available in kicad-sch-api:**
```python
# In kicad_sch_api/core/schematic.py
class Schematic:
    @staticmethod
    def load(path: Union[str, Path]) -> "Schematic":
        """Load schematic from file."""
        # ... implementation
```

**Usage:**
```python
sch = ksa.Schematic.load("/path/to/design.kicad_sch")
```

**Status:** ✅ Ready to use

---

### ✅ AVAILABLE: File System Traversal

**Need:** Find all .kicad_sch files in directory tree

**Not built-in, but trivial Python:**
```python
from pathlib import Path

def find_schematics(directory: Path, recursive: bool = True) -> list[Path]:
    """Find all .kicad_sch files in directory."""
    if recursive:
        return list(directory.rglob("*.kicad_sch"))
    else:
        return list(directory.glob("*.kicad_sch"))
```

**Status:** ✅ Trivial to implement (standard library)

---

### ✅ AVAILABLE: Component Filtering by lib_id

**Need:** Filter components by library ID (e.g., only Device:R)

**Available in kicad-sch-api:**
```python
# In kicad_sch_api/collections/components.py
class ComponentCollection:
    def filter(self, **criteria) -> List[Component]:
        """Filter components by criteria."""
        # Can filter by lib_id, value, etc.
```

**Usage:**
```python
# Get only resistors
resistors = sch.components.filter(lib_id="Device:R")

# Or manually filter
for component in sch.components.all():
    if component.lib_id == "Device:R":
        # Check this component
        pass
```

**Status:** ✅ Ready to use

---

## Missing Functionality Analysis

### ❓ UNCLEAR: Property Iteration

**Need:** Iterate over all property keys efficiently

**Available:**
```python
for component in sch.components.all():
    for prop_name, prop_value in component.properties.items():
        # Check properties
        pass
```

**Status:** ✅ Available via dict.items()

---

### ⚠️ TO IMPLEMENT: CSV Report Generation

**Need:** Generate CSV reports from audit results

**Status:** ❌ Not in kicad-sch-api, will implement in audit_bom.py

**Implementation plan:**
```python
import csv
from pathlib import Path

def generate_csv_report(results: BOMAuditReport, output: Path):
    """Generate CSV report from audit results."""
    with open(output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Schematic",
            "Reference",
            "Value",
            "Footprint",
            "LibID",
            "MissingProperties",
            # Plus existing properties as columns
        ])
        writer.writeheader()

        for issue in results.issues:
            row = {
                "Schematic": str(issue.schematic_path),
                "Reference": issue.reference,
                "Value": issue.value,
                "Footprint": issue.footprint,
                "LibID": issue.lib_id,
                "MissingProperties": ",".join(issue.missing_properties),
            }
            # Add existing properties as columns
            for prop, value in issue.existing_properties.items():
                row[prop] = value

            writer.writerow(row)
```

**Complexity:** Low (standard library)

---

### ⚠️ TO IMPLEMENT: JSON Report Generation

**Need:** Generate JSON reports from audit results

**Status:** ❌ Not in kicad-sch-api, will implement in audit_bom.py

**Implementation plan:**
```python
import json
from pathlib import Path

def generate_json_report(results: BOMAuditReport, output: Path):
    """Generate JSON report from audit results."""
    data = {
        "summary": results.summary,
        "issues": [
            {
                "schematic": str(issue.schematic_path),
                "reference": issue.reference,
                "value": issue.value,
                "footprint": issue.footprint,
                "lib_id": issue.lib_id,
                "missing_properties": issue.missing_properties,
                "existing_properties": issue.existing_properties,
            }
            for issue in results.issues
        ]
    }

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)
```

**Complexity:** Low (standard library)

---

### ⚠️ TO IMPLEMENT: Data Structures

**Need:** ComponentAuditResult and BOMAuditReport dataclasses

**Status:** ❌ Not in kicad-sch-api, will implement in audit_bom.py

**Implementation plan:**
```python
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

@dataclass
class ComponentAuditResult:
    """Result of auditing a single component."""
    schematic_path: Path
    reference: str
    value: str
    footprint: str
    lib_id: str
    missing_properties: List[str]
    existing_properties: Dict[str, str]

@dataclass
class BOMAuditReport:
    """Complete audit report for one or more schematics."""
    summary: Dict[str, Any]
    issues: List[ComponentAuditResult]
```

**Complexity:** Trivial (dataclasses)

---

## Implementation Dependencies

### Files to Create in kicad-sch-api

1. **`kicad_sch_api/cli/audit_bom.py`** - Main audit logic
   - `audit_schematic()` - Audit single schematic
   - `audit_directory()` - Scan directory for schematics
   - `generate_csv_report()` - CSV export
   - `generate_json_report()` - JSON export
   - `audit_bom()` - CLI entry point

2. **No changes needed to existing kicad-sch-api code** ✅
   - All required functionality exists
   - Just need to use it correctly

---

## Summary

### What We Have ✅

- ✅ Component iteration (`sch.components.all()`)
- ✅ Property access (`component.properties`, `component.get_property()`)
- ✅ Component metadata (reference, value, footprint, lib_id)
- ✅ DNP status (`component.in_bom`)
- ✅ Schematic loading (`Schematic.load()`)
- ✅ Component filtering by lib_id

### What We Need to Implement ⚠️

- ⚠️ `audit_schematic()` function
- ⚠️ `audit_directory()` function
- ⚠️ CSV report generator
- ⚠️ JSON report generator
- ⚠️ Data structures (ComponentAuditResult, BOMAuditReport)
- ⚠️ CLI command registration

### Complexity Assessment

**Overall complexity: LOW**

- All core functionality exists in kicad-sch-api
- Implementation is primarily:
  - Iterating over components
  - Checking if properties exist
  - Collecting results
  - Generating reports (CSV/JSON with stdlib)

**Estimated implementation time:**
- Core logic: 1-2 hours
- Tests: 1-2 hours
- Total: 2-4 hours for kicad-sch-api layer

---

## Next Steps

1. ✅ Test fixtures generated (6 schematics, 54 components)
2. ⏳ Implement kicad-sch-api core:
   - Create `kicad_sch_api/cli/audit_bom.py`
   - Implement data structures
   - Implement `audit_schematic()`
   - Implement `audit_directory()`
   - Implement CSV/JSON generators
   - Add CLI command
   - Write tests using fixtures
3. ⏳ Implement circuit-synth wrapper:
   - Create `BOMPropertyAuditor` class
   - Create `BOMPropertyAuditReport` class
   - Write wrapper tests
4. ⏳ Documentation & release

---

## Test Strategy Verification

### Can We Test Everything? ✅ YES

Using our generated fixtures, we can test:

1. **Perfect compliance** (amp_power_supply.kicad_sch)
   - Load schematic ✅
   - Iterate components ✅
   - Check properties ✅
   - Verify empty issues list ✅

2. **Zero compliance** (vintage_preamp.kicad_sch)
   - All components flagged ✅
   - Properties exist but PartNumber missing ✅

3. **Partial compliance** (overdrive_pedal.kicad_sch)
   - Some have, some don't ✅
   - Group by component type ✅

4. **DNP handling** (di_box.kicad_sch)
   - Check `component.in_bom` ✅
   - Exclude DNP from count ✅

5. **Property variations** (clean_boost.kicad_sch)
   - Check multiple property names ✅
   - MPN vs PartNumber vs CompanyPN ✅

6. **Empty schematic** (empty_test.kicad_sch)
   - No crash on empty ✅
   - Proper handling ✅

**All test scenarios are covered by available functionality!**

---

## Conclusion

**✅ kicad-sch-api HAS ALL REQUIRED FUNCTIONALITY**

We can implement the entire BOM audit feature using existing kicad-sch-api capabilities. No modifications to kicad-sch-api core are needed - only new functionality in `cli/audit_bom.py`.

**Ready to proceed with implementation!**
