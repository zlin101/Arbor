# Security & Reliability Checklist

Applied to the changed scope. Call out both exploitability and impact. Report only
issues the change introduces or worsens.

## Input / output safety

- **Injection**: SQL/NoSQL/command/GraphQL injection via concatenation or unescaped
  templates; shell interpolation of user data.
- **XSS / template safety**: raw HTML injection, unescaped output, unsafe rich-text
  handling.
- **SSRF**: user-controlled URLs reaching internal services without allowlisting.
- **Path traversal**: user input in file paths (`../`), unsanitized file names.
- **Deserialization**: untrusted data into object deserializers without validation.

## Authn / authz

- Missing tenant/ownership check on read or write of a resource.
- New endpoint/handler without an auth guard, or guard bypassed for "internal" calls.
- Trusting client-provided identities, roles, flags, or ids (IDOR).
- Authorization checked before an await/retry that can invalidate it (check-then-act).

## Secrets & PII

- API keys, tokens, credentials, or connection strings in code, config, logs, or error
  messages.
- Sensitive payloads logged at info/debug; PII masking missing in new log lines.
- Secrets exposed to the client (bundled into frontend, embedded in responses).

## Race conditions & atomicity

Ask for every shared-state touch: what happens with two concurrent callers?

- **Shared state**: unsynchronized global/singleton/collection mutation; lazy init
  without a lock; non-thread-safe structures used concurrently.
- **Check-then-act (TOCTOU)**:

```text
if not exists(key): create(key)        # existence check, then act
value = get(key); value += 1; set(key) # read-modify-write, non-atomic
if user.balance >= amount: user.balance -= amount
```

- **Database concurrency**: missing optimistic locking (version column) on
  read-modify-write; missing row locks where required; non-atomic counter updates;
  unique-constraint races on concurrent insert.
- **Distributed**: missing locks around shared resource work; cache invalidation
  races; ordering assumptions across async events; split-brain risks.
- **Partial writes**: related mutations not sharing one transaction/boundary, so a
  mid-sequence failure leaves inconsistent state.

## Data integrity

- Missing transactions around multi-step persistence.
- Weak validation before persistence (silent type coercion, unvalidated lengths).
- Missing idempotency for retryable operations (duplicate side effects on retry).
- Lost updates: concurrent modification overwrites without merge/conflict handling.

## Reliability of external interactions

- New external calls without timeout, retry policy, or failure handling.
- Resource leaks: file handles, connections, subscriptions opened without release.
- Unbounded loops/recursion; memory exhaustion paths.

## Supply chain (only when the change touches dependencies)

- New dependencies with known vulnerabilities, unpinned versions, or from untrusted
  sources; expanded permissions/capabilities granted to a dependency.
