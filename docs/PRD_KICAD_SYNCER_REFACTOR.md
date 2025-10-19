# PRD: Refactor KiCadToPythonSyncer to Use JSON Input

**Issue:** #211
**Epic:** #208 (Phase 0: Make JSON the Canonical Format)
**Branch:** `feature/issue-211-refactor-kicad-syncer`
**Created:** 2025-10-19
**Status:** In Development
**Dependencies:**
- ✅ #209 - Automatic JSON generation
- ✅ #210 - KiCad → JSON export

---

## Executive Summary

This PRD defines the refactoring of `KiCadToPythonSyncer` to use JSON as the canonical input format instead of parsing KiCad `.net` files directly. This is a critical deliverable for Phase 0 Week 3 that aligns the syncer with the architectural principle that JSON is the single source of truth.

**Goal:** Make JSON the primary data source for Python code generation while maintaining backward compatibility with existing KiCad project-based workflows.

**Success Metric:** All sync operations flow through JSON (KiCad → JSON → Python) with deprecation warnings for legacy direct KiCad input.

---

## Problem Statement

### Current Architecture (WRONG)

```
KiCad .kicad_sch → .net file → KiCadNetlistParser → Python
                                     ↑
                          Direct .net parsing bypasses JSON
```

**Issues:**
1. Violates canonical data flow where JSON should be source of truth
2. Maintains duplicate parsing paths (.net and JSON)
3. No consistent intermediate representation
4. Hard to test and maintain multiple parsing implementations

### Target Architecture (CORRECT)

```
KiCad .kicad_sch → JSON (via KiCadSchematicParser #210) → KiCadToPythonSyncer → Python
                           ↑
                    JSON is canonical format
```

**Benefits:**
1. Single source of truth (JSON)
2. Consistent data flow across all tools
3. JSON can be version-controlled and diffed
4. Enables better testing and validation
5. Supports manual JSON editing when needed

---

## Current Implementation Analysis

### KiCadToPythonSyncer Current Behavior

**File:** `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py`

**Constructor:**
```python
def __init__(
    self,
    kicad_project: str,
    python_file: str,
    preview_only: bool = True,
    create_backup: bool = True,
):
    self.kicad_project = Path(kicad_project)
    self.parser = KiCadParser(str(self.kicad_project))
```

**Current Data Flow:**
1. Accept KiCad project path (.kicad_pro)
2. Initialize `KiCadParser` with project
3. `KiCadParser` generates `.net` files via `kicad-cli`
4. Parse `.net` files to extract components/nets
5. Generate Python code directly from parsed data

**Problems:**
- No JSON involved in main sync path
- Direct dependency on `.net` file format
- Bypasses canonical JSON representation

---

## Refactored Architecture

### New Constructor Signature

```python
def __init__(
    self,
    kicad_project_or_json: str,
    python_file: str,
    preview_only: bool = True,
    create_backup: bool = True,
):
    """
    Initialize syncer with JSON or KiCad project path.

    Args:
        kicad_project_or_json: Path to .json netlist (preferred)
                               OR .kicad_pro file (deprecated)
        python_file: Target Python file path
        preview_only: If True, only preview changes
        create_backup: Create backup before overwriting
    """
```

### New Input Handling Logic

```python
path = Path(kicad_project_or_json)

if path.suffix == '.json':
    # ✅ NEW PATH: Use JSON directly (preferred)
    self.json_path = path
    logger.info(f"Using JSON netlist: {self.json_path}")

elif path.suffix == '.kicad_pro' or path.is_dir():
    # ⚠️ LEGACY PATH: Find or generate JSON (deprecated)
    warnings.warn(
        "Passing KiCad project directly is deprecated. "
        "Pass JSON netlist path instead. "
        "This will be removed in v2.0.",
        DeprecationWarning,
        stacklevel=2
    )
    self.json_path = self._find_or_generate_json(path)
    logger.warning(f"Auto-generated JSON from KiCad: {self.json_path}")

else:
    raise ValueError(
        f"Unsupported input: {path}. "
        "Expected .json netlist or .kicad_pro project file."
    )

# Load JSON data (unified path for both inputs)
self.json_data = self._load_json()
```

### New Helper Methods

#### _find_or_generate_json()

