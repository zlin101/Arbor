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
include_staged: bool
include_unstaged: bool
include_untracked: bool
```

Derive it from the user's request:

- **Working-tree review** (default when the user points at current work): include
  staged + unstaged changes, plus relevant untracked files, within the paths the user
  named (all paths if none named).
- **Branch / PR review**: baseline is what would actually merge. Prefer the merge-base
  of the branch and its base (`git merge-base <branch> <base>`) over a naive direct
  diff between the two tips, which can silently include or exclude unrelated work.
- **Commit-range review**: the named range; baseline is the range's first parent.
- **Explicit files**: exactly the named files; baseline is omitted — reviewers judge
  current content plus its direct context.

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

- manifestation of a change-induced regression;
- interaction point (caller/callee, configuration, schema, contract compatibility).

Unrelated pre-existing defects remain OUT of scope — they are context, never
findings, and `causal_link` must not be used to wrap them into scope.

When a finding's `location` is in untouched code, `causal_link` is REQUIRED and must
name the changed code that causes or materially worsens it (see finding-schema.md).

This is not a license for repo-wide review: findings still must trace to the change.

## 5. Loop-generated files

Files the main agent creates or modifies while fixing findings automatically join the
next round's full review scope (they are part of `current target change` now).

## 6. Presenting scope to reviewers

Each round, hand every reviewer the same materialization of the full change:

- the frozen baseline identity (ref/commit),
- the current diff or changed-file list with contents as available,
- applicable project instructions.

Do not include previous rounds' findings or conclusions — fresh reviewers get scope,
project rules, code, and their rubric; nothing else.
