# Arbor · 信息gap

个人 Agent Plugin Marketplace — 一个仓库，同时发布到 OpenAI Codex 与 Claude Code。

## Plugins

- **dual-review-loop** — 双审收敛循环：两个独立、fresh-context、只读 reviewer（correctness / structure）并行审查同一冻结 scope；主 Agent 归并 findings、做根因修复、跑项目验证，再让两个全新 reviewer 重审完整 scope，直到满足收敛条件或有界停止。

## Install (Codex)

```bash
codex plugin marketplace add zlin101/Arbor          # HTTPS 凭据可用的机器
codex plugin marketplace add git@github.com:zlin101/Arbor.git  # SSH-only 机器
codex plugin add dual-review-loop@arbor
```

## Install (Claude Code)

```bash
claude plugin marketplace add zlin101/Arbor
claude plugin install dual-review-loop@arbor
```

## Layout

- `.agents/plugins/marketplace.json` — Codex repo marketplace
- `.claude-plugin/marketplace.json` — Claude Code repo marketplace
- `plugins/dual-review-loop/` — plugin（skills 双平台共享，manifests 各平台一份）

## Attribution

Reviewer rubrics are attributed adaptations of MIT-licensed upstream skills —
see `plugins/dual-review-loop/THIRD_PARTY_NOTICES.md`.

## Publishing（Owner 操作，未自动执行）

```bash
# 首次发布：推送到 GitHub（需要 Owner 权限）
git remote add origin git@github.com:zlin101/Arbor.git
git push -u origin main

# 之后任意机器安装（Codex）
codex plugin marketplace add zlin101/Arbor
codex plugin add dual-review-loop@arbor

# 之后任意机器安装（Claude Code）
claude plugin marketplace add zlin101/Arbor
claude plugin install dual-review-loop@arbor
```
