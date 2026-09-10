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

- Strict profile applies only when the user explicitly asked (`strict` /
  `zero findings` / `fix everything reasonable`).
- **P2 default posture**: fix when direct, low-risk, and clearly inside the current
  change; otherwise record as residual.
- **P3**: never auto-fixed, never blocks PASS on either profile.
- **Taste is not a finding.** The schema cannot express it; taste-level observations
  belong in `residual_risks`. If the change introduces no structural regression, PASS
  is the correct verdict even when further polish is imaginable.

**Classification audit (main agent).** A classification counts as its evidence states.
`structure: regression` blocks only if the evidence names concrete material worsening
introduced by THIS change (new spaghetti, boundary leak, duplicated canonical logic)
relative to the baseline. If the classification is unsupported — the cited
"regression" contradicts a previous round's demand, describes a pre-existing condition,
or is preference phrased as regression — run ONE evidence-resolution pass; if the
evidence settles it, downgrade the classification (never upgrade) and say so in the
final report; if it does not settle it, STOP as an unresolved reviewer conflict.

## 2. Convergence gate (PASS)

Evaluate in order. Gate **blockers** are the finding-side and conflict-side conditions
only; validation is the action that COMPLETES convergence, not a precondition to enter
the path:

```text
gate blockers =
    open correctness P0/P1 findings (BLOCK row above)
  + open structural regressions (BLOCK row above)
  + strict-profile extras (P2 / improvement, when strict is active)
  + unresolved material reviewer conflict

if gate blockers == 0:
    ensure validation is current (see §4); run it if not
    green        → PASS (residual findings recorded, never blocking)
    not green    → classify the failure per §4
else:
    stop guards (§5) → actionable findings (§3) → fix batch → validate → fresh round
```

PASS therefore requires: gate blockers == 0 AND validation green **on the current
tree**. A clean round-1 (both reviewers PASS) follows the same path — validation runs,
then PASS. A residual-only round-1 (only non-blocking findings) is the same path; it
must never terminate as STOP for lack of something to fix.

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

**Freshness**: a validation result is current ONLY if no repository write has occurred
since that command completed. Any write (including the loop's own fixes) invalidates
prior results; when gate blockers reach zero and no current result exists, run the
required validation before PASS. This is internal orchestrator state — reviewers are
never told validation results or history.

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
| PASS | gate blockers == 0 AND validation green on the current tree | final PASS report |
| max rounds | `max_rounds` reached with gate blockers open | STOPPED, list open blockers |
| no progress | stagnation (defined below) sustained for `no_progress_rounds` consecutive comparable rounds | STOPPED, reason `no progress` |
| oscillation | design flip-flops between two directions (e.g. round N demands an abstraction, round N+1 demands its removal, round N+2 returns to the original) | STOPPED, present both directions' trade-offs, hand back to the user |
| permission boundary | fix requires destructive action, external write, or API/security/deployment authorization the loop does not have | STOPPED, reason `permission boundary` |
| reviewer conflict | reviewers disagree on material behavior/architecture, or a classification cannot be settled by the §1 evidence-resolution pass | ONE resolution pass; if still undecidable → BLOCKED, STOPPED. Never decide by majority vote |

### Progress semantics

Classify the previous round's open gate blockers against the current round
semantically (root cause, not line numbers):

```text
persistent = previous ∩ current    # same root cause still open
resolved   = previous − current    # fixed and confirmed by fresh review
new        = current − previous    # first surfacing this round (churn)
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
`What was tried` if material): oscillation → permission boundary → reviewer conflict →
no progress → max rounds. Guards override the fix policy: once a stop condition fires,
no further fixes are applied, even ones the fix order would rank as actionable.
