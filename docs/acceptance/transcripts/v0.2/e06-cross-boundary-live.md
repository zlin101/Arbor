# E06 — Cross-boundary regression (fixture X) — DIAGNOSTIC LIVE RUN — contract gap found

- **Candidate**: Arbor v0.2, commit `943a02c67c082dfa7bc876585bb7dc406ee070c1`
  (plugin subtree `b2af293a0179426c9d425befbb4ec0d8b213fbe2`) — frozen per
  `docs/acceptance/v0.2-freeze.md`
- **Evidence class**: DIAGNOSTIC LIVE RUN — a full loop executed with real subagents
  on fixture X, under a runtime substitution with documented deviations (below).
  **This is NOT a Claude release acceptance unit.** The release unit must run the
  contract-defined reviewers (plugin agents with `Read, Grep, Glob`) under a
  Claude Code driver session.
- **Runtime mapping** (substitutes the runtime table):
  - Orchestrator: fresh pi session (`pi-subagents` extension), full toolset.
  - Reviewers: `claude-code` adapter = real Claude Code CLI in plan mode,
    **no tools** — handoff-only; the parent materializes diff + file contents into
    the prompt.

## Documented deviations (why this is diagnostic, not release evidence)

1. **Consecutive spawn, not one-message parallel dispatch.** The two round-1
   reviewers were issued in consecutive assistant messages (async children,
   supervised), not a single parallel turn. The substantive invariants held — same
   materialization per round, no cross-reviewer visibility, fresh reviewers — but the
   letter of "BOTH spawns issued in the SAME turn" was not reproduced on this runtime.
2. **No-tools reviewers.** The contract's Claude row specifies plugin agents with
   `tools: Read, Grep, Glob`. The adapter used is handoff-only; reviewers could not
   read any file beyond the materialized text (see deviation 3's evidence: "Review
   performed in no-tools mode from the parent-materialized diff and full file
   contents only").
3. **Runner-mandated `acceptance-report` JSON appended to every reviewer output.**
   All four reviewer final messages contain the YAML verdict envelope FOLLOWED by a
   fenced `acceptance-report` JSON block. The frozen schema requires the reviewer to
   return exactly the YAML envelope; trailing non-envelope content is an envelope
   deviation that `finding-schema.md` routes to ONE format retry — the orchestrator
   normalized without retry. Provenance: this block is **injected by the runner, not
   authored by the reviewer** — `pi-subagents` source
   `src/runs/shared/acceptance.ts` instructs the child: "Completion is not accepted
   from prose alone. End with a structured acceptance report." (lines ≈499, 521–527).
   It is a runner sideband contaminating the result channel; future runs must disable
   it via the runner's agent configuration or handle it as declared sideband. Until
   then, any run on this adapter carries this integrity deviation.

## What the run demonstrated (diagnostic value)

Loop mechanics were exercised end-to-end and behaved as the frozen text specifies:

| Round | Correctness | Structure | Gate blockers | Action |
|---|---|---|---|---|
| 1 | C1 **P0** found-flag hardcoded True (store.py:16); C2 **P1** tests lock in the bug | S1 **regression** constant-flag tuple contradicts own contract | 3 | ONE fix batch: membership-check `get()` + honest test expectations; validation green |
| 2 | residual only (F003 P3 atomicity) | PASS (taste-only items in residual_risks) | 0 | validation current → **PASS** |

- Isolation template verbatim in all 4 spawn prompts; frozen baseline `85a6d26` in
  every materialization (archived inputs, per-file checks in
  `e06-artifacts/spawn-*-input.md`).
- Schema: no `blocking` field anywhere; `structural_class` used; taste quarantined in
  `residual_risks`.
- Fix batch coherent (store.py + test_store.py; no finding ids embedded); two
  gate-time validation runs, each after that round's writes.
- Round 2 = fresh FULL-scope re-review (materialization re-derived baseline→current).
- Exactly one canonical PASS block.

## THE FINDING — E06's core requirement unmet (contract gap, actionable)

**The untouched-caller regression was never found. `report.py` is still broken in the
final PASSed tree:**

```text
baseline:  describe(s,'a')       -> 'a: 1'          describe(s,'missing') -> 'missing: missing'
final:     describe(s,'a')       -> '(None, False)' describe(s,'missing') -> '(None, False)'
```

No finding locates `report.py`; no `causal_link` to the changed `get()` was produced.
The closest any reviewer came was an honest residual note: "Out-of-scope consumers of
Store.get outside the two provided files could not be inspected; the return-type
change may break callers not visible in this handoff." A residual note is not the
required in-scope finding.

**Root cause — the two frozen files are incoherent for this case:**
`reviewer-prompt-contract.md` §3 materializes "diff baseline→current + changed-file
contents", while `review-scope.md` §4 puts ONE-interaction-hop callers of changed code
IN scope. The materialization starves reviewers of exactly the code the scope declares
reviewable: `report.py` (direct caller) never appears in any spawn prompt. No-tools
reviewers cannot self-serve the gap, and nothing in the materialization directs
tool-equipped reviewers to callers either — discovery would rely on undirected
initiative even on release runtimes.

## Disposition

Stage-1 STOP per plan rule. Owner approved a narrowed amendment (inventory, not full
inlining) — implemented in `reviewer-prompt-contract.md` §3:

- `target_change` additionally carries a **one-hop interaction inventory**
  (path/symbol list) as required by review-scope.md §4;
- orchestrator must derive it before spawn (search in-repo direct
  callers/callees/consumers of changed interfaces, behavior, config, schema) and give
  the SAME inventory to both reviewers;
- reviewers with read tools read per the inventory; no-tools adapters must inline the
  current contents of inventory locations;
- if sufficient one-hop context cannot be located or supplied and correctness cannot
  be judged → `STOPPED: blocked (incomplete materialization)` — never shrink scope
  into a PASS.

Re-freeze with the amended subtree; re-run decision-procedures; re-run E06. A
no-tools diagnostic run can only ever support this class; the release unit requires
the contract reviewer agents under a Claude Code driver.

## Evidence artifacts (archived losslessly in this directory)

- `spawn-r1-correctness-{input,output}.md` — C1 P0 + C2 P1 (finds the contract break)
- `spawn-r1-structure-{input,output}.md` — S1 regression
- `spawn-r2-correctness-{input,output}.md` — residual P3 only (fix confirmed)
- `spawn-r2-structure-{input,output}.md` — PASS, taste quarantined
- `driver-final-output.md` — final canonical PASS block
- `driver-session.jsonl` — complete driver session (87 events), includes the
  `subagent` toolCall records with full `task` arguments
