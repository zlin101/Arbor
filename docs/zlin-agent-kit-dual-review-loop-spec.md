# Zlin Agent Kit — `dual-review-loop` 项目实施规范

> 状态：Implementation Ready  
> 日期：2026-09-09  
> 工作仓库名：`zlin-agent-kit`（如 Owner 后续决定其他品牌名，可整体重命名；不要因此阻塞实现）  
> Marketplace 名：`zlin-agent-kit`  
> 首个 Plugin：`dual-review-loop`  
> 目标读者：负责实际创建、实现、验证该项目的 Coding Agent

---

## 0. 执行摘要

本项目不是“把两个 Review Skill 放到同一个目录”。

本项目要实现的是一个**有界、可验证、自动收敛的双审代码质量循环**：

```text
freeze scope
    ↓
spawn 2 fresh read-only reviewers in parallel
    ↓
normalize + dedupe + classify findings
    ↓
main agent fixes actionable blockers
    ↓
run project-defined validation
    ↓
spawn 2 NEW reviewers on the SAME full scope
    ↓
compare finding set
    ↓
PASS / continue / STOP
```

两个 reviewer 的职责互补：

1. **Correctness reviewer**
   - 灵感/来源：`sanyuan0704/sanyuan-skills` 的 `code-review-expert`
   - 重点：correctness、security、reliability、SOLID、error handling、performance、boundary cases、missing tests。

2. **Structural reviewer**
   - 灵感/来源：`cursor/plugins` 的 `thermo-nuclear-code-quality-review`
   - 重点：结构简化、抽象质量、spaghetti growth、错误 ownership/layer、过度 branching、无价值 wrapper、类型边界、可维护性、code-judo 式复杂度删除。

**真正的产品资产不是这两个 rubric，而是 Convergence Contract：**
- 谁能写代码；
- review scope 如何冻结；
- findings 如何归并；
- 一轮如何修；
- 下一轮如何重新审；
- 什么叫“已经收敛”；
- 什么情况下必须停下并交还给人。

---

# 1. 项目目标

## 1.1 Primary Goal

创建一个可通过 Codex Plugin Marketplace 安装的 `dual-review-loop` 插件，使用户能够在任意目标代码仓库内触发：

> 使用两个独立、fresh-context、read-only reviewer 并行审查同一个 change scope；主 Agent 汇总问题、执行安全修复、运行验证，再让两个新的 reviewer 重新审查，直到满足明确的收敛条件或触发停止条件。

## 1.2 Product promise

一次正常执行应该提供以下性质：

- **Multi-perspective**：正确性/安全与结构/可维护性分开审。
- **Fresh review**：每一轮都新开 reviewer，避免被上一轮答案锚定。
- **Single writer**：只有主 Agent/Fixer 修改代码。
- **Stable scope**：每轮审的是同一个“目标变更”的当前完整状态，而不是只看上一轮新增 diff。
- **Bounded**：不会无限 review/fix。
- **Project-aware**：遵循目标仓库自己的 `AGENTS.md`、测试门禁和授权边界。
- **Portable**：不依赖 Iris，不硬编码某个项目、语言、branch 或测试命令。
- **Auditable**：最终明确报告修了什么、还剩什么、运行了哪些验证、为什么结束。

---

# 2. 非目标（v0.1 必须克制）

以下能力 **不要在 v0.1 实现**：

- 不做通用 workflow engine。
- 不做数据库。
- 不做跨 session 持久化 finding 状态机。
- 不默认创建 review ledger 文件。
- 不做 Web UI。
- 不做 MCP server。
- 不做 hooks。
- 不做 CI service。
- 不做 GitHub App。
- 不做自动 PR merge。
- 不自动 commit/push。
- 不做 reviewer 投票系统。
- 不引入第三个常驻 verifier reviewer。
- 不实现动态 reviewer marketplace。
- 不实现复杂 YAML 配置系统。
- 不同时维护 Cursor 专用 manifest。
- 不硬编码 Iris 的 `vault/`、TASK 编号、G1/G2/G3/G4、`develop`、`go test ./...` 等任何项目细节。

如果未来需求证明这些能力有价值，再增加；不要为了“以后可能需要”提前设计。

---

# 3. 命名

## 3.1 Repository

推荐工作名：

```text
zlin-agent-kit
```

原因：
- 带有 Owner 的个人 flag；
- 不绑定 Codex 单一产品；
- 能容纳未来多个 plugin；
- 比 `codex-workflows` 更有归属感，又不会像纯品牌词那样让用途不可理解。

若 Owner 已经指定新名字，遵循 Owner，不要争论命名。

## 3.2 Marketplace

```text
zlin-agent-kit
```

显示名：

```text
Zlin Agent Kit
```

## 3.3 Plugin

```text
dual-review-loop
```

## 3.4 Skills

建议暴露三个 skills：

```text
dual-review-loop
dual-review-correctness
dual-review-structure
```

不要直接使用上游 skill slug 作为内部名称，原因：
- 避免与用户已安装的 standalone skill 冲突；
- 明确它们是为本 loop 重写/适配的 reviewer；
- 允许去掉与自动 loop 冲突的上游交互规则；
- 仍在 `THIRD_PARTY_NOTICES.md` 中完整 attribution。

---

# 4. 官方实现基线

实现前应再次核对当时最新官方文档，但当前基线如下。

## 4.1 Portable plugin

优先使用插件根目录：

```text
plugin.json
```

而不是把 `.codex-plugin/plugin.json` 作为主 manifest。

