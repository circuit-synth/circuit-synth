---
name: new-kicad-project
description: Bootstrap a brand-new circuit-synth / KiCad project from an empty folder in one step, then hand off to circuit design. Use when the user asks to "start/create a new KiCad project", "new circuit-synth project", "set up a new board", or opens an empty directory and asks to begin a circuit. NOT for editing an existing project (that already has its own design-circuit skill).
---

# Start a new circuit-synth / KiCad project

Turns "start a new KiCad project called X" into a ready-to-design project: creates
the folder, installs circuit-synth, scaffolds the `.claude/` skill + `.mcp.json` +
a starter circuit, and generates the first schematic. Wraps the `cs-bootstrap`
console script.

## Inputs to settle first
- **Project name** — from the user's request; else ask. Must be a valid package
  name (letters/digits/`_`/`-`, no leading underscore or digit).
- **Where** — the current working directory by default (pass `--base-dir` to place
  it elsewhere). The new project is created as a **subfolder** `<name>/`.
- **Starter circuit(s)** — optional, e.g. `resistor,led`. Omit for the default
  (resistor divider). If the user described a specific circuit, still scaffold the
  default here, then design theirs in the handoff step.

## Install source (important)
`cs-bootstrap` installs circuit-synth from **PyPI by default** — this is correct for
normal/public use. Use the **editable local fork only for development**, and only
when opted in:
- If the `CIRCUIT_SYNTH_FORK` environment variable is set, or the user says "dev" /
  points at a local checkout, install editable from that path.
- Otherwise, PyPI.

Never hardcode a fork path. Check the env var; if absent, default to PyPI.

## Run it

`cs-bootstrap` only needs circuit-synth importable *once* to launch; the new
project's own `uv init` then picks a wheel-compatible Python and resolves deps, so
the launcher's interpreter doesn't have to have every wheel.

**Local dev (against a patched checkout — set `CIRCUIT_SYNTH_FORK` or pass the
path).** Launch with the already-installed circuit-synth (most reliable — avoids
rebuilding the fork in an ephemeral env, which can fail where the launcher's Python
lacks a dep wheel):

```bash
# If cs-bootstrap is on PATH (circuit-synth installed):
cs-bootstrap <name> --editable "$CIRCUIT_SYNTH_FORK" [--circuits resistor,led]

# Otherwise call the module directly (always works when circuit-synth is importable):
python -m circuit_synth.tools.project_management.bootstrap <name> \
    --editable "$CIRCUIT_SYNTH_FORK" [--circuits resistor,led]
```

**Public / normal (from PyPI, once a release ships `cs-bootstrap`).** Works from any
empty folder with only `uv` installed:

```bash
uvx --from circuit-synth cs-bootstrap <name> [--circuits resistor,led]
```

`cs-bootstrap --help` lists all flags (`--base-dir`, `--pypi-spec` to pin a version,
`--no-agents`, `--no-generate`).

## After it runs — the handoff
`cs-bootstrap` prints the project location and a verified schematic. Then:

1. **Tell the user to open the NEW folder as the workspace in Claude Code.** The
   project ships its own `.claude/skills/design-circuit` skill and a `.mcp.json`
   wiring the `kicad-sch-api` MCP — but those load only when Claude Code opens
   *that folder* as the workspace. They are not hot-loaded into the current session.
2. Once reopened there, the user describes the circuit they want and the project's
   **design-circuit** skill drives the plan → write → generate → simulate → refine
   loop. If you are already operating inside the new folder (e.g. the user reopened
   it), invoke `design-circuit` directly.

## Guardrails
- Don't overwrite an existing directory — `cs-bootstrap` refuses if `<name>/`
  exists; pick a different name or `--base-dir`.
- Requires `uv` and (to open results) KiCad 10. Scaffolding/generation are headless;
  KiCad is only needed to open the `.kicad_pro`.
- A "Gerber generation failed (return code 3)" message is expected in this build —
  PCB/Gerber output is out of scope; schematic/BOM/PDF are the real deliverables.
