# BOM Audit Test Fixtures Design

**Purpose:** Realistic test schematics representing Alembic Guitars' design library, covering edge cases and migration scenarios.

---

## Test Fixture Overview

| Schematic | Description | Components | Compliance | Purpose |
|-----------|-------------|------------|------------|---------|
| `amp_power_supply.kicad_sch` | Modern design, fully compliant | 8 | 100% | Ideal state - all properties present |
| `vintage_preamp.kicad_sch` | Legacy design, no properties | 12 | 0% | Worst case - needs full migration |
| `overdrive_pedal.kicad_sch` | Partially migrated | 15 | 60% | Real migration scenario |
| `di_box.kicad_sch` | Edge cases (DNP, connectors) | 10 | 70% | Test filtering logic |
| `clean_boost.kicad_sch` | Property variations | 9 | 55% | Test property name variations |
| `empty_test.kicad_sch` | No components | 0 | N/A | Edge case - empty schematic |

**Total: 6 test schematics, 54 components**

---

## Fixture 1: amp_power_supply.kicad_sch

**Scenario:** Modern design (2024), fully compliant with company standards

**Components:**

| Ref | Value | Footprint | LibID | PartNumber | Manufacturer | Tolerance | Notes |
|-----|-------|-----------|-------|------------|--------------|-----------|-------|
| U1 | AMS1117-3.3 | SOT-223 | Regulator_Linear:AMS1117-3.3 | AMS1117-3.3 | Advanced Monolithic | - | 3.3V regulator |
| U2 | LM7815 | TO-220-3 | Regulator_Linear:LM7815_TO220 | LM7815CT | Texas Instruments | - | +15V regulator |
| U3 | LM7915 | TO-220-3 | Regulator_Linear:LM7915_TO220 | LM7915CT | Texas Instruments | - | -15V regulator |
| C1 | 100uF | C_1206 | Device:C_Polarized | GRM31CR61E107KA12L | Murata | 10% | Input filter |
| C2 | 100uF | C_1206 | Device:C_Polarized | GRM31CR61E107KA12L | Murata | 10% | Output filter |
| C3 | 10uF | C_0805 | Device:C | GRM21BR61E106KA73L | Murata | 10% | Bypass cap |
| C4 | 100nF | C_0603 | Device:C | GRM188R71H104KA93D | Murata | 10% | Decoupling |
| D1 | 1N4001 | DO-41 | Device:D | 1N4001-T | Diodes Inc | - | Reverse protection |

**Expected Audit Result:**
- Total components: 8
- Missing properties: 0
- Compliance: 100%

**Test validates:**
- ✓ Perfect compliance scenario
- ✓ All required properties present
- ✓ Should produce empty issues list

---

## Fixture 2: vintage_preamp.kicad_sch

**Scenario:** Legacy design (2018), predates company part number system

**Components:**

| Ref | Value | Footprint | LibID | PartNumber | Manufacturer | Tolerance | Notes |
|-----|-------|-----------|-------|------------|--------------|-----------|-------|
| U1 | TL072 | DIP-8 | Amplifier_Operational:TL072 | - | - | - | Op-amp |
| R1 | 10k | R_0805 | Device:R | - | - | 1% | Input resistor |
| R2 | 10k | R_0805 | Device:R | - | - | 1% | Feedback |
| R3 | 100k | R_0805 | Device:R | - | - | 1% | Bias |
| R4 | 47k | R_0805 | Device:R | - | - | 1% | Gain set |
| C1 | 100nF | C_0805 | Device:C | - | - | 10% | Input coupling |
| C2 | 100nF | C_0805 | Device:C | - | - | 10% | Output coupling |
| C3 | 10uF | C_1206 | Device:C_Polarized | - | - | 20% | Power supply |
| C4 | 10uF | C_1206 | Device:C_Polarized | - | - | 20% | Power supply |
| C5 | 100nF | C_0603 | Device:C | - | - | 10% | Decoupling |
| J1 | Audio_In | PJ-307 | Connector:AudioJack2 | - | - | - | Input jack |
| J2 | Audio_Out | PJ-307 | Connector:AudioJack2 | - | - | - | Output jack |

**Note:** All components have Tolerance and basic info, but NO PartNumber or Manufacturer

**Expected Audit Result:**
- Total components: 12
- Missing PartNumber: 12
- Missing Manufacturer: 12
- Compliance: 0%

**Test validates:**
- ✓ Zero compliance scenario
- ✓ All components flagged
- ✓ Legacy schematic detection

---

## Fixture 3: overdrive_pedal.kicad_sch

**Scenario:** Partially migrated (2022), passives updated but ICs pending

**Components:**

