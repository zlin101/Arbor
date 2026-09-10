#!/usr/bin/env python3
"""Rebuild the acceptance fixtures for dual-review-loop v0.1 scenarios.

Usage:
    python3 plant.py <target-root> <scenario> [<scenario> ...]

Scenarios with a fixture: A B C D H J   (one letter = one scenario in
docs/acceptance/dual-review-loop-v0.1.md). Scenarios E, I, J-prime and
J-double-prime are DECISION-PROCEDURE runs with NO fixture — their synthetic
histories are stated inline in docs/acceptance/transcripts/scenario-*.md.

For EACH requested scenario this script creates a SEPARATE fresh git repo at
    <target-root>/<SCENARIO>/      (branch main, one commit "base store")
and applies that scenario's planted working-tree change on top. Directories are
never shared between scenarios, so N scenarios yield N independent fixtures.
The loop under test never commits, so after a scenario run `git diff HEAD` is
exactly the change the reviewers saw. Base content and every planted string are
verbatim from the 2026-09-09/10 acceptance runs.
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

# Scenario H's fixture (ttl contract bug); scenario E itself has NO fixture.
AGENTS_H_EXTRA = '''- The `ttl` parameter on `Store.set` is a committed v2 API contract: it must remain
  accepted and must eventually work. Removing it, or silently ignoring caller-supplied
  values, is not an acceptable resolution.
- Never invent product policy. If a fix requires a product decision this repository
  cannot answer, stop and hand the decision back to the owner instead of guessing.
'''

REPORT_PY = '''"""Report helper built on the store's plain-value contract."""


def describe(store, key):
    value = store.get(key)
    if value is None:
        return f"{key}: missing"
    return f"{key}: {value}"
'''

# (old, new) string replacements on store.py / test_store.py per scenario.
# "base_extra" files land in the BASE commit only (before the planted
# working-tree change); scenarios without the key are unaffected.
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
    "H": {
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
        "agents": AGENTS_H_EXTRA,
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
    # X (v0.2, E06 cross-boundary): changed get() contract, untouched caller.
    "X": {
        "base_extra": {"report.py": REPORT_PY},
        "store": [('''    def get(self, key, default=None):
        return self._data.get(key, default)''',
                  '''    def get(self, key, default=None):
        # v2 contract: returns a (value, found) tuple so callers can tell
        # "stored None" from "absent".
        return (self._data.get(key, default), True)''')],
        "tests": [('''    def test_set_get_roundtrip(self):
        s = Store()
        s.set("a", 1)
        self.assertEqual(s.get("a"), 1)''',
                  '''    def test_set_get_roundtrip(self):
        s = Store()
        s.set("a", 1)
        self.assertEqual(s.get("a"), (1, True))'''),
                  ('''    def test_get_default(self):
        s = Store()
        self.assertIsNone(s.get("missing"))
        self.assertEqual(s.get("missing", 0), 0)''',
                   '''    def test_get_default(self):
        s = Store()
        self.assertEqual(s.get("missing"), (None, True))
        self.assertEqual(s.get("missing", 0), (0, True))'''),
                  ('''        self.assertTrue(s.delete("a"))
        self.assertIsNone(s.get("a"))''',
                   '''        self.assertTrue(s.delete("a"))
        self.assertEqual(s.get("a"), (None, True))''')],
    },
}


def run(*cmd, cwd):
    subprocess.run(cmd, check=True, cwd=cwd, capture_output=True, text=True)


def build_scenario(root: pathlib.Path, scenario: str):
    """Create <root>/<scenario>/ as an independent fixture repo."""
    target = root / scenario
    if target.exists():
        sys.exit(f"refusing to overwrite existing {target}")
    target.mkdir(parents=True)
    plant = PLANTS[scenario]
    # 1. pristine base, committed — this is the frozen baseline the loop freezes.
    (target / "store.py").write_text(BASE_STORE)
    (target / "test_store.py").write_text(BASE_TESTS)
    (target / "AGENTS.md").write_text(AGENTS_BASE)
    for name, content in plant.get("base_extra", {}).items():
        (target / name).write_text(content)
    run("git", "init", "-q", "-b", "main", cwd=target)
    run("git", "add", "-A", cwd=target)
    run("git", "-c", "user.email=plant@local", "-c", "user.name=plant",
        "commit", "-qm", "base store", cwd=target)
    # 2. planted change as an UNCOMMITTED working-tree modification, so
    #    `git diff HEAD` is exactly what the reviewers saw.
    store, tests = BASE_STORE, BASE_TESTS
    for old, new in plant["store"]:
        assert old in store, f"scenario {scenario}: store anchor missing"
        store = store.replace(old, new, 1)
    for old, new in plant["tests"]:
        assert old in tests, f"scenario {scenario}: tests anchor missing"
        tests = tests.replace(old, new, 1)
    (target / "store.py").write_text(store)
    (target / "test_store.py").write_text(tests)
    agents = AGENTS_BASE
    if plant.get("agents"):
        agents = agents.replace("## Rules", "## Rules\n" + plant["agents"].rstrip("\n"), 1)
    (target / "AGENTS.md").write_text(agents)
    run("python3", "test_store.py", cwd=target)  # must exit 0
    return target


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    root = pathlib.Path(sys.argv[1])
    scenarios = [s.upper() for s in sys.argv[2:]]
    unknown = [s for s in scenarios if s not in PLANTS]
    if unknown:
        sys.exit(f"unknown scenarios {unknown}; fixture-backed: {sorted(PLANTS)}")
    built = [build_scenario(root, s) for s in scenarios]
    print("built independent fixtures:")
    for p in built:
        print(f"  {p}")
