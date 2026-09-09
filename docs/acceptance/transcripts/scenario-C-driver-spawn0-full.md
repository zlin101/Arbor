# scenario-C-driver — spawn 0 (full, untruncated)

- description: Round 1 correctness reviewer
- subagent_type: general-purpose

## Full prompt

```
You are the CORRECTNESS REVIEWER in a dual-review loop. You never fix and never write.

FIRST, read your rubric before reviewing anything:
1. /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md
2. Every file in /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/references/ (correctness-checklist.md, security-reliability-checklist.md)

Then apply that rubric to the scope below.

<ISOLATION_CONTRACT>
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
</ISOLATION_CONTRACT>

=== SCOPE MATERIALIZATION ===
scope_type: working-tree
repo: /tmp/arbor-acceptance/fixture-c
baseline_commit: 28c4eb409ecfd30e5742837121761fd38df1c1e4 ("base store")
include_staged: true, include_unstaged: true, include_untracked: true (only untracked path is __pycache__/, build noise)
changed scope: store.py, test_store.py
Everything below is the FULL current change (baseline → current working tree), not a partial fix diff.

--- Project instructions (/tmp/arbor-acceptance/fixture-c/AGENTS.md, verbatim) ---
# Project Instructions

## Validation
- Required validation command: `python3 test_store.py` — must exit 0.

## Rules
- Never commit; work happens in the working tree.
- Python 3 standard library only. No new dependencies.

--- Full diff vs baseline (git diff HEAD) ---
diff --git a/store.py b/store.py
index c87bfe3..c591511 100644
--- a/store.py
+++ b/store.py
@@ -7,13 +7,19 @@ class Store:
         self.audit = []
 
     def set(self, key, value):
+        if key.startswith("sys:"):
+            raise PermissionError("sys: keys are read-only")
         self._data[key] = value
         self.audit.append(("set", key))
 
     def get(self, key, default=None):
+        if key.startswith("sys:") and key not in self._data:
+            return "<protected>"
         return self._data.get(key, default)
 
     def delete(self, key):
+        if key.startswith("sys:") and key not in self._data:
+            return False
         if key in self._data:
             del self._data[key]
             self.audit.append(("delete", key))
diff --git a/test_store.py b/test_store.py
index 33a2c46..126dbc6 100644
--- a/test_store.py
+++ b/test_store.py
@@ -14,6 +14,13 @@ class TestStore(unittest.TestCase):
         self.assertIsNone(s.get("missing"))
         self.assertEqual(s.get("missing", 0), 0)
 
+    def test_sys_keys(self):
+        s = Store()
+        with self.assertRaises(PermissionError):
+            s.set("sys:config", 1)
+        self.assertEqual(s.get("sys:missing"), "<protected>")
+        self.assertFalse(s.delete("sys:missing"))
+
     def test_delete(self):
         s = Store()
         s.set("a", 1)

--- Current full contents: /tmp/arbor-acceptance/fixture-c/store.py ---
"""In-memory key-value store with an audit log."""


class Store:
    def __init__(self):
        self._data = {}
        self.audit = []

    def set(self, key, value):
        if key.startswith("sys:"):
            raise PermissionError("sys: keys are read-only")
        self._data[key] = value
        self.audit.append(("set", key))

    def get(self, key, default=None):
        if key.startswith("sys:") and key not in self._data:
            return "<protected>"
        return self._data.get(key, default)

    def delete(self, key):
        if key.startswith("sys:") and key not in self._data:
            return False
        if key in self._data:
            del self._data[key]
            self.audit.append(("delete", key))
            return True
        return False

--- Current full contents: /tmp/arbor-acceptance/fixture-c/test_store.py ---
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

    def test_sys_keys(self):
        s = Store()
        with self.assertRaises(PermissionError):
            s.set("sys:config", 1)
        self.assertEqual(s.get("sys:missing"), "<protected>")
        self.assertFalse(s.delete("sys:missing"))

    def test_delete(self):
        s = Store()
        s.set("a", 1)
        self.assertTrue(s.delete("a"))
        self.assertIsNone(s.get("a"))
        self.assertFalse(s.delete("a"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
=== END SCOPE MATERIALIZATION ===

You may read other files in the repo as context, but findings may only be raised against the changed scope above.

OUTPUT CONTRACT — return to the parent only, exactly this YAML envelope:

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

Rules: `verdict: PASS` with an empty findings list is valid. Set `blocking: true` for P0/P1 findings, and for a P2 only when it directly endangers the change's correctness. Do not generate global ids, do not merge with another reviewer's findings, do not compare notes. Return the YAML envelope as your final message.
```
