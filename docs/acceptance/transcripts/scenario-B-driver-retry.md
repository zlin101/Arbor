# scenario-B-driver-retry

- task: ac1eebdfd7fcd3f96
- evidence class: LIVE-LOOP
- assistant text blocks: 16
- reviewer spawns: 4 (full prompts in spawn3-full.md files)

## Spawns

0. **Round 1 correctness review** (general-purpose) — full prompt: `scenario-B-driver-retry-spawn0-full.md`
1. **Round 1 structure review** (general-purpose) — full prompt: `scenario-B-driver-retry-spawn1-full.md`
2. **Round 2 correctness review** (general-purpose) — full prompt: `scenario-B-driver-retry-spawn2-full.md`
3. **Round 2 structure review** (general-purpose) — full prompt: `scenario-B-driver-retry-spawn3-full.md`

## Final assistant output (verbatim)

```
Both rounds complete, gate met. Final report below.

---

# 1. Final user-facing report

```text
Dual Review Loop: PASS

Rounds: 2/3

Resolved
- F001 [P1] batch_set applies pairs before validating them, leaving partial writes and phantom audit entries on failure
- F002 [P2] batch_set duplicates set's write path and splits the None invariant across two entry points
- F003 [P2] only the happy path is tested — error path and audit side effects unverified

Residual non-blocking
- F004 [P2] docstring's "atomically" over-claims: in-loop failures other than None still leave partial writes
- F005 [P3] passing a dict instead of a pair sequence unpacks its keys and can silently write wrong data

Validation
- python3 test_store.py: PASS

Review coverage
- correctness reviewer: FINDINGS (round 2 — two non-blocking residuals only; gate met)
- structural reviewer: PASS

No commit or push was performed.
```

Note on one line: `output-format.md` hardcodes "correctness reviewer: PASS". Round 2's correctness reviewer returned `verdict: FINDINGS` carrying only non-blocking P2/P3 residuals, so I rendered the literal verdict rather than a false PASS.

---

# 2. EVIDENCE

## (a) Round-1 reviewer verdict envelopes (verbatim)

Correctness reviewer:

```yaml
reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P1
    blocking: true
    category: correctness
    location:
      file: store.py
      line: 16-21
      symbol: Store.batch_set
    title: batch_set is not atomic — a mid-batch ValueError leaves partially applied data and audit entries
    problem: The None validation runs inside the mutation loop, so earlier pairs are committed to _data and audited before a later pair can fail. There is no rollback, so a raised ValueError leaves the store in a partially applied state.
    evidence: For s.batch_set([("a", 1), ("b", None)]), iteration 1 executes s._data["a"] = 1 and s.audit.append(("set", "a")); iteration 2 raises ValueError("value must not be None") at line 19. After the exception, s.get("a") == 1 and s.audit == [("set", "a")] even though the batch call failed. The same applies to any later failure mode (unhashable key raising TypeError mid-loop). This is the exact "first steps committed before a later step can fail, no rollback" pattern; the module's distinguishing feature is its audit log, which now records writes belonging to an operation the caller saw fail.
    impact: A caller that catches the error (or retries the batch) cannot tell which keys were applied, cannot undo them, and the audit log — the module's stated purpose — is left asserting sets that the caller believes did not happen. Retry of the same batch after the failure would re-apply the prefix and still never reach the tail pairs.
    recommended_direction: Validate the whole batch first (one pass rejecting any None) before mutating _data/audit in a second pass; or delegate each pair to the existing self.set(key, value) inside a try that restores prior state on failure. Pin the chosen semantics with a test that raises mid-batch and asserts the resulting _data/audit state.
  - local_id: C2
    severity: P2
    blocking: false
    category: correctness
    location:
      file: store.py
      line: 9-11, 16-21
      symbol: Store.set / Store.batch_set
    title: Divergent validation between the two write paths — set accepts None, batch_set rejects it
    problem: batch_set introduces a value constraint (value is None raises ValueError) that the pre-existing single-write path set does not have, so the same logical operation behaves differently depending on which path is used, while both emit the identical ("set", key) audit event.
    evidence: s.set("a", None) succeeds and s.get("a") is None; s.batch_set([("a", None)]) raises ValueError. Both methods append the indistinguishable tuple ("set", "a") to audit, so audit consumers cannot tell which contract produced an entry.
    impact: Callers cannot reason about a uniform store contract; a batch refactored into per-key set calls (or vice versa) silently changes which inputs are legal. The duplicated write path has already diverged on its first edit, which is the mechanism behind C1.
    recommended_direction: Decide once where the None rule lives — either validate in set and have batch_set call set per pair (contract unifies and C1 shrinks), or drop the None check from batch_set to match set. A one-line docstring stating the contract would suffice if divergence is intended.
  - local_id: C3
    severity: P2
    blocking: false
    category: tests
    location:
      file: test_store.py
      line: 17-22
      symbol: TestStore.test_batch_set
    title: Only the happy path is tested; error path and audit behavior are unverified
    problem: test_batch_set asserts only that two valid pairs round-trip. Nothing covers the ValueError path, the resulting store state after a mid-batch failure, or that batch_set appends to audit at all — the areas where C1 and C2 live.
    evidence: The added test makes two assertions, both against s.get after s.batch_set([("a", 1), ("b", 2)]). No test passes a None value, no test inspects s.audit, and no test asserts the exception type. The riskiest behavior of the change (state after a raise) is entirely unobserved by the suite.
    impact: The change's failure semantics are untested, so a fix to C1 could regress silently or the current partial-application behavior could be unknowingly enshrined; the audit side effect of the new method is unverified.
    recommended_direction: Smallest addition: one test asserting with self.assertRaises(ValueError): s.batch_set([("a", 1), ("b", None)]) plus assertions pinning the intended post-failure state of s._data and s.audit, and one assertion in the happy-path test that s.audit == [("set", "a"), ("set", "b")].
