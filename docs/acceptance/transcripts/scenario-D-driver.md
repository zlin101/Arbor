# scenario-D-driver

- task: a3457f221c22add0a
- evidence class: LIVE-LOOP
- assistant text blocks: 17
- reviewer spawns: 5 (full prompts in spawn4-full.md files)

## Spawns

0. **Round 1 correctness review** (general-purpose) — full prompt: `scenario-D-driver-spawn0-full.md`
1. **Round 1 structure review** (general-purpose) — full prompt: `scenario-D-driver-spawn1-full.md`
2. **Round 1 correctness review** (general-purpose) — full prompt: `scenario-D-driver-spawn2-full.md`
3. **Round 2 correctness review** (general-purpose) — full prompt: `scenario-D-driver-spawn3-full.md`
4. **Round 2 structure review** (general-purpose) — full prompt: `scenario-D-driver-spawn4-full.md`

## Final assistant output (verbatim)

```
Loop complete — PASS at round 2. Here is the final report, then the required evidence.

---

## (1) Final report

```text
Dual Review Loop: PASS

Rounds: 2/3

Resolved
- F001 [P2] rename validates the target only after mutating state, so a failed rename needs a compensating restore
- F002 [P2] rename crashes with AttributeError on a non-string target key
- F004 [P2] no test covers any rename failure path
- F005 [P2] rename splits the store's outcome contract three ways (resolved by round-2 re-review, not by a code edit)

Residual non-blocking
- F003 [P3] `sys:` guard is rename-target-only, so it is not a namespace boundary
- F006 [P2] successful rename's audit entry is never asserted
- F007 [P3] self-rename no-op branch is unpinned and inconsistent for `sys:` keys

Validation
- python3 test_store.py: PASS

Review coverage
- correctness reviewer: FINDINGS (non-blocking residuals only)
- structural reviewer: PASS

No commit or push was performed.
```

---

## (2) EVIDENCE

### (a) Round-1 verdict envelopes (verbatim)

**Reviewer 1 — correctness**

```yaml
reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P2
    blocking: false
    category: correctness
    location:
      file: /tmp/arbor-acceptance/fixture-d/store.py
      line: 19
      symbol: Store.rename
    title: rename crashes with AttributeError for non-string target keys
    problem: The guard `new.startswith("sys:")` assumes the target key is a str, but the rest of the Store API accepts any hashable key, so a non-str target raises an unhandled AttributeError instead of the method's own error protocol (False / ValueError).
    evidence: Verified in-memory against the current file — `s.set(7, 'v'); s.rename(7, 'x')` returns True (non-str source keys fully work), while `s.rename('a', 2)` raises `AttributeError: 'int' object has no attribute 'startswith'`. No caller in the repo passes non-str keys today, and the exception fires before the pop, so state stays intact.
    impact: An implicit str-only constraint on targets that nothing validates or documents; callers handling the documented failure modes (False, ValueError) get an unexpected crash on an input class set/get/delete accept.
    recommended_direction: Guard the prefix test (e.g. `isinstance(new, str) and new.startswith("sys:")`), or validate/reject non-str keys explicitly before touching _data.
  - local_id: C2
    severity: P2
    blocking: false
    category: security
    location:
      file: /tmp/arbor-acceptance/fixture-d/store.py
      line: 19
      symbol: Store.rename
    title: "sys: namespace guard is one-sided and provides no real reservation"
    problem: The new check only blocks rename into the `sys:` prefix; it does not establish the reservation it appears to enforce, because set can create `sys:` keys and rename can move keys out of the namespace.
    evidence: Verified in-memory — `s.set('sys:reserved', 'x')` succeeds, and `s.rename('sys:thing', 'plain')` returns True, so a `sys:` key can be created via set and drained away via rename.
    impact: Any caller relying on rename's ValueError to keep `sys:` reserved has no actual guarantee; the guard is trivially bypassed within the same class.
    recommended_direction: Either enforce the prefix on all write paths (set as well) or scope the check's meaning to "rename target only" in a docstring so callers do not over-trust it.
  - local_id: C3
    severity: P2
    blocking: false
    category: tests
    location:
      file: /tmp/arbor-acceptance/fixture-d/test_store.py
      line: 17
      symbol: TestStore.test_rename
    title: No test covers any rename failure path, including the pop/restore rollback
    problem: test_rename exercises only the happy path. The collision branch that pops the source key and restores it, and the sys: rejection, have zero test protection.
    evidence: Deleting line 23 of store.py (`self._data[old] = value`) would make a failed rename silently destroy the source key, and all 4 tests still pass (verified by reading the assertions — none touch the collision, sys:, or missing-source branches).
    impact: The only rollback logic in this change is unguarded; silent data loss on the collision path could ship green.
    recommended_direction: Smallest test — set 'a' and 'b', assert `rename('a', 'b')` raises ValueError, then assert `get('a')` still returns the original value and the audit log gained no rename entry.
  - local_id: C4
    severity: P3
    blocking: false
    category: correctness
    location:
      file: /tmp/arbor-acceptance/fixture-d/store.py
      line: 21
      symbol: Store.rename
    title: Failed rename restores the value but reorders dict insertion order
    problem: The code pops the source key before validating the target, then re-inserts on collision; re-insertion moves the key to the end of the dict, so a failed rename is not fully side-effect free.
    evidence: Verified in-memory — with keys inserted as ['a','b','c'], a failed `rename('a','c')` leaves data equal to {'b','c','a'} in iteration order. Values and the audit log are consistent; only order changes.
    impact: Not observable through the current public surface (no iteration/keys method), but it is a latent integrity trap for any future order-dependent consumer, and the destructive-pop-then-compensate shape is the mechanism.
    recommended_direction: Check `new in self._data` before popping so the mutating step happens only after all validation passes, which also removes the need for the restore.
coverage: Reviewed the full diff vs baseline 28c4eb4 (Store.rename and test_rename); confirmed the repo has no other callers (only AGENTS.md, store.py, test_store.py); ran `python3 -B test_store.py` (4 tests, exit 0, no files written); empirically probed non-str keys, self-rename, collision rollback, sys: asymmetry, and audit behavior in-memory.
residual_risks:
  - Concurrency unverified: rename is not atomic (pop -> membership check -> insert); two concurrent renames of the same source key could surface an unhandled KeyError from pop instead of the documented False/ValueError. No threading exists in this codebase, so the path is unexercised.
  - The intent of the sys: prefix rule is not documented anywhere in the repo; C2's impact assessment assumes the guard is meant to reserve the namespace.
```

**Reviewer 2 — structure**

```yaml
reviewer: structure
verdict: FINDINGS
findings:
  - local_id: S1
    severity: P2
    blocking: false
    category: complexity
    discipline: material improvement
    location:
      file: store.py
      line: 21-24
      symbol: Store.rename
    title: Target check ordered after mutation forces a compensating restore
    problem: The diff validates the collision precondition *after* mutating state, so it must
      then undo the mutation by hand. The pop-then-maybe-put-back sequence is complexity the
      check's placement creates, not complexity the problem requires.
    evidence: Line 21 `value = self._data.pop(old)` mutates `_data`; lines 22-24 then test
      `if new in self._data:` and, on failure, execute `self._data[old] = value` purely to
      undo line 21 before raising. Between line 21 and line 24 the store's observable state is
      missing `old`, and the reader must track a temporary `value` binding plus a rollback
      write to follow a 3-line case.
    impact: Every future edit to `rename` (new precondition, extra audit detail, exception
      type) has to reason about which mutations are already applied and which need manual
      reversal; the rollback write is also easy to drop during refactoring because nothing
      marks it as compensation.
    recommended_direction: Hoist the `new in self._data` check above any mutation so the
      method is validate-then-apply (one `self._data[new] = self._data.pop(old)` tail, no
      `value` temp, no restore). Note the reorder changes the unspecified `old == new` case,
      which today "succeeds" as a no-op and appends an audit entry — make that case explicit
      rather than leaving it accidental; the intended self-rename semantics are a spec
      question for the correctness reviewer.
  - local_id: S2
    severity: P2
    blocking: false
    category: abstraction
    discipline: material improvement
    location:
      file: store.py
      line: 16-27
      symbol: Store.rename
    title: New public method splits the store's outcome contract three ways
    problem: `rename` reports failure through three different channels — `return False` for a
      missing source, `raise ValueError("invalid target")` for a reserved prefix, and
      `raise ValueError("target exists")` for a collision — and it introduces an overwrite
      policy that contradicts the class's existing write model.
    evidence: In this file `set` silently overwrites an existing key (line 10) and `delete`
      returns `False` for a missing key (line 34); no baseline method raised. `rename` returns
      bool for absence (line 18, consistent with `delete`) but raises for both target
      problems, where the two error cases are distinguishable only by comparing exception
      message strings ("invalid target" vs "target exists").
    impact: Callers must handle a union contract (truthiness check plus try/except) and cannot
      programmatically tell the two error cases apart without string matching; the store now
      answers "does a write clobber an existing key?" two different ways (`set` yes, `rename`
      no), which is the invariant the next contributor will guess wrong.
    recommended_direction: Pick one convention for the new API and state it — e.g. bool for
      "operation did not happen" (matching `delete`) with raise reserved for genuinely invalid
      requests, or raise for all failures — and make the no-overwrite policy explicit
      (documented, or distinct exception types) instead of two same-typed messages.
coverage: Reviewed the full working-tree diff (Store.rename, test_rename) in
  /tmp/arbor-acceptance/fixture-d against baseline 28c4eb4, including baseline store.py/test_store.py and a repo-wide
  check that "sys:" appears nowhere else; test suite not executed (read-only mandate).
residual_risks:
  - Taste (aggregate, not findings): the inline magic literal "sys:" is unnamed as a
    module/class constant and no consumer for the reserved-prefix policy exists anywhere in
    the repo — naming it is polish with no material payoff at this size.
  - Residual: only rename's happy path is tested; the missing-source, sys:-target and
    target-exists branches and the audit-log append are unpinned, so neither the S1
    self-rename behavior nor the S2 error contract is locked by the suite.
```

### (b) Dedupe analysis — F-id assignment and merges

Normalization produced 6 round-1 local findings → 5 F-ids. One cross-lens merge; four findings stayed alone.

**MERGED → F001** = R1-C4 (correctness, P3) + R1-S1 (structure, P2). Sources: `correctness`, `structure`. Severity P2 (higher of the pair), blocking false.
- Root cause (one sentence): `Store.rename` performs its collision precondition check *after* the mutating `pop`, so every failure path must compensate for a mutation that should never have happened.
- Why these two are the same root cause: both point at the identical mechanism — the ordering of `value = self._data.pop(old)` (line 21) relative to `if new in self._data:` (line 22). The correctness lens reached it through the *behavioral* consequence (failed rename is not side-effect free: dict insertion order changes, rollback write is the only thing preventing data loss); the structure lens reached it through the *maintainability* consequence (a hand-written compensating restore plus a temporary binding that exist only because the check is late). Same symbol (`Store.rename`), same behavioral risk (a rejected rename leaves residue), and fixing one eliminates the other — hoisting the check deletes the restore, the temp, and the reordering simultaneously. This is the textbook merge case in finding-schema.md §3, and it is why both reviewers independently flagging it was treated as corroboration, not as two defects (severity stayed P2; it was not inflated).
- Why I did not merge on symbol alone: C1, C2 and S2 also live in `Store.rename`. Reading "same or adjacent symbol" as sufficient on its own would collapse every finding in the function into one F-id, which contradicts the doc's own "do NOT merge on similar titles / matching categories" guard. The symbol criterion marks where to look; root cause decides the merge. Stated explicitly, because this is the discipline the scenario tests.

**Kept separate:**
- **F002** = R1-C1 (non-str target → `AttributeError`). Root cause: an unvalidated key type reaches a str-only method. Different failure mode (crash on an input the rest of the API accepts) from F001's (side effects on a rejected rename). Rejecting a rename is correct behavior; crashing is a different bug. Same symbol, different root cause → separate.
- **F003** = R1-C2 (`sys:` guard is one-sided, so it reserves nothing). Root cause: the reservation policy is not established across write paths. It implicates `set` (untouched baseline code) as much as `rename`, so it is a different ownership boundary than F001, and no fix to `rename`'s ordering eliminates it. Separate.
- **F004** = R1-C3 (no test covers any rename failure path). Root cause: absent coverage, not defective code. Fixing F001 removes the rollback being tested but does not create the missing test. Separate.
- **F005** = R1-S2 (`rename` reports failure through three channels). Root cause: the new API's outcome-signaling contract, an API-design decision. Orthogonal to check ordering — a validate-then-apply rewrite can keep all three channels untouched. Separate.

**Round-2 mapping (semantic, no line numbers):**
- R2-C3 → mapped to existing **F003** (same root cause, re-derived independently: `sys:` target-only guard is not a namespace boundary). Downgraded P2 → P3 by the fresh reviewer; still non-blocking.
- R2-C1 → **new F006** (success-path audit append unpinned). Not a recurrence of F004: F004 was about failure paths and is now closed by `test_rename_failure_paths`; F006 is about the positive path's audit side effect, which no round-1 reviewer raised.
- R2-C2 → **new F007** (self-rename no-op unpinned; `sys:` → `sys:` raises). Not a recurrence of F001 — S1 *predicted* the reorder would make this case explicit, which it now is; the residual issue is that it is unspecified and untested.
- F001, F002, F004, F005: no fresh round-2 finding re-confirms any of them → RESOLVED (validation green).

### (c) The single fix + validation

One coherent root-cause batch, one writer (me), one round — not two fixes for F001:

- `/tmp/arbor-acceptance/fixture-d/store.py` — `Store.rename` rewritten validate-then-apply: all precondition checks (`old` present, `isinstance(new, str)` prefix guard, `new != old`, `new in self._data`) run before the single mutating statement `self._data[new] = self._data.pop(old)`. The `value` temporary and the `self._data[old] = value` rollback write are deleted. `sys:` check keeps its original precedence over the collision check, and self-rename still returns `True` with an audit entry — observable behavior preserved for every previously-working input. This one edit resolves F001 (the merged finding) and, because the guard had to be written for the API's real key domain, F002.
- `/tmp/arbor-acceptance/fixture-d/test_store.py` — added `test_rename_failure_paths`: missing source → `False`; `sys:` target → `ValueError`; collision → `ValueError` with the source key's value intact and no audit entry. Resolves F004 and pins F001's fix.
- F003 and F005 were deliberately not fixed: both require a policy decision (is `sys:` a store-wide invariant or a rename-target rule? bool-vs-raise convention?) that no spec in the repo answers. The loop does not invent policy.

Validation: `python3 test_store.py` (the command AGENTS.md requires) → **exit code 0**, 5 tests, OK.

### (d) Round-2 verdict envelopes (verbatim)

**Reviewer A2 — correctness**

```yaml
reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P2
    blocking: false
    category: tests
    location:
      file: test_store.py
      line: 17
      symbol: TestStore.test_rename
    title: Success-path audit entry is never asserted
    problem: The new tests verify rename's data movement but never verify that a successful rename appends its audit record, even though the audit log is this module's stated contract ("In-memory key-value store with an audit log") and the audit append is the new method's only other side effect.
    evidence: The only audit assertion added is negative — `self.assertNotIn(("rename", "a", "b"), s.audit)` in test_rename_failure_paths (test_store.py:35). If store.py:25 (`self.audit.append(("rename", old, new))`) were deleted, all 5 tests still pass (verified by reading the assertion set; the positive path has no assertion).
    impact: A future regression that silently drops rename audit records (or logs the wrong tuple) would ship undetected; the failure-path test greenlights an audit-less rename because its negative assertion is satisfied by absence of any entry.
    recommended_direction: Add one assertion to test_rename that the audit log contains ("rename", "a", "b") after the successful rename (e.g. assertIn or assertEqual on the tail of s.audit).
  - local_id: C2
    severity: P3
    blocking: false
    category: tests
    location:
      file: store.py
      line: 21
      symbol: Store.rename
    title: No-op self-rename branch is untested and inconsistent for sys: keys
    problem: The `if new != old:` short-circuit makes self-rename a successful no-op, but the sys: guard is checked before it, so a self-rename of a reserved key raises instead of no-op'ing; neither behavior is specified or tested.
    evidence: Verified in-memory against the current code — `s.rename("a", "a")` returns True, leaves data intact, and appends ("rename", "a", "a"); `s.rename("sys:k", "sys:k")` raises ValueError("invalid target") even though it would change nothing. No test exercises either path (the added tests only cover old-missing, sys: target on a different key, and existing-target).
    impact: The reserved-key self-rename raising is a verified boundary inconsistency a caller doing an idempotent "ensure key named X" would hit; because the no-op branch's contract (return value, audit tuple with identical names) is unpinned, any refactor of the guard ordering can silently change it.
    recommended_direction: Add a small test pinning self-rename semantics (returns True, data unchanged, audit entry logged) and one line deciding whether sys:->sys: should raise or no-op; move the `new != old` check before the sys: guard if no-op should win.
  - local_id: C3
    severity: P3
    blocking: false
    category: security
    location:
      file: store.py
      line: 19
      symbol: Store.rename
    title: sys: guard is enforced on rename targets only, so it is not a namespace boundary
    problem: The new reserved-namespace check constrains only the destination of a rename; the same new method will happily move a sys: key out of the reserved namespace, so the guard reads as a protection but guarantees much less than it appears to.
    evidence: Verified in-memory — `s.rename("sys:cfg", "user:cfg")` returns True and relocates the reserved key (`{'user:cfg': 'secret'}`). For context (pre-existing code, not a finding): baseline `set` also creates sys: keys unchecked (`s.set("sys:auth", "x")` succeeds). "sys:" appears nowhere else in the repo or its single-commit history, so no spec pins the intended guarantee.
    impact: If sys: is meant to be system-reserved, a caller can strip a key of its reserved name via the new write path, and the target-only check gives a false impression that the namespace is enforced; if it is only a rename-target naming rule, the code is fine but undocumented.
    recommended_direction: Confirm the intended semantics and either document the guard as target-only in the docstring/error message or extend the check to cover moving keys out of the sys: prefix as well.
