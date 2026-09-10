# dual-review-loop v0.2.0

有界、可验证、自动收敛的双审代码质量循环。

```text
freeze scope
    ↓
spawn 2 fresh read-only reviewers (correctness + structure) in parallel
    ↓
normalize + dedupe + classify findings
    ↓
main agent fixes actionable findings
    ↓
run project-defined validation
    ↓
spawn 2 NEW reviewers on the SAME full scope
    ↓
compare finding set
    ↓
PASS / continue / STOP
```

## Skills

| Skill | 角色 |
|---|---|
| `dual-review-loop` | 编排器：冻结 scope、并行派发 reviewer、归并 dedupe、修复、验证、收敛判定 |
| `dual-review-correctness` | 只读 reviewer：correctness / security / reliability / 性能回归 / 边界 / 缺失测试，P0–P3 |
| `dual-review-structure` | 只读 reviewer：结构简化 / 抽象质量 / spaghetti 增长 / 层与类型边界，regression-vs-improvement 分类 |

## 用法

对当前工作区、branch、commit range 或显式文件列表运行循环；用户可显式指定
`strict`（P2 和 structural improvement 也作为收敛门）、`max_rounds`、
`no_progress_rounds` 覆盖。其余全部走默认合同
（`max_rounds: 3`，`no_progress_rounds: 2`）。

- Claude Code：安装后 `/dual-review-loop`，或直接描述"用双审循环收敛这个改动"
- Codex：安装后直接请求运行 dual review loop

## 永远不会做的事

- reviewer 永远只读；只有主 Agent 写代码
- 不自动 commit / push / merge / 建 PR
- 默认不创建 review ledger 文件
- 不硬编码任何语言、分支名或测试命令 — 验证以目标仓库自己的
  `AGENTS.md` / project instructions 为准

## 平台说明

- **Codex**：reviewer 为 prompt 合同隔离的 subagent（可在用户侧用
  `.codex/agents/*.toml` 的 `sandbox_mode = "read-only"` 进一步硬化）
- **Claude Code**：reviewer 运行在插件自带的只读工具白名单 agent 上
  （`Read, Grep, Glob`），隔离由运行时强制

## Attribution

Reviewer rubrics 为 MIT 上游 skill 的 attributed adaptation（改写而非复制）—
见 `THIRD_PARTY_NOTICES.md`。