coverage: Reviewed the full working-tree diff (Store.batch_set in store.py, test_batch_set in test_store.py) against the correctness and security/reliability checklists; confirmed via grep that these are the only two source files and batch_set/audit have no other consumers; did not execute the validation command (parent runs it — statically reasoned the suite exits 0 since the new test uses only valid values and pre-existing tests are untouched by the method insertion).
residual_risks:
  - "Thread safety not asserted: the module has no locking and batch_set is a multi-step compound mutation of _data/audit, so concurrent callers can interleave; this is a pre-existing property shared with set/delete (set is also a two-step data+audit mutation) and no concurrency exists in the repo, so it is noted as residual risk rather than a finding."
  - Validation exit status was reasoned statically, not executed, per the read-only constraint.
```

Structure reviewer:

```yaml
reviewer: structure
verdict: FINDINGS
findings:
  - local_id: S1
    severity: P2
    blocking: false
    category: abstraction
    location:
      file: store.py
      line: 16-21
      symbol: Store.batch_set
    title: batch_set reimplements set's write path and splits the None invariant across two entry points
    problem: The diff adds a second public write path that copies set's body (self._data[key] = value; self.audit.append(("set", key))) instead of delegating to set, and attaches a None-rejection rule that exists only on this path. Store now has two ways to write a key with different validation contracts over the same _data/audit state, and the invariant is enforced mid-loop rather than at the boundary, so a rejected pair leaves earlier pairs of the same batch already applied to data and audit.
    evidence: store.py:9-11 (set writes data then appends audit) vs store.py:20-21 (batch_set repeats the identical pair); store.py:18-19 raises ValueError between iterations while set("a", None) is accepted. No test exercises the ValueError path, so the divergent rule is unanchored to any stated contract.
    impact: A maintainer can no longer assume writes flow through one choke point or that None is rejected consistently; any future rule added to set (validation, audit shape, normalization) silently bypasses batch_set, and the divergence must be remembered rather than read.
    recommended_direction: Keep the None guard as up-front validation of pairs, then delegate each write to self.set(key, value) so set remains the single write path; if batch atomicity is intended, validate all pairs before applying any.
    discipline: material improvement