| Ref | Value | Footprint | LibID | PartNumber | Manufacturer | Tolerance | Notes |
|-----|-------|-----------|-------|------------|--------------|-----------|-------|
| U1 | TL072 | DIP-8 | Amplifier_Operational:TL072 | - | - | - | Op-amp (NEEDS UPDATE) |
| U2 | 4558 | DIP-8 | Amplifier_Operational:JRC4558 | - | - | - | Op-amp (NEEDS UPDATE) |
| D1 | 1N4148 | DO-35 | Device:D | 1N4148-TAP | Diodes Inc | - | Clipping diode ✓ |
| D2 | 1N4148 | DO-35 | Device:D | 1N4148-TAP | Diodes Inc | - | Clipping diode ✓ |
| R1 | 10k | R_0805 | Device:R | RC0805FR-0710KL | Yageo | 1% | Input resistor ✓ |
| R2 | 100k | R_0805 | Device:R | RC0805FR-07100KL | Yageo | 1% | Feedback ✓ |
| R3 | 47k | R_0805 | Device:R | RC0805FR-0747KL | Yageo | 1% | Gain ✓ |
| R4 | 4.7k | R_0805 | Device:R | RC0805FR-074K7L | Yageo | 1% | Tone ✓ |
| C1 | 100nF | C_0805 | Device:C | CC0805KRX7R9BB104 | Yageo | 10% | Coupling ✓ |
| C2 | 47nF | C_0805 | Device:C | CC0805KRX7R9BB473 | Yageo | 10% | Tone cap ✓ |
| C3 | 10uF | C_1206 | Device:C_Polarized | - | - | 20% | Power (NEEDS UPDATE) |
| C4 | 100nF | C_0603 | Device:C | CC0603KRX7R9BB104 | Yageo | 10% | Decoupling ✓ |
| J1 | IN | PJ-307 | Connector:AudioJack2 | - | - | - | Input (NEEDS UPDATE) |
| J2 | OUT | PJ-307 | Connector:AudioJack2 | - | - | - | Output (NEEDS UPDATE) |
| SW1 | DPDT | DPDT | Switch:SW_DPDT | - | - | - | Bypass (NEEDS UPDATE) |

**Expected Audit Result:**
- Total components: 15
- Components with PartNumber: 9 (resistors, diodes, some caps)
- Missing PartNumber: 6 (ICs, connectors, switch, one cap)
- Compliance: 60%

**Test validates:**
- ✓ Real-world migration scenario
- ✓ Partial compliance detection
- ✓ Grouping by component type useful (show "all ICs need updating")

---

## Fixture 4: di_box.kicad_sch

**Scenario:** Test DNP components and component filtering

**Components:**

| Ref | Value | Footprint | LibID | PartNumber | Manufacturer | DNP | Notes |
|-----|-------|-----------|-------|------------|--------------|-----|-------|
| U1 | DRV134 | SOIC-8 | Audio:DRV134 | DRV134UA | Texas Instruments | No | Balanced line driver ✓ |
| R1 | 10k | R_0805 | Device:R | RC0805FR-0710KL | Yageo | No | Input ✓ |
| R2 | 10k | R_0805 | Device:R | RC0805FR-0710KL | Yageo | No | Input ✓ |
| R3 | 100 | R_0805 | Device:R | - | - | Yes | Test point (DNP) |
| C1 | 100nF | C_0805 | Device:C | CC0805KRX7R9BB104 | Yageo | No | Coupling ✓ |
| C2 | 47uF | C_1206 | Device:C_Polarized | GRM31CR61A476KE19L | Murata | No | Power ✓ |
| J1 | XLR_IN | XLR-3 | Connector:XLR3 | - | - | No | Balanced input (NEEDS UPDATE) |
| J2 | XLR_OUT | XLR-3 | Connector:XLR3 | - | - | No | Balanced output (NEEDS UPDATE) |
| J3 | 1/4" | PJ-307 | Connector:AudioJack2 | MJ-3536N | CUI Devices | No | Instrument in ✓ |
| H1 | MountingHole | M3 | Mechanical:MountingHole | - | - | No | Mechanical (might exclude) |

**Expected Audit Result (with --exclude-dnp):**
- Total components: 9 (excluding R3 which is DNP)
- Missing PartNumber: 3 (J1, J2, H1)
- Compliance: 66.7%

**Expected Audit Result (without --exclude-dnp):**
- Total components: 10
- Missing PartNumber: 4 (R3, J1, J2, H1)
- Compliance: 60%

**Test validates:**
- ✓ DNP component handling
- ✓ Connector filtering (may want to exclude connectors)
- ✓ Mechanical component filtering (may want to exclude mounting holes)

---

## Fixture 5: clean_boost.kicad_sch

