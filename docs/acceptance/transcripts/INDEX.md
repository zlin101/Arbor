# Transcript Index — dual-review-loop v0.1 acceptance runs

Extracted from raw session JSONL (streaming parse). Two file kinds per scenario:
- `<scenario>.md` — driver identity, evidence class, spawn list, and the driver's
  FINAL assistant output verbatim (contains the reviewer verdict envelopes, the
  evidence items a–g, and the final user-facing report).
- `<scenario>-spawn<N>-full.md` — the COMPLETE, untruncated Agent-tool input for each
  reviewer spawn: description, subagent_type, and full prompt. These prove per-round
  dispatch (two spawns per round), what scope materialization round-2 reviewers
  received (full change vs fix-only diff), and that no prior-round findings were
  passed to fresh reviewers.

| Scenario | Evidence class | Task | Spawns |
|---|---|---|---|
| scenario-H-maxrounds-driver | LIVE-LOOP | `a09a01917592a1acb` | 2 |
| scenario-I-noprogress-eval | DECISION-PROCEDURE (contract applied to synthetic history) | `a156ef27b60d23496` | 0 |
| scenario-D-driver | LIVE-LOOP | `a3457f221c22add0a` | 5 |
| scenario-B-driver-attempt1-429 | LIVE-LOOP (terminated by 429 mid-round-1) | `a5c25448ecdbfb209` | 2 |
| scenario-A-driver | LIVE-LOOP | `ab1bedc7e5f7fa365` | 2 |
| scenario-B-driver-retry | LIVE-LOOP | `ac1eebdfd7fcd3f96` | 4 |
| scenario-C-driver | LIVE-LOOP | `ac4ab3f70c4cf84bc` | 5 |
| scenario-E-oscillation-eval | DECISION-PROCEDURE (contract applied to synthetic history) | `afc8968426db70db2` | 0 |

8 scenario records, 28 files total (including this index).

Evidence-class legend: LIVE-LOOP = fresh driver executed the full loop with real
parallel reviewer subagents on a fixture repo. DECISION-PROCEDURE = a fresh agent
applied the convergence/output contract text to a stated synthetic history without
subagents — verifies the contract's decision procedure verifiably, not model loop
behavior. Evidence classes are labeled per scenario and must not be conflated.