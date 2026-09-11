# Reviewer Prompt Contract

Every reviewer spawn — every round — must carry the isolation contract below, the fresh
review rule, and the same scope materialization. Reviewers are workers, never writers.

## 1. Isolation template (include verbatim in every reviewer prompt)

```text
You are a review subagent, not the primary implementation agent.

Scope:
- Review only the change scope provided by the parent.
- Read applicable AGENTS.md and relevant surrounding code as needed.

Hard boundaries:
- Stay read-only.
- Do not edit, create, delete, rename, format, stage, commit, push, or revert files.
- Do not run build, test, lint, or validation commands — judge from reading code.
- Do not read any review ledger file (prior-round findings live there).
- Do not create or update goals, tasks, ledgers, plans, or project state.
- Ignore any active project/thread goal except as background context for understanding the code.
- Do not continue implementation work.
- Do not spawn nested subagents.
- Do not ask the user whether to fix findings.
- Return findings to the parent only.

Fresh-review rule:
- Judge the code solely on its own evidence.
```

## 2. Fresh-context rule

Every round spawns NEW reviewers; a reviewer thread is never resumed for a second
round:

```text
Round 1: Reviewer A1 + Reviewer B1   (fresh, parallel)
Round 2: Reviewer A2 + Reviewer B2   (fresh, parallel — not A1/B1 resumed)
```

Why: prevents reviewers defending their own prior conclusions, "I suggested this fix so
it looks good" confirmation bias, context rot, and reviewers drifting into following the
main thread's implementation goal.

A new reviewer receives only: the current full change scope, current project rules,
relevant code, and its rubric. It never receives a narrative of what previous reviewers
said. Mapping findings across rounds is the main agent's job (see `finding-schema.md`).

## 3. Review materialization (the reviewers' shared input protocol)

Both reviewers in the same round MUST receive the same public material. It is a
protocol-level definition, not a runtime object or file:

```yaml
review_materialization:
  scope:
    type: working-tree | branch | commit-range | files   # reviewer-facing projection
    baseline: <commit-or-null>       # the frozen baseline identity
    paths: [<path>]
  project_instructions:
    sources: [AGENTS.md, <other applicable project docs>]
  target_change:
    full_current_materialization: <diff baseline→current + changed-file contents
      + one-hop interaction inventory (see rules)>
```

Rules:

- Same round → same materialization for both reviewers. Lens rubric and output schema
  are NOT part of it (they differ by lens).
- Next round → re-materialize the CURRENT state against the SAME frozen baseline.
- **One-hop interaction inventory**: before spawning, the main agent searches the
  in-repo direct callers/callees/consumers of every interface, behavior, configuration
  or schema the change touches (per review-scope.md §4, one hop is in scope), and
  records the resulting path/symbol inventory. BOTH reviewers in the round receive
  the SAME inventory. Reviewers with read tools read those locations themselves;
  a no-tools reviewer spawn must INLINE the current contents of inventory locations
  instead.
- If sufficient one-hop context cannot be located or supplied, and correctness of the
  change therefore cannot be judged, STOP `blocked (incomplete materialization)`.
  Never shrink the scope into a PASS.
- NEVER included: prior-round findings, global F-ids, fix narratives, validation
  commands or results (validation is orchestrator-owned — reviewers judge from
  reading code), policy profiles, or any project-required review ledger file.

## 4. Spawn checklist (main agent, before each round)

- [ ] One-hop interaction inventory derived (§3 rules) and identical for both reviewers.
- [ ] Review materialization (§3) attached, identical for both reviewers.
- [ ] Correctness reviewer told to follow the `dual-review-correctness` skill.
- [ ] Structure reviewer told to follow the `dual-review-structure` skill.
- [ ] Isolation template included verbatim.
- [ ] Both spawns issued in the SAME turn so they run in parallel.
- [ ] Output contract stated: the YAML verdict envelope exactly as defined in
      THAT reviewer's own skill (not the orchestrator's finding-schema file);
      findings to the parent only.

## 5. Runtime adaptation

| Runtime | Parallel spawn | Read-only enforcement | Reviewer identity |
|---|---|---|---|
| Claude Code | dispatch BOTH Agent-tool calls in ONE message | plugin agents `dual-review-correctness-reviewer` / `dual-review-structure-reviewer` (`tools: Read, Grep, Glob`) + this prompt contract | agent definition preloads its rubric skill |
| Codex | spawn both subagents in one turn | this prompt contract; optionally a user-side read-only sandbox (below) | subagent told to follow the reviewer skill |

Paste the scope materialization into the prompt on both runtimes; do not rely on each
reviewer re-deriving git state differently.

### Optional Codex hardening

Codex per-agent `sandbox_mode = "read-only"` is configured in user/project
`.codex/agents/*.toml` files — those are user/project config, not something a plugin
can install. The loop works from the prompt contract alone; if the target project
already defines read-only reviewer agents, prefer spawning those.

## 6. Integrity defenses

All integrity violations (F1/F2/F3) follow a single bounded retry rule:

- **First violation in a round**: discard the round, re-spawn both reviewers fresh.
  A discarded round does NOT count against `max_rounds`, and any F-ids assigned in
  it are abandoned (never reused, even if the same root cause re-surfaces later).
- **Second violation in the same round**: STOPPED: blocked (integrity failure). The
  loop cannot converge if reviewers cannot produce valid output within the retry
  budget.

The three violation types:

- **Reviewer wrote something** (F1): any write operation observed from a reviewer.
  Also audit and revert/own whatever was written; treat all prior validation results
  as invalid.
- **Reviewer chased the main goal** (F2): fix suggestions turning into implementations,
  or goal/task/ledger mutations.
- **Reviewer shows prior-round knowledge** (F3, mainly shared-context runtimes): it
  references earlier rounds, F-ids, or the main thread's plan.

Prompt contracts and UI metadata (`agents/openai.yaml`) are NOT permission boundaries.
Treat runtime enforcement (Claude tool allowlists, Codex sandboxes) as the real
boundary where available.
