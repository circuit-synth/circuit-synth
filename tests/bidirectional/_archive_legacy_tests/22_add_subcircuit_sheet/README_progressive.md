# Test 22: Progressive Subcircuit Addition (1→2→3 Levels)

## What This Tests

**Core Question**: Can you incrementally add subcircuits to a design (1→2→3 hierarchy levels) and have KiCad regenerate correctly at each step?

This validates the **incremental hierarchical development workflow** - building complexity one subcircuit at a time.

## When This Situation Happens

Real circuit development is incremental:
1. **Start simple**: Single circuit with a few components
2. **Add organization**: Break into subcircuits as design grows
3. **Nest deeper**: Add subcircuits within subcircuits for complex designs

**Developer workflow:**
- Day 1: Create main circuit with R1
- Day 2: Add level1 subcircuit with R2 (organize into 2-level hierarchy)
- Day 3: Add level2 subcircuit within level1 (3-level nested hierarchy)
- Each step: Regenerate KiCad and verify it works

## What Should Work

### Step 1: Single-level circuit (main with R1)
```python
@circuit(name="main")
def main():
    r1 = Component("Device:R", ref="R1", value="10k")
```
Generate → Verify:
- 1 schematic file: `main.kicad_sch`
- R1 visible on main sheet

### Step 2: Add level1 subcircuit (2 levels)
```python
@circuit(name="level1")
def level1():
    r2 = Component("Device:R", ref="R2", value="4.7k")

@circuit(name="main")
def main():
    r1 = Component("Device:R", ref="R1", value="10k")
    level1()  # Add subcircuit
```
Regenerate → Verify:
- 2 schematic files: `main.kicad_sch` + `level1.kicad_sch`
- Hierarchical sheet symbol on main sheet (links to level1)
- R1 position preserved (didn't move)
- R2 visible on level1 sheet

### Step 3: Add level2 subcircuit (3 levels, nested)
```python
@circuit(name="level2")
def level2():
    r3 = Component("Device:R", ref="R3", value="20k")

@circuit(name="level1")
def level1():
    r2 = Component("Device:R", ref="R2", value="4.7k")
    level2()  # Nest another level

@circuit(name="main")
def main():
    r1 = Component("Device:R", ref="R1", value="10k")
    level1()
```
Regenerate → Verify:
- 3 schematic files: `main.kicad_sch` + `level1.kicad_sch` + `level2.kicad_sch`
- Hierarchical sheet symbol on main (links to level1)
- Hierarchical sheet symbol on level1 (links to level2)
- R1, R2 positions preserved
- R3 visible on level2 sheet

## Manual Test Instructions

```bash
cd tests/bidirectional/22_add_subcircuit_sheet

# STEP 1: Generate single-level circuit
# Edit progressive_hierarchy.py - ensure level1() call is commented out
uv run progressive_hierarchy.py
open progressive_hierarchy/progressive_hierarchy.kicad_pro
# Verify:
#   - Only main sheet visible
#   - R1 present

# STEP 2: Add level1 subcircuit (2 levels)
# Edit progressive_hierarchy.py:
#   - Uncomment @circuit(name="level1") definition
#   - Uncomment level1() call in main()
uv run progressive_hierarchy.py
open progressive_hierarchy/progressive_hierarchy.kicad_pro
# Verify:
#   - Main sheet shows R1 + hierarchical sheet symbol "level1"
#   - Level1 sheet shows R2
#   - R1 position unchanged from step 1

# STEP 3: Add level2 subcircuit (3 levels)
# Edit progressive_hierarchy.py:
#   - Uncomment @circuit(name="level2") definition
#   - Uncomment level2() call in level1()
uv run progressive_hierarchy.py
open progressive_hierarchy/progressive_hierarchy.kicad_pro
# Verify:
#   - Main sheet: R1 + hierarchical sheet symbol "level1"
#   - Level1 sheet: R2 + hierarchical sheet symbol "level2"
#   - Level2 sheet: R3
#   - R1, R2 positions unchanged
```

## Expected Result

**Step 1 (1 level):**
- ✅ Files: `progressive_hierarchy.kicad_sch`
- ✅ Main sheet: R1 visible

**Step 2 (2 levels):**
- ✅ Files: `progressive_hierarchy.kicad_sch` + `level1.kicad_sch`
- ✅ Main sheet: R1 + hierarchical sheet symbol
- ✅ Level1 sheet: R2
- ✅ R1 position preserved

**Step 3 (3 levels):**
- ✅ Files: `main` + `level1.kicad_sch` + `level2.kicad_sch`
- ✅ Main sheet: R1 + hierarchical sheet symbol (level1)
- ✅ Level1 sheet: R2 + hierarchical sheet symbol (level2)
- ✅ Level2 sheet: R3
- ✅ R1, R2 positions preserved
- ✅ Nested hierarchy works correctly

## Why This Is Critical

**Incremental development is how real circuits are built:**

1. **No big-bang design**: Start small, grow organically
2. **Test at each step**: Verify each addition works before moving forward
3. **Refactor safely**: Can reorganize into subcircuits without breaking existing work
4. **Position preservation**: Components don't jump around when hierarchy changes

**If this doesn't work:**
- Must design entire hierarchy upfront (unrealistic)
- Adding subcircuits breaks existing layout
- Cannot refactor/reorganize safely
- Iterative workflow impossible

**If this works:**
- Start simple, add complexity incrementally
- Each step verifiable in KiCad
- Positions preserved through refactoring
- Real-world iterative workflow enabled

## Success Criteria

This test PASSES when:
- Step 1: Single-level generation works (1 schematic)
- Step 2: Adding level1 creates 2 schematics + sheet symbol
- Step 3: Adding level2 creates 3 schematics + nested sheet symbols
- R1 position preserved through all steps
- R2 position preserved from step 2 to step 3
- All hierarchical sheet symbols generated automatically
- Each level's components visible on correct sheet

## Current Status

⚠️ **XFAIL - Blocked by Issue #406**

This test will likely fail at Step 2 because:
- Subcircuit sheet generation is broken (Issue #406)
- `level1.kicad_sch` won't be created even though `level1()` is called
- Hierarchical sheet symbol won't appear on main sheet

Test is written to document expected workflow. Will pass once Issue #406 is fixed.

## Validation Level

**Level 2 (Semantic Validation)**: File existence + component verification
- Check .kicad_sch file existence
- kicad-sch-api to load schematics
- Verify components on correct sheets
- Position preservation verification

## Related Tests

- **Test 24** - Cross-sheet connection (after subcircuits work)
- **Test 67** - Connected multi-level subcircuits (next test)
- **Issue #406** - Subcircuit generation broken (blocking issue)

## Design Notes

**Progressive hierarchy structure:**

After Step 1:
```
progressive_hierarchy/
└── progressive_hierarchy.kicad_sch  (main with R1)
```

After Step 2:
```
progressive_hierarchy/
├── progressive_hierarchy.kicad_sch  (main with R1 + sheet symbol)
└── level1.kicad_sch                 (level1 with R2)
```

After Step 3:
```
progressive_hierarchy/
├── progressive_hierarchy.kicad_sch  (main with R1 + sheet symbol)
├── level1.kicad_sch                 (level1 with R2 + sheet symbol)
└── level2.kicad_sch                 (level2 with R3)
```

**Hierarchical sheet symbols:**
- Main sheet: Rectangle labeled "level1" linking to level1.kicad_sch
- Level1 sheet: Rectangle labeled "level2" linking to level2.kicad_sch

**What circuit-synth must do:**
1. Detect when subcircuit function is called: `level1()`
2. Generate .kicad_sch file for that subcircuit
3. Create hierarchical sheet symbol on parent sheet
4. Link sheet symbol to child .kicad_sch file
5. Preserve all existing component positions
