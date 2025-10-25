# Testing Plan Summary: Round-Trip & Bidirectional Update

## Completed Work

### ✅ Basic Round-Trip Pipeline Validated

The fundamental round-trip pipeline has been tested and confirmed working:

```
Python → JSON → KiCad → JSON
  ✅      ✅      ✅
```

**Test Suite:** `tests/bidirectional/test_00_basic_round_trip.py`

**All 5 tests passing:**
1. ✅ Python → JSON generation
2. ✅ JSON → KiCad generation
3. ✅ KiCad → JSON export
4. ✅ Complete round-trip (all three directions)
5. ✅ Component values preservation

**Example Test Output:**
```
Step 1 (Python → JSON): ✓
  - Components: ['R1', 'R2']
  - Nets: ['VIN', 'VOUT', 'GND']

Step 2 (JSON → KiCad): ✓
  - Project: /tmp/voltage_divider

Step 3 (KiCad → JSON): ✓
  - Components: ['R1', 'R2']
  - Nets: ['VIN', 'VOUT', 'GND']

Step 4 (Verification): ✓
✅ COMPLETE ROUND-TRIP: Python → JSON → KiCad → JSON
```

---

## Current Architecture

### What's Working (Proven by Tests)

**Python → JSON** (Implemented in `Circuit.generate_json_netlist()`)
- Generates valid JSON with all circuit data
- Preserves component references, values, symbols, footprints
- Preserves net names and electrical connectivity
- Schema: `{name, components, nets, annotations}`

**JSON → KiCad** (Implemented in `Circuit.generate_kicad_project()`)
- Creates KiCad project directory
- Generates .kicad_sch schematic file
- Generates .kicad_pro project file
- Auto-places components
- Automatically creates JSON netlist in project directory

**KiCad → JSON** (Implemented in `KiCadSchematicParser.parse_and_export()`)
- Parses .kicad_sch files
- Exports to JSON format
- Preserves component and net data
- Tested via `tests/integration/test_kicad_to_json_export.py`

### What's NOT Working (Next Priority)

**JSON → Python** (Required for bidirectional sync)
- No `Circuit.update_python_from_json()` method yet
- No component matching logic
- No file rewriting capability
- **Phase 1 work:** Issues #217, #218

---

## Usage Patterns

### Current: Python-Centric Workflow ✅

```python
from circuit_synth import Circuit, Component, Net, circuit

@circuit(name="my_design")
def my_circuit():
    # Define circuit in Python
    vcc = Net("VCC")
    gnd = Net("GND")

    r1 = Component(symbol="Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="20k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

    r1[1] += vcc
    r1[2] += gnd
    r2[1] += vcc
    r2[2] += gnd

# Step 1: Define circuit
circuit = my_circuit()

# Step 2: Generate KiCad project
result = circuit.generate_kicad_project("my_design", generate_pcb=False)
# Creates: my_design/my_design.kicad_sch, .kicad_pro, .json

# Step 3: Export/generate netlists
circuit.generate_json_netlist("netlist.json")
circuit.generate_kicad_netlist("netlist.net")
```

### Future: Bidirectional Workflow ⏳

```python
# After Phase 1 implementation:

# Step 1: Define in Python
circuit = my_circuit()
circuit.generate_kicad_project("design")

# Step 2: User edits in KiCad (manual changes)
# - Changes R1 value from 10k to 12k
# - Changes R2 position manually
# - Exports back to JSON

# Step 3: Update Python source from JSON changes
circuit.update_python_from_json(
    "design/design.json",
    "my_circuit.py",
    update_values=True,        # Update component values
    update_positions=False,    # Keep manual positions in KiCad
    preserve_comments=True,    # Keep Python comments
)
# Result: Python source now has R1 value = "12k"
```

---

## Testing Framework

### Basic Round-Trip Tests

**File:** `tests/bidirectional/test_00_basic_round_trip.py`

**Key Testing Patterns:**
```python
# Test 1: Python → JSON
circuit.generate_json_netlist(json_path)
json_data = json.load(json_path)
assert "components" in json_data
assert "R1" in json_data["components"]

# Test 2: JSON → KiCad
result = circuit.generate_kicad_project("name")
project_dir = result.get("project_path")
assert project_dir.exists()

# Test 3: KiCad → JSON
parser = KiCadSchematicParser(kicad_sch)
parser.parse_and_export(json_path)
assert json_path.exists()

# Test 4: Complete Round-Trip
# 1. Generate from Python
# 2. Export from KiCad
# 3. Verify components match
assert original_components == exported_components
```

### Running Tests

```bash
# Just the basic round-trip tests
uv run pytest tests/bidirectional/test_00_basic_round_trip.py -v

# Full bidirectional suite (including advanced tests)
uv run pytest tests/bidirectional/ -v

# KiCad→JSON export tests
uv run pytest tests/integration/test_kicad_to_json_export.py -v

# Run with output preservation for debugging
PRESERVE_FILES=1 uv run pytest tests/bidirectional/test_00_basic_round_trip.py -v
```

---

## Blocked Issues & Fixes Required

### Critical Blockers for Phase 1

