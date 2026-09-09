# scenario-E-oscillation-eval

- task: afc8968426db70db2
- evidence class: DECISION-PROCEDURE (contract applied to synthetic history)
- assistant text blocks: 2
- reviewer spawns: 0 (full prompts in spawn4-full.md files)

## Spawns

(none — decision-procedure evaluation, no subagents)

## Final assistant output (verbatim)

```
I read only the two specified files. Here is the decision-procedure evaluation.

## 1. End of round 3 — what the loop does

**STOPPED, handing back to the user. No further fix.** Three guards fire concurrently:

- **Oscillation** (convergence-contract.md §4 table): "design flip-flops between two directions (e.g. round N demands an abstraction, round N+1 demands its removal, round N+2 returns to the original) → STOPPED, present both directions' trade-offs, hand back to the user." Round 1 = removal (inline), round 2 = abstraction, round 3 = removal. Exactly the flip-flop shape (mirrored relative to the contract's `e.g.`, but the governing clause is "design flip-flops between two directions," which is direction-agnostic).
- **Max rounds**: "`max_rounds` reached with blockers open → STOPPED, list open blockers." max_rounds is 3, round 3 just delivered verdicts, and F-c is an open P1, so convergence gate conditions 2 ("open P1 findings == 0") and 3 ("structural blocking findings == 0") both fail. PASS is impossible.
- **No progress** (secondary): "2 consecutive rounds: blocking set not shrinking / same root cause recurring in equivalent form." The blocking set was size 1 in rounds 1, 2, and 3, and per "Compare against the previous round's blocking set semantically (root cause, not line numbers)," F-a and F-c share one root cause in equivalent form. Rounds 2 and 3 are the two consecutive non-shrinking rounds.

Not fired: permission boundary, reviewer conflict (correctness reviewer PASSed; the conflict guard covers "reviewers disagree on material behavior/architecture" and says nothing about one reviewer contradicting its own prior round — see Q4).

## 2. Should the main agent fix F-c? No.

Four independent contract reasons:

1. **No verification budget remains.** PASS requires the gate to be met, and gate condition 3 can only be confirmed by a re-review ("review whole scope → … → re-review whole scope"). With max_rounds exhausted, a round-3 fix could never be re-reviewed, so the fix buys nothing except a fourth design inversion.
2. **The oscillation guard removes the decision from the loop**: "hand back to the user." Applying F-c is precisely the "round N+2 returns to the original" move the guard exists to terminate.
3. **Fix policy forbids it**: "Never ping-pong `fix F001 → re-review → fix F002 → re-review`; it burns review rounds and oscillates on local optima." Also, "Progress = the set of open blockers shrank" — an F-c fix would not shrink the blocking set.
4. **F-c likely fails the discipline bar and should not exist as a finding at all.** §1 defines `blocking regression` as "change made structure materially worse." F-c asserts the opposite of what round 2's reviewer asserted about the same code state; "the abstraction is unnecessary" is `taste`, and taste "must NOT be reported as a finding; at most one aggregate `residual_risks` line." Caveat: the contract assigns the `discipline:` label to the reviewer and gives the main agent no rule for reclassifying a mislabeled finding, so reason 4 is an argument, not an instruction (see Q4).

## 3. Final report per output-format.md (STOPPED template)

```text
Dual Review Loop: STOPPED

Reason: oscillation

Rounds: 3/3

Open blockers
- F-c [P1] Formatter abstraction flip-flop (inline vs. extract) — the same design
  decision has been inverted three times; a fourth fix would repeat the cycle.

What was tried
- Round 1: F-a [P1 blocking regression] — inlined the formatting and deleted the
  `Formatter` abstraction; validation passed.
- Round 2: F-b [P1 blocking regression] — re-extracted a dedicated `Formatter` to
  remove three-way duplication; validation passed.
- Round 3: F-c [P1 blocking regression] raised against the abstraction; no fix
  applied, handed back to the user.

