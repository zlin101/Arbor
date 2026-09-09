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
