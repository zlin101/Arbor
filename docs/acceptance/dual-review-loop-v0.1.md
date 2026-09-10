# dual-review-loop v0.1 — Acceptance Evidence (2026-09-09)

Raw run records: **`docs/acceptance/transcripts/`** (INDEX.md + per-driver final
outputs with verbatim reviewer verdict envelopes + per-round spawn dispatch evidence,
extracted from session JSONL). Summary below; waiver for the plugin-eval budget
finding: `plugin-eval-budget-waiver.md`.

**Fixture reproduction**: the /tmp fixtures are ephemeral; `fixtures/plant.py`
rebuilds any scenario's exact at-plant-time starting state (content-verified against
the 2026-09-09/10 session records: `python3 docs/acceptance/fixtures/plant.py
/tmp/repro A B C D E J` — each scenario builds a fresh git repo, applies the planted
working-tree change, and its `python3 test_store.py` exits 0). After a scenario's loop
run, `git diff HEAD` shows exactly what the reviewers saw.

Environment: codex-cli 0.153.4 (local), Claude Code (local), fixture repo
`/tmp/arbor-acceptance/fixture*` (base commit 28c4eb4, `store.py` + `test_store.py`
+ `AGENTS.md` declaring `python3 test_store.py` as required validation).
Loop drivers were fresh-context agents; reviewers were fresh parallel subagents per
`reviewer-prompt-contract.md`. Plugin skills read from the repo working tree.

## Scenario results

| Scenario | Result | Key evidence |
|---|---|---|
| A — clean change | **PASS 1/2** | Both reviewers PASS round 1; validation `python3 test_store.py` exit 0; zero modifications (`git status` identical before/after, diff byte-identical); no commit; structure reviewer withheld a taste item as "Taste only, not a finding". |
| B — correctness bug | **PASS 2/3** | Round 1: planted partial-application bug flagged P1 blocking (correctness) + path duplication P2 `material improvement` (structure); cross-lens merge F002 (C2+S1). Fix: validate-all-then-apply delegating to `set()`. Validation exit 0. Round 2 NEW reviewers on explicitly FULL scope materialization (full diff quoted in transcript): structure PASS, correctness only residual P2/P3 → gate met. No commits; reviewer writes ruled out via file md5 + `__pycache__` mtime windows. |
| C — structural regression | **PASS 2/3** | Round 1: correctness P1 (inverted sys: guard, verified empirically) + structure P1 `discipline: blocking regression` (policy smeared across 3 accessors). Dedupe merged cross-lens halves (F001, F002). One batch fix (`SYS_PREFIX` + `_is_sys` predicate, guards made unconditional). Round 2 full scope: structure PASS with taste confined to residual_risks; correctness only new P3 → residual. No commits. |
| D — duplicate root cause | **PASS 2/3** | 6 raw findings → 5 round-1 F-ids; planted pop-before-validate bug merged into ONE F001 `sources: [correctness, structure]`, fixed ONCE. Explicit no-merge-on-symbol discipline (3 same-symbol findings kept separate by root cause). Round 2: R2-C3 semantically mapped onto existing F003 (no duplicate id). 7 F-ids / 7 root causes total. |
| E — oscillation guard | **STOP deterministic; contract hardened** | Synthetic 3-round flip-flop (inline→abstract→inline): STOPPED with both trade-offs, no third fix — deterministic. Exposed 2 contract gaps: (1) co-firing guards had no precedence rule for `Reason:`; (2) mislabeled taste-as-`blocking-regression` could not be reclassified (PASS/STOPPED flip risk). FIXED in convergence-contract.md (guard precedence order + label audit with downgrade-only authority). Committed 908f289. |
| H — max rounds (live) | **STOPPED 1/1** | Live loop, user override `max_rounds: 1`, planted `ttl` accepted-but-ignored contract bug under AGENTS.md rules forbidding policy invention. Round 1: both reviewers block (correctness P1 + structure `blocking regression`); label audit run and SUPPORTED; fake-convergence "fix" (delete the docstring claim) explicitly rejected as not root-cause; blocker is BLOCKED (needs human decision). Budget exhausted with open blocker → STOPPED. Guard precedence applied live: co-firing `permission boundary` + `max rounds` → Reason = `permission boundary`, max rounds recorded. Baseline frozen, zero writes, validation from AGENTS.md. |
| I — no-progress (decision procedure) | **STOPPED no progress 3/5** | 4-round synthetic history, same root cause recurring in equivalent form with zero validation improvement: counter arithmetic shown round-by-round (round 1 = baseline, exempt; rounds 2–3 = two consecutive non-shrinking rounds → counter 2 → fire), guards-override-fix-policy honored (no round-3 fix), pre-existing lint failure correctly routed to residual validation risk. Exposed 2 more contract gaps, both FIXED (4c2e2e0): `blocked` was missing from output-format.md's `Reason:` enum; round-1 counter exemption now explicit. |
| J — max-rounds, live | **PASS 2/2** (honest outcome) | Live loop, binding `max_rounds: 2`, three planted independent P1s. Round-1 reviewers empirically reproduced and reported ALL three; one batch fixed all; round 2 confirmed with only new non-blocking residuals → gate met. Equally important negative evidence: at budget exhaustion with ZERO blockers open, the max-rounds row correctly did NOT fire ("blockers open" predicate enforced) — no false stop. Demonstrates the guard's predicate precision live. |
| J′ — max-rounds precedence (decision procedure) | **STOPPED no progress 3/3** (by precedence) | Blocker-rotation history {A}→{B}→{C}: under the contract's cardinality progress definition, replaced-by-new-blockers rounds count as non-shrinking → no-progress fires at round 3 and OUTRANKS max rounds (precedence row "no progress → max rounds" exercised). Exposed the cardinality-definition tension (discovery of new independent defects reads as no-progress); now documented as deliberate in convergence-contract.md (stop signal for non-converging changes). |
| J″ — max-rounds sole cause (decision procedure) | **STOPPED max rounds 3/3** | Shrinking-then-stuck history {A,B,C} → {C} → {C}: counter capped at 1 < 2 (round-1 exemption + round-2 progress), so no-progress mathematically cannot fire; oscillation/permission/conflict all negative; **max rounds is the SOLE satisfied guard** and determines the terminal state. Deterministic; a deviant per-finding counter reading changes only the Reason label, never the outcome. |
| F — project gate | **PASS** (A/B/C/D/H runs) | Every run took the validation command verbatim from fixture `AGENTS.md` (`python3 test_store.py`); no plugin-default test command appeared anywhere in any loop transcript. |
| G — reviewer isolation | **PASS** (A/C/D runs) | Reviewers: no file writes (git status/diff identical across review rounds; D additionally verified via tracked-file mtimes and bytecode timestamps), no nested subagent spawns, no user questions, findings returned to parent only. F1/F2 integrity defenses never triggered. |

