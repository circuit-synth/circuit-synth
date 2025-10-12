# Round-Trip Schematic Updates

**Feature**: Preserve manual KiCad edits when re-generating schematics from Python
**Status**: ~90% Implemented, Needs Verification
**Timeline**: 2 weeks

## Quick Summary

Users can now iteratively develop circuits:
1. Generate KiCad schematics from Python
2. Manually refine in KiCad (move components, route wires)
3. Modify Python code (add components, change values)
4. Re-run → Python changes applied, **manual work preserved**

## What Works ✅

- **Automatic detection**: System knows when to update vs regenerate
- **Component positions**: Matched components keep manual positions
- **Component matching**: 3 strategies (reference, connection, value/footprint)
- **Value updates**: Component values/footprints update from Python
- **Add/remove components**: New components added, deleted ones removed
- **Hierarchical support**: Multi-sheet projects work

## What Needs Verification ❓

- **Wire preservation**: Does it preserve manually-routed wires?
- **Label preservation**: Net labels, hierarchical labels?
- **Annotations**: Text boxes, notes, graphics?

## Documents

- [requirements.md](requirements.md) - Core requirements and user stories
- [architecture.md](architecture.md) - Technical implementation
- [testing.md](testing.md) - Test strategy
- [questions.md](questions.md) - Open questions for discussion

## Key Code Locations

- `src/circuit_synth/kicad/sch_gen/main_generator.py:412-478` - Update logic
- `src/circuit_synth/kicad/schematic/synchronizer.py` - Core synchronizer
- `src/circuit_synth/kicad/schematic/hierarchical_synchronizer.py` - Multi-sheet

## Next Steps

1. Verify wire/label preservation works
2. Create round-trip integration tests
3. Document user-facing behavior
