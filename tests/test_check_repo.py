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

ALL_SKILLS = ["dual-review-loop", "dual-review-correctness", "dual-review-structure"]


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


def _make_skill_tree(root: pathlib.Path, *, skill: str = "dual-review-correctness",
                     name: str | None = None, description: str = "A test",
                     openai_yaml: str | None = None, apply_name_to_all: bool = False):
    """Create a minimal skill tree under root for one or all skills."""
    plugin_dir = root / "plugins" / "dual-review-loop"
    skills_to_create = [skill] if skill != "ALL" else ALL_SKILLS
    for s in skills_to_create:
        d = plugin_dir / "skills" / s
        d.mkdir(parents=True, exist_ok=True)
        if apply_name_to_all and name is not None:
            fm_name = name
        elif name is not None and len(skills_to_create) == 1:
            fm_name = name
        else:
            fm_name = s
        desc_line = f"description: {description}" if description is not None else "description:"
        (d / "SKILL.md").write_text(f"---\nname: {fm_name}\n{desc_line}\n---\n# {s}\n")
        (d / "agents").mkdir(parents=True, exist_ok=True)
        oy = openai_yaml or "interface:\n  display_name: Test\n  short_description: Test desc\n"
        (d / "agents" / "openai.yaml").write_text(oy)


def _make_agent_tree(root: pathlib.Path, *,
                     correctness_name: str = "dual-review-correctness-reviewer",
                     structure_name: str = "dual-review-structure-reviewer",
                     correctness_skills: str = "dual-review-correctness",
                     structure_skills: str = "dual-review-structure",
                     correctness_tools: str = "Read, Grep, Glob",
                     structure_tools: str = "Read, Grep, Glob"):
    """Create Claude agent definitions."""
    agents = root / "plugins" / "dual-review-loop" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    (agents / "dual-review-correctness-reviewer.md").write_text(
        f"---\nname: {correctness_name}\n"
        f"description: Test\ntools: {correctness_tools}\n"
        f"skills: {correctness_skills}\n---\n# T\n")
    (agents / "dual-review-structure-reviewer.md").write_text(
        f"---\nname: {structure_name}\n"
        f"description: Test\ntools: {structure_tools}\n"
        f"skills: {structure_skills}\n---\n# T\n")


# ---------------------------------------------------------------- packaging --
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

    def test_non_mapping_json_root_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(pathlib.Path(tmp))
            pj = root / "plugins" / "dual-review-loop" / "plugin.json"
            pj.write_text('["not", "a", "mapping"]')
            check_repo.check_packaging_for(root)
        self.assertTrue(any("not a mapping" in f for f in check_repo.failures))


# ------------------------------------------------ forbidden schema fields --
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


