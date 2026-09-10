# dual-review-loop — Regression Eval Runbook (v0.2)

Central definition of the behavioral regression matrix. One file, no per-case
directories, no evaluator engine: fixtures come from
`docs/acceptance/fixtures/plant.py` (or are stated inline as synthetic histories),
expected outcomes are fixed here, and actual outcomes are produced by release runs
on real runtimes. Deterministic static checks live in `scripts/check_repo.py` and
run on every PR; the behavioral cases here run before a release.

## Evidence classes

- **LIVE-LOOP** — a fresh driver executes the full loop with real parallel reviewer
  subagents on a fixture; transcripts recorded under `docs/acceptance/transcripts/`.
- **DECISION-PROCEDURE** — a fresh agent applies the contract text to a stated
  synthetic history (no subagents). Verifies the contract's decision procedure, not
  model loop behavior. Labeled per case; the two classes are never conflated.

## Case matrix

| Case | Class | Fixture / input | Must prove | v0.1 status |
|---|---|---|---|---|
| E01 Clean | LIVE-LOOP | `plant.py <dir> A` | round-1 dual PASS + current validation → PASS; zero modifications | pass (scenario A) |
| E02 Correctness blocker | LIVE-LOOP | `plant.py <dir> B` | blocker → single-writer fix → current validation → fresh FULL-scope re-review → PASS | pass (scenario B) |
| E03 Structural regression | LIVE-LOOP | `plant.py <dir> C` | structural `regression` blocks; `improvement`/taste never block convergence | pass (scenario C, pre-v0.2 schema) |
| E04 Duplicate root cause | LIVE-LOOP | `plant.py <dir> D` | same root cause across lenses → ONE F-id; different root causes at one symbol stay separate | pass (scenario D) |
| E05 Residual-only | DECISION-PROCEDURE | case R1 below | no gate blocker + residuals → validation RUNS on current tree → PASS (never STOP for want of a fix) | **FAILS on v0.1** (R1) |
| E06 Cross-boundary regression | LIVE-LOOP | `plant.py <dir> X` (v0.2) | change-caused regression may manifest in untouched code and stays in scope with a causal link; unrelated pre-existing issues stay out | **FAILS on v0.1** (R2) |
| E07 Progress semantics | DECISION-PROCEDURE | cases R3, R4 below | persistent stagnation triggers no-progress; resolved-old + equal-count new (churn) does NOT | **FAILS on v0.1** (R4) |
| E08 Oscillation | DECISION-PROCEDURE | history in scenario-E transcript | inline↔extract flip-flop → STOPPED oscillation with both trade-offs; no third fix | pass (scenario E) |
| E09 Reviewer conflict | DECISION-PROCEDURE | synthetic: reviewers disagree on material behavior; one evidence-resolution pass settles it → loop continues; if unresolved → STOPPED conflict | pass (contract text; exercised in H evidence) |
| E10 Validation failure | LIVE-LOOP | fixture with failing validation | change-caused failure repaired within round; unattributable/external failure → residual risk or BLOCKED, never silently ignored | pass (contract §3; H ran green path) |

## v0.2 failure cases (reproduce the four P1 defects on v0.1)

### R1 — Residual-only + validation unknown (E05, DECISION-PROCEDURE)

Input history (max_rounds 3): round-1 correctness `verdict: PASS`; structure
`verdict: FINDINGS` with exactly one P2 `improvement` residual (blocking-derived
policy: non-block); required validation NOT yet executed this session.

- v0.1 algorithm (`SKILL.md`): `if convergence gate met AND required validation green`
  is FALSE (validation unknown) → falls through to `select actionable blockers` →
  no gate blocker, P2 not selected (not low-risk in-scope) → `none actionable → STOP`.
  **Wrong: STOPPED although the change may be convergent.**
- Empirically confirmed on v0.1 text (2026-09-10, DECISION-PROCEDURE run recorded in
  `docs/acceptance/transcripts/`): evaluator walked the exact branches — gate false
  (validation leg unmet), PASS branch unreachable, no validation site reachable,
  terminal `STOP (blocked / unresolved)`; verdict: "the v0.1 text has a dead-end here".
- v0.2 required outcome: gate blockers derived first = 0 → validation RUNS on the
  current tree → PASS (validation green) / classify failure (not green). Validation
  is the action that COMPLETES convergence, not a precondition to enter the path.

### R2 — Cross-boundary regression (E06, LIVE-LOOP, fixture key `X`, added in v0.2)

Base: `store.py` + untouched caller `report.py` (imports `Store`, calls `get()`,
subscribes to the plain-value contract). Planted change: `get()` return semantics
change (wraps value), store.py only. Correctness reviewer must be ABLE to report:
crash manifests in untouched `report.py`, root cause is the changed `get()` — finding
IN scope, with a causal link to the changed code. An unrelated pre-existing wart in
`report.py` (e.g. pre-existing magic string) remains OUT of scope.

- v0.1 contract (`review-scope.md` §4, correctness SKILL §3): "findings may only be
  raised against code the change adds or modifies" / untouched code "context, not
  findings" → **the regression is unreportable. Wrong scope predicate.**
- v0.2 required outcome: causality-based scope — "in scope iff causally attributable
  to the target change"; untouched code admissible as manifestation/evidence.

### R3 — Persistent stagnation (E07 positive, DECISION-PROCEDURE)

History (from scenario-I transcript): same root cause recurring in equivalent form
across rounds, no validation improvement → no-progress counter 0 (r1 baseline) → 1
(r2) → 2 (r3) → STOPPED no progress. v0.2 keeps this outcome: persistent blockers
unchanged + no validation improvement = stagnation.

### R4 — Resolution progress mislabeled as stagnation (E07 negative, DECISION-PROCEDURE)

Input history (max_rounds ≥ 3): r1 blockers {F-a, F-b}; r2 fresh reviewers: F-a, F-b
RESOLVED, new independent blockers {F-c, F-d}; validation green each round.

- v0.1 contract: cardinality 2 → 2, "set REPLACED by new independent blockers counts
  as NOT shrinking" → **stagnation on a history where every blocker was resolved.
  Wrong label; conflates churn with stagnation.**
- v0.2 required outcome: persistent = previous ∩ current = ∅ → resolved > 0 → this
  is progress; {F-c, F-d} recorded as churn. Stagnation requires PERSISTENT blockers
  with no semantic improvement AND no validation improvement. max_rounds still bounds
  endless churn.

## Release runbook (per release, both runtimes)

1. `python3 scripts/check_repo.py` and `python3 -m unittest discover -s tests` — green.
2. Build fixtures: `python3 docs/acceptance/fixtures/plant.py <dir> A B C D H J X`.
3. Run LIVE-LOOP cases (E01–E04, E06, E10) on Codex AND Claude with the installed
   plugin; run DECISION-PROCEDURE cases (E05, E07–E09) fresh on each runtime.
4. Record: reviewer spawn inputs (full materialization), verdict envelopes, validation
   command + exit code + freshness, final outcome — under `docs/acceptance/transcripts/`.
5. Compare outcomes against the matrix above; any mismatch is a release blocker.
6. Record analyzer + plugin-eval numbers (waiver carries the current baseline and
   reproduction commands).

## Analyzer baseline (point-in-time)

- 2026-09-10, tree `f33ab2ff00c806bdbae006ca4dda8ca62545d983` → 13,150:
  plugin deferred 13,150 (excessive, waived); three skills 100/100, 0 fail 0 warn.
  Current numbers live in `docs/acceptance/plugin-eval-budget-waiver.md`.
