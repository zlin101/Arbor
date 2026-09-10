# E09 — Reviewer conflict resolution — DECISION-PROCEDURE

- **Candidate**: Arbor v0.2, commit `943a02c67c082dfa7bc876585bb7dc406ee070c1`
- **Evidence class**: DECISION-PROCEDURE — frozen contract text applied to a stated
  synthetic conflict history. No subagents. (v0.1 exercised the green path in
  scenario-H evidence; this walk covers both branches.)
- **Frozen definitions under test** (convergence-contract.md §1 audit, §5 conflict
  guard, guard precedence).

## Synthetic history

Working-tree review of a queue class. Reviewers disagree on material behavior:

- **Correctness reviewer (P1)**: `dequeue()` on an empty queue dereferences
  `self._head.next` without an empty-check — null-pointer crash on first dequeue.
  Evidence cites the constructor (`self._head = None`) and the unchanged
  `dequeue` body.
- **Structure reviewer**: same area, claims "input is validated upstream — callers
  guard with `size() > 0`", classifies the empty-check suggestion as
  `structural_class: improvement` (defensive redundancy).

This is a material behavioral disagreement about the SAME code path: is the empty
case reachable?

## Branch walk

1. **Normalize**: both verdicts valid envelope; no illegal fields.
2. **Conflict detection**: correctness P1 (crash reachable) vs structure's evidence
   claim (crash unreachable) — a material behavioral/architectural disagreement →
   conflict identified.
3. **ONE evidence-resolution pass** (budgeted once per finding): the main agent reads
   the current tree. `dequeue()` has two internal call sites; neither guards with
   `size()`; the only external caller in scope calls `dequeue()` unconditionally on a
   possibly-empty queue. The upstream-validation claim is **unsupported by
   current-tree evidence**.
4. **Settles?** Yes. The audit rests on current-tree evidence only (never on
   consistency with a previous round's demands). Downgrade targets do not apply here:
   the BLOCK-producing P1 is **supported**, so nothing is downgraded; the structure
   `improvement` was never BLOCK-producing under the default profile, so no audit
   downgrade is needed either. Note: had the evidence supported the structure
   reviewer instead, the P1 would be downgraded P1→P2 (never upgraded), disclosed in
   the final report.
5. **Loop continues**: gate blockers = {F001 P1} → actionable → fix batch adds the
   empty-check → validation → fresh full-scope re-review.

**Alternative branch (for completeness)**: if the evidence pass could NOT settle
reachability (e.g. callers outside the review scope make it undecidable) → do not
decide by majority vote, do not silently pick a side → **STOPPED, reason
`unresolved conflict`, both positions presented** (guard precedence: after
oscillation, before no progress).

## Result

| Branch | Required | Frozen-text outcome | Match |
|---|---|---|---|
| Evidence settles | continue loop; classification stands or downgrades (never upgrades); disclose | P1 stands on current-tree evidence; loop continues | ✅ |
| Evidence does not settle | STOPPED `unresolved conflict`, both positions, no majority vote | exact guard action | ✅ |
| Single pass budget | ONE evidence-resolution pass per finding | enforced in §1/§5 text | ✅ |

**E09 decision-procedure: PASS on v0.2 text.**
