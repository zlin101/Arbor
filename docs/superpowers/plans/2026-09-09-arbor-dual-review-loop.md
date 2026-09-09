# Arbor (信息gap) — dual-review-loop Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `dual-review-loop` Codex + Claude Code plugin — two fresh read-only reviewers in parallel over one frozen scope, single-writer root-cause fixes, project validation, full-scope re-review, bounded convergence (PASS or STOP) — published from the `Arbor` marketplace repo (brand: 信息gap).

**Architecture:** One repo = one plugin marketplace in two formats (`.agents/plugins/marketplace.json` for Codex, `.claude-plugin/marketplace.json` for Claude Code), one plugin (`plugins/dual-review-loop/`) with three shared skills (orchestrator + 2 reviewers). Reviewer isolation: prompt contract everywhere; on Claude Code hardened with plugin `agents/*.md` tool allowlists (`Read, Grep, Glob`). All loop semantics live in the orchestrator skill's `references/` (progressive disclosure); reviewers are self-contained and output one unified finding schema.

**Tech Stack:** Markdown skills (portable frontmatter: `name`, `description` only), JSON manifests, YAML UI metadata, `codex` CLI 0.153.4 (local, verified), `claude` CLI (local), Node 20 + `plugin-eval` official validator, python3 for JSON checks.

**Authoritative spec:** `docs/zlin-agent-kit-dual-review-loop-spec.md` (in-repo). Where this plan cites spec sections, those sections are binding. Owner overrides already applied to the spec: repo name = **Arbor** (github.com/zlin101/Arbor), brand display name = **信息gap** (spec §3.1: owner naming wins); **dual Claude+Codex compatibility is in scope** (spec §2 "不同时维护 Cursor 专用 manifest" and §30.2 "多平台同时支持" are superseded by owner instruction — Cursor remains out of scope).

## Global Constraints

- Skill frontmatter carries ONLY `name` and `description` (spec §4.4). No Cursor/Claude-specific fields (`disable-model-invocation` etc.).
- Reviewers are read-only: no edit/create/delete/stage/commit/push, no goal/task/ledger writes, no nested subagents, no "shall I fix?" questions (spec §7.2, §7.3, §8).
- Main agent is the single writer (spec §7.1, §15.1).
- Scope freeze at loop start; every round re-reviews `baseline → current full target change`, never only the last fix diff (spec §10).
- Defaults: `max_rounds: 3`, `no_progress_rounds: 2`; convergence = open P0=0 ∧ open P1=0 ∧ structural blockers=0 ∧ required validation green ∧ no unresolved material reviewer conflict (spec §17, §18).
- NO hardcoded project details: no Iris, no branch names, no language/test commands (`go test`, `pytest`, `npm test` must not appear as plugin defaults) (spec §16.2, §22).
- No default review ledger; no automatic commit/push/merge/PR (spec §23, §15.5).
- Attribution: MIT notices with EXACT upstream copyright lines — `Copyright (c) 2025 sanyuan0704` and `Copyright (c) 2026 Cursor` (verified 2026-09-09 against upstream LICENSE files).
- Naming: repo/marketplace id `arbor`, display 信息gap; plugin `dual-review-loop`; skills `dual-review-loop`, `dual-review-correctness`, `dual-review-structure`; Claude agents `dual-review-correctness-reviewer`, `dual-review-structure-reviewer`.
- Git: local repo has zero commits on unborn `master`; first task renames to `main`. Commit messages: conventional (feat/docs/chore), each ending `Co-Authored-By: Claude Code <noreply@anthropic.com>`. Never push (spec §31: no external writes).
- Validation of this docs/plugin repo is command-based (JSON parse, frontmatter grep, `plugin-eval`, `claude plugin validate`, CLI smoke tests) — there is no unit-test framework here; each task's "test" is the exact command + expected output given.

## File Structure (complete end state)

```text
Arbor/
├── README.md                                  # 信息gap brand + marketplace usage (both runtimes)
├── LICENSE                                    # MIT, Copyright (c) 2026 zlin101
├── .gitignore
├── .agents/plugins/marketplace.json           # Codex repo marketplace
├── .claude-plugin/marketplace.json            # Claude Code repo marketplace
├── docs/
│   ├── zlin-agent-kit-dual-review-loop-spec.md# (exists) authoritative spec
│   └── superpowers/plans/2026-09-09-...md     # (exists) this plan
└── plugins/dual-review-loop/
    ├── plugin.json                            # Codex portable manifest (root, verified working)
    ├── .claude-plugin/plugin.json             # Claude Code manifest
    ├── README.md
    ├── CHANGELOG.md
    ├── LICENSE                                # MIT, Copyright (c) 2026 zlin101
    ├── THIRD_PARTY_NOTICES.md                 # sanyuan0704 + Cursor attribution
    ├── agents/
    │   ├── dual-review-correctness-reviewer.md  # Claude-only read-only subagent def
    │   └── dual-review-structure-reviewer.md    # Claude-only read-only subagent def
    └── skills/
        ├── dual-review-loop/
        │   ├── SKILL.md
        │   ├── agents/openai.yaml
        │   └── references/
        │       ├── convergence-contract.md
        │       ├── finding-schema.md
        │       ├── review-scope.md
        │       ├── reviewer-prompt-contract.md
        │       └── output-format.md
        ├── dual-review-correctness/
        │   ├── SKILL.md
        │   ├── agents/openai.yaml
        │   └── references/
        │       ├── correctness-checklist.md
        │       └── security-reliability-checklist.md
        └── dual-review-structure/
            ├── SKILL.md
            ├── agents/openai.yaml
            └── references/
                └── structural-quality-checklist.md
```

Not created (spec §5, §30.2): `scripts/`, `hooks/`, `mcp.json`, `assets/`, `.codex-plugin/` (only if Task 9 smoke test fails on root manifest), empty placeholder dirs.

---

### Task 1: Repo scaffold — branding, license, both marketplace manifests

**Files:**
- Create: `README.md`, `LICENSE`, `.gitignore`
- Create: `.agents/plugins/marketplace.json`
- Create: `.claude-plugin/marketplace.json`

**Interfaces:**
- Produces: marketplace id `arbor` resolvable by BOTH `codex plugin marketplace add <repo>` and `claude plugin marketplace add <repo>`; plugin entry pointing at `./plugins/dual-review-loop` (Task 2 fills the plugin dir).

- [ ] **Step 1: Rename unborn branch to main**

