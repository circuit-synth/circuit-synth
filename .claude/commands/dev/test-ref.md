---
name: test-ref
description: Create reference material for testing and development
---

# Test Reference Creation Command

**Purpose:** Help users efficiently create reference material (KiCad projects, log patterns, expected outputs) for iterative testing and development.

## Usage
```bash
/dev:test-ref <what-you-need>
```

## Why This Matters

**The Pattern:**
Creating reference material manually takes 20+ minutes. With agent assistance: 2 minutes.

Having reference material enables:
- **Iterative development:** Compare output against known-good reference
- **Regression testing:** Detect unintended changes
- **Visual validation:** Screenshots, KiCad projects as ground truth
- **Log-driven debugging:** Compare logs against expected patterns

**This cuts development time by 10x in many cases.**

## Critical Use Case: Cooperative Debugging

**This command is ESSENTIAL for debugging visual/KiCad bugs.**

### The Problem

Visual bugs (component positioning, rotation, text placement) **cannot be reliably tested programmatically**. You might check that rotation=90°, but miss that text is sideways.

### The Solution

1. **Create reference** with this command
2. **User manipulates** in KiCad (rotate, move, etc.)
3. **Trigger bug** by syncing changes
4. **User visually confirms** what's wrong
5. **Compare KiCad files** before/after to find root cause

### Real Example: Issue #514

\`\`\`bash
User: /dev:test-ref "we need to make a reference kicad project to test against for this issue"

Agent: Creates rotation_90.py, generates circuit

User: Opens in KiCad, rotates R1 to 90°, saves

Agent: Changes value in code, runs sync

User: "R1 and 47k are sideways" [provides screenshot]

Agent: Compares schematic files, finds text positions reset
        → Fix: Apply rotation transform to text offsets
        → Test with user verification at 90°, 180°, 270°
        → User: "perfect!" ✅
\`\`\`

**Without this methodology:** Would have closed issue as "working" based on programmatic checks alone.

**With this methodology:** Found and fixed the real bug in 90 minutes.

## How It Works

The agent helps by:
1. **Generating base files** - Circuit-synth creates KiCad project scaffold
2. **Waiting for your edits** - You manually place/configure in KiCad
3. **Capturing reference** - Agent documents what's expected
4. **Enabling comparison** - Tests can now validate against reference

## Common Reference Types

### 1. KiCad Project Reference (Most Common)

```bash
User: /dev:test-ref "KiCad project with R1 (10k), R2 (4.7k), C1 (100nF) for position preservation test"

Agent:
Creating base circuit with circuit-synth...

Generated: tests/reference/position-preservation/circuit.kicad_sch

📋 Next Steps:
1. Open: tests/reference/position-preservation/circuit.kicad_sch
2. Place components where you want them (positions, rotations)
3. Add any wires, labels, power symbols
4. Save the file
5. Tell me "done"

[User opens KiCad, places components, saves]

User: "done"

Agent:
✅ Reference captured!

Created: tests/reference/position-preservation/REFERENCE.md

## Reference: Position Preservation Test

### Purpose
Validate that component positions are preserved during sync operations.

### Expected Behavior
- R1 at (30.48, 35.56) mm, 0° rotation
- R2 at (58.42, 35.56) mm, 0° rotation
- C1 at (76.20, 35.56) mm, 0° rotation
- All components on rotation 0°

### How to Use
```python
def test_position_preservation():
    ref_sch = Schematic.load("tests/reference/position-preservation/circuit.kicad_sch")
    # Your test logic here
    # Compare positions against reference
```

### Files
- circuit.kicad_sch - Reference schematic
- circuit.kicad_pro - Project file
- circuit.kicad_pcb - PCB layout (if needed)

---

Now you can develop/test against this reference!
```

**Time saved:** 18 minutes (20 min manual → 2 min with help)

### 2. Log Pattern Reference

```bash
User: /dev:test-ref "Expected log output for successful netlist generation"

Agent:
Running circuit generation to capture logs...

Please review these logs and tell me what's expected vs. noise:

[Shows logs]

User: "Lines with 'Generated netlist' and 'Component validated' are expected. Rest is noise."

Agent:
✅ Reference pattern created!

Created: tests/reference/log-patterns/netlist-generation.txt

# Expected Log Pattern: Netlist Generation

## Success Pattern
- INFO: Generated netlist for {circuit_name}
- INFO: Component {ref} validated
- INFO: Wrote {n} nets to netlist

## Noise (Ignore)
- DEBUG: Symbol loading...
- DEBUG: Footprint resolution...

## Error Patterns (Should NOT Appear)
- ERROR: Component validation failed
- WARNING: Missing footprint

---

Use this pattern in tests to validate log output.
```

### 3. Screenshot Reference

```bash
User: /dev:test-ref "Screenshot of correct label orientation at 90° rotation"

Agent:
I'll help you create this reference.

Please:
1. Generate the circuit showing correct behavior
2. Take screenshot
3. Save as: tests/reference/screenshots/label-90deg-correct.png
4. Tell me what this screenshot shows

