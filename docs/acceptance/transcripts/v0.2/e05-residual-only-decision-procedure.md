# E05 — Residual-only + validation unrun (R1) — DECISION-PROCEDURE

- **Candidate**: Arbor v0.2, commit `943a02c67c082dfa7bc876585bb7dc406ee070c1`
  (plugin subtree `b2af293a0179426c9d425befbb4ec0d8b213fbe2`)
- **Evidence class**: DECISION-PROCEDURE — the frozen contract text was applied to the
  stated synthetic history, branch by branch. No subagents, no live loop. This verifies
  the contract's decision procedure, NOT model loop behavior.
- **Executor note**: executed by the same agent session that authored the v0.2 text
  (self-review bias possible). A live driver re-run on Codex/Claude is still required
  by the release runbook before this case may be marked released.
- **v0.1 reference**: this history empirically dead-ended on v0.1 text (see R1 record,
  2026-09-10).

## Input history (max_rounds = 3, default profile)

- Round 1 materialization: frozen baseline `B0` → current tree.
- Correctness reviewer: `verdict: PASS`, `findings: []`, coverage stated.
- Structure reviewer: `verdict: FINDINGS`, exactly one finding
  `structural_class: improvement` (behavior-preserving simplification, evidence cited).
- Required validation (`python3 test_store.py`, declared in the project's AGENTS.md):
  NOT executed at any point this session.
- User did not ask for strict.

## Branch walk (frozen text, SKILL.md round algorithm + convergence-contract.md)

1. **Normalize**: no envelope violations; correctness PASS contributes no findings;
   structure contributes S1 (`improvement`). Assign F-ids: F001 minted (first
   appearance). classification per source: `structure: improvement`.
2. **Conflict/audit**: no reviewer conflict. Audit applies to BLOCK-producing
   classifications only (§1); `improvement` under default profile is not
   BLOCK-producing → no audit pass consumed.
3. **Derive gate blockers** (§2):

   ```text
   gate blockers =
       open correctness P0/P1 findings   → 0
     + open structural regressions       → 0
     + strict-profile extras             → 0 (default profile; improvement → RESIDUAL row)
   ```

   **gate blockers == 0** → enter the PASS path. F001 is NOT a gate blocker.

4. **Validation is the action that COMPLETES convergence** (§2; SKILL.md: "never STOP
   for lack of a fix while validation is still unrun"). No prior result exists and no
   write occurred since session start → run required validation NOW:
   `python3 test_store.py`.
5. **Outcome branches** (§2):
   - green → **PASS**, residual F001 recorded, never blocking.
   - red, pre-existing and not blocking correctness → PASS with the failing line
     rendered `python3 test_store.py: FAIL (pre-existing, residual validation risk)`.
   - red, blocks confirming correctness or caused by the change → §4 handling:
     repair in-round or STOP BLOCKED.
   - none declared → vacuous pass, render `none declared by project`.

   All four branches terminate in PASS or a handled repair — **no branch reaches
   STOP for lack of something to fix.**

6. **Final report**: exactly one canonical PASS block (output-format.md). No second
   outcome block; residual F001 listed as residual.

## Result

| Aspect | Required (runbook) | Frozen-text outcome | Match |
|---|---|---|---|
| Dead-end `STOP (blocked / unresolved)` | must NOT occur | unreachable: validation runs at gate-zero before any STOP-for-no-fix | ✅ |
| Validation executes on current tree | must run | step 4: runs now, priority 4 level | ✅ |
| Terminal state | PASS (green case) | PASS with residual recorded | ✅ |
| Improvement finding | never blocks default-profile PASS | policy row RESIDUAL; not in gate blockers | ✅ |

**E05 decision-procedure: PASS on v0.2 text.** The v0.1 failure (STOP although
convergent) is not expressible in the frozen algorithm: with zero gate blockers the
only exits are the validation branches.

---

## Re-run against re-freeze 2 (commit `bffa075`, subtree `8655c6a2…`)

Amendment under test: §3 one-hop interaction inventory + incomplete-materialization
stop. Walk delta:

- Round-1 history unchanged (correctness PASS; structure one `improvement` residual).
- Inventory rule: the orchestrator must derive the one-hop inventory before spawn. In
  this history the changed code has no callers beyond the co-updated tests (the
  synthetic tree's consumers are the tests themselves) — inventory is derivable and
  supplied. No incomplete-materialization stop.
- Gate derivation, validation-completes-convergence, PASS branches: identical to the
  walk above. The new stop cannot fire: inventory was locatable.

**E05 re-run: PASS on re-freeze 2 text. Outcome unchanged.**
