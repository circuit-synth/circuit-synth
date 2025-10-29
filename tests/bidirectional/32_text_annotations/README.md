# Test 32: Text Annotations (Design Notes) Round-Trip

## What This Tests

**Core Question**: When you add text annotations (design notes) to a circuit and regenerate, do the text annotations survive and remain in place?

This validates that **text annotations are preserved during round-trip generation** - a critical feature for circuit documentation and collaboration.

## When This Situation Happens

- Developer generates circuit with text annotations like "DESIGN NOTE: This is power section"
- Later adds another text annotation or modifies the circuit
- Regenerates KiCad from Python
- **Critical**: Do the text annotations survive with correct content and position?

## What Should Work

1. Generate KiCad with text annotation "DESIGN NOTE: This is power section"
2. Verify text appears in .kicad_sch file (search for `(text` elements)
3. Add another text annotation "POWER BUDGET: 500mW" in Python
4. Regenerate KiCad
5. **Both text annotations present** with correct content and positions preserved

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/32_text_annotations

# Step 1: Generate initial KiCad project with text annotation
uv run circuit_with_notes.py
open circuit_with_notes/circuit_with_notes.kicad_pro
# Verify: Text annotation "DESIGN NOTE: This is power section" visible in schematic

# Step 2: Edit circuit_with_notes.py to add another text annotation
# Add another add_text() call in the circuit function

# Step 3: Regenerate KiCad project
uv run circuit_with_notes.py

# Step 4: Open regenerated KiCad and verify
open circuit_with_notes/circuit_with_notes.kicad_pro
# Verify:
#   - Original text annotation still present
#   - New text annotation added
#   - Both texts at correct positions
#   - Content unchanged
```

## Expected Result

- ✅ Initial generation includes text annotation with correct content
- ✅ Text annotation appears in .kicad_sch file (identified by `(text` entries)
- ✅ Adding new text annotation in Python and regenerating preserves original
- ✅ Both text annotations present after regeneration
- ✅ Text content and positions preserved exactly
- ✅ No duplicate text annotations

## Why This Is Important

**Design documentation workflow:**
1. Generate circuit from Python code
2. Add design notes via text annotations ("Power section", "High-speed lines", etc.)
3. Add more components or modify circuit
4. Regenerate - design notes must survive

If annotations are lost:
- Documentation is destroyed each regeneration
- Design notes must be re-added manually
- Collaboration becomes difficult (notes lost during code updates)
- The tool becomes unreliable for real design work

If annotations persist:
- Design notes accumulate and persist
- Documentation survives circuit evolution
- Team notes and design rationale are preserved
- The tool becomes trustworthy for professional design

## Success Criteria

This test PASSES when:
- Text annotations generate correctly from Python code
- Text content appears exactly as specified in .kicad_sch file
- Text positions are preserved across regenerations
- Multiple text annotations can coexist without conflict
- Adding new annotations doesn't lose existing ones
- Round-trip generation preserves all text annotations

## Validation Methodology

Level 2 Semantic Validation:
- Parse .kicad_sch file looking for `(text` elements
- Extract text content from KiCad s-expression format
- Validate content matches Python specification
- Check position coordinates preserved
- Verify count of text elements matches expectations