coverage: Reviewed the full working-tree diff vs 28c4eb4 (Store.rename and its two new tests) at /tmp/arbor-acceptance/fixture-d; traced every rename branch and failure path including state and audit effects, ran `python3 -B test_store.py` (exit 0, no bytecode writes), verified edge cases in memory (self-rename, missing-source with sys: target, sys:->user rename, unhashable target), and confirmed rename/sys: have no other callers or references in the repo or history.
residual_risks:
  - Concurrency: rename's exists-check and pop are not a single atomic step, so under threaded callers two concurrent renames onto the same target could both pass the check and silently lose one source's value (both returning True), and a concurrent delete between the checks and the pop would raise KeyError from `pop`. Not raised as a finding — the class has no locking anywhere (baseline delete is already check-then-act) and no threading exists in the repo, so this is contingent on an execution model nothing uses today.
  - The intended semantics of the sys: prefix are unverifiable from the repo (no spec, no callers, single commit); C3 flags the asymmetry but the "correct" behavior cannot be determined from available evidence.
```

**Reviewer B2 — structure**

```yaml
reviewer: structure
verdict: PASS
findings: []
coverage: Reviewed the +12/+32-line rename addition to Store and its two tests in /tmp/arbor-acceptance/fixture-d (store.py, test_store.py) against baseline 28c4eb4, checking branch growth, abstraction quality, layer/reuse, atomicity, sprawl, and missed simplifications; ran `python3 -B test_store.py` (5 tests, exit 0) read-only.
residual_risks:
  - Taste-level only, aggregated per skill section 5: (a) the `isinstance(new, str)` guard in `rename` (store.py:19) exists because the store's key-type contract is undeclared — declaring keys as strings would put that check once at the `set` boundary, but that is a behavior change, so it is not a behavior-preserving improvement; (b) the `sys:` reserved-prefix policy is scoped to exactly one of the two write paths (enforced on `rename` targets, not on `set`), so a reader cannot tell whether it is a store-wide invariant or rename-specific — naming the constant or documenting the scope would clarify it, but applying it to `set` changes behavior and extracting it for a single call site merely relocates one line (checklist remedy 6 discourages that); (c) the class now mixes error-signaling conventions (`delete`/`rename` return False for missing keys while `rename` raises for a conflicting target) — defensible since missing-vs-conflict are different severities; (d) `test_rename_failure_paths` asserts one specific audit tuple is absent (`assertNotIn(("rename", "a", "b"), s.audit)`) instead of asserting the audit log is unchanged, which is the weaker form of the same invariant.