# ------------------------------------------------- frontmatter parsing --
class FrontmatterParsing(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []

    def _write_skill_file(self, tmp: pathlib.Path, content: str) -> pathlib.Path:
        d = tmp / "skills" / "test-skill"
        d.mkdir(parents=True)
        p = d / "SKILL.md"
        p.write_text(content)
        return p

    def test_valid_frontmatter_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill_file(pathlib.Path(tmp),
                                       "---\nname: test\ndescription: A test\n---\n# Title\n")
            check_repo.failures = []
            fm = check_repo.parse_frontmatter(p)
        self.assertIsNotNone(fm)
        self.assertEqual(check_repo.failures, [])
        self.assertEqual(fm["name"], "test")

    def test_invalid_yaml_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill_file(pathlib.Path(tmp),
                                       "---\nname: test\nbad: [unclosed\n---\n# Title\n")
            check_repo.failures = []
            fm = check_repo.parse_frontmatter(p)
        self.assertIsNone(fm)
        self.assertTrue(any("not valid YAML" in f for f in check_repo.failures))

    def test_no_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill_file(pathlib.Path(tmp), "# Title\nNo frontmatter\n")
            check_repo.failures = []
            fm = check_repo.parse_frontmatter(p)
        self.assertIsNone(fm)
        self.assertTrue(any("does not start with ---" in f for f in check_repo.failures))

    def test_no_closing_delimiter_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill_file(pathlib.Path(tmp),
                                       "---\nname: test\nno closing\n")
            check_repo.failures = []
            fm = check_repo.parse_frontmatter(p)
        self.assertIsNone(fm)
        self.assertTrue(any("no closing ---" in f for f in check_repo.failures))

    def test_non_mapping_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill_file(pathlib.Path(tmp),
                                       "---\n- item1\n- item2\n---\n# Title\n")
            check_repo.failures = []
            fm = check_repo.parse_frontmatter(p)
        self.assertIsNone(fm)
        self.assertTrue(any("not a YAML mapping" in f for f in check_repo.failures))


# ------------------------------------------- frontmatter name/description --
class FrontmatterNameMismatch(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.old = check_repo.PLUGIN
        check_repo.PLUGIN = self.root / "plugins" / "dual-review-loop"

    def tearDown(self):
        check_repo.PLUGIN = self.old
        self.tmp.cleanup()

    def test_name_mismatch_fails(self):
        _make_skill_tree(self.root, skill="ALL", name="WRONG", apply_name_to_all=True)
        check_repo.check_frontmatter_and_names()
        self.assertTrue(any("!= directory name" in f for f in check_repo.failures))

    def test_empty_description_fails(self):
        _make_skill_tree(self.root, skill="ALL", description="")
        check_repo.check_frontmatter_and_names()
        self.assertTrue(any("description" in f for f in check_repo.failures))

    def test_missing_name_fails(self):
        _make_skill_tree(self.root, skill="ALL")
        # Rewrite one skill to remove name
        p = self.root / "plugins" / "dual-review-loop" / "skills" / "dual-review-loop" / "SKILL.md"
        p.write_text("---\ndescription: X\n---\n# T\n")
        check_repo.check_frontmatter_and_names()
        self.assertTrue(any("'name' missing" in f for f in check_repo.failures))

    def test_valid_frontmatter_passes(self):
        _make_skill_tree(self.root, skill="ALL")
        check_repo.check_frontmatter_and_names()
        self.assertEqual(check_repo.failures, [])


# ------------------------------------------- Claude agent validation --
class ClaudeAgentValidation(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.old = check_repo.PLUGIN
        check_repo.PLUGIN = self.root / "plugins" / "dual-review-loop"

    def tearDown(self):
        check_repo.PLUGIN = self.old
        self.tmp.cleanup()

    def test_correct_agent_passes(self):
        _make_agent_tree(self.root)
        check_repo.check_claude_agents()
        self.assertEqual(check_repo.failures, [])

    def test_wrong_skill_fails(self):
        _make_agent_tree(self.root, correctness_skills="WRONG")
        check_repo.check_claude_agents()
        self.assertTrue(any("WRONG" in f for f in check_repo.failures))

    def test_missing_name_fails(self):
        agents = self.root / "plugins" / "dual-review-loop" / "agents"
        agents.mkdir(parents=True)
        (agents / "dual-review-correctness-reviewer.md").write_text(
            "---\ndescription: Test\ntools: Read, Grep, Glob\n"
            "skills: dual-review-correctness\n---\n# T\n")
        _make_agent_tree(self.root)  # writes structure agent normally
        # Overwrite correctness agent without name
        (agents / "dual-review-correctness-reviewer.md").write_text(
            "---\ndescription: Test\ntools: Read, Grep, Glob\n"
            "skills: dual-review-correctness\n---\n# T\n")
        check_repo.check_claude_agents()
        self.assertTrue(any("'name' missing" in f for f in check_repo.failures))

    def test_write_capable_tool_fails(self):
        _make_agent_tree(self.root, correctness_tools="Read, Grep, Glob, Write")
        check_repo.check_claude_agents()
        self.assertTrue(any("write-capable" in f for f in check_repo.failures))

    def test_missing_skills_fails(self):
        agents = self.root / "plugins" / "dual-review-loop" / "agents"
        agents.mkdir(parents=True)
        (agents / "dual-review-correctness-reviewer.md").write_text(
            "---\nname: dual-review-correctness-reviewer\n"
            "description: Test\ntools: Read, Grep, Glob\n---\n# T\n")
        _make_agent_tree(self.root)
        (agents / "dual-review-correctness-reviewer.md").write_text(
            "---\nname: dual-review-correctness-reviewer\n"
            "description: Test\ntools: Read, Grep, Glob\n---\n# T\n")
        check_repo.check_claude_agents()
        self.assertTrue(any("'skills' missing" in f for f in check_repo.failures))

    def test_name_mismatch_fails(self):
        _make_agent_tree(self.root, correctness_name="WRONG")
        check_repo.check_claude_agents()
        # fail format: "{agent}.md: frontmatter name 'WRONG' != 'dual-review-correctness-reviewer'"
        self.assertTrue(any("dual-review-correctness-reviewer" in f and "WRONG" in f
                            for f in check_repo.failures))


# ------------------------------------------- non-mapping YAML/JSON roots --
class NonMappingYamlRoot(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []

    def test_yaml_list_root_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "test.yaml"
            p.write_text("- item1\n- item2\n")
            result = check_repo.load_yaml(p)
        self.assertIsNone(result)
        self.assertTrue(any("not a mapping" in f for f in check_repo.failures))

    def test_json_list_root_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "test.json"
            p.write_text('["a", "b"]')
            result = check_repo.load_json(p)
        self.assertIsNone(result)
        self.assertTrue(any("not a mapping" in f for f in check_repo.failures))


# ------------------------------------------- protocol required clauses --
class ProtocolRequiredClauses(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.refs = (self.root / "plugins" / "dual-review-loop" /
                     "skills" / "dual-review-loop" / "references")
        self.refs.mkdir(parents=True)
        self.old = check_repo.PLUGIN
        check_repo.PLUGIN = self.root / "plugins" / "dual-review-loop"

    def tearDown(self):
        check_repo.PLUGIN = self.old
        self.tmp.cleanup()

    def _write_all_required(self):
        (self.refs / "review-scope.md").write_text(
            "causally attributable to the target change\ncausal_link\nfrozen anchor\n")
        (self.refs / "reviewer-prompt-contract.md").write_text(
            "review_materialization\nStay read-only\nFresh-review rule\n## 5. Runtime adaptation\n")
        (self.refs / "finding-schema.md").write_text(
            "structural_class: regression | improvement\ncausal_link\nno `discipline: taste`\n")
        (self.refs / "convergence-contract.md").write_text(
            "structural_class: regression | improvement\npersistent\nchurn\n"
            "no repository write\nGuard precedence\nseen_before\n")
        (self.refs / "output-format.md").write_text(
            "exactly one canonical PASS or STOPPED outcome block\n")

    def test_missing_clause_fails(self):
        (self.refs / "review-scope.md").write_text("# Scope\nsome content but no causal_link\n")
        check_repo.check_protocol_files()
        self.assertTrue(any("required clause absent" in f for f in check_repo.failures))

    def test_extra_file_fails(self):
        self._write_all_required()
        (self.refs / "extra-file.md").write_text("should not exist\n")
        check_repo.check_protocol_files()
        self.assertTrue(any("unexpected extra" in f for f in check_repo.failures))

    def test_all_required_passes(self):
        self._write_all_required()
        check_repo.check_protocol_files()
        self.assertEqual(check_repo.failures, [])


# ------------------------------------------- openai.yaml validation --
class OpenaiYamlValidation(unittest.TestCase):
    def setUp(self):
        check_repo.failures = []
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.old = check_repo.PLUGIN
        check_repo.PLUGIN = self.root / "plugins" / "dual-review-loop"

    def tearDown(self):
        check_repo.PLUGIN = self.old
        self.tmp.cleanup()

    def test_non_mapping_interface_fails(self):
        _make_skill_tree(self.root, skill="dual-review-correctness",
                         openai_yaml="interface:\n- not\n- a\n- mapping\n")
        # Fill other skills
        for s in ("dual-review-loop", "dual-review-structure"):
            _make_skill_tree(self.root, skill=s)
        check_repo.check_frontmatter_and_names()
        self.assertTrue(any("not a mapping" in f for f in check_repo.failures))

    def test_missing_display_name_fails(self):
        _make_skill_tree(self.root, skill="dual-review-correctness",
                         openai_yaml="interface:\n  short_description: X\n")
        for s in ("dual-review-loop", "dual-review-structure"):
            _make_skill_tree(self.root, skill=s)
        check_repo.check_frontmatter_and_names()
        self.assertTrue(any("display_name" in f for f in check_repo.failures))


# ------------------------------------------- fixture builder contract --
class FixtureBuilderContract(unittest.TestCase):
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
