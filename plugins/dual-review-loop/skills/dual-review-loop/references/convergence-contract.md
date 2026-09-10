# Convergence, Fix Policy, and Stop Guards

When the loop may claim success, what it may fix, when it must stop.

The orchestrator is the policy owner. Reviewers classify; this contract derives what
blocks, orders the work, and defines validation, progress, and every stop condition.

## 1. Gate policy — derived by the orchestrator, not declared by reviewers

Reviewers output classification only (correctness `severity: P0–P3`; structure
`structural_class: regression | improvement`). The orchestrator derives each finding's
gate effect from this fixed table:

| Reviewer classification | Default profile | Strict profile |
|---|---|---|
| correctness P0 / P1 | **BLOCK** | BLOCK |
| correctness P2 | RESIDUAL | **BLOCK** |
| correctness P3 | RESIDUAL | RESIDUAL |
| structure `regression` | **BLOCK** | BLOCK |
| structure `improvement` | RESIDUAL | **BLOCK** |

- Strict profile applies only when the user explicitly asked for a zero-findings-grade
  bar (`strict`, `zero findings`, `fix everything reasonable`, or an equivalent
  meaning). If the request is unclear, use the default profile and state that choice
  in the final report.
- **P2 default posture**: fix when direct, low-risk, and clearly inside the current
  change; otherwise record as residual.
- **P3**: never auto-fixed, never blocks PASS on either profile.
- **Taste is not a finding.** The schema cannot express it; taste-level observations
  belong in `residual_risks`. If the change introduces no structural regression, PASS
  is the correct verdict even when further polish is imaginable.

**Classification audit (main agent).** A classification counts as its evidence states.
The audit applies to EVERY BLOCK-producing classification: correctness P0/P1, structure
`regression`, and — under the strict profile — correctness P2 and structure
`improvement`. A blocking classification must cite CURRENT-tree evidence naming the
concrete problem this change introduced or materially worsened; the audit must rest on
that evidence only — never on consistency with a previous round's demands (that
comparison belongs to the oscillation guard). Downgrade targets: P0→P1→P2 and
`regression`→`improvement`; under strict, an `improvement` whose payoff is below the
finding bar is downgraded to a `residual_risks` line. Never upgrade. If the evidence
looks unsupported, run the ONE evidence-resolution pass (the same single pass §5
budgets for conflicts, per finding); if the evidence settles it, downgrade and disclose
the downgrade in the final report; if it does not settle it, STOP as an unresolved
reviewer conflict.

## 2. Convergence gate (PASS)

Evaluate in order. Gate **blockers** are the finding-side conditions only; validation
is the action that COMPLETES convergence, not a precondition to enter the path.
Conflicts never reach the gate — the conflict stop fires upstream during resolution:

```text
gate blockers =
    open correctness P0/P1 findings (BLOCK row above)
  + open structural regressions (BLOCK row above)
  + strict-profile extras (P2 / improvement, when strict is active)

"open" = lifecycle OPEN (not RESOLVED, not WAIVED; BLOCKED findings exit via the
blocked path, they do not linger as gate blockers)

if gate blockers == 0:
    ensure validation is CURRENT and at gate level (§4); run it if not
    green                    → PASS (residual findings recorded, never blocking)
    red, pre-existing and not blocking correctness
                             → PASS, with the failing line rendered as
                               `<command>: FAIL (pre-existing, residual validation risk)`
    red, blocks confirming correctness or caused by the change
                             → §4 failure handling (repair, or STOP BLOCKED)
    no validation declared by the project and none discoverable
                             → the validation condition is satisfied vacuously;
                               render `none declared by project`
else:
    stop guards (§5) → actionable findings (§3) → fix batch → validate → fresh round
```

PASS therefore requires: gate blockers == 0 AND validation green on the current tree —
OR the two sanctioned red/vacuous passes above, both explicitly rendered. A clean
round-1 (both reviewers PASS) follows the same path; so does a residual-only round-1:
it must never terminate as STOP for lack of something to fix.

At gate-zero, remaining P2/P3 findings and structural `improvement`s are recorded as
residual — P2s are fixable only inside a batch triggered by a blocking finding, never
as a post-gate fix (a post-gate write would invalidate validation and restart the
round).

## 3. Fix policy

- **Single writer**: reviewers never write; the main agent is the only writer.
- **Actionable findings** (fix order): (1) correctness P0, (2) correctness P1,
  (3) structural regressions, (4) clear low-risk in-scope P2, (5) P3 not auto-fixed.
  Say "findings", not "blockers": this list may contain non-blocking items.
- **One coherent root-cause batch per round**:

```text
review whole scope → dedupe actionable findings → fix one coherent batch
→ validate → re-review whole scope
```

