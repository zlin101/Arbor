# Changelog

## 0.1.0 — 2026-09-09

- Initial release: `dual-review-loop` orchestrator skill plus `dual-review-correctness` and `dual-review-structure` reviewer skills.
- Frozen-scope full re-review each round; root-cause dedupe; single-writer fixes; project-defined validation.
- Guards: max_rounds=3, no-progress=2, oscillation, permission boundary, reviewer conflict.
- Works on Codex (portable root plugin.json + repo marketplace) and Claude Code (.claude-plugin manifests + read-only reviewer agents).
