# Waiver — plugin-eval `deferred_cost_tokens` (dual-review-loop)

## v0.2 re-evaluation and disposition

Status: **WAIVED (formal, narrowed)** · Date: 2026-09-11 · Waiver owner: zlin101

Candidate: re-freeze 2, commit `bffa075`, plugin subtree
`8655c6a2afc43e88489d80aaf487ca95a7680625`. Acceptance-only commits after
`bffa075` do not change that subtree.

Final local analysis on this exact plugin subtree:

```text
plugin                       score 86/B   fail 1   deferred 16,963 excessive
dual-review-loop             score 100/A  fail 0   trigger 63 moderate   invoke 1,364 good   deferred 7,884 moderate
dual-review-correctness      score 100/A  fail 0   trigger 64 moderate   invoke 1,311 good   deferred 1,594 good
dual-review-structure        score 100/A  fail 0   trigger 54 moderate   invoke 1,484 good   deferred 1,002 good
```

The only failing/error check remains the generic plugin-level
`deferred_cost_tokens-budget-high`. This v0.2 waiver covers that check and no
other check. The increase from the v0.1 point measurement (13,150 → 16,963) is
accepted because v0.2's protocol corrections and the E06-proven one-hop
materialization rule are the product behavior being shipped; deleting enough
contract text to meet the generic 1,600-token band would remove reviewed safety
and convergence semantics rather than eliminate speculative machinery.

### Observed usage

No additional benchmark session was launched during closeout. The analyzer ingested
10 de-duplicated assistant-message usage samples extracted from the already archived
E06 Claude release session. The analyzer-ready projection is
`transcripts/v0.2/e06-claude-release-artifacts/observed-usage.jsonl`; its source is
the adjacent `claude-session-8493e95a.jsonl`:

```text
input tokens:   total 53,264   average 5,326.4   min 242   max 20,406
output tokens:  total 12,697   average 1,269.7   min 44    max 3,839
total tokens:   total 65,961   average 6,596.1   min 399   max 20,553
cached tokens:  total 294,208  average 29,420.8
```

These are real Claude Code session measurements, not per-reference attribution and
not a Codex benchmark. Consequently they demonstrate that a two-round E06 workflow
completed with observable usage, but they do not prove that every deferred file was
loaded or permit a direct static-estimate/observed-cost comparison (`estimateComparison`
was null for the generic plugin target). The owner explicitly stopped further paid
runtime expansion; this limitation is recorded instead of manufacturing precision.

Reproduction uses plugin-eval 0.1.0 `analyze` on the plugin and each skill, with
`observed-usage.jsonl` passed through `--observed-usage`. Re-run before citing the
figures against a different plugin subtree.

---

## v0.1 historical waiver

Status: **WAIVED (formal, narrowed)** · Date: 2026-09-10 · Waiver owner: zlin101
Re-evaluated for v0.2: see the current section above.

**Measurement date: 2026-09-10, tree `f33ab2ff00c806bdbae006ca4dda8ca62545d983`.**
Plugin content was identical from the measurement commit through the then-current
HEAD (verified at the time with `git diff --stat 09a8a21..HEAD -- plugins/`; re-measured
13,150). The analyzer's token estimates drift as contract text
evolves; numbers below are point-in-time for that tree, and the commands shown
reproduce them. Do not cite these numbers without re-running the commands.

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
