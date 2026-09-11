# E06 — Cross-boundary regression (fixture X) — LIVE-LOOP **Claude release unit** — **PASS**

- **Candidate**: re-freeze 2 — commit `bffa075`, plugin subtree
  `8655c6a2afc43e88489d80aaf487ca95a7680625`
- **Evidence class**: LIVE-LOOP — **Claude Code release runtime**: plugin loaded via
  `claude --plugin-dir` into a fresh nested `claude -p` session (driver semantics
  equal to an interactive fresh session; no plugin install, no persistent config
  change). Reviewers are the PLUGIN'S OWN agents spawned through the Agent tool.
- **Model note (honesty)**: the CLI runtime is Claude Code 2.1.263; the model behind
  it was the operator's configured default (`glm-5.3-flash`, `unrecognized_model`
  warning in stderr, run completed). This unit therefore evidences **runtime +
  protocol behavior** (plugin loading, Agent-tool dispatch semantics, permission
  gating, tool allowlists), not Claude-model quality per se.
- **Permissions**: `--allowedTools "Edit" "Write" "Bash" "Task" "Agent"` (minimal
  allowlist after the permission classifier rejected `--dangerously-skip-permissions`
  — the gate held and was narrowed instead of bypassed). Reviewer agents run under
  the plugin's own frontmatter allowlist `Read, Grep, Glob` (verified:
  `subagent_type='dual-review-loop:dual-review-correctness-reviewer'` /
  `…structure-reviewer'` on all four spawns).
- **Fixture**: fresh `plant.py X`, baseline `7a1daf1`; defect pre-verified present
  (`describe(s,'missing')` → `'missing: (None, True)'`).

## Independent verification (this archive re-derived every claim from raw records)

| # | Claim | Verification method | Result |
|---|---|---|---|
| 1 | 4 spawns, both rounds **same-turn parallel** | `run-claude.jsonl`: both round-1 Agent calls in assistant message `71ebc09b4189`; both round-2 calls in `dfff20614af1` — same `message.id` = one turn | ✅ |
| 2 | Isolation template verbatim, every spawn | grep across all 4 archived spawn prompts | ✅ ×4 |
| 3 | Frozen baseline in every materialization | `7a1daf1` present ×4; R2 zero F-id leakage (no `F00` matches) | ✅ |
| 4 | One-hop inventory names the untouched caller | R1: `report.py::describe — direct caller of Store.get (untouched by the change); read it` | ✅ |
| 5 | Materialization parity per round | shared-section diff R1 exit 0; sizes differ only by lens rubric (2893/2899, 3544/3550 bytes) | ✅ |
| 6 | Cross-boundary finding with `causal_link` | R1 correctness C2 [P1] at untouched `report.py:4 describe`, causal_link → `store.py::Store.get` contract change; **structure lens independently flagged it too** | ✅ |
| 7 | Envelope cleanliness | 4/4 verdicts valid (`FINDINGS`), no `blocking` output field, no `discipline`, no invalid enum — **no retry needed** | ✅ |
| 8 | Fix batch coherence + freshness | exactly 3 Edits (get() honest found-flag; tests to `(None, False)` + new stored-None test; report.py migrated) → THEN `python3 test_store.py` exit 0 → zero writes after | ✅ |
| 9 | No narrative leakage | no F-id/reviewer/round strings in fixed code (only pre-existing `test_set_get_roundtrip` matches) | ✅ |
| 10 | Final tree behavior (re-executed now) | `'a: 1'` / `'missing: missing'` restored / stored-None `'k: None'` distinguishable via `(None, True)` vs `(None, False)` | ✅ |
| 11 | No commit/stage | git log still `7a1daf1 base store`; status = 3 modified files, nothing staged | ✅ |
| 12 | Classification audit exercised | F006 "default param redundant" R2 `regression` → one evidence pass → downgraded to `improvement` (baseline not strictly lighter), disclosed in final report — the v0.2 audit path ran in production | ✅ |

## Loop flow

| Round | Verdicts | Blockers | Action |
|---|---|---|---|
| 1 | correctness FINDINGS (C1 P0 constant found-flag; **C2 P1 untouched report.py**, causal_link; F003 P1 tests certify the bug) + structure FINDINGS (incl. same cross-boundary regression, causal_link) | 4 | ONE batch: 3 Edits → validation green |
| 2 | both FINDINGS, residual only (F004/F005 P3; F006 improvement after audit downgrade) | 0 | validation current → **PASS** (2/3) |

## Contrast with the pi diagnostic run (why this closes E06)

The pi diagnostic run failed E06 because §3 starved reviewers of one-hop code. Here,
on the release runtime: the amended materialization carried the inventory, the
plugin's tool-equipped reviewers **read `report.py` themselves**, and BOTH lenses
reported the untouched-caller regression in scope with causal links. The
deviations that marked the pi run (consecutive spawns, no-tools reviewers,
runner-injected acceptance-report) are all absent: parallelism is literal
(same message.id), reviewers are the contract's own agents, result channel is clean.

## Result

**E06 Claude release unit: PASS.** E06 is closed at the release level on this
candidate — remaining release work is breadth (E01–E05, E07–E10 release units),
not depth.

## Evidence artifacts (archived in `e06-claude-release-artifacts/`)

- `claude-session-8493e95a.jsonl` — canonical session transcript (301 KB, lossless)
- `run-claude-stream.jsonl.gz` — full stream-json (gzip, lossless; parent events =
  empty `parent_tool_use_id`, reviewer events = non-empty)
- `spawn-{0,1}-*.txt`, `spawn-round2-{0,1}-*.txt` — the 4 complete spawn prompts
- `spawn-{r1,r2}-{correctness,structure}-verdict.md` — the 4 verdict envelopes
- `fixture-initial.diff` — planted change snapshot (loop writes reproducible)
- `driver-final-output.md` — canonical PASS block, verbatim
- `observed-usage.jsonl` — 10 de-duplicated assistant-message usage samples derived
  from the canonical session for the final plugin-eval analysis
