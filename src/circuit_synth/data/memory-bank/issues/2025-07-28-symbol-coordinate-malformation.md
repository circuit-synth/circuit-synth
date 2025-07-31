# Symbol Coordinate Malformation Issue - 2025-07-28

## Issue Summary - URGENT FINAL BLOCKER
KiCad symbols are now visible in the schematic viewer but display with malformed internal positioning and graphics. This is the **final blocker** for complete KiCad integration - symbols render but coordinates are incorrect.

## Visual Evidence
Screenshot shows:
- U2 (NCP1117 regulator): Shows as rectangle with "3V3 D VDD" text overlay in wrong position
- C4, C6 (10uF capacitors): Show as rectangles with "5V" and "3V" labels positioned incorrectly
- Pin positions appear disconnected from symbol graphics
- Symbol body graphics are not properly aligned with their text labels

## Technical Root Cause Analysis

### 1. Coordinate System Mismatch
KiCad uses a specific coordinate system with:
- Origin (0,0) typically at symbol center or specific anchor point
- Y-axis may be inverted compared to circuit-synth expectations
- Pin coordinates must align precisely with graphics elements

### 2. Symbol Graphics Processing Chain
Current flow:
```
KiCad Library Symbol → Python Parser → Rust Cache → S-expression Generator → KiCad File
```

Issue likely occurs in:
- **Pin coordinate calculation**: `src/circuit_synth/kicad_api/core/symbol_cache.py`
- **Graphics coordinate transformation**: `src/circuit_synth/kicad_api/core/s_expression.py`
- **Symbol origin/anchor handling**: During S-expression generation

### 3. Graphics Element Integrity
From logs, graphics are being processed:
```
🎨 Processing 1 graphic elements for Regulator_Linear:NCP1117-3.3_SOT223
  Element 0: rectangle -> 225 chars
✅ Added graphics symbol with 1 elements
```

But coordinate transformation may be corrupting positions during conversion.

## Files to Investigate

### Primary Suspects:
1. **`src/circuit_synth/kicad_api/core/s_expression.py`**
   - Graphics element coordinate processing
   - Symbol positioning logic
   - Pin-to-graphics alignment

2. **`src/circuit_synth/kicad_api/core/symbol_cache.py`**
   - Symbol coordinate extraction from KiCad libraries
   - Pin position calculation
   - Graphics data preservation

3. **`src/circuit_synth/kicad/kicad_symbol_parser.py`**
   - Initial symbol parsing from .kicad_sym files
   - Coordinate system interpretation
   - Graphics element extraction

### Supporting Files:
4. **`src/circuit_synth/kicad/rust_accelerated_symbol_cache.py`**
   - Rust-Python coordinate data transfer
   - Cache integrity verification

## Debugging Strategy

### Phase 1: Coordinate System Verification
1. Export a simple resistor symbol from KiCad library directly
2. Compare coordinates with circuit-synth generated resistor
3. Identify coordinate transformation differences
4. Check Y-axis orientation and origin handling

### Phase 2: Graphics Element Analysis
1. Add debug logging to S-expression graphics processing
2. Compare generated polyline/rectangle coordinates with reference
3. Verify pin positions match graphics anchor points
4. Check symbol unit/part indexing

### Phase 3: Cache Integrity Testing
1. Test Python fallback vs Rust cache coordinate consistency
2. Verify graphics data preservation through cache layers
3. Check coordinate precision loss during serialization

## Immediate Action Items - CRITICAL PATH

1. **Phase 1 - Coordinate System Analysis** (URGENT):
   - Create minimal test case with single resistor component
   - Export KiCad Device:R symbol as reference for coordinate comparison
   - Add coordinate debug logging to S-expression graphics processing pipeline
   - Compare generated vs reference symbol coordinates point-by-point

2. **Phase 2 - Graphics Element Investigation** (HIGH PRIORITY):
   - Debug pin position calculations in `src/circuit_synth/kicad_api/core/symbol_cache.py`
   - Check symbol origin/anchor point handling in S-expression generation
   - Verify coordinate transformations preserve scale and positioning
   - Test symbol unit/part indexing for multi-unit components

3. **Phase 3 - Implementation Fix** (EXECUTION):
   - Fix coordinate system mismatch in graphics processing
   - Correct pin-to-graphics alignment calculations
   - Validate against KiCad standard library symbols
   - Test with multiple component types (resistors, capacitors, ICs)

## Success Criteria
When fixed, symbols should display with:
- Correct internal graphics positioning
- Proper text label alignment
- Accurate pin positions relative to symbol body
- Consistent appearance with KiCad standard library symbols

## Priority: HIGH
This is the final major blocker for KiCad integration. Symbol graphics pipeline is working; coordinate system needs alignment with KiCad standards.