```python
def _find_or_generate_json(self, kicad_project: Path) -> Path:
    """
    Find existing JSON or generate from KiCad project.

    Args:
        kicad_project: Path to .kicad_pro or project directory

    Returns:
        Path to JSON netlist file

    Raises:
        RuntimeError: If JSON generation fails
    """
    # Determine project directory and name
    if kicad_project.is_file():
        project_dir = kicad_project.parent
        project_name = kicad_project.stem
    else:
        project_dir = kicad_project
        project_name = kicad_project.name

    # Check for existing JSON
    json_path = project_dir / f"{project_name}.json"

    if json_path.exists():
        logger.info(f"Found existing JSON: {json_path}")
        return json_path

    # Generate JSON from KiCad
    logger.info(f"No JSON found, generating from KiCad project...")
    return self._export_kicad_to_json(kicad_project)
```

#### _export_kicad_to_json()

```python
def _export_kicad_to_json(self, kicad_project: Path) -> Path:
    """
    Export KiCad project to JSON format.

    Uses KiCadSchematicParser (from #210) to parse .kicad_sch
    and export to canonical JSON format.

    Args:
        kicad_project: Path to .kicad_pro or project directory

    Returns:
        Path to generated JSON file

    Raises:
        RuntimeError: If export fails
    """
    from circuit_synth.tools.utilities.kicad_schematic_parser import KiCadSchematicParser

    # Find .kicad_sch file
    if kicad_project.is_file():
        project_dir = kicad_project.parent
        project_name = kicad_project.stem
        schematic_path = project_dir / f"{project_name}.kicad_sch"
    else:
        project_dir = kicad_project
        # Find first .kicad_sch in directory
        sch_files = list(project_dir.glob("*.kicad_sch"))
        if not sch_files:
            raise FileNotFoundError(f"No .kicad_sch files found in {project_dir}")
        schematic_path = sch_files[0]
        project_name = schematic_path.stem

    if not schematic_path.exists():
        raise FileNotFoundError(f"Schematic not found: {schematic_path}")

    # Generate JSON output path
    json_path = project_dir / f"{project_name}.json"

    # Parse and export
    logger.info(f"Parsing schematic: {schematic_path}")
    parser = KiCadSchematicParser(schematic_path)
    result = parser.parse_and_export(json_path)

    if not result.get("success"):
        raise RuntimeError(f"Failed to export KiCad to JSON: {result.get('error')}")

    logger.info(f"Successfully exported JSON: {json_path}")
    return Path(result["json_path"])
```

#### _load_json()

```python
def _load_json(self) -> dict:
    """
    Load and parse JSON netlist.

    Returns:
        Parsed JSON data as dictionary

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        JSONDecodeError: If JSON is malformed
    """
    import json

    if not self.json_path.exists():
        raise FileNotFoundError(f"JSON netlist not found: {self.json_path}")

    try:
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Loaded JSON with {len(data.get('components', {}))} components")
        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {self.json_path}: {e}") from e
```

### Updated sync() Method

The `sync()` method needs to be updated to use `self.json_data` instead of parsing `.net` files:

```python
def sync(self) -> bool:
    """Perform the synchronization from JSON to Python"""
    logger.info("=== Starting JSON to Python Synchronization ===")

    try:
        # Step 1: Convert JSON to Circuit objects
        logger.info("Step 1: Converting JSON to Circuit objects")
        circuits = self._json_to_circuits()

        if not circuits:
            logger.error("No circuits found in JSON")
            return False

        # Step 2-4: Same as before (directory creation, backup, code generation)
        # ... existing logic ...

    except Exception as e:
        logger.error(f"Synchronization failed: {e}")
        return False
```

New helper method:

