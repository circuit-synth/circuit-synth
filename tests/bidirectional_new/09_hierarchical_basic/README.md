# Test 09: Hierarchical Circuits (Basic)

## Purpose

Validates 2-3 level hierarchical circuit structures (subcircuits).

## Test Cases

### Test 9.1: Two-Level Hierarchy (Main + Sub)
- `main.py` calls `subcircuit.py`
- Generate KiCad → `main.kicad_sch` + `subcircuit.kicad_sch`
- Import back → verify structure preserved

### Test 9.2: Hierarchical Ports
- Subcircuit has input/output ports (VIN, VOUT)
- Verify hierarchical pins in KiCad sheet
- Import back → verify ports in Python

### Test 9.3: Multiple Instances
- Main calls subcircuit 2x (U1, U2)
- Verify unique instances in KiCad
- Verify components have unique references (U1.R1, U2.R1)

### Test 9.4: Three-Level Hierarchy
- `main.py` → `sub1.py` → `sub2.py`
- Verify all 3 levels in KiCad
- Import back → verify 3 Python files

### Test 9.5: Hierarchical Round-Trip
- Full cycle: Python hierarchy → KiCad → Python
- Verify structure preserved
- Verify all files generated

## Manual Setup

**Fixtures needed:**
- `hierarchical_simple/` - main + 1 subcircuit
- `hierarchical_complex/` - 3-level hierarchy

---

**Status**: 🚧 Setup required
**Priority**: P2
**Time**: 40 min
