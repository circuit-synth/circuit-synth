# PRD: KiCad → JSON Export Functionality

**Issue:** #210
**Epic:** #208 (Phase 0: Make JSON the Canonical Format)
**Branch:** `feature/issue-210-kicad-to-json-export`
**Created:** 2025-10-19
**Status:** In Development

---

## Executive Summary

This PRD defines the implementation of KiCad → JSON export functionality, a critical component of Phase 0 that enables bidirectional conversion between KiCad schematics and circuit-synth JSON format. Currently, the `KiCadNetlistParser` only creates intermediate `Circuit` objects without the ability to export to the canonical JSON format.

**Goal:** Create a complete workflow to parse `.kicad_sch` files and export them to circuit-synth JSON format with proper schema transformation.

**Success Metric:** Ability to parse any KiCad schematic and export it to JSON that matches the schema used by `Circuit._generate_hierarchical_json_netlist()`.

---

## Problem Statement

### Current State

1. **KiCadNetlistParser exists** but only parses `.net` files (not `.kicad_sch`)
2. **Circuit.to_dict()** returns internal format (lists for components/nets)
3. **No export path to JSON** - can't convert KiCad schematics to canonical format
4. **Schema mismatch** - `to_dict()` format ≠ circuit-synth JSON format

### Gap Analysis

**Gap 1: No .kicad_sch Parser**
- KiCadNetlistParser only handles `.net` files
- Need parser for S-expression `.kicad_sch` format
- Must extract components, nets, hierarchical structure

**Gap 2: Schema Mismatch**
- `Circuit.to_dict()` uses lists: `{"components": [...]}`
- JSON schema uses dicts: `{"components": {"R1": {...}}}`
- Need transformation layer

**Gap 3: No Export Method**
- No way to trigger export from Circuit object
- Need `Circuit.to_circuit_synth_json()` method

---

## Existing Code Analysis

### KiCadNetlistParser (`kicad_netlist_parser.py`)

**What it does:**
- Parses KiCad `.net` netlist files (S-expressions)
- Extracts components: reference, lib_id, value, footprint
- Extracts nets: name, connections list
- Returns `(List[Component], List[Net])`

**Strengths:**
- Good S-expression parsing with regex
- Handles multi-line formats
- Clean error handling
- Logging infrastructure

**Limitations:**
- Only parses `.net` files (requires netlist generation)
- Doesn't parse `.kicad_sch` directly
- No JSON export capability

### KiCadParser (`kicad_parser.py`)

**What it does:**
- Main orchestrator for KiCad project parsing
- Generates `.net` files via `kicad-cli`
- Parses `.kicad_sch` files for hierarchical structure
- Creates `Circuit` objects with real connections

**Strengths:**
- Comprehensive hierarchical handling
- Symbol block extraction (`_extract_symbol_blocks`)
- Component parsing (`_parse_component_block`)
- Sheet instance parsing (`_parse_sheet_instances`)
- Excellent logging

**Key Methods We Can Reuse:**
- `_extract_symbol_blocks()` - Extract components from schematic
- `_parse_component_block()` - Parse component details
- `_parse_sheet_instances()` - Handle hierarchical sheets
- `_build_hierarchical_tree()` - Build parent-child relationships

### Circuit Model (`models.py`)

**Current Structure:**
```python
@dataclass
class Circuit:
    name: str
    components: List[Component]
    nets: List[Net]
    schematic_file: str = ""
    is_hierarchical_sheet: bool = False
    hierarchical_tree: Optional[Dict[str, List[str]]] = None

    def to_dict(self):
        return {
            "name": self.name,
            "components": [c.to_dict() for c in self.components],  # LIST
            "nets": [n.to_dict() for n in self.nets],              # LIST
            "schematic_file": self.schematic_file,
            "is_hierarchical_sheet": self.is_hierarchical_sheet,
            "hierarchical_tree": self.hierarchical_tree,
        }
```

**Problem:** `to_dict()` returns lists, but JSON schema expects dicts.

### Target JSON Schema (`circuit.py:576-586`)

**Expected Format:**
```python
json_data = {
    "name": self.name,
    "description": getattr(self, "description", ""),
    "tstamps": "",
    "source_file": f"{self.name}.kicad_sch",
    "components": all_components,  # DICT: {ref: component_dict}
    "nets": all_nets,              # DICT: {name: [connections]}
    "subcircuits": [],
    "annotations": getattr(self, "_annotations", []),
}
```

