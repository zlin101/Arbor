# Final Output Format

The user gets the final state, not the process log. Two templates, nothing else.

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

Include a `Residual non-blocking` section only when residual findings exist. Validation
lines list the commands actually run (or `none declared by project` if the project
defines no validation and none was discoverable). Always end PASS with the line
`No commit or push was performed.`

## STOPPED

```text
Dual Review Loop: STOPPED

Reason: oscillation | max rounds | no progress | permission boundary | unresolved conflict

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
