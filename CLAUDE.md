# CLAUDE.md — circuit-synth (fork) development guide

Fork of `circuit-synth/circuit-synth`, taken 2025-07-02 at commit
`ddb15a50afe9d17f389deb32f0973061a4abae67`. This guide covers how Claude Code
helps develop **this fork**.

**We are not releasing to PyPI.** There is no version bump, publish, or release
step. The goal is a human-in-the-loop cycle: **design → evaluate → test →
branch/commit**, iterated with the user steering.

---

## Working policy

- **Human in the loop.** Propose an approach and show evidence; let the user
  decide. Don't autonomously make large, destructive, or outward-facing changes
  without checkpointing first.
- **Commit often.** Small, focused commits on a working branch (not `main`).
  Clear messages. No releases, no version bumps, no publishing.
- **Test before you commit.** Prefer writing/adjusting a test that captures the
  intended behavior, then make it pass. Never commit code you haven't run.
- **Observe, don't assume.** Reproduce and read actual behavior (logs, test
  output, generated files) before theorizing about a cause.
- **Fix the root cause in the right layer** (see Loop boundary contract and
  Layer separation below) rather than papering over it.

---

## Loop boundary contract

The design loop has a **language-agnostic layer** (design-circuit SKILL.md
procedure, `tools/find_symbol.py`, the kicad-sch-api MCP server, `.claude`/`.mcp.json`)
kept separate from the **circuit_synth-coupled engine** (`core`, `simulation`,
`kicad.sch_gen`, `interop.skidl_export`) so a future DSL swap (e.g. SKiDL) stays a
live option at near-zero cost. This is a stated, test-enforced contract:
`workingdocs/design_considerations/loop-boundary-contract.md` (rules R1–R5), enforced by
`tests/unit/test_loop_boundary_contract.py`. **New loop tooling must declare its
layer** (add a row to the contract's layer table in the same commit — rule R5).

---

## Investigation: tight, log-driven cycles

Work in short loops, not big-bang edits: **add a strategic log → run → observe →
adjust → repeat.** Each cycle should teach you one concrete thing.

- Mark temporary investigation logs with a `CYCLE:` prefix so they're easy to
  grep out and remove before committing.
- Silence noisy modules while studying one area
  (`logging.getLogger('circuit_synth.netlist').setLevel(logging.WARNING)`), and
  raise the level only on the code under study.
- Keep genuinely useful operational logs (state transitions, warnings, errors);
  delete the scaffolding.
- **No emojis or decorative characters in log output** — plain, parseable text.

Report findings as you go: what the log showed, your current hypothesis, and the
next thing you'll check. This keeps the human able to redirect early.

---

## Code quality (what's actually enforced)

- **Formatting:** `black` and `isort` run via pre-commit
  (`.pre-commit-config.yaml`), plus trailing-whitespace / end-of-file / line-ending
  hygiene hooks. Run `pre-commit run --all-files` before committing broad changes.
- **Type hints** on new functions; **docstrings** on public APIs.
- **Writing:** technical claims only — no marketing language, no aspirational
  "this will…" docs. If a doc describes something, it should exist and match.

(Note: mypy, ruff, bandit/safety, and coverage gates are *not* currently wired
up. Don't claim they ran unless you actually ran them.)

---

## Layer separation — where to fix a bug

circuit-synth sits on top of sibling API layers we also control in this workspace
(`kicad-sch-api` and its MCP server, `mcp-kicad-sh-api`). When you hit a bug:

1. **Root cause in circuit-synth** → fix it here.
2. **Root cause in the API layer** → fix it there, in that repo, with a test —
   don't add a workaround in circuit-synth that hides an upstream defect.

This mirrors the loop boundary contract: keeping the engine and the
language-agnostic tooling honest is what keeps a DSL swap cheap.

---

## Repo layout

```
circuit-synth/
├── src/circuit_synth/
│   ├── core/            # Circuit, Component, Net
│   ├── kicad/           # KiCad integration (sch_gen, pcb_gen, ...)
│   ├── simulation/      # SPICE / ngspice
│   ├── interop/         # skidl_export and other backends
│   ├── fast_generation/ # reference circuits
│   ├── io/  manufacturing/  pcb/  quality_assurance/  ...
│   └── data/            # bundled skills, templates, tools
├── tests/
│   ├── unit/            # incl. test_loop_boundary_contract.py
│   ├── bidirectional/   # KiCad <-> Python sync test suite
│   └── ...
└── .claude/
    ├── agents/          # dev agents
    └── commands/dev/    # slash commands
```

Build backend is setuptools; the environment is managed with **uv** (`uv.lock`).
Not poetry.

---

## Commands

- Run tests directly: `uv run pytest` (see Testing below).
- `/dev:update-and-commit [description]` — document changes and commit.
- Code review / security: use the built-in `/code-review`, `/review`, and
  `/security-review`.

---

## Testing

- **Unit** — individual functions/classes (`tests/unit/`).
- **Integration / bidirectional** — KiCad↔Python round-trips and sync
  (`tests/bidirectional/`).
- **Regression** — lock in fixed bugs so they stay fixed.
- The loop boundary contract is itself a test — keep it green when adding loop
  tooling.

Run the relevant tests for what you touched, and say plainly what passed, what
failed, and what you skipped.
