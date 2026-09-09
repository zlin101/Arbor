---
name: dual-review-loop
description: Bounded dual-review convergence loop — two fresh read-only reviewers in parallel, dedupe, fix, validate, full-scope re-review until PASS or bounded STOP. Use when asked to run the dual review loop or review-and-fix a change until clean.
---

# Dual Review Loop

You are the orchestrator — and the ONLY writer. Two independent fresh reviewers see the
same frozen scope in parallel; you fix, validate, and re-review with two NEW reviewers
until the change converges or a bounded stop fires.

## Inputs

- **Scope source** from the user's request: working tree (default), branch vs base,
  commit range, or explicit files — resolved per `references/review-scope.md`.
- Optional explicit overrides, honored only when the user states them: `strict`
  (P2 joins the convergence gate), `max_rounds`.
- Everything else comes from the contracts below. Precedence: user's explicit
  instruction > target project instructions (`AGENTS.md` and equivalents) > this
  skill's defaults. Never bypass project rules.

## Roles

- **You (main agent)**: freeze scope, spawn reviewers, normalize/dedupe, fix, validate,
  decide PASS/STOP. Sole write owner.
- **Reviewers**: fresh read-only subagents. They never fix, never write, never see
  prior-round findings.

## Round algorithm

```text
read project instructions (AGENTS.md / project docs)
freeze review scope (baseline_commit anchors the loop; see review-scope.md)

for round in 1..max_rounds:
    materialize FULL current change: frozen baseline → current state (never just the last fix diff)
    spawn BOTH reviewers in parallel, same turn (see reviewer-prompt-contract.md):
        - correctness reviewer  → dual-review-correctness skill
        - structure reviewer    → dual-review-structure skill
    collect unified YAML verdicts
    normalize + root-cause dedupe + assign F-ids + map to previous round
        (see finding-schema.md)
    if convergence gate met AND required validation green (see convergence-contract.md):
        run final required validation if not yet run → report PASS (see output-format.md); done
    select actionable blockers (P0 → P1 → structural blockers → low-risk in-scope P2)
    if none actionable → STOP (blocked / unresolved)
    if oscillation detected → STOP (present both trade-offs)
    apply ONE coherent root-cause fix batch           # you are the only writer
    run project validation (project's own commands; repair or revert YOUR fix if it regressed)
    update no-progress counter (blocking set shrank? validation improved?)
    if no_progress >= 2 → STOP (no progress)
```

Round 1 special case: if both reviewers return PASS, run the required validation once,
then PASS — no fixes, no modifications.

## Guards

Defaults: `max_rounds: 3`, `no_progress_rounds: 2` (user may override explicitly).

| Stop on | Meaning |
|---|---|
| max rounds | rounds exhausted with blockers open |
| no progress | 2 consecutive rounds without the blocking set shrinking or validation improving |
| oscillation | design flip-flopping between two directions — stop, present trade-offs, hand back |
| permission boundary | fix needs destructive action / external write / authorization the loop lacks |
| reviewer conflict | material disagreement unresolved after ONE evidence-resolution pass — never majority vote |

Full gate definitions and fix policy: `references/convergence-contract.md`.

## Runtime adaptation (spawning reviewers)

- **Claude Code**: in ONE message, dispatch both plugin agents —
  `dual-review-correctness-reviewer` and `dual-review-structure-reviewer` — passing each
  the same scope materialization (baseline identity, diff / changed-file contents,
  project instructions) in labeled sections. Their read-only toolsets are enforced by
  the runtime.
- **Codex**: in one turn, spawn two subagents, telling each to follow its reviewer
  skill; include the isolation template verbatim from
  `references/reviewer-prompt-contract.md` and the same scope materialization. Optionally
  point the user at read-only sandbox agent TOMLs — never required.
- Both runtimes: reviewers never write, never spawn subagents, never see earlier
  rounds' findings.

## Final report

Render exactly one of the two templates in `references/output-format.md` — PASS or
STOPPED — and nothing longer. Never commit, push, or open PRs unless the user
explicitly asked.

## References

| File | Purpose |
|---|---|
| `references/review-scope.md` | scope model, baseline freeze, full-scope re-review rule |
| `references/reviewer-prompt-contract.md` | isolation template, fresh-context rule, spawn checklist, runtime table |
| `references/finding-schema.md` | verdict envelope, dedupe semantics, F-id mapping, lifecycle |
| `references/convergence-contract.md` | PASS gate, fix policy, validation contract, stop guards |
| `references/output-format.md` | final PASS / STOPPED report templates |