```python
def _json_to_circuits(self) -> Dict[str, Circuit]:
    """
    Convert JSON data to Circuit objects.

    Returns:
        Dictionary mapping circuit names to Circuit objects
    """
    from circuit_synth.tools.utilities.models import Circuit, Component, Net

    circuits = {}

    # Parse main circuit
    circuit_name = self.json_data.get("name", "main")

    # Extract components from JSON dict format
    components = []
    for ref, comp_data in self.json_data.get("components", {}).items():
        component = Component(
            reference=comp_data.get("ref", ref),
            lib_id=comp_data.get("symbol", ""),
            value=comp_data.get("value", ""),
            footprint=comp_data.get("footprint", ""),
            position=(0.0, 0.0)  # Position not in JSON
        )
        components.append(component)

    # Extract nets from JSON dict format
    nets = []
    for net_name, connections in self.json_data.get("nets", {}).items():
        net_connections = []
        for conn in connections:
            comp_ref = conn.get("component")
            pin_num = conn.get("pin", {}).get("number", "")
            net_connections.append((comp_ref, pin_num))

        net = Net(name=net_name, connections=net_connections)
        nets.append(net)

    # Create circuit object
    circuit = Circuit(
        name=circuit_name,
        components=components,
        nets=nets,
        schematic_file=self.json_data.get("source_file", ""),
        is_hierarchical_sheet=False
    )

    circuits[circuit_name] = circuit

    # TODO: Handle subcircuits if present in JSON

    logger.info(f"Converted JSON to {len(circuits)} circuits")
    return circuits
```

---

## Migration Path

### V1 (Legacy) Usage - Still Works But Deprecated

```python
# Old way - passing KiCad project directly
syncer = KiCadToPythonSyncer(
    'my_board.kicad_pro',
    'output/main.py'
)
syncer.sync()

# Output:
# ⚠️ DeprecationWarning: Passing KiCad project directly is deprecated.
#    Pass JSON netlist path instead. This will be removed in v2.0.
# INFO: Auto-generated JSON from KiCad: my_board/my_board.json
# INFO: Using JSON netlist: my_board/my_board.json
```

### V2 (New) Usage - Recommended

```python
# New way - passing JSON directly
syncer = KiCadToPythonSyncer(
    'my_board/my_board.json',  # ✅ JSON path
    'output/main.py'
)
syncer.sync()

# Output:
# INFO: Using JSON netlist: my_board/my_board.json
# (No warnings)
```

### Workflow Integration

#### Manual Workflow

```bash
# Step 1: Export KiCad to JSON (user runs manually)
kicad-to-json my_board.kicad_pro

# Step 2: Sync JSON to Python (new syncer)
kicad-to-python my_board/my_board.json output/
```

#### Automatic Workflow (Legacy Support)

```bash
# One command - auto-generates JSON internally
kicad-to-python my_board.kicad_pro output/
# ⚠️ Shows deprecation warning
```

---

## Backward Compatibility Strategy

### Phase 1: Support Both Inputs (Current Implementation)

- Accept both `.json` and `.kicad_pro` inputs
- Show deprecation warning for `.kicad_pro`
- Auto-generate JSON if not found
- All workflows continue to work

### Phase 2: Deprecation Period (6 months)

- Update documentation to prefer JSON input
- Add logging metrics for input types used
- Notify users in release notes
- Provide migration guide

### Phase 3: Remove Legacy Support (v2.0)

- Remove `.kicad_pro` input support
- Require JSON input only
- Simplify codebase

---

## API Changes Summary

### Constructor

**Before:**
```python
KiCadToPythonSyncer(kicad_project: str, python_file: str, ...)
```

**After:**
```python
KiCadToPythonSyncer(kicad_project_or_json: str, python_file: str, ...)
```

### New Methods

| Method | Purpose |
|--------|---------|
| `_find_or_generate_json(kicad_project)` | Find existing JSON or generate from KiCad |
| `_export_kicad_to_json(kicad_project)` | Export KiCad to JSON using KiCadSchematicParser |
| `_load_json()` | Load and parse JSON file |
| `_json_to_circuits()` | Convert JSON data to Circuit objects |

### Removed Direct Usage

- ❌ Direct `.net` file parsing in main sync path
- ❌ `KiCadNetlistParser` usage in sync workflow
- ✅ Still used internally by KiCadParser for netlist generation

---

## Test Plan

### Unit Tests: test_kicad_to_python_syncer_refactored.py

#### Test 1: Accept JSON File Path

```python
def test_accept_json_file_path(tmp_path):
    """Test accepting .json file path as input."""
    # Create sample JSON netlist
    json_file = tmp_path / "test.json"
    json_data = {
        "name": "test_circuit",
        "components": {
            "R1": {"ref": "R1", "symbol": "Device:R", "value": "10k", "footprint": ""}
        },
        "nets": {},
        "source_file": "test.kicad_sch"
    }
    json_file.write_text(json.dumps(json_data))

    # Create syncer with JSON path
    syncer = KiCadToPythonSyncer(
        str(json_file),
        str(tmp_path / "output.py")
    )

    # Verify JSON was loaded
    assert syncer.json_path == json_file
    assert syncer.json_data["name"] == "test_circuit"
    assert len(syncer.json_data["components"]) == 1
```

