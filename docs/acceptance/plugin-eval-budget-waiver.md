# Waiver — plugin-eval `deferred_cost_tokens` (dual-review-loop v0.1)

Status: **WAIVED (formal)** · Date: 2026-09-09 · Waiver owner: zlin101
Re-evaluate: v0.2, with observed-usage data attached (`plugin-eval benchmark`).

## Finding

```
$ node ~/.codex/.tmp/plugins/plugins/plugin-eval/scripts/plugin-eval.js \
    analyze plugins/dual-review-loop --format markdown

Score: 86/100  Grade: B  Risk: high
Checks: 1 fail, 0 warn, 4 info
deferred_cost_tokens: 13078 (excessive)   [re-run after final edits: 13078]
Fix First: "deferred_cost_tokens is excessive relative to the current Codex baseline.
Reduce repeated instruction text and move detail into deferred supporting files."
```

Analyzer band thresholds (from its own `src/core/baseline.js`): deferred bands are
good ≤320 / moderate ≤900 / heavy ≤1600 (directory profile) / excessive >1600.

## Why waived, not fixed

1. **The fail bucket is the product.** The 13,078 deferred tokens are the loop's
   contract documents: 5 convergence-loop references (scope freeze, reviewer isolation,
   finding schema, convergence gate, output format), 3 reviewer checklists, 3 SKILL.md
   bodies, and 2 reviewer agent definitions — 12+ components of 500–1,400 tokens each,
   with no dominant bloated file. Reaching ≤1,600 would require deleting ~88% of the
   contracts that implement spec §8–§21.

2. **The always-loaded cost — what the budget exists to protect — is zero.**
   `trigger_cost_tokens = 0`, `invoke_cost_tokens = 0` (both "good"). Nothing enters
   context until a skill is invoked, and the heavy references load only on demand
   (progressive disclosure, per spec §26 Phase 3). The analyzer's own recommended fix —
   "move detail into deferred supporting files" — is already fully applied; the residual
   complaint is that the SUM of on-demand files exceeds a population baseline calibrated
   for typical single-purpose skills (median 240).

3. **Per-invocation cost is bounded by design.** A single loop round loads the
   orchestrator SKILL.md plus at most the references it needs (scope + isolation +
   schema + convergence ≈ 2.5k tokens) and each reviewer loads only its own skill —
   not the full 13k. The budget tool measures static totals; it cannot express
   per-round load profiles (its own `Fix First` text concedes conclusions are static:
   "No observed usage supplied yet, so budget conclusions are still based on static
   estimates").

4. **Acceptance behavior does not degrade with size.** Scenarios A–I (see
   `dual-review-loop-v0.1.md`) passed with these contracts as-is, including the
   fresh-context, isolation, and full-scope re-review properties the contracts define.

## Conditions of this waiver

- Re-measure in v0.2 with observed usage (`plugin-eval benchmark`); if real rounds show
  reference files loading that rounds do not need, split or trim then, guided by data.
- Any future content ADDED to references must justify its tokens against a scenario;
  do not grow deferred content speculatively.
- This waiver covers only the `deferred_cost_tokens` static finding. Any future
  fail/error check of a different kind requires its own disposition.