当前 OpenAI 文档将 root `plugin.json` 定义为 portable Agent Plugins package；`.codex-plugin/plugin.json` 仍是兼容 fallback。

**v0.1 先只实现 portable manifest。**

只有实际 smoke test 证明当前目标 Codex 客户端仍需要兼容 manifest 时，才额外添加：

```text
.codex-plugin/plugin.json
```

不要双写两份 manifest 作为默认方案。

## 4.2 Marketplace

Repo marketplace：

```text
<repo-root>/.agents/plugins/marketplace.json
```

插件目录：

```text
<repo-root>/plugins/<plugin-name>/
```

一个 marketplace 可以管理多个 plugins，因此不要每个 workflow 建一个 GitHub repo。

## 4.3 Marketplace CLI

目标安装体验：

```bash
codex plugin marketplace add zlin101/zlin-agent-kit
codex plugin marketplace list
codex plugin marketplace upgrade zlin-agent-kit
```

发布前以实际 CLI 帮助和官方文档验证命令。

## 4.4 Skills

每个 skill 至少：

```text
skill-name/
├── SKILL.md
└── agents/
    └── openai.yaml
```

`SKILL.md` frontmatter 对 Codex 适配版保持：

```yaml
---
name: ...
description: ...
---
```

不要把 Cursor/Claude 特有字段原样带过来。

`agents/openai.yaml` 是 UI/产品元数据，**不是权限边界**。

---

# 5. 推荐仓库结构

```text
zlin-agent-kit/
├── README.md
├── LICENSE
├── .gitignore
│
├── .agents/
│   └── plugins/
│       └── marketplace.json
│
└── plugins/
    └── dual-review-loop/
        ├── plugin.json
        ├── README.md
        ├── CHANGELOG.md
        ├── LICENSE
        ├── THIRD_PARTY_NOTICES.md
        │
        └── skills/
            ├── dual-review-loop/
            │   ├── SKILL.md
            │   ├── agents/
            │   │   └── openai.yaml
            │   └── references/
            │       ├── convergence-contract.md
            │       ├── finding-schema.md
            │       ├── review-scope.md
            │       ├── reviewer-prompt-contract.md
            │       └── output-format.md
            │
            ├── dual-review-correctness/
            │   ├── SKILL.md
            │   ├── agents/
            │   │   └── openai.yaml
            │   └── references/
            │       ├── correctness-checklist.md
            │       └── security-reliability-checklist.md
            │
            └── dual-review-structure/
                ├── SKILL.md
                ├── agents/
                │   └── openai.yaml
                └── references/
                    └── structural-quality-checklist.md
```

### 为什么不再加更多目录？

v0.1 没有 deterministic script 的刚需，因此暂不创建 `scripts/`。

没有 MCP，因此不创建 `mcp.json`。

没有 hooks，因此不创建 `hooks/`。

没有 assets，因此不创建空 `assets/`。

不要创建空目录“占位”。

---

# 6. Manifest 基线

## 6.1 `plugins/dual-review-loop/plugin.json`

