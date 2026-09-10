# E06 — Cross-boundary regression (fixture X) — LIVE-LOOP — **FAIL (contract gap found)**

- **Candidate**: Arbor v0.2, commit `943a02c67c082dfa7bc876585bb7dc406ee070c1`
  (plugin subtree `b2af293a0179426c9d425befbb4ec0d8b213fbe2`) — frozen per
  `docs/acceptance/v0.2-freeze.md`
- **Evidence class**: LIVE-LOOP — a fresh driver session executed the full loop with
  real parallel reviewer subagents on fixture X.
- **Runtime mapping** (substitutes the runtime table; disclosed):
  - Orchestrator: fresh pi session (`pi-subagents` extension), full toolset.
  - Reviewers: `claude-code` adapter = real Claude Code CLI, **plan mode, no tools**
    (handoff-only): the parent materializes diff + file contents into the prompt; the
    reviewer cannot read additional files.
  - Deviation vs contract letter: reviewers were spawned in consecutive messages
    (async + supervised), not literally one message; both lenses per round ran on the
    same materialization and never saw each other's verdicts, so the isolation
    invariants hold.
- **Fixture**: `plant.py /tmp/e06-live X`, baseline `85a6d26`, working-tree change =
  `get()` returns `(value, found)` tuple (store.py + test_store.py updated);
  untouched `report.py` depends on the plain-value contract.
  Validation: `python3 test_store.py` (AGENTS.md).

## What the loop did (all mechanics contract-conformant)

| Round | Correctness | Structure | Gate blockers | Action |
|---|---|---|---|---|
| 1 | C1 **P0** found-flag hardcoded True (store.py:16); C2 **P1** tests lock in the bug | S1 **regression** constant-flag tuple contradicts own contract | 3 (P0+P1+regression) | ONE fix batch: membership-check `get()` + honest test expectations; validation green |
| 2 | PASS with F003 **P3** atomicity residual | PASS (taste-only items in residual_risks) | 0 | validation current → **PASS** |

Contract mechanics verified working end-to-end:

- Reviewer isolation template verbatim in all 4 spawn prompts (parent session JSONL,
  `subagent` toolCall `task` args, e.g. call `382ee7d`: baseline `85a6d26`,
  materialization, AGENTS.md, lens rubric, no prior findings).
- Schema conformant: no `blocking` field anywhere; `structural_class` used; taste
  quarantined in `residual_risks` (round-2 structure PASS names NamedTuple polish as
  "taste-only, non-blocking").
- Fix batch coherent (store.py + test_store.py, no finding-ids embedded); two gate-time
  validation runs (one per round), each after that round's writes.
- Progress: F001/F002 resolved confirmed by fresh full-scope re-review; churn none;
  PASS at round 2/3.
- Report: exactly one canonical PASS block.

## THE FAILURE — E06's core requirement not met

**The untouched-caller regression was never found. `report.py` is still broken in the
final PASSed tree:**

```text
baseline:  describe(s,'a')       -> 'a: 1'          describe(s,'missing') -> 'missing: missing'
final:     describe(s,'a')       -> '(None, False)' describe(s,'missing') -> '(None, False)'
```

No finding locates `report.py`; no `causal_link` to the changed `get()` was produced.
The closest the reviewers came was an honest residual note (round-1 correctness):
"Out-of-scope consumers of Store.get outside the two provided files could not be
inspected; the return-type change may break callers not visible in this handoff."
A residual note is not the required in-scope finding.

## Root cause (two cooperating defects, one in the frozen text)

1. **Materialization gap (contract bug — the actionable one).**
   `reviewer-prompt-contract.md` §3 defines `target_change` as "diff baseline→current
   + changed-file contents". But `review-scope.md` §4 puts ONE-interaction-hop callers
   of changed code IN scope. The materialization therefore starves reviewers of
   exactly the code the scope declares reviewable: `report.py` (direct caller) never
   appears in any spawn prompt. The two frozen files are incoherent for the E06 case.
2. **No-tools reviewers cannot self-serve the gap.** The isolation template says
   "Read applicable AGENTS.md and relevant surrounding code as needed" — impossible
   for handoff-only reviewers. On release runtimes (Codex; Claude plugin agents with
   Read/Grep/Glob) reviewers *could* read surrounding code, but nothing in the
   materialization directs them to callers, so discovery depends on un-directed
   reviewer initiative. The run shows the failure mode concretely.

## Disposition — stage-1 STOP per plan rule

Plan rule: "any mismatch → contract bug → STOP stage 1, fix text, re-freeze, re-run."
Proposed minimal amendment (no new objects/files — pure §3 text):

```yaml
  target_change:
    full_current_materialization: <diff baseline→current + changed-file contents
      + current contents of code ONE interaction hop from changed code
      (direct callers/callees within the review scope), as required by
      review-scope.md §4 — reviewers must be able to see the code their
      causal_link may point at>
```

Upon owner approval: amend §3, re-freeze (new subtree hash), re-run the four
decision-procedures against the amended text (cheap; gate/progress/guard logic
untouched) and re-run E06 live. E10 live runs start only after E06 passes.

## Evidence artifacts (raw, retained)

- Driver session JSONL: `/tmp/e06-session/2026-09-10T15-12-13-384Z_*.jsonl`
  (87 events; subagent `task` args contain complete spawn prompts)
- Per-spawn artifacts: `/tmp/e06-session/subagent-artifacts/`
  - Round 1: `c637396d…` (correctness, C1 P0 + C2 P1), `868238ff…` (structure, S1 regression)
  - Round 2: `187b110d…` (correctness, P3 residual), `05c5b564…` (structure, PASS)
- Final tree state reproduced above; `report.py` untouched (`git status` empty) and
  still misbehaving at close.
