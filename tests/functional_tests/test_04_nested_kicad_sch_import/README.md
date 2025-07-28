# Test 4: Complex Hierarchical File Structure with Nested Subcircuits

## Overview

This test validates the KiCad-to-Python converter's ability to handle deep hierarchical circuit structures with multiple subcircuit levels.

## Test Structure

### 3-Level Circuit Hierarchy:
```
main.py
├── resistor_divider.py  
    └── capacitor_bank.py
```

### Circuit Description:
- **main_circuit**: System-level power and signal routing
- **resistor_divider**: Voltage division (R1, R2) + power conditioning
- **capacitor_bank**: Multi-stage filtering (C1: 100nF, C2: 10µF, C3: 1µF)

## Files in This Test

### Python Reference Files (Complete)
- `reference_python_project/main.py` ✅ - Top-level circuit with VIN/GND/MID nets
- `reference_python_project/resistor_divider.py` ✅ - Enhanced resistor divider + capacitor bank import
- `reference_python_project/capacitor_bank.py` ✅ - Multi-stage power filtering

### KiCad Reference Project (Manual Setup Required)
- `complex_hierarchical_reference/` - Renamed from previous project
- **⚠️ MANUAL SETUP NEEDED**: You need to open the KiCad project and add the capacitor bank subcircuit

### Test Code
- `test_complex_hierarchical_structure.py` ✅ - Complete test with hierarchical validation

## Manual Setup Required

### 1. Open KiCad Project
```bash
cd complex_hierarchical_reference/
open complex_hierarchical.kicad_pro  # or use KiCad directly
```

### 2. Add Capacitor Bank Subcircuit
In KiCad, you need to:

1. **Open the resistor_divider.kicad_sch sheet**
2. **Add hierarchical sheet** for capacitor bank:
   - Add → Hierarchical Sheet
   - Name: "CapacitorBank"
   - File: "capacitor_bank.kicad_sch"
   - Size: Appropriate for the design

3. **Create capacitor_bank.kicad_sch** with:
   - **C1**: 100nF, 0603 footprint, connected VCC→GND
   - **C2**: 10µF, 0805 footprint, connected VCC→GND  
   - **C3**: 1µF, 0603 footprint, connected VCC→GND
   - **Hierarchical labels**: VCC (input), GND (input)

4. **Connect in resistor_divider.kicad_sch**:
   - Connect capacitor bank VCC to the VIN net
   - Connect capacitor bank GND to the GND net

5. **Save all files**

### 3. Run Test
```bash
# Run with file preservation for manual inspection
PRESERVE_FILES=1 uv run pytest test_complex_hierarchical_structure.py -v

# Or run normally  
uv run pytest test_complex_hierarchical_structure.py -v
```

## Expected Test Results

### File Structure Validation:
- ✅ 3 Python files generated: `main.py`, `resistor_divider.py`, `capacitor_bank.py`
- ✅ Correct import chain: main → resistor_divider → capacitor_bank
- ✅ Each file contains only its relevant circuit logic
- ✅ All files syntactically valid and executable

### Component Separation:
- ✅ `main.py`: Only net definitions and subcircuit instantiation
- ✅ `resistor_divider.py`: R1, R2 components + capacitor_bank import
- ✅ `capacitor_bank.py`: C1, C2, C3 filtering components

### Import Chain:
```python
# main.py
from resistor_divider import resistor_divider

# resistor_divider.py  
from capacitor_bank import capacitor_bank

# capacitor_bank.py
# (leaf node - no circuit imports)
```

## Success Criteria

This test passes when:
1. **File Structure**: Exactly 3 Python files generated
2. **Import Relationships**: Correct hierarchical import chain
3. **Component Separation**: Each file contains appropriate components only
4. **Syntax Validation**: All generated files compile without errors
5. **Hierarchical Parameters**: Proper net passing through all levels

## Next Steps

After this test is working:
- Test 5: Add components in KiCad and observe Python updates
- Test 6: Add components in Python and observe KiCad preservation
- Test 7-8: Test hierarchy restructuring in both directions

---

**Status**: Ready for manual KiCad setup and testing