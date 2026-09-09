# scenario-I-noprogress-eval

- task: a156ef27b60d23496
- evidence class: DECISION-PROCEDURE (contract applied to synthetic history)
- assistant text blocks: 2
- reviewer spawns: 0 (full prompts in spawn1-full.md files)

## Spawns

(none — decision-procedure evaluation, no subagents)

## Final assistant output (verbatim)

```
## 1. When the no-progress guard fires: at the round-3 re-review (end of round 3)

Contract citations: guard row "no progress" — "**2 consecutive rounds: blocking set not shrinking / same root cause recurring in equivalent form / validation not improving** → STOPPED, reason `no progress`" (§4 table); progress definition — "**Progress = the set of open blockers shrank, or validation moved from failing to passing. Compare against the previous round's blocking set semantically (root cause, not line numbers).**" (§4, after the table).

Counter arithmetic (no_progress_rounds = 2):

| Round | Blocking set (semantic root cause) | Validation | No-progress? | Counter |
|---|---|---|---|---|
| 1 | {unbounded buffer} — F-a, first report | `make check` FAIL (pre-existing) | No — baseline | 0 |
| 2 | {unbounded buffer} — F-b, "same as round 1" | same failure | Yes — all three disjuncts: set did not shrink; same root cause recurring in equivalent form; validation did not move failing→passing | 1 |
| 3 | {unbounded buffer} — F-c, "unbounded buffer remains" | same failure | Yes — 2nd consecutive | **2 → fire** |

Round 1 cannot count as a no-progress round: the progress definition is a comparison "against the previous round's blocking set," and the guard's detection clause requires the root cause to be "**recurring**." Round 1 has no prior round to compare against; it establishes the baseline. Round 2 is the first comparison (set unchanged semantically: F-b explicitly says "same as round 1"), round 3 the second. Counter reaches 2 at the round-3 re-review → STOPPED, reason `no progress`, `Rounds: 3/5`. max_rounds = 5 is never reached, and even if it were, precedence (§4) puts `no progress` above `max rounds`, so the reason token is `no progress` either way.

## 2. The pre-existing lint failure is orthogonal to this STOP

Citation: §3, "If validation fails: … **Pre-existing / unrelated failure → do not expand scope; record evidence.** If it blocks confirming correctness, STOP with `BLOCKED`; otherwise report it as a residual validation risk."

- It is pre-existing and unrelated (unrelated lint failure), so the rule's default branch applies: record evidence, report as residual validation risk. Do not expand scope to fix it.
- It does not "block confirming correctness": a lint failure is not the instrument that would confirm or refute the memory-bounding behavior at issue, and the loop's correctness evidence here is the reviewers' repeated semantic finding, not that command. The history also already records it as "residual validation risk."
- Convergence-gate condition 4 ("required project validation passes") is irrelevant: we are not claiming PASS — we are stopping with an open blocker, and the STOPPED template only requires validation lines with their actual status.

## 3. No — the main agent must not apply another fix for F-c

Citation: §4 guard precedence, closing sentence — "**Guards override the fix policy: once a stop condition fires, no further fixes are applied, even ones the fix order would rank as actionable.**" F-c is P1 correctness (fix-order rank 1–2, §2), so the fix policy would rank it actionable, but the guard fired at the round-3 re-review, which terminates the fix loop; the trade-off is handed back to the user via the STOPPED report's `Decision required`.

## 4. Final report, per output-format.md STOPPED template

```text
Dual Review Loop: STOPPED

Reason: no progress

Rounds: 3/5

Open blockers
- F-c [P1] Unbounded buffering: helper loads entire input into memory before emitting — same root
  cause as F-a (R1) and F-b (R2) in equivalent form; memory is unbounded for inputs under the 1 GB
  cap and three fix attempts have not moved it.

What was tried
- Round 1: docstring warning added; buffer unchanged.
- Round 2: ValueError raised for inputs over 1 GB; buffer for smaller inputs unchanged.
- Round 3: no fix applied — no-progress guard fired at the round-3 re-review.

Validation
- make check: FAIL (pre-existing, unrelated lint failure; residual validation risk, not introduced
  by this change)

Decision required
- Authorize a redesign of the helper to stream/chunk its input (bounding memory for inputs under
  the 1 GB cap), or accept the 1 GB cap plus the documented risk as the final state?
```

Fidelity notes: the STOPPED template is used verbatim (output-format.md: "Two templates, nothing else"), so the `No commit or push was performed.` line is *not* appended — output-format.md mandates it only for PASS, even though §2's forbidden-actions rule still applies. `Decision required` is a single concrete trade-off (the `unresolved conflict`/`oscillation` variants that require presenting both positions do not apply here).

## 5. Determinism: the outcome is deterministic; the round count has one residual ambiguity

Sentences that decide it:
- Guard row, "no progress": "**2 consecutive rounds: blocking set not shrinking / same root cause recurring in equivalent form / validation not improving**". The three disjuncts are OR-ed and all three hold here, so an agent who weighs "shrinking" differently still lands on the same verdict — the redundancy makes the *outcome* (STOPPED, reason `no progress`, no further fix) deterministic.
- "**Compare against the previous round's blocking set semantically (root cause, not line numbers).**" This kills the tempting reading that F-a → F-b → F-c are three different findings because their text differs; semantically they are one root cause, so the blocking set never shrank.
- "**Guards override the fix policy: once a stop condition fires, no further fixes are applied, even ones the fix order would rank as actionable.**" This settles Q3 identically for any agent.
- "**Guard precedence** … no progress → max rounds" — settles the `Reason:` token independently of the max_rounds = 5 override.

Residual ambiguities:
1. **Whether round 1 counts toward the counter.** The contract never states explicitly that the baseline round is exempt; it is implied by "recurring" and "compare against the previous round's blocking set." An agent who counted round 1 as no-progress would stop at end of round 2 (`Rounds: 2/5`, blocker F-b) instead of round 3. Outcome type and reason are unchanged; the round count and which finding ID appears are not. This is the only materially non-deterministic point.
2. **BLOCKED vs no progress.** §3 says "If it blocks confirming correctness, STOP with `BLOCKED`", but output-format.md's STOPPED `Reason:` enum (`oscillation | max rounds | no progress | permission boundary | unresolved conflict`) contains **no BLOCKED token** — a genuine cross-file gap. It does not bite here (the failure is pre-existing/unrelated and routed to "residual validation risk"), but an agent reading "validation never passed at any round" as "correctness never machine-confirmed" could reach a different reason token. The contract's own text ("otherwise report it as a residual validation risk") resolves it toward `no progress`.
3. Cosmetic only: whether the open blocker is labeled F-c or collapsed into the recurring root cause; does not affect the verdict.
```