Never ping-pong `fix F001 → re-review → fix F002 → re-review`; it burns review rounds
and oscillates on local optima.
- **Minimal but not artificially tiny**: correctness fixes are the smallest safe
  root-cause fix. Structure fixes may exceed one function but must directly serve this
  change's maintainability — the loop is not a repo-wide refactor vehicle.
- **Fixes must read as if written blind.** Never embed finding ids, reviewer
  feedback, or round history in code, comments, test names, or commit-adjacent text —
  fresh reviewers read changed-file contents and any such narrative leaks prior rounds
  into their context.
- **Forbidden automatic actions** (unless the user explicitly asked): commit, amend,
  push, merge, create PR, delete branch, destructive reset/revert, touching unrelated
  user work.

## 4. Validation contract

Priority order for what to run:

1. What the target repo's `AGENTS.md` / project instructions explicitly require;
2. The project's own scripts / Makefile / package config where the match is obvious;
3. Targeted tests directly covering the touched scope;
4. Final full validation before declaring PASS.

The plugin has NO language and NO default test command. `go test`, `pytest`,
`npm test`, `cargo test` are the target project's business, discovered from its rules
and files — never assumed.

**Freshness and level**: a validation result is current ONLY if no repository write
has occurred since that command completed. Any write (including the loop's own fixes,
and any write observed from a reviewer) invalidates prior results. Intermediate rounds
may run targeted validation (priority 3); the gate-time check at zero blockers must
satisfy priority 4 — the project's required/full validation — before PASS. This is
internal orchestrator state — reviewers are never told validation commands, results,
or history.

**If validation fails:**

- Failure related to this round's fixes → repair within the round (it is still part of
  convergence); if your own fix regressed and cannot be repaired safely, revert YOUR fix.
- Pre-existing / unrelated failure → do not expand scope; record evidence. If it blocks
  confirming correctness, STOP with `BLOCKED`; otherwise report it as a residual
  validation risk.

## 5. Guards and stop conditions

Defaults (a user may override them explicitly in-request):

```yaml
max_rounds: 3
no_progress_rounds: 2
```

| Condition | Detection | Action |
|---|---|---|
| PASS | gate blockers == 0 AND validation green (or sanctioned red/vacuous pass, §2) on the current tree | final PASS report |
| max rounds | `max_rounds` reached with gate blockers open | STOPPED, list open blockers; findings fixed by the last round but not yet re-reviewed are listed as `fixed, pending review confirmation` |
| no progress | stagnation (defined below) sustained for `no_progress_rounds` consecutive comparable rounds | STOPPED, reason `no progress` |
| oscillation | the main agent's OWN fix directions for the SAME design question flip between two answers across three comparable rounds (N demands X, N+1 demands not-X, N+2 returns to X) | STOPPED, present both directions' trade-offs, hand back to the user |
| permission boundary | fix requires destructive action, external write, or API/security/deployment authorization the loop does not have | STOPPED, reason `permission boundary` |
| reviewer conflict | reviewers disagree on material behavior/architecture, or a classification cannot be settled by the §1 evidence-resolution pass | ONE resolution pass; if still undecidable → STOPPED, reason `unresolved conflict`, presenting both positions |

PASS is evaluated first. The guards apply only when gate blockers > 0 (or validation
has not yet sanctioned the round): a round meeting the PASS condition reports PASS
even if a guard's pattern is also detectable.

### Progress semantics

Classify the previous round's open gate blockers against the current round
semantically (root cause, not line numbers). "New" means a root cause that has
NEVER appeared in this session — a re-surfacing root cause is always persistent
(reopened), never new churn (see finding-schema.md §2 for identity rules):

```text
seen_before = union of all root causes that appeared in ANY previous round
persistent  = current ∩ seen_before   # still open or reopened after absence
new         = current − seen_before   # first appearance in this session (churn)
resolved    = previous − current      # fixed and confirmed by fresh review
```

- **Stagnation** (the ONLY thing the no-progress guard measures): every persistent
  blocker shows no semantic improvement AND validation did not improve
  (failing → passing). Each stagnation round where this holds increments the counter.
- **Resolved > 0, or a persistent blocker materially improved, or validation
  improved** → real progress: reset the counter. Fresh new blockers are recorded as
  churn — they do NOT by themselves make a round "no progress"; `max_rounds` bounds
  endless churn.
- Round 1 establishes the baseline and NEVER counts — counting starts from the first
  round that can be compared against a previous one.

**Guard precedence**: when several stop conditions fire in the same round, evaluate in
this order and use the first match as the report's `Reason:` (listing any others in
`What was tried` if material): blocked (validation failure blocking correctness, or
nothing actionable and a human decision/permission is missing) → oscillation →
permission boundary → unresolved conflict → no progress → max rounds. Guards override
the fix policy: once a stop condition fires, no further fixes are applied, even ones
the fix order would rank as actionable. Churn counts as progress for the counter;
stagnation alone triggers no-progress.