Validation
- <project validation command>: PASS

Decision required
- Keep the dedicated `Formatter` abstraction, or inline the formatting at the three
  call sites? Direction A — extract (round 2): one owner for the formatting rules and
  no duplicated logic drifting apart, at the cost of an extra indirection layer that
  only pays off if the rules or call sites grow. Direction B — inline (rounds 1 and
  3): no abstraction to justify and nothing extra to read through, at the cost of the
  same logic maintained, and drift-prone, in three places.
```

Fidelity notes: the template's "What was tried" shows two lines as an illustration; I rendered three because three rounds occurred and the brevity rules only forbid transcripts, not round lines. The `Validation` command is a placeholder — the history says "validation passed" without naming a command, and output-format.md requires "<command>: <status>" (the `none declared by project` fallback applies only when nothing ran). No `No commit or push was performed.` line: output-format.md scopes that line to PASS ("Always end PASS with the line"), and "Two templates, nothing else" forbids appending extra lines.

## 4. Is the outcome deterministic? The STOP is; the report is not.

**Deterministic core.** Any agent that accepts F-c as an open P1 must stop, because the max-rounds row is mechanically checkable: "max_rounds reached with blockers open → STOPPED." The sentence that decides "stop rather than fix" is the oscillation row's action clause: "**STOPPED, present both directions' trade-offs, hand back to the user**" (reinforced by "Never ping-pong `fix F001 → re-review → fix F002 → re-review`… oscillates on local optima").

**Three genuine nondeterminism gaps:**

1. **No guard precedence rule.** Oscillation, max rounds, and no progress all fire at round 3, but §4's table presents them as sibling rows with no "evaluate in order / first match wins" sentence, and the STOPPED template's `Reason:` field takes exactly one value. Agent A writes `Reason: oscillation`, agent B writes `Reason: max rounds`. This is not cosmetic: the Reason selects the Decision-required content rule — "For `oscillation`, it presents both structural directions and their trade-offs" — while the contract prescribes no Decision-required content for `max rounds` or `no progress`, so the two agents' report bodies legitimately diverge.
2. **No authority to reclassify a mislabeled finding — the biggest divergence.** §1 says taste "must NOT be reported as a finding" and "If the change introduces no structural regression, PASS is the correct verdict even when further polish is imaginable." F-c is arguably taste wearing a `blocking regression` label. But the `discipline:` label is authored by the reviewer, and no sentence lets the main agent audit or downgrade it. So agent A may discount F-c as invalid, find the gate met (no accepted open P0/P1, validation passed, conflict guard inapplicable since correctness PASSed), and emit **PASS** with F-c as a residual — while agent B accepts F-c at face value and emits **STOPPED**. Same contract, opposite terminal states.
3. **Judgment-dependent detections.** "Same root cause recurring in equivalent form" and "Compare … semantically (root cause, not line numbers)" are agent judgments, as is counting "2 consecutive rounds" (a stricter counting could have demanded a stop already at end of round 2). Here all readings converge on STOPPED by round 3, so this gap does not change the terminal state — only its reason string.

Minor nits, not outcome-affecting: the oscillation example is introduced with "e.g." and is the mirror image of this history (abstraction → removal → abstraction), so a hyper-literal agent could contest the match, though the operative clause "design flip-flops between two directions" settles it; and §2's fix order ("(3) structural blockers") read alone would instruct a fix for F-c — only the guards' action clauses and the anti-ping-pong sentence override it, and the contract never states that guards trump the fix policy.

**Bottom line:** the loop state (STOPPED, no F-c fix) is deterministic; the Reason string and possibly even PASS-vs-STOPPED are not, with gap #2 (no reclassification authority for a taste finding labeled `blocking regression`) being the one that can flip the terminal state itself.

Files read: `/home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-loop/references/convergence-contract.md`, `/home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-loop/references/output-format.md`.
```
