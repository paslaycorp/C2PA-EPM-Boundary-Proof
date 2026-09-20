# C2PA–EPM Boundary Proof

Adversarial proof harness for testing the separation between **C2PA provenance verification** and **EPM evidentiary, applicability, and authority decisions**.

This repository is intentionally external to EPM. It does not modify EPM release tags or production authority, and it does **not** claim C2PA endorsement, certification, or conformance.

## Core proposition

> Verifiable provenance must not silently become evidentiary sufficiency, contextual applicability, or authority to act.

## Test surfaces

| Lane | Immutable pin | Purpose |
| --- | --- | --- |
| Frozen release | EPM v0.1.2 — `bb0559ddb8eff7f78acc432c0334ce7596c1045c` | Establish released behavior and preserve historical falsifications |
| Post-release authority | `adb1c31cdb428816c95a3cf98c9a4427c13ec482` | Attack later composition and authority-boundary hardening |

The frozen lane deliberately retains known historical limitations as expected falsifications rather than rewriting history to make the release appear stronger than it was.

## Current adversarial exam

The first exam attacks:

- provenance-to-authority transmutation;
- purpose/context changes without preservation;
- UNKNOWN promotion;
- typed contradiction preservation;
- unsupported schema handling;
- hidden material property changes;
- omission versus explicit UNKNOWN;
- caller-asserted authority;
- retroactive validation;
- revocation;
- network reachability versus permission; and
- deterministic composition receipts.

See [BOUNDARY-CLAIM.md](BOUNDARY-CLAIM.md) for the exact claim under attack and [UPSTREAM-PINS.json](UPSTREAM-PINS.json) for machine-readable pins.

## Scope boundary

The initial suite proves the **EPM-side semantic boundary** using C2PA-shaped provenance evidence references. A C2PA specification/toolchain pin and real manifest fixtures should be added as a separate phase. Until then, this repository must not be described as a C2PA conformance test suite.
