# Waiver — plugin-eval `deferred_cost_tokens` (dual-review-loop v0.1)

Status: **WAIVED (formal, narrowed)** · Date: 2026-09-10 · Waiver owner: zlin101
Re-evaluate: v0.2, with observed-usage data attached (`plugin-eval benchmark`).

**Measurement date: 2026-09-10 at HEAD (16 commits).** The analyzer's token estimates
drift as contract text evolves; numbers below are point-in-time for this commit, and
the commands shown reproduce them. Do not cite these numbers without re-running the
commands.

## Scope of this waiver

Covers exactly one remaining check: the **plugin-level** `deferred_cost_tokens`
budget band. Everything else is green — all three skills analyze clean individually:

```
$ node ~/.codex/.tmp/plugins/plugins/plugin-eval/scripts/plugin-eval.js \
    analyze plugins/dual-review-loop/skills/<skill> --format json

dual-review-loop          trigger 63 (moderate)  invoke 1226 (good)  deferred 4951 (moderate)
dual-review-correctness   trigger 64 (moderate)  invoke 1170 (good)  deferred 1594 (good)
dual-review-structure     trigger 72 (moderate)  invoke 1296 (good)  deferred  992 (good)

all three: Score 100/100, Checks 0 fail / 0 warn
```

Trigger is **moderate, not good** (63–72, inside the empirical moderate band ≤73;
the budget fail fires only at heavy/excessive). Invoke surfaces are good. The loop
skill's deferred is moderate because it carries the five contract references.

(History: the 2026-09-09 review correctly flagged that a plugin-level run alone is a
generic analysis and understates skill-level costs — per-skill runs showed
`trigger_cost_tokens` fails and `trigger-description` warnings. The warnings were fixed
by rewriting all three descriptions with explicit "Use when …" trigger sentences
tightened into the moderate band; the trigger fails cleared as a result. Only the
plugin-level deferred finding remains, and only that is waived.)

## The remaining finding

```
$ node ~/.codex/.tmp/plugins/plugins/plugin-eval/scripts/plugin-eval.js \
    analyze plugins/dual-review-loop --format json

deferred_cost_tokens = 13150 (excessive)     # 2026-09-10, HEAD
Score: 86/100  Checks: 1 fail, 0 warn, 4 info
```

(Drift log: 13,203 pre-tightening → 13,091 → 13,150 after later contract-text
additions. Band source: population baseline, excessive > ~2,200.)

## Why waived, not fixed

1. **The failing bucket is the product.** The deferred bucket is the loop's contract
   documentation — the 5 convergence-loop references (scope freeze, reviewer isolation,
   finding schema, convergence gate, output format; spec §8–§21), 3 reviewer checklists,
   and per-skill reference files, spread evenly across 12+ components of 500–1,400
   tokens with no dominant bloated file. Reaching the band would require deleting
   roughly 85% of the contracts that implement the spec.

2. **Everything actually loaded at runtime is in-band.** Trigger (moderate, 63–72) and
   invoke (good, 1170–1296) — the surfaces a session pays for on invocation — are all
   inside their bands at every skill. The heavy content is deferred by design
   (progressive disclosure per spec §26 Phase 3): a single round loads only the
   contracts that round needs, not the 13k total. The analyzer's own caveat applies to
   this check: "No observed usage is attached yet, so budget conclusions are still
   based on static estimates."

3. **Acceptance behavior is unaffected by the size.** Scenarios A–J (see
   `dual-review-loop-v0.1.md`) passed with these contracts, including fresh-context,
   isolation, full-scope re-review, and all stop guards.

## Conditions of this waiver

- Re-measure in v0.2 with observed usage (`plugin-eval benchmark`); if real rounds load
  references a round does not need, split or trim then, guided by data.
- Any content ADDED to reference files must justify its tokens against a scenario; do
  not grow deferred content speculatively.
- This waiver covers only the plugin-level `deferred_cost_tokens` band. Any new or
  different fail/error requires its own disposition.
