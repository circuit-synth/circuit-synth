# Rotation Preservation Reference

## Purpose
Three separate KiCad projects to test rotation preservation for each angle (90°, 180°, 270°).

## Projects

### 1. rotation_90
- **File:** `rotation_90/rotation_90.kicad_sch`
- **Component:** R1 (10k resistor)
- **Setup:** Rotate R1 to **90°** in KiCad (press 'R' once)

### 2. rotation_180
- **File:** `rotation_180/rotation_180.kicad_sch`
- **Component:** R1 (10k resistor)
- **Setup:** Rotate R1 to **180°** in KiCad (press 'R' twice)

### 3. rotation_270
- **File:** `rotation_270/rotation_270.kicad_sch`
- **Component:** R1 (10k resistor)
- **Setup:** Rotate R1 to **270°** in KiCad (press 'R' three times)

## Setup Instructions

For each project:
1. Open the schematic in KiCad
2. Select R1 and press 'R' to rotate to the target angle
3. Save (Ctrl+S)

## Test Scenario (Reproduce Bug)

For each angle:

1. **Set rotation manually** (as above)
2. **Modify Python code** - change value:
   ```python
   value="10k" → value="47k"
   ```
3. **Run sync:**
   ```bash
   uv run python3 rotation_90.py
   ```
4. **Check if rotation preserved:**
   ```python
   import kicad_sch_api as ksa
   sch = ksa.Schematic.load("rotation_90/rotation_90.kicad_sch")
   r1 = next(c for c in sch.components if c.reference == "R1")
   print(f"R1 rotation: {r1.rotation}° (expected: 90°)")
   ```

## Expected vs Actual

| Test | Expected | Actual (if bug) |
|------|----------|-----------------|
| rotation_90 | 90° preserved | ??? |
| rotation_180 | 180° preserved | ??? |
| rotation_270 | 270° preserved | ??? |

## Files Generated

- `rotation_90.py` + `rotation_90/` - 90° test
- `rotation_180.py` + `rotation_180/` - 180° test
- `rotation_270.py` + `rotation_270/` - 270° test
