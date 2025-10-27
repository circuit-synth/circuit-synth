# PRD: Python API for KiCad Project Import

**Status**: Draft for Review
**Created**: 2025-01-27
**Owner**: Circuit-Synth Team
**Related**: Automated Bidirectional Tests (PR #356)

---

## Executive Summary

Create a Python API function `import_kicad_project()` that programmatically imports KiCad projects into circuit-synth Circuit objects. This enables automated testing of bidirectional sync and provides a cleaner programmatic interface than CLI subprocess calls.

## Problem Statement

### Current State
- **CLI tool exists**: `kicad-to-python` command-line tool works well
- **No Python API**: Can only call via subprocess, no programmatic access
- **Testing blocked**: 10 automated tests blocked without import API
- **User friction**: Python users can't import KiCad programmatically

### Why Now?
- **Automated tests ready**: 39 tests implemented, 10 blocked on this API
- **User demand**: Programmatic import is a natural use case
- **Code reuse**: CLI already has all the logic, just needs wrapping

## Goals

### Primary Goals
1. **Enable automated testing**: Unblock 10 import/roundtrip tests
2. **Provide programmatic API**: Python function to import KiCad projects
3. **Match CLI functionality**: Support same inputs/outputs as CLI
4. **Clean API surface**: Pythonic interface, not just CLI wrapper

### Non-Goals (For Initial Version)
- ❌ Change CLI implementation or behavior
- ❌ Add new import features beyond CLI
- ❌ Support streaming/async import
- ❌ GUI integration

## Proposed API

### Function Signature

```python
def import_kicad_project(
    kicad_project: Union[str, Path],
    *,
    output_python_file: Optional[Union[str, Path]] = None,
    preview_only: bool = False,
    create_backup: bool = True,
    return_circuit: bool = True,
) -> Union[Circuit, str, None]:
    """
    Import KiCad project to circuit-synth Circuit object.

    Args:
        kicad_project: Path to:
            - .kicad_pro file
            - .json netlist (preferred)
            - Directory containing KiCad project

        output_python_file: Optional Python file to write
            - If None: Only return Circuit object (default)
            - If provided: Write Python code to file

        preview_only: If True, don't write files, only return preview
        create_backup: Create .backup file before overwriting
        return_circuit: If True, return Circuit object (default)

    Returns:
        Circuit object if return_circuit=True
        Generated Python code if preview_only=True
        None if only writing file

    Raises:
        FileNotFoundError: If KiCad project not found
        ValueError: If JSON is malformed or invalid
        RuntimeError: If import fails

    Examples:
        # Import to Circuit object (most common)
        circuit = import_kicad_project("my_project.kicad_pro")
        print(f"Found {len(circuit.components)} components")

        # Import and save to Python file
        import_kicad_project(
            "my_project.json",
            output_python_file="circuit.py"
        )

        # Preview without writing
        code = import_kicad_project(
            "my_project.kicad_pro",
            preview_only=True
        )
        print(code)

        # Import from directory
        circuit = import_kicad_project("/path/to/kicad/project/")
    """
```

### Module Location

```
src/circuit_synth/kicad/importer.py  # New file

OR

src/circuit_synth/kicad/import_project.py  # Alternative
```

**Import path:**
```python
from circuit_synth.kicad.importer import import_kicad_project
```

### Return Type: Circuit Object

The function returns a `circuit_synth.core.circuit.Circuit` object with:

```python
class Circuit:
    name: str                          # Circuit name from KiCad
    components: Dict[str, Component]   # Components by reference
    nets: List[Net]                    # Net connections
    # ... other Circuit attributes
```

## Implementation Strategy

### Option 1: Wrap Existing CLI Logic (Recommended)

**Approach**: Extract core logic from `KiCadToPythonSyncer` into reusable functions.

**Pros:**
- ✅ Reuses existing, tested code
- ✅ Maintains CLI/API consistency
- ✅ Quick to implement (refactor, don't rewrite)
- ✅ Single source of truth

**Cons:**
- ⚠️ Need to refactor CLI class for library use
- ⚠️ May expose some CLI-specific details

**Implementation:**
```python
# src/circuit_synth/kicad/importer.py

from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer
from circuit_synth.core.circuit import Circuit

def import_kicad_project(
    kicad_project: Union[str, Path],
    *,
    output_python_file: Optional[Union[str, Path]] = None,
    preview_only: bool = False,
    create_backup: bool = True,
    return_circuit: bool = True,
) -> Union[Circuit, str, None]:
    """Import KiCad project to Circuit object."""

    # Use dummy output file if only returning Circuit
    temp_output = output_python_file or "temp_output.py"

    # Create syncer
    syncer = KiCadToPythonSyncer(
        kicad_project_or_json=str(kicad_project),
        python_file=str(temp_output),
        preview_only=preview_only or (output_python_file is None),
        create_backup=create_backup,
    )

    # Get circuits from JSON
    circuits = syncer._json_to_circuits()

    if not circuits:
        raise RuntimeError("No circuits found in KiCad project")

    # Get main circuit
    main_circuit = circuits.get("main") or list(circuits.values())[0]

    # Convert from models.Circuit to circuit_synth.Circuit
    circuit = _convert_to_circuit_synth_circuit(main_circuit)

    # Handle output options
    if preview_only:
        # Generate and return Python code
        code = syncer.code_generator.generate_code_for_circuit(main_circuit)
        return code if not return_circuit else circuit

    if output_python_file:
        # Write Python file
        syncer.sync()

    return circuit if return_circuit else None


def _convert_to_circuit_synth_circuit(models_circuit) -> Circuit:
    """Convert from models.Circuit to circuit_synth.Circuit"""
    # Convert components
    # Convert nets
    # Build Circuit object
    # Return
    pass
```

### Option 2: New Implementation (Not Recommended)

**Approach**: Write new import logic from scratch.

**Pros:**
- ✅ Clean API from start
- ✅ No CLI baggage

**Cons:**
- ❌ Code duplication with CLI
- ❌ More work, more testing
- ❌ Two implementations to maintain

**Decision**: Use Option 1 (wrap existing logic)

## Data Flow

```
┌──────────────────┐
│  KiCad Project   │
│  (.kicad_pro)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Parse KiCad     │
│  Generate JSON   │  (KiCadParser)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   JSON Netlist   │
│   (.json)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  JSON → Circuit  │  (_json_to_circuits)
│  models.Circuit  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Convert to      │  (_convert_to_circuit_synth_circuit)
│  Circuit Object  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Return Circuit  │
│  to User         │
└──────────────────┘
```

## Type Conversions

The existing CLI uses `models.Circuit` (from `tools.utilities.models`), but we need to return `circuit_synth.Circuit` (from `core.circuit`).

### models.Circuit vs circuit_synth.Circuit

Need to understand the differences to convert properly.

**Questions for User:**
1. Are `models.Circuit` and `circuit_synth.Circuit` the same class?
2. If different, what's the mapping between them?
3. Should we just return `models.Circuit` and let caller convert?

## Testing Strategy

### Unit Tests
```python
def test_import_from_kicad_pro():
    """Test importing from .kicad_pro file"""
    circuit = import_kicad_project("test.kicad_pro")
    assert len(circuit.components) == 2

def test_import_from_json():
    """Test importing from .json netlist (preferred)"""
    circuit = import_kicad_project("test.json")
    assert circuit.name == "test"

def test_import_with_output_file():
    """Test importing and writing Python file"""
    import_kicad_project(
        "test.kicad_pro",
        output_python_file="output.py"
    )
    assert Path("output.py").exists()

def test_preview_mode():
    """Test preview returns code without writing"""
    code = import_kicad_project(
        "test.kicad_pro",
        preview_only=True
    )
    assert "def" in code
    assert "circuit" in code
```

### Integration Tests (Will Unblock)
All tests in `tests/test_bidirectional_automated/`:
- `test_kicad_to_python.py` - 4 tests
- `test_roundtrip.py` - 3 tests (partial)
- `test_position_preservation.py` - 1 test (partial)
- `test_component_operations.py` - 2 tests (partial)

**Total unblocked**: ~10 tests

## Migration Path

### Phase 1: New API (This PR)
- Create `import_kicad_project()` function
- Wrap existing `KiCadToPythonSyncer` logic
- Add unit tests
- Update automated tests to use new API

### Phase 2: Documentation (Same PR)
- Add docstring examples
- Update README with import examples
- Add to API reference docs

### Phase 3: CLI Unchanged (Future)
- Keep CLI as-is for now
- CLI can eventually call new API (refactor)
- Maintain backward compatibility

## Questions for User

### 1. Type System
**Q**: Are `models.Circuit` and `circuit_synth.Circuit` the same?
- If yes: Can return directly
- If no: Need conversion logic

**Where to look:**
- `src/circuit_synth/tools/utilities/models.py`
- `src/circuit_synth/core/circuit.py`

### 2. API Design Preferences
**Q**: Should `output_python_file` be optional?
- **Option A**: Optional (default None) - returns Circuit object
- **Option B**: Required - always writes file
- **Option C**: Separate functions: `import_kicad()` vs `convert_kicad_to_python()`

**Recommendation**: Option A (optional, default returns Circuit)

### 3. Module Location
**Q**: Where should the function live?
- **Option A**: `src/circuit_synth/kicad/importer.py` (new file)
- **Option B**: Add to existing file (which one?)
- **Option C**: `src/circuit_synth/__init__.py` (top-level convenience)

**Recommendation**: Option A, with convenience import in `__init__.py`

### 4. Error Handling
**Q**: How strict should validation be?
- **Option A**: Raise exceptions on any error (fail fast)
- **Option B**: Warn and continue with partial data
- **Option C**: Return Result object with success/error info

**Recommendation**: Option A (raise exceptions, cleaner for API)

### 5. Backward Compatibility
**Q**: Should we support deprecated paths?
- KiCadToPythonSyncer has deprecation warnings for .kicad_pro
- Should new API also warn?

**Recommendation**: Yes, mirror CLI behavior

### 6. Return Type Flexibility
**Q**: Should we support returning just components/nets?
```python
components = import_kicad_project("test.kicad_pro", return_type="components")
nets = import_kicad_project("test.kicad_pro", return_type="nets")
```

**Recommendation**: No, keep simple for V1. Caller can extract from Circuit.

## Success Criteria

### Must Have
- ✅ Function accepts .kicad_pro, .json, and directory paths
- ✅ Returns valid circuit_synth.Circuit object
- ✅ 10 automated tests unblocked and passing
- ✅ Unit tests for new function
- ✅ Docstring with examples

### Nice to Have
- ✅ Optionally writes Python file
- ✅ Preview mode returns code
- ✅ Detailed error messages
- ✅ Type hints throughout

### Out of Scope
- ❌ Streaming/async import
- ❌ Partial/incremental import
- ❌ GUI integration
- ❌ CLI refactor (separate effort)

## Timeline Estimate

**Phase 1** (Core Implementation): 2-3 hours
- Write `import_kicad_project()` function
- Handle type conversions
- Basic error handling

**Phase 2** (Testing): 1-2 hours
- Unit tests
- Update automated tests
- Verify all 10 tests pass

**Phase 3** (Documentation): 30 mins
- Docstrings
- README examples
- CHANGELOG entry

**Total**: 4-6 hours

## Open Questions for Review

Before starting implementation, need answers to:

1. **Type conversion**: Are `models.Circuit` and `circuit_synth.Circuit` compatible?
2. **Module location**: Where should `import_kicad_project()` live?
3. **API design**: Is optional `output_python_file` the right design?
4. **Error handling**: Raise exceptions or return errors?
5. **Scope**: Any other features needed for V1?

---

**Ready to implement after user answers questions above.**
