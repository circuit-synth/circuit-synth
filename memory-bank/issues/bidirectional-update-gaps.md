# Bidirectional Update Implementation Gaps

## Issue: False "Synchronization" Mode

### Problem Description
The `kicad-to-python` command claims to "synchronize" and "update" existing Python files, but actually performs complete file regeneration, losing all user modifications.

### Evidence
```bash
# Command that should preserve user changes:
uv run kicad-to-python <kicad_project> <existing_python_file> --backup

# Actual behavior:
- Creates backup ✅
- Logs "CODE_UPDATE: Updating Python file" ✅  
- Completely overwrites existing file ❌
- Loses all user modifications ❌
```

### Root Cause
Missing selective update logic - no comparison between existing Python code and new KiCad changes.

## Issue: Reference Designator Parsing Bug

### Problem Description
KiCad files contain proper reference designators (`C1`, `U1`) but the Python generator outputs broken references (`C?`, `U?`).

### Evidence
```python
# KiCad files contain: C1, U1
# Python output generates:
c_ = Component(symbol="Device:C", ref="C?", ...)  # Should be ref="C1"
u_ = Component(symbol="RF_Module:ESP32-C6-MINI-1", ref="U?", ...)  # Should be ref="U1"
```

### Location
Likely in `circuit_synth.tools.kicad_netlist_parser` or related netlist processing.

## Issue: Missing Canonical Analysis Module

### Problem Description
The bidirectional update plan references `circuit_synth.kicad.canonical` module which doesn't exist.

### Required Components
```python
@dataclass
class CanonicalConnection:
    component_index: int
    pin: str  
    net_name: str
    component_type: str

class CanonicalCircuit:
    def from_circuit(circuit: Circuit) -> CanonicalCircuit
    def from_kicad(kicad_data) -> CanonicalCircuit
    def get_structural_fingerprint() -> str
```

### Impact
Without canonical analysis, impossible to implement selective updates that preserve user modifications.

## Solution Priority
1. **High**: Fix reference designator parsing (quick win)
2. **High**: Implement canonical analysis module (foundation)  
3. **Medium**: Build selective update engine (main feature)

## Testing Framework Available
Complete step-by-step testing workflow in `bidirectional_update_test/` ready for validation.