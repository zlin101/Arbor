# Finding Schema, Dedupe, and Lifecycle

One schema for both reviewers; identity, merging, and history belong to the main agent.

## 1. Reviewer output envelope

Each reviewer returns exactly this shape (YAML):

```yaml
reviewer: correctness | structure
verdict: PASS | FINDINGS
findings:
  - local_id: C1            # reviewer-local (C1… / S1…); NOT a global id
    severity: P0 | P1 | P2 | P3
    blocking: true | false
    category: correctness | security | reliability | performance | tests | architecture | maintainability | abstraction | complexity | types | other
    location:
      file: path/to/file
      line: optional
      symbol: optional
    title: concise title
    problem: what is wrong
    evidence: concrete evidence from code/behavior
    impact: why it matters
    recommended_direction: smallest useful direction, not a full implementation plan
    discipline: blocking regression | material improvement | taste   # structure reviewer only, mandatory
coverage: what was actually reviewed, one line
residual_risks: []          # may be empty; clean reviews must state residual risk
```

Rules:

- `verdict: PASS` with an empty findings list is a valid, expected outcome.
- Structure reviewer sets `blocking: true` only for `discipline: blocking regression`.
- Correctness reviewer sets `blocking: true` for P0/P1 (and a P2 only when it directly
  endangers the change's correctness).
- Reviewers do NOT generate global ids, do not merge each other's findings, and do not
  compare notes.

## 2. Global identity — assigned by the main agent

After normalization the main agent assigns stable ids:

```text
F001, F002, F003, …
```

Why reviewers don't: line numbers move as fixes land, two reviewers may reach the same
root cause from different angles, and cross-round identity is orchestration state the
main agent alone must own.

Never use exact line numbers as identity. Match findings across rounds semantically:
same root cause, same symbol / ownership boundary, same behavior risk.

## 3. Dedupe semantics

**Merge two findings into one ONLY when they share a root cause** — i.e. one underlying
defect or design decision produces both, and fixing one naturally eliminates the other.

Supporting indicators (evidence FOR a shared root cause, never sufficient alone):

- same or adjacent symbol, or same ownership boundary;
- same behavioral risk;
- one fix would naturally eliminate both.

A shared symbol or boundary WITHOUT a shared root cause is the classic over-merge trap:
several distinct defects routinely live in one function. Same symbol + different root
cause → separate F-ids.

Do NOT merge on: similar titles, identical line numbers, matching category strings,
symbol adjacency alone, or "the same area of code".

Merged finding shape:

```yaml
id: F002
severity: P1
blocking: true
sources:
  - correctness
  - structure
location:
  file: internal/store/update.go
  symbol: ApplyUpdate
problem: related state updates can partially apply because ownership and transaction boundary are split
evidence:
  - correctness reviewer observed partial state on second-write failure
  - structural reviewer observed transaction ownership in the wrong layer
```

Both reviewers independently hitting one root cause is a signal to treat the finding
seriously — it does NOT mechanically raise its severity.

## 4. Lifecycle (single session, no persistent state machine)

```text
OPEN      — still reproducible / still present
RESOLVED  — the new round's fresh review no longer confirms it, and related validation passes
BLOCKED   — missing permission, insufficient evidence, external dependency, or needs a human decision
WAIVED    — only when the user or the project's explicit rules allow it; the agent may NEVER self-waive a blocker
```

`DUPLICATE` / `INVALID` are normalization outcomes, not lifecycle states.
`FIXED_PENDING_VERIFY` is a transient within a round, not a state.
Everything lives in the main agent's session context — the loop writes no ledger file
unless the target project's rules explicitly require one (path supplied by the project).