**Key Differences:**

| Field | to_dict() Format | JSON Schema Format |
|-------|------------------|-------------------|
| components | `List[Component]` | `Dict[str, Dict]` keyed by ref |
| nets | `List[Net]` | `Dict[str, List]` keyed by name |
| New fields | None | description, tstamps, source_file, subcircuits, annotations |

---

## Schema Transformation Details

### Components Transformation

**Input (to_dict):**
```python
"components": [
    {"reference": "R1", "lib_id": "Device:R", "value": "10k", ...},
    {"reference": "C1", "lib_id": "Device:C", "value": "100nF", ...}
]
```

**Output (JSON schema):**
```python
"components": {
    "R1": {
        "symbol": "Device:R",
        "ref": "R1",
        "value": "10k",
        "footprint": "Resistor_SMD:R_0603_1608Metric",
        "datasheet": "",
        "description": "",
        "properties": {},
        "tstamps": "",
        "pins": []
    },
    "C1": {...}
}
```

**Mapping Rules:**
- List → Dict keyed by `reference`
- `lib_id` → `symbol`
- Add `reference` → `ref` (keep both for compatibility)
- Add empty defaults for: datasheet, description, properties, tstamps, pins

### Nets Transformation

**Input (to_dict):**
```python
"nets": [
    {
        "name": "VCC",
        "connections": [("R1", "1"), ("C1", "1")]
    }
]
```

**Output (JSON schema):**
```python
"nets": {
    "VCC": [
        {
            "component": "R1",
            "pin": {"number": "1", "name": "~", "type": "passive"}
        },
        {
            "component": "C1",
            "pin": {"number": "1", "name": "~", "type": "passive"}
        }
    ]
}
```

**Mapping Rules:**
- List → Dict keyed by `name`
- Connections: `(ref, pin_num)` → `{"component": ref, "pin": {...}}`
- Pin format: Expand to object with number, name, type

---

## Implementation Plan

### Phase 1: Create KiCadSchematicParser Class

**New File:** `src/circuit_synth/tools/utilities/kicad_schematic_parser.py`

```python
class KiCadSchematicParser:
    """Parse .kicad_sch files and export to circuit-synth JSON format."""

    def __init__(self, schematic_path: Path):
        """Initialize with path to .kicad_sch file."""
        self.schematic_path = Path(schematic_path)
        self.kicad_parser = KiCadParser(self.schematic_path.parent)

    def parse_schematic(self) -> Circuit:
        """
        Parse .kicad_sch file to Circuit object.

        Uses KiCadParser methods for actual parsing:
        - _extract_symbol_blocks() for components
        - _parse_component_block() for details
        - Netlist generation for connections

        Returns:
            Circuit object with components and nets
        """
        pass

    def export_to_json(self, circuit: Circuit, json_path: Path):
        """
        Export Circuit to circuit-synth JSON format.

        Uses circuit.to_circuit_synth_json() method.
        Writes formatted JSON to file.
        """
        pass

    def parse_and_export(self, json_path: Path) -> Dict[str, Any]:
        """
        Complete workflow: parse schematic and export to JSON.

        Returns:
            Result dict with success status, json_path, errors
        """
        pass
```

**Design Decisions:**
1. Reuse KiCadParser methods - no need to reimplement parsing
2. Thin wrapper that orchestrates parsing + export
3. Support both flat and hierarchical circuits
4. Return structured results for error handling

### Phase 2: Add Circuit.to_circuit_synth_json() Method

**File:** `src/circuit_synth/tools/utilities/models.py`

```python
@dataclass
class Circuit:
    # ... existing fields ...

    def to_circuit_synth_json(self) -> dict:
        """
        Export to circuit-synth JSON format.

        This converts the internal Circuit representation to the format
        expected by circuit-synth JSON schema. Key transformations:

        1. Components: List[Component] → Dict[ref, component_dict]
        2. Nets: List[Net] → Dict[name, connections_list]
        3. Add required fields: description, tstamps, source_file, etc.

        Returns:
            Dictionary matching circuit-synth JSON schema
        """
        # Transform components: list → dict
        components_dict = {}
        for comp in self.components:
            comp_dict = {
                "symbol": comp.lib_id,
                "ref": comp.reference,
                "value": comp.value,
                "footprint": comp.footprint,
                "datasheet": "",  # Default
                "description": "",  # Default
                "properties": {},  # Default
                "tstamps": "",  # Default
                "pins": []  # Default - could be populated from schematic
            }
            components_dict[comp.reference] = comp_dict

        # Transform nets: list → dict
        nets_dict = {}
        for net in self.nets:
            connections = []
            for ref, pin_num in net.connections:
                connection = {
                    "component": ref,
                    "pin": {
                        "number": str(pin_num),
                        "name": "~",  # Default - could lookup from component
                        "type": "passive"  # Default
                    }
                }
                connections.append(connection)
            nets_dict[net.name] = connections

        # Build final JSON structure
        return {
            "name": self.name,
            "description": "",
            "tstamps": "",
            "source_file": self.schematic_file,
            "components": components_dict,
            "nets": nets_dict,
            "subcircuits": [],  # TODO: Handle hierarchical circuits
            "annotations": []
        }
```

