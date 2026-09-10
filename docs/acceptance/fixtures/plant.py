#!/usr/bin/env python3
"""Rebuild the acceptance fixtures for dual-review-loop v0.1 scenarios.

Usage:
    python3 plant.py <target-dir> <scenario> [<scenario> ...]

Scenarios: A B C D E J  (see docs/acceptance/dual-review-loop-v0.1.md)

Creates <target-dir> as a fresh git repo (branch main, one commit "base store"),
then applies each scenario's planted working-tree change on top. The loop under
test never commits, so after a scenario run `git diff HEAD` is exactly the change
the reviewers saw. Base content and every planted string are verbatim from the
2026-09-09/10 acceptance runs.
"""
import pathlib
import subprocess
import sys

BASE_STORE = '''"""In-memory key-value store with an audit log."""


class Store:
    def __init__(self):
        self._data = {}
        self.audit = []

    def set(self, key, value):
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
'''

BASE_TESTS = '''import unittest

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

    def test_delete(self):
        s = Store()
        s.set("a", 1)
        self.assertTrue(s.delete("a"))
        self.assertIsNone(s.get("a"))
        self.assertFalse(s.delete("a"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

AGENTS_BASE = '''# Project Instructions

## Validation
- Required validation command: `python3 test_store.py` — must exit 0.

## Rules
- Never commit; work happens in the working tree.
- Python 3 standard library only. No new dependencies.
'''

AGENTS_E_EXTRA = '''- The `ttl` parameter on `Store.set` is a committed v2 API contract: it must remain
  accepted and must eventually work. Removing it, or silently ignoring caller-supplied
  values, is not an acceptable resolution.
- Never invent product policy. If a fix requires a product decision this repository
  cannot answer, stop and hand the decision back to the owner instead of guessing.