#### Test 2: Accept KiCad Project Path (Legacy)

```python
def test_accept_kicad_pro_legacy(tmp_path, mocker):
    """Test accepting .kicad_pro with deprecation warning."""
    # Create minimal KiCad project
    kicad_pro = tmp_path / "test.kicad_pro"
    kicad_pro.write_text("{}")

    # Mock _find_or_generate_json to avoid actual parsing
    mock_json = tmp_path / "test.json"
    mocker.patch.object(
        KiCadToPythonSyncer,
        '_find_or_generate_json',
        return_value=mock_json
    )
    mocker.patch.object(
        KiCadToPythonSyncer,
        '_load_json',
        return_value={"name": "test", "components": {}, "nets": {}}
    )

    # Create syncer - should trigger deprecation warning
    with pytest.warns(DeprecationWarning, match="Passing KiCad project directly"):
        syncer = KiCadToPythonSyncer(
            str(kicad_pro),
            str(tmp_path / "output.py")
        )

    # Verify fallback path was used
    assert syncer.json_path == mock_json
```

#### Test 3: _find_or_generate_json() - JSON Exists

```python
def test_find_existing_json(tmp_path):
    """Test finding existing JSON file."""
    # Create KiCad project and JSON
    kicad_pro = tmp_path / "test.kicad_pro"
    kicad_pro.write_text("{}")

    json_file = tmp_path / "test.json"
    json_file.write_text('{"name": "test", "components": {}, "nets": {}}')

    # Create syncer
    syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)

    # Should find existing JSON
    found_json = syncer._find_or_generate_json(kicad_pro)
    assert found_json == json_file
```

#### Test 4: _find_or_generate_json() - Generate JSON

```python
def test_generate_json_when_missing(tmp_path, mocker):
    """Test generating JSON when it doesn't exist."""
    kicad_pro = tmp_path / "test.kicad_pro"
    kicad_pro.write_text("{}")

    # Mock _export_kicad_to_json
    expected_json = tmp_path / "test.json"
    mocker.patch.object(
        KiCadToPythonSyncer,
        '_export_kicad_to_json',
        return_value=expected_json
    )

    syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)

    # Should call export when JSON doesn't exist
    result = syncer._find_or_generate_json(kicad_pro)

    assert result == expected_json
    KiCadToPythonSyncer._export_kicad_to_json.assert_called_once()
```

#### Test 5: _export_kicad_to_json() Integration

```python
def test_export_kicad_to_json(tmp_path, mocker):
    """Test exporting KiCad to JSON using KiCadSchematicParser."""
    # Create minimal project structure
    kicad_pro = tmp_path / "test.kicad_pro"
    kicad_pro.write_text("{}")

    kicad_sch = tmp_path / "test.kicad_sch"
    kicad_sch.write_text("(kicad_sch)")

    # Mock KiCadSchematicParser
    mock_parser = mocker.Mock()
    mock_parser.parse_and_export.return_value = {
        "success": True,
        "json_path": str(tmp_path / "test.json")
    }

    mocker.patch(
        'circuit_synth.tools.utilities.kicad_schematic_parser.KiCadSchematicParser',
        return_value=mock_parser
    )

    syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)

    # Should use KiCadSchematicParser
    result = syncer._export_kicad_to_json(kicad_pro)

    assert result == tmp_path / "test.json"
    mock_parser.parse_and_export.assert_called_once()
```

#### Test 6: _load_json() Success

```python
def test_load_json_success(tmp_path):
    """Test loading valid JSON file."""
    json_file = tmp_path / "test.json"
    json_data = {
        "name": "test",
        "components": {"R1": {}},
        "nets": {}
    }
    json_file.write_text(json.dumps(json_data))

    syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
    syncer.json_path = json_file

    loaded = syncer._load_json()

    assert loaded == json_data
    assert loaded["name"] == "test"
```

#### Test 7: _load_json() File Not Found

