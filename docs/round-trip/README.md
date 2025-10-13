# Round-Trip Preservation Testing

This directory contains comprehensive testing documentation for circuit-synth's round-trip preservation feature.

## Overview

Round-trip preservation allows users to:
1. Generate KiCad schematics from Python code
2. Manually edit schematics in KiCad (wires, labels, positions, etc.)
3. Update Python code (change values, add/remove components)
4. Re-generate schematics with `force_regenerate=False`
5. **All manual edits are preserved** while Python changes apply ✅

## Directory Structure

```
docs/round-trip/
├── README.md                    # This file - overview and quick start
├── ARCHITECTURE_ANALYSIS.md     # Round-trip architecture deep-dive
├── TEST_RESULTS_SUMMARY.md      # Automated test results (11/11 ✅)
├── MANUAL_TEST_PLAN.md          # Manual test plan (19 systematic tests)
├── examples/                    # Example test scripts
│   └── test1_basic_divider.py   # Basic voltage divider starter script
└── test-projects/               # Test project artifacts
    └── voltage_divider/         # Example test project
```

## Files Explained

### README.md (This File)
- Overview of round-trip preservation
- Quick start guide
- Documentation roadmap

### TEST_RESULTS_SUMMARY.md
**Automated test results and technical documentation**
- All 11 automated tests passing (100%)
- Complete feature coverage
- Bug fixes and implementation details
- Technical parser implementations
- Session metrics and improvements

**Use this file to:**
- Verify automated test status
- Understand what bugs were fixed
- Learn technical implementation details
- See test execution commands

### MANUAL_TEST_PLAN.md
**Comprehensive manual testing guide**
- 19 systematic tests exercising real-world workflows
- Step-by-step instructions with expected results
- Progress tracking with checkboxes
- Bug reporting template
- Critical test identification

**Use this file to:**
- Perform hands-on testing of round-trip features
- Validate realistic engineering workflows
- Document test progress
- Report bugs systematically

### ARCHITECTURE_ANALYSIS.md
**Technical architecture deep-dive**
- Round-trip update system analysis
- Code path documentation (generation vs update)
- Implementation details and design decisions

**Use this file to:**
- Understand how round-trip preservation works internally
- Learn about the synchronizer architecture
- See what's already implemented vs what's needed

### examples/test1_basic_divider.py
**Ready-to-run starter script**
- Basic voltage divider circuit
- Starting point for Test 1 in manual plan
- Demonstrates simple circuit generation

**Use this file to:**
- Start manual testing immediately
- See example circuit-synth code
- Generate initial test schematic

### test-projects/voltage_divider/
**Example test project artifacts**
- Generated KiCad project from test1_basic_divider.py
- Reference implementation for testing

## Quick Start - Manual Testing

```bash
# 1. Navigate to test directory
cd ~/Desktop/circuit-synth/docs/round-trip

# 2. Run the basic voltage divider test
uv run python examples/test1_basic_divider.py

# 3. Open the generated schematic in KiCad
open test-projects/voltage_divider/voltage_divider.kicad_sch

# 4. Follow MANUAL_TEST_PLAN.md step by step
```

## Test Coverage

### Automated Tests (11/11 ✅)

1. Component position preservation
2. Component value updates with position preservation
3. Component rotation preservation
4. Footprint updates
5. Component addition via Python
6. Component removal via Python
7. Wire preservation
8. Label preservation
9. Manual component preservation
10. Power symbol preservation
11. Component movement with labels

**Status:** All automated tests passing (100%)

### Manual Tests (19 Tests)

Systematic testing of real-world workflows:
- Basic generation
- Manual wiring
- Component additions/removals
- Value/footprint updates
- Position/rotation changes
- Power symbols
- Complex wiring patterns
- Junction preservation
- Power symbols vs hierarchical labels
- Stress testing

**Status:** See `MANUAL_TEST_PLAN.md` for current progress

## Key Features Validated

### ✅ Python → KiCad (Generation)
- Components generate correctly
- Nets and connections work
- Footprints assigned properly
- Values and references correct

### ✅ KiCad → Python (Preservation)
- Manual wires preserved
- Manual labels preserved
- Component positions preserved
- Component rotations preserved
- Power symbols preserved
- Junctions preserved
- Manual components preserved

### ✅ Bidirectional (Round-Trip)
- Python changes propagate
- Manual edits coexist with Python changes
- No data loss
- No corruption
- Predictable behavior

## Testing Strategy

### Automated Testing
```bash
# Run all automated tests
PRESERVE_FILES=1 uv run pytest tests/integration/test_roundtrip_preservation.py tests/integration/test_roundtrip_advanced.py -v

# Expected: 11 passed in ~1.5s
```

### Manual Testing
1. Read `MANUAL_TEST_PLAN.md`
2. Start with Test 1 (basic generation)
3. Progress through all 18 tests
4. Check off completed tests
5. Document any issues

## Critical Validation Points

These are the most important things to verify:

1. **Wire Preservation** - Manual wires must never disappear
2. **Position Preservation** - Component moves must stick
3. **Value Updates** - Python value changes must propagate
4. **Coexistence** - Manual edits + Python changes must work together
5. **No Corruption** - Files must remain valid after updates

## Troubleshooting

### Test Failures
- Check `TEST_RESULTS_SUMMARY.md` for known issues
- Review previous bug fixes for similar problems
- Use the bug reporting template in `MANUAL_TEST_PLAN.md`

### File Corruption
- All generated files are valid KiCad schematics
- If corruption occurs, this is a CRITICAL bug
- Save corrupted files for debugging

### Unexpected Behavior
- Re-run automated tests to verify core functionality
- Check if issue is reproducible
- Document exact steps to reproduce

## Contributing

When adding new tests:
1. Add automated test to `tests/integration/test_roundtrip_*.py`
2. Add manual verification to `MANUAL_TEST_PLAN.md`
3. Update `TEST_RESULTS_SUMMARY.md` with results
4. Document any new edge cases discovered

## Support

For questions or issues:
- Open GitHub issue at `circuit-synth/circuit-synth`
- Include test results and reproduction steps
- Attach relevant `.kicad_sch` files

---

**Last Updated:** 2025-10-12
**Test Status:** 11/11 automated tests passing ✅
**Manual Testing:** Ready for execution
