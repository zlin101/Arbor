# scenario-C-driver

- task: ac4ab3f70c4cf84bc
- evidence class: LIVE-LOOP
- assistant text blocks: 17
- reviewer spawns: 5 (full prompts in spawn4-full.md files)

## Spawns

0. **Round 1 correctness reviewer** (general-purpose) — full prompt: `scenario-C-driver-spawn0-full.md`
1. **Round 1 structure reviewer** (general-purpose) — full prompt: `scenario-C-driver-spawn1-full.md`
2. **Round 1 correctness reviewer** (general-purpose) — full prompt: `scenario-C-driver-spawn2-full.md`
3. **Round 2 correctness reviewer** (general-purpose) — full prompt: `scenario-C-driver-spawn3-full.md`
4. **Round 2 structure reviewer** (general-purpose) — full prompt: `scenario-C-driver-spawn4-full.md`

## Final assistant output (verbatim)

```
Round 2 verdicts are in and the convergence gate is met. Final answer below.

---

## (1) Final report

```text
Dual Review Loop: PASS

Rounds: 2/3

Resolved
- F001 [P1] sys: guard fired only where it was a no-op
- F004 [P1] protection policy duplicated across three accessors with no definition site
- F002 [P2] get() silently overrode the caller's default with a hardcoded sentinel
- F003 [P2] non-string keys regressed from working to AttributeError

Residual non-blocking
- F005 [P3] rejected sys-key write's no-side-effect property is untested

Validation
- python3 test_store.py: PASS

Review coverage
- correctness reviewer: FINDINGS (round 2) — one P3, non-blocking
- structural reviewer: PASS

No commit or push was performed.
```

Convergence gate: open P0 = 0, open P1 = 0, structural blocking = 0, `python3 test_store.py` exit 0, no unresolved reviewer conflict. Round 2's only new finding is P3, which never enters the gate, so no third round was needed.

---

## (2) EVIDENCE

Note on quoting: the subagent-notification payload HTML-escaped `<`/`>` (e.g. `&lt;protected&gt;`, `&gt;` block scalars). Both envelopes below are the reviewers' literal text with those characters restored.

### (a) Round 1 verdict envelopes (verbatim)

Correctness reviewer (round 1):

```yaml
reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P1
    blocking: true
    category: correctness
    location:
      file: /tmp/arbor-acceptance/fixture-c/store.py
      line: 21
      symbol: Store.delete
    title: sys: guard is inverted — it "protects" only absent keys and leaves present sys: keys deletable and readable
    problem: >
      The new guard is `if key.startswith("sys:") and key not in self._data: return False`,
      so it fires only when the key does not exist — precisely the case where baseline
      `delete` already returned False. When a sys: key IS present, the guard is skipped and
      the key is deleted and audit-logged. Store.get (line 16) has the same inverted
      condition and returns the real value for a present sys: key instead of "<protected>".
    evidence: >
      Baseline `delete` on a missing key already returned False, so the added lines change
      nothing for the guarded case. Seeding `Store()._data["sys:config"] = "SECRET"`
      (the only way a sys: key can exist, since set() refuses them) yields
      `get("sys:config") -> "SECRET"` and `delete("sys:config") -> True` with
      `audit == [("delete", "sys:config")]`. This directly contradicts the invariant the
      change itself declares in set(): "sys: keys are read-only". The new test
      (test_store.py:17-22) exercises only the missing-key paths — exactly the paths where
      the guard is a no-op — so the suite passes while the protection is inverted.
    impact: >
      The change's stated guarantee is not enforced by the guards that were added to enforce
      it; it holds only as a side effect of set() blocking creation. Any future bootstrap
      path that seeds sys: keys (a constructor taking initial data, a bulk-load method, or a
      direct `_data` write — the scenario "protected system keys" implies) silently gets
      readable and deletable protected keys, with the deletion recorded in the audit log.
    recommended_direction: >
      Make the sys: guard unconditional in delete (and get): return False / "<protected>"
      for every key starting with "sys:" regardless of presence, and add one test that seeds
      a sys: key directly and asserts it cannot be read or deleted.
  - local_id: C2
    severity: P2
    blocking: false
    category: correctness
    location:
      file: /tmp/arbor-acceptance/fixture-c/store.py
      line: 16
      symbol: Store.get
    title: get() silently discards the caller's default for sys: keys
    problem: >
      For sys: keys the early return bypasses `self._data.get(key, default)`, so the
      `default` parameter of `get(key, default=None)` is ignored.
    evidence: >
      `Store().get("sys:x", 0)` returns "<protected>", while `Store().get("plain", 0)`
      returns 0. Verified by execution against the working tree.
    impact: >
      Callers using a sentinel default to mean "not found" (the documented contract, and
      what test_get_default asserts for non-sys keys) get a truthy magic string instead,
      changing their not-found handling without any signal.
    recommended_direction: >
      Either honor `default` for sys: keys, or document the "<protected>" sentinel as a
      deliberate exception in the docstring and cover the default interaction in a test.
  - local_id: C3
    severity: P2
    blocking: false
    category: reliability
    location:
      file: /tmp/arbor-acceptance/fixture-c/store.py
      line: 10
      symbol: Store.set
    title: Non-string keys now raise AttributeError in set/get/delete
    problem: >
      The guards call `key.startswith("sys:")` before any type check. Keys only need to be
      hashable for the dict; at baseline `set(1, "v")`, `get(1)`, and `delete(1)` all worked.
    evidence: >
      All three methods raise `AttributeError: 'int' object has no attribute 'startswith'`
      for an int key. Baseline (28c4eb4) accepted them. No in-repo caller currently passes
      non-string keys, so this is latent rather than active breakage.
    impact: >
      A previously valid input class now fails with an unrelated-looking AttributeError
      instead of either working or raising a clear type error.
    recommended_direction: >
      Guard with `isinstance(key, str)` (treat non-str keys as non-sys) or state the
      str-only key contract in the module docstring.
