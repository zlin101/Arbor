# scenario-J-maxrounds-live — spawn 2 (full, untruncated)

- description: Round 2 correctness reviewer
- subagent_type: 

## Full prompt

```
You are REVIEWER 1 (correctness) in a dual-review loop. Your rubric is the `dual-review-correctness` skill.

FIRST STEP (do this before anything else): read your rubric in full:
- /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md
- and every file under /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/references/

Then review the change scope below strictly according to that rubric.

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

=======================================================================
SCOPE MATERIALIZATION (identical for both reviewers this round)
=======================================================================

--- Frozen baseline identity ---
repo: /tmp/arbor-acceptance/fixture-j (read-only for you)
scope_type: working-tree
baseline_commit: 28c4eb4 ("base store")  — this is the frozen anchor of the loop
paths in scope: store.py, test_store.py
include_staged: true, include_unstaged: true
(untracked `__pycache__/` is a Python bytecode artifact, out of scope)

--- Project instructions (AGENTS.md, verbatim) ---
# Project Instructions

## Validation
- Required validation command: `python3 test_store.py` — must exit 0.

## Rules
- Never commit; work happens in the working tree.
- Python 3 standard library only. No new dependencies.

--- Full current diff vs baseline (git diff HEAD, current state) ---
diff --git a/store.py b/store.py
index c87bfe3..18150ec 100644
--- a/store.py
+++ b/store.py
@@ -13,6 +13,21 @@ class Store:
     def get(self, key, default=None):
         return self._data.get(key, default)
 
+    def batch_delete(self, keys):
+        missing = [key for key in keys if key not in self._data]
+        if missing:
+            raise KeyError(missing[0])
+        for key in keys:
+            self.delete(key)
+
+    def snapshot(self):
+        return dict(self._data)
+
+    def history(self, limit):
+        if limit <= 0:
+            return []
+        return self.audit[-limit:]
+
     def delete(self, key):
         if key in self._data:
             del self._data[key]
diff --git a/test_store.py b/test_store.py
index 33a2c46..a1dfe63 100644
--- a/test_store.py
+++ b/test_store.py
@@ -14,6 +14,50 @@ class TestStore(unittest.TestCase):
         self.assertIsNone(s.get("missing"))
         self.assertEqual(s.get("missing", 0), 0)
 
+    def test_batch_delete(self):
+        s = Store()
+        s.set("a", 1); s.set("b", 2)
+        s.batch_delete(["a", "b"])
+        self.assertIsNone(s.get("a")); self.assertIsNone(s.get("b"))
+
+    def test_snapshot(self):
+        s = Store()
+        s.set("a", 1)
+        snap = s.snapshot()
+        self.assertEqual(snap["a"], 1)
+
+    def test_batch_delete_missing_key_is_atomic(self):
+        s = Store()
+        s.set("a", 1)
+        s.set("b", 2)
+        with self.assertRaises(KeyError):
+            s.batch_delete(["a", "missing"])
+        self.assertEqual(s.get("a"), 1)
+        self.assertEqual(s.get("b"), 2)
+        self.assertEqual(s.history(10), [("set", "a"), ("set", "b")])
+
+    def test_snapshot_is_isolated(self):
+        s = Store()
+        s.set("a", 1)
+        snap = s.snapshot()
+        s.set("b", 2)
+        self.assertNotIn("b", snap)
+        snap["a"] = 999
+        self.assertEqual(s.get("a"), 1)
+
+    def test_history_non_positive_limit(self):
+        s = Store()
+        s.set("a", 1)
+        s.set("b", 2)
+        self.assertEqual(s.history(0), [])
+        self.assertEqual(s.history(-1), [])
+        self.assertEqual(s.history(1), [("set", "b")])
+
+    def test_history(self):
+        s = Store()
+        s.set("a", 1)
+        self.assertEqual(len(s.history(1)), 1)
+
     def test_delete(self):
         s = Store()
         s.set("a", 1)

--- Full current contents of changed file: store.py ---
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

    def batch_delete(self, keys):
        missing = [key for key in keys if key not in self._data]
        if missing:
            raise KeyError(missing[0])
        for key in keys:
            self.delete(key)

    def snapshot(self):
        return dict(self._data)

    def history(self, limit):
        if limit <= 0:
            return []
        return self.audit[-limit:]

    def delete(self, key):
        if key in self._data:
            del self._data[key]
            self.audit.append(("delete", key))
            return True
        return False

--- Full current contents of changed file: test_store.py ---
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

    def test_batch_delete(self):
        s = Store()
        s.set("a", 1); s.set("b", 2)
        s.batch_delete(["a", "b"])
        self.assertIsNone(s.get("a")); self.assertIsNone(s.get("b"))

    def test_snapshot(self):
        s = Store()
        s.set("a", 1)
        snap = s.snapshot()
        self.assertEqual(snap["a"], 1)

    def test_batch_delete_missing_key_is_atomic(self):
        s = Store()
        s.set("a", 1)
        s.set("b", 2)
        with self.assertRaises(KeyError):
            s.batch_delete(["a", "missing"])
        self.assertEqual(s.get("a"), 1)
        self.assertEqual(s.get("b"), 2)
        self.assertEqual(s.history(10), [("set", "a"), ("set", "b")])

    def test_snapshot_is_isolated(self):
        s = Store()
        s.set("a", 1)
        snap = s.snapshot()
        s.set("b", 2)
        self.assertNotIn("b", snap)
        snap["a"] = 999
        self.assertEqual(s.get("a"), 1)

    def test_history_non_positive_limit(self):
        s = Store()
        s.set("a", 1)
        s.set("b", 2)
        self.assertEqual(s.history(0), [])
        self.assertEqual(s.history(-1), [])
        self.assertEqual(s.history(1), [("set", "b")])

    def test_history(self):
        s = Store()
        s.set("a", 1)
        self.assertEqual(len(s.history(1)), 1)

    def test_delete(self):
        s = Store()
        s.set("a", 1)
        self.assertTrue(s.delete("a"))
        self.assertIsNone(s.get("a"))
        self.assertFalse(s.delete("a"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

=======================================================================
OUTPUT CONTRACT — return your verdict as exactly this YAML envelope, nothing else
=======================================================================

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

Rules that apply to you (correctness reviewer):
- `verdict: PASS` with an empty findings list is a valid, expected outcome.
- Set `blocking: true` for P0/P1 findings (and a P2 only when it directly endangers the change's correctness).
- Do NOT generate global ids, do not merge another reviewer's findings, do not compare notes.
- The `discipline:` field is structure-reviewer-only; omit it.
- `residual_risks:` may be empty; a clean review must still state residual risk.

Return findings to the parent only. Do not write or modify any file.
```
