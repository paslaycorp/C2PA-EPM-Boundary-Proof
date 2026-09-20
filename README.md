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
| Real C2PA interoperability | C2PA published spec 2.4 metadata + c2patool 0.27.22 + pinned signed fixture | Test an actual provenance result crossing into the EPM decision boundary |

The frozen lane deliberately retains known historical limitations as expected falsifications rather than rewriting history to make the release appear stronger than it was.

## Exam v1

The adversarial suite attacks provenance-to-authority transmutation, changed purpose/context, UNKNOWN promotion, typed contradiction, unsupported schemas, hidden materiality, omission versus explicit UNKNOWN, caller-asserted authority, retroactive validation, revocation, reachability versus permission, deterministic composition, and real signed-asset tampering.

The first complete green evidence run is **GitHub Actions run 35542651303**, tested at proof-harness head:

`4725bf0b55e3fafb64ce65d26ae6c3b65ce01bde`

Observed results:

- frozen v0.1.2, Python 3.12: **4 passed + 2 expected historical falsifications**;
- frozen v0.1.2, Python 3.13: **4 passed + 2 expected historical falsifications**;
- post-release authority, Python 3.12: **11/11 passed**;
- post-release authority, Python 3.13: **11/11 passed**;
- real C2PA manifest: **validated under explicitly pinned fixture trust material**;
- changed-purpose handoff: **DENY / MISAPPLICATION / fail-closed**;
- action without authority basis: **DEFER / AUTHORITY_UNESTABLISHED / not permitted**;
- mutated signed asset: **Invalid / assertion.dataHash.mismatch**.

The preceding real-C2PA attempt is intentionally retained as a falsification record: the sample's test certificate was untrusted under the default trust store. The correction made that trust basis explicit rather than weakening the test.

See [EXAM-RESULT-v1.md](EXAM-RESULT-v1.md) for the human-readable evidence record, [receipts/EXAM-v1.json](receipts/EXAM-v1.json) for the machine-readable receipt, [BOUNDARY-CLAIM.md](BOUNDARY-CLAIM.md) for the exact claim under attack, and [UPSTREAM-PINS.json](UPSTREAM-PINS.json) for immutable upstream pins.

## Scope boundary

The real interoperability lane uses pinned public C2PA specification metadata, a checksum-pinned c2patool release, and a pinned signed c2patool fixture. It demonstrates the behavior of this boundary harness for those exact inputs.

It remains **not a C2PA conformance test suite**, and a green result must not be represented as C2PA certification, endorsement, or universal proof across all manifests, trust stores, implementations, or policy environments.
