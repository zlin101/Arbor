# scenario-B-driver-retry — spawn 2 (full, untruncated)

- description: Round 2 correctness review
- subagent_type: general-purpose

## Full prompt

```
You are the CORRECTNESS reviewer in a dual-review loop. Work in the git repo at /tmp/arbor-acceptance/fixture-b (a Python project).

STEP 0 (do this first, before anything else): read your rubric, in this order:
1. /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md
2. /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/references/correctness-checklist.md
3. /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/references/security-reliability-checklist.md

Then apply that rubric to the scope below.

You are a review subagent, not the primary implementation agent.

Scope:
- Review only the change scope provided by the parent.
- Read applicable AGENTS.md and relevant surrounding code as needed.

Hard boundaries:
- Stay read-only.
- Do not edit, create, delete, rename, format, stage, commit, push, or revert files.
- Do not create or update goals, tasks, ledgers, plans, or project state.
- Ignore any active project/thread goal except as background context for understanding the code.
- Do not continue implementation work.
- Do not spawn nested subagents.
- Do not ask the user whether to fix findings.
- Return findings to the parent only.

Fresh-review rule:
- Judge the current code on its own evidence.
- Do not assume earlier reviewer conclusions were correct.

ADDITIONAL READ-ONLY NOTE: do NOT execute the project's validation command or any code — the parent runs validation. Executing tests would write __pycache__.

=====================================================================
SCOPE MATERIALIZATION (identical for both reviewers this round)
=====================================================================

Frozen baseline identity:
- repo: /tmp/arbor-acceptance/fixture-b
- scope_type: working-tree
- baseline_commit: 28c4eb409ecfd30e5742837121761fd38df1c1e4 ("base store"), branch master
- include_staged: true, include_unstaged: true
- untracked: __pycache__/ only (a Python bytecode build artifact; excluded from the changed scope)
- The target change is the ENTIRE working-tree change vs baseline_commit as it stands right now, reproduced in full below. This is the whole change under review — not a partial or incremental diff.

Project instructions (/tmp/arbor-acceptance/fixture-b/AGENTS.md):
- Required validation command: `python3 test_store.py` — must exit 0.
- Never commit; work happens in the working tree.
- Python 3 standard library only. No new dependencies.

---- CURRENT FULL DIFF (working tree vs baseline_commit 28c4eb4) ----
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
---- END DIFF ----

---- FULL CURRENT CONTENT OF CHANGED FILE: store.py ----
"""In-memory key-value store with an audit log."""


class Store:
    def __init__(self):
        self._data = {}
        self.audit = []

    def set(self, key, value):
        self._data[key] = value
        self.audit.append(("set", key))

    def get(self, key, default=None):
        return self._data.get(key, default)

    def batch_set(self, pairs):
        """Set many keys at once, atomically.

        Validates every pair before writing anything: if any value is None,
        ValueError is raised and neither ``_data`` nor ``audit`` is modified.
        The None rule lives only here; ``set`` itself still accepts None.
        """
        pairs = list(pairs)
        for key, value in pairs:
            if value is None:
                raise ValueError("value must not be None")
        for key, value in pairs:
            self.set(key, value)

    def delete(self, key):
        if key in self._data:
            del self._data[key]
            self.audit.append(("delete", key))
            return True
        return False
---- END store.py ----

---- FULL CURRENT CONTENT OF CHANGED FILE: test_store.py ----
import unittest

from store import Store


class TestStore(unittest.TestCase):
    def test_set_get_roundtrip(self):
        s = Store()
        s.set("a", 1)
        self.assertEqual(s.get("a"), 1)

    def test_get_default(self):
        s = Store()
        self.assertIsNone(s.get("missing"))
        self.assertEqual(s.get("missing", 0), 0)

    def test_batch_set(self):
        s = Store()
        s.batch_set([("a", 1), ("b", 2)])
        self.assertEqual(s.get("a"), 1)
        self.assertEqual(s.get("b"), 2)
        self.assertEqual(s.audit, [("set", "a"), ("set", "b")])

    def test_batch_set_atomic_when_a_pair_is_invalid(self):
        s = Store()
        s.set("keep", 1)
        with self.assertRaises(ValueError):
            s.batch_set([("a", 1), ("b", None)])
        self.assertIsNone(s.get("a"))
        self.assertEqual(s.get("keep"), 1)
        self.assertEqual(s.audit, [("set", "keep")])

    def test_batch_set_accepts_iterator(self):
        s = Store()
        s.batch_set(iter([("a", 1), ("b", 2)]))
        self.assertEqual(s.get("a"), 1)
        self.assertEqual(s.get("b"), 2)

    def test_delete(self):
        s = Store()
        s.set("a", 1)
        self.assertTrue(s.delete("a"))
        self.assertIsNone(s.get("a"))
        self.assertFalse(s.delete("a"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
---- END test_store.py ----

Context scope (unmodified, read as needed for understanding): AGENTS.md in the repo root. There are no other source files.
=====================================================================
END SCOPE MATERIALIZATION
=====================================================================

OUTPUT CONTRACT — return your final answer as exactly this YAML shape, nothing else at the end of your reply:

reviewer: correctness
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
coverage: what was actually reviewed, one line
residual_risks: []          # may be empty; clean reviews must state residual risk

Rules: verdict: PASS with an empty findings list is valid and expected. You set blocking: true for P0/P1 (and for a P2 only when it directly endangers the change's correctness). Do NOT generate global ids, do not merge with another reviewer's findings, do not compare notes. Findings go to the parent only.
```