**Issue #236:** kicad-to-python generates broken code
- Generated code missing `placement_algorithm` parameter
- Causes: AttributeError on ConnectionAnalyzer
- Fix: Update `python_code_generator.py` to include all required params

**Issue #226:** Source reference rewriting removed
- PR #221 deleted `update_source_refs` parameter
- Tests failing because feature was removed
- Fix: Restore parameter and rewriting logic

**Issue #229:** Publish kicad-sch-api v0.3.3
- Blocks PR #197 (geometry module refactor)
- 30 min to publish, verify installation
- Required before merging PR #197

---

## Phase 1-4 Implementation Roadmap

### Phase 0: JSON Canonical Format (In Progress)
- [x] #209: Automatic JSON generation ✅ COMPLETE
- [ ] #210: KiCad → JSON export
- [ ] #211: Refactor KiCadToPythonSyncer
- [ ] #212: Phase 0 integration tests

### Phase 1: Core JSON → Python Updates (Next)
- [ ] #217: JSONToPythonUpdater class
- [ ] #218: Circuit.update_python_from_json() method
- Tests for basic value/footprint updates
- Canonical component matching

### Phase 2: Robust Matching
- [ ] #214: Multi-strategy matching
- Handle duplicate components
- Ambiguity resolution
- Occurrence tracking

### Phase 3: Hierarchical Support
- [ ] #215: Multi-file circuits
- Subcircuit updates
- File organization preservation

### Phase 4: Advanced Features
- [ ] #216: CLI command, preview mode, performance
- Position updates (opt-in)
- Custom properties
- Performance optimization

---

## Success Metrics

### Current Status
- ✅ **Basic infrastructure:** Python→JSON, JSON→KiCad, KiCad→JSON all working
- ✅ **Component preservation:** Values, symbols, footprints survive round-trip
- ✅ **Net preservation:** All nets present at each stage
- ✅ **Test coverage:** 5 integration tests validating each direction

### After Phase 1 (Target: 2-3 weeks)
- ✅ Bidirectional Python↔JSON sync working
- ✅ Component value updates working
- ✅ Footprint updates working
- ✅ 15+ tests covering matching strategies

### After Phase 4 (Target: 6-8 weeks)
- ✅ Full bidirectional Python↔KiCad workflow
- ✅ Position preservation option
- ✅ CLI tool for syncing
- ✅ Performance <1s for 100 components
- ✅ 50+ tests covering all scenarios

---

## Key Files

**Test Files:**
- `tests/bidirectional/test_00_basic_round_trip.py` - NEW
- `tests/bidirectional/test_01_resistor_divider/test_netlist_comparison.py` - Python→KiCad
- `tests/integration/test_kicad_to_json_export.py` - KiCad→JSON
- `tests/bidirectional/BIDIRECTIONAL_SYNC_TESTS.md` - Master test plan

**Documentation:**
- `ROUND_TRIP_TESTING_SUMMARY.md` - Complete status overview
- `TESTING_PLAN_SUMMARY.md` - This file

**Implementation Files:**
- `src/circuit_synth/core/circuit.py` - generate_kicad_project(), generate_json_netlist()
- `src/circuit_synth/tools/utilities/kicad_schematic_parser.py` - KiCad→JSON export
- `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py` - KiCadToPythonSyncer

---

## Next Actions

### Immediate (This Sprint)
1. Commit round-trip tests (✅ DONE)
2. Fix critical blockers (#236, #226)
3. Complete Phase 0 prerequisites

### Next Sprint
1. Implement Phase 1 core classes (#217, #218)
2. Create JSONToPythonUpdater
3. Add update_python_from_json() API

### Ongoing
1. Expand test coverage as features are added
2. Monitor for regressions
3. Track performance metrics

---

## Resources

### Documentation Links
- Architecture: `ARCHITECTURE_REVIEW_KICAD_TO_PYTHON.md`
- PRD: `PRD_JSON_TO_PYTHON_CANONICAL_UPDATE.md`
- Test Plan: `BIDIRECTIONAL_SYNC_TESTS.md`

### GitHub Issues
- Phase epics: #208 (Phase 0), #213 (Phase 1), #214 (Phase 2), #215 (Phase 3), #216 (Phase 4)
- Critical blockers: #236, #226, #229, #197

### Test Commands
```bash
# Run all bidirectional tests
uv run pytest tests/bidirectional/ -v

# Run basic round-trip only
uv run pytest tests/bidirectional/test_00_basic_round_trip.py -v

# Run with coverage
uv run pytest tests/bidirectional/ --cov=circuit_synth --cov-report=html
```

---

## Summary

✅ **The basic round-trip pipeline is validated and working**

The fundamental transformation pipeline (Python → JSON → KiCad → JSON) has been proven through comprehensive testing. All three directions work independently and preserve circuit data through the complete round-trip.

The next step is implementing **Phase 1 (JSON → Python updates)** to enable true bidirectional editing, allowing engineers to:
- Edit circuits in Python
- Export and work in KiCad
- Sync changes back to Python automatically

This is foundational infrastructure for the circuit-synth automation vision.
