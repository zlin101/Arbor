# Correctness Checklist

Work the changed scope through every applicable section. Report only what the change
adds or modifies.

## Behavior regression & side effects

- Change in one module breaking a caller elsewhere — trace cross-module/cross-package
  interactions of every edited contract.
- Changed function signature, return shape, error semantics, or default value with
  callers not updated.
- Removed or weakened precondition that another component relied on.
- Feature flag / gate removed or inverted so a previously disabled path turns on.
- Environment/developer-workflow breakage: renamed or removed env vars, changed secret
  lookup, remapped ports, now-required setup steps.
- Behavior differences between the happy path and retry/replay/interrupt paths.

## Error handling

- **Swallowed errors**: empty catch, catch-and-log-and-continue where the caller needed
  to know.
- **Over-broad catch** hiding specific failures (catching a base exception type around
  unrelated operations).
- **Missing error handling** on fallible operations: I/O, network, parsing, encoding.
- **Error information leakage**: stack traces or internals surfaced to users.
- **Async errors**: unhandled rejections, missing `.catch()`/error propagation, errors
  lost across goroutines/tasks.
- Partial failure in multi-step operations: first steps committed before a later step
  can fail (no rollback/compensation).

## Boundary conditions

- Null/nil/undefined property access on optional data.
- Truthiness checks that exclude valid values (`0`, `""`, `false`).
- Empty collections: first/last element access, division by counts, `for` over nothing.
- Numeric edges: division by zero, overflow, off-by-one in loop bounds/slicing/
  pagination, negative counts/indices.
- Strings: empty and whitespace-only inputs, very long inputs, Unicode/combining chars.
- Time: timezone-naive comparisons, DST boundaries, non-monotonic clocks for ordering.

## Performance

- N+1 access patterns: per-item queries/IO where a batch exists.
- New hot-path costs: regex compilation, parsing, crypto, or reflection inside loops.
- Unbounded growth: collections, caches, or buffers with no limit; loading entire
  files/tables into memory.
- Missing timeouts/retries/rate limits on new external calls.
- Synchronous expensive work added to a request path or UI thread.

## Architecture / SOLID — only when it endangers correctness

Report architecture here ONLY when it is the mechanism of the bug risk (e.g. two
uncoordinated owners of one state transition, a "temporarily" duplicated write path
that can diverge). Naming, cohesion aesthetics, and taste belong to the structural
reviewer — do not duplicate that role.

- Split ownership: two components can each mutate the same state without coordination.
- Divergent duplicates: near-identical logic in two places where one was updated.
- Hidden coupling: change relies on an ordering or invariant nothing enforces.
