# Convergence, Fix Policy, and Stop Guards

When the loop may claim success, what it may fix, when it must stop.

## 1. Convergence gate (PASS) — all five required

```text
1. open P0 findings == 0
2. open P1 findings == 0
3. structural blocking findings == 0
4. required project validation passes
5. no unresolved material reviewer conflict
```

- **P2**: fix when direct, low-risk, and clearly inside the current change; otherwise
  record as residual. P2 never blocks PASS by default. If the user explicitly asked for
  `strict` / `zero findings` / `fix everything reasonable`, promote P2 into the gate.
- **P3**: never auto-fixed, never blocks PASS.
- A clean round-1 (both reviewers PASS) still requires condition 4: run the required
  validation once, then PASS.

**Structure reviewers cannot block convergence with taste.** Every structure finding
carries `discipline:` — `blocking regression` (change made structure materially worse),
`material improvement` (clear behavior-preserving win), or `taste` (must NOT be reported
as a finding; at most one aggregate `residual_risks` line). If the change introduces no
structural regression, PASS is the correct verdict even when further polish is
imaginable.

## 2. Fix policy

- **Single writer**: reviewers never write; the main agent is the only writer.
- **Fix order**: (1) P0 correctness/security/data-loss, (2) P1, (3) structural
  blockers, (4) clear low-risk in-scope P2, (5) P3 not auto-fixed.
- **One coherent root-cause batch per round**:

```text
review whole scope → dedupe actionable blockers → fix one coherent batch
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

## 3. Validation contract

Priority order for what to run:

1. What the target repo's `AGENTS.md` / project instructions explicitly require;
2. The project's own scripts / Makefile / package config where the match is obvious;
3. Targeted tests directly covering the touched scope;
4. Final full validation before declaring PASS.

The plugin has NO language and NO default test command. `go test`, `pytest`,
`npm test`, `cargo test` are the target project's business, discovered from its rules
and files — never assumed.

**If validation fails:**

- Failure related to this round's fixes → repair within the round (it is still part of
  convergence); if your own fix regressed and cannot be repaired safely, revert YOUR fix.
- Pre-existing / unrelated failure → do not expand scope; record evidence. If it blocks
  confirming correctness, STOP with `BLOCKED`; otherwise report it as a residual
  validation risk.

## 4. Guards and stop conditions

Defaults (a user may override them explicitly in-request):

```yaml
max_rounds: 3
no_progress_rounds: 2
```

| Condition | Detection | Action |
|---|---|---|
| PASS | convergence gate met | final PASS report |
| max rounds | `max_rounds` reached with blockers open | STOPPED, list open blockers |
| no progress | 2 consecutive rounds: blocking set not shrinking / same root cause recurring in equivalent form / validation not improving | STOPPED, reason `no progress` |
| oscillation | design flip-flops between two directions (e.g. round N demands an abstraction, round N+1 demands its removal, round N+2 returns to the original) | STOPPED, present both directions' trade-offs, hand back to the user |
| permission boundary | fix requires destructive action, external write, or API/security/deployment authorization the loop does not have | STOPPED, reason `permission boundary` |
| reviewer conflict | reviewers disagree on material behavior/architecture | main agent runs ONE evidence resolution pass (code, tests, contracts); if still undecidable → BLOCKED, STOPPED. Never decide by majority vote |

Progress = the set of open blockers shrank, or validation moved from failing to
passing. Compare against the previous round's blocking set semantically (root cause,
not line numbers).