coverage: >
  Reviewed the full working-tree diff of store.py and test_store.py vs baseline 28c4eb4;
  traced all three sys: guards empirically against both baseline and current behavior
  (including present-key, default-argument, non-string-key, and failed-set paths); checked
  for other callers (none — repo is only store.py and test_store.py); ran the required
  validation command `python3 test_store.py` (exit 0, 4 tests pass) and confirmed the
  working tree was left untouched.
residual_risks:
  - >
    C1's harmful branch requires a sys: key to exist in _data, which the public API
    currently prevents (set blocks creation), so the defect is latent; its severity assumes
    the read-only invariant is meant to hold against direct _data access or future
    bootstrap/seeding paths, which the change's own error message implies.
  - >
    Store is an in-memory, single-threaded structure; concurrency and persistence concerns
    are out of scope for this fixture and were not evaluated.
```

Structure reviewer (round 1):

```yaml
reviewer: structure
verdict: FINDINGS
findings:
  - local_id: S1
    severity: P1
    blocking: true
    category: abstraction
    discipline: blocking regression
    location:
      file: /tmp/arbor-acceptance/fixture-c/store.py
      line: 10
      symbol: Store.set / Store.get / Store.delete
    title: sys: protection policy smeared across all three accessors as duplicated magic-string conditionals
    problem: >
      This diff introduces a single policy ("sys: keys are protected") but writes it
      three times, in three different shapes, directly into the public API of the only
      module in the repo — instead of giving the concept one home. The baseline store
      had zero policy branching (get was a one-liner); the change bolts an ad-hoc
      special case into every accessor, so the messy version is baked into the shared
      API rather than named once.
    evidence: >
      `key.startswith("sys:")` appears at store.py:10, store.py:16, and store.py:21,
      plus a fourth occurrence of the literal in the error message at store.py:11 and
      the same literal mirrored in test_store.py:20-22. The three guards do not even
      agree on shape: set guards on `startswith` alone, get and delete on
      `startswith(...) and key not in self._data`. No symbol in the file states the
      policy; it exists only as a repeated literal that a reader must notice three times.
    impact: >
      Any change to the policy — new prefix, second protected class, changed sentinel
      string — requires finding and editing 3+ mutually unreferencing sites, each with a
      subtly different guard, with no compile-time or test signal that one was missed.
      The diff makes the file harder to scan for no compensating simplification.
    recommended_direction: >
      Name the concept once: a module-level `SYS_PREFIX = "sys:"` plus a single
      `_is_sys(key)` predicate used by set, get, delete, and the test, so the policy has
      exactly one definition site and the guards stop diverging in shape.
  - local_id: S2
    severity: P2
    blocking: false
    category: complexity
    discipline: material improvement
    location:
      file: /tmp/arbor-acceptance/fixture-c/store.py
      line: 16
      symbol: Store.get / Store.delete
    title: get/delete guards encode a phantom state that set makes unreachable
    problem: >
      The `key not in self._data` clause in get and delete guards against a state the
      class cannot reach, adding a conditional concept with no real referent and giving
      get a second, hidden not-found convention that overrides the caller's `default`.
    evidence: >
      `_data` starts empty (store.py:6) and set raises for every `sys:` key
      (store.py:10-11), so through the public API `key in self._data` is never true for
      a `sys:` key; the clause can never change the outcome in any reachable state.
      Meanwhile get's protected path returns the magic literal "<protected>"
      (store.py:17) instead of the caller-supplied `default`, so the method now has a
      three-way return contract (stored value / caller default / hardcoded sentinel)
      that its signature does not hint at.
    impact: >
      Readers must reason about a present-`sys:`-key case that cannot occur, and the
      sentinel is an unnamed string that duplicates the not-found concept `default`
      already owns. Dead branches plus a magic value make the accessors harder to read
      than the baseline one-liners.
    recommended_direction: >
      Once the predicate from S1 exists, drop the phantom `key not in self._data` clause
      from get and delete (behavior-preserving in every reachable state) and express the
      protected fallback once — e.g. `self._data.get(key, _PROTECTED_SENTINEL if
      _is_sys(key) else default)` — keeping `default` as the only caller-facing
      not-found channel.
