# Final Output Format

The final response MUST contain exactly one canonical PASS or STOPPED outcome block,
rendered from the templates below. Additional explanation may be included around the
block ONLY when:

1. the user explicitly asked for it (e.g. "tell me in detail what you changed"); or
2. it is necessary to explain a STOP decision; or
3. this contract or the convergence contract requires the disclosure (classification
   downgrades, conflict resolutions, required-statement corrections).

Never render a second outcome block, and never let extra prose contradict the block.
The user always gets the final state, not the process log.

## PASS

```text
Dual Review Loop: PASS

Rounds: <n>/<max_rounds>

Resolved
- F001 [P1] <short title>
- F002 [P2] <short title>

Residual non-blocking
- F003 [P3] <short title>

Validation
- <command>: PASS
- <command>: PASS

Review coverage
- correctness reviewer: PASS
- structural reviewer: PASS

No commit or push was performed.
```

Include a `Residual non-blocking` section only when residual findings exist. In `Review
coverage`, state each reviewer's actual final verdict: `PASS`, or `FINDINGS (residual
only)` when its round-final findings are all non-blocking and the gate is met by the
other conditions. Validation lines list the commands actually run (or `none declared by
project` if the project defines no validation and none was discoverable). Always end
PASS with the line `No commit or push was performed.`

## STOPPED

```text
Dual Review Loop: STOPPED

Reason: oscillation | max rounds | no progress | permission boundary | blocked | unresolved conflict

`blocked` covers stop conditions outside the named guards: a validation failure that
blocks confirming correctness (spec: STOP with BLOCKED), a finding needing a product
decision the repository cannot answer, or any external dependency the loop lacks. For
`blocked`, `Decision required` states the exact decision or dependency needed.

Rounds: <n>/<max_rounds>

Open blockers
- F00X [P1] <short title> — <one-line why it is stuck>

What was tried
- Round 1: <one line>
- Round 2: <one line>

Validation
- <command>: <status>

Decision required
- <one concise, concrete question or trade-off the user must decide>
```

For `unresolved conflict`, `Decision required` presents BOTH reviewers' positions and
the evidence that failed to settle them. For `oscillation`, it presents both structural
directions and their trade-offs.

## Brevity rules

- No round-by-round transcripts, no full finding dumps from earlier rounds, no ten-page
  process narrative.
- High-value findings only; P3s collapse into a count if there is more than a handful.
- If the user asked a scope question mid-loop, answer it, then resume — the report stays
  in one of the two shapes above.
- No persistent ledger is written unless the target project's rules explicitly require
  review results at a specific path supplied by that project.