## Scenario B run record (final)

- Planted: `batch_set` partial application (raises mid-list after earlier pairs applied)
  + happy-path-only test.
- Attempt 1 (structure verdict on record before a 429 rate limit killed the driver):
  S1 [P2, `discipline: material improvement`] "batch_set reimplements the canonical
  write path", partial-application defect correctly handed to the correctness lens via
  residual_risks.
- Attempt 2 (fresh driver, complete): round-1 correctness C1 [P1, blocking] "applies
  pairs before validating them → partial writes + phantom audit entries"; dedupe merged
  C2+S1 into F002 (same root cause: duplicated write path / split None invariant); one
  batch fix (materialize → validate-all → delegate to `set()`); `python3 test_store.py`
  exit 0; round 2 with two NEW reviewers on full-scope materialization → structure
  PASS, correctness residuals only (F004 docstring over-claim P2, F005 dict-as-pairs
  P3) → PASS 2/3. 5 F-ids / 5 root causes; no commits; no reviewer writes.
- Bonus defect found by B: `output-format.md` hardcoded "correctness reviewer: PASS" —
  fixed to allow `FINDINGS (residual only)` when the gate is met by other conditions.

## Verdict against spec §27 acceptance checklist

- Packaging: root portable `plugin.json` (Agent Plugins spec v1.0.0) ✔ · marketplace
  resolvable ✔ (both formats) · plugin installable ✔ (verified on both CLIs) · 3 skills
  discoverable ✔ (verified in live sessions on both runtimes) · `agents/openai.yaml`
  matches skill content ✔ · no unsupported upstream metadata ✔ (`disable-model-invocation`
  etc. absent).