**Scenario:** Test property name variations and mixed properties

**Components:**

| Ref | Value | Footprint | LibID | PartNumber | MPN | CompanyPN | Manufacturer | Notes |
|-----|-------|-----------|-------|------------|-----|-----------|--------------|-------|
| U1 | TL071 | SOIC-8 | Amplifier_Operational:TL071 | - | TL071CDR | - | Texas Instruments | Has MPN but not PartNumber |
| R1 | 1M | R_0805 | Device:R | RC0805FR-071ML | - | - | Yageo | Has PartNumber ✓ |
| R2 | 10k | R_0805 | Device:R | - | - | ALG-R-10K-0805 | Yageo | Has CompanyPN (different field) |
| R3 | 47k | R_0805 | Device:R | RC0805FR-0747KL | - | - | Yageo | Has PartNumber ✓ |
| C1 | 100nF | C_0805 | Device:C | - | - | - | - | Missing all properties |
| C2 | 10uF | C_1206 | Device:C_Polarized | GRM31CR61E106KA12L | - | - | Murata | Has PartNumber ✓ |
| C3 | 47pF | C_0603 | Device:C | CC0603JRNPO9BN470 | - | - | Yageo | Has PartNumber ✓ |
| J1 | IN | PJ-307 | Connector:AudioJack2 | MJ-3536N | - | - | CUI Devices | Has PartNumber ✓ |
| J2 | OUT | PJ-307 | Connector:AudioJack2 | MJ-3536N | - | - | CUI Devices | Has PartNumber ✓ |

**Expected Audit Result (checking "PartNumber" only):**
- Total components: 9
- Missing PartNumber: 4 (U1 has MPN instead, R2 has CompanyPN instead, C1 has nothing)
- Compliance: 55.6%

**Expected Audit Result (checking "PartNumber,MPN,CompanyPN" as alternatives):**
- Total components: 9
- Missing all three: 1 (C1)
- Compliance: 88.9%

**Test validates:**
- ✓ Property name variations (PartNumber vs MPN vs CompanyPN)
- ✓ Testing multiple required properties
- ✓ "Missing any of these properties" logic

---

## Fixture 6: empty_test.kicad_sch

**Scenario:** Edge case - completely empty schematic

**Components:** None

**Expected Audit Result:**
- Total components: 0
- Missing properties: 0
- Compliance: N/A (or 100%?)

**Test validates:**
- ✓ Edge case handling
- ✓ No crash on empty schematic
- ✓ Proper reporting for "no components found"

---

## Test Coverage Matrix

| Test Case | Fixture(s) | Validates |
|-----------|------------|-----------|
| **100% compliance** | amp_power_supply | Ideal state, empty issues list |
| **0% compliance** | vintage_preamp | Worst case, all components flagged |
| **Partial compliance** | overdrive_pedal, di_box, clean_boost | Real migration scenarios |
| **DNP handling** | di_box | --exclude-dnp flag works |
| **Component filtering** | di_box | Filter by lib_id works |
| **Property variations** | clean_boost | Multiple property name support |
| **Empty schematic** | empty_test | Edge case handling |
| **Large component count** | vintage_preamp (12 components) | Performance with moderate size |
| **Mixed component types** | All except empty_test | Realistic variety |
| **Summary statistics** | All fixtures combined | Correct aggregation |

---

## Recommended Test Structure

