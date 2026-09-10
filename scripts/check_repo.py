#!/usr/bin/env python3
"""Arbor repo consistency checker (deterministic).

Validates packaging parity, protocol-file integrity, reviewer boundary
projections, and forbidden schema fields. Exits non-zero on the first
category with failures; prints every failure it finds.

Requires PyYAML (pip install pyyaml==6.0.2). No degraded mode: missing
PyYAML is a hard failure.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    print("FATAL: PyYAML is required. Install with: pip install pyyaml==6.0.2",
          file=sys.stderr)
    sys.exit(1)

REPO = pathlib.Path(__file__).resolve().parent.parent

failures: list[str] = []
PLUGIN = REPO / "plugins" / "dual-review-loop"


def fail(msg: str) -> None:
    failures.append(msg)


def load_json(path: pathlib.Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{path}: unparseable JSON: {exc}")
        return None
    if not isinstance(data, dict):
        fail(f"{path}: JSON root is not a mapping (got {type(data).__name__})")
        return None
    return data


def load_yaml(path: pathlib.Path) -> dict | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{path}: unparseable YAML: {exc}")
        return None
    if not isinstance(data, dict):
        fail(f"{path}: YAML root is not a mapping (got {type(data).__name__})")
        return None
    return data


# ---------------------------------------------------------------- packaging --
def check_packaging() -> None:
    check_packaging_for(REPO)


def check_packaging_for(root: pathlib.Path) -> None:
    plugin = root / "plugins" / "dual-review-loop"
    codex_plugin = load_json(plugin / "plugin.json") or {}
    claude_plugin = load_json(plugin / ".claude-plugin" / "plugin.json") or {}
    for key in ("name", "version", "license"):
        if codex_plugin.get(key) != claude_plugin.get(key):
            fail(f"plugin manifest parity: {key} differs "
                 f"({codex_plugin.get(key)!r} vs {claude_plugin.get(key)!r})")
    if codex_plugin.get("repository") != claude_plugin.get("homepage"):
        fail("plugin manifest parity: repository/homepage differ "
             f"({codex_plugin.get('repository')!r} vs {claude_plugin.get('homepage')!r})")

    codex_mkt = load_json(root / ".agents" / "plugins" / "marketplace.json") or {}
    claude_mkt = load_json(root / ".claude-plugin" / "marketplace.json") or {}
    if codex_mkt.get("name") != claude_mkt.get("name"):
        fail(f"marketplace name parity: {codex_mkt.get('name')!r} vs "
             f"{claude_mkt.get('name')!r}")
    codex_entry = next((p for p in codex_mkt.get("plugins", [])
                        if p.get("name") == codex_plugin.get("name")), None)
    claude_entry = next((p for p in claude_mkt.get("plugins", [])
                         if p.get("name") == claude_plugin.get("name")), None)
    if codex_entry is None or claude_entry is None:
        fail("marketplace entries: plugin missing from one of the marketplaces")
    else:
        src = codex_entry.get("source", {})
        path = src.get("path") if isinstance(src, dict) else src
        if not (root / str(path)).is_dir():
            fail(f"codex marketplace source path does not exist: {path}")
        if not (root / str(claude_entry.get("source", ""))).is_dir():
            fail(f"claude marketplace source path does not exist: "
                 f"{claude_entry.get('source')}")


# --------------------------------------------------------------- structure --
def skill_md(skill: str) -> pathlib.Path:
    return PLUGIN / "skills" / skill / "SKILL.md"


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(path: pathlib.Path) -> dict | None:
    """Parse YAML frontmatter between --- delimiters. Returns None on failure."""
    text = read(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"{path.name}: frontmatter does not start with ---")
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        fail(f"{path.name}: frontmatter has no closing ---")
        return None
    raw = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(raw)
    except Exception as exc:  # noqa: BLE001
        fail(f"{path.name}: frontmatter is not valid YAML: {exc}")
        return None
    if not isinstance(data, dict):
        fail(f"{path.name}: frontmatter is not a YAML mapping")
        return None
    return data


def check_protocol_files() -> None:
    loop_refs = PLUGIN / "skills" / "dual-review-loop" / "references"
    required = {
        "review-scope.md": ["causally attributable to the target change",
                            "causal_link", "frozen anchor"],
        "reviewer-prompt-contract.md": ["review_materialization",
                                        "Stay read-only", "Fresh-review rule",
                                        "## 5. Runtime adaptation"],
        "finding-schema.md": ["structural_class: regression | improvement",
                              "causal_link", "no `discipline: taste`"],
        "convergence-contract.md": ["structural_class: regression | improvement",
                                    "persistent", "churn", "no repository write",
                                    "Guard precedence", "seen_before"],
        "output-format.md": ["exactly one canonical PASS or STOPPED outcome block"],
    }
    for name, clauses in required.items():
        path = loop_refs / name
        if not path.is_file():
            fail(f"missing protocol reference: {name}")
            continue
        text = read(path)
        for clause in clauses:
            if clause not in text:
                fail(f"{name}: required clause absent: {clause!r}")
    for extra in loop_refs.glob("*.md"):
        if extra.name not in required:
            fail(f"unexpected extra protocol reference (keep the file set fixed): "
                 f"{extra.name}")


def check_frontmatter_and_names() -> None:
    skills = ["dual-review-loop", "dual-review-correctness", "dual-review-structure"]
    for skill in skills:
        path = skill_md(skill)
        if not path.is_file():
            fail(f"missing SKILL.md for {skill}")
            continue
        fm = parse_frontmatter(path)
        if fm is None:
            continue
        if not fm.get("name"):
            fail(f"{skill}/SKILL.md: frontmatter 'name' missing or empty")
        elif fm["name"] != skill:
            fail(f"{skill}/SKILL.md: frontmatter name {fm['name']!r} "
                 f"!= directory name {skill!r}")
        if not fm.get("description"):
            fail(f"{skill}/SKILL.md: frontmatter 'description' missing or empty")

        yaml_path = PLUGIN / "skills" / skill / "agents" / "openai.yaml"
        if not yaml_path.is_file():
            fail(f"missing agents/openai.yaml for {skill}")
        else:
            data = load_yaml(yaml_path)
            if data is None:
                continue
            iface = data.get("interface") or {}
            if not isinstance(iface, dict):
                fail(f"{skill}/agents/openai.yaml: interface is not a mapping")
            else:
                for key in ("display_name", "short_description"):
                    if not iface.get(key):
                        fail(f"{skill}/agents/openai.yaml: interface.{key} empty")


def check_claude_agents() -> None:
    """Validate Claude agent definitions: frontmatter name, skills, tools."""
    agent_skill_map = {
        "dual-review-correctness-reviewer": "dual-review-correctness",
        "dual-review-structure-reviewer": "dual-review-structure",
    }
    for agent, expected_skill in agent_skill_map.items():
        path = PLUGIN / "agents" / f"{agent}.md"
        if not path.is_file():
            fail(f"missing Claude agent definition: {agent}.md")
            continue
        fm = parse_frontmatter(path)
        if fm is None:
            continue
        if not fm.get("name"):
            fail(f"{agent}.md: frontmatter 'name' missing or empty")
        elif fm["name"] != agent:
            fail(f"{agent}.md: frontmatter name {fm['name']!r} != {agent!r}")
        actual_skill = fm.get("skills")
        if not actual_skill:
            fail(f"{agent}.md: frontmatter 'skills' missing")
        elif actual_skill != expected_skill:
            fail(f"{agent}.md: skills {actual_skill!r} != {expected_skill!r}")
        tools = fm.get("tools", "")
        if "Read" not in tools or "Grep" not in tools or "Glob" not in tools:
            fail(f"{agent}.md: tools missing Read/Grep/Glob (got {tools!r})")
        if "Write" in tools or "Bash" in tools or "Edit" in tools:
            fail(f"{agent}.md: tools includes write-capable tool (got {tools!r})")


# ------------------------------------------------- forbidden schema fields --
def check_forbidden_reviewer_fields() -> None:
    check_forbidden_reviewer_fields_for(PLUGIN / "skills", PLUGIN / "agents")


def check_forbidden_reviewer_fields_for(skills_dir: pathlib.Path,
                                        agents_dir: pathlib.Path) -> None:
    """Reviewer-facing files must not teach the reviewer to emit gate policy."""
    reviewer_files = [
        skills_dir / "dual-review-correctness" / "SKILL.md",
        skills_dir / "dual-review-structure" / "SKILL.md",
        agents_dir / "dual-review-correctness-reviewer.md",
        agents_dir / "dual-review-structure-reviewer.md",
    ]
    for path in reviewer_files:
        if not path.is_file():
            continue
        text = read(path)
        if re.search(r"^\s*blocking:\s*(true | false | P)", text, re.M):
            fail(f"{path.name}: reviewer output teaches a 'blocking' field")
        if re.search(r"discipline:\s*blocking regression", text):
            fail(f"{path.name}: legacy 'discipline' enum present")
    schema = read(skill_md("dual-review-loop").parent / "references" /
                  "finding-schema.md")
    if "discipline: blocking regression | material improvement | taste" in schema:
        fail("finding-schema.md: legacy discipline enum present")


# ------------------------------------------------------------------- main --
def main() -> int:
    check_packaging()
    check_protocol_files()
    check_frontmatter_and_names()
    check_claude_agents()
    check_forbidden_reviewer_fields()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("check_repo: OK (packaging, protocol files, projections, schema)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
