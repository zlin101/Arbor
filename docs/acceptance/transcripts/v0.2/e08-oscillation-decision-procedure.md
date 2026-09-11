# E08 — Oscillation guard — DECISION-PROCEDURE

- **Candidate**: Arbor v0.2, commit `943a02c67c082dfa7bc876585bb7dc406ee070c1`
- **Evidence class**: DECISION-PROCEDURE — frozen contract text applied to the
  scenario-E synthetic history (v0.1 transcript
  `scenario-E-oscillation-eval.md`). No subagents.
- **Frozen definition under test** (convergence-contract.md §5):

  > oscillation: the main agent's OWN fix directions for the SAME design question
  > flip between two answers across three comparable rounds (N demands X, N+1 demands
  > not-X, N+2 returns to X) → STOPPED, present both directions' trade-offs, hand
  > back to the user.

## Input history (from scenario-E)

Design question: should `parse_entry` keep the inline format checks or extract a
shared `_validate_header` helper?

- r1: both reviewers flag the duplicated inline checks as a maintainability finding
  (non-blocking classification under default profile); main agent's fix direction:
  **extract the helper** (X).
- r2: fresh reviewers flag the new helper as speculative abstraction over two
  call sites; main agent's fix direction: **inline it back** (not-X).
- r3: fresh reviewers again flag the duplicated checks; main agent returns to
  **extract** (X).

## Branch walk

1. Three comparable rounds (r1, r2, r3), same design question, main agent's own fix
   directions: X → not-X → X. The pattern matches the guard's definition exactly.
2. Gate blockers > 0 each round (the maintainability finding keeps cycling), so guard
   evaluation is reached (guards apply only when the PASS condition is not met).
3. Guard precedence: blocked → oscillation → permission boundary → unresolved
   conflict → no progress → max rounds. No blocked state, no permission issue, no
   reviewer conflict this round. No-progress counter: each round resolved the prior
   finding (real progress), so no-progress never accumulated. max_rounds (3) is
   reached in the same round as the oscillation pattern completes — **oscillation
   outranks max rounds** in the precedence order, and both point to STOP.
4. **STOPPED, reason `oscillation`**; final report presents both directions'
   trade-offs (inline: duplication risk, zero indirection; extract: single canonical
   check, one extra indirection) and hands the decision back to the user. No third
   fix applied.

## Result

| Aspect | Required | Frozen-text outcome | Match |
|---|---|---|---|
| Flip-flop detection | X → not-X → X across 3 comparable rounds fires | fires at r3 | ✅ |
| No third fix | guard overrides fix policy | "once a stop condition fires, no further fixes are applied" | ✅ |
| Report content | both trade-offs, hand back | required by guard action text | ✅ |
| Precedence vs max rounds | oscillation first | first match in precedence order | ✅ |

**E08 decision-procedure: PASS on v0.2 text.** (v0.1 behavior preserved — this is a
regression check; the v0.2 edit tightened attribution to the main agent's OWN fix
directions, which this history satisfies.)

---

## Re-run against re-freeze 2 (commit `bffa075`, subtree `8655c6a2…`)

Amendment under test: §3 inventory + incomplete-materialization stop. The oscillation
walk is a guard-precedence decision over three completed rounds with valid verdicts;
materialization supply is not a branch condition anywhere in it, and the history's
changed code has derivable one-hop consumers (the co-updated tests), so the new stop
cannot fire. Precedence order untouched by the amendment.

**E08 re-run: PASS on re-freeze 2 text. Outcome unchanged.**
