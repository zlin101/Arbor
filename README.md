# Arbor

个人 Agent Plugin Marketplace — 一个仓库，同时发布到 OpenAI Codex、Claude Code 与 Pi。

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

## Install (Pi)

```bash
pi install git:github.com/zlin101/Arbor
```

Pi 按根目录 `package.json` 的 `pi.skills` 声明加载 `plugins/dual-review-loop/skills/` 下的三个 skill（`dual-review-loop` / `dual-review-correctness` / `dual-review-structure`），个人级安装、任意项目可用。

- 验证：`pi list` 应出现 `git:github.com/zlin101/Arbor`；会话内 `/skill:dual-review-loop` 可显式触发
- reviewer 子代理并行审查依赖 pi-subagents，建议一并安装：`pi install npm:pi-subagents`
- 更新：`pi update --extensions`（如需钉住版本，先打 git tag 再 `pi install git:github.com/zlin101/Arbor@<tag>`）
- 移除：`pi remove git:github.com/zlin101/Arbor`
- 仅当前项目生效：`pi install -l git:github.com/zlin101/Arbor`（写入项目 `.pi/settings.json`，授予项目信任后加载）

## Layout

- `.agents/plugins/marketplace.json` — Codex repo marketplace
- `.claude-plugin/marketplace.json` — Claude Code repo marketplace
- `package.json` — Pi package manifest（`pi.skills` 指向 `plugins/dual-review-loop/skills/`）
- `plugins/dual-review-loop/` — plugin（skills 三平台共享，manifests 各平台一份）

## Attribution

Reviewer rubrics are attributed adaptations of MIT-licensed upstream skills —
see `plugins/dual-review-loop/THIRD_PARTY_NOTICES.md`.
