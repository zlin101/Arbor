# Structural Quality Checklist

Signs and remedies for structural problems in the changed scope. Escalate in this
order: structural regressions → missed dramatic simplifications → spaghetti growth →
boundary/type problems → sprawl → legibility.

## Ambition & code judo

Ask of every meaningful change:

- Is there a reframing that makes whole branches, helpers, modes, or layers disappear?
- Can this be expressed so fewer concepts remain in the reader's head?
- Does the solution feel inevitable in hindsight, or does it accumulate exceptions?
- Is there a path that DELETES complexity rather than moving it?

If yes to any of these and the change ignored it, that is an `improvement`
finding — or a `regression` finding if the change actively forecloses the simpler
shape (e.g. bakes the messy version into a shared API). Whether it blocks is the
orchestrator's derivation, never yours.

## Spaghetti & branching growth

- New special-case conditionals inserted into unrelated, already-busy flows.
- One-off boolean modes or nullable flags that complicate existing control flow.
- "Temporary" branching with no removal path (temporary branches become permanent).
- Narrow edge-case handling buried mid-function instead of at a boundary.
- Repeated near-identical conditionals signaling a missing model or helper.

## Abstraction quality

- Thin wrappers / identity abstractions adding indirection without clarity.
- Speculative generality: parameterization for hypothetical future needs.
- "Magic" generic mechanisms hiding simple data-shape assumptions.
- Abstractions that would not survive being named after what they actually do.
- Cast-heavy or optionality-heavy contracts where an explicit type would simplify
  control flow.

## Canonical layer & reuse

- Feature logic leaking into shared/general-purpose modules.
- Implementation details crossing API/module boundaries.
- Bespoke one-off helpers where a canonical utility already exists in the codebase.
- Logic placed in the wrong layer/package when a more central home exists.

## Orchestration & atomicity

- Obviously independent work serialized for no reason.
- Related updates that can leave state half-applied (non-atomic sequences).
- Orchestration complexity that exists only because logic lives in the wrong place.

## File & component sprawl

- A previously cohesive module now larger, more coupled, or harder to scan.
- Divergent-change smell: one file changing for many unrelated reasons.
- Size growth (e.g. crossing ~1,000 lines) — evidence to investigate, NEVER a finding
  by itself. Always name the structural cause.

## Preferred remedies (in order of preference)

1. Delete a whole layer of indirection rather than polish it.
2. Reframe the state model so conditionals disappear instead of being centralized.
3. Move ownership so the feature becomes a natural extension of an existing abstraction.
4. Collapse duplicate branches into one clearer flow.
5. Reuse the canonical helper instead of a near-duplicate.
6. Extract a pure function or helper (when extraction deletes concepts, not when it
   just relocates them).
7. Make type boundaries explicit so control flow simplifies.
8. Parallelize independent work when that also simplifies orchestration.

## Review tone

- Direct and serious about real regressions; never soften a maintainability problem
  into a mild suggestion.
- Never present taste as a blocker; never demand polish without payoff.
- High-conviction comments over long cosmetic lists — if the biggest issue is a
  subjective style preference, the verdict is PASS.
