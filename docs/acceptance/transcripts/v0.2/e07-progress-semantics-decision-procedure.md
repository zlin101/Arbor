# E07 — Progress semantics: R3 / R4 / R4b — DECISION-PROCEDURE

- **Candidate**: Arbor v0.2, commit `943a02c67c082dfa7bc876585bb7dc406ee070c1`
  (plugin subtree `b2af293a0179426c9d425befbb4ec0d8b213fbe2`)
- **Evidence class**: DECISION-PROCEDURE — frozen contract text applied to stated
  synthetic histories. No subagents, no live loop.
- **Executor note**: same-session self-review (see E05). Live re-run still required
  before release marking.
- **Frozen definitions under test** (convergence-contract.md §5, finding-schema.md §2):

  ```text
  seen_before = union of all root causes that appeared in ANY previous round
  persistent  = current ∩ seen_before
  new         = current − seen_before
  resolved    = previous − current
  ```

  Identity: F-id minted at first appearance, reused on re-surfacing; a re-surfacing
  root cause is always `persistent`, never `new`. Stagnation: every persistent
  blocker without semantic improvement AND validation not improved. Real progress:
  resolved > 0, or persistent materially improved, or validation improved → reset.

---

## R3 — Persistent stagnation fires (positive case)

History: r1 blockers {F-a}; r2 same root cause, equivalent form, original F-id kept;
r3 same again. Validation (declared, run each round): failing → failing (no
improvement).

Walk:

- r1: baseline. Counter 0 (round 1 never counts).
- r2: seen_before={F-a}; current={F-a}; persistent={F-a}; new=∅; resolved=∅.
  F-a shows no semantic improvement vs r1 form; validation not improved.
  → stagnation round → counter 1.
- r3: identical derivation → counter 2 = `no_progress_rounds` → **STOPPED,
  reason `no progress`**.

✅ Matches runbook requirement (counter 0→1→2, stagnation fires on persistent
unimproved blockers).

## R4 — Resolution progress is NOT stagnation (negative case; R4 defect)

History: r1 blockers {F-a, F-b}; r2 fresh reviewers: F-a, F-b gone (fresh full-scope
review confirms), two NEW independent root causes {F-c, F-d}; validation green every
round.

Walk (r2):

- seen_before={F-a, F-b}; current={F-c, F-d}.
- persistent = {F-c,F-d} ∩ {F-a,F-b} = ∅.
- new = {F-c, F-d} (never seen — churn).
- resolved = {F-a, F-b} − ∅ = {F-a, F-b} → **resolved > 0 → real progress → counter
  reset (stays 0)**. Churn recorded; churn alone never triggers no-progress.
- Gate blockers now = 2 (F-c, F-d open P1s) → loop continues within `max_rounds`.

v0.1 failure mode (cardinality 2→2 counted as "not shrinking" → stagnation on a
history where every blocker was resolved) is **not expressible**: the frozen set
semantics classify by root-cause identity, not blocker count.

✅ Matches runbook requirement.

## R4b — Reopened finding after one absent round is persistent, not new (new case)

History (max_rounds ≥ 4):
- r1 blockers {F-a, F-b}.
- r2 fresh review: F-a, F-b RESOLVED (confirmed by fresh full-scope review + related
  validation green), new blocker {F-c}. (This round alone = R4: progress, counter 0.)
- r3 fresh review: F-c RESOLVED; **F-a re-surfaces** — same root cause (same defect
  re-introduced on the same symbol), original F-id reused per finding-schema §2.

Walk (r3):

- seen_before = {F-a, F-b} ∪ {F-c} = {F-a, F-b, F-c}.
- current = {F-a}.
- persistent = {F-a} ∩ seen_before = **{F-a}** → classified `persistent` (reopened),
  NOT `new` churn. Lifecycle returns to OPEN under original F-id.
- new = ∅. resolved = previous({F-c}) − current = {F-c} > 0 → **real progress →
  counter reset**. The reopened F-a does not retroactively create stagnation because
  F-c was resolved in the same round.
- Stagnation comparison for F-a from here: vs its **most recent appearance** (r1
  form), per convergence-contract §5 note.
- Forward check (r4, within budget): if F-a persists unimproved and validation does
  not improve → persistent, resolved=∅ → stagnation counter 1; `max_rounds` remains
  the hard bound.

✅ Required outcome: F-a in r3 is persistent under its original F-id; the
seen_before-based formula and the identity rule now agree (the P1-3 contradiction
identified in review is closed at the text level).

## Result

| Sub-case | Required | Frozen-text outcome | Match |
|---|---|---|---|
| R3 persistent stagnation | STOPPED no progress | counter 0→1→2 → STOPPED `no progress` | ✅ |
| R4 resolution progress | progress, churn recorded | resolved>0 → reset; churn ≠ stagnation | ✅ |
| R4b reopened finding | persistent, never new | persistent via seen_before ∩; original F-id reused | ✅ |

**E07 decision-procedure: PASS on v0.2 text (all three sub-histories).**
