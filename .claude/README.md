# circuit-synth — `.claude/` development integration

Agents and slash commands for developing this fork with Claude Code.
**Read `../CLAUDE.md` first** — it's the development guide (working policy,
loop boundary contract, testing).

## Commands (`.claude/commands/dev/`)

- `update-and-commit.md` — document changes and commit
- `bug.md`, `feature.md`, `make-test.md`, `test-ref.md`, `review-prompt.md`,
  `compare-three-repos.md` — task-specific helpers

For code review and security review, use the built-in `/code-review`,
`/review`, and `/security-review` (not a custom command).

## Agents (`.claude/agents/`)

- `prompt-improver.md`

## Running tests

```bash
uv run pytest
```

## Settings

`.claude/settings.json` holds Claude Code configuration (model, environment).

---

Working policy lives in `../CLAUDE.md`: human-in-the-loop (design → evaluate →
test → branch/commit), commit often, **no PyPI releases**.