coverage: Full working-tree diff vs 28c4eb4 (store.py batch_set, test_store.py test_batch_set) against the structural checklist; files read, nothing executed.
residual_risks:
  - Taste, not findings: batch_set is placed between get and delete rather than adjacent to set; AGENTS.md imposes no structural constraint the change violates.
  - Out of role, left to the correctness reviewer: the untested ValueError path and the half-applied batch on mid-loop failure (behavioral consequences of S1's placement, not re-raised here as bugs).
```

## (b) What I fixed + exact validation command and exit code

Single writer (me). One coherent root-cause batch, ordered P1 → low-risk in-scope P2:

- `/tmp/arbor-acceptance/fixture-b/store.py` — `batch_set` rewritten to materialize `pairs = list(pairs)`, then a validate-all pass (None check), then an apply pass that delegates each write to `self.set(key, value)` instead of duplicating the write+audit body. Docstring states the contract explicitly, including that the None rule lives only on `batch_set`. Fixes F001 (validation no longer interleaved with mutation — a rejected batch leaves `_data` and `audit` untouched; also preserves iterator support, which the pre-pass would otherwise have consumed) and F002 (single write choke point, documented contract).
- `/tmp/arbor-acceptance/fixture-b/test_store.py` — added `s.audit` assertion to `test_batch_set`; added `test_batch_set_atomic_when_a_pair_is_invalid` (asserts `ValueError`, and that `_data` and `audit` are unchanged after the raise); added `test_batch_set_accepts_iterator`. Fixes F003.

Validation command from `/tmp/arbor-acceptance/fixture-b/AGENTS.md`: `python3 test_store.py` → **EXIT_CODE=0** (6 tests, OK). Run immediately after the fix batch, and re-run at the end on the identical state → EXIT_CODE=0 again.

## (c) Scope materialization given to round-2 reviewers

**It covered the FULL change vs HEAD — baseline commit `28c4eb409ecfd30e5742837121761fd38df1c1e4` plus my fix — not only the fix diff.** Both round-2 reviewers received the byte-identical materialization containing: frozen baseline identity (commit + scope_type working-tree + include flags); the project instructions from AGENTS.md; the full current `git diff HEAD` (shown below, 20-line store.py hunk + 28-line test hunk); and the full current contents of both changed files. No prior-round findings were passed.

```diff
diff --git a/store.py b/store.py
index c87bfe3..1b2d683 100644
--- a/store.py
+++ b/store.py
@@ -13,6 +13,20 @@ class Store:
     def get(self, key, default=None):
         return self._data.get(key, default)
 
+    def batch_set(self, pairs):
+        """Set many keys at once, atomically.
+
+        Validates every pair before writing anything: if any value is None,
+        ValueError is raised and neither ``_data`` nor ``audit`` is modified.
+        The None rule lives only here; ``set`` itself still accepts None.
+        """
+        pairs = list(pairs)
+        for key, value in pairs:
+            if value is None:
+                raise ValueError("value must not be None")
+        for key, value in pairs:
+            self.set(key, value)
+
     def delete(self, key):
         if key in self._data:
             del self._data[key]
diff --git a/test_store.py b/test_store.py
index 33a2c46..7498d49 100644
--- a/test_store.py
+++ b/test_store.py
@@ -14,6 +14,28 @@ class TestStore(unittest.TestCase):
         self.assertIsNone(s.get("missing"))
         self.assertEqual(s.get("missing", 0), 0)
 
+    def test_batch_set(self):
+        s = Store()
+        s.batch_set([("a", 1), ("b", 2)])
+        self.assertEqual(s.get("a"), 1)
+        self.assertEqual(s.get("b"), 2)
+        self.assertEqual(s.audit, [("set", "a"), ("set", "b")])
+
+    def test_batch_set_atomic_when_a_pair_is_invalid(self):
+        s = Store()
+        s.set("keep", 1)
+        with self.assertRaises(ValueError):
+            s.batch_set([("a", 1), ("b", None)])
+        self.assertIsNone(s.get("a"))
+        self.assertEqual(s.get("keep"), 1)
+        self.assertEqual(s.audit, [("set", "keep")])
+
+    def test_batch_set_accepts_iterator(self):
+        s = Store()
+        s.batch_set(iter([("a", 1), ("b", 2)]))
+        self.assertEqual(s.get("a"), 1)
+        self.assertEqual(s.get("b"), 2)
+
     def test_delete(self):
         s = Store()
         s.set("a", 1)
```

Defect in my materialization, disclosed: I labeled the branch "master"; the fixture is on branch `main`. HEAD equaled the stated baseline commit `28c4eb4` exactly, so the reviewed diff was unaffected — the round-2 correctness reviewer caught and noted this.

## (d) Round-2 reviewer verdict envelopes (verbatim)

Correctness reviewer:

```yaml
reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P2
    blocking: false
    category: correctness
    location:
      file: store.py
      line: 16-28
      symbol: Store.batch_set
    title: "Atomicity" over-claims: only the None rule is pre-validated, in-loop failures still leave partial writes
    problem: The docstring says "Set many keys at once, atomically," but the implementation only guarantees atomicity for the failure modes the pre-pass can see (a None value, and pair-unpacking errors). Any exception raised by `self.set` during the write loop commits earlier pairs first.
    evidence: The write loop calls `self.set(key, value)`, which executes `self._data[key] = value`. With an unhashable key — `s.batch_set([("a", 1), (["b"], 2)])` — the pre-pass sees no None and passes, `("a", 1)` is committed to both `_data` and `audit`, then `set(["b"], 2)` raises `TypeError: unhashable type`. State is now `{"a": 1}` / `audit == [("set", "a")]` despite the atomic contract. The docstring's own second sentence scopes the guarantee to the None rule, contradicting its unqualified first sentence.
    impact: A caller relying on the documented atomicity for any failure path gets a partially applied batch with a consistent-looking audit log. No test covers a non-None in-loop failure, so the existing atomicity test cannot catch this class.
    recommended_direction: Either qualify the docstring ("atomic with respect to value validation") or extend the pre-pass to cover the realistic in-loop failure (e.g. call `hash(key)` per pair before writing), and add one test with an unhashable key asserting `_data` and `audit` are unchanged.
  - local_id: C2
    severity: P3
    blocking: false
    category: correctness
    location:
      file: store.py
      line: 23-27
      symbol: Store.batch_set
    title: Passing a dict instead of a pair sequence silently writes wrong keys
    problem: `list(pairs)` on a dict yields its keys, so the natural-but-wrong call shape `batch_set({"ab": 1})` is not rejected — it unpacks the 2-character string.
    evidence: `batch_set({"ab": 1})` becomes `pairs = ["ab"]`; the pre-pass unpacks `"ab"` into `key="a", value="b"`, passes the None check, and stores `"a" -> "b"` with no error. A dict whose keys are single characters (`batch_set({"a": 1})`) instead raises a bare `ValueError: not enough values to unpack`, which does not mention pairs or the actual argument shape.
    impact: The most plausible misuse of this API (key-to-value dict, which is what a key-value store's own vocabulary suggests) either corrupts store contents silently or fails with a misleading error.
    recommended_direction: Validate pair shape in the pre-pass (e.g. reject items that do not unpack to exactly two values with a message naming `pairs`) so a dict argument fails loudly instead of writing wrong data.
coverage: Reviewed the full working-tree diff (Store.batch_set and its three new tests in /tmp/arbor-acceptance/fixture-b/store.py and test_store.py) against both checklists, verified the working tree matches the frozen baseline 28c4eb4, and traced all callers (none outside test_store.py); did not execute python3 test_store.py per the read-only constraint.
residual_risks:
  - "Validation command not executed (read-only constraint); test pass/fail established by static trace only."
  - "batch_set is unsynchronized, so concurrent callers could observe mid-batch state; accepted as a residual because Store makes no thread-safety promise anywhere and no concurrency requirement exists in this codebase."
  - "Scope metadata listed branch master; the checkout is on branch main, but HEAD equals the stated baseline commit 28c4eb4 exactly, so the reviewed diff is unaffected."
  - "Unbounded audit-log growth is pre-existing baseline behavior, not introduced by this change."
```

Structure reviewer:

```yaml
reviewer: structure
verdict: PASS
findings: []
coverage: Reviewed store.py and test_store.py in full (new batch_set method + 3 tests) against baseline 28c4eb4 and AGENTS.md; confirmed no other source files exist in scope.
residual_risks:
  - Taste-only, not findings: the validation loop could collapse to `any(v is None for _, v in pairs)` and its `key` binding is unused; structurally, the two-phase design validates only the None precondition, so the docstring's "atomically" is best-effort rather than guaranteed against other apply-phase failures (e.g. unhashable keys) — contract territory for the correctness reviewer.
```

## (e) Git state before and after the run (no commits)

Before:
```
$ git -C /tmp/arbor-acceptance/fixture-b status --porcelain
 M store.py
 M test_store.py
?? __pycache__/
$ git -C /tmp/arbor-acceptance/fixture-b log --oneline
28c4eb4 base store
```

After:
```
$ git -C /tmp/arbor-acceptance/fixture-b status --porcelain
 M store.py
 M test_store.py
?? __pycache__/
$ git -C /tmp/arbor-acceptance/fixture-b log --oneline
28c4eb4 base store
```

Identical. One commit before and after; `git diff --cached --stat` empty (nothing staged). No commit, push, or branch action.

## (f) Write operations observed from reviewers

**None.** md5 of `store.py`/`test_store.py` was identical before and after each round (pre-round-1 `625b9c2b…`/`6e706dad…`; post-fix `0f574a43…`/`c19367a1…` unchanged across round 2). `__pycache__/store.cpython-312.pyc` has exactly one mtime, 22:37:14, which is my own validation run (my edits landed 22:37:05/22:37:09) — no `.pyc` was written during either reviewer window, so no reviewer executed code either. The only writes in the entire run were my two Edit calls. F1/F2 reviewer-integrity defenses never fired; no round was discarded.

---

# 3. Merged finding list (F-ids, sources, lifecycle)

| id | sev | blocking | sources | title | lifecycle |
|---|---|---|---|---|---|
| F001 | P1 | yes (R1) | correctness (R1-C1) | `batch_set` applies pairs before validating them → partial writes + phantom audit entries on failure | **RESOLVED** — round 2 did not re-confirm; pinned by `test_batch_set_atomic_when_a_pair_is_invalid`; validation green |
| F002 | P2 | no | correctness (R1-C2) + structure (R1-S1) | `batch_set` duplicates `set`'s write path; None invariant split across two entry points | **RESOLVED** — merged on shared root cause (duplicated write path / split contract); round 2 structure PASS, correctness did not re-raise |
| F003 | P2 | no | correctness (R1-C3) | only happy path tested; error path and audit unverified | **RESOLVED** — error-path and audit assertions added |
| F004 | P2 | no | correctness (R2-C1) | docstring's "atomically" over-claims: non-None in-loop failures still leave partial writes | OPEN — residual non-blocking; raised against my fix's docstring, not a regression of F001 (different root cause) |
| F005 | P3 | no | correctness (R2-C2) | dict passed as `pairs` unpacks its keys → silent wrong writes or misleading error | OPEN — P3 never auto-fixed, never blocks |

Dedupe notes: R1-C2 and R1-S1 merged (same root cause, same ownership boundary, one fix eliminates both). R1-C1 kept separate from that merge despite the same symbol — its root cause is validation interleaved with mutation, not path duplication; the structure reviewer's atomicity remark was supporting evidence only. R2-C1 mapped as related-to-F001 but a new finding, since its target is the docstring's breadth in the new code. Label audit: R1-S1 carried `discipline: material improvement` with `blocking: false` — label supported, no reclassification. Both round-2 reviewers independently flagged the unhashable-key/in-loop-failure territory (correctness as F004, structure as a residual_risks line), and both flagged the unused `key` binding / collapsible loop as taste only.

Convergence gate at end of round 2: P0=0, P1=0, structural blocking=0, `python3 test_store.py` exit 0, no unresolved reviewer conflict → PASS. `strict` was not requested, so F004 stays residual.
```
