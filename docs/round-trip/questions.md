# Open Questions

## Critical (Needs Verification)

### Q1: Does wire preservation actually work?
**Status**: Code loads wires from existing schematics, but does `_save_schematic()` preserve them?
**Action**: Create test to verify
**Priority**: HIGH

### Q2: Does label preservation work?
**Status**: Same as wires - loaded but save behavior unclear
**Action**: Create test to verify
**Priority**: HIGH

### Q3: What about annotations?
**Status**: No explicit handling found in synchronizer code
**Types**: Text boxes, graphics, notes, dimensions
**Action**: Check if kicad-sch-api preserves these automatically
**Priority**: MEDIUM

## Design Decisions Needed

### Q4: Net name changes?
**Scenario**: User renames net in Python but wires exist in KiCad with old name
**Options**:
- A) Update wire labels to new net name
- B) Preserve wires but disconnect from net
- C) Error and ask user to resolve
**Decision**: ?

### Q5: Component type changes?
**Scenario**: R1 changes from `Device:R` to custom resistor symbol
**Options**:
- A) Replace component, lose position
- B) Error and require manual fix
- C) Preserve position, update symbol
**Decision**: ?

### Q6: Footprint changes with different pin counts?
**Scenario**: IC changes from SOIC-8 to SOIC-16
**Options**:
- A) Update footprint, keep position (may look wrong)
- B) Replace component, place new
- C) Warn user about pin mismatch
**Decision**: ?

### Q7: User-added components?
**Scenario**: User manually adds components in KiCad (not in Python)
**Current**: `preserve_user_components` flag exists
**Question**: Should this be default True or False?
**Decision**: ?

### Q8: Power symbols?
**Scenario**: KiCad auto-generates power flags, ground symbols
**Question**: Should we preserve these or regenerate?
**Action**: Test behavior
**Priority**: MEDIUM

## Performance

### Q9: Large schematic performance?
**Question**: Does matching scale to 500+ components?
**Action**: Test with large project
**Priority**: LOW (optimize later if needed)

## User Experience

### Q10: Change summary?
**Question**: Should we show a report of what changed?
**Example**: "Updated 3 values, added 2 components, preserved 45 manual edits"
**Priority**: NICE TO HAVE

### Q11: Dry-run mode?
**Question**: Should users preview changes before applying?
**Priority**: NICE TO HAVE

### Q12: Backup before update?
**Question**: Auto-backup schematic before risky updates?
**Priority**: NICE TO HAVE (v2)

## Documentation

### Q13: What should users know?
**Topics**:
- What's safe to edit manually?
- What causes full regeneration?
- How to force regeneration?
- Troubleshooting common issues

**Priority**: HIGH (document after testing)

## Timeline Impact

- **Critical questions (Q1-Q3)**: Block completion - resolve Week 1
- **Design questions (Q4-Q8)**: Can defer to v2 if needed
- **Nice-to-have (Q9-Q12)**: Post-v1 enhancements
