# scenario-Jprime-maxrounds-precedence

- task: ac9536ae2d5dd5ca1
- evidence class: DECISION-PROCEDURE (result: no-progress outranks max-rounds under cardinality progress reading; contract tension documented in convergence-contract.md)
- assistant text blocks: 2
- spawns: 0

## Final assistant output (verbatim)

```
Both files read. Below is the decision-procedure evaluation, using only these two files.

Files: `/home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-loop/references/convergence-contract.md` (cited as CC line N), `/home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-loop/references/output-format.md` (cited as OF line N).

## Preliminary: the round-2 progress question

Exact sentences (CC 98–102):

> "Progress = the set of open blockers shrank, or validation moved from failing to passing. Compare against the previous round's blocking set semantically (root cause, not line numbers). Round 1 establishes the baseline and NEVER counts as a no-progress round — counting starts from the first round that can be compared against a previous one."

Round 2's blocking set is {F-a} → {F-b}: cardinality 1 → 1, validation PASS → PASS.

- **Reading A (cardinality-first; semantics governs element identity).** "Shrank" is a cardinality predicate. The second sentence tells you *how to match* blockers across rounds — by root cause, so a relabeled or renumbered same-root-cause blocker cannot masquerade as shrinkage. Matching semantically: round 1 = {root cause α}, round 2 = {root cause β}; sizes equal, so the set did not shrink. Second disjunct (validation failing → passing) is also false. **Round 2 = no progress.**
- **Reading B (semantic-burden reading).** Read "compare semantically" as qualifying the shrink predicate itself: one real root cause was genuinely eliminated and did not recur, so the loop's blocking burden decreased in substance even though a new independent defect replaced it. Under this reading round 2 "is" progress in spirit — but note that even Reading B cannot cite a sentence that says so: neither disjunct of the definition is literally satisfied; B requires importing a notion of progress ("a blocker was resolved and did not recur") that the text never states.

**The text supports Reading A.** The definition is explicit and disjunctive; the semantic clause is an anti-gaming instruction about comparison, not an additional progress disjunct. Corroboration: the no-progress detection row (CC 93) lists "blocking set not shrinking" as a standalone trigger, disjoined from "same root cause recurring in equivalent form" — if rotation-by-new-root-cause counted as progress, the first disjunct would be dead text for exactly this fact pattern. Note the tension this exposes: the definition is cardinality-based and therefore penalizes *discovery* of new independent defects, which is precisely what happens here (two independent P1s surfacing in separate rounds despite the "one coherent root-cause batch per round" policy, CC 43–48).

**Adopting Reading A, the rest follows deterministically.** I carry Reading A through Q1–Q3 and flag where Reading B would differ.

## Q1 — Guard table walk and the firing condition

**PASS row** (CC 91): Not satisfied. Gate condition 2 "open P1 findings == 0" (CC 9) fails — F-c is an open P1 at end of round 3. Conditions 4 and 5 hold, but all five are required (CC 5).

**Oscillation row** (CC 94): Cannot be established on this history. Detection is "design flip-flops between two directions (e.g. round N demands an abstraction, round N+1 demands its removal, round N+2 returns to the original)". The pattern requires (a) two opposed design directions and (b) a return to the original at round N+2. Here all three blockers are independent correctness defects in separate methods (partial application in batch op → aliasing leak in snapshot → boundary bug in history(0)); no design direction is ever demanded, removed, or revisited; the blocking-set sequence {F-a} → {F-b} → {F-c} never returns to a prior element. No flip-flop exists to detect. **Not fired.**

**Permission boundary row** (CC 95): Detection requires a fix that "requires destructive action, external write, or API/security/deployment authorization the loop does not have". Both fixes were applied and validated; the history stipulates no permission issues. **Not fired.**

**Reviewer conflict row** (CC 96): Detection is "reviewers disagree on material behavior/architecture". Reviewers agree in every round; the one-shot evidence resolution pass is never triggered, and BLOCKED is unreachable. **Not fired.**

**No progress row** (CC 93): Counter arithmetic under Reading A, with the baseline sentence (CC 100–102) applied:

| Round | Blocking set | vs. previous | Shrank? | Validation failing→passing? | Counts toward counter? | Counter after |
|---|---|---|---|---|---|---|
| 1 | {F-a} | — (baseline) | n/a | n/a (PASS from start) | No — "Round 1 … NEVER counts … counting starts from the first round that can be compared" | 0 |
| 2 | {F-b} | 1 → 1, new root cause | No | No (PASS → PASS) | Yes — first comparable round | 1 |
| 3 | {F-c} | 1 → 1, new root cause | No | No (PASS → PASS) | Yes | **2** |

Trigger is "2 consecutive rounds: blocking set not shrinking / …" — rounds 2 and 3 are consecutive and both non-shrinking, so the guard fires in round 3. (Even without the baseline carve-out, round 1 would be non-shrinking too, 0 → 1; the "NEVER" clause is what keeps the count at 2 rather than 3 — it does not change whether the guard fires.) **Fired.**

**Max rounds row** (CC 92): "`max_rounds` reached with blockers open" — max_rounds = 3, round 3's review completed with {F-c} open. **Also satisfied**, but outranked.

**Why no fix may be applied in round 3** — the exact sentence (CC 107–108):

> "Guards override the fix policy: once a stop condition fires, no further fixes are applied, even ones the fix order would rank as actionable."

F-c is a P1 and would rank second in the fix order (CC 41–42); the sentence bars it explicitly.

**Sole cause.** Two rows are satisfied in round 3 (no progress, max rounds). The precedence clause (CC 104–106) — "evaluate in this order and use the first match as the report's `Reason:` (listing any others in `What was tried` if material): oscillation → permission boundary → reviewer conflict → no progress → max rounds" — makes **`no progress` the sole `Reason:`**, with max rounds relegated to `What was tried`. So `no progress` is the sole *reported* cause by precedence, not by exclusivity; max rounds is a co-satisfied condition that the precedence rule silences. (Under Reading B, only max rounds fires and it becomes the sole cause outright — see Q3.)

## Q2 — Final report per output-format.md

Rendered per the STOPPED template (OF 39–63), with no additions from the PASS template (OF 30: "Two templates, nothing else"; the STOPPED shape has no `Resolved` or `Review coverage` section, so none appears). `Reason: no progress` gets no special `Decision required` rule (those exist only for `unresolved conflict` and `oscillation`, OF 65–67), so a single concrete question suffices (OF 62). Max rounds is listed in `What was tried` per CC 105–106.

```text
Dual Review Loop: STOPPED

