---
name: layout-schematic
description: Lay out a generated KiCad schematic so it reads like a schematic an engineer drew - grouped by function, wired with orthogonal wires, power symbols on the rails, nothing overlapping. Use when converting a circuit-synth Python script to KiCad, or when an existing generated project looks messy. Triggers on "generate the schematic", "convert this to KiCad", "the schematic looks bad", "lay out the schematic", "tidy the schematic".
---

# Laying out a generated schematic

circuit-synth works out what connects to what. It does not know that a
half-bridge is drawn as a totem pole, that decoupling capacitors belong beside
the pin they decouple, or that signals should flow left to right. That is a
judgement call, and it is yours to make here.

You place the parts and draw the wires. The library gives you the geometry to
do it with and checks that you have not changed the circuit.

## The loop

1. **Generate** the project from the Python script.
2. **Describe** each sheet: parts, pin positions, pin types, nets.
3. **Place** - decide where everything goes and how it is wired. This is the
   part only you can do.
4. **Apply** the placement.
5. **Validate** that the connectivity is unchanged. This is not optional.
6. **Render** the sheet to a PNG and *look at it*.
7. **Refine** and repeat from 3 until it reads well. Two or three passes is
   normal; the first pass gets the topology right, later passes fix text that
   collides and space that is used badly.

## Running it

```python
from pathlib import Path
from circuit_synth.kicad.layout import (
    describe_sheet, PlacementSpec, apply_placement, validate_layout, render_sheets,
)
from circuit_synth.kicad.layout.extract import sheet_nets, sheet_ports

project = Path("bldc_motor_driver")
root = project / "BLDC_Motor_Driver.kicad_sch"
circuit_json = project / "BLDC_Motor_Driver.json"

# 2. Describe the sheet you are about to lay out.
nets, ports = sheet_nets(circuit_json), sheet_ports(circuit_json)
sheet = describe_sheet(project / "PhaseDriver.kicad_sch",
                       nets["PhaseDriver"], ports["PhaseDriver"])
print(sheet.to_json())

# 4. Apply the placement you wrote.
apply_placement(project / "PhaseDriver.kicad_sch",
                PlacementSpec.from_json(Path("phasedriver.json")))

# 5. Validate. Must be empty.
problems = validate_layout(root, circuit_json)
assert not problems, problems

# 6. Look at it.
render_sheets(root, project / "img")
```

Then Read the PNG. Judge it. Fix what is wrong.

## What the description gives you

For every part: reference, value, library id, body size, and every pin with its
number, name, electrical type, offset from the symbol origin and which net it is
on. The offsets are what you place against - a pin ends up at the symbol
position plus its offset, rotated.

Rotation moves a pin the opposite way round from the naive sign convention. At
90 degrees a two-pin part has pin 1 on the **left**. Check the offsets in the
description rather than assuming.

## The placement spec

```json
{
  "components": [{"ref": "U3", "at": [76.2, 88.9], "rotation": 0}],
  "wires": [[[83.82, 81.28], [102.87, 81.28]]],
  "junctions": [[102.87, 81.28]],
  "labels": [
    {"text": "HI", "at": [58.42, 88.9], "rotation": 180,
     "kind": "hierarchical", "shape": "input"},
    {"text": "BOOT", "at": [102.87, 78.74], "rotation": 0, "kind": "local"}
  ],
  "power": [{"lib_id": "power:GND", "at": [76.2, 106.68], "rotation": 0}],
  "no_connects": []
}
```

Applying a spec moves the symbols and redraws all of the wiring. Component
UUIDs, properties and hierarchical instance paths are left alone, so the sheet
stays the same design.

## Rules that are not negotiable

- **Everything on the 1.27mm grid.** A wire that misses a pin by a fraction
  looks connected and is not. `apply_placement` rejects off-grid coordinates.
- **Validate every time.** `validate_layout` compares the schematic KiCad reads
  back against the circuit JSON, pin for pin. If it reports anything, your
  wiring is wrong - fix it, do not ship it.
- **Orthogonal wires only.** Horizontal and vertical segments, never diagonal.
- **A junction wherever three or more connections meet.** Two wires that merely
  cross are separate nets in KiCad; three that meet without a junction are not
  connected at all.
- **Ground and the supply rails use power symbols**, never a wire dragged
  across the sheet and never a label.
- **A hierarchical label for every declared port**, with the direction the
  block declared, or the sheet pin above it will not match.

## Conventions to follow

**Flow.** Signals go left to right, inputs on the left edge, outputs on the
right. Power comes in at the top, ground goes out at the bottom. If a signal
has to go backwards, it is usually a sign the parts are in the wrong order.

**Grouping.** Draw each functional block as a unit, separated from the next by
clear space. A reader should be able to point at the bootstrap supply, the gate
drive and the half-bridge as three distinct things.

**Anchors first.** Place the IC that defines the block, then arrange the parts
around it on the side their pins face. Do not put a part on the left of a chip
if it wires to a pin on the right.

**Passives.** Series parts lie horizontally in line at a constant pitch.
Anything to a rail stands vertically, with the rail above or the ground symbol
below. Decoupling capacitors sit next to the pin they decouple, not in a row at
the bottom of the sheet.

**Standard shapes.** Draw the circuits that have a conventional appearance the
conventional way: a half-bridge as a vertical totem pole with the phase node
between the two devices, a divider as a vertical stack with the tap on the
right, an op-amp with the feedback over the top.

**Spacing.** 2.54mm minimum between anything and anything. Leave a wire long
enough to read as a wire - 5mm or more. Fill the sheet rather than crowding the
top-left corner, but do not spread a small circuit over a whole page either;
pick the paper size to suit.

**Text.** Nothing may overlap. Net labels sit on a short stub off the pin, not
over the symbol body. Check the render, since symbol reference and value text
moves with the symbol and collides in ways the coordinates do not show.

## Sheets of hierarchical blocks

A sheet whose parts are all sheet symbols is laid out the same way, using the
same flow: source blocks on the left, consumers to the right, one sheet symbol
per block with its pins on the side the signal travels. Give each sheet symbol
room for its pin names.

## When you cannot make something clean

Say so. A sheet with thirty parts and no structure may genuinely need a
different sheet size or a split into sub-blocks. Suggest that rather than
producing a dense layout and calling it done.
