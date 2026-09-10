# Transcript Index — dual-review-loop v0.1 acceptance runs

Extracted from raw session JSONL (streaming parse). Per scenario:
- `<scenario>.md` — identity, EVIDENCE CLASS, spawn list, final assistant output verbatim
  (reviewer verdict envelopes + evidence items + final report).
- `<scenario>-spawn<N>-full.md` — COMPLETE untruncated Agent-tool input per reviewer
  spawn: proves per-round parallel dispatch, the round-2 scope materialization
  (full change vs fix-only), and that fresh reviewers received no prior-round findings.

Evidence classes: LIVE-LOOP = fresh driver ran the full loop with real parallel reviewer
subagents on a fixture repo. DECISION-PROCEDURE = fresh agent applied the contract text
to a stated synthetic history (no subagents) — verifies the contract's decision
procedure, not model loop behavior. Classes are labeled and must not be conflated.

| Scenario | Evidence class |
|---|---|
| scenario-A-driver | LIVE-LOOP |
| scenario-B-driver-attempt1-429 | LIVE-LOOP (terminated by 429 mid-round-1) |
| scenario-B-driver-retry | LIVE-LOOP |
| scenario-C-driver | LIVE-LOOP |
| scenario-D-driver | LIVE-LOOP |
| scenario-E-oscillation-eval | DECISION-PROCEDURE (contract applied to synthetic history) |
| scenario-H-maxrounds-driver | LIVE-LOOP |
| scenario-I-noprogress-eval | DECISION-PROCEDURE (contract applied to synthetic history) |
| scenario-J-maxrounds-live | LIVE-LOOP (result: PASS 2/2 - converged within budget; max-rounds correctly NOT fired, blockers were zero at exhaustion) |
| scenario-Jdoubleprime-maxrounds-sole | DECISION-PROCEDURE (result: STOPPED max rounds as SOLE firing guard, deterministic; no-progress mathematically capped at 1 < 2) |
| scenario-Jprime-maxrounds-precedence | DECISION-PROCEDURE (result: no-progress outranks max-rounds under cardinality progress reading; contract tension documented in convergence-contract.md) |

---

# v0.2 acceptance evidence (candidate `943a02c`)

Evidence class definitions unchanged (see header above). v0.2 evidence lives in
`v0.2/` and never overwrites v0.1 files.

| File | Evidence class | Result |
|---|---|---|
| `v0.2/e05-residual-only-decision-procedure.md` | DECISION-PROCEDURE | PASS on frozen text (R1 dead-end not expressible) |
| `v0.2/e07-progress-semantics-decision-procedure.md` | DECISION-PROCEDURE | PASS on frozen text (R3 fires; R4 churn ≠ stagnation; R4b reopened → persistent) |
| `v0.2/e08-oscillation-decision-procedure.md` | DECISION-PROCEDURE | PASS on frozen text (regression check) |
| `v0.2/e09-conflict-decision-procedure.md` | DECISION-PROCEDURE | PASS on frozen text (both branches) |
| `v0.2/e06-cross-boundary-live.md` | LIVE-LOOP (pi orchestrator + Claude Code reviewers) | **FAIL — contract gap**: materialization lacks one-hop callers; untouched `report.py` regression unreported, still broken in PASSed tree. Stage-1 STOP; §3 amendment proposed |
| `v0.2/live-run-prep.md` | prep material | fixtures verified, driver prompts, evidence checklist |
| `v0.2/e06-…` / `e10-…` / `e01-…`–`e04-…` | LIVE-LOOP | **pending** — requires live driver runs (Codex + Claude) |
