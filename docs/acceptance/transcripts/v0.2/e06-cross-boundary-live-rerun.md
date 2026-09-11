# E06 — Cross-boundary regression (fixture X) — LIVE-LOOP re-run — **PASS**

- **Candidate**: re-freeze 2 — commit `bffa075`, plugin subtree
  `8655c6a2afc43e88489d80aaf487ca95a7680625` (§3 one-hop interaction inventory
  amendment; contract file sha256[:16] `d39c6163e2d0eec8`)
- **Evidence class**: LIVE-LOOP (pi orchestrator + pi-native read-only reviewer
  agents, `tools: read, grep, find, ls`). Closer to release conditions than the
  prior diagnostic run: reviewers had real read tools and read inventory locations
  themselves. The Claude release unit (plugin agents under a Claude Code driver)
  remains a separate required run.
- **Fixture**: fresh `plant.py X`, baseline `67de402`; untouched `report.py` depends
  on the plain-value `get()` contract; validation `python3 test_store.py` (AGENTS.md).

## Runtime deviations vs this run's predecessor — ALL CLOSED

| Deviation (diagnostic run) | This run |
|---|---|
| Consecutive spawns | **BOTH reviewers in ONE message** every round (session events 31, 40, 66) |
| No-tools adapter | reviewers carry `read, grep, find, ls` and read inventory locations themselves |
| Runner-injected `acceptance-report` JSON in result channel | **absent** — all six outputs end at the YAML fence; result channel clean |

## What happened

| Round | Verdicts | Gate blockers | Action |
|---|---|---|---|
| 1 attempt 1 | correctness `verdict: FAIL` (**out-of-enum**); structure prefixed prose (**envelope violation**) | — | per finding-schema normalization: re-spawn each ONCE |
| 1 retry (same materialization + envelope-correction note) | both valid `FINDINGS`: C1 P0 constant-True flag; C2 P0 **report.py consumer broken — `causal_link: report.py was not migrated to the new tuple return from Store.get`**; S1 regression; S2 tests-enshrine-bug | 4 | ONE fix batch: honest membership-check `get()`, test expectations, **report.py migrated to `value, found` contract**; validation green |
| 2 | both `PASS` (residuals recorded) | 0 | validation current → **PASS** (2/3 rounds) |

## E06 core requirement — MET

- Untouched-caller regression **reported IN scope with `causal_link`** naming the
  changed code (archived: `spawn-r1-{correctness,structure}-retry-valid-output.md`).
- Fix migrated `report.py`; final-tree behavior check executed during evidence
  extraction:
  - `describe(s.set('a',1)…, 'a')` → `'a: 1'` (baseline match)
  - `describe(…, 'missing')` → `'missing: missing'` (baseline match)
  - stored-None: `'k: None'` — the new contract's stated purpose now works
- `python3 test_store.py` → OK (5 tests) after the fix; PASS only after fresh
  full-scope re-review.

## Bonus verification: envelope-violation retry rule

The run exercised finding-schema normalization involuntary: out-of-enum
`verdict: FAIL` + prose-prefixed verdict both occurred in round 1 attempt 1; the
orchestrator re-spawned each reviewer exactly once with the same materialization
(retry inputs are the round-1 materialization plus an explicit output-contract
correction — archived as `spawn-r1-*-attempt2-input.md`); both retries were valid,
so no STOP was required. The rule that exists on paper demonstrably drives correct
orchestrator behavior.

## Result

**E06 LIVE-LOOP re-run: PASS on re-freeze 2.** The materialization amendment closes
the gap; no scope shrink occurred; the incomplete-materialization stop was not
needed (inventory derivable and supplied).

## Evidence artifacts (archived in `e06r2-artifacts/`)

- 6 spawn inputs (r1 pair, r1 retry pair with correction note, r2 pair)
- 6 outputs (2 invalid attempts preserved as negative evidence, 4 valid verdicts)
- `driver-final-output.md`, `driver-session.jsonl` (complete session)
