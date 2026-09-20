# C2PA–EPM Boundary Claim

This repository is an independent adversarial proof harness. It does **not** claim C2PA endorsement, certification, or conformance.

## Claim under attack

A provenance result can supply evidence about origin, history, or integrity. It must not silently become a conclusion that an artifact is evidentially sufficient, applicable to a changed context, or authorized for a consequential action.

The harness therefore attacks these invariants:

1. **Provenance is not authority.** Capability, reachability, verified origin, or intact provenance cannot manufacture permission.
2. **Context is material.** Purpose, scope, jurisdiction, time, rule, and governing authority changes cannot inherit assurance without an explicit preservation basis.
3. **Uncertainty is conserved.** UNKNOWN must not become PRESERVED or AUTHORIZED merely because later processing prefers a definitive result.
4. **Contradiction is not absence.** Where the tested EPM surface supports typed contradiction, CONTRADICTED must remain distinguishable from UNKNOWN.
5. **No retroactive authority.** A validation, grant, or later evidence state cannot authorize an earlier action merely by existing later.
6. **Composition cannot hide material change.** Explicit source-to-target property changes must not disappear because callers omit them from a materiality declaration.
7. **Receipts must be deterministic.** Equivalent inputs must not change semantic outcomes because of container or declaration ordering.

## Two test lanes

### Frozen release lane

Pinned to EPM v0.1.2 at:

`bb0559ddb8eff7f78acc432c0334ce7596c1045c`

This lane is immutable. Known historical limitations are recorded as expected falsifications rather than repaired here.

### Post-release authority lane

Pinned to:

`adb1c31cdb428816c95a3cf98c9a4427c13ec482`

This lane tests later authority and constitutional hardening. It is explicitly **not** represented as the frozen v0.1.2 release.

## Result semantics

- **PASS** — the pinned implementation resisted the attack.
- **XFAIL / known frozen gap** — the immutable release exhibits a known historical limitation preserved for auditability.
- **FAIL** — an unexpected invariant violation or regression requiring investigation.

No failure in this repository changes either upstream EPM pin.