**Design Decisions:**
1. Add method to Circuit class (natural location)
2. Handle schema transformation in one place
3. Use defaults for missing fields (datasheet, pins, etc.)
4. Keep method focused on schema conversion only

### Phase 3: Handle Hierarchical Circuits

**Challenge:** Subcircuits need special handling

**Approach:**
```python
def to_circuit_synth_json(self) -> dict:
    # ... components and nets as above ...

    # Handle subcircuits recursively
    subcircuits = []
    if hasattr(self, '_subcircuits'):
        for subcircuit in self._subcircuits:
            subcircuits.append(subcircuit.to_circuit_synth_json())

    return {
        # ... other fields ...
        "subcircuits": subcircuits
    }
```

**Note:** Current Circuit model doesn't have `_subcircuits` attribute. May need to extend or use hierarchical_tree instead.

---

## Edge Cases and Error Handling

### 1. Missing or Invalid .kicad_sch File
**Scenario:** File doesn't exist or is corrupted
**Solution:**
- Check file existence before parsing
- Try-catch around file operations
- Return structured error dict

### 2. Empty Circuit (No Components)
**Scenario:** Schematic has no components
**Solution:**
- Allow empty components dict
- Log warning but don't error
- Valid JSON with empty structure

### 3. Hierarchical Circuits with Missing Sheets
**Scenario:** Sheet reference exists but file is missing
**Solution:**
- Log warning for missing sheet
- Continue parsing other sheets
- Include partial hierarchy in output

### 4. Net Connections to Non-Existent Components
**Scenario:** Net references component that doesn't exist
**Solution:**
- Validate connections during transformation
- Filter out invalid connections
- Log warning

### 5. Duplicate Component References
**Scenario:** Multiple components with same reference
**Solution:**
- Detect during parsing
- Use last occurrence or error out
- Log warning