```

Round-2 convergence gate: open P0 = 0, open P1 = 0, structural blocking = 0, `python3 test_store.py` exit 0, no reviewer conflict → PASS at round 2 of 3. Round 3 not needed.

### (e) Git state before / after (no commits performed)

| | `status --porcelain` | `log --oneline` |
|---|---|---|
| Before loop (freeze) | ` M store.py` / ` M test_store.py` / `?? __pycache__/` | `28c4eb4 base store` |
| After loop | ` M store.py` / ` M test_store.py` / `?? __pycache__/` | `28c4eb4 base store` |

Baseline stayed frozen at `28c4eb409ecfd30e5742837121761fd38df1c1e4` for both rounds; nothing was staged, committed, or pushed. Diff grew from 20 to 32 insertions across the same two files.

### (f) Reviewer write operations

**None.** Evidence:

- Tracked file mtimes never changed outside my own writes: `store.py` 22:27:50 and `test_store.py` 22:27:54 are my two Edits; both round-2 reviewers ran entirely after that and touched nothing (final `date` check at 22:35:05).
- `__pycache__/` contains exactly one file, `store.cpython-312.pyc`, last written 22:28:01 — that was **my** validation run (`python3 test_store.py` imports `store`), executed before the round-2 reviewers launched. No `test_store` bytecode ever appeared, and round-1/round-2 reviewers used `python3 -B` (no bytecode), matching their disclosures.
- Round-1 integrity check immediately after both verdicts: `git diff HEAD` sha256 `6458a1e4…` with stat still `13 + 7 insertions`, identical to freeze; tracked mtimes still 22:13:09 (setup time, before any reviewer ran).
- Reviewers ran the test suite read-only and probed behavior in-memory rather than editing; no reviewer created, modified, staged, or deleted anything. F1/F2 integrity defenses were not triggered, so no round was discarded or re-spawned. (Note: the first attempt to launch the round-1 correctness reviewer failed with a transient infrastructure error before it started; I re-issued that spawn immediately — no results were lost or duplicated.)

---

## (3) F-ids per root cause

Each distinct root cause received **exactly one** F-id — no root cause was double-counted across lenses or rounds, and no F-id bundles two unrelated causes:

| Root cause | F-ids | Local ids carried |
|---|---|---|
| Collision check ordered after the mutating pop → compensating restore / side effects on failed rename | **1 (F001)** | R1-C4 (correctness) + R1-S1 (structure) — the cross-lens merge |
| Non-string target crashes on the str-only prefix guard | **1 (F002)** | R1-C1 |
| `sys:` reservation not actually established (target-only guard, `set` unchecked) | **1 (F003)** | R1-C2, re-derived in R2 as C3 (mapped, not duplicated) |
| Rename failure paths untested | **1 (F004)** | R1-C3 |
| `rename`'s three-channel outcome contract | **1 (F005)** | R1-S2 |
| Success-path audit append unpinned | **1 (F006)** | R2-C1 |
| Self-rename no-op unpinned / `sys:`→`sys:` inconsistency | **1 (F007)** | R2-C2 |

Total: 7 F-ids for 7 root causes. The scenario's target case — both reviewers landing on the same root cause from different lenses — occurred exactly once and was merged into a single F-id with both `sources` recorded and fixed exactly once.
```