coverage: >
  Full diff vs baseline 28c4eb4 for store.py and test_store.py, AGENTS.md, repo-wide
  grep confirming no other Store/sys: usage sites, and validation run
  (PYTHONDONTWRITEBYTECODE=1, no files written): 4 tests pass, exit 0.
residual_risks:
  - "Taste only, not findings: preferred sentinel representation (module constant vs
  sentinel object), idiomatic-exception choice, and test ordering/placement are style
  calls with no material payoff either way."
```

### (b) Restructure summary + validation

Round 1 dedupe produced two actionable P1 blockers (F001 correctness, F004 structural blocking) plus two low-risk in-scope P2s. One coherent batch applied by me as sole writer; the only file touched was `/tmp/arbor-acceptance/fixture-c/store.py` (`test_store.py` was not modified by the loop).

What moved where:
- Policy named once: added module-level `SYS_PREFIX = "sys:"` and `PROTECTED = "<protected>"`, plus a single `_is_sys(key)` predicate — one definition site for the policy that previously existed as three divergent inline conditionals plus duplicated literals (fixes F004; also implements S2's "drop the phantom clause", since the guard is now expressed once).
- Guard made unconditional: `get` and `delete` now guard on `_is_sys(key)` alone, dropping the `key not in self._data` qualifier (fixes F001 and the phantom-clause half of S2).
- Type safety folded into the single predicate: `isinstance(key, str)` lives inside `_is_sys`, so non-string keys are ordinary keys at all three call sites (fixes F003, restoring baseline behavior).
- F002 resolved by documentation rather than behavior change: honoring `default` for sys: keys would have broken the project's own `test_sys_keys` assertion (`get("sys:missing") == "<protected>"`), so per C2's stated alternative the sentinel became a named constant and the contract is stated in the `Store` docstring ("`get` reports `PROTECTED` for them (in place of `default`)").

Why behavior is preserved: the restructure is a pure extraction/rename for every input the existing tests exercise — `_is_sys` returns exactly `key.startswith("sys:")` for strings, and `set`/`get`/`delete` bodies are otherwise the baseline logic with guard clauses hoisted to the top. The two deliberate behavior deltas (unconditional sys: guard; non-string keys no longer raising) are the F001/F003 root-cause repairs requested by the reviewers, and neither is covered by an existing test, so the project's suite is unaffected. All 4 existing tests pass unchanged.

Validation: `python3 test_store.py` → exit code **0** (4 tests OK). Run three times total: pre-fix baseline exit 0, immediately post-fix exit 0, and again at loop end exit 0.

### (c) Round 2 verdict envelopes (verbatim)

Structure reviewer (round 2):

```yaml
reviewer: structure
verdict: PASS
findings: []
coverage: Reviewed store.py and test_store.py in full against baseline 28c4eb4 via the working-tree diff, ran `python3 test_store.py` (exit 0) and direct behavior probes, checked AGENTS.md rules; checklist categories ambition/judo, branch growth, abstraction, canonical layer, types, sprawl, atomicity.
residual_risks:
  - "Taste only, non-blocking: the `\"<protected>\"` string sentinel returned for sys keys is indistinguishable from a stored value and silently overrides `default`; the PermissionError message hardcodes the `sys:` literal instead of `SYS_PREFIX`; `test_sys_keys` bundles set/get/delete behavior into one test method."