Reason: no progress

Rounds: 3/3

Open blockers
- F-c [P1] boundary bug in history(0) — found by fresh reviewers in the final round;
  stop guards fired before any fix round could address it.

What was tried
- Round 1: fixed F-a [P1] partial application in batch op; validation PASS.
- Round 2: fresh reviewers confirmed F-a resolved; fixed F-b [P1] aliasing leak in
  snapshot; validation PASS.
- Round 3: fresh reviewers confirmed F-b resolved; new blocker F-c found. No progress
  over rounds 2-3 (blocking set flat at one blocker, new root cause each round) and
  max_rounds (3) reached, so no further fix was applied.

Validation
- <required project validation command>: PASS

Decision required
- Extend the loop (raise max_rounds / no_progress_rounds) so F-c can be fixed in a
  round 4, or stop here and fix F-c [P1] boundary bug in history(0) outside the loop?
```

One placeholder caveat: OF 33–34 requires validation lines to "list the commands actually run (or `none declared by project` …)". The synthetic history records "validation PASS" without naming a command, so `<required project validation command>` stands in for the actual command string a real run would emit.

## Q3 — Determinism

**Deciding sentences:**
1. CC 98 — "Progress = the set of open blockers shrank, or validation moved from failing to passing." (makes rounds 2 and 3 non-progress)
2. CC 100–102 — "Round 1 … NEVER counts as a no-progress round — counting starts from the first round that can be compared against a previous one." (counter = 2, not 3)
3. CC 93 — no-progress detection: "2 consecutive rounds: blocking set not shrinking / …" (fires in round 3)
4. CC 104–106 — guard precedence "… reviewer conflict → no progress → max rounds … use the first match as the report's `Reason:`"
5. CC 107–108 — "Guards override the fix policy: once a stop condition fires, no further fixes are applied…"
6. CC 92 — "max rounds | `max_rounds` reached with blockers open | STOPPED, list open blockers"

**Verdict.** Under Reading A (the reading the text supports), the outcome is fully deterministic: STOPPED at rounds 3/3, `Reason: no progress`, open blocker F-c, no round-3 fix, no commit/push (CC 55–57 forbidden actions were never requested).

**If round 2 is instead read as progress (Reading B):** the terminal state does not change — the loop still ends STOPPED at 3/3 with F-c open and no fix applied, because max rounds fires independently of the counter and the fix-suppression sentence applies either way. Only two things move: the no-progress counter (2 → 1, guard no longer fires) and the `Reason:` label (`no progress` → `max rounds`), which propagates to `Decision required` framing. So the round-2 ambiguity is a **label-level, not state-level** indeterminacy — except that it is exactly the kind a downstream consumer cares about, since `no progress` (a divergence signal) and `max rounds` (a budget signal) invite different user responses. Adopting Reading A removes it.
```