```python
def test_load_json_file_not_found(tmp_path):
    """Test error handling for missing JSON file."""
    syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
    syncer.json_path = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError, match="JSON netlist not found"):
        syncer._load_json()
```

#### Test 8: _load_json() Invalid JSON

```python
def test_load_json_invalid_format(tmp_path):
    """Test error handling for malformed JSON."""
    json_file = tmp_path / "invalid.json"
    json_file.write_text("{invalid json content")

    syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
    syncer.json_path = json_file

    with pytest.raises(ValueError, match="Invalid JSON format"):
        syncer._load_json()
```

#### Test 9: _json_to_circuits() Conversion

```python
def test_json_to_circuits_conversion(tmp_path):
    """Test converting JSON to Circuit objects."""
    json_data = {
        "name": "test_circuit",
        "components": {
            "R1": {
                "ref": "R1",
                "symbol": "Device:R",
                "value": "10k",
                "footprint": "R_0603"
            },
            "C1": {
                "ref": "C1",
                "symbol": "Device:C",
                "value": "100nF",
                "footprint": "C_0603"
            }
        },
        "nets": {
            "VCC": [
                {"component": "R1", "pin": {"number": "1"}},
                {"component": "C1", "pin": {"number": "1"}}
            ],
            "GND": [
                {"component": "C1", "pin": {"number": "2"}}
            ]
        },
        "source_file": "test.kicad_sch"
    }

    syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
    syncer.json_data = json_data

    circuits = syncer._json_to_circuits()

    assert len(circuits) == 1
    assert "test_circuit" in circuits

    circuit = circuits["test_circuit"]
    assert len(circuit.components) == 2
    assert len(circuit.nets) == 2

    # Verify component data
    refs = [c.reference for c in circuit.components]
    assert "R1" in refs
    assert "C1" in refs

    # Verify net data
    net_names = [n.name for n in circuit.nets]
    assert "VCC" in net_names
    assert "GND" in net_names
```

#### Test 10: Unsupported Input Type

```python
def test_unsupported_input_type(tmp_path):
    """Test error for unsupported file type."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not a valid input")

    with pytest.raises(ValueError, match="Unsupported input"):
        KiCadToPythonSyncer(str(txt_file), str(tmp_path / "output.py"))
```

### Integration Tests: test_kicad_syncer_json_workflow.py

#### Test 11: End-to-End JSON Workflow

```python
def test_end_to_end_json_workflow(tmp_path):
    """Test complete workflow: JSON → Python generation."""
    # Create JSON netlist
    json_file = tmp_path / "test.json"
    json_data = {
        "name": "voltage_divider",
        "components": {
            "R1": {"ref": "R1", "symbol": "Device:R", "value": "10k", "footprint": "R_0603"},
            "R2": {"ref": "R2", "symbol": "Device:R", "value": "10k", "footprint": "R_0603"}
        },
        "nets": {
            "VIN": [{"component": "R1", "pin": {"number": "1"}}],
            "VOUT": [
                {"component": "R1", "pin": {"number": "2"}},
                {"component": "R2", "pin": {"number": "1"}}
            ],
            "GND": [{"component": "R2", "pin": {"number": "2"}}]
        },
        "source_file": "test.kicad_sch"
    }
    json_file.write_text(json.dumps(json_data, indent=2))

    # Run syncer with JSON input
    output_file = tmp_path / "circuit.py"
    syncer = KiCadToPythonSyncer(
        str(json_file),
        str(output_file),
        preview_only=False
    )

    success = syncer.sync()

    assert success
    assert output_file.exists()

    # Verify generated Python content
    content = output_file.read_text()
    assert "def main" in content or "@circuit" in content
    assert "R1" in content or "r1" in content
    assert "R2" in content or "r2" in content
```

#### Test 12: Round-Trip Test (KiCad → JSON → Python)

```python
def test_round_trip_kicad_json_python(tmp_path, sample_kicad_project):
    """Test complete round-trip from KiCad through JSON to Python."""
    # Step 1: Export KiCad to JSON (using KiCadSchematicParser)
    from circuit_synth.tools.utilities.kicad_schematic_parser import KiCadSchematicParser

    json_file = tmp_path / "test.json"
    parser = KiCadSchematicParser(sample_kicad_project / "test.kicad_sch")
    result = parser.parse_and_export(json_file)

    assert result["success"]
    assert json_file.exists()

    # Step 2: Sync JSON to Python (using refactored syncer)
    output_file = tmp_path / "circuit.py"
    syncer = KiCadToPythonSyncer(
        str(json_file),
        str(output_file),
        preview_only=False
    )

    success = syncer.sync()

    assert success
    assert output_file.exists()
```

