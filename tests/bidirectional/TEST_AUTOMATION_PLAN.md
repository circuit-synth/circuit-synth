# Bidirectional Test Suite Automation Plan

## Analysis of Existing Tests (01-11)

### Consistent Pattern Observed

Every test directory (01-11) follows this structure:
```
XX_test_name/
├── README.md          # Explains what, why, when, how
├── fixture.py         # Python circuit file (or blank_kicad_ref/ for KiCad starting point)
├── test_XX_name.py    # Automated pytest
└── __pycache__/       # Generated
```

### README.md Template Pattern

All READMEs follow the same structure:
1. **What This Tests** - Core question or capability being validated
2. **When This Situation Happens** - Real-world scenarios
3. **What Should Work** - Expected behavior (numbered steps)
4. **Manual Test Instructions** - Bash commands for manual testing
5. **Expected Result** - Checklist of success criteria
6. **Why This Is Critical/Important** - Business value explanation

### Test File Pattern

All test files follow this pattern:
```python
#!/usr/bin/env python3
"""
Detailed docstring explaining:
- What is being tested
- Why it matters
- Workflow steps
- Validation approach (Level 2/3)
"""

def parse_netlist(netlist_content):  # If needed
    """Helper for netlist validation"""
    ...

def test_XX_feature_name(request):
    """Main test function.

    Workflow:
    1. Setup paths
    2. Clean output directory
    3. Step 1: Initial generation
    4. Step 2: Validate initial state
    5. Step 3: Make change (Python or KiCad)
    6. Step 4: Regenerate
    7. Step 5: Validate change reflected
    8. Step 6: Validate positions preserved (if applicable)

    Validation:
    - Level 2: kicad-sch-api for semantic validation
    - Level 3: Netlist comparison for electrical validation
    """
    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Test steps with clear print statements
        print("\n" + "="*70)
        print("STEP 1: Description")
        print("="*70)
        # ...
    finally:
        # Always restore original files
        # Always cleanup if requested
```

### Validation Levels Used

- **Level 1**: Text matching (not used in recent tests)
- **Level 2**: kicad-sch-api semantic validation (positions, references, component count)
- **Level 3**: Netlist comparison via kicad-cli (electrical connectivity) - PREFERRED

## Recommendations

### 1. Test Numbering (14-25 Mapping)

Based on FUTURE_TESTS.md priorities and logical flow:

```
✅ 12: change_pin_connection (just created, needs README.md)
✅ 13: rename_component (exists, needs README.md)
🆕 14: merge_nets (Phase 1 - Nets are critical)
🆕 15: split_net (Phase 1 - Nets are critical)
🆕 16: add_power_symbol (Phase 2 - Power handling)
🆕 17: add_ground_symbol (Phase 2 - Power handling)
🆕 18: multiple_power_domains (Phase 2 - Power handling)
🆕 19: swap_component_type (Phase 3 - Component changes)
🆕 20: component_orientation (Phase 3 - Component changes)
🆕 21: multi_unit_components (Phase 5 - Advanced features)
🆕 22: add_subcircuit_sheet (Phase 4 - Hierarchical - SIMPLIFIED)
🆕 23: remove_subcircuit_sheet (Phase 4 - Hierarchical - SIMPLIFIED)
🆕 24: add_global_label (Phase 4 - Labels)
🆕 25: add_local_label (Phase 4 - Labels)
✅ 26: power_symbol_replacement (exists, needs README.md)
```

**Rationale**:
- Prioritize nets (critical infrastructure)
- Then power (common use case)
- Then component manipulation (frequent workflow)
- Then advanced features
- Leave complex hierarchical tests (cross-sheet) for later dedicated work

### 2. Test 26 Handling

Test 26 has 6 test files for different power symbols. **Recommendation**:
- Create **ONE comprehensive README.md** explaining all power symbol tests
- Verify each test file has proper fixtures
- Add missing fixtures if needed

### 3. Starting File Strategy

**Recommendation: Option A** (Python script generates KiCad)

Reasons:
1. ✅ Matches existing pattern (tests 01-11 all use Python fixtures)
2. ✅ Reproducible - anyone can regenerate starting KiCad files
3. ✅ Self-documenting - Python code shows circuit intent
4. ✅ Maintainable - easier to modify than raw .kicad_sch files
5. ✅ Version control friendly - Python diffs are readable

**Implementation**:
- For tests needing KiCad starting point: Create `fixture.py` that generates the KiCad
- Test can run `uv run fixture.py` to create initial state
- Follows exact pattern from tests 03-11

### 4. Complex Hierarchical Tests (22-23)

**Recommendation: Create SIMPLIFIED versions now**

