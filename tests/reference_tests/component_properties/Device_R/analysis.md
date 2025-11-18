# Component Property Analysis: Device:R (Resistor)

## Component Position and Rotation
- **Position**: `(35.56, 33.02)` mm
- **Rotation**: `0` degrees (horizontal)
- **Unit**: `1`

## Key Findings

### 1. `fields_autoplaced` Property
**KiCad manually placed component includes:**
```
(fields_autoplaced yes)
```
This is line 164 in the manually placed schematic.

**Circuit-synth generated:** This property is likely MISSING or set to `no`

**Action needed:** Investigate if circuit-synth sets `fields_autoplaced yes` when generating components.

### 2. Property Text Positioning

#### Reference Property (R1)
- **Position**: `(at 38.1 31.7499 0)`
- **Offset from component**: X: +2.54mm, Y: -1.27mm (approximately)
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

#### Value Property (10k)
- **Position**: `(at 38.1 34.2899 0)`
- **Offset from component**: X: +2.54mm, Y: +1.27mm (approximately)
- **Justification**: `(justify left)`
- **Font size**: `1.27 1.27`

#### Footprint Property (Resistor_SMD:R_0603_1608Metric)
- **Position**: `(at 33.782 33.02 90)`
- **Offset from component**: X: -1.778mm, Y: 0mm
- **Rotation**: `90` degrees (vertical text)
- **Font size**: `1.27 1.27`
- **Hidden**: `yes`

### 3. All Properties Present in Manual KiCad Placement

| Property | Value | Position | Rotation | Hidden | Notes |
|----------|-------|----------|----------|--------|-------|
| Reference | R1 | (38.1, 31.7499, 0) | 0° | no | To the right of component |
| Value | 10k | (38.1, 34.2899, 0) | 0° | no | To the right, below Reference |
| Footprint | Resistor_SMD:R_0603_1608Metric | (33.782, 33.02, 90) | 90° | yes | To the left, rotated |
| Datasheet | ~ | (35.56, 33.02, 0) | 0° | yes | At component center |
| Description | Resistor | (35.56, 33.02, 0) | 0° | yes | At component center |

### 4. Property Positioning Pattern

**Pattern observed for resistor at rotation 0°:**
- Reference: RIGHT side, ABOVE center (X: +2.54, Y: -1.27)
- Value: RIGHT side, BELOW center (X: +2.54, Y: +1.27)
- Footprint: LEFT side, at center height, rotated 90° (X: -1.778, Y: 0, rotation: 90)
- Hidden properties (Datasheet, Description): at component center (0, 0)

This matches the positioning rules in `kicad-sch-api/kicad_sch_api/core/property_positioning.py`:

```python
"Device:R": ComponentPositioningRule(
    reference_offset=PropertyOffset(x=2.54, y=-1.2701, rotation=0),
    value_offset=PropertyOffset(x=2.54, y=1.2699, rotation=0),
    footprint_offset=PropertyOffset(x=-1.778, y=0, rotation=90),
),
```

**Close match!** The Y offsets are slightly different:
- KiCad actual: Y=-1.27 and Y=+1.27 (round numbers)
- Rule file: Y=-1.2701 and Y=+1.2699

### 5. Comparison Checklist

**To verify circuit-synth output matches this:**

- [ ] `fields_autoplaced yes` is present
- [ ] Reference property at (component_x + 2.54, component_y - 1.27, 0)
- [ ] Value property at (component_x + 2.54, component_y + 1.27, 0)
- [ ] Footprint property at (component_x - 1.778, component_y, 90) with `(hide yes)`
- [ ] Datasheet property at component center with `(hide yes)`
- [ ] Description property at component center with `(hide yes)`
- [ ] All properties have `(justify left)` for visible text
- [ ] Font size is `1.27 1.27` for all properties

## Comparison: Circuit-Synth vs Manual KiCad

### Component Position
- **Manual KiCad**: `(at 35.56 33.02 0)`
- **Circuit-Synth**: `(at 30.48 35.56 0)`
- **Difference**: Different positions (expected - just placement difference)

### Property Positioning Comparison

| Property | Manual KiCad | Circuit-Synth | Match? |
|----------|--------------|---------------|--------|
| Reference | (38.1, 31.7499, 0) | (33.02, 34.2899, 0) | ✅ Offset correct |
| Value | (38.1, 34.2899, 0) | (33.02, 36.8299, 0) | ✅ Offset correct |
| Footprint | (33.782, 33.02, 90) | (28.702, 35.56, 90) | ✅ Offset correct |

**Offset verification (manual at 35.56, 33.02):**
- Reference: (38.1, 31.7499) = (+2.54, -1.27) ✅
- Value: (38.1, 34.2899) = (+2.54, +1.27) ✅
- Footprint: (33.782, 33.02) = (-1.778, 0) ✅

**Offset verification (circuit-synth at 30.48, 35.56):**
- Reference: (33.02, 34.2899) = (+2.54, -1.27) ✅
- Value: (33.02, 36.8299) = (+2.54, +1.27) ✅
- Footprint: (28.702, 35.56) = (-1.778, 0) ✅

**TEXT POSITIONING IS CORRECT! ✅**

### Key Differences Found

#### 1. Missing Properties in Manual KiCad
**Circuit-synth includes these extra properties (NOT in manual KiCad):**
- `hierarchy_path` (line 173-180)
- `project_name` (line 182-189)
- `root_uuid` (line 191-198)

**Action:** These are circuit-synth internal properties. Check if they should be prefixed with `_circuit_synth_` to avoid namespace pollution.

#### 2. Missing Properties in Circuit-Synth
**Manual KiCad includes these (NOT in circuit-synth):**
- `Datasheet` property (line 193-200 in manual)
- `Description` property (line 202-209 in manual)

**Action:** Circuit-synth should add Datasheet and Description properties when generating components.

#### 3. Generator Field
- **Manual KiCad**: `(generator "eeschema")` + `(generator_version "9.0")`
- **Circuit-Synth**: `(generator "circuit_synth")` + `(generator_version "0.8.36")`
- **Status**: ✅ This is expected and correct

#### 4. Project Name in Instances
**Manual KiCad (line 218):**
```
(project "resistor_reference"
```

**Circuit-Synth (line 207):**
```
(project ""
```

**Action:** Circuit-synth should populate the project name in the instances section.

### Summary of Issues to Fix

1. ❌ Missing `Datasheet` property in circuit-synth generated components
2. ❌ Missing `Description` property in circuit-synth generated components
3. ❌ Empty project name in `instances` section (should be "resistor_reference")
4. ⚠️ Extra properties (`hierarchy_path`, `project_name`, `root_uuid`) - should these be prefixed?
5. ✅ Text positioning is CORRECT - no changes needed!
6. ✅ `fields_autoplaced yes` is present in both - correct!

## Next Steps

1. Fix missing Datasheet and Description properties
2. Fix empty project name in instances section
3. Review whether internal properties need `_circuit_synth_` prefix
4. Test with additional component types to verify consistency
