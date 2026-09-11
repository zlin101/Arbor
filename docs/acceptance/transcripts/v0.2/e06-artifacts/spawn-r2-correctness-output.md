reviewer: correctness
verdict: FINDINGS
findings:
  - local_id: C1
    severity: P3
    category: reliability
    location:
      file: store.py
      line: 16
      symbol: Store.get
    title: get() check-then-access lost dict.get's atomicity
    problem: "The rewrite replaces a single atomic dict.get(key, default) with two steps: `if key in self._data` followed by `self._data[key]`. Under concurrent mutation (another thread executing delete between the membership check and the subscript), the subscript raises KeyError instead of returning (default, False). It also performs two hash lookups where one sufficed."
    evidence: "store.py:16-17 — `if key in self._data: return (self._data[key], True)`. Baseline used `self._data.get(key, default)`, a single C-level atomic operation. No concurrent callers exist anywhere in the repo (only consumer is test_store.py), so the window is currently unobservable."
    impact: "Latent only: if Store is ever used from multiple threads, an interleaved delete turns a documented (default, False) return into an unhandled KeyError. No in-scope behavior changes today."
    recommended_direction: "Use a module-level sentinel with a single lookup — `value = self._data.get(key, _MISSING)` then compare against the sentinel — which restores atomicity and halves the lookups while keeping the v2 (value, found) contract."
coverage: "Reviewed the full working-tree diff of store.py and test_store.py against baseline 85a6d26; verified by inspection that all four tests' assertions match the implementation (they pass as written); confirmed tests are the only in-repo caller of Store.get, stdlib-only constraint holds, and AGENTS.md rules are respected."
residual_risks:
  - "Validation command `python3 test_store.py` was not executed — review is read-only/no-tools; runtime behavior was judged from code reading."
  - "Out-of-repo consumers of Store.get's previous plain-value return contract cannot be verified from this repo; the contract change is breaking for any such caller."

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Change under review stays in scope: only Store.get's return contract in store.py and the corresponding expectations in test_store.py are touched; set/delete/audit untouched; stdlib-only per AGENTS.md."
    },
    {
      "id": "criterion-2",
      "status": "satisfied",
      "evidence": "YAML verdict envelope above gives file:line locations, concrete evidence, and severity rationale (one P3, non-blocking); all four test assertions were traced against the implementation and are consistent as written."
    }
  ],
  "changedFiles": [
    "store.py",
    "test_store.py"
  ],
  "testsAddedOrUpdated": [
    "test_store.py — updated test_set_get_roundtrip, test_get_default, test_delete to v2 tuple contract; added test_stored_none_vs_absent"
  ],
  "commandsRun": [
    {
      "command": "python3 test_store.py",
      "result": "not-run",
      "summary": "Review runs read-only/no-tools; validation command not executed — assertions verified by inspection and expected to exit 0."
    }
  ],
  "validationOutput": [],
  "residualRisks": [
    "Required validation command not executed (reviewer is read-only); runtime pass/fail not directly observed.",
    "Possible out-of-repo consumers of the old Store.get plain-value contract cannot be ruled out from this repository."
  ],
  "noStagedFiles": true,
  "diffSummary": "Store.get changed from returning the plain value/default to a (value, found) tuple distinguishing stored-None from absent; tests updated to the v2 contract and a new stored-None-vs-absent test added.",
  "reviewFindings": [
    "P3 (non-blocking): store.py:16-17 - Store.get check-then-access lost dict.get's atomicity and doubles hash lookups; theoretical KeyError under concurrent delete; recommend sentinel-based single lookup."
  ],
  "manualNotes": "Review performed no-tools/read-only per isolation contract; no review ledger read, no commands run, nothing staged. Otherwise the change is internally consistent and correct for a single-threaded caller."
}
```