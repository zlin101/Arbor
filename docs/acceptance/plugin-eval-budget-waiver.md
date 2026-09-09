# Waiver — plugin-eval `deferred_cost_tokens` (dual-review-loop v0.1)

Status: **WAIVED (formal, narrowed)** · Date: 2026-09-10 · Waiver owner: zlin101
Re-evaluate: v0.2, with observed-usage data attached (`plugin-eval benchmark`).

## Scope of this waiver

Covers exactly one remaining check: the **plugin-level** `deferred_cost_tokens`
budget band. Everything else is green — after the 2026-09-10 fixes, all three skills
analyze clean individually:

```
$ node ~/.codex/.tmp/plugins/plugins/plugin-eval/scripts/plugin-eval.js \
    analyze plugins/dual-review-loop/skills/<skill> --format markdown

dual-review-loop          Score: 100/100  Checks: 0 fail, 0 warn  (trigger 63 moderate, invoke 1239 good, deferred 4892 moderate)
dual-review-correctness   Score: 100/100  Checks: 0 fail, 0 warn  (trigger 64 moderate, invoke 1186 good, deferred 1594 good)
dual-review-structure     Score: 100/100  Checks: 0 fail, 0 warn  (trigger 72 moderate, invoke 1313 good, deferred  992 good)
```

(History: the 2026-09-09 review correctly flagged that a plugin-level run alone is a
generic analysis and understates skill-level costs — per-skill runs showed
`trigger_cost_tokens` fails and `trigger-description` warnings. The warnings were fixed
by rewriting all three descriptions with explicit "Use when …" trigger sentences
tightened to 63–72 tokens, inside the empirical moderate band (≤73); the trigger fails
cleared as a result. Only the plugin-level deferred finding remains, and only that is
waived.)

## The remaining finding

```
$ node ~/.codex/.tmp/plugins/plugins/plugin-eval/scripts/plugin-eval.js \
    analyze plugins/dual-review-loop --format markdown

Score: 86/100  Grade: B
Checks: 1 fail, 0 warn, 4 info
deferred_cost_tokens: 13091 (excessive)
```

(13,091 after the description tightening; 13,203 before; band source: population
baseline, excessive > ~2,200.)

## Why waived, not fixed

1. **The failing bucket is the product.** The deferred bucket is the loop's contract
   documentation — the 5 convergence-loop references (scope freeze, reviewer isolation,
   finding schema, convergence gate, output format; spec §8–§21), 3 reviewer checklists,
   and per-skill reference files, spread evenly across 12+ components of 500–1,400
   tokens with no dominant bloated file. Reaching the band would require deleting
   roughly 85% of the contracts that implement the spec.

2. **Nothing loads until it is needed.** Per-skill numbers show the always/often-loaded
   surfaces (trigger + invoke) are all "good" bands; the loop skill's own references
   are "moderate". The heavy content is deferred by design — progressive disclosure per
   spec §26 Phase 3 — and a single round loads only the contracts that round needs, not
   the 13k total. The analyzer's own caveat applies to this check: "No observed usage
   is attached yet, so budget conclusions are still based on static estimates."

3. **Acceptance behavior is unaffected by the size.** Scenarios A–I (see
   `dual-review-loop-v0.1.md`) passed with these contracts, including fresh-context,
   isolation, full-scope re-review, and all stop guards.

## Conditions of this waiver

- Re-measure in v0.2 with observed usage (`plugin-eval benchmark`); if real rounds load
  references a round does not need, split or trim then, guided by data.
- Any content ADDED to reference files must justify its tokens against a scenario; do
  not grow deferred content speculatively.
- This waiver covers only the plugin-level `deferred_cost_tokens` band. Any new or
  different fail/error requires its own disposition.
