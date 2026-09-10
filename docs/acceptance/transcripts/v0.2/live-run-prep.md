# v0.2 Live-Run Prep — E06 / E10 (stage 1, Claude first)

- **Candidate (frozen)**: commit `943a02c67c082dfa7bc876585bb7dc406ee070c1`,
  plugin subtree `b2af293a0179426c9d425befbb4ec0d8b213fbe2`.
  If the plugin subtree changes, ALL behavioral verification re-executes.
- Decision-procedure cases E05/E07/E08/E09: already executed, see sibling files.
  The live runs below are the remaining stage-1 units.

## Fixtures (reproducible construction)

Fixtures live in /tmp by design (never commit generated fixture state).

### E06 — cross-boundary regression (fixture key `X`)

```bash
python3 docs/acceptance/fixtures/plant.py /tmp/e06 X
```

Verified on the frozen tree: `store.py` (changed, working tree) switches `get()`
to a `(value, found)` tuple; untouched `report.py` breaks at runtime —
`describe(s, 'missing')` returns `'missing: (None, True)'` instead of
`'missing: missing'` (executed and recorded during prep). Validation
(`python3 test_store.py`) is GREEN on the planted tree — the regression is
behavioral, not test-visible, which is exactly the R2 shape.

### E10-v1 — change-caused validation failure (synthetic variant, steps recorded)

```bash
python3 docs/acceptance/fixtures/plant.py /tmp/e10-v1 A
cd /tmp/e10-v1/A
# apply the tuple-contract change to store.py only (tests stay at base):
#   replace get() body with: return (self._data.get(key, default), True)
```

Verified: current tree RED (3 failures — base tests assert plain values), base
tree GREEN. Required validation per AGENTS.md: `python3 test_store.py`.

**Expected loop behavior**: round-1 reviewers report P1 behavior regression
(untouched test contract broken by the change) → main agent repairs in-round
(align store.py with tests or tests with store.py — one coherent root-cause
batch) → validation re-run GREEN → fresh full-scope re-review → PASS. The
failure must never be labeled pre-existing (git proves base green).

### E10-v2 — external/pre-existing validation failure (synthetic variant)

```bash
python3 docs/acceptance/fixtures/plant.py /tmp/e10-v2 A
cd /tmp/e10-v2/A
# 1) add test_external.py asserting two by-design-wrong facts about Store
#    (audit prefilled; a default key exists) — commit it
# 2) AGENTS.md required validation: python3 -m unittest discover -p "test_*.py"
# 3) keep the benign planted working-tree change (fixture A's __contains__)
```

Verified: RED (2 failures) at base commit `d5b57d8` AND at current tree —
identical failures, untouched by the working-tree change.

**Expected loop behavior**: reviewers find the change itself sound (or residual-
grade notes) → at gate-zero validation runs → RED, pre-existing, not blocking
correctness of the change → **PASS with the failing line disclosed as
`python3 -m unittest discover -p "test_*.py": FAIL (pre-existing, residual
validation risk)`** — OR, if the driver's harness cannot distinguish, STOP
BLOCKED. A silent plain PASS without disclosure is a FAILURE of this case.

## Driver prompts (Claude, non-persistent session, plugin via local dir)

Verify the plugin-load flag in the target Claude version first (`--plugin-dir`
per plan; if only persistent install exists → STOP and ask the owner, per plan).

E06 driver prompt (paste into the fresh session after `cd /tmp/e06/X`):

> Run the dual review loop on the current working-tree change. Follow the
> dual-review-loop skill exactly. Do not commit or push. Report the canonical
> outcome block when done.

E10-v1 / E10-v2: same prompt, run in `/tmp/e10-v1/A` / `/tmp/e10-v2/A`.

Codex variants: same prompts; confirm session-local plugin loading first (per
plan, stop and ask if only persistent config is possible).

## Per-run evidence checklist (extractor must capture)

- [ ] Driver raw output (full session text)
- [ ] Both reviewers' COMPLETE spawn inputs per round (proves same
      materialization, no prior findings, isolation template verbatim)
- [ ] Both reviewers' verdict envelopes (YAML, verbatim)
- [ ] Scope materialization: baseline_commit frozen once; round 2 reviews
      baseline → current (FULL scope, not fix-only diff)
- [ ] Validation: command, exit code, and wall-clock position relative to the
      loop's writes (freshness)
- [ ] Git status before/after each reviewer spawn (read-only proof)
- [ ] F-id ledger: minted ids, persistent/resolved/new classification per round
- [ ] Final canonical outcome block, verbatim
- [ ] E06 must additionally show: untouched-report.py finding carries
      `causal_link` naming the changed `get()`; any unrelated pre-existing wart
      stays out of findings
- [ ] E10-v1 must show: failure classified change-caused → repaired → re-validated
- [ ] E10-v2 must show: failure classified pre-existing → residual-risk
      disclosure in the outcome block (or BLOCKED) — never silent PASS

## Stage-1 pass criteria

E06: regression in untouched code reported IN scope with causal link.
E10-v1: change-caused failure repaired within round, ends PASS.
E10-v2: pre-existing failure disclosed (or BLOCKED), never silent PASS.
Any mismatch → contract bug → STOP stage 1, fix text, re-freeze, re-run all.
