# circuit-synth

Define electronic circuits in Python and generate KiCad projects (schematic +
PCB) from them.

> **This is a development fork** of [circuit-synth](https://github.com/circuit-synth/circuit-synth).
> It is not published to PyPI under this fork; install it locally (below).
> Everything documented here is verified against the code in `src/circuit_synth/`.

## What it does

You describe components and their connections in Python; circuit-synth produces
a complete KiCad project. Because the design is code, it is diffable,
version-controlled, and composable — subcircuits are just functions you call.

```python
from circuit_synth import circuit, Component, Net

@circuit(name="Power_Supply")
def power_supply(vin, vout, gnd):
    """5V -> 3.3V linear regulator with decoupling."""
    reg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )
    cin  = Component(symbol="Device:C", ref="C", value="10uF")
    cout = Component(symbol="Device:C", ref="C", value="22uF")

    reg["VI"] += vin
    reg["VO"] += vout
    reg["GND"] += gnd
    cin[1]  += vin;  cin[2]  += gnd
    cout[1] += vout; cout[2] += gnd

@circuit(name="Main")
def main():
    vbus, vcc, gnd = Net("VBUS"), Net("VCC_3V3"), Net("GND")
    power_supply(vbus, vcc, gnd)

if __name__ == "__main__":
    main().generate_kicad_project("my_board")   # -> my_board/*.kicad_sch, *.kicad_pcb
```

## Install (development fork)

```bash
git clone <this fork's url> circuit-synth
cd circuit-synth
uv sync                     # create the environment from uv.lock
uv run pytest               # sanity-check the install
```

Requirements:
- Python 3.12+
- `uv` (environment/build; the project uses setuptools + uv, not poetry)
- A KiCad install with `kicad-cli` on PATH. The fork's active work targets
  KiCad 10; `kicad-cli` is used for BOM/PDF/Gerber export.

## Core API

Exported from `circuit_synth`: `circuit`, `Component`, `Net`, `Pin`, `Circuit`.

- `Component(symbol=..., ref=..., footprint=..., value=..., **fields)` — a KiCad
  symbol instance. Extra keywords become component fields (used in the BOM).
- `Net("NAME")` — an electrical net. Connect a pin with `component["PIN"] += net`
  (named) or `component[1] += net` (numbered).
- `@circuit(name=...)` — decorates a function into a circuit; call other
  `@circuit` functions inside it to build hierarchy.

### Generation and manufacturing outputs

Methods on the circuit object returned by a `@circuit` function:

```python
c = main()

c.generate_kicad_project(
    "my_board",
    generate_pcb=True,                 # also lay out a .kicad_pcb
    placement_algorithm="hierarchical",# or "simple"
    force_regenerate=False,            # True discards manual KiCad edits
    update_source_refs=None,           # see "Reference rewriting"
)

c.generate_bom("my_board")            # CSV BOM (kwargs: output_file, group_by, exclude_dnp, ...)
c.generate_pdf_schematic("my_board")  # PDF (kwargs: black_and_white, pages, ...)
c.generate_gerbers("my_board")        # Gerber + drill files
```

BOM/PDF/Gerber export shells out to KiCad's `kicad-cli`. See
[docs/BOM_EXPORT.md](docs/BOM_EXPORT.md), [docs/PDF_EXPORT.md](docs/PDF_EXPORT.md),
[docs/GERBER_EXPORT.md](docs/GERBER_EXPORT.md).

### Reference rewriting

When references are finalized during generation (e.g. `ref="C"` becomes
`ref="C1"`), circuit-synth can write the finalized refs back into your Python
source file, so repeated generations stay consistent. Controlled by
`update_source_refs` (default `None` = auto-update unless `force_regenerate=True`;
pass `True`/`False` to force it). It rewrites `ref=` assignments only and leaves
comments/docstrings alone.

### Round-trip (KiCad <-> Python)

Both directions exist as CLI tools: `python-to-kicad` and `kicad-to-python`. You
can generate from Python, edit in KiCad, and import back.

## Starting a project

```bash
uv run cs-new-project my_board     # scaffold a project (starter circuit + Claude tooling)
cd my_board
uv run python circuit-synth/main.py   # generate the KiCad files
```

`cs-new-project` copies the packaged `example_project` template (a `circuit-synth/`
source folder, a `.claude/` design skill, and `tools/find_symbol.py`).
`cs-bootstrap` does the same and can run `main.py` for you in one step.

## Other capabilities (real, optional)

These exist in the package; most need extra setup or network access, and are
peripheral to the core Python -> KiCad flow:

- **SPICE simulation** — `circuit.simulator()` exposes `operating_point()`,
  `ac_analysis()`, etc. (ngspice). See [docs/SIMULATION_SETUP.md](docs/SIMULATION_SETUP.md).
- **FMEA report** — `cs-fmea my_circuit.py` generates a reliability report. See
  [docs/FMEA_GUIDE.md](docs/FMEA_GUIDE.md).
- **Component sourcing** — JLCPCB/DigiKey/SnapEDA search via the `jlc-fast` CLI
  and `circuit_synth.manufacturing.find_parts(...)`. DigiKey/SnapEDA need API
  keys (`cs-setup-digikey-api`, `cs-setup-snapeda-api`); JLCPCB search needs
  network access.

## Claude Code integration

The design loop is driven by skills and tools (not custom slash commands):

- **`new-kicad-project` skill** — bootstrap a new project.
- **`design-circuit` skill** — the design → verify → generate loop, including
  symbol/footprint lookup via `tools/find_symbol.py`.
- **kicad-sch-api MCP server** — programmatic read/write of `.kicad_sch` files.

Verify symbols/footprints with `tools/find_symbol.py` rather than trusting a
static list — names vary by KiCad version and are easy to get wrong.

## Development

```bash
uv run pytest                # tests
black src/ tests/            # format (also run by pre-commit)
isort src/ tests/
```

See [CLAUDE.md](CLAUDE.md) for the working policy (human-in-the-loop; commit
often; **no PyPI releases**) and the loop boundary contract, and
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) / [docs/TESTING.md](docs/TESTING.md).

## Architecture

JSON is the canonical intermediate representation between Python and KiCad,
which makes the design text-based and round-trippable. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/JSON_SCHEMA.md](docs/JSON_SCHEMA.md).

## License

MIT