#### Test 13: Hierarchical Circuit Support

```python
def test_hierarchical_circuit_json(tmp_path):
    """Test syncer with hierarchical JSON structure."""
    json_data = {
        "name": "main",
        "components": {},
        "nets": {},
        "subcircuits": [
            {
                "name": "power_supply",
                "components": {
                    "U1": {"ref": "U1", "symbol": "Regulator", "value": "LM7805", "footprint": ""}
                },
                "nets": {}
            }
        ],
        "source_file": "main.kicad_sch"
    }

    json_file = tmp_path / "hierarchical.json"
    json_file.write_text(json.dumps(json_data))

    syncer = KiCadToPythonSyncer(
        str(json_file),
        str(tmp_path / "main.py"),
        preview_only=False
    )

    success = syncer.sync()
    assert success
```

#### Test 14: Backward Compatibility - Legacy Path Still Works

```python
def test_backward_compatibility_kicad_input(tmp_path, sample_kicad_project):
    """Test that old KiCad project input still works with warning."""
    output_file = tmp_path / "circuit.py"

    # Should work but show deprecation warning
    with pytest.warns(DeprecationWarning):
        syncer = KiCadToPythonSyncer(
            str(sample_kicad_project / "test.kicad_pro"),
            str(output_file),
            preview_only=False
        )

        success = syncer.sync()
        assert success
```

#### Test 15: Error Handling - JSON Export Failure

```python
def test_error_handling_json_export_failure(tmp_path, mocker):
    """Test error handling when JSON export fails."""
    kicad_pro = tmp_path / "test.kicad_pro"
    kicad_pro.write_text("{}")

    # Mock parser to return failure
    mock_parser = mocker.Mock()
    mock_parser.parse_and_export.return_value = {
        "success": False,
        "error": "Failed to parse schematic"
    }

    mocker.patch(
        'circuit_synth.tools.utilities.kicad_schematic_parser.KiCadSchematicParser',
        return_value=mock_parser
    )

    with pytest.raises(RuntimeError, match="Failed to export KiCad to JSON"):
        syncer = KiCadToPythonSyncer(str(kicad_pro), str(tmp_path / "out.py"))
```

---

## Acceptance Criteria

### Functional Requirements

- [ ] **FR1:** Accept `.json` file path as primary input
- [ ] **FR2:** Accept `.kicad_pro` file path with deprecation warning (backward compatible)
- [ ] **FR3:** `_find_or_generate_json()` finds existing JSON or generates new one
- [ ] **FR4:** `_export_kicad_to_json()` uses `KiCadSchematicParser` from #210
- [ ] **FR5:** `_load_json()` loads and parses JSON netlist
- [ ] **FR6:** `_json_to_circuits()` converts JSON to Circuit objects
- [ ] **FR7:** No direct `.net` file parsing in main sync path
- [ ] **FR8:** Python code generation works from JSON data
- [ ] **FR9:** Hierarchical circuits supported (subcircuits in JSON)
- [ ] **FR10:** All error cases handled gracefully

### Non-Functional Requirements

- [ ] **NFR1:** 15+ tests covering all scenarios
- [ ] **NFR2:** All existing tests still pass (no regressions)
- [ ] **NFR3:** Deprecation warnings properly formatted
- [ ] **NFR4:** Logging at appropriate levels (INFO, WARNING, ERROR)
- [ ] **NFR5:** Code follows existing patterns and style
- [ ] **NFR6:** Documentation updated (docstrings, comments)
- [ ] **NFR7:** Performance: No significant slowdown vs. current implementation

### Quality Gates

1. **All tests pass:** 15+ new tests + existing integration tests
2. **Code review:** PR approved
3. **Migration guide:** Clear documentation for users
4. **Deprecation policy:** Timeline communicated

---

## Implementation Checklist