```

The round-2 structure reviewer's prose explicitly declined to raise findings: "The only smells I found are taste-grade … None is a regression or a behavior-preserving simplification with clear payoff, so per convergence discipline these stay out of findings." It also confirmed no structural regression against the rubric (ambition/judo, branch growth, abstraction, canonical layer, atomicity, sprawl, AGENTS.md rules).

Correctness reviewer (round 2):

```yaml
reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P3
    blocking: false
    category: tests
    location:
      file: /tmp/arbor-acceptance/fixture-c/test_store.py
      line: 17
      symbol: test_sys_keys
    title: New sys-key guard's no-side-effect property is untested
    problem: The only new test asserts that set() raises PermissionError, get() returns
      "<protected>", and delete() returns False, but it never asserts that a rejected
      write leaves the store untouched. The whole point of the guard is that a sys-key
      write must not take effect; that invariant is not pinned.
    evidence: test_sys_keys wraps s.set("sys:config", 1) in assertRaises and stops there.
      If the guard in store.py set() (lines 35-36) were moved below the
      self._data[key] = value / self.audit.append(...) pair, the store would be silently
      corrupted and this test would still pass. Verified by probe: the current code
      leaves _data and audit byte-identical across a rejected set, but no test records
      that. Likewise unpinned are the documented "PROTECTED in place of default"
      semantics (s.get("sys:x", 42) must return "<protected>", not 42) and the
      _is_sys docstring claim that non-string keys are ordinary keys
      (s.set(("sys:", "k"), 5) must succeed).
    impact: The strongest correctness property this change adds — rejected writes have
      zero effect on state or audit trail — is unguarded against regression, so a future
      reordering of the guard could ship green.
    recommended_direction: Extend test_sys_keys with three assertions after the
      assertRaises block — self.assertEqual(s.audit, []), self.assertEqual(s._data, {}),
      and self.assertEqual(s.get("sys:missing", 42), "<protected>") — plus one line
      setting a non-string sys-prefixed key to lock the _is_sys contract.
coverage: Reviewed the full working-tree diff of store.py and test_store.py against
  baseline 28c4eb4 on its own evidence; ran python3 test_store.py (exit 0, 4 tests OK)
  and runtime probes of rejected-set atomicity, default override, delete-on-sys,
  non-string/case/empty-key boundaries, and ordinary-key baseline preservation;
  confirmed via repo inventory (AGENTS.md, store.py, test_store.py only) that no
  in-repo callers exist to break.
residual_risks:
  - No consumers of Store exist in this repo, so the new contract — notably get()
    returning "<protected>" instead of a caller-supplied default for sys keys — could
    not be validated against real caller expectations; any out-of-tree caller passing
    defaults for sys-prefixed keys would see changed return values.
  - __pycache__/ untracked build noise was explicitly out of scope and not reviewed.
  - Single-threaded semantics only; the pre-existing non-atomic data+audit pair in
    set()/delete() is baseline behavior, unchanged, and was not re-adjudicated.
