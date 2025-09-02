# CLAUDE.md — PRD + Logging Cooperative Workflow (Slim)

> **Premise:** Keep it simple. We collaborate through a **thorough but crisp PRD**, build in **small chunks** with **TDD or probes**, and use **extensive logging breadcrumbs** so it’s obvious where logic runs, what decisions were made, and how to troubleshoot.

---

## Repo & Naming

* **PRDs:** `.claude/PRD/PRD-YYYYMMDD-<slug>.md`  (Status: Draft → Implementable → Shipped)
* **Bugs:** `./claude/bug_fixes/BUG-YYYYMMDD-<slug>.md`

```bash
mkdir -p .claude/PRD ./claude/bug_fixes
```

---

## Core Loop

1. **Ask lots of questions** (be inquisitive; mark blocking vs. non‑blocking).
2. **Draft/Update PRD** (it’s the source of truth).
3. **Break into small chunks** (each proves one behavior).
4. **TDD or probe‑first** (write a test or a precise probe before code).
5. **Log breadcrumbs extensively** (see below).
6. **Iterate**: code → run → read logs/tests → adjust → repeat until acceptance passes.

---

## Default Response (keep answers short)

* **Summary & Success Criteria**
* **Questions** (grouped; defaults offered; blocking tagged)
* **Plan** (3–5 bullets)
* **Chunks + Acceptance** (Given–When–Then)
* **Test/Probe Next** (what we’ll add now)
* **Next Action** (one concrete step)

---

## PRD — Thorough but Crisp (features)

**Header:** `PRD-YYYYMMDD-<slug>` | Owner | Status | Version | Last updated

**1. Executive Summary** — who/what/why now.
**2. Goals / Non‑Goals** — scope boundaries.
**3. Acceptance Criteria (Given–When–Then)** — clear, verifiable.
**4. Requirements** — functional + key non‑functional.
**5. Interfaces & Data Contracts** — inputs/outputs; link ERD only if data‑heavy.
**6. Risks & Open Questions** — with how we’ll answer them.
**7. Test Strategy** — what proves it works.
**8. Logging Notes** — what breadcrumbs we expect to see when it runs.
**Change Log** — date/version/summary.

---

## Unified Bug Fix Doc (single file)

**Header:** `BUG-YYYYMMDD-<slug>` | Owner | Status | Version | Last updated
**1. Summary & Impact**
**2. Environment & Repro**
**3. Expected vs. Actual**
**4. Hypotheses → Experiments** (tests/probes)
**5. Change Plan** (smallest safe)
**6. Embedded Logging Plan** (breadcrumbs for the fix)
**7. Acceptance (Given–When–Then)**
**8. Rollback/Mitigations**
**9. Evidence (key logs/traces)**
**Change Log**

---

## Chunk Template (tiny)

```
Chunk: <name>
Acceptance: <Given–When–Then>
Test/Probe: <first proof>
Next Step: <one action>
```

---

## TDD / Probe‑First (tiny)

1. Add a failing test **or** a precise probe.
2. Make it pass with the **smallest** change.
3. Refactor; keep green.
4. Read logs; tighten probe if needed.

---

## Logging Breadcrumbs (directive)

Use **extensive, moderate‑frequency breadcrumbs** to make execution paths obvious:

* Log **entry/exit** of key functions/steps.
* Log **decisions** (conditions, chosen branches, key parameters).
* Log **inputs/outputs** at boundaries.
* Include a **run/session id** when helpful.
  Keep messages short, consistent, and easy to scan. Demote/trim once acceptance passes, but leave enough to troubleshoot later.

---

## Ready‑to‑Use Prompts

**PRD Builder** — "Draft a crisp PRD using the template with Given–When–Then acceptance and brief logging notes."

**Bug Doc Builder** — "Create the unified bug document (report + fix plan + logging) with repro, hypotheses→experiments, acceptance, and rollback."

**Intake & Plan** — "Summarize goals, ask grouped questions, outline a short plan, list chunks with acceptance, specify the first test/probe, and give one next action."

**Question Bank (auto‑ask)** — "List questions across goals/users, constraints, interfaces/data, environment, acceptance, risks, rollout; mark blocking vs. non‑blocking and suggest defaults."