User: "Shows VCC label oriented correctly at 90°"

Agent:
✅ Reference documented!

Created: tests/reference/screenshots/REFERENCE.md

## label-90deg-correct.png

**Purpose:** Reference for correct label orientation at 90° component rotation

**What to look for:**
- Label text readable (not upside down)
- Label positioned correctly relative to component
- Label justify setting appropriate for rotation

**Use in tests:** Visual comparison during development

---

Reference ready for visual validation during debugging.
```

### 4. Expected Output Files

```bash
User: /dev:test-ref "Expected .kicad_pcb file structure after PCB generation"

Agent:
Generating PCB with circuit-synth...

Generated: tests/reference/pcb-structure/expected.kicad_pcb

Please review this file. Should I capture:
- Entire file as reference?
- Specific sections (footprints, tracks, zones)?
- Just structure (not exact values)?

User: "Just footprint placement and layer structure"

Agent:
✅ Reference extracted!

Created: tests/reference/pcb-structure/REFERENCE.md

## PCB Structure Reference

### Footprint Placement
- R1: Resistor_SMD:R_0603_1608Metric at (x, y)
- R2: Resistor_SMD:R_0603_1608Metric at (x, y)
- C1: Capacitor_SMD:C_0603_1608Metric at (x, y)

### Layer Structure
- F.Cu (front copper)
- B.Cu (back copper)
- F.Silkscreen
- B.Silkscreen

Tests can validate generated PCBs have this structure.
```

## Reference Storage Organization

```
tests/reference/
├── position-preservation/
│   ├── circuit.kicad_sch
│   ├── circuit.kicad_pro
│   └── REFERENCE.md
├── rotation-tests/
│   ├── 90deg/
│   │   ├── circuit.kicad_sch
│   │   └── REFERENCE.md
│   ├── 180deg/
│   └── 270deg/
├── log-patterns/
│   ├── netlist-generation.txt
│   ├── component-validation.txt
│   └── REFERENCE.md
├── screenshots/
│   ├── label-90deg-correct.png
│   ├── component-placement.png
│   └── REFERENCE.md
└── expected-outputs/
    ├── pcb-structure/
    └── netlist-format/
```

## Workflow Integration

### With /dev:feature

```bash
User: /dev:feature "Add rotation preservation"

Agent: [Creates PRD]

User: "Let's create a reference first"
User: /dev:test-ref "KiCad project with rotated components"

Agent: [Helps create reference]

User: "Now implement the feature"

Agent: [Implements, comparing against reference]
  Cycle 1: Generate circuit
  → Compare to reference: Rotations don't match
  Cycle 2: Fix rotation logic
  → Compare to reference: Now matches!
```

### With /dev:bug

```bash
User: /dev:bug "Labels wrong orientation (#517)"

User: "First, let's capture what 'correct' looks like"
User: /dev:test-ref "Screenshot of correct label orientation"

Agent: [Helps create reference]

User: "Now debug against this reference"

Agent: [Iterates, comparing against reference]
  Cycle 3: Current output doesn't match reference
  Cycle 5: Output now matches reference!
  Bug fixed!
```

## Key Benefits

1. **Speed:** 20 min → 2 min for reference creation
2. **Accuracy:** Agent captures exact details you need
3. **Reusability:** Reference serves multiple tests
4. **Clarity:** Documented expectations prevent confusion
5. **Regression Protection:** Known-good reference prevents backsliding

## Common Patterns

### Pattern 1: Position/Layout Reference
- Generate circuit with circuit-synth
- You place components in KiCad
- Agent documents positions
- Tests validate preservation

### Pattern 2: Visual Reference
- You take screenshot of correct behavior
- Agent documents what's expected
- Manual comparison during development

### Pattern 3: File Structure Reference
- Agent generates example file
- You mark what's important
- Tests validate structure

### Pattern 4: Log Pattern Reference
- Run code to generate logs
- You identify signal vs. noise
- Tests validate log patterns

## Tips for Efficient Reference Creation

1. **Start minimal** - Simplest case that shows the issue
2. **Document intent** - Why this reference exists
3. **Version control** - Commit references to git
4. **Update when needed** - /update-ref when behavior intentionally changes
5. **One concern per reference** - Position OR rotation OR values, not all at once

## Integration with kicad-sch-api

Remember: We maintain kicad-sch-api and kicad-pcb-api.

When creating references, consider:
- Is this testing circuit-synth behavior? → Reference here
- Is this testing kicad-sch-api behavior? → Reference in that repo
- Is this integration? → Reference in both repos

## Success Criteria

Reference is "done" when:
- [ ] Base files generated (if applicable)
- [ ] User has edited/configured files
- [ ] REFERENCE.md documents expectations
- [ ] Tests can use this reference for validation
- [ ] Reference is minimal (simplest case that works)
- [ ] Reference is documented (clear intent)

---

**This command transforms reference creation from tedious manual work into efficient collaboration, enabling 10x faster iterative development.**