For tests 22-23 (subcircuit operations):
- Create basic single-level hierarchy (root + 1 child sheet)
- Test component placement on child sheet
- Test position preservation on child sheet
- Mark as "Basic hierarchical test" in README.md
- Note that complex multi-sheet operations are in FUTURE_TESTS.md Category B

**Rationale**:
- Establishes basic hierarchical testing infrastructure
- Tests basic sync on child sheets (critical gap per FUTURE_TESTS.md)
- Doesn't block on complex cross-sheet scenarios
- Can be enhanced later with Category B tests (50-66)

### 5. Parallel Execution Strategy

**Recommendation: Launch in ONE batch - 15 Haiku agents simultaneously**

Tasks to create:
1. Test 12: README.md only (has test already)
2. Test 13: README.md only (has test already)
3. Tests 14-25: Full test creation (README + fixture + pytest)
4. Test 26: README.md only (has tests already)

Total: 15 agents
- Agent 1-2: README.md creation (fast)
- Agents 3-14: Full test creation (12 new tests)
- Agent 15: README.md for test 26

**Why all at once:**
1. Haiku is fast and cheap
2. Tests are independent (no dependencies)
3. Maximizes parallelism per CLAUDE.md guidelines
4. All agents follow same template pattern
5. Can review all output together for consistency

### 6. Test Pattern

**Recommendation: ALL tests follow Pattern A with enhancements**

Pattern A (from existing tests):
```
1. Generate initial circuit from Python fixture
2. Validate initial state (Level 2: kicad-sch-api)
3. Make change (modify Python OR modify KiCad)
4. Regenerate
5. Validate change reflected (Level 2 or Level 3)
6. Validate positions preserved (if applicable)
7. Restore original fixture in finally block
```

**Enhancements to apply:**
- Use netlist comparison (Level 3) for ANY test involving electrical connections
- Use kicad-sch-api (Level 2) for structural tests (positions, references, component types)
- Include "Why This Is Critical" section in README.md (like test 09)
- Include clear step-by-step printed output (like test 11)
- Mark known limitations with issue numbers (like test 10, test 12)

### 7. Validation Strategy

**Recommendation: Use HIGHEST applicable validation level**

Decision tree:
- Test involves electrical connectivity (nets, pins)? → **Level 3** (netlist comparison)
- Test involves component structure/properties? → **Level 2** (kicad-sch-api)
- Test involves visual/layout only? → **Level 2** (kicad-sch-api positions)

**Specific recommendations per test:**
- 14 (merge nets): Level 3 ✅
- 15 (split net): Level 3 ✅
- 16-18 (power symbols): Level 3 ✅
- 19 (swap component): Level 2 (no electrical change)
- 20 (orientation): Level 2 (position/angle)
- 21 (multi-unit): Level 3 ✅
- 22-23 (subcircuits): Level 2 initially (structure), Level 3 if nets cross sheets
- 24-25 (labels): Level 3 ✅

## Implementation Plan

### Step 1: Prepare Agent Instructions

Create standardized instructions for each agent type:

**Type A: README.md Only** (tests 12, 13, 26)
- Read existing test file(s)
- Follow README.md template from test 09 or 11
- Include: What, When, Manual Instructions, Expected Result, Why Critical
- Path format: `XX_test_name/README.md`

**Type B: Full Test Creation** (tests 14-25)
- Read FUTURE_TESTS.md for test description
- Create directory: `XX_test_name/`
- Create fixture Python file (generates starting KiCad)
- Create test file following pattern from test 11
- Create README.md following pattern from test 09
- Use Level 2 or Level 3 validation as appropriate
- Include netlist parser if Level 3

### Step 2: Launch All Agents in Single Message

Use Task tool with subagent_type="general-purpose", model="haiku"
Launch 15 agents simultaneously:

```
Agents 1-2: README.md creation (fast)
Agents 3-14: Full test creation
Agent 15: README.md for test 26
```

### Step 3: Verification After Agents Complete

Run full test suite:
```bash
cd tests/bidirectional
pytest -v --keep-output
```

Expected: All new tests should pass (or XFAIL with documented issues)

### Step 4: Commit

Single commit or batched commits:
```
feat: Add automated bidirectional tests 14-25

- Test 14: Merge nets
- Test 15: Split net
- Test 16-18: Power symbol handling
- Test 19: Swap component type
- Test 20: Component orientation
- Test 21: Multi-unit components
- Test 22-23: Basic hierarchical sheet operations
- Test 24-25: Label handling
- Add README.md for tests 12, 13, 26

All tests follow consistent pattern with Level 2/3 validation.
Tests 22-23 are simplified hierarchical tests (complex cross-sheet
operations documented in FUTURE_TESTS.md Category B).
```