- Architecture: reviewers = fresh subagents ✔ · same-round parallel ✔ · read-only ✔
  (prompt contract verified; Claude runtime additionally enforces via `tools:
  Read, Grep, Glob` agent defs) · no goal-following ✔ · no nested spawns ✔ · single
  writer ✔.
- Scope: baseline frozen at loop start ✔ (28c4eb4 held across rounds in all runs) ·
  full-scope re-review each round ✔ (C/D drivers explicitly confirmed full-diff
  materialization, not fix-only) · loop-generated fixes joined next round's scope ✔ ·
  no fix-diff narrowing ✔.
- Findings: unified schema ✔ (all envelopes schema-conformant) · orchestrator dedupe ✔
  · same root cause fixed once ✔ (D) · cross-round semantic mapping ✔ (D: R2-C3→F003) ·
  no line-number identity ✔ · dedupe contract hardened post-review: shared root cause is
  the ONLY merge condition; symbol/boundary/risk are supporting indicators, never
  sufficient alone (9359f7b) ✔.
- Convergence: P0/P1 = 0 + structural blocking = 0 + validation green + fresh reviewer
  confirmation → PASS ✔ · max_rounds enforced ✔ (H: binding 1-round override honored,
  precedence applied; J″: max-rounds proven as SOLE firing guard with deterministic
  terminal state; J: predicate precision live — budget exhaustion with zero blockers
  does NOT fire the row; J′: precedence "no progress → max rounds" exercised) ·
  no-progress guard verified ✔ (I live-arithmetic: fires after 2 consecutive
  non-shrinking rounds, round-1 exemption explicit; J′/J″ counter walks) ·
  oscillation guard verified ✔ (E). Evidence classes (LIVE-LOOP vs DECISION-PROCEDURE)
  are labeled per scenario in the table above and in `transcripts/INDEX.md`; live and
  decision-procedure evidence are not conflated.
- Portability: no Iris paths ✔ · no fixed branch names ✔ · no fixed language/test
  commands ✔ · follows target AGENTS.md ✔ (F) · no default ledger ✔ · no commit/push ✔
  (git state identical after every run).
- Legal: upstream licenses re-verified 2026-09-09 (both MIT) ✔ · THIRD_PARTY_NOTICES.md
  with exact copyright lines (`Copyright (c) 2025 sanyuan0704`,
  `Copyright (c) 2026 Cursor`) ✔ · adaptation (not verbatim copy) documented ✔ ·
  no false originality claims ✔.

## Known limitations / residual risks

1. `plugin-eval` findings, final state: **all three skills analyze 100/100 (0 fail,
   0 warn)** after the 2026-09-10 description fixes (explicit "Use when …" triggers,
   63–72 tokens, inside the moderate band); the ONLY remaining finding is the
   plugin-level `deferred_cost_tokens` band (~13k vs population baseline) —
   **formally waived** — `plugin-eval-budget-waiver.md` (the deferred bucket IS the
   spec §8–§21 contract documentation, 12+ even components; per-round load is bounded
   by progressive disclosure; all trigger/invoke surfaces are in "good" bands).
   Re-measure with observed usage in v0.2.
2. Isolation on Codex is prompt-contract only (agent TOMLs are user config, not
   installable by plugins); Claude Code runtime-enforces via tool allowlists. Scenario G
   passed under prompt-contract conditions.
3. Oscillation/no-progress detection is judgment-based (semantic comparison); STOP
   outcomes are deterministic (E/I), and round-1 counter exemption plus guard
   precedence are now explicit contract text.
4. Acceptance runs used fresh subagents reading the skills from the repo (prompt-contract
   isolation), not the installed plugin agent types; the Claude plugin agents
   (`tools: Read, Grep, Glob`) were separately verified for discovery, and their
   read-only toolset is runtime-enforced.
5. One infrastructure event: a 429 rate limit killed the first Scenario B driver
   mid-round; B was re-run fresh and passed. No results were fabricated from the
   failed run.
6. Contract defects found BY acceptance (all fixed in-repo): guard precedence +
   blocking-label audit (908f289), output-format coverage line (f13a468), dedupe
   root-cause-only merge (9359f7b), `blocked` Reason token + round-1 counter exemption
   (4c2e2e0). This is the acceptance process working as intended; none remain open.
