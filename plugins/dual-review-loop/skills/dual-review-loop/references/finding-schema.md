# Finding Schema, Dedupe, and Lifecycle

Reviewers are evidence producers: they observe, classify, and explain. Gate policy
(severity → blocking derivation) belongs to the orchestrator alone — reviewers do
NOT output blocking state. One schema for both reviewers; identity, merging, and
history belong to the main agent.

## 1. Reviewer output envelope

Each reviewer returns exactly this shape (YAML):

```yaml
reviewer: correctness | structure
verdict: PASS | FINDINGS
findings:
  - local_id: C1            # reviewer-local (C1… / S1…); NOT a global id
    severity: P0 | P1 | P2 | P3     # correctness reviewer
    # structure reviewer uses structural_class instead of severity:
    structural_class: regression | improvement
    category: correctness | security | reliability | performance | tests | architecture | maintainability | abstraction | complexity | types | other
    location:
      file: path/to/file
      line: optional
      symbol: optional
    causal_link: optional   # REQUIRED when location is in untouched code: name the
                            # changed code that causes or materially worsens this
    title: concise title
    problem: what is wrong
    evidence: concrete evidence from code/behavior
    impact: why it matters
    recommended_direction: smallest useful direction, not a full implementation plan
coverage: what was actually reviewed, one line
residual_risks: []          # may be empty; clean reviews must state residual risk
```

Rules:

- `verdict: PASS` with an empty findings list is a valid, expected outcome.
- There is NO `blocking` field and no `discipline: taste` value in this schema.
  Whether a finding blocks is derived by the orchestrator from the policy table in
  `convergence-contract.md` §1 — the schema cannot express illegal states like
  "P1 but non-blocking" or "taste finding". Taste-level observations go to
  `residual_risks`, never to `findings`.
- Structure findings use `structural_class: regression | improvement`; correctness
  findings use `severity: P0–P3`.
- `causal_link` is required whenever `location` is in code the change does not touch:
  name the changed code that causes or materially worsens the problem. Omit it when
  the location itself is changed code.
- Reviewers do NOT generate global ids, do not merge each other's findings, and do
  not compare notes.

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

Identity rules:

- An F-id is minted at the root cause's FIRST appearance and is never renumbered or
  reused — not across rounds, and not after a discarded round (discarded ids are
  reclaimed and skipped).
- Identity is per ROOT CAUSE for the whole session: if a resolved root cause
  re-surfaces in a later round, it REUSES its original F-id and returns to OPEN
  (it is then `persistent` for progress purposes, not `new` churn).

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

Merged finding shape (orchestrator-internal state; not reviewer output):

```yaml
id: F002
classification:                    # per source; gate derives from the MOST SEVERE row
  correctness: P1
  structure: regression
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

### Normalizing envelope violations

- Unknown/extra fields: drop silently.
- Both class fields present (severity + structural_class): keep the reviewer's OWN
  lens field, treat the other as noise.
- Out-of-enum values (e.g. `structural_class: blocking regression`): re-spawn that
  reviewer ONCE; if it repeats, treat the verdict as FINDINGS-unclassified — which is
  never gate-blocking — and note it in the final report.
- Non-YAML output: re-spawn once, then treat as PASS-with-coverage-note; never
  improvise findings from prose.

Each lens emits its own `category` subset; the union in §1 is the normalizer's
accepted set.

## 4. Lifecycle (single session, no persistent state machine)

```text
OPEN      — still reproducible / still present (a re-surfacing root cause re-enters OPEN under its original F-id)
RESOLVED  — the new round's fresh review no longer confirms it, and related validation passes — or no related validation exists or is declared
BLOCKED   — missing permission, insufficient evidence, external dependency, or needs a human decision
WAIVED    — only when the user or the project's explicit rules allow it; the agent may NEVER self-waive a blocker
```

`DUPLICATE` / `INVALID` are normalization outcomes, not lifecycle states.
`FIXED_PENDING_VERIFY` is a transient within a round, not a state.
Everything lives in the main agent's session context — the loop writes no ledger file
unless the target project's rules explicitly require one (path supplied by the project).