最小 portable manifest：

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "dual-review-loop",
  "version": "0.1.0",
  "description": "Run two independent code reviewers, fix actionable findings, validate, and repeat until the change converges or a bounded stop condition is reached.",
  "author": {
    "name": "zlin101"
  }
}
```

不要加入没有实际用途的 fields。

## 6.2 `.agents/plugins/marketplace.json`

基线：

```json
{
  "name": "zlin-agent-kit",
  "interface": {
    "displayName": "Zlin Agent Kit"
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

以最新官方 schema validator 为准。如果 schema 已变化，修正实现并在 README 记录，不要死守本文示例。

---

# 7. 核心角色模型

整个 loop 只有三类逻辑角色。

## 7.1 Orchestrator / Main Agent

职责：

- 读取目标 repo instructions；
- 冻结 review scope；
- 启动 reviewers；
- 收集结果；
- normalize / dedupe；
- 判断 finding 是否 actionable；
- 唯一拥有代码写权限；
- 应用修复；
- 运行验证；
- 管理轮次；
- 判断 PASS/STOP；
- 生成最终报告。

**Main Agent 是唯一 write owner。**

## 7.2 Correctness Reviewer

必须是 fresh subagent。

职责只包括：

- correctness；
- behavior regression；
- security；
- auth/authz；
- data integrity；
- race/atomicity；
- error handling；
- boundary cases；
- performance regression；
- relevant missing tests；
- 与 correctness 直接相关的 SOLID/architecture 问题。

禁止：
- 修改文件；
- stage；
- commit；
- push；
- 创建/更新 goal；
- 更新 review ledger；
- 执行主任务；
- 修复代码；
- spawn nested subagents。

## 7.3 Structural Reviewer

必须是另一个 fresh subagent，与 correctness reviewer 并行。

职责只包括：

- maintainability；
- abstraction quality；
- ownership/layer；
- code-judo simplification；
- spaghetti/branch growth；
- unnecessary modes/flags；
- thin wrappers；
- duplicated concepts；
- unclear type boundaries；
- file/component sprawl；
- non-atomic or needlessly sequential orchestration（当它也是结构问题时）；
- “能否删除复杂度，而非移动复杂度”。

同样严格只读。

---

# 8. Reviewer 隔离契约

每一次 spawn reviewer，都必须把以下含义明确写入 reviewer prompt。

建议统一模板：

```text
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
```

如果运行时支持 custom subagent `sandbox_mode = "read-only"`，可以使用它强化限制。

**但不要依赖 prompt 或 `agents/openai.yaml` 作为真正的 permission boundary。**

---

# 9. Fresh Context 原则

这是本项目的硬规则之一。

每轮 review：

```text
Round 1:
  Reviewer A1
  Reviewer B1

Round 2:
  Reviewer A2
  Reviewer B2

Round 3:
  Reviewer A3
  Reviewer B3
```

不要：

```text
Reviewer A1 -> resume -> review again
Reviewer B1 -> resume -> review again
```

原因：
- 避免 reviewer 为自己上一轮观点辩护；
- 避免“我建议的修复，所以我认为它已经好了”的确认偏差；
- 避免 context rot；
- 避免 reviewer 跟随主线程 goal 继续实现。

Reviewer 新一轮不应收到“上一轮你说了什么”的叙事。

它只需要：
- 当前完整 change scope；
- 当前项目规则；
- 当前相关代码；
- reviewer rubric。

历史 finding 的映射由主 Agent 完成。

---

# 10. Review Scope Contract

这是另一个硬规则。

## 10.1 Freeze baseline, not snapshot

在 loop 开始时确定：

```yaml
scope_type: branch | working-tree | commit-range | files
base_ref: optional
baseline_commit: optional
paths: optional
include_staged: bool
include_unstaged: bool
include_untracked: bool
```

不要求真的写 YAML 文件；这是主 Agent 内部必须掌握的 scope model。

### Branch / PR review

应以“真正会 merge 的 change”为准。

如果是 branch vs base，优先根据 merge-base 确定 baseline，而不是简单拿两个 branch tip 做可能误导的 direct diff。

### Working tree review

包括用户要求范围内：
- staged；
- unstaged；
- relevant untracked files。

## 10.2 Scope 必须跨轮次保持语义稳定

第一轮是：

```text
baseline → current target change
```

修复后第二轮仍然是：

```text
same baseline → current target change after fixes
```

**绝不能变成：**

```text
only diff produced by the previous fix round
```

否则会出现假收敛。

## 10.3 Changed scope vs context scope

区分：

- **Changed scope**：需要审查的目标 change。
- **Context scope**：为了理解 change 而读取的相关未修改文件、callers、contracts、tests。

Reviewer 可以扩大 context scope。

Reviewer 不得自行扩大产品目标或修改 changed scope。

## 10.4 Loop-generated files

如果 Main Agent 为修复目标 finding 新建/修改文件，这些变更自动属于下一轮完整 review scope。

---

# 11. 两个 Reviewer 的 Rubric

## 11.1 `dual-review-correctness`

应从 `code-review-expert` 的高价值部分重新编写，保留：

- P0/P1/P2/P3 severity 思维；
- SOLID/architecture smell；
- security；
- race/TOCTOU；
- secret leakage；
- error handling；
- performance；
- boundary conditions；
- removal candidates（仅当与当前 change 有直接价值）；
- tests/validation gap；
- clean review 时说明 residual risk。

必须删除/修改：

- “review 后必须询问用户是否修复”；
- “未经用户确认绝不实现”的 reviewer-to-user 交互；
- 与 loop 输出 contract 重复的长格式；
- 与当前 review 无关的泛化建议。

Reviewer 本身永远不会修，所以无需“询问是否修”。

## 11.2 `dual-review-structure`

应从 thermo-nuclear 的高价值部分重新编写，保留：

- ambitious structural simplification；
- delete complexity > rearrange complexity；
- code-judo；
- spaghetti/branch growth；
- canonical layer；
- thin abstraction；
- explicit type/boundary；
- large-file growth smell；
- duplicate/bespoke helper；
- atomicity / needless sequential orchestration；
- behavior-preserving restructuring。

必须修正：

- 删除 `disable-model-invocation` 等非 Codex portable frontmatter；
- 不把 1000 行阈值当作机械 blocker；
- 行数只是 smell/evidence，不是自动失败条件；
- reviewer 应说明“为什么当前 diff 的结构变差”，而不是仅报告文件长度；
- 不为了“更漂亮”提出与目标 change 无关的大重构。

---

# 12. Unified Finding Schema

两个 reviewer 输出同一 schema。

建议每个 finding：

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

### Reviewer verdict

```yaml
verdict: PASS | FINDINGS
```

并附：

```yaml
coverage:
residual_risks:
```

## 12.1 不需要 reviewer 生成全局 stable finding ID

Reviewer 只生成 local ID。

主 Agent dedupe 后生成：

```text
F001
F002
F003
```

原因：
- line number 会随着 fix 变化；
- 两个 reviewer 可能发现同一 root cause；
- global identity 应由 orchestrator 统一掌握。

---

# 13. Dedupe 与 Finding Identity

主 Agent 收到两个结果后：

## 13.1 Duplicate 判定

两个 finding 在以下语义上相同，应合并：

- 同一个 root cause；
- 相同/相邻 symbol 或 ownership boundary；
- 同一个行为风险；
- 修复其中一个会自然消除另一个。

不要只按：
- 标题文字；
- exact line；
- category 字符串
去重。

## 13.2 合并后 finding

示例：

```yaml
id: F002
severity: P1
blocking: true
sources:
  - correctness
  - structure
location:
  file: internal/state.go
  symbol: Apply
problem: related state updates can partially apply because ownership and transaction boundary are split
evidence:
  - correctness reviewer observed partial state on second-write failure
  - structural reviewer observed transaction ownership in the wrong layer
```

如果两个 reviewer 都独立命中同一 root cause，应提高主 Agent 对该 finding 的重视程度，但不要机械提高 severity。

---

# 14. Finding Lifecycle — v0.1 消融版

不要实现复杂状态机。

一次 loop session 内只需要：

```text
OPEN
RESOLVED
BLOCKED
WAIVED
```

其中：

- `OPEN`：当前仍可复现/仍存在。
- `RESOLVED`：新一轮 fresh review 已不再确认，且相关验证通过。
- `BLOCKED`：当前 Agent 无权限、证据不足、外部依赖或需要人类决策。
- `WAIVED`：只有用户或目标项目明确规则允许时才能标记；Agent 不得自行 waive blocker。

`DUPLICATE`、`INVALID` 是 normalization 结果，不需要作为生命周期状态长期保存。

`FIXED_PENDING_VERIFY` 是执行过程瞬态，也不需要状态化。

---

# 15. Fix Policy

## 15.1 Single writer

两个 reviewers 永远不写。

只有主 Agent/Fixer 写。

## 15.2 Fix order

默认优先级：

1. P0 correctness/security/data loss；
2. P1；
3. structural blocker；
4. 明确、低风险、scope 内的 P2；
5. P3 默认不自动修。

## 15.3 Root-cause batch

一轮不要：

```text
find F001
fix F001
spawn reviewers
find F002
fix F002
spawn reviewers
```

应：

```text
review whole scope
dedupe actionable blockers
fix one coherent root-cause batch
validate
review whole scope again
```

减少 review 次数与局部优化造成的 oscillation。

## 15.4 Minimal but not artificially tiny

正确性问题：
- 优先最小、安全、可验证的 root-cause fix。

结构问题：
- 允许超出单行/单函数修改；
- 但必须直接服务当前 change 的可维护性；
- 不把 loop 变成全仓库 refactor。

## 15.5 不允许的自动动作

除非用户明确要求：

- commit；
- amend；
- push；
- merge；
- create PR；
- delete branch；
- destructive git reset/revert；
- 修改与当前 change 无关的 user work。

---

# 16. Validation Contract

每个 fix round 后验证。

## 16.1 优先级

1. 目标 repo `AGENTS.md` / project instructions 明确规定的验证；
2. 目标项目已有 scripts/Makefile/package config 中明显对应的验证；
3. 与 touched scope 直接相关的 targeted tests；
4. 必要时 final full validation。

## 16.2 不硬编码语言

Plugin 不知道：

```text
go test ./...
pytest
npm test
cargo test
```

由目标 repo 决定。

## 16.3 验证失败

如果失败与本轮修复直接相关：
- 修复；
- 仍属于本轮 convergence。

如果失败明显是 pre-existing / unrelated：
- 不擅自扩大 scope；
- 记录 evidence；
- 若它阻止确认正确性，则 STOP/BLOCKED；
- 否则作为 residual validation risk 报告。

---

# 17. Convergence Contract

默认成功条件：

```text
1. P0 open findings == 0
2. P1 open findings == 0
3. structural blocking findings == 0
4. required project validation passes
5. no unresolved material reviewer conflict
```

P2：
- 如果是直接、低风险、明确属于当前 change，优先修；
- 否则允许作为 residual finding；
- 不默认阻止 PASS。

P3：
- 默认不阻止 PASS。

如果用户明确要求：

```text
strict / zero findings / fix everything reasonable
```

则可提升 P2 为 convergence gate。

**结构 reviewer 不能靠无限提出“还可以更优雅”阻止收敛。**
必须区分：
- blocking regression；
- material actionable improvement；
- optional taste/suggestion。

---

# 18. Loop Guards / Stop Conditions

默认：

```yaml
max_rounds: 3
no_progress_rounds: 2
```

这些是 skill contract 默认值，不需要 v0.1 配置文件。

用户明确指定时可覆盖。

## 18.1 PASS

满足 Convergence Contract。

## 18.2 STOP — max rounds

达到 `max_rounds` 仍有 blocker。

## 18.3 STOP — no progress

连续两轮：
- blocker set 没有减少；
- 同一 root cause 在等价形式重复；
- validation 没有改善。

## 18.4 STOP — oscillation

例如：

```text
Round N reviewer demands abstraction
→ fix
Round N+1 reviewer demands removal of that abstraction
→ fix
Round N+2 returns to original structure
```

检测到设计来回摆动时，不继续机械修。

输出冲突和两个方向的 trade-off，交还用户。

## 18.5 STOP — permission boundary

需要：
- destructive action；
- external write；
- API/security/deployment authorization；
- 项目规则要求明确批准
时停止。

## 18.6 STOP — reviewer conflict

如果两个 reviewer 对 material behavior/architecture 得出相反结论：

主 Agent先通过代码、测试、contract 做一次 evidence resolution。

如果仍无法可靠判断：
- 标记 BLOCKED；
- 不靠“多数票”决定；
- STOP 并报告。

---

# 19. 每轮算法

伪代码：

```text
read_project_instructions()
scope = freeze_review_scope()

previous_open = ∅
no_progress = 0

for round in 1..max_rounds:
    current_change = materialize_full_change(scope)

    reviewer_a = spawn_fresh_readonly(
        skill = dual-review-correctness,
        scope = current_change
    )

    reviewer_b = spawn_fresh_readonly(
        skill = dual-review-structure,
        scope = current_change
    )

    wait_for_both()

    raw_findings = reviewer_a + reviewer_b
    findings = normalize_and_dedupe(raw_findings)
    map_to_previous_ids(findings)

    if convergence_gate(findings) and required_validation_is_green:
        return PASS

    actionable = select_actionable(findings)

    if actionable is empty:
        return STOP(reason = blocked_or_unresolved)

    if detects_oscillation(findings):
        return STOP(reason = oscillation)

    main_agent_apply_root_cause_fix_batch(actionable)

    validation = run_project_validation()

    if validation reveals fix regression:
        repair_or_revert_own_fix_safely()

    progress = compare_blocking_set(previous_open, findings, validation)

    if not progress:
        no_progress += 1
    else:
        no_progress = 0

    if no_progress >= 2:
        return STOP(reason = no_progress)

    previous_open = current_blocking_set(findings)

return STOP(reason = max_rounds)
```

注意：

`required_validation_is_green` 在第一轮纯 review 时可能尚未运行。

推荐：
- 如果第一轮 reviewers 完全 PASS，再运行最终 required validation，随后 PASS；
- 有 findings 时，修复后运行 validation，再进入 fresh re-review。

---

# 20. Reviewer Output Contract 示例

## 20.1 Correctness reviewer

```yaml
reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P1
    blocking: true
    category: reliability
    location:
      file: internal/store/update.go
      symbol: ApplyUpdate
    title: partial update can escape on second write failure
    problem: the first mutation is committed before the second can fail
    evidence: ...
    impact: callers can observe internally inconsistent state
    recommended_direction: make the related writes share one atomic ownership/transaction boundary
coverage: reviewed full change plus direct callers and related tests
residual_risks: []
```

## 20.2 Structural reviewer

```yaml
reviewer: structure
verdict: FINDINGS
findings:
  - local_id: S1
    severity: P1
    blocking: true
    category: architecture
    location:
      file: internal/store/update.go
      symbol: ApplyUpdate
    title: transaction ownership sits in the wrong layer
    problem: ...
    evidence: ...
    impact: ...
    recommended_direction: move ownership to the layer that already owns both state transitions
coverage: reviewed changed modules and canonical state ownership layer
residual_risks: []
```

主 Agent应将二者合并为同一个 `F001`，而不是修两次。

---

# 21. 最终用户输出

PASS 示例：

```text
Dual Review Loop: PASS

Rounds: 2/3

Resolved
- F001 [P1] atomic state ownership
- F002 [P2] duplicated branch logic

Residual non-blocking
- F003 [P3] naming cleanup

Validation
- <command>: PASS
- <command>: PASS

Review coverage
- correctness reviewer: PASS
- structural reviewer: PASS

No commit or push was performed.
```

STOP 示例：

```text
Dual Review Loop: STOPPED

Reason: oscillation / max rounds / permission boundary / unresolved conflict

Rounds: 3/3

Open blockers
- F002 ...

What was tried
- Round 1 ...
- Round 2 ...

Validation
- ...

Decision required
- concise concrete question/trade-off
```

不要输出十页过程日志。

用户需要的是：
- 最终状态；
- 高价值 finding；
- 变更；
- 验证；
- 剩余风险；
- 为什么停止。

---

# 22. 与目标项目 `AGENTS.md` 的边界

Plugin 负责 **HOW**：

- 怎么双审；
- 怎么隔离 reviewer；
- 怎么 dedupe；
- 怎么 fix/review；
- 怎么收敛；
- 怎么停。

目标项目负责 **WHAT IS ALLOWED / WHAT IS DONE**：

- repo 特定约束；
- test commands；
- branch policy；
- API contract；
- security gate；
- deployment authorization；
- review ledger 位置；
- commit/push policy；
- 目录 ownership。

优先级：

```text
User explicit instruction
    ↓
Applicable project instructions / AGENTS.md
    ↓
dual-review-loop generic defaults
```

Plugin 不得绕过项目规则。

---

# 23. Review Ledger 策略

v0.1 默认：

```text
NO persistent ledger
```

主 Agent 在当前 session 内维护 finding mapping。

只有目标项目明确规定：

```text
review results must be written to X
```

时才写。

而且：
- Reviewer 不写 ledger；
- Main Agent 写；
- 路径由项目规则提供；
- Plugin 不发明默认 `vault/tasks/...`。

---

# 24. 第三方来源与许可证

实现前再次打开原始 LICENSE，保留准确版权信息。

当前来源审计表明两个上游 repository 均采用 MIT license：

1. `sanyuan0704/sanyuan-skills`
   - component: `skills/code-review-expert`

2. `cursor/plugins`
   - component: `cursor-team-kit/skills/thermo-nuclear-code-quality-review`
   - 还可参考后续独立 `thermos` plugin 的双 reviewer orchestration 设计。

## 24.1 不要“洗掉来源”

插件目录必须有：

```text
LICENSE
THIRD_PARTY_NOTICES.md
```

`THIRD_PARTY_NOTICES.md` 至少记录：

- upstream repository；
- component/path；
- license；
- 原始 copyright notice（从上游 LICENSE 准确复制）；
- 本项目是 derived/adapted implementation；
- 哪些部分经过重写。

## 24.2 为什么选择重写而不是原样复制

不是因为 MIT 不允许。

而是因为原 skill 有 runtime-specific 语义：

- `code-review-expert` 有“review 后询问用户是否修”的 standalone workflow；
- thermo skill 有非 Codex portable metadata；
- 本项目需要统一 finding schema；
- 本项目 reviewer 必须是纯 read-only worker。

因此应做**attributed adaptation**。

---

# 25. 与 Cursor Thermos 的关系

实现时应把 `cursor/plugins/thermos` 当作重要先例，而不是盲区。

Thermos 已经验证了：

```text
two independent reviewers
    ↓
parallel
    ↓
same scoped context
    ↓
dedupe + synthesize
```

这是合理模式。

本项目的差异化不应声称“发明双 reviewer”。

本项目真正增加的是：

```text
scope freeze
+ single-writer fix ownership
+ finding reconciliation across rounds
+ project validation
+ fresh re-review
+ explicit convergence predicate
+ bounded stop guards
```

也就是：

```text
Thermos-like dual review
        +
Fix / Validate / Re-review convergence loop
```

---

# 26. v0.1 实现步骤

按顺序完成，不要提前做后面版本。

## Phase 1 — Scaffold

创建：

```text
zlin-agent-kit/
.agents/plugins/marketplace.json
plugins/dual-review-loop/plugin.json
```

加入 root/plugin README、LICENSE、CHANGELOG、THIRD_PARTY_NOTICES。

## Phase 2 — Reviewer skills

先完成：

```text
dual-review-correctness
dual-review-structure
```

要求：
- 两者可被独立调用；
- 输出统一 schema；
- 只 review；
- 不问“是否帮你修”；
- 不修改目标 repo。

## Phase 3 — Orchestrator skill

实现：

```text
dual-review-loop
```

只在 `SKILL.md` 保留核心流程。

细节放 references，遵循 progressive disclosure。

## Phase 4 — Scope + convergence

实现并文档化：
- baseline freeze；
- stable full-scope re-review；
- dedupe；
- stable finding mapping；
- max rounds；
- no-progress；
- oscillation；
- PASS/STOP。

## Phase 5 — Validation

实现 generic project validation discovery。

严禁在 skill 中出现某个项目固定测试命令。

## Phase 6 — Local plugin validation

检查：
- JSON parse；
- plugin schema；
- marketplace schema；
- SKILL frontmatter；
- `agents/openai.yaml`；
- 所有相对路径；
- 无 TODO placeholder；
- 无 unsupported copied frontmatter。

如官方 `@plugin-creator` / validator 可用，优先用官方 validator。

## Phase 7 — Local marketplace smoke test

添加本地 marketplace / GitHub source（视开发位置而定）。

确认：
- plugin 可发现；
- 三个 skills 可发现；
- orchestrator 会请求/触发 subagents；
- 两 reviewers 真正并行；
- reviewer threads fresh；
- 主 Agent唯一写。

## Phase 8 — Behavior acceptance

至少用以下场景验证。

### Scenario A — Clean change

预期：
- 两 reviewers PASS；
- required validation PASS；
- Round 1 收敛；
- 无代码修改。

### Scenario B — Correctness bug

预期：
- correctness reviewer 给 blocker；
- structural reviewer 可有或无 finding；
- 主 Agent修；
- validation；
- 新 reviewers 重新看完整 scope；
- PASS。

### Scenario C — Structural regression

预期：
- structure reviewer 给 blocker；
- 主 Agent执行 behavior-preserving restructure；
- validation；
- 新 reviewers；
- PASS。

### Scenario D — Duplicate root cause

两个 reviewers 用不同语言指出同一个问题。

预期：
- 合成一个 global finding；
- 只修一次。

### Scenario E — Oscillation

构造/选择一个容易在 abstraction 与 direct code 间摆动的 case。

预期：
- 不无限循环；
- 达到 guard 后 STOP；
- 输出 trade-off。

### Scenario F — Project-specific gate

目标 repo `AGENTS.md` 指定验证。

预期：
- plugin 使用项目命令；
- 没有回退到硬编码语言命令。

### Scenario G — Reviewer isolation

预期：
- reviewers 不 edit；
- 不 stage；
- 不 commit；
- 不 update goal；
- 不 spawn nested agents。

---

# 27. Acceptance Criteria

只有全部满足，v0.1 才算完成。

## Packaging

- [ ] root `plugin.json` 符合当前 portable Agent Plugins schema
- [ ] marketplace 可解析
- [ ] plugin 可安装/发现
- [ ] 三个 skills 可发现
- [ ] `agents/openai.yaml` 与 skill 内容一致
- [ ] 无不支持的上游 metadata

## Architecture

- [ ] 两 reviewers 是独立 fresh subagents
- [ ] 两 reviewers 同轮并行
- [ ] 两 reviewers read-only
- [ ] reviewers 不追随主 goal 执行实现
- [ ] reviewers 不 spawn nested subagents
- [ ] main Agent 是唯一 writer

## Scope

- [ ] baseline 在 loop 起始时冻结
- [ ] 每轮重新审完整目标 change
- [ ] fix 新增的目标相关文件进入下一轮 scope
- [ ] 不把“上一轮新增 diff”误当成完整 scope

## Findings

- [ ] reviewer 输出统一 schema
- [ ] orchestrator dedupe
- [ ] 同 root cause 不重复修
- [ ] finding 跨轮次可语义匹配
- [ ] 不依赖 exact line number 做 identity

## Convergence

- [ ] P0/P1 blocker 为 0
- [ ] structural blocker 为 0
- [ ] required validation green
- [ ] fresh reviewers 确认
- [ ] max rounds 生效
- [ ] no-progress guard 生效
- [ ] oscillation guard 生效

## Portability

- [ ] 无 Iris 特定路径
- [ ] 无固定 branch 名
- [ ] 无固定语言/test command
- [ ] 遵循目标 repo `AGENTS.md`
- [ ] 默认不创建 ledger
- [ ] 默认不 commit/push

## Legal

- [ ] 上游 license 重新核对
- [ ] plugin 内含第三方 notices
- [ ] attribution 准确
- [ ] 不错误声称 reviewer rubric 完全原创

---

# 28. Failure Modes 必须主动防御

## F1. Reviewer 偷偷修代码

处理：
- reviewer prompt 明确只读；
- 可用时使用 read-only sandbox；
- 主 Agent检测异常改动；
- reviewer 产生写操作则该轮结果不可信，重新 spawn。

## F2. Reviewer 追随主线程 Goal

处理：
- prompt 明确“ignore active goal except background context”；
- 禁止 goal/task/ledger 写入；
- fresh thread；
- 不 resume reviewer。

## F3. 假收敛

症状：
第二轮只审修复 diff。

处理：
每轮都重建：

```text
frozen baseline → current full target change
```

## F4. 两个 reviewer 输出十几个重复 finding

处理：
root-cause dedupe 后再 fix。

## F5. Thermo reviewer 永远能找到“更优雅”

处理：
必须区分 blocking structural regression 与 optional suggestion。

没有 material regression/clear actionable blocker，就不能无限阻止 PASS。

## F6. Fix 引入新 bug

处理：
- 每轮 fix 后 validation；
- 下一轮是 fresh correctness reviewer；
- 新问题成为 OPEN finding。

## F7. 修复在两个结构之间来回摆动

处理：
oscillation guard → STOP。

## F8. 项目验证很贵

处理：
- 遵循项目规则；
- round 内优先 targeted；
- final 做 required full gate；
- 不私自跳过项目 hard gate。

## F9. 用户同时修改工作区

处理：
- 不覆盖；
- 不 revert unrelated changes；
- 如果无法安全区分 ownership，STOP 并报告。

---

# 29. v0.2 之后再考虑

只有 v0.1 在真实 repo 中稳定后：

### v0.2
- optional strict mode；
- user-configurable `max_rounds`；
- richer finding fingerprints；
- optional session report artifact。

### v0.3
- reviewer set 可配置；
- security-only reviewer；
- test-quality reviewer；
- API compatibility reviewer。

### v0.4
把 convergence kernel 抽象给：

```text
test-convergence-loop
doc-review-loop
task-acceptance-loop
```

**不要在 v0.1 预先实现这个 abstraction。**

先让 `dual-review-loop` 自己工作可靠，再观察真正重复的部分。

---

# 30. 设计 Review / 反思 / 消融结果

本文已经按“能不能删除复杂度而不损失核心价值”的标准做过收敛。

## 30.1 保留

这些是产品本质，不能删：

- 两个不同 rubric；
- parallel fresh reviewers；
- reviewer read-only；
- single writer；
- scope freeze；
- full-scope re-review；
- dedupe；
- project validation；
- convergence predicate；
- max-round/no-progress/oscillation guards；
- project instruction boundary；
- third-party attribution。

## 30.2 删除

以下设计最初看起来“完整”，但 v0.1 不值得：

### 删除：持久化 finding 状态机

原因：
一次运行内的状态用主 Agent context 足够。
引入文件/DB 只会带来同步、恢复、schema 和项目污染。

### 删除：默认 review ledger

原因：
这是目标项目 policy，不是通用 plugin 的职责。

### 删除：第三常驻 verifier

原因：
两个 reviewer + 主 Agent evidence resolution 已足够。
第三 reviewer 只增加 token/latency，暂未证明价值。

### 删除：逐 finding 修完立刻 review

原因：
review 成本高、容易局部优化。
改为每轮统一 dedupe → coherent batch fix → validation → full re-review。

### 删除：原样 vendor 两个 skill

原因：
上游交互语义/runtime metadata 与 Codex loop 不完全兼容。
做 attributed adaptation 更稳。

### 删除：复杂配置文件

原因：
`max_rounds=3` 等少量默认值可以直接写 contract。
有真实配置需求再抽象。

### 删除：兼容 manifest 默认双写

原因：
当前官方推荐 root portable `plugin.json`。
兼容 `.codex-plugin` 仅在 smoke test 证明必要时增加。

### 删除：多平台同时支持

原因：
当前目标是让 Codex loop 先跑稳。
不要同时调试 Cursor/Claude packaging 差异。

## 30.3 收敛结论

v0.1 的最小完整产品是：

```text
3 skills
+ 1 portable plugin manifest
+ 1 repo marketplace
+ 5 contract/reference docs
+ attribution
+ local smoke/e2e scenarios
```

无需服务端、数据库、脚本框架或 workflow runtime。

这是当前最小、可维护、能真正验证用户目标的方案。

---

# 31. Agent 开工总提示词

下面内容可直接作为执行本项目的总指令。

---

## GOAL

实现一个个人 Agent Plugin Marketplace 仓库，工作名 `zlin-agent-kit`，首个插件为 `dual-review-loop`。

它必须把两个互补代码审查思想编排成一个**有界自动收敛 loop**：

```text
freeze scope
→ two fresh read-only reviewers in parallel
→ normalize/dedupe
→ main agent fixes
→ project validation
→ two new fresh reviewers on the same full scope
→ repeat until PASS or bounded STOP
```

### Reviewer A — correctness

基于并改写：

```text
sanyuan0704/sanyuan-skills
skills/code-review-expert
```

关注：
correctness、security、reliability、SOLID、error handling、performance、boundary cases、race、missing tests。

### Reviewer B — structure

基于并改写：

```text
cursor/plugins
cursor-team-kit/skills/thermo-nuclear-code-quality-review
```

同时参考：

```text
cursor/plugins/thermos
```

关注：
maintainability、structural simplification、code-judo、spaghetti growth、abstraction quality、canonical layer、type boundaries、unnecessary branches/wrappers、atomicity。

### Hard architecture rules

1. Reviewers 必须是 fresh subagents。
2. 同一轮两个 reviewers 并行。
3. Reviewers 永远 read-only。
4. Reviewers 不修改代码、不 stage、不 commit、不 push。
5. Reviewers 不创建/更新 goal、task、ledger。
6. Reviewers 不继续主线程 implementation goal。
7. Reviewers 不 spawn nested subagents。
8. Main Agent 是唯一 writer。
9. Loop 开始时 freeze review baseline/scope。
10. 每轮 review 的都是相同 baseline 到当前完整 target change，而不是上一轮新增 diff。
11. Main Agent负责 normalize、root-cause dedupe 和 stable finding mapping。
12. Fix 以 coherent root-cause batch 进行。
13. 每个 fix round 后运行目标 repo 规定的 validation。
14. 每轮 re-review 必须创建两个新的 reviewer threads。
15. 默认 convergence：
    - open P0 = 0
    - open P1 = 0
    - structural blocker = 0
    - required validation PASS
    - 无 unresolved material reviewer conflict
16. 默认 `max_rounds = 3`。
17. 连续 2 轮 no progress 时 STOP。
18. 检测 oscillation 时 STOP。
19. 权限不足、需要人类授权、reviewer material conflict 无法用 evidence 解决时 STOP。
20. P3 默认不自动修、不阻止 PASS。
21. P2 仅在直接相关、低风险、scope 内时自动修；否则作为 residual。
22. Plugin 不硬编码任何 Iris、branch、语言或 test command。
23. 优先读取目标仓库 `AGENTS.md` 和 project instructions。
24. 默认不创建持久化 review ledger。
25. 默认不 commit/push/merge。

### Packaging rules

优先使用当前 OpenAI portable plugin 结构：

```text
plugins/dual-review-loop/plugin.json
```

Repo marketplace：

```text
.agents/plugins/marketplace.json
```

创建三个 skills：

```text
dual-review-loop
dual-review-correctness
dual-review-structure
```

每个 skill 使用 Codex-compatible `SKILL.md`，frontmatter 只保留 `name`、`description`；生成/维护 `agents/openai.yaml`。

不要原样复制 Cursor/Claude-specific frontmatter。

### License

两个上游当前均为 MIT，但你必须在实现时重新核对最新 LICENSE。

在 plugin 自身目录保留：

```text
LICENSE
THIRD_PARTY_NOTICES.md
```

准确 attribution 上游 repo/component/copyright/license。

### Scope

不要做：
- DB
- MCP
- hooks
- Web UI
- persistent state engine
- default ledger
- third permanent verifier
- general workflow framework
- automatic PR/merge
- multi-platform packaging
- complex config system

### Required validation

完成后至少证明：

1. clean change 可 Round 1 PASS；
2. correctness bug 能 review → fix → validate → fresh re-review → PASS；
3. structural regression 能收敛；
4. duplicate root cause 会合并；
5. reviewers 没有写目标代码；
6. 第二轮仍审 full original scope；
7. no-progress / max-round / oscillation 至少有可验证行为；
8. project `AGENTS.md` 中的验证规则优先；
9. plugin 不含 Iris 特定假设；
10. marketplace/plugin/skills 能被当前 Codex 正确发现。

### Implementation discipline

- 先核对最新官方 OpenAI plugin/skills/subagent 文档。
- 以当前官方 schema/CLI 为准，本文示例与官方冲突时采用官方，并记录差异。
- 不因小的不确定性停下来询问；选择最小安全实现并继续。
- 不执行 GitHub repo 创建、push、发布等外部写操作，除非 Owner 已明确授权。
- 在本地实现、验证到可发布状态。
- 最终给出：
  - file tree
  - design summary
  - validation evidence
  - remaining risks
  - release/publish commands（只展示，不擅自执行）
  - v0.1 readiness verdict

---

# 32. 参考来源

实现 Agent 应在开工时重新核对以下一手来源：

- OpenAI Developers — Package your plugin
- OpenAI Codex — Subagents
- OpenAI Skills — skill-creator / skill structure
- OpenAI Codex — review-agent sample
- `sanyuan0704/sanyuan-skills` — `skills/code-review-expert`
- `cursor/plugins` — `cursor-team-kit/skills/thermo-nuclear-code-quality-review`
- `cursor/plugins` — `thermos`

当前审查得到的关键事实：

- OpenAI 当前支持 root `plugin.json` portable package；`.codex-plugin/plugin.json` 是兼容 fallback。
- Repo marketplace 位于 `.agents/plugins/marketplace.json`。
- Marketplace CLI 支持 GitHub shorthand / Git URL / SSH URL / local root。
- 一个 marketplace 可以承载多个 plugins。
- Codex 当前支持由 project/skill instructions 触发 subagents。
- 官方建议 subagents 优先用于 read-heavy 并行工作，并对并行 write-heavy workflows 更谨慎。
- OpenAI 自带 review-agent sample 明确采用 read-only reviewer 思路。
- Skill 的 `agents/openai.yaml` 是产品/UI metadata，不应被当成 permission boundary。
- 两个目标上游 repo 当前均声明 MIT；发布前仍需重新核对实际 LICENSE 和 copyright notice。

---

**End of implementation specification.**
