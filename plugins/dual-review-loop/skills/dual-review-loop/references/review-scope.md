# Review Scope Contract

How the loop defines, freezes, and re-uses the review target. This is a hard rule of the
loop: every round reviews the **same semantic change**, never just the newest diff.

## 1. Scope model

At loop start, determine and hold (internally — no file is written):

```yaml
scope_type: branch | working-tree | commit-range | files
base_ref: optional
baseline_commit: optional
paths: optional
```

Derive it from the user's request (discovery rules — two agents must reach the same
scope from the same request):

- **Working-tree review** (default when the user points at current work): staged +
  unstaged changes, plus untracked files that are imported/referenced by a changed
  file or share its directory — never ignored-path or generated files. Paths: all,
  unless the user named some.
- **Branch / PR review**: baseline is what would actually merge. The base is the
  user-named base ref, else the PR target, else the repo's default branch; take
  `git merge-base <branch> <base>` — never a direct tip-to-tip diff.
- **Commit-range review**: the named range; baseline is the range's first parent.
- **Explicit files**: exactly the named files; there is no diff baseline — causality
  is judged against the named files' current content and contracts, and loop-generated
  files still join later rounds (§5).

`baseline_commit` is the frozen anchor. Record it once; never re-derive it after fixes.

## 2. Freeze the baseline, not a snapshot

Freeze **where the change starts** (`baseline_commit`), not its content at freeze time.
Each round materializes the current state of the target change against that same
baseline. Do not snapshot file contents at round 1 and review the stale copy in later
rounds — later rounds must see fixes as they are now.

## 3. Scope stays semantically stable across rounds

Round 1 reviews:

```text
baseline → current target change
```

After fixing, round 2 reviews the same thing:

```text
same baseline → current target change after fixes
```

**Never** narrow a later round to:

```text
only the diff produced by the previous fix round
```

That narrowing is the primary cause of fake convergence (a fix can regress code the
narrow diff no longer contains).

## 4. Scope ownership is causality-based, not location-based

> **A finding is in scope iff it is causally attributable to the target change.**

Whether the change CAUSED or materially worsened the problem is the ownership
question — not whether the problem happens to sit on a changed line. The two must
never be conflated:

```text
changed:   service.GetUser() return semantics modified
untouched: handler calling GetUser() now crashes on the new contract
→ the crash IS in scope: manifestation in untouched code, cause in the change.
```

Untouched code may appear in a finding as:

- direct manifestation of a change-induced regression (crash, wrong result, broken
  contract);
- ONE interaction hop away: direct callers/callees of changed code, and code whose
  behavior is fed by configuration or schema values the change reads or writes.

"Materially worsened" means the baseline did not exhibit the problem, or exhibited it
strictly less severely (evidence required). Beyond one hop, or without a worsening
comparison, an issue is context — not a finding.

Unrelated pre-existing defects remain OUT of scope — they are context, never
findings, and `causal_link` must not be used to wrap them into scope.

When a finding's `location` is in untouched code, `causal_link` is REQUIRED and must
name the changed code that causes or materially worsens it (see finding-schema.md).

This is not a license for repo-wide review: findings still must trace to the change.

## 5. Loop-generated files

Files the main agent creates or modifies while fixing findings automatically join the
next round's full review scope (they are part of `current target change` now).

## 6. Presenting scope to reviewers

Each round, hand every reviewer the review materialization (§3 of
`reviewer-prompt-contract.md` — the single definition) of this scope's current state,
plus that reviewer's own rubric. Nothing else: no prior findings, no fix narratives.