```

Cross-round mapping: no round-2 finding re-confirms F001–F004 → all four RESOLVED. Round-2 C1 is a new finding → F005 (P3, OPEN, residual).

### (d) Round-2 scope: FULL, not fix-diff

Both round-2 reviewers received the full materialization: frozen `baseline_commit: 28c4eb409ecfd30e5742837121761fd38df1c1e4`, a freshly generated `git diff HEAD` covering the entire change (31 insertions across `store.py` + `test_store.py` — including my fix), the full current contents of both changed files, and the verbatim `AGENTS.md`. The prompt stated explicitly: "This is NOT a fix-only diff: review the whole change against the frozen baseline." No prior-round findings, verdicts, or narrative were passed to either reviewer; both confirmed in `coverage` that they reviewed the full diff vs baseline `28c4eb4`.

### (e) Git state (no commits performed)

Before (loop start):
```
$ git status --porcelain          $ git log --oneline
 M store.py                       28c4eb4 base store
 M test_store.py
?? __pycache__/
```
After (loop end):
```
$ git status --porcelain          $ git log --oneline
 M store.py                       28c4eb4 base store
 M test_store.py
?? __pycache__/
```
`git status --porcelain` output is byte-identical before and after; HEAD is unchanged at `28c4eb409ecfd30e5742837121761fd38df1c1e4` (one commit, unchanged). Diff stat moved only via my own fix: round-1 snapshot `store.py +6 / test_store.py +7`, after my fix `store.py +24 / test_store.py +7`. No commit, no stage, no push.

### (f) Reviewer write operations

**None observed.** Evidence: after round 1 and after the round-2 structure verdict, `git status --porcelain` and `git diff --stat HEAD` were identical to the pre-round snapshot (6/7 insertions). Both round-2 reviewers ran the project's validation command themselves (`python3 test_store.py`) and the round-1 structure reviewer used `PYTHONDONTWRITEBYTECODE=1`; that is execution, not a file write. `__pycache__/` was already present before the loop started, so no untracked-file creation is attributable to a reviewer. No reviewer edited, created, deleted, staged, or committed anything, and no reviewer spawned nested subagents — the round results were trusted and no re-spawn under the integrity defense was required.

Process note: the two round-1 Agent calls were issued in a single message, but the correctness spawn was rejected by a transient model-availability error; I re-issued it immediately, so both round-1 reviewers still ran concurrently. Round 2's two spawns ran in one message as required.

---

## (3) Merged findings

| F-id | Sev | Blocking | Sources | Root cause | Discipline (structure) | Lifecycle |
|---|---|---|---|---|---|---|
| F001 | P1 | true | correctness C1 (r1) + structure S2 phantom-clause half (r1) | `key not in self._data` qualifier made the sys: guard fire only where it was already a no-op — present sys: keys stayed readable/deletable/audit-logged | material improvement (contributing half) | RESOLVED (r2) |
| F002 | P2 | false | correctness C2 (r1) + structure S2 sentinel half (r1) | hardcoded `"<protected>"` overrode the caller's `default`, an undocumented third return channel | material improvement (contributing half) | RESOLVED (r2 — contract documented, named constant) |
| F003 | P2 | false | correctness C3 (r1) | `key.startswith(...)` called before any type check → non-string keys regressed to `AttributeError` | — | RESOLVED (r2) |
| F004 | P1 | true (structural) | structure S1 (r1) | protection policy had no single definition site: three divergent guards + duplicated literals | **blocking regression** | RESOLVED (r2 — `SYS_PREFIX` + `_is_sys`) |
| F005 | P3 | false | correctness C1 (r2) | rejected-write atomicity, default-override, and non-string-key contracts unpinned by tests | — | OPEN (residual; P3 is never auto-fixed and never blocks PASS) |

Round-2 structure findings' `discipline:` values: none — round 2 returned `findings: []` with three taste-grade items confined to `residual_risks` per the convergence contract. The only structural `discipline` values in the run were round 1's S1 `blocking regression` and S2 `material improvement`.

Key files: `/tmp/arbor-acceptance/fixture-c/store.py` (only file the loop wrote), `/tmp/arbor-acceptance/fixture-c/test_store.py` (untouched by the loop), `/tmp/arbor-acceptance/fixture-c/AGENTS.md` (validation source).
```
