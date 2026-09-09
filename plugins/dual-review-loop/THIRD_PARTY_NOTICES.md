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
