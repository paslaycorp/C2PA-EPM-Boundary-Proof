# Boundary contract

This demonstrator is intentionally narrow.

## C2PA side

The C2PA SDK owns C2PA parsing and validation. The demonstrator wraps the returned structures without rewriting C2PA status codes, changing the asset, or converting provenance into a value judgment.

## EPM side

EPM v0.1.2 consumes a stable evidence identifier derived from the canonical C2PA manifest-store report and evaluates whether the `applicability` assurance property survives a downstream context transition.

An EPM `AUTHORIZED` result is an authorization of the modeled evidentiary transition under EPM's rule semantics. It is **not** a grant of real-world permission.

## Authority side

External action authority is always emitted as `OUTSIDE_EPM_SCOPE` by this demonstrator. No C2PA result and no EPM transition result can populate an external authorization.

## Four invariants

1. Changing downstream context does not modify the C2PA receipt.
2. C2PA validation detail remains visible and lossless at the handoff.
3. Context changes are explicit, typed, and included in the proof trace.
4. External action authority cannot be inferred from C2PA or EPM output.
