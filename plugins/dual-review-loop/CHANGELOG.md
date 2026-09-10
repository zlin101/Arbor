# Changelog

## 0.2.0 — 2026-09-10

### Protocol fixes

- **Residual-only validation**: validation now runs before PASS even when gate blockers == 0; residual-only rounds never STOP for lack of a fix.
- **Causality-based scope**: findings in scope iff causally attributable to the target change; untouched code admissible as manifestation with causal_link.
- **Reviewer schema cleanup**: removed `blocking` field from reviewer output; `taste` no longer a finding class; orchestrator derives gate policy from fixed table.
- **Progress semantics**: persistent/resolved/new separation; churn (resolved-old + new-same-count) no longer triggers stagnation.

### Improvements

- Validation freshness: no write since completion; gate-time check at priority 4.
- Oscillation guard: main agent's own fix directions flip-flop across 3 comparable rounds.
- Conflict resolution: one evidence-resolution pass per finding; unresolved → STOP.
- Max rounds: lists fixed-but-pending-review findings in STOPPED report.

### QA

- Added `scripts/check_repo.py`: deterministic consistency checker (packaging, protocol files, boundary projections, forbidden fields).
- Added `tests/test_check_repo.py`: pass/fail coverage for key checker rules.
- Added `evals/dual-review-loop/README.md`: central regression eval runbook E01–E10.
- Added `.github/workflows/validate.yml`: CI runs deterministic checks on PR.

## 0.1.0 — 2026-09-09

- Initial release: `dual-review-loop` orchestrator skill plus `dual-review-correctness` and `dual-review-structure` reviewer skills.
- Frozen-scope full re-review each round; root-cause dedupe; single-writer fixes; project-defined validation.
- Guards: max_rounds=3, no-progress=2, oscillation, permission boundary, reviewer conflict.
- Works on Codex (portable root plugin.json + repo marketplace) and Claude Code (.claude-plugin manifests + read-only reviewer agents).