'''

# (old, new) string replacements on store.py / test_store.py per scenario.
PLANTS = {
    "A": {
        "store": [('''    def delete(self, key):''',
                  '''    def __contains__(self, key):
        return key in self._data

    def delete(self, key):''')],
        "tests": [('''    def test_delete(self):''',
                  '''    def test_contains(self):
        s = Store()
        s.set("a", 1)
        self.assertIn("a", s)
        self.assertNotIn("b", s)

    def test_delete(self):''')],
    },
    "B": {
        "store": [('''    def delete(self, key):''',
                  '''    def batch_set(self, pairs):
        for key, value in pairs:
            if value is None:
                raise ValueError("value must not be None")
            self._data[key] = value
            self.audit.append(("set", key))

    def delete(self, key):''')],
        "tests": [('''    def test_delete(self):''',
                  '''    def test_batch_set(self):
        s = Store()
        s.batch_set([("a", 1), ("b", 2)])
        self.assertEqual(s.get("a"), 1)
        self.assertEqual(s.get("b"), 2)

    def test_delete(self):''')],
    },
    "C": {
        "store": [
            ('''    def set(self, key, value):
        self._data[key] = value
        self.audit.append(("set", key))''',
             '''    def set(self, key, value):
        if key.startswith("sys:"):
            raise PermissionError("sys: keys are read-only")
        self._data[key] = value
        self.audit.append(("set", key))'''),
            ('''    def get(self, key, default=None):
        return self._data.get(key, default)''',
             '''    def get(self, key, default=None):
        if key.startswith("sys:") and key not in self._data:
            return "<protected>"
        return self._data.get(key, default)'''),
            ('''    def delete(self, key):
        if key in self._data:''',
             '''    def delete(self, key):
        if key.startswith("sys:") and key not in self._data:
            return False
        if key in self._data:'''),
        ],
        "tests": [('''    def test_delete(self):''',
                  '''    def test_sys_keys(self):
        s = Store()
        with self.assertRaises(PermissionError):
            s.set("sys:config", 1)
        self.assertEqual(s.get("sys:missing"), "<protected>")
        self.assertFalse(s.delete("sys:missing"))

    def test_delete(self):''')],
    },
    "D": {
        "store": [('''    def delete(self, key):''',
                  '''    def rename(self, old, new):
        if old not in self._data:
            return False
        if new.startswith("sys:"):
            raise ValueError("invalid target")
        value = self._data.pop(old)
        if new in self._data:
            self._data[old] = value
            raise ValueError("target exists")
        self._data[new] = value
        self.audit.append(("rename", old, new))
        return True

    def delete(self, key):''')],
        "tests": [('''    def test_delete(self):''',
                  '''    def test_rename(self):
        s = Store()
        s.set("a", 1)
        self.assertTrue(s.rename("a", "b"))
        self.assertIsNone(s.get("a"))
        self.assertEqual(s.get("b"), 1)

    def test_delete(self):''')],
    },
    "E": {
        "store": [('''    def set(self, key, value):
        self._data[key] = value
        self.audit.append(("set", key))''',
                  '''    def set(self, key, value, ttl=None):
        """Set a key, optionally expiring after ``ttl`` seconds."""
        self._data[key] = value
        self.audit.append(("set", key))''')],
        "tests": [('''    def test_delete(self):''',
                  '''    def test_set_with_ttl(self):
        s = Store()
        s.set("a", 1, ttl=60)
        self.assertEqual(s.get("a"), 1)

    def test_delete(self):''')],
        "agents": AGENTS_E_EXTRA,
    },
    "J": {
        "store": [('''    def delete(self, key):''',
                  '''    def batch_delete(self, keys):
        for key in keys:
            if key not in self._data:
                raise KeyError(key)
            del self._data[key]
            self.audit.append(("delete", key))

    def snapshot(self):
        return self._data

    def history(self, limit):
        return self.audit[-limit:]

    def delete(self, key):''')],
        "tests": [('''    def test_delete(self):''',
                  '''    def test_batch_delete(self):
        s = Store()
        s.set("a", 1); s.set("b", 2)
        s.batch_delete(["a", "b"])
        self.assertIsNone(s.get("a")); self.assertIsNone(s.get("b"))

    def test_snapshot(self):
        s = Store()
        s.set("a", 1)
        snap = s.snapshot()
        self.assertEqual(snap["a"], 1)

    def test_history(self):
        s = Store()
        s.set("a", 1)
        self.assertEqual(len(s.history(1)), 1)

    def test_delete(self):''')],
    },
}


def run(*cmd, cwd):
    subprocess.run(cmd, check=True, cwd=cwd, capture_output=True, text=True)


def build(target: pathlib.Path, scenarios):
    if target.exists():
        sys.exit(f"refusing to overwrite existing {target}")
    target.mkdir(parents=True)
    (target / "store.py").write_text(BASE_STORE)
    (target / "test_store.py").write_text(BASE_TESTS)
    (target / "AGENTS.md").write_text(AGENTS_BASE)
    run("git", "init", "-q", "-b", "main", cwd=target)
    run("git", "add", "-A", cwd=target)
    run("git", "-c", "user.email=plant@local", "-c", "user.name=plant",
        "commit", "-qm", "base store", cwd=target)
    for sc in scenarios:
        plant = PLANTS[sc]
        store, tests = BASE_STORE, BASE_TESTS
        for old, new in plant["store"]:
            assert old in store, f"scenario {sc}: store anchor missing"
            store = store.replace(old, new, 1)
        for old, new in plant["tests"]:
            assert old in tests, f"scenario {sc}: tests anchor missing"
            tests = tests.replace(old, new, 1)
        (target / "store.py").write_text(store)
        (target / "test_store.py").write_text(tests)
        if plant.get("agents"):
            agents = AGENTS_BASE.replace(
                "## Rules", "## Rules\n" + plant["agents"].rstrip("\n"), 1)
            (target / "AGENTS.md").write_text(agents)
    run("python3", "test_store.py", cwd=target)  # must exit 0
    print(f"built {target} with scenarios {'+'.join(scenarios)}; validation green")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    build(pathlib.Path(sys.argv[1]), [s.upper() for s in sys.argv[2:]])
