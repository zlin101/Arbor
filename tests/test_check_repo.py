"""Tests for scripts/check_repo.py and the fixture builder contract.

Every rule in the checker must have a demonstrated pass AND fail branch here;
a rule that cannot be failed in a test does not belong in the checker.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("check_repo", REPO / "scripts" / "check_repo.py")
check_repo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_repo)

GOOD_PLUGIN = {
    "name": "dual-review-loop", "version": "0.2.0", "license": "MIT",
    "repository": "https://github.com/zlin101/Arbor",
}
GOOD_MARKET = {"name": "arbor", "plugins": [
    {"name": "dual-review-loop", "source": {"source": "local", "path": "./plugins/dual-review-loop"}},
]}


def make_repo(root: pathlib.Path, *, plugin=None, market=None, plugin_override=None):
    plugin = {**GOOD_PLUGIN, **(plugin or {})}
    market = {**GOOD_MARKET, **(market or {})}
    pdir = root / "plugins" / "dual-review-loop"
    (pdir / ".claude-plugin").mkdir(parents=True)
    (root / ".agents" / "plugins").mkdir(parents=True)
    (root / ".claude-plugin").mkdir(parents=True)
    pj = {**plugin, **(plugin_override or {})}
    (pdir / "plugin.json").write_text(json.dumps(pj))
    cpj = {**plugin, "homepage": plugin["repository"]}
    cpj.pop("repository", None)
    (pdir / ".claude-plugin" / "plugin.json").write_text(json.dumps(cpj))
    (root / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps(market))
    (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
        {**market, "plugins": [{"name": plugin["name"], "source": "./plugins/dual-review-loop"}]}))
    return root


class PackagingParity(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []

    def test_good_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(pathlib.Path(tmp))
            check_repo.check_packaging_for(pathlib.Path(tmp))
        self.assertEqual(check_repo.failures, [])

    def test_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(pathlib.Path(tmp))
            pj = root / "plugins" / "dual-review-loop" / "plugin.json"
            data = json.loads(pj.read_text()); data["version"] = "9.9.9"
            pj.write_text(json.dumps(data))
            check_repo.check_packaging_for(root)
        self.assertTrue(any("version" in f for f in check_repo.failures))

    def test_marketplace_source_path_missing_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(pathlib.Path(tmp))
            mkt = root / ".agents" / "plugins" / "marketplace.json"
            data = json.loads(mkt.read_text())
            data["plugins"][0]["source"]["path"] = "./plugins/does-not-exist"
            mkt.write_text(json.dumps(data))
            check_repo.check_packaging_for(root)
        self.assertTrue(any("does not exist" in f for f in check_repo.failures))


class ForbiddenReviewerFields(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.skills = root / "skills"
        self.agents = root / "agents"
        self.sdir = self.skills / "dual-review-structure"
        self.sdir.mkdir(parents=True)
        self.agents.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_skill(self, text):
        (self.sdir / "SKILL.md").write_text(text)

    def run_check(self):
        check_repo.check_forbidden_reviewer_fields_for(self.skills, self.agents)

    def test_blocking_field_in_reviewer_output_fails(self):
        self.write_skill("```yaml\nfindings:\n  - local_id: S1\n    blocking: true | false\n```")
        self.run_check()
        self.assertTrue(any("blocking" in f for f in check_repo.failures))

    def test_legacy_discipline_enum_fails(self):
        self.write_skill("discipline: blocking regression | material improvement | taste")
        self.run_check()
        self.assertTrue(any("discipline" in f for f in check_repo.failures))

    def test_clean_skill_passes(self):
        self.write_skill("```yaml\nfindings:\n  - local_id: S1\n"
                         "    structural_class: regression | improvement\n```")
        self.run_check()
        self.assertEqual(check_repo.failures, [])


class FixtureBuilderContract(unittest.TestCase):
    """plant.py: v0.1 keys must keep their exact historical shape."""

    EXPECTED_STATS = {
        "A": "2 files changed, 9 insertions(+)",
        "B": "2 files changed, 13 insertions(+)",
        "C": "2 files changed, 13 insertions(+)",
        "D": "2 files changed, 20 insertions(+)",
        "H": "3 files changed, 12 insertions(+), 1 deletion(-)",
        "J": "2 files changed, 30 insertions(+)",
        "X": "2 files changed, 7 insertions(+), 5 deletions(-)",
    }

    def _plant(self, key: str) -> pathlib.Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        target = pathlib.Path(tmp.name) / "root"
        subprocess.run([sys.executable,
                        str(REPO / "docs" / "acceptance" / "fixtures" / "plant.py"),
                        str(target), key], check=True, capture_output=True)
        return target / key

    def test_legacy_keys_keep_their_diff_shape(self):
        for key, expected in self.EXPECTED_STATS.items():
            with self.subTest(key=key):
                fixture = self._plant(key)
                log = subprocess.run(["git", "-C", str(fixture), "log", "--oneline"],
                                     capture_output=True, text=True).stdout.strip().splitlines()
                self.assertEqual(len(log), 1, f"{key}: expected exactly the base commit")
                stat = subprocess.run(["git", "-C", str(fixture), "diff", "--stat"],
                                      capture_output=True, text=True).stdout.strip().splitlines()[-1]
                self.assertIn(expected, stat)

    def test_rebuild_refuses_overwrite(self):
        fixture = self._plant("A")
        result = subprocess.run([sys.executable,
                                 str(REPO / "docs" / "acceptance" / "fixtures" / "plant.py"),
                                 str(fixture.parent), "A"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to overwrite", result.stderr)

    def test_unknown_scenario_rejected(self):
        result = subprocess.run([sys.executable,
                                 str(REPO / "docs" / "acceptance" / "fixtures" / "plant.py"),
                                 str(pathlib.Path(self._plant("A")).parent.parent), "E"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown scenarios ['E']", result.stderr)


if __name__ == "__main__":
    unittest.main()
