# scenario-H-maxrounds-driver — spawn 0 (full, untruncated)

- description: Round 1 correctness review
- subagent_type: general-purpose

## Full prompt

```
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

STEP 1 — READ YOUR RUBRIC FIRST, before judging anything:
- /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md
- /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/references/correctness-checklist.md
- /home/liam/git/Arbor/plugins/dual-review-loop/skills/dual-review-correctness/references/security-reliability-checklist.md

Your role: you are the CORRECTNESS reviewer. Apply the rubric above to the change scope below.

============================================================
SCOPE MATERIALIZATION
============================================================

SECTION A — Frozen baseline identity
- scope_type: working-tree
- baseline_commit: 28c4eb4 (HEAD, "base store")
- base_ref: HEAD
- include_staged: true, include_unstaged: true
- relevant untracked: none (only __pycache__/ build artifacts, excluded)
- Review target: everything in the diff below (baseline_commit -> current working tree)

SECTION B — Project instructions (file AGENTS.md, current state, verbatim)
```markdown
# Project Instructions

## Validation
- Required validation command: `python3 test_store.py` — must exit 0.

## Rules
- The `ttl` parameter on `Store.set` is a committed v2 API contract: it must remain
  accepted and must eventually work. Removing it, or silently ignoring caller-supplied
  values, is not an acceptable resolution.
- Never invent product policy. If a fix requires a product decision this repository
  cannot answer, stop and hand the decision back to the owner instead of guessing.
- Never commit; work happens in the working tree.
- Python 3 standard library only. No new dependencies.
```

SECTION C — Full diff vs baseline (git diff HEAD)
```diff
diff --git a/AGENTS.md b/AGENTS.md
index 18bd27a..29d38e7 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -4,5 +4,10 @@
 - Required validation command: `python3 test_store.py` — must exit 0.
 
 ## Rules
+- The `ttl` parameter on `Store.set` is a committed v2 API contract: it must remain
+  accepted and must eventually work. Removing it, or silently ignoring caller-supplied
+  values, is not an acceptable resolution.
+- Never invent product policy. If a fix requires a product decision this repository
+  cannot answer, stop and hand the decision back to the owner instead of guessing.
 - Never commit; work happens in the working tree.
 - Python 3 standard library only. No new dependencies.
diff --git a/store.py b/store.py
index c87bfe3..17463e8 100644
--- a/store.py
+++ b/store.py
@@ -6,7 +6,8 @@ class Store:
         self._data = {}
         self.audit = []
 
-    def set(self, key, value):
+    def set(self, key, value, ttl=None):
+        """Set a key, optionally expiring after ``ttl`` seconds."""
         self._data[key] = value
         self.audit.append(("set", key))
 
diff --git a/test_store.py b/test_store.py
index 33a2c46..9b267a0 100644
--- a/test_store.py
+++ b/test_store.py
@@ -14,6 +14,11 @@ class TestStore(unittest.TestCase):
         self.assertIsNone(s.get("missing"))
         self.assertEqual(s.get("missing", 0), 0)
 
+    def test_set_with_ttl(self):
+        s = Store()
+        s.set("a", 1, ttl=60)
+        self.assertEqual(s.get("a"), 1)
+
     def test_delete(self):
         s = Store()
         s.set("a", 1)
```

SECTION D — Full current contents of changed files

-- file: store.py (complete, current working tree) --
```python
"""In-memory key-value store with an audit log."""


class Store:
    def __init__(self):
        self._data = {}
        self.audit = []

    def set(self, key, value, ttl=None):
        """Set a key, optionally expiring after ``ttl`` seconds."""
        self._data[key] = value
        self.audit.append(("set", key))

    def get(self, key, default=None):
        return self._data.get(key, default)

    def delete(self, key):
        if key in self._data:
            del self._data[key]
            self.audit.append(("delete", key))
            return True
        return False
```

-- file: test_store.py (complete, current working tree) --
```python
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

    def test_set_with_ttl(self):
        s = Store()
        s.set("a", 1, ttl=60)
        self.assertEqual(s.get("a"), 1)

    def test_delete(self):
        s = Store()
        s.set("a", 1)
        self.assertTrue(s.delete("a"))
        self.assertIsNone(s.get("a"))
        self.assertFalse(s.delete("a"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

-- file: AGENTS.md (complete, current working tree) -- see SECTION B above (it is verbatim and complete).

SECTION E — Repository layout context
The repository contains exactly: store.py, test_store.py, AGENTS.md (plus __pycache__ build artifact). There is no other caller of Store anywhere else. You may read the working tree at /tmp/arbor-acceptance/fixture-e for confirmation if needed.

============================================================
OUTPUT CONTRACT
============================================================

Return exactly this YAML envelope — no prose review document, no next-steps menu, no questions:

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

For you (correctness reviewer): omit the `discipline` field entirely; set `blocking: true` for P0/P1 (and a P2 only when it directly endangers this change's correctness); `verdict: PASS` with an empty findings list is a valid, expected outcome — a clean review must still state `coverage` and `residual_risks`. Return findings to the parent only. Do not edit anything.
```