### 6. Special Characters in Net Names
**Scenario:** Net names with `/`, spaces, special chars
**Solution:**
- Preserve exact names (don't sanitize)
- JSON escaping handles special chars
- Test with real KiCad netlists

### 7. Missing Required Fields
**Scenario:** Component missing footprint or value
**Solution:**
- Use empty string defaults
- Don't error on optional fields
- Maintain schema consistency

### 8. Large Circuits (Performance)
**Scenario:** 1000+ components
**Solution:**
- Use efficient dict construction
- Stream JSON writing for large files
- Profile and optimize if needed

---

## Test Plan

### Unit Tests: test_kicad_schematic_parser.py

**Test 1: Parse Simple Flat Circuit**
```python
def test_parse_simple_flat_circuit():
    """Test parsing a simple schematic with 2-3 components."""
    # Create minimal .kicad_sch with R, C
    # Parse to Circuit
    # Verify: components list, nets list, references
```

**Test 2: Export Simple Circuit to JSON**
```python
def test_export_simple_circuit_to_json():
    """Test exporting Circuit to JSON format."""
    # Create Circuit with known components/nets
    # Export to JSON
    # Verify: file exists, valid JSON, correct schema
```

**Test 3: Parse and Export End-to-End**
```python
def test_parse_and_export_workflow():
    """Test complete workflow from .kicad_sch to JSON."""
    # Parse schematic
    # Export to JSON
    # Verify: matches expected JSON
```

**Test 4: Handle Missing Schematic File**
```python
def test_handle_missing_schematic():
    """Test error handling for non-existent file."""
    # Try to parse missing file
    # Verify: returns error result, doesn't crash
```

**Test 5: Handle Empty Circuit**
```python
def test_handle_empty_circuit():
    """Test parsing schematic with no components."""
    # Parse empty schematic
    # Verify: valid JSON with empty components/nets
```

### Unit Tests: test_circuit_json_schema.py

**Test 6: Components List to Dict Transformation**
```python
def test_components_list_to_dict():
    """Test transforming components from list to dict format."""
    # Create Circuit with component list
    # Call to_circuit_synth_json()
    # Verify: components is dict keyed by ref
    # Verify: all required fields present
```

**Test 7: Nets List to Dict Transformation**
```python
def test_nets_list_to_dict():
    """Test transforming nets from list to dict format."""
    # Create Circuit with net list
    # Call to_circuit_synth_json()
    # Verify: nets is dict keyed by name
    # Verify: connections have correct pin format
```

**Test 8: Schema Field Mapping**
```python
def test_schema_field_mapping():
    """Test lib_id → symbol and other field mappings."""
    # Create Component with lib_id
    # Transform to JSON
    # Verify: symbol field exists with lib_id value
    # Verify: ref field matches reference
```

**Test 9: Default Fields Added**
```python
def test_default_fields_added():
    """Test that missing fields get default values."""
    # Create minimal Component
    # Transform to JSON
    # Verify: datasheet="", properties={}, tstamps="", pins=[]
```

**Test 10: Pin Format Transformation**
```python
def test_pin_format_transformation():
    """Test connection format: (ref, pin) → pin object."""
    # Create Net with simple connections
    # Transform to JSON
    # Verify: pin is object with number, name, type
```

### Integration Tests: test_kicad_to_json_export.py

**Test 11: Round-Trip Validation**
```python
def test_round_trip_kicad_to_json():
    """Test KiCad → JSON produces valid schema."""
    # Start with real .kicad_sch file
    # Parse and export to JSON
    # Load JSON and validate against schema
    # Verify: can be loaded by load_circuit_from_json_file()
```

**Test 12: Hierarchical Circuit Export**
```python
def test_hierarchical_circuit_export():
    """Test exporting hierarchical circuits with subcircuits."""
    # Create hierarchical .kicad_sch
    # Parse and export
    # Verify: subcircuits array populated
    # Verify: hierarchical structure preserved
```

**Test 13: Real KiCad Project Export**
```python
def test_real_kicad_project_export():
    """Test with actual KiCad project from examples."""
    # Use example project (ESP32 dev board?)
    # Parse and export
    # Verify: all components present
    # Verify: all nets connected correctly
```

**Test 14: JSON Matches Circuit._generate_hierarchical_json_netlist**
```python
def test_json_matches_generate_hierarchical():
    """Test exported JSON matches circuit.py format."""
    # Create circuit in Python
    # Export via to_circuit_synth_json()
    # Export via _generate_hierarchical_json_netlist()
    # Compare: same schema structure (keys, types)
```

**Test 15: Large Circuit Performance**
```python
def test_large_circuit_performance():
    """Test performance with 100+ components."""
    # Create large schematic programmatically
    # Parse and export
    # Verify: completes in <5 seconds
    # Verify: memory usage reasonable
```

### Test Data

**Required Test Fixtures:**
1. `simple_resistor.kicad_sch` - Single resistor
2. `rc_filter.kicad_sch` - R + C circuit
3. `empty.kicad_sch` - No components
4. `hierarchical_power.kicad_sch` - With subcircuits
5. `esp32_dev_board.kicad_sch` - Real-world example (if available)

---

## Acceptance Criteria

### Functional Requirements

- [ ] **FR1:** Can parse any `.kicad_sch` file to Circuit object
- [ ] **FR2:** Can export Circuit to circuit-synth JSON format
- [ ] **FR3:** JSON matches schema used by `_generate_hierarchical_json_netlist()`
- [ ] **FR4:** Handles hierarchical circuits (subcircuits)
- [ ] **FR5:** Handles flat circuits
- [ ] **FR6:** Preserves all component data (ref, value, footprint, position)
- [ ] **FR7:** Preserves all net connections (name, component refs, pin numbers)
- [ ] **FR8:** Error handling returns structured results

### Non-Functional Requirements

- [ ] **NFR1:** All unit tests pass (10+ tests)
- [ ] **NFR2:** All integration tests pass (5+ tests)
- [ ] **NFR3:** Code coverage >80% for new code
- [ ] **NFR4:** Performance: <5s for 100 components
- [ ] **NFR5:** Comprehensive error handling and logging
- [ ] **NFR6:** Follows existing code patterns (KiCadParser style)
- [ ] **NFR7:** Documented with docstrings and examples

### Quality Gates

1. **All tests pass:** 15+ tests green
2. **Code review:** PR approved by maintainer
3. **Integration test:** Round-trip KiCad → JSON → Python works
4. **Schema validation:** JSON loadable by `load_circuit_from_json_file()`
5. **Documentation:** PRD complete and reviewed

---

## Dependencies and Blockers

### Dependencies

1. **KiCadParser** - Reuse existing parsing logic
2. **KiCadNetlistParser** - Reuse S-expression parsing patterns
3. **Circuit model** - Extend with new method
4. **JSON schema** - Must match `_generate_hierarchical_json_netlist()` format

### Blockers

- **None currently** - All dependencies exist in codebase

### Risks

1. **Schema drift:** JSON schema might change - mitigation: extensive tests
2. **Hierarchical complexity:** Subcircuits add complexity - mitigation: reuse KiCadParser logic
3. **KiCad version compatibility:** Different KiCad versions - mitigation: test with v6/v7/v8

---

## Implementation Checklist

### Week 2 (Current)

- [x] **Day 1:** Write PRD (this document)
- [ ] **Day 2:** Create test files with 15+ test cases
- [ ] **Day 3:** Implement `Circuit.to_circuit_synth_json()` method
- [ ] **Day 4:** Implement `KiCadSchematicParser` class
- [ ] **Day 5:** Run tests, fix failures, iterate

### Week 2 Deliverables

1. PRD: `docs/PRD_KICAD_TO_JSON_EXPORT.md` ✅
2. Tests: 15+ tests covering all scenarios
3. Implementation: Both classes functional
4. PR: Ready for review

---

## Open Questions

1. **Q: Should we support KiCad v6, v7, and v8 formats?**
   A: Start with v7/v8 (current versions), test compatibility

2. **Q: How to handle pin data if not in netlist?**
   A: Use defaults (passive, ~) - can enhance later

3. **Q: Should subcircuits be flattened or hierarchical?**
   A: Support both - match `_generate_hierarchical_json_netlist()` behavior

4. **Q: Where to store test fixtures (.kicad_sch files)?**
   A: `tests/fixtures/kicad/` directory

5. **Q: Should we validate JSON schema after export?**
   A: Yes - use `load_circuit_from_json_file()` as validator

---

## References

### Code Files

- `src/circuit_synth/tools/utilities/kicad_netlist_parser.py` - Netlist parsing
- `src/circuit_synth/tools/utilities/kicad_parser.py` - Schematic parsing
- `src/circuit_synth/tools/utilities/models.py` - Circuit/Component/Net models
- `src/circuit_synth/core/circuit.py:576-586` - Target JSON schema

### Documentation

- `docs/JSON_SCHEMA.md` - Circuit-synth JSON schema specification
- `PROJECT_STATUS.md` - Phase 0 timeline and progress

### GitHub Issues

- Issue #210 - This task
- Epic #208 - Phase 0: Make JSON the Canonical Format
- Issue #211 - Depends on this (KiCadToPythonSyncer refactor)

---

## Appendix: Example JSON Output

```json
{
  "name": "simple_rc_filter",
  "description": "",
  "tstamps": "",
  "source_file": "simple_rc_filter.kicad_sch",
  "components": {
    "R1": {
      "symbol": "Device:R",
      "ref": "R1",
      "value": "10k",
      "footprint": "Resistor_SMD:R_0603_1608Metric",
      "datasheet": "",
      "description": "",
      "properties": {},
      "tstamps": "",
      "pins": []
    },
    "C1": {
      "symbol": "Device:C",
      "ref": "C1",
      "value": "100nF",
      "footprint": "Capacitor_SMD:C_0603_1608Metric",
      "datasheet": "",
      "description": "",
      "properties": {},
      "tstamps": "",
      "pins": []
    }
  },
  "nets": {
    "VCC": [
      {
        "component": "R1",
        "pin": {"number": "1", "name": "~", "type": "passive"}
      }
    ],
    "OUT": [
      {
        "component": "R1",
        "pin": {"number": "2", "name": "~", "type": "passive"}
      },
      {
        "component": "C1",
        "pin": {"number": "1", "name": "~", "type": "passive"}
      }
    ],
    "GND": [
      {
        "component": "C1",
        "pin": {"number": "2", "name": "~", "type": "passive"}
      }
    ]
  },
  "subcircuits": [],
  "annotations": []
}
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Author:** Claude Code
**Reviewers:** TBD
