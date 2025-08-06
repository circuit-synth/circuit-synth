# Bidirectional Update Feature - Progress Notes

## Date: 2025-08-06

### Initial Investigation

**Goal**: Enable re-running Python circuit generation without losing manual KiCad edits

**Test Project**: simple_voltage_divider
- 2 resistors (R1, R2) 
- 3 nets (+5V, GND, Vout)
- Basic series voltage divider circuit

### Key Findings

#### 1. Position Extraction Working ✅
- Created `test_position_extraction.py` script
- Successfully extracts component positions from KiCad .kicad_sch files
- Extracts: reference, value, footprint, position (x,y), UUID
- Ready to use for preservation logic

#### 2. File Always Regenerated ❌
**Test Setup:**
- Generated initial KiCad project with `main.py`
- Re-ran `main.py` without any changes
- Expected: File should remain unchanged
- Actual: File completely regenerated (682 lines → 571 lines)

**Evidence:**
```python
# Even with force_regenerate=False
circuit.generate_kicad_project("simple_voltage_divider", force_regenerate=False)
```
Still regenerates the entire file, losing:
- Manual formatting
- Wire routing
- Text annotations  
- Component positioning
- User customizations

#### 3. Quote Escaping Bug 🐛
**Problem**: Power symbol descriptions contain embedded quotes that break KiCad parser
```
Line 171: (property "Description" "Power symbol creates a global label with name "GND" , ground"
Line 276: (property "Description" "Power symbol creates a global label with name "+5V""
```
**Error**: KiCad expects '(' at line 171, offset 76
**Impact**: Generated files cannot be opened in KiCad

#### 4. API vs Implementation Gap
- API has `force_regenerate` parameter
- Documentation suggests preservation should work
- Implementation always regenerates regardless of parameter
- The bidirectional sync feature exists in design but not in implementation

### Next Steps

1. **Immediate**: Fix quote escaping bug so generated files are valid
2. **Short-term**: Implement basic preservation logic:
   - Check if project exists
   - Extract existing positions/customizations
   - Apply to regenerated project
3. **Long-term**: Full bidirectional sync as per BIDIRECTIONAL_UPDATE_FEATURE.md

### Technical Approach

Starting with simplest implementation:
1. Detect existing KiCad project
2. Extract component positions before regeneration
3. Regenerate project  
4. Restore positions to regenerated components
5. Preserve wires, junctions, labels where possible

### Files Created
- `test_position_extraction.py` - Extracts positions from KiCad files
- `extracted_positions.txt` - Sample position data from test project
- `progress_notes.md` - This file
- `test_cases.md` - Comprehensive test scenarios (to be created)

### Blockers
- `force_regenerate=False` not implemented in circuit-synth core
- Quote escaping needs fix in KiCad S-expression generator
- No existing preservation logic in codebase