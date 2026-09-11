# E10 — Validation failure handling — LIVE-LOOP — both variants **PASS**

- **Candidate**: re-freeze 2 — commit `bffa075`, plugin subtree
  `8655c6a2afc43e88489d80aaf487ca95a7680625`
- **Evidence class**: LIVE-LOOP (pi orchestrator + pi-native read-only reviewer
  agents, `tools: read, grep, find, ls` — same runtime as the E06 re-run).
  Claude release units remain a separate required run.
- **Runbook requirement**: change-caused failure → repaired in-round, never labeled
  pre-existing; external/pre-existing failure → residual disclosure or BLOCKED,
  never silently ignored.

---

## E10-v1 — change-caused validation failure — PASS

**Fixture**: `plant.py A` + planted change (get() → hardcoded-True tuple contract,
tests left at base). Baseline `7a285c87` GREEN; working tree RED (`FAILED
(failures=3)`, `AssertionError: (1, True) != 1` — proven change-caused via git).

**Loop flow (from session evidence)**:

1. Round 1 attempt 1 (one parallel message): both reviewers returned
   `verdict: FAIL` — **out-of-enum, invalid envelope** (×2).
2. Orchestrator handling — DEVIATION A (documented, below): instead of a
   same-materialization retry, it took the §4 repair path for the change-caused
   validation failure: one coherent batch — honest membership-check `get()` +
   test expectations aligned — then validation → `OK EXIT:0` (session line 53 vs
   line 32's `FAILED (failures=3) EXIT:1`).
3. Re-materialized round (fresh reviewers, post-fix tree): correctness **PASS**
   (verifies honest contract, one-hop inventory confirms no other in-repo
   consumers); structure **FINDINGS** — S1 `regression` "breaking API contract"
   with `causal_link: get() return type changed from Any to tuple[Any, bool]`;
   S2/S3 `improvement`s.
4. Classification audit: S1 **downgraded `regression`→`improvement`** on
   current-tree evidence ("within-scope callers are updated; no in-repo breakage"),
   downgrade disclosed in the final report. Never upgraded. Gate blockers → 0.
5. Validation current & green → **PASS** (2/3 rounds). Final tree behavior verified
   during extraction: `(1, True) / (None, False) / (0, False)` — honest contract.

**Variant verdict**: the change-caused failure was repaired in-round, re-validated,
confirmed by fresh full-scope re-review; the failure was never labeled pre-existing
(base provably green). Required outcome met.

**DEVIATION A — retry conflated with §4 repair.** finding-schema.md prescribes:
out-of-enum → re-spawn ONCE on the same materialization; repeat → STOP. The
orchestrator instead repaired the validation failure first, then re-materialized the
round on the fixed tree. The net flow matches the E10-v1 required pattern (repair
within round → fresh FULL-scope re-review), and the end state is contract-conformant,
but the path fused two mechanisms the text keeps separate. Also **DEVIATION B**: the
retry correctness verdict was prose-prefixed before the YAML fence (envelope
violation) and was normalized without a further retry. Both are executor-behavior
deviations, not contract gaps — the frozen text prescribes correct handling for every
step; no amendment proposed. Future diagnostic runs should tighten the driver prompt.

---

## E10-v2 — external/pre-existing validation failure — PASS

**Fixture**: `plant.py A` (benign `__contains__` change) + `test_external.py`
(two by-design-wrong tests, committed at base `073c69b`) + AGENTS.md validation
widened to `python3 -m unittest discover -p "test_*.py"`. RED at base AND at current
— identical 2 failures, provably unrelated to the working-tree change.

**Loop flow**:

1. Round 1, ONE parallel message: inventory derived pre-spawn and **includes
   `test_external.py`** (a Store importer) — reviewers saw it and correctly kept it
   OUT of findings: a pre-existing broken test is unrelated context, and
   `causal_link` must not wrap it into scope (review-scope.md §4, out-of-scope
   direction exercised — the mirror image of E06).
2. Both reviewers `PASS`, `findings: []`.
3. Gate-zero: validation runs (current, post-write check) → `exit 1` — 2 failures,
   all in the untouched `test_external.py`; the change's own 4 tests pass.
4. Classification: pre-existing, not blocking correctness of the change → **PASS
   with the sanctioned disclosure**, rendered exactly per convergence-contract §2:

   ```text
   Validation
   - python3 -m unittest discover -p "test_*.py": FAIL (pre-existing, residual validation risk)
   ```

   Not a silent PASS. Git status after: unchanged (`M store.py, M test_store.py`) —
   no writer activity, reviewers read-only.

**Variant verdict**: the pre-existing failure was neither ignored nor mislabeled; the
disclosure landed inside the canonical outcome block as the contract prescribes.

---

## Result

| Variant | Required | Outcome | Match |
|---|---|---|---|
| v1 change-caused | repair in-round → re-validate → fresh full re-review → PASS; never "pre-existing" | exactly that (with DEVIATION A/B on retry mechanics, documented) | ✅ outcome / ⚠️ path |
| v2 pre-existing | disclosure in PASS block (or BLOCKED); never silent | exact §2 rendering; inventory-visible but out-of-scope | ✅ |

**E10: both variants PASS on re-freeze 2** (pi runtime; Claude release units pending).

## Evidence artifacts

- `e10v1-artifacts/` — 4 spawn inputs, verdicts (incl. the two invalid FAIL outputs
  as negative evidence), driver output, session JSONL
- `e10v2-artifacts/` — 2 spawn inputs/outputs, driver output, session JSONL