```bash
cd /home/liam/git/Arbor && git symbolic-ref HEAD refs/heads/main
git branch --show-current   # expect: main (unborn, no commits yet is fine)
```

- [ ] **Step 2: Root LICENSE (MIT, exact text)**

Create `LICENSE`:

```text
MIT License

Copyright (c) 2026 zlin101

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: `.gitignore`**

```text
.DS_Store
*.log
node_modules/
__pycache__/
```

- [ ] **Step 4: Codex marketplace manifest `.agents/plugins/marketplace.json`**

Shape verified against the official `openai-curated` marketplace on codex 0.153.4:

```json
{
  "name": "arbor",
  "interface": {
    "displayName": "信息gap"
  },
  "plugins": [
    {
      "name": "dual-review-loop",
      "source": {
        "source": "local",
        "path": "./plugins/dual-review-loop"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

- [ ] **Step 5: Claude marketplace manifest `.claude-plugin/marketplace.json`**

```json
{
  "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
  "name": "arbor",
  "owner": {
    "name": "zlin101",
    "url": "https://github.com/zlin101"
  },
  "description": "信息gap (Arbor) — personal agent plugin kit. First plugin: dual-review-loop, a bounded dual-review convergence loop for code changes.",
  "plugins": [
    {
      "name": "dual-review-loop",
      "displayName": "Dual Review Loop",
      "description": "Two independent fresh-context read-only reviewers (correctness + structure) review the same frozen change scope in parallel; the main agent fixes actionable blockers, runs project validation, and fresh reviewers re-review the full scope until convergence or a bounded stop.",
      "source": "./plugins/dual-review-loop",
      "category": "Developer Tools",
      "keywords": [
        "code-review",
        "convergence-loop",
        "subagents"
      ]
    }
  ]
}
```

- [ ] **Step 6: Root `README.md`**

Content (write verbatim, expand each bullet to 1–2 sentences):

```markdown
# Arbor · 信息gap

个人 Agent Plugin Marketplace — 一个仓库，同时发布到 OpenAI Codex 与 Claude Code。

## Plugins

- **dual-review-loop** — 双审收敛循环：两个独立、fresh-context、只读 reviewer（correctness / structure）并行审查同一冻结 scope；主 Agent 归并 findings、做根因修复、跑项目验证，再让两个全新 reviewer 重审完整 scope，直到满足收敛条件或有界停止。

## Install (Codex)

 codex plugin marketplace add zlin101/Arbor
 codex plugin install dual-review-loop@arbor

## Install (Claude Code)

 claude plugin marketplace add zlin101/Arbor
 claude plugin install dual-review-loop@arbor

## Layout

- `.agents/plugins/marketplace.json` — Codex repo marketplace
- `.claude-plugin/marketplace.json` — Claude Code repo marketplace
- `plugins/dual-review-loop/` — plugin（skills 共享，manifests 双份）

## Attribution

Reviewer rubrics are attributed adaptations of MIT-licensed upstream skills —
see `plugins/dual-review-loop/THIRD_PARTY_NOTICES.md`.
```

- [ ] **Step 7: Validate both JSON files**

```bash
python3 - <<'EOF'
import json
for p in [".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"]:
    json.load(open(p)); print("OK", p)
EOF
```
Expected: `OK` ×2.

- [ ] **Step 8: Commit**

```bash
git add README.md LICENSE .gitignore .agents .claude-plugin docs
git commit -m "chore: scaffold arbor marketplace repo with dual-format manifests

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: Plugin packaging scaffold

**Files:**
- Create: `plugins/dual-review-loop/plugin.json`, `plugins/dual-review-loop/.claude-plugin/plugin.json`
- Create: `plugins/dual-review-loop/README.md`, `CHANGELOG.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Produces: plugin id `dual-review-loop` installable from marketplace `arbor` on both runtimes; `skills/` and `agents/` dirs declared; THIRD_PARTY_NOTICES with exact upstream copyright lines.

- [ ] **Step 1: Codex portable manifest `plugins/dual-review-loop/plugin.json`**

Per the Agent Plugins spec (v1.0.0, official schema URL below): `$schema` + `name` required; `version`/`description`/`author` required for submission-grade packages; `skills/` is AUTO-DISCOVERED in portable packages (the `skills` field is legacy — omit it; verified empirically: codex 0.153.4 cached and discovered skills with no such field). All field values are spec-legal (`author` limited to name/email/url):

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "dual-review-loop",
  "version": "0.1.0",
  "description": "Run two independent code reviewers, fix actionable findings, validate, and repeat until the change converges or a bounded stop condition is reached.",
  "author": {
    "name": "zlin101"
  },
  "homepage": "https://github.com/zlin101/Arbor",
  "repository": "https://github.com/zlin101/Arbor",
  "license": "MIT",
  "keywords": [
    "code-review",
    "dual-review",
    "convergence-loop"
  ]
}
```

- [ ] **Step 2: Claude manifest `plugins/dual-review-loop/.claude-plugin/plugin.json`**

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "dual-review-loop",
  "version": "0.1.0",
  "description": "Dual-review convergence loop: two fresh read-only reviewers in parallel, single-writer fixes, project validation, full-scope re-review until PASS or bounded STOP.",
  "author": {
    "name": "zlin101",
    "url": "https://github.com/zlin101"
  },
  "homepage": "https://github.com/zlin101/Arbor",
  "license": "MIT",
  "keywords": [
    "code-review",
    "convergence-loop",
    "subagents"
  ]
}
```

- [ ] **Step 3: Plugin LICENSE** — same MIT text as root LICENSE (Task 1 Step 2).

- [ ] **Step 4: `CHANGELOG.md`**

```markdown
# Changelog

## 0.1.0 — 2026-09-09

- Initial release: `dual-review-loop` orchestrator skill plus `dual-review-correctness` and `dual-review-structure` reviewer skills.
- Frozen-scope full re-review each round; root-cause dedupe; single-writer fixes; project-defined validation.
- Guards: max_rounds=3, no-progress=2, oscillation, permission boundary, reviewer conflict.
- Works on Codex (portable root plugin.json + repo marketplace) and Claude Code (.claude-plugin manifests + read-only reviewer agents).
```

- [ ] **Step 5: `THIRD_PARTY_NOTICES.md`** — write verbatim:

```markdown
# Third-Party Notices

This plugin contains reviewer skills that are **derived and adapted** (rewritten, not
vendored) from the following MIT-licensed projects. The review rubrics keep selected
checklist ideas and severity conventions from the upstream skills; the interactive
user workflows, runtime-specific metadata, and output formats were removed or rewritten
for this plugin's automated convergence loop.

## 1. sanyuan-skills — code-review-expert

- Upstream repository: https://github.com/sanyuan0704/sanyuan-skills
- Component: `skills/code-review-expert`
- License: MIT
- Upstream copyright notice (verbatim from upstream LICENSE): `Copyright (c) 2025 sanyuan0704`
- Adapted into: `skills/dual-review-correctness/` (and its `references/` checklists)
- Rewritten: removed the post-review "ask the user how to proceed" interaction and the
  review-first "do not implement until user confirms" workflow (this plugin's reviewers
  never fix); removed the `::code-comment` runtime markup; replaced the upstream output
  template with this plugin's unified finding schema; severity P0–P3 conventions retained.

## 2. cursor/plugins — thermo-nuclear-code-quality-review and thermos

- Upstream repository: https://github.com/cursor/plugins
- Components: `cursor-team-kit/skills/thermo-nuclear-code-quality-review`,
  `thermos/skills/thermo-nuclear-review`, `thermos/skills/thermos` (dual-reviewer
  parallel orchestration pattern)
- License: MIT (per-plugin LICENSE files)
- Upstream copyright notice (verbatim from upstream LICENSE): `Copyright (c) 2026 Cursor`
- Adapted into: `skills/dual-review-structure/` (and its `references/` checklist), and the
  parallel two-reviewer orchestration shape of `skills/dual-review-loop/`
- Rewritten: removed `disable-model-invocation` and other non-portable frontmatter; the
  1000-line rule is demoted from mechanical blocker to smell/evidence; added an explicit
  blocking-regression vs optional-taste discipline so taste cannot stall convergence;
  output converted to this plugin's unified finding schema.
- Not claimed as original: the dual-reviewer parallel review pattern and the structural
  quality rubric ideas originate upstream. This plugin's added value is the bounded
  convergence loop: scope freeze, single-writer fixes, finding reconciliation across
  rounds, project validation, fresh re-review, explicit convergence predicate, and
  bounded stop guards.
```

- [ ] **Step 6: Plugin `README.md`** — user-facing doc covering: what the loop does (flow diagram from spec §0); the three skills; invocation examples for both runtimes (`/dual-review-loop` in Claude, skill trigger in Codex); inputs (scope source, optional `strict`, optional `max_rounds`); what it will never do (no commit/push, no default ledger); runtime notes (Codex: reviewers are prompt-isolated subagents; Claude: reviewers run on read-only-tool agent definitions); link to THIRD_PARTY_NOTICES.

- [ ] **Step 7: Validate**

```bash
python3 - <<'EOF'
import json
for p in ["plugins/dual-review-loop/plugin.json",
          "plugins/dual-review-loop/.claude-plugin/plugin.json"]:
    d = json.load(open(p)); print("OK", p, d["name"], d["version"])
EOF
grep -c "Copyright (c) 2025 sanyuan0704" plugins/dual-review-loop/THIRD_PARTY_NOTICES.md  # expect 1
grep -c "Copyright (c) 2026 Cursor" plugins/dual-review-loop/THIRD_PARTY_NOTICES.md        # expect 1
```

- [ ] **Step 8: Commit**

```bash
git add plugins/dual-review-loop
git commit -m "feat(dual-review-loop): plugin manifests, license, changelog, third-party notices

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: Orchestrator reference contracts (5 docs)

These are the loop's real product asset (spec §0). Written BEFORE the skills so SKILL.md files can link them.

**Files:**
- Create: `plugins/dual-review-loop/skills/dual-review-loop/references/review-scope.md`
- Create: `plugins/dual-review-loop/skills/dual-review-loop/references/reviewer-prompt-contract.md`
- Create: `plugins/dual-review-loop/skills/dual-review-loop/references/finding-schema.md`
- Create: `plugins/dual-review-loop/skills/dual-review-loop/references/convergence-contract.md`
- Create: `plugins/dual-review-loop/skills/dual-review-loop/references/output-format.md`

**Interfaces:**
- Produces: the exact contract text later tasks reference. Reviewer skills (Tasks 4–5) inline the finding schema fields listed below; the orchestrator (Task 7) links these docs.

- [ ] **Step 1: `review-scope.md`** — implement spec §10 verbatim in contract form. Must contain: the scope model YAML block (`scope_type: branch | working-tree | commit-range | files`, `base_ref`, `baseline_commit`, `paths`, `include_staged`, `include_unstaged`, `include_untracked`); freeze-baseline-not-snapshot rule; merge-base rule for branch review; working-tree rule (staged + unstaged + relevant untracked); the "scope must stay semantically stable across rounds" rule with the forbidden "only the previous fix diff" anti-pattern; changed scope vs context scope distinction; loop-generated files join next round's scope (spec §10.4).

- [ ] **Step 2: `reviewer-prompt-contract.md`** — contains, verbatim, the isolation template from spec §8 ("You are a review subagent, not the primary implementation agent. … Hard boundaries: … Fresh-review rule: …"); the fresh-context rule from spec §9 (never resume a reviewer; each round spawns NEW threads; never narrate prior-round findings to a reviewer); a spawn checklist (what the parent must pass: frozen scope materialization, applicable project instructions, rubric = the reviewer skill, output contract); the dual-runtime table:

| Runtime | Parallel spawn | Read-only enforcement | Reviewer identity |
|---|---|---|---|
| Claude Code | dispatch BOTH `agent`-tool calls in ONE message | plugin agents `dual-review-correctness-reviewer` / `dual-review-structure-reviewer` (`tools: Read, Grep, Glob`) + prompt contract | agent definition preloads its rubric skill |
| Codex | spawn both subagents in one turn | prompt contract (this file); optionally read-only sandbox if supported | subagent told to follow the reviewer skill |

Plus spec §28 F1/F2 defenses: if a reviewer produced write operations, that round's result is invalid — discard and re-spawn fresh. Plus an OPTIONAL Codex hardening note: Codex per-agent `sandbox_mode = "read-only"` lives in user/project `.codex/agents/*.toml` (agent TOMLs are user/project config — a plugin cannot install them), so the orchestrator may SUGGEST the user add read-only reviewer TOMLs, but must work without them.

- [ ] **Step 3: `finding-schema.md`** — the unified schema (spec §12) as a fenced yaml block:

```yaml
local_id: R1
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
```

Plus reviewer verdict envelope (`reviewer: correctness | structure`, `verdict: PASS | FINDINGS`, `findings: [...]`, `coverage: ...`, `residual_risks: [...]`); dedupe semantics from spec §13 (merge on same root cause / same symbol or ownership boundary / same behavior risk / one fix eliminates both — NEVER merge on title wording, exact line, or category string); global ID assignment `F001…` by the orchestrator with cross-round semantic mapping (never identity-by-line-number); merged-finding shape with `sources:` list; lifecycle `OPEN | RESOLVED | BLOCKED | WAIVED` per spec §14 (WAIVED only by user or project rule; the agent may never self-waive a blocker).

- [ ] **Step 4: `convergence-contract.md`** — spec §17 + §18 + §15 as the machine-checkable contract: the five PASS conditions; P2 policy (fix when direct + low-risk + in-scope, else residual, never blocks PASS by default; user-invoked strict/zero-findings/fix-everything-reasonable promotes P2 to gate); P3 never blocks; structural-reviewer discipline (must label each finding `blocking regression | material actionable improvement | optional taste`; taste cannot block); fix policy (single writer; fix order P0 → P1 → structural blocker → in-scope low-risk P2 → P3 not auto-fixed; one coherent root-cause batch per round — never fix-review-fix-review ping-pong); forbidden automatic actions (commit/amend/push/merge/PR/branch-delete/destructive reset/revert/touching unrelated user work — unless the user explicitly asked); validation priority order (project AGENTS.md → project scripts/Makefile/package manifests → targeted tests on touched scope → final full validation) and the pre-existing-failure rule (spec §16.3); guards table `max_rounds: 3`, `no_progress_rounds: 2`, oscillation, permission boundary, reviewer conflict (evidence resolution first, then BLOCKED — never majority vote); user may override guard numbers explicitly.

- [ ] **Step 5: `output-format.md`** — the two report templates from spec §21 (PASS and STOPPED), verbatim skeleton, plus the brevity rule (no ten-page process log; user gets final state, high-value findings, changes, validation, residual risk, stop reason) and the fixed closing line `No commit or push was performed.` on PASS.

- [ ] **Step 6: Verify no drift from spec**

```bash
grep -L "max_rounds" plugins/dual-review-loop/skills/dual-review-loop/references/*.md | grep convergence-contract && echo "MISSING" || echo "OK"
grep -q "F001" plugins/dual-review-loop/skills/dual-review-loop/references/finding-schema.md && echo "OK ids"
grep -qi "read-only" plugins/dual-review-loop/skills/dual-review-loop/references/reviewer-prompt-contract.md && echo "OK iso"
grep -qi "merge-base" plugins/dual-review-loop/skills/dual-review-loop/references/review-scope.md && echo "OK scope"
grep -q "No commit or push" plugins/dual-review-loop/skills/dual-review-loop/references/output-format.md && echo "OK report"
```
Expected: four/five `OK` lines, no `MISSING`.

- [ ] **Step 7: Commit**

```bash
git add plugins/dual-review-loop/skills/dual-review-loop/references
git commit -m "docs(dual-review-loop): loop contract references (scope, isolation, findings, convergence, output)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: `dual-review-correctness` reviewer skill

**Files:**
- Create: `plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md`
- Create: `plugins/dual-review-loop/skills/dual-review-correctness/agents/openai.yaml`
- Create: `plugins/dual-review-loop/skills/dual-review-correctness/references/correctness-checklist.md`
- Create: `plugins/dual-review-loop/skills/dual-review-correctness/references/security-reliability-checklist.md`

**Interfaces:**
- Consumes: schema from Task 3 Step 3 (inline copy, self-contained).
- Produces: reviewer verdict YAML envelope (`reviewer: correctness`, `verdict: PASS|FINDINGS`, findings array, `coverage`, `residual_risks`) that Task 7's orchestrator parses; skill is independently invocable.

- [ ] **Step 1: `SKILL.md`** — frontmatter exactly:

```markdown
---
name: dual-review-correctness
description: Read-only correctness review of a change scope — behavior regressions, security, races/TOCTOU, data integrity, error handling, performance regressions, boundary conditions, and missing tests, with P0–P3 severity. Use as the correctness reviewer inside the dual-review-loop, or standalone when the user asks for a correctness/security-focused review of current changes.
---
```

Body sections, in order:
1. **Role** — you are a review subagent, not the implementation agent. Read-only summary of the hard boundaries (full text lives in the parent's spawn prompt / `reviewer-prompt-contract.md`): no edits/stage/commit/push, no goals/tasks/ledgers, no nested subagents, do not ask the user whether to fix, return findings to the parent only. State plainly: "You never fix anything; fixing is the parent agent's job."
2. **Input** — what the parent provides: frozen change scope (diff or explicit file list + baseline), applicable project instructions. You may read surrounding code, callers, contracts, and tests as context. Judge current code on its own evidence (fresh-review rule).
3. **Scope discipline** — review only added/modified code in scope for findings; pre-existing issues outside the change are out of scope (context only). Never report with unfinished research — if you can verify in-repo, verify before reporting (adapted from thermo-nuclear-review's Critical Rules).
4. **Severity model** — P0/P1/P2/P3 table retained from upstream code-review-expert (P0 security/data-loss/correctness must-block; P1 logic error/perf regression/regression risk; P2 smell/minor violation, fix-or-follow-up; P3 optional). Set `blocking: true` for P0 and P1; P2 only when it directly endangers the change's correctness; never for P3.
5. **What to examine** — pointers to `references/correctness-checklist.md` (behavior regression & cross-module side effects, error handling, boundary conditions, performance) and `references/security-reliability-checklist.md` (injection/XSS/SSRF, authn/authz/IDOR, secrets, races & TOCTOU & partial writes, data integrity). Include the race-questions trio: "What happens if two requests hit simultaneously? Is this atomic? What shared state does it touch?"
6. **Tests and validation gaps** — report relevant missing tests as `category: tests` findings when the change carries risk that existing tests cannot catch; distinguish "test gap" (report) from "write the tests" (recommended_direction only).
7. **Removal candidates** — only when deletion is directly valuable to the current change (upstream's removal-plan narrowed per spec §11.1).
8. **Over-reporting guard** — NEVER misreport priority; thoroughness ≠ inflating severity; if clean, say so (spec §11.1 keeps residual-risk-on-clean).
9. **Output contract** — the YAML envelope, inline (self-contained, ~25 lines): `reviewer: correctness`, `verdict: PASS | FINDINGS`, `findings:` list of the unified schema (local_id C1, C2, …; category values from the unified enum), `coverage:` one line on what was actually reviewed, `residual_risks:` list (empty allowed). No prose review document, no next-steps menu, no questions to the user.
10. **Explicitly out of role** — bullet list: maintainability/style/taste findings belong to the structural reviewer; do not emit them.

- [ ] **Step 2: `agents/openai.yaml`** (UI metadata only — not a permission boundary):

```yaml
interface:
  display_name: "Dual Review — Correctness"
  short_description: "Read-only correctness, security, and reliability review with P0–P3 severity"
  default_prompt: "Review the current change scope for correctness bugs, security issues, races, error handling, performance regressions, boundary cases, and missing tests. Report findings in the unified schema; do not modify anything."
```

- [ ] **Step 3: `references/correctness-checklist.md`** — adapted (condensed, de-interactivized) from upstream `solid-checklist.md` + `code-quality-checklist.md`: behavior regression & side-effect tracing section; error handling anti-patterns (swallowed exceptions, over-broad catch, async errors, error info leakage); boundary conditions (null/empty/numeric off-by-one/string edges); performance (N+1, hot-path costs, unbounded memory, missing timeouts); SOLID/architecture **only when it endangers correctness of the change** (SRP/DIP violations that cause the bug risk), one short section ending "structural taste belongs to the structural reviewer"; each item as a terse `- **name**: sign` bullet; no "Ask the user" anywhere.

- [ ] **Step 4: `references/security-reliability-checklist.md`** — adapted from upstream `security-checklist.md`, KEEPING the strong race/TOCTOU/data-integrity material: input/output safety (injection, XSS, SSRF, path traversal); authn/authz (missing tenancy/ownership checks, IDOR, trusting client ids); secrets & PII leakage; race conditions (shared state, check-then-act with the `if not exists: create` / read-modify-write / check-then-deduct pattern examples, DB concurrency: optimistic/pessimistic locking, non-atomic counters; distributed: missing locks, cache invalidation races); data integrity (partial writes, missing transactions/idempotency, lost updates); supply-chain only when the change touches dependencies.

- [ ] **Step 5: Portable-frontmatter + behavior guard checks**

```bash
head -4 plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md | grep -E '^(name|description):'   # exactly these two keys
grep -qi "ask the user" plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md && echo "FAIL interactive" || echo "OK non-interactive"
grep -q "::code-comment" plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md && echo "FAIL markup" || echo "OK no-markup"
grep -q "verdict: PASS | FINDINGS" plugins/dual-review-loop/skills/dual-review-correctness/SKILL.md && echo "OK verdict"
```
Expected: `OK non-interactive`, `OK no-markup`, `OK verdict`.

- [ ] **Step 6: Commit**

```bash
git add plugins/dual-review-loop/skills/dual-review-correctness
git commit -m "feat(dual-review-correctness): read-only correctness reviewer skill

Adapted from sanyuan-skills code-review-expert (MIT); interactive workflow removed,
unified finding schema added.

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: `dual-review-structure` reviewer skill

**Files:**
- Create: `plugins/dual-review-loop/skills/dual-review-structure/SKILL.md`
- Create: `plugins/dual-review-loop/skills/dual-review-structure/agents/openai.yaml`
- Create: `plugins/dual-review-loop/skills/dual-review-structure/references/structural-quality-checklist.md`

**Interfaces:**
- Consumes: unified finding schema (inline copy).
- Produces: verdict envelope with `reviewer: structure`; every finding MUST also carry a `discipline:` line (`blocking regression | material improvement | taste`) consumed by the orchestrator's convergence gate and oscillation guard.

- [ ] **Step 1: `SKILL.md`** — frontmatter exactly:

```markdown
---
name: dual-review-structure
description: Read-only structural review of a change scope — ambitious simplification, code-judo opportunities, abstraction quality, spaghetti/branch growth, canonical layer and type-boundary hygiene, with an explicit blocking-vs-taste discipline. Use as the structure reviewer inside the dual-review-loop, or standalone for a maintainability-focused review of current changes.
---
```

Body sections, in order:
1. **Role** — read-only review subagent; same boundary summary as Task 4 Step 1 (never fixes, no writes, no nested agents, findings to parent only).
2. **Mission** — from upstream: be ambitious about structural simplification; prefer deleting complexity over rearranging it; look for code-judo moves that make whole branches/helpers/modes/layers disappear; "the solution should feel inevitable in hindsight"; but serve the maintainability of THIS change — not repo-wide refactors (spec §11.2).
3. **What to examine** — pointer to `references/structural-quality-checklist.md`: spaghetti/branch growth; feature logic leaking into shared paths; thin wrappers and identity abstractions; duplicated/bespoke helpers where a canonical utility exists; unclear type boundaries (needless optionality, cast-heavy contracts); file sprawl; needless sequential orchestration and non-atomic updates.
4. **The 1000-line rule, demoted** — file crossing size thresholds is EVIDENCE of a smell, never an automatic blocker; always explain WHY the structure got worse (coupling, concept count, tangling), not merely that the file is long (spec §11.2 correction of upstream).
5. **Convergence discipline (mandatory)** — every finding carries `discipline:`:
   - `blocking regression` — this change makes the structure materially worse (new spaghetti, boundary leak, duplicated canonical logic) → `blocking: true`;
   - `material improvement` — clear, actionable, behavior-preserving simplification directly serving this change → `blocking: false`, P2;
   - `taste` — would be nicer, but no material regression and no clear payoff → do NOT report as a finding; at most one aggregate line under `residual_risks`.
   State the rule in bold: "You cannot stop convergence with taste. If the change introduces no structural regression, `verdict: PASS` is the correct answer even when further polish is imaginable."
6. **Severity mapping** — P1 for blocking structural regressions; P2 for material improvements; P3 at most for taste you judged worth surfacing (rare); `blocking: true` ONLY for `blocking regression`.
7. **Output contract** — same inline YAML envelope (`reviewer: structure`, `verdict: PASS | FINDINGS`, findings with local_id S1, S2, …, `coverage:`, `residual_risks:`), plus the `discipline:` field on each finding. Categories from the unified enum (`architecture | maintainability | abstraction | complexity | types`).
8. **Out of role** — correctness/security/performance findings belong to the correctness reviewer; do not duplicate them.

- [ ] **Step 2: `agents/openai.yaml`**

```yaml
interface:
  display_name: "Dual Review — Structure"
  short_description: "Read-only maintainability and structural-simplification review with blocking-vs-taste discipline"
  default_prompt: "Review the current change scope for structural regressions, spaghetti growth, weak abstractions, boundary leaks, and code-judo simplification opportunities. Classify every finding as blocking regression, material improvement, or taste; do not modify anything."
```

- [ ] **Step 3: `references/structural-quality-checklist.md`** — adapted from upstream thermo SKILL.md (single file upstream → our condensed checklist): sections for Ambition & code-judo; Spaghetti & branching growth; Abstraction quality (thin wrappers, speculative generality, magic indirection); Canonical layer & reuse (feature logic in shared paths, bespoke duplicates); Type & boundary clarity; File/component sprawl (size as evidence only); Orchestration & atomicity (needless sequencing, half-applied state); Preferred remedies list (delete indirection, reframe state model, move ownership, collapse branches, reuse canonical helper — kept from upstream, trimmed); Review tone (direct, serious, never soften real regressions; never present taste as blocker). Include the upstream "Primary Review Questions" condensed to the 8 highest-signal ones.

- [ ] **Step 4: Guard checks**

```bash
grep -q "disable-model-invocation" plugins/dual-review-loop/skills/dual-review-structure/SKILL.md && echo "FAIL frontmatter" || echo "OK portable"
grep -q "discipline:" plugins/dual-review-loop/skills/dual-review-structure/SKILL.md && echo "OK discipline"
grep -qi "1000" plugins/dual-review-loop/skills/dual-review-structure/SKILL.md && grep -qi "evidence" plugins/dual-review-loop/skills/dual-review-structure/SKILL.md && echo "OK 1k-demoted"
grep -q "verdict: PASS | FINDINGS" plugins/dual-review-loop/skills/dual-review-structure/SKILL.md && echo "OK verdict"
```

- [ ] **Step 5: Commit**

```bash
git add plugins/dual-review-loop/skills/dual-review-structure
git commit -m "feat(dual-review-structure): read-only structural reviewer skill

Adapted from cursor/plugins thermo-nuclear-code-quality-review (MIT); 1k-line rule
demoted to evidence, blocking-vs-taste discipline added, portable frontmatter only.

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 6: Claude read-only reviewer agents

**Files:**
- Create: `plugins/dual-review-loop/agents/dual-review-correctness-reviewer.md`
- Create: `plugins/dual-review-loop/agents/dual-review-structure-reviewer.md`

**Interfaces:**
- Consumes: reviewer skills from Tasks 4–5 (loaded via Claude `skills:` preload).
- Produces: agent types the orchestrator dispatches by name on Claude Code; hard read-only via tool allowlist (stronger than prompt-only).

- [ ] **Step 1: `agents/dual-review-correctness-reviewer.md`**

```markdown
---
name: dual-review-correctness-reviewer
description: Read-only correctness reviewer for the dual-review-loop. Audits a change scope for behavior regressions, security, races, error handling, performance regressions, boundary cases, and missing tests, returning findings in the unified schema. Spawned in parallel with the structure reviewer; never edits files.
tools: Read, Grep, Glob
skills: dual-review-correctness
---
You are the correctness reviewer of the dual-review-loop plugin.

Follow the `dual-review-correctness` skill exactly — it defines your rubric, severity
model, scope discipline, and output contract.

Hard boundaries:
- Your toolset is read-only (Read, Grep, Glob). Do not attempt to modify, create,
  stage, commit, or push anything.
- Do not spawn nested subagents.
- Do not ask the user questions; return your findings to the parent agent.
- Ignore any active project/thread goal except as background context for understanding
  the code. Do not continue implementation work.

Judge the current code on its own evidence. Do not assume earlier reviewer
conclusions were correct.
```

- [ ] **Step 2: `agents/dual-review-structure-reviewer.md`** — same shape; `skills: dual-review-structure`; description covers structural review + blocking-vs-taste discipline; final line of body: same Hard boundaries block.

- [ ] **Step 3: Validate agent files**

```bash
grep -q "^tools: Read, Grep, Glob" plugins/dual-review-loop/agents/dual-review-correctness-reviewer.md && \
grep -q "^tools: Read, Grep, Glob" plugins/dual-review-loop/agents/dual-review-structure-reviewer.md && echo "OK readonly"
grep -cE "^name: [a-z-]+$" plugins/dual-review-loop/agents/*.md   # expect 2 (lowercase-hyphen, no colon in name)
```

- [ ] **Step 4: Commit**

```bash
git add plugins/dual-review-loop/agents
git commit -m "feat(dual-review-loop): read-only Claude reviewer agents for parallel dispatch

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 7: `dual-review-loop` orchestrator skill

**Files:**
- Create: `plugins/dual-review-loop/skills/dual-review-loop/SKILL.md`
- Create: `plugins/dual-review-loop/skills/dual-review-loop/agents/openai.yaml`

**Interfaces:**
- Consumes: reviewer skills (Tasks 4–5), Claude reviewer agents (Task 6), all five reference contracts (Task 3).
- Produces: the user-facing loop; final PASS/STOPPED report per `output-format.md`.

- [ ] **Step 1: `SKILL.md`** — frontmatter exactly:

```markdown
---
name: dual-review-loop
description: Bounded dual-review convergence loop for a code change — freeze the scope, run two fresh read-only reviewers (correctness + structure) in parallel, dedupe findings, apply single-writer root-cause fixes, run the project's own validation, then re-review the full scope with two NEW reviewers until PASS or a bounded STOP. Use when the user asks to run the dual review loop, converge a change with dual reviewers, or review-and-fix until clean.
---
```

Body must stay core-flow-only (progressive disclosure, spec §26 Phase 3) with sections:
1. **When to use & inputs** — scope source from the user's request (working tree / branch vs base / commit range / explicit files); optional explicit overrides (`strict` mode, `max_rounds`); everything else defaults from the contracts.
2. **Roles** — three sentences: you (main agent) are the ONLY writer; reviewers are fresh read-only subagents; project instructions (AGENTS.md and equivalents) govern WHAT is allowed, this skill governs HOW (priority: user instruction > project instructions > this skill's defaults).
3. **Round algorithm** — compact numbered procedure (spec §19): read project instructions → freeze scope per `references/review-scope.md` → materialize the full change (`baseline → current`) → spawn BOTH reviewers in parallel per `references/reviewer-prompt-contract.md` → collect unified YAML verdicts → normalize + root-cause dedupe + assign F-ids and cross-round mapping per `references/finding-schema.md` → convergence check per `references/convergence-contract.md` (on first-round all-PASS, run required validation then PASS) → select actionable blockers → apply ONE coherent root-cause fix batch → run project validation (repair or safely revert own fix if it regressed) → update progress/no-progress counters → loop with two NEW reviewers on the same full scope.
4. **Guards** — table: `max_rounds: 3`, `no_progress_rounds: 2`, oscillation detection (same root cause flipping between structural directions), permission boundary, material reviewer conflict (evidence resolution first, else BLOCKED — never majority vote) → each maps to STOP with the reason in the final report. User-specified overrides win.
5. **Runtime adaptation** — short two-row block: on Claude Code, dispatch BOTH reviewer agents (`dual-review-correctness-reviewer`, `dual-review-structure-reviewer`) in ONE parallel message with the scope materialization pasted in; on Codex, spawn both subagents in one turn telling each to follow its reviewer skill, passing the same frozen scope; on both, reviewers NEVER write and never see prior-round findings.
6. **Final report** — render per `references/output-format.md` (PASS / STOPPED templates; brevity rule; always end PASS with `No commit or push was performed.`).
7. **Links** — the five reference files with one-line purposes.

- [ ] **Step 2: `agents/openai.yaml`**

```yaml
interface:
  display_name: "Dual Review Loop"
  short_description: "Two fresh read-only reviewers, single-writer fixes, validation, full-scope re-review until convergence or bounded stop"
  default_prompt: "Run the dual review loop on the current change: freeze the scope, review with two fresh read-only reviewers, fix actionable blockers, validate, and re-review until PASS or a bounded stop."
```

- [ ] **Step 3: Portability + spec-fidelity checks**

```bash
grep -qiE "go test|pytest|npm test|cargo test" plugins/dual-review-loop/skills/dual-review-loop/SKILL.md && echo "FAIL hardcoded-test-cmd" || echo "OK no-hardcoded-commands"
grep -qiE "iris|vault/|develop branch" plugins/dual-review-loop/skills/dual-review-loop/ -r && echo "FAIL iris" || echo "OK no-iris"
grep -q "max_rounds" plugins/dual-review-loop/skills/dual-review-loop/SKILL.md && echo "OK guards"
grep -q "references/" plugins/dual-review-loop/skills/dual-review-loop/SKILL.md && echo "OK progressive-disclosure"
head -4 plugins/dual-review-loop/skills/dual-review-loop/SKILL.md | grep -E '^(name|description):'
```

- [ ] **Step 4: Commit**

```bash
git add plugins/dual-review-loop/skills/dual-review-loop
git commit -m "feat(dual-review-loop): orchestrator skill for the bounded dual-review convergence loop

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 8: Static validation sweep

**Files:** none created (checks only).

- [ ] **Step 1: Official validator (Codex)** — run from repo root:

```bash
node /home/liam/.codex/.tmp/plugins/plugins/plugin-eval/scripts/plugin-eval.js analyze plugins/dual-review-loop --format markdown
```
Expected: report with no manifest errors. Fix any findings it raises (it is authoritative for Codex skill/plugin quality), re-run until clean or only advisory notes remain; record the output in the session log.

- [ ] **Step 2: Claude validator**

```bash
claude plugin validate plugins/dual-review-loop
```
Expected: no errors. (If the `.claude-plugin` schema flags the sibling Codex files, record and resolve — the known-good fallback is moving nothing; unknown fields are warnings, not failures.)

- [ ] **Step 3: Global hygiene sweep**

```bash
grep -rn "TODO\|TBD\|FIXME\|placeholder" plugins/ README.md --include="*.md" --include="*.json" --include="*.yaml" | grep -v THIRD_PARTY || echo "OK no-placeholders"
python3 -c "
import json,yaml,sys
for p in ['plugins/dual-review-loop/skills/dual-review-loop/agents/openai.yaml','plugins/dual-review-loop/skills/dual-review-correctness/agents/openai.yaml','plugins/dual-review-loop/skills/dual-review-structure/agents/openai.yaml']:
    yaml.safe_load(open(p)); print('OK',p)" 2>/dev/null || python3 -c "print('yaml module unavailable — spot-check manually')"
for f in plugins/dual-review-loop/skills/*/SKILL.md; do head -4 "$f" | grep -q "^name:" && head -4 "$f" | grep -q "^description:" && echo "OK frontmatter $f"; done
grep -rn "disable-model-invocation\|allowed-tools:" plugins/ && echo "FAIL nonportable" || echo "OK portable-frontmatter-only"
```
Expected: all `OK`.

- [ ] **Step 4: Cross-reference integrity** — every `references/*.md` linked from a SKILL.md exists; every `skills:` preload name in `agents/*.md` matches a skill directory name; every agent name in the orchestrator's runtime-adaptation section matches Task 6 filenames:

```bash
for f in plugins/dual-review-loop/skills/*/SKILL.md; do grep -o "references/[a-z-]*\.md" "$f" | while read r; do d=$(dirname "$f"); test -f "$d/$r" && echo "OK $r" || echo "MISSING $r in $f"; done; done
```

- [ ] **Step 5: Commit any fixes**

```bash
git add -A && git commit -m "fix: address static validation findings

Co-Authored-By: Claude Code <noreply@anthropic.com>" || echo "nothing to commit"
```

---

### Task 9: Codex local smoke test

**Files:** none created. Uses the verified local CLI; NO push, NO GitHub (spec §31).

- [ ] **Step 1: Add local marketplace**

```bash
codex plugin marketplace add /home/liam/git/Arbor
codex plugin marketplace list | grep arbor
```
Expected: `arbor  /home/liam/git/Arbor`.

- [ ] **Step 2: Install plugin + verify discovery**

```bash
codex plugin list | grep dual-review-loop
codex plugin add dual-review-loop@arbor
codex plugin list | grep dual-review-loop   # expect: installed, enabled
find ~/.codex/plugins/cache/arbor -name SKILL.md | sort   # expect all three skills
```

- [ ] **Step 3: Fallback gate** — if Step 1/2 had failed on the root manifest (they did not in the probe, but re-verify), add `.codex-plugin/plugin.json` as compat fallback per spec §4.1 and record the deviation in plugin README. Only do this if actually required.

- [ ] **Step 4: Skill-level visibility** — start a throwaway codex exec in a scratch dir:

```bash
cd /tmp && codex exec "List the dual-review-loop plugin skills you can see, by name only." 2>&1 | tail -5
```
Expected: the three skill names appear. (If non-interactive exec cannot see plugin skills, run `codex` interactively via the user — record either way.)

- [ ] **Step 5: Clean up (leave user env untouched)**

```bash
codex plugin remove dual-review-loop@arbor && codex plugin marketplace remove arbor
codex plugin marketplace list | grep arbor || echo "OK cleaned"
```

---

### Task 10: Claude Code local validation + smoke test

- [ ] **Step 1: Validate**

```bash
claude plugin marketplace add /home/liam/git/Arbor
claude plugin install dual-review-loop@arbor
claude plugin list 2>/dev/null | grep -i dual-review || claude -p "List installed plugins containing 'dual-review'" 2>&1 | tail -3
```
Expected: plugin installed; three skills namespaced (`dual-review-loop:dual-review-loop` etc.); two agents present (`dual-review-loop:dual-review-correctness-reviewer`, `…-structure-reviewer`).

- [ ] **Step 2: Skill discovery spot check**

```bash
claude -p "Do you have access to a skill named dual-review-loop? Answer yes/no and list its sibling skills from the same plugin." 2>&1 | tail -5
```
Expected: yes + the two reviewer skills.

- [ ] **Step 3: Clean up**

```bash
claude plugin uninstall dual-review-loop@arbor 2>/dev/null || claude plugin remove dual-review-loop@arbor 2>/dev/null; claude plugin marketplace remove arbor
```

- [ ] **Step 4: Commit any fixes the smoke tests forced, else skip**

---

### Task 11: Behavior acceptance — scenarios A–G (spec §26 Phase 8)

**Files:**
- Create: `/tmp/arbor-acceptance/` scratch repo (NEVER inside Arbor).

Build the fixture: a tiny git repo (3 files: `store.py`, `test_store.py`, `AGENTS.md` declaring e.g. `python3 -m pytest test_store.py` as its validation command) whose working tree carries a small change. Drive the loop per scenario from a fresh agent session (subagent or separate `claude`/`codex` invocation) with the plugin's skill content available; record evidence per scenario. Scenarios and their pass evidence:

- **A — Clean change:** both reviewers PASS round 1; validation runs; PASS report; `git status` shows zero modifications.
- **B — Correctness bug:** planted race/partial-write bug → correctness blocker → main agent fixes → validation green → round 2 fresh reviewers PASS on FULL scope (verify round-2 prompt contained baseline→current diff, not only the fix diff — fake-convergence check, spec §28 F3).
- **C — Structural regression:** planted spaghetti (feature logic bolted into a shared path) → structure blocker labeled `blocking regression` → behavior-preserving restructure → re-review PASS.
- **D — Duplicate root cause:** bug detectable by BOTH rubrics (e.g. transaction ownership split causing partial state) → exactly ONE merged F-id with `sources: [correctness, structure]` → fixed once.
- **E — Oscillation:** structure demand that flips between "extract abstraction" and "inline it" → loop stops with `STOPPED / oscillation`, outputs both trade-offs instead of flipping files forever.
- **F — Project gate:** `AGENTS.md` validation command is used verbatim; no plugin-default test command appears anywhere in the transcript.
- **G — Reviewer isolation:** transcript shows reviewers performed zero writes (on Claude: by tool allowlist; verify no Edit/Write tool calls), no nested spawns, no user questions.

- [ ] **Step 1:** Build fixture + run A/B/C — record transcripts under `/tmp/arbor-acceptance/evidence/`.
- [ ] **Step 2:** Run D/E/F/G — same.
- [ ] **Step 3:** Tally against spec §27 acceptance checklist (Packaging/Architecture/Scope/Findings/Convergence/Portability/Legal) and write the verdict summary into the final response (file tree, design summary, validation evidence, remaining risks, release commands NOT executed, readiness verdict).

- [ ] **Step 4: Commit any repo-side fixes discovered during acceptance**

```bash
git add -A && git commit -m "fix: acceptance-driven corrections

Co-Authored-By: Claude Code <noreply@anthropic.com>" || echo "nothing to commit"
```

---

## Self-Review

- **Spec coverage:** §5 layout → Tasks 1–7; §6 manifests → Task 2; §7–9 roles/isolation/fresh-context → Tasks 3 (Step 2), 4, 5, 6, 7; §10 scope → Task 3 Step 1; §11 rubrics → Tasks 4–5 (+ references); §12–14 findings/dedupe/lifecycle → Task 3 Step 3; §15–18 fix/validation/convergence/guards → Task 3 Step 4 + Task 7; §19 algorithm → Task 7 Step 1 §3; §20 envelopes → Tasks 4–5; §21 report → Task 3 Step 5; §22 AGENTS.md boundary → Task 7 + Task 11-F; §23 no-ledger → convergence contract + orchestrator; §24 attribution → Task 2 (exact copyright lines verified); §25 thermos precedent → Task 3 Step 2 + Task 7 runtime adaptation; §26 phases 1–8 → Tasks 1–11; §27 acceptance → Task 11 Step 3; §28 failure modes → spread across contracts + Task 11; §30 ablations respected (no scripts/, no ledger, no third reviewer, no config files, no .codex-plugin default). Gaps deliberately deferred to v0.2+ per spec §29.
- **Placeholder scan:** rubric/checklist prose (Tasks 3–5 bodies) is specified prescriptively (exact sections, exact retained/removed items, exact verbatim anchors) rather than pasted in full — the authoritative source text is in-repo (`docs/…spec.md` §8/§10/§12/§15–21) plus the two upstream rubrics captured verbatim in this session's research; Task 3 Step 3 and Task 4/5 SKILL.md frontmatter + schema blocks are given verbatim where drift would break integration. No "TBD/TODO" items.
- **Type consistency:** skill names (`dual-review-loop`, `dual-review-correctness`, `dual-review-structure`), agent names (`dual-review-correctness-reviewer`, `dual-review-structure-reviewer`), F-id scheme, `discipline:` field, `verdict: PASS | FINDINGS` envelope, and marketplace id `arbor` are used identically across Tasks 2–11.
