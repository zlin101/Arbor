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
  (P2 and structural improvements join the convergence gate), `max_rounds`.
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
    resolve material reviewer conflicts: ONE evidence pass; if still undecidable
        → STOP (conflict). audit classifications against evidence; downgrade only
    derive gate blockers from the policy table (convergence-contract.md §1;
        strict profile only if the user asked)
    if gate blockers == 0:
        ensure validation is CURRENT (no write since it last ran); run it now if not
        green     → report PASS (see output-format.md); done
        not green → classify the failure per the validation contract → done or repair
    select actionable FINDINGS (P0 → P1 → structural regressions → low-risk in-scope P2)
    if none actionable → STOP (blocked / unresolved)
    if a stop guard fires → STOP per the precedence table (convergence-contract.md §5)
    apply ONE coherent root-cause fix batch           # you are the only writer
    run project validation (project's own commands; repair or revert YOUR fix if it regressed)
    update progress: persistent / resolved / new (convergence-contract.md §5)
    if stagnation sustained → STOP (no progress)
```

Validation is the action that COMPLETES convergence: when gate blockers reach zero,
run the required validation on the current tree — never STOP for lack of a fix while
validation is still unrun.

## Guards

Defaults: `max_rounds: 3`, `no_progress_rounds: 2` (user may override explicitly).

| Stop on | Meaning |
|---|---|
| max rounds | rounds exhausted with gate blockers open |
| no progress | stagnation sustained: persistent blockers unimproved AND validation not improving (resolved-old + equal-count new blockers is churn, not stagnation) |
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