## Specific Test Specifications

### Test 14: Merge Nets

**Fixture**: Two separate nets (NET1 connects R1-R2, NET2 connects R3-R4)
**Change**: Connect NET1 and NET2 (add wire or common component)
**Validate**: Netlist shows all 4 components on same net (Level 3)
**Critical**: Validates net merging logic

### Test 15: Split Net

**Fixture**: Single net connecting R1-R2-R3
**Change**: Remove connection between R2 and R3
**Validate**: Netlist shows two separate nets (Level 3)
**Critical**: Validates net splitting and automatic net naming

### Test 16: Add Power Symbol (VCC)

**Fixture**: R1 with pin unconnected
**Change**: Add VCC power symbol connection in Python
**Validate**: Netlist shows R1 pin connected to VCC net (Level 3)
**Critical**: Power nets are special in KiCad

### Test 17: Add Ground Symbol

**Fixture**: R1 with pin unconnected
**Change**: Add GND power symbol connection in Python
**Validate**: Netlist shows R1 pin connected to GND net (Level 3)
**Critical**: Ground handling validation

### Test 18: Multiple Power Domains

**Fixture**: Circuit with multiple power rails (VCC, 3V3, 5V, GND)
**Change**: Connect different components to different power domains
**Validate**: Netlist shows correct power domain assignments (Level 3)
**Critical**: Multi-voltage designs common in real circuits

### Test 19: Swap Component Type

**Fixture**: R1 resistor
**Change**: Change to capacitor (Device:C) keeping same reference and position
**Validate**: KiCad shows capacitor symbol, position preserved (Level 2)
**Critical**: Component type changes during design iteration

### Test 20: Component Orientation

**Fixture**: R1 at 0° rotation
**Change**: Rotate to 90° in Python
**Validate**: KiCad shows R1 at 90° rotation, position preserved (Level 2)
**Critical**: Orientation affects layout and readability

### Test 21: Multi-Unit Components

**Fixture**: Quad op-amp (4 units)
**Change**: Use all 4 units in circuit
**Validate**: Netlist shows all 4 units with correct pin connections (Level 3)
**Critical**: Multi-unit components common (op-amps, gates, etc.)

### Test 22: Add Subcircuit Sheet (Simplified)

**Fixture**: Root sheet with R1
**Change**: Add child sheet with R2
**Validate**: Both sheets exist, R2 on child sheet, positions preserved (Level 2)
**Note**: Simplified - no cross-sheet connections yet
**Critical**: Basic hierarchical design testing

### Test 23: Remove Subcircuit Sheet (Simplified)

**Fixture**: Root sheet + child sheet with component
**Change**: Remove child sheet in Python
**Validate**: Only root sheet remains, child sheet removed (Level 2)
**Note**: Simplified - tests sheet removal without complex cross-sheet nets
**Critical**: Sheet management operations

### Test 24: Add Global Label

**Fixture**: Two components on root sheet
**Change**: Add global label connecting them
**Validate**: Netlist shows connection via global label (Level 3)
**Critical**: Global labels enable cross-sheet connections

### Test 25: Add Local Label

**Fixture**: Two components on same sheet
**Change**: Add local label to name net
**Validate**: Netlist shows connection with correct net name (Level 3)
**Critical**: Local labels for net naming within sheet

## Success Criteria

This automation is successful when:

✅ All tests 12-26 have README.md files following consistent template
✅ All tests 14-25 have complete test implementations
✅ All tests use Level 2 or Level 3 validation (no text matching)
✅ All tests follow the established pattern from tests 01-11
✅ All tests can run independently with --keep-output flag
✅ All tests restore original fixture files in finally block
✅ Test suite runs in CI/CD without manual intervention
✅ Each test has clear printed output showing progress
✅ Known limitations documented with issue numbers

## Next Steps After Automation

1. **Run full test suite**: Verify all tests pass or XFAIL appropriately
2. **Manual validation**: Spot-check 3-5 tests manually to ensure they match expectations
3. **Document issues**: Create GitHub issues for any XFAIL tests
4. **Update FUTURE_TESTS.md**: Mark tests 14-25 as complete
5. **Plan Category B**: Begin hierarchical cross-sheet testing (tests 50-66)

---

**Estimated Time**:
- Agent execution: 5-10 minutes (parallel)
- Review and fixes: 15-30 minutes
- Full test suite run: 5-10 minutes
- Total: ~30-50 minutes

**Total New Tests**: 12 (tests 14-25)
**Total READMEs**: 15 (tests 12-26)