```python
# tests/unit/cli/test_audit_bom.py

class TestBOMAuditCore:
    """Test core audit logic with individual schematics."""

    def test_perfect_compliance(self):
        """Test schematic with all properties present."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/amp_power_supply.kicad_sch",
            required_properties=["PartNumber"]
        )
        assert len(result.issues) == 0
        assert result.summary["compliance_percentage"] == 100.0

    def test_zero_compliance(self):
        """Test legacy schematic with no properties."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/vintage_preamp.kicad_sch",
            required_properties=["PartNumber"]
        )
        assert len(result.issues) == 12
        assert result.summary["compliance_percentage"] == 0.0

    def test_partial_compliance(self):
        """Test partially migrated schematic."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/overdrive_pedal.kicad_sch",
            required_properties=["PartNumber"]
        )
        assert len(result.issues) == 6  # 6 out of 15 missing
        assert result.summary["compliance_percentage"] == 60.0

    def test_dnp_exclusion(self):
        """Test that DNP components are excluded when flag set."""
        result_with_dnp = audit_schematic(
            "tests/fixtures/bom_audit/di_box.kicad_sch",
            required_properties=["PartNumber"],
            exclude_dnp=False
        )
        result_without_dnp = audit_schematic(
            "tests/fixtures/bom_audit/di_box.kicad_sch",
            required_properties=["PartNumber"],
            exclude_dnp=True
        )
        assert len(result_with_dnp.issues) == 4
        assert len(result_without_dnp.issues) == 3  # One less (R3 excluded)

    def test_component_type_filtering(self):
        """Test filtering by component lib_id."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/overdrive_pedal.kicad_sch",
            required_properties=["PartNumber"],
            filter_lib_ids=["Device:R"]  # Only resistors
        )
        # Should only check 4 resistors, all have PartNumber
        assert len(result.issues) == 0

    def test_property_variations(self):
        """Test checking multiple alternative property names."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/clean_boost.kicad_sch",
            required_properties=["PartNumber", "MPN", "CompanyPN"]
        )
        # Only C1 missing all three
        assert len(result.issues) == 1
        assert result.issues[0].reference == "C1"

    def test_empty_schematic(self):
        """Test edge case of empty schematic."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/empty_test.kicad_sch",
            required_properties=["PartNumber"]
        )
        assert len(result.issues) == 0
        assert result.summary["total_components"] == 0


class TestBOMAuditReports:
    """Test report generation."""

    def test_csv_report_format(self, tmp_path):
        """Test CSV report has correct columns and data."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/overdrive_pedal.kicad_sch",
            required_properties=["PartNumber"]
        )
        output = tmp_path / "audit.csv"
        generate_csv_report(result, output)

        # Verify CSV structure
        import csv
        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 6  # 6 components with issues

            # Check columns present
            assert "Schematic" in reader.fieldnames
            assert "Reference" in reader.fieldnames
            assert "Value" in reader.fieldnames
            assert "Footprint" in reader.fieldnames
            assert "MissingProperties" in reader.fieldnames

    def test_json_report_format(self, tmp_path):
        """Test JSON report structure."""
        result = audit_schematic(
            "tests/fixtures/bom_audit/vintage_preamp.kicad_sch",
            required_properties=["PartNumber", "Manufacturer"]
        )
        output = tmp_path / "audit.json"
        generate_json_report(result, output)

        # Verify JSON structure
        import json
        with open(output) as f:
            data = json.load(f)
            assert "summary" in data
            assert "issues" in data
            assert data["summary"]["total_components"] == 12
            assert len(data["issues"]) == 12


class TestBOMAuditDirectory:
    """Test directory scanning."""

    def test_recursive_scan(self, tmp_path):
        """Test recursive directory scanning."""
        # Create test directory structure
        # tests/fixtures/bom_audit/
        #   ├── amp_power_supply.kicad_sch
        #   └── legacy/
        #       └── vintage_preamp.kicad_sch

        result = audit_directory(
            path="tests/fixtures/bom_audit",
            required_properties=["PartNumber"],
            recursive=True
        )

        assert result.summary["total_schematics"] >= 2
        assert result.summary["total_components"] >= 20

    def test_non_recursive_scan(self):
        """Test non-recursive scanning."""
        result = audit_directory(
            path="tests/fixtures/bom_audit",
            required_properties=["PartNumber"],
            recursive=False
        )

        # Should only find schematics in root, not in subdirectories
        # Adjust assertion based on fixture structure
```

---

## Creating Test Fixtures

### Manual Creation (Recommended for Reference Tests)

Following kicad-sch-api testing patterns:

1. **Create blank schematics using kicad-sch-api**
2. **Open in KiCad and manually add components**
3. **Set properties as specified above**
4. **Save and commit to test fixtures**

This ensures test fixtures are valid KiCad schematics.

### Programmatic Creation (Alternative)

```python
# scripts/create_bom_audit_fixtures.py
import kicad_sch_api as ksa

# Create amp_power_supply.kicad_sch
sch = ksa.create_schematic("AmpPowerSupply")

# Add U1 with all properties
u1 = sch.components.add(
    'Regulator_Linear:AMS1117-3.3',
    reference='U1',
    value='AMS1117-3.3',
    position=(100, 100)
)
u1.set_property('PartNumber', 'AMS1117-3.3')
u1.set_property('Manufacturer', 'Advanced Monolithic')

# ... add remaining components ...

sch.save("tests/fixtures/bom_audit/amp_power_supply.kicad_sch")
```

---

## Summary

**6 realistic test schematics covering:**
- ✓ Perfect compliance (modern design)
- ✓ Zero compliance (legacy design)
- ✓ Partial compliance (migration in progress)
- ✓ DNP component handling
- ✓ Component type filtering
- ✓ Property name variations
- ✓ Edge cases (empty schematic)

**Total test surface:**
- 54 components across 6 schematics
- Multiple component types (ICs, passives, connectors, mechanical)
- Real guitar electronics use cases
- Realistic part numbers and manufacturers

**Ready for implementation!**