### Day 1: PRD and Analysis ✅
- [x] Write PRD (this document)
- [x] Review existing code
- [x] Understand dependencies (#210)

### Day 2: Test Implementation (TDD)
- [ ] Create `tests/unit/test_kicad_to_python_syncer_refactored.py`
- [ ] Create `tests/integration/test_kicad_syncer_json_workflow.py`
- [ ] Write 15+ test cases (all should fail initially)
- [ ] Verify test structure and mocking setup

### Day 3: Core Implementation
- [ ] Modify `KiCadToPythonSyncer.__init__()` to accept both inputs
- [ ] Implement `_find_or_generate_json()`
- [ ] Implement `_export_kicad_to_json()`
- [ ] Implement `_load_json()`
- [ ] Add deprecation warnings

### Day 4: Integration and Conversion
- [ ] Implement `_json_to_circuits()`
- [ ] Update `sync()` method to use JSON data
- [ ] Remove direct `.net` parsing from sync path
- [ ] Handle hierarchical circuits
- [ ] Run tests, fix failures

### Day 5: Testing and PR
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Existing tests still pass (no regressions)
- [ ] Update documentation
- [ ] Create PR with detailed description

---

## Migration Guide for Users

### For Developers

**Before (still works):**
```python
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer

syncer = KiCadToPythonSyncer(
    'my_board.kicad_pro',  # Old way
    'output/main.py'
)
syncer.sync()
```

**After (recommended):**
```python
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer

# Step 1: Export KiCad to JSON first (manual or automated)
from circuit_synth.tools.utilities.kicad_schematic_parser import KiCadSchematicParser
parser = KiCadSchematicParser('my_board/my_board.kicad_sch')
parser.parse_and_export('my_board/my_board.json')

# Step 2: Sync JSON to Python
syncer = KiCadToPythonSyncer(
    'my_board/my_board.json',  # New way ✅
    'output/main.py'
)
syncer.sync()
```

### For CLI Users

**Before:**
```bash
kicad-to-python my_board.kicad_pro output/
```

**After:**
```bash
# Option 1: Two-step (explicit)
kicad-to-json my_board.kicad_pro
kicad-to-python my_board/my_board.json output/

# Option 2: One-step (automatic JSON generation with warning)
kicad-to-python my_board.kicad_pro output/
# ⚠️ Shows deprecation warning
```

---

## Dependencies and Risks

### Dependencies

1. **KiCadSchematicParser (#210)** - ✅ Complete
   - Required for JSON export
   - Provides `parse_and_export()` method

2. **Circuit.to_circuit_synth_json() (#210)** - ✅ Complete
   - Required for JSON schema format
   - Already implemented in models.py

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing workflows | Medium | High | Maintain backward compatibility with deprecation warnings |
| JSON schema changes | Low | Medium | Comprehensive testing of JSON format |
| Performance degradation | Low | Low | Profile and optimize if needed |
| User confusion | Medium | Low | Clear documentation and migration guide |

---

## Open Questions

1. **Q: Should we cache generated JSON files?**
   A: Yes, cache in project directory. Reuse if exists, regenerate if .kicad_sch is newer.

2. **Q: How to handle hierarchical circuits in JSON?**
   A: Support `subcircuits` array in JSON schema. Parse recursively in `_json_to_circuits()`.

3. **Q: Should deprecation warning be suppressible?**
   A: No, users should migrate to JSON input. Warning is important signal.

4. **Q: What happens if both .kicad_pro and .json exist?**
   A: If user passes .kicad_pro, check for existing JSON and use it (with message).

5. **Q: Should we validate JSON schema?**
   A: Yes, basic validation (required fields). Full schema validation can be added later.

---

## References

### Code Files

- `src/circuit_synth/tools/kicad_integration/kicad_to_python_sync.py` - Main refactor target
- `src/circuit_synth/tools/utilities/kicad_schematic_parser.py` - JSON export (from #210)
- `src/circuit_synth/tools/utilities/models.py` - Circuit, Component, Net models
- `src/circuit_synth/tools/utilities/python_code_generator.py` - Python code generation

### Documentation

- `docs/PRD_KICAD_TO_JSON_EXPORT.md` - #210 PRD (dependency)
- `PROJECT_STATUS.md` - Phase 0 progress tracking

### GitHub Issues

- Issue #211 - This task
- Issue #210 - KiCad → JSON export (dependency)
- Epic #208 - Phase 0: Make JSON the Canonical Format

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Author:** Claude Code
**Status:** Ready for Implementation